from django.conf import settings
from django.db.models import Q
from django.core.mail import send_mail
from django.http import FileResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework import generics, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdminGeneral
from notifications.utils import create_notification
from .models import DemandeAnalyse, Resultat
from .permissions import IsResultatAccessible, IsResultatOwner
from .serializers import (
    DemandeAnalyseSerializer, DemandeAnalyseCreateSerializer, DemandeAnalyseCloturerSerializer,
    ResultatSerializer, ResultatCreateSerializer,
    PartageSerializer, ResultatPublicSerializer,
)


# ──────────────────────────────────────────────
# BioTrack — Demandes d'analyse
# ──────────────────────────────────────────────

class DemandeAnalyseListCreateView(generics.ListCreateAPIView):
    """
    Liste des demandes d'analyse du laborantin connecté.
    POST : Inscrire un nouveau patient pour une analyse (statut en_cours automatique).
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['patient_nom', 'patient_prenom', 'patient_email', 'type_analyse']
    ordering_fields = ['date_inscription', 'statut']

    def get_queryset(self):
        user = self.request.user
        qs = DemandeAnalyse.objects.select_related(
            'hopital', 'laborantin', 'patient__user', 'resultat'
        )
        if user.role == 'laborantin':
            qs = qs.filter(hopital=user.hopital)
        elif user.role == 'admin_hopital':
            qs = qs.filter(hopital=user.hopital)
        elif user.role == 'admin_general':
            pass
        elif user.role == 'patient':
            qs = qs.filter(Q(patient__user=user) | Q(patient_email=user.email))
        else:
            return qs.none()

        # Filtrer par statut (optionnel)
        statut_filtre = self.request.query_params.get('statut')
        if statut_filtre:
            qs = qs.filter(statut=statut_filtre)

        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DemandeAnalyseCreateSerializer
        return DemandeAnalyseSerializer


class DemandeAnalyseCloturerView(APIView):
    """
    Clôturer une demande d'analyse : déposer le fichier résultat.
    Crée un Resultat, met à jour la demande à 'cloture', envoie un email au patient.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            demande = DemandeAnalyse.objects.select_related(
                'hopital', 'laborantin', 'patient__user'
            ).get(pk=pk)
        except DemandeAnalyse.DoesNotExist:
            return Response({'error': 'Demande introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        # Seul le laborantin responsable ou un admin peut clôturer
        user = request.user
        if user.role == 'laborantin' and demande.laborantin != user:
            return Response({'error': 'Non autorisé.'}, status=status.HTTP_403_FORBIDDEN)

        if demande.statut == DemandeAnalyse.Statut.CLOTURE:
            return Response({'error': 'Cette demande est déjà clôturée.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = DemandeAnalyseCloturerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fichier = serializer.validated_data['fichier']
        titre = serializer.validated_data.get('titre') or demande.type_analyse

        # Récupérer le profil patient si inscrit
        patient_link = demande.patient  # peut être None

        # Créer le Resultat
        resultat = Resultat.objects.create(
            patient=patient_link,
            laborantin=user,
            hopital=demande.hopital,
            titre=titre,
            fichier=fichier,
            date_analyse=timezone.now().date(),
            laboratoire=getattr(user, 'laborantin_profile', None) and user.laborantin_profile.laboratoire or demande.hopital.nom,
            patient_nom_externe=f"{demande.patient_prenom} {demande.patient_nom}",
            patient_email_externe=demande.patient_email,
        )

        # Associer à la demande et mettre à jour le statut
        demande.resultat = resultat
        demande.statut = DemandeAnalyse.Statut.CLOTURE
        demande.date_cloture = timezone.now()
        demande.save(update_fields=['resultat', 'statut', 'date_cloture'])

        # Envoyer email au patient
        email_dest = demande.patient_email
        nom_patient = f"{demande.patient_prenom} {demande.patient_nom}"
        try:
            html_message = render_to_string('resultats/emails/nouveau_resultat.html', {
                'resultat': resultat,
                'nom_patient': nom_patient,
                'hopital': demande.hopital,
            })
            send_mail(
                subject=f"[{demande.hopital.code_court}] Vos resultats d'analyse sont disponibles",
                message=strip_tags(html_message),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_dest],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception:
            pass  # On ne bloque pas si l'email échoue

        # Notification si patient inscrit
        if patient_link:
            create_notification(
                user=patient_link.user,
                type='nouveau_resultat',
                message=f"Vos resultats d'analyse ({titre}) sont disponibles. Code : {resultat.code_acces}",
                lien=f"/api/resultats/{resultat.pk}/",
            )

        # Envoi SMS Twilio (Patient)
        from accounts.twilio_utils import send_twilio_sms
        try:
            # Récupérer le téléphone (soit via le profil patient, soit via la demande si on l'avait stocké, 
            # mais ici on utilise le profil si dispo)
            tel = None
            if patient_link:
                tel = patient_link.user.telephone
            
            if tel:
                msg = (
                    f"E-SANTE [{resultat.hopital.code_court}]: Vos resultats sont disponibles. "
                    f"Code de verification: {resultat.code_acces}"
                )
                send_twilio_sms(tel, msg)
        except Exception:
            pass

        return Response(
            {
                'message': 'Analyse cloturee. Le patient a ete notifie par email.',
                'code_acces': resultat.code_acces,
                'resultat_id': resultat.pk,
            },
            status=status.HTTP_201_CREATED,
        )


# ──────────────────────────────────────────────
# Liste et dépôt de résultats (legacy conservé)
# ──────────────────────────────────────────────

class ResultatListCreateView(generics.ListCreateAPIView):
    """Liste des résultats / Dépôt par un laborantin."""

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titre', 'patient__user__first_name', 'patient__user__last_name']
    ordering_fields = ['date_depot', 'date_analyse']

    def get_queryset(self):
        user = self.request.user
        queryset = Resultat.objects.select_related(
            'patient__user', 'laborantin', 'consultation', 'hopital'
        ).prefetch_related('partages__user')

        if user.role == 'patient':
            queryset = queryset.filter(Q(patient__user=user) | Q(patient_email_externe=user.email))
        elif user.role == 'medecin':
            queryset = queryset.filter(partages__user=user)
        elif user.role == 'laborantin':
            queryset = queryset.filter(hopital=user.hopital)
        elif user.role == 'admin_hopital':
            queryset = queryset.filter(hopital=user.hopital)
        elif user.role == 'admin_general':
            pass
        else:
            queryset = queryset.none()

        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResultatCreateSerializer
        return ResultatSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in ('laborantin', 'admin_general'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Seul un laborantin peut deposer un resultat.")
        resultat = serializer.save()

        # Envoyer l'email au patient si inscrit
        if resultat.patient:
            html_message = render_to_string('resultats/emails/nouveau_resultat.html', {
                'resultat': resultat,
                'nom_patient': resultat.patient.user.get_full_name(),
                'hopital': resultat.hopital,
            })
            send_mail(
                subject=f"Nouveau resultat d'analyse : {resultat.titre}",
                message=strip_tags(html_message),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[resultat.patient.user.email],
                html_message=html_message,
                fail_silently=True,
            )


# ──────────────────────────────────────────────
# Détail d'un résultat
# ──────────────────────────────────────────────

class ResultatDetailView(generics.RetrieveAPIView):
    """Détail d'un résultat."""

    queryset = Resultat.objects.select_related(
        'patient__user', 'laborantin', 'consultation', 'hopital'
    ).prefetch_related('partages__user')
    serializer_class = ResultatSerializer
    permission_classes = [IsAuthenticated, IsResultatAccessible]


# ──────────────────────────────────────────────
# Téléchargement du fichier PDF
# ──────────────────────────────────────────────

class ResultatTelechargerView(APIView):
    """Télécharger le fichier PDF d'un résultat."""

    permission_classes = [IsAuthenticated, IsResultatAccessible]

    def get(self, request, pk):
        try:
            resultat = Resultat.objects.get(pk=pk)
        except Resultat.DoesNotExist:
            return Response({'error': 'Résultat introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, resultat)

        if not resultat.fichier:
            return Response({'error': 'Aucun fichier associé.'}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(
            resultat.fichier.open('rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"{resultat.titre}.pdf",
        )


# ──────────────────────────────────────────────
# Partage avec un médecin
# ──────────────────────────────────────────────

class ResultatPartagerView(APIView):
    """Partager un résultat avec un médecin."""

    permission_classes = [IsAuthenticated, IsResultatOwner]

    def post(self, request, pk):
        try:
            resultat = Resultat.objects.get(pk=pk)
        except Resultat.DoesNotExist:
            return Response({'error': 'Résultat introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, resultat)

        serializer = PartageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        medecin_id = serializer.validated_data['medecin']

        resultat.partages.add(medecin_id)

        from accounts.models import Medecin
        medecin = Medecin.objects.select_related('user').get(pk=medecin_id)
        create_notification(
            user=medecin.user,
            type='nouveau_resultat',
            message=(
                f"{resultat.patient_display_nom} a partage un resultat "
                f"d'analyse « {resultat.titre} » avec vous."
            ),
            lien=f"/api/resultats/{resultat.pk}/",
        )

        return Response({'message': 'Résultat partagé avec le médecin.'}, status=status.HTTP_200_OK)


class ResultatRetirerPartageView(APIView):
    """Retirer l'accès d'un médecin à un résultat."""

    permission_classes = [IsAuthenticated, IsResultatOwner]

    def delete(self, request, pk, medecin_pk):
        try:
            resultat = Resultat.objects.get(pk=pk)
        except Resultat.DoesNotExist:
            return Response({'error': 'Résultat introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, resultat)

        if not resultat.partages.filter(pk=medecin_pk).exists():
            return Response(
                {'error': "Ce médecin n'a pas accès à ce résultat."},
                status=status.HTTP_404_NOT_FOUND,
            )

        resultat.partages.remove(medecin_pk)
        return Response({'message': "Accès retiré."}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
# Accès public via code
# ──────────────────────────────────────────────

class ResultatAccesCodeView(APIView):
    """Accéder à un résultat via son code d'accès (sans authentification)."""

    permission_classes = [AllowAny]

    def get(self, request, code):
        try:
            resultat = Resultat.objects.select_related('patient__user', 'hopital').get(code_acces=code)
        except Resultat.DoesNotExist:
            return Response(
                {'error': "Code d'accès invalide."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ResultatPublicSerializer(resultat)
        return Response(serializer.data)


class LaborantinPatientListView(generics.ListAPIView):
    """Liste des patients éligibles pour une analyse (RDV terminés dans l'hôpital)."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from accounts.models import Patient
        from rendezvous.models import RendezVous
        user = self.request.user
        
        if user.role != 'laborantin' or not user.hopital_id:
             return Patient.objects.none()
             
        # Patients ayant un RDV "termine" dans cet hôpital
        patient_ids = RendezVous.objects.filter(
            medecin__user__hopital_id=user.hopital_id,
            statut='termine'
        ).values_list('patient_id', flat=True).distinct()
        
        return Patient.objects.filter(id__in=patient_ids).select_related('user')

    def get_serializer_class(self):
        from accounts.serializers import PatientListSerializer
        return PatientListSerializer
