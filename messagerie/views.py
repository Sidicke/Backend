from django.db.models import Q, Max, Count
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Message
from .permissions import IsConsultationParticipant, IsMessageDestinataire
from .serializers import (
    MessageSerializer, MessageCreateSerializer, ConversationSerializer,
)


class ConversationListView(APIView):
    """Liste des conversations de l'utilisateur connecté (Consultations & Messages Directs)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Subquery, OuterRef, Count, Value, CharField
        from django.db.models.functions import Substr
        user = request.user
        conversations = []

        # ─── 1. Conversations liées aux consultations ───────────────────
        from rendezvous.models import Consultation

        # Sous-requête : dernier message de chaque consultation
        latest_msg_subquery = Message.objects.filter(
            consultation_id=OuterRef('pk')
        ).order_by('-date_envoi')

        consultations_qs = Consultation.objects.select_related(
            'rendez_vous__patient__user',
            'rendez_vous__medecin__user',
        ).annotate(
            last_msg_contenu=Subquery(latest_msg_subquery.values('contenu')[:1]),
            last_msg_date=Subquery(latest_msg_subquery.values('date_envoi')[:1]),
            non_lus=Count(
                'rendez_vous__consultation__messages',
                filter=Q(
                    rendez_vous__consultation__messages__destinataire=user,
                    rendez_vous__consultation__messages__lu=False,
                ),
            ),
        )

        if user.role == 'patient':
            consultations_qs = consultations_qs.filter(rendez_vous__patient__user=user)
        elif user.role == 'medecin':
            consultations_qs = consultations_qs.filter(rendez_vous__medecin__user=user)
        elif user.role == 'admin_hopital':
            consultations_qs = consultations_qs.filter(
                rendez_vous__medecin__user__hopital=user.hopital
            )
        else:
            consultations_qs = consultations_qs.filter(
                Q(rendez_vous__patient__user=user) | Q(rendez_vous__medecin__user=user)
            )

        for c in consultations_qs:
            rdv = c.rendez_vous
            if user.pk == rdv.patient.user_id:
                dest_id = rdv.medecin.user_id
                titre = f"Consultation avec Dr. {rdv.medecin.user.last_name}"
            else:
                dest_id = rdv.patient.user_id
                titre = f"Patient {rdv.patient.user.get_full_name()}"

            conversations.append({
                'consultation_id': c.pk,
                'destinataire_id': dest_id,
                'titre': titre,
                'dernier_message': (c.last_msg_contenu or '')[:100],
                'date_dernier_message': c.last_msg_date or c.date_consultation,
                'non_lus': c.non_lus or 0,
                'type': 'consultation',
                'est_cloture': c.est_cloture,
            })

        # ─── 2. Messages directs (hors consultation) ───────────────────
        direct_msgs = Message.objects.filter(
            (Q(expediteur=user) | Q(destinataire=user)) & Q(consultation__isnull=True)
        ).select_related('expediteur', 'destinataire').order_by('-date_envoi')

        # Pré-calculer les comptages de non-lus par pair (1 seule requête)
        unread_counts = dict(
            Message.objects.filter(
                consultation__isnull=True,
                destinataire=user,
                lu=False,
            ).values_list('expediteur').annotate(cnt=Count('id')).values_list('expediteur', 'cnt')
        )

        visited_peers = set()
        for msg in direct_msgs:
            peer = msg.destinataire if msg.expediteur_id == user.pk else msg.expediteur
            if peer.pk in visited_peers:
                continue
            visited_peers.add(peer.pk)

            conversations.append({
                'consultation_id': None,
                'destinataire_id': peer.pk,
                'titre': peer.get_full_name(),
                'dernier_message': msg.contenu[:100],
                'date_dernier_message': msg.date_envoi,
                'non_lus': unread_counts.get(peer.pk, 0),
                'type': 'direct',
                'est_cloture': False,
            })

        # Trier par date du dernier message (le plus récent en premier)
        conversations.sort(key=lambda c: c['date_dernier_message'] or '', reverse=True)
        return Response(conversations)


class MessageListCreateView(generics.ListCreateAPIView):
    """Liste des messages d'une consultation / Envoi d'un message."""

    permission_classes = [IsAuthenticated, IsConsultationParticipant]

    def get_serializer_class(self):
        """Utiliser MessageSerializer pour GET, MessageCreateSerializer pour POST."""
        if self.request.method == 'POST':
            return MessageCreateSerializer
        return MessageSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Message.objects.select_related('expediteur', 'destinataire')

        consultation_id = self.request.query_params.get('consultation')
        destinataire_id = self.request.query_params.get('destinataire')

        if consultation_id:
            queryset = queryset.filter(consultation_id=consultation_id)
            # Marquer comme lu seulement si l'utilisateur est le destinataire
            queryset.filter(destinataire=user, lu=False).update(lu=True)
        elif destinataire_id:
            queryset = queryset.filter(
                (Q(expediteur=user) & Q(destinataire_id=destinataire_id)) |
                (Q(expediteur_id=destinataire_id) & Q(destinataire=user))
            ).filter(consultation__isnull=True)
            queryset.filter(destinataire=user, lu=False).update(lu=True)
        else:
            # Vue générale : participants ou admin hopital (pour consultations)
            general_filter = Q(expediteur=user) | Q(destinataire=user)
            if user.role == 'admin_hopital':
                general_filter |= Q(consultation__rendez_vous__medecin__user__hopital=user.hopital)
            queryset = queryset.filter(general_filter)

        return queryset.order_by('date_envoi')

    def perform_create(self, serializer):
        message = serializer.save(expediteur=self.request.user)

        # Broadcast via WebSocket
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if message.consultation:
            group_name = f"chat_{message.consultation.pk}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'chat_message',
                    'message': MessageSerializer(message).data
                }
            )


class MessageMarkReadView(APIView):
    """Marquer un message comme lu (destinataire uniquement)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            message = Message.objects.get(pk=pk, destinataire=request.user)
        except Message.DoesNotExist:
            return Response(
                {'error': 'Message introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        message.lu = True
        message.save(update_fields=['lu'])

        return Response({'message': 'Message marqué comme lu.'}, status=status.HTTP_200_OK)
