from datetime import date, timedelta
from django.db.models import Q

from django.utils import timezone
from rest_framework import generics, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Medecin
from accounts.permissions import IsAdminGeneral, IsMedecin, IsPatient, IsMedecinOrAdminGeneral
from notifications.utils import create_notification
from Chatbot.whatsapp_utils import send_whatsapp_message
from .models import Disponibilite, RendezVous, Consultation
from .permissions import (
    IsDisponibiliteOwner, IsRendezVousMedecin, IsRendezVousParticipant,
    IsConsultationParticipant,
)
from .serializers import (
    DisponibiliteSerializer, DisponibiliteCreateSerializer, CreneauSerializer,
    RendezVousSerializer, RendezVousCreateSerializer, CommentaireSerializer,
    ConsultationSerializer, ConsultationUpdateSerializer,
)
from .utils import generer_creneaux


# ──────────────────────────────────────────────
# Disponibilités
# ──────────────────────────────────────────────

class DisponibiliteListCreateView(generics.ListCreateAPIView):
    """Liste et création des disponibilités."""

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['jour_semaine', 'heure_debut']

    def get_queryset(self):
        user = self.request.user
        queryset = Disponibilite.objects.select_related('medecin__user')
        medecin_id = self.request.query_params.get('medecin')
        if medecin_id:
            # Filtrage explicite par médecin (utilisé par les patients pour voir les créneaux)
            queryset = queryset.filter(medecin_id=medecin_id)
        elif user.is_authenticated and user.role == 'medecin':
            # Un médecin connecté ne voit QUE ses propres disponibilités
            queryset = queryset.filter(medecin__user=user)
        elif user.is_authenticated and user.role == 'admin_hopital':
            # Un admin hôpital voit les disponibilités de son hôpital
            queryset = queryset.filter(medecin__user__hopital=user.hopital)
        elif user.is_authenticated and user.role == 'admin_general':
            pass  # Voit tout
        else:
            # Aucun accès sans filtre explicite pour les non-authentifiés
            queryset = queryset.none()
        type_dispo = self.request.query_params.get('type')
        if type_dispo:
            queryset = queryset.filter(type=type_dispo)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DisponibiliteCreateSerializer
        return DisponibiliteSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsMedecinOrAdminGeneral()]

    def perform_create(self, serializer):
        # Le médecin connecté est automatiquement le propriétaire
        if self.request.user.role == 'medecin':
            serializer.save(medecin=self.request.user.medecin_profile)
        else:
            # Admin général doit préciser le médecin
            serializer.save()


class DisponibiliteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et suppression d'une disponibilité."""

    queryset = Disponibilite.objects.select_related('medecin__user')
    serializer_class = DisponibiliteSerializer
    permission_classes = [IsAuthenticated, IsDisponibiliteOwner]


class MedecinDisponibilitesView(generics.ListAPIView):
    """Plages d'un médecin spécifique (public)."""

    serializer_class = DisponibiliteSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Disponibilite.objects.filter(
            medecin_id=self.kwargs['medecin_pk'],
            is_active=True,
        ).select_related('medecin__user')


class MedecinCreneauxView(APIView):
    """Créneaux libres d'un médecin sur une période (public)."""

    permission_classes = [AllowAny]

    def get(self, request, medecin_pk):
        try:
            medecin = Medecin.objects.get(pk=medecin_pk, statut='actif')
        except Medecin.DoesNotExist:
            return Response(
                {'error': 'Médecin introuvable ou inactif.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Paramètres de date (par défaut : 7 prochains jours)
        date_debut_str = request.query_params.get('date_debut')
        date_fin_str = request.query_params.get('date_fin')

        try:
            date_debut = date.fromisoformat(date_debut_str) if date_debut_str else date.today()
            date_fin = date.fromisoformat(date_fin_str) if date_fin_str else date_debut + timedelta(days=7)
        except ValueError:
            return Response(
                {'error': 'Format de date invalide. Utilisez AAAA-MM-JJ.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Limiter à 30 jours maximum
        if (date_fin - date_debut).days > 30:
            date_fin = date_debut + timedelta(days=30)

        creneaux = generer_creneaux(medecin, date_debut, date_fin)
        serializer = CreneauSerializer(creneaux, many=True)
        return Response(serializer.data)


# ──────────────────────────────────────────────
# Rendez-vous
# ──────────────────────────────────────────────

class RendezVousListCreateView(generics.ListCreateAPIView):
    """Liste des RDV de l'utilisateur connecté / Prise de RDV par un patient."""

    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['date_heure', 'cree_le']

    def get_queryset(self):
        user = self.request.user
        queryset = RendezVous.objects.select_related(
            'patient__user', 'medecin__user', 'pre_enregistrement'
        ).prefetch_related('consultation')

        if user.role == 'patient':
            queryset = queryset.filter(patient__user=user)
        elif user.role == 'medecin':
            queryset = queryset.filter(medecin__user=user)
        elif user.role == 'admin_hopital':
            queryset = queryset.filter(medecin__user__hopital=user.hopital)
        elif user.role == 'laborantin':
            queryset = queryset.filter(medecin__user__hopital=user.hopital)
        elif user.role == 'admin_general':
            pass  # Voit tout
        else:
            queryset = queryset.none()

        # Filtres optionnels
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

        medecin_id = self.request.query_params.get('medecin')
        if medecin_id:
            queryset = queryset.filter(medecin_id=medecin_id)

        service_id = self.request.query_params.get('service')
        if service_id:
            # On filtre les RDV des médecins proposant ce service dans leur hôpital
            queryset = queryset.filter(medecin__user__hopital__hopital_services__service_id=service_id)

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RendezVousCreateSerializer
        return RendezVousSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsPatient()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Tentative de création de RDV par user={self.request.user.email}, role={self.request.user.role}")
        
        # Le patient connecté est automatiquement le demandeur
        if self.request.user.role == 'patient':
            serializer.save()
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les patients peuvent prendre rendez-vous.")


class RendezVousDetailView(generics.RetrieveAPIView):
    """Détail d'un rendez-vous."""

    queryset = RendezVous.objects.select_related('patient__user', 'medecin__user').prefetch_related('consultation')
    serializer_class = RendezVousSerializer
    permission_classes = [IsAuthenticated, IsRendezVousParticipant]


class RendezVousConfirmerView(APIView):
    """Confirmer un rendez-vous en attente (médecin)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            rdv = RendezVous.objects.select_related('patient__user', 'medecin__user').get(
                pk=pk, medecin__user=request.user
            )
        except RendezVous.DoesNotExist:
            return Response({'error': 'Rendez-vous introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if rdv.statut != 'en_attente':
            return Response(
                {'error': f"Impossible de confirmer un rendez-vous avec le statut « {rdv.get_statut_display()} »."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rdv.statut = 'confirme'
        rdv.save(update_fields=['statut', 'modifie_le'])

        create_notification(
            user=rdv.patient.user,
            type='rdv_confirme',
            message=(
                f"Votre rendez-vous avec Dr. {rdv.medecin.user.last_name} "
                f"le {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} a été confirmé."
            ),
            lien=f"/api/rendezvous/{rdv.pk}/",
        )
        
        # Envoi de l'email au patient
        from accounts.utils import send_appointment_status_email
        try:
            send_appointment_status_email(rdv)
        except Exception:
            pass

        # Envoi de la notification WhatsApp au patient
        try:
            patient_tel = rdv.patient.user.telephone
            if patient_tel:
                clean_phone = "".join(filter(str.isdigit, str(patient_tel)))
                msg = (
                    f"✅ RDV Confirmé !\n\n"
                    f"Votre rendez-vous avec Dr. {rdv.medecin.user.last_name} "
                    f"est confirmé pour le {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}.\n"
                    f"Lieu : {rdv.medecin.user.hopital.nom}"
                )
                send_whatsapp_message(clean_phone, msg)
        except Exception:
            pass

        return Response({'message': 'Rendez-vous confirmé.'}, status=status.HTTP_200_OK)


class RendezVousRefuserView(APIView):
    """Refuser un rendez-vous en attente (médecin)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            rdv = RendezVous.objects.select_related('patient__user', 'medecin__user').get(
                pk=pk, medecin__user=request.user
            )
        except RendezVous.DoesNotExist:
            return Response({'error': 'Rendez-vous introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if rdv.statut != 'en_attente':
            return Response(
                {'error': f"Impossible de refuser un rendez-vous avec le statut « {rdv.get_statut_display()} »."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CommentaireSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rdv.statut = 'refuse'
        rdv.commentaire_annulation = serializer.validated_data['commentaire']
        rdv.save(update_fields=['statut', 'commentaire_annulation', 'modifie_le'])

        create_notification(
            user=rdv.patient.user,
            type='rdv_refuse',
            message=(
                f"Votre rendez-vous avec Dr. {rdv.medecin.user.last_name} "
                f"le {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} a été refusé. "
                f"Motif : {rdv.commentaire_annulation}"
            ),
            lien=f"/api/rendezvous/{rdv.pk}/",
        )
        
        # Envoi de la notification WhatsApp au patient (Refus)
        try:
            patient_tel = rdv.patient.user.telephone
            if patient_tel:
                clean_phone = "".join(filter(str.isdigit, str(patient_tel)))
                msg = (
                    f"❌ RDV Refusé\n\n"
                    f"Votre rendez-vous avec Dr. {rdv.medecin.user.last_name} "
                    f"le {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} a été refusé.\n"
                    f"Motif : {rdv.commentaire_annulation}"
                )
                send_whatsapp_message(clean_phone, msg)
        except Exception:
            pass

        return Response({'message': 'Rendez-vous refusé.'}, status=status.HTTP_200_OK)


class Rendez_vousAnnulerView(APIView):
    """Annuler un rendez-vous confirmé (médecin uniquement)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            rdv = RendezVous.objects.select_related('patient__user', 'medecin__user').get(
                pk=pk, medecin__user=request.user
            )
        except RendezVous.DoesNotExist:
            return Response({'error': 'Rendez-vous introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if rdv.statut in ('annule', 'termine'):
            return Response(
                {'error': f"Impossible d'annuler un rendez-vous avec le statut « {rdv.get_statut_display()} »."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CommentaireSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rdv.statut = 'annule'
        rdv.commentaire_annulation = serializer.validated_data['commentaire']
        rdv.save(update_fields=['statut', 'commentaire_annulation', 'modifie_le'])

        # Envoi notification WhatsApp (Annulation)
        try:
            patient_tel = rdv.patient.user.telephone
            if patient_tel:
                clean_phone = "".join(filter(str.isdigit, str(patient_tel)))
                msg = (
                    f"⚠️ RDV Annulé\n\n"
                    f"Votre rendez-vous avec Dr. {rdv.medecin.user.last_name} "
                    f"le {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} a été annulé par le médecin.\n"
                    f"Motif : {rdv.commentaire_annulation}"
                )
                send_whatsapp_message(clean_phone, msg)
        except Exception:
            pass

        return Response({'message': 'Rendez-vous annulé.'}, status=status.HTTP_200_OK)


class RendezVousTerminerView(APIView):
    """Marquer un rendez-vous comme terminé et créer la consultation (médecin)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            rdv = RendezVous.objects.select_related('patient__user', 'medecin__user').get(
                pk=pk, medecin__user=request.user
            )
        except RendezVous.DoesNotExist:
            return Response({'error': 'Rendez-vous introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if rdv.statut != 'confirme':
            return Response(
                {'error': "Seul un rendez-vous confirmé peut être marqué comme terminé."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérifier que l'heure du RDV est passée
        # Commenté pour la démo : on peut terminer un RDV à tout moment
        # if rdv.date_heure > timezone.now():
        #     return Response(
        #         {'error': "Impossible de terminer un rendez-vous avant l'heure prévue."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )

        # Marquer comme terminé
        rdv.statut = 'termine'
        rdv.save(update_fields=['statut', 'modifie_le'])

        # Créer la consultation
        consultation = Consultation.objects.create(
            rendez_vous=rdv,
            compte_rendu=request.data.get('compte_rendu', ''),
            diagnostic=request.data.get('diagnostic', ''),
            prescription=request.data.get('prescription', ''),
        )

        create_notification(
            user=rdv.patient.user,
            type='consultation_ajoutee',
            message=(
                f"Votre consultation avec Dr. {rdv.medecin.user.last_name} "
                f"du {rdv.date_heure.strftime('%d/%m/%Y')} est terminée. "
                f"Le compte rendu est disponible."
            ),
            lien=f"/api/consultations/{consultation.pk}/",
        )

        return Response(
            ConsultationSerializer(consultation).data,
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────
# Consultations
# ──────────────────────────────────────────────

class ConsultationListView(generics.ListAPIView):
    """Liste des consultations de l'utilisateur connecté."""

    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Consultation.objects.select_related(
            'rendez_vous__patient__user', 'rendez_vous__medecin__user'
        )

        if user.role == 'patient':
            queryset = queryset.filter(rendez_vous__patient__user=user)
        elif user.role == 'medecin':
            queryset = queryset.filter(rendez_vous__medecin__user=user)
        elif user.role == 'admin_hopital':
            queryset = queryset.filter(rendez_vous__medecin__user__hopital=user.hopital)
        elif user.role == 'admin_general':
            pass
        else:
            queryset = queryset.none()

        return queryset


class ConsultationDetailView(generics.RetrieveUpdateAPIView):
    """Détail et mise à jour d'une consultation."""

    queryset = Consultation.objects.select_related(
        'rendez_vous__patient__user', 'rendez_vous__medecin__user'
    )
    permission_classes = [IsAuthenticated, IsConsultationParticipant]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            # Seul le médecin peut modifier
            if self.request.user.role != 'medecin':
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Seul le médecin peut modifier la consultation.")
            return ConsultationUpdateSerializer
        return ConsultationSerializer
class ConsultationCloturerView(APIView):
    """Clôturer une consultation (médecin)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            consultation = Consultation.objects.select_related(
                'rendez_vous__medecin__user'
            ).get(pk=pk, rendez_vous__medecin__user=request.user)
        except Consultation.DoesNotExist:
            return Response({'error': 'Consultation introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if consultation.est_cloture:
            return Response({'error': 'Cette consultation est déjà clôturée.'}, status=status.HTTP_400_BAD_REQUEST)

        consultation.est_cloture = True
        consultation.date_cloture = timezone.now()
        consultation.save(update_fields=['est_cloture', 'date_cloture'])

        create_notification(
            user=consultation.rendez_vous.patient.user,
            type='consultation_cloturee',
            message=f"Votre consultation avec Dr. {consultation.rendez_vous.medecin.user.last_name} est désormais clôturée.",
            lien=f"/api/consultations/{consultation.pk}/",
        )

        return Response({'message': 'Consultation clôturée.'}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
# Préenregistrement (Intake)
# ──────────────────────────────────────────────

class PreEnregistrementView(APIView):
    """Récupération (GET) et Édition (POST/PUT) du préenregistrement pour un RendezVous (Patient Intake)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            rdv = RendezVous.objects.select_related('pre_enregistrement').get(pk=pk)
        except RendezVous.DoesNotExist:
            return Response({'error': 'Rendez-vous introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        # Vérification participant
        is_patient = request.user.role == 'patient' and getattr(request.user, 'patient_profile', None) == rdv.patient
        is_medecin = request.user.role == 'medecin' and getattr(request.user, 'medecin_profile', None) == rdv.medecin
        
        if not (is_patient or is_medecin or request.user.role == 'admin_general'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Accès refusé.")

        if not hasattr(rdv, 'pre_enregistrement'):
            return Response({'error': 'Aucun préenregistrement.'}, status=status.HTTP_404_NOT_FOUND)

        from .serializers import PreEnregistrementSerializer
        return Response(PreEnregistrementSerializer(rdv.pre_enregistrement).data)

    def post(self, request, pk):
        return self._save(request, pk, create=True)

    def put(self, request, pk):
        return self._save(request, pk, create=False)

    def _save(self, request, pk, create):
        try:
            rdv = RendezVous.objects.get(pk=pk)
        except RendezVous.DoesNotExist:
            return Response({'error': 'Rendez-vous introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role != 'patient' or getattr(request.user, 'patient_profile', None) != rdv.patient:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul le patient titulaire du rendez-vous peut éditer cet intake.")

        if rdv.statut in ('termine', 'annule', 'refuse'):
            return Response(
                {'error': f"Édition verrouillée car le rendez-vous est {rdv.get_statut_display()}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if create and hasattr(rdv, 'pre_enregistrement'):
            return Response({'error': 'Déjà existant (utilisez PUT).'}, status=status.HTTP_400_BAD_REQUEST)
        if not create and not hasattr(rdv, 'pre_enregistrement'):
            return Response({'error': 'N\'existe pas (utilisez POST).'}, status=status.HTTP_404_NOT_FOUND)

        from .serializers import PreEnregistrementSerializer
        instance = getattr(rdv, 'pre_enregistrement', None)
        serializer = PreEnregistrementSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(rendez_vous=rdv)

        return Response(serializer.data, status=status.HTTP_201_CREATED if create else status.HTTP_200_OK)
