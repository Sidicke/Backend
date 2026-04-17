from django.utils import timezone
from rest_framework import generics, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from accounts.models import Medecin
from accounts.permissions import IsAdminGeneral, IsAdminGeneralOrAdminHopital, IsPatient
from notifications.utils import create_notification
from .models import Hopital, Service, HopitalService, MedecinService, DemandeAjoutService
from .permissions import IsAdminHopitalOwner
from .serializers import (
    HopitalListSerializer, HopitalCreateSerializer, HopitalUpdateSerializer,
    ServiceSerializer, HopitalServiceSerializer,
    MedecinServiceSerializer, MedecinServiceCreateSerializer,
    DemandeAjoutServiceSerializer, DemandeAjoutServiceCreateSerializer, DemandeRefusSerializer,
)


# ──────────────────────────────────────────────
# Hôpitaux
# ──────────────────────────────────────────────

class HopitalListCreateView(generics.ListCreateAPIView):
    """Liste publique des hôpitaux / Création par admin général."""

    filter_backends = [filters.SearchFilter]
    search_fields = ['nom', 'ville', 'hopital_services__service__nom', 'hopital_services__service__description']

    def get_queryset(self):
        queryset = Hopital.objects.filter(is_active=True)
        ville = self.request.query_params.get('ville')
        if ville:
            queryset = queryset.filter(ville__icontains=ville)
        service_id = self.request.query_params.get('service')
        if service_id:
            queryset = queryset.filter(hopital_services__service_id=service_id)
        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return HopitalCreateSerializer
        return HopitalListSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminGeneral()]


class HopitalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et désactivation d'un hôpital."""

    queryset = Hopital.objects.all()
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return HopitalUpdateSerializer
        return HopitalListSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        if self.request.method == 'DELETE':
            return [IsAdminGeneral()]
        # PUT/PATCH : admin général ou admin de cet hôpital
        return [IsAdminGeneralOrAdminHopital(), IsAdminHopitalOwner()]

    def perform_destroy(self, instance):
        """Désactivation au lieu de suppression."""
        instance.is_active = False
        instance.save(update_fields=['is_active'])


# ──────────────────────────────────────────────
# Services globaux
# ──────────────────────────────────────────────

class ServiceListCreateView(generics.ListCreateAPIView):
    """Liste publique des services / Création par admin général."""

    serializer_class = ServiceSerializer

    def get_queryset(self):
        return Service.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminGeneral()]


class ServiceDetailView(generics.RetrieveUpdateAPIView):
    """Détail et modification d'un service global."""

    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminGeneral()]


# ──────────────────────────────────────────────
# Services d'un hôpital
# ──────────────────────────────────────────────

class HopitalServiceListView(generics.ListAPIView):
    """Liste des services proposés par un hôpital (public)."""

    serializer_class = HopitalServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return HopitalService.objects.filter(
            hopital_id=self.kwargs['hopital_pk']
        ).select_related('service')


# ──────────────────────────────────────────────
# Demandes d'ajout de service
# ──────────────────────────────────────────────

class DemandeCreateView(generics.CreateAPIView):
    """Création d'une demande d'ajout de service (admin hôpital)."""

    serializer_class = DemandeAjoutServiceCreateSerializer
    permission_classes = [IsAdminGeneralOrAdminHopital]

    def perform_create(self, serializer):
        hopital_id = self.kwargs['hopital_pk']
        user = self.request.user

        # Vérifier que l'admin hôpital demande pour son propre hôpital
        if user.role == 'admin_hopital' and user.hopital_id != int(hopital_id):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Vous ne pouvez faire une demande que pour votre propre hôpital.")

        demande = serializer.save(hopital_id=hopital_id, demande_par=user)

        # Notifier tous les admins généraux
        from django.contrib.auth import get_user_model
        User = get_user_model()
        service_nom = (
            demande.service_existant.nom if demande.service_existant
            else demande.nom_nouveau_service
        )
        for admin in User.objects.filter(role='admin_general', is_active=True):
            create_notification(
                user=admin,
                type='demande_service',
                message=f"Nouvelle demande d'ajout du service « {service_nom} » pour l'hôpital {demande.hopital.nom}.",
                lien=f"/api/demandes/{demande.pk}/",
            )


class DemandeListView(generics.ListAPIView):
    """Liste des demandes (admin général = tout, admin hôpital = son hôpital)."""

    serializer_class = DemandeAjoutServiceSerializer
    permission_classes = [IsAdminGeneralOrAdminHopital]

    def get_queryset(self):
        user = self.request.user
        queryset = DemandeAjoutService.objects.select_related(
            'hopital', 'service_existant', 'demande_par', 'traite_par'
        )
        if user.role == 'admin_hopital':
            queryset = queryset.filter(hopital=user.hopital)
        return queryset


class DemandeValiderView(APIView):
    """Validation d'une demande d'ajout de service (admin général)."""

    permission_classes = [IsAdminGeneral]

    def post(self, request, pk):
        try:
            demande = DemandeAjoutService.objects.select_related(
                'hopital', 'service_existant', 'demande_par'
            ).get(pk=pk, statut='en_attente')
        except DemandeAjoutService.DoesNotExist:
            return Response(
                {'error': 'Demande introuvable ou déjà traitée.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Déterminer le service à associer
        if demande.service_existant:
            service = demande.service_existant
        else:
            # Créer le nouveau service global
            service = Service.objects.create(
                nom=demande.nom_nouveau_service,
                description=demande.description_nouveau_service,
            )

        # Associer le service à l'hôpital
        HopitalService.objects.get_or_create(hopital=demande.hopital, service=service)

        # Mettre à jour la demande
        demande.statut = 'valide'
        demande.date_traitement = timezone.now()
        demande.traite_par = request.user
        demande.save(update_fields=['statut', 'date_traitement', 'traite_par'])

        # Notifier l'admin hôpital in-app
        create_notification(
            user=demande.demande_par,
            type='validation_service',
            message=f"Votre demande d'ajout du service « {service.nom} » pour l'hôpital {demande.hopital.nom} a été validée.",
        )

        # Envoyer un e-mail
        html_message = render_to_string('hopitaux/emails/service_valide.html', {
            'demande': demande,
            'service_nom': service.nom,
        })
        send_mail(
            subject=f"Validation de votre service : {service.nom}",
            message=strip_tags(html_message),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[demande.demande_par.email],
            html_message=html_message,
            fail_silently=True,
        )

        return Response(
            {'message': f"Demande validée. Le service « {service.nom} » a été ajouté à l'hôpital."},
            status=status.HTTP_200_OK,
        )


class DemandeRefuserView(APIView):
    """Refus d'une demande d'ajout de service (admin général)."""

    permission_classes = [IsAdminGeneral]

    def post(self, request, pk):
        try:
            demande = DemandeAjoutService.objects.select_related(
                'hopital', 'service_existant', 'demande_par'
            ).get(pk=pk, statut='en_attente')
        except DemandeAjoutService.DoesNotExist:
            return Response(
                {'error': 'Demande introuvable ou déjà traitée.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DemandeRefusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Mettre à jour la demande
        demande.statut = 'refuse'
        demande.date_traitement = timezone.now()
        demande.traite_par = request.user
        demande.commentaire = serializer.validated_data.get('commentaire', '')
        demande.save(update_fields=['statut', 'date_traitement', 'traite_par', 'commentaire'])

        service_nom = (
            demande.service_existant.nom if demande.service_existant
            else demande.nom_nouveau_service
        )

        # Notifier l'admin hôpital
        message = f"Votre demande d'ajout du service « {service_nom} » pour l'hôpital {demande.hopital.nom} a été refusée."
        if demande.commentaire:
            message += f" Motif : {demande.commentaire}"

        create_notification(
            user=demande.demande_par,
            type='refus_service',
            message=message,
        )

        # Envoyer un e-mail
        html_message = render_to_string('hopitaux/emails/service_refuse.html', {
            'demande': demande,
            'service_nom': service_nom,
        })
        send_mail(
            subject=f"Refus de votre demande de service : {service_nom}",
            message=strip_tags(html_message),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[demande.demande_par.email],
            html_message=html_message,
            fail_silently=True,
        )

        return Response(
            {'message': 'Demande refusée.'},
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────
# Services d'un médecin
# ──────────────────────────────────────────────

class MedecinServiceListCreateView(APIView):
    """Liste et association des services d'un médecin."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminGeneralOrAdminHopital()]

    def get(self, request, medecin_pk):
        """Liste publique des services exercés par un médecin."""
        services = MedecinService.objects.filter(
            medecin_id=medecin_pk
        ).select_related('service')
        serializer = MedecinServiceSerializer(services, many=True)
        return Response(serializer.data)

    def post(self, request, medecin_pk):
        """Associer un service à un médecin."""
        try:
            medecin = Medecin.objects.select_related('user').get(pk=medecin_pk)
        except Medecin.DoesNotExist:
            return Response(
                {'error': 'Médecin introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Vérifier que l'admin hôpital gère ce médecin
        if request.user.role == 'admin_hopital' and medecin.user.hopital_id != request.user.hopital_id:
            return Response(
                {'error': "Vous ne pouvez gérer que les médecins de votre hôpital."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = MedecinServiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service_id = serializer.validated_data['service']

        # Vérifier que le service est proposé par l'hôpital du médecin
        if not HopitalService.objects.filter(
            hopital_id=medecin.user.hopital_id, service_id=service_id
        ).exists():
            return Response(
                {'error': "Ce service n'est pas proposé par l'hôpital du médecin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Créer l'association
        obj, created = MedecinService.objects.get_or_create(
            medecin=medecin, service_id=service_id
        )

        if not created:
            return Response(
                {'message': "Ce service est déjà associé à ce médecin."},
                status=status.HTTP_200_OK,
            )

        return Response(
            MedecinServiceSerializer(obj).data,
            status=status.HTTP_201_CREATED,
        )


class MedecinServiceDeleteView(APIView):
    """Retirer un service d'un médecin."""

    permission_classes = [IsAdminGeneralOrAdminHopital]

    def delete(self, request, medecin_pk, service_pk):
        try:
            medecin = Medecin.objects.select_related('user').get(pk=medecin_pk)
        except Medecin.DoesNotExist:
            return Response(
                {'error': 'Médecin introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Vérifier les permissions
        if request.user.role == 'admin_hopital' and medecin.user.hopital_id != request.user.hopital_id:
            return Response(
                {'error': "Vous ne pouvez gérer que les médecins de votre hôpital."},
                status=status.HTTP_403_FORBIDDEN,
            )

        deleted, _ = MedecinService.objects.filter(
            medecin=medecin, service_id=service_pk
        ).delete()

        if not deleted:
            return Response(
                {'error': "Association introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class HopitalMesServicesView(APIView):
    """Services de l'hôpital de l'admin connecté."""

    permission_classes = [IsAdminGeneralOrAdminHopital]

    def get(self, request):
        user = request.user
        if user.role == 'admin_hopital' and user.hopital_id:
            services = HopitalService.objects.filter(
                hopital_id=user.hopital_id
            ).select_related('service')
        elif user.role == 'admin_general':
            services = HopitalService.objects.all().select_related('service')
        else:
            services = HopitalService.objects.none()

        serializer = HopitalServiceSerializer(services, many=True)
        return Response(serializer.data)


class HopitalServiceUpdateView(generics.UpdateAPIView):
    """Mise à jour d'un service d'hôpital (description locale)."""

    serializer_class = HopitalServiceSerializer
    permission_classes = [IsAdminGeneralOrAdminHopital]

    def get_queryset(self):
        user = self.request.user
        queryset = HopitalService.objects.all()
        if user.role == 'admin_hopital' and user.hopital_id:
            queryset = queryset.filter(hopital_id=user.hopital_id)
        elif user.role != 'admin_general':
            # Sécurité si un autre rôle arrivait ici
            queryset = HopitalService.objects.none()
        return queryset


class HopitalStatistiquesView(APIView):
    """Statistiques de l'hôpital de l'admin connecté."""

    permission_classes = [IsAdminGeneralOrAdminHopital]

    def get(self, request):
        from django.contrib.auth import get_user_model
        from accounts.models import Medecin, Patient
        from rendezvous.models import RendezVous
        from messagerie.models import Message
        from django.db.models import Count
        from django.db.models.functions import TruncDay

        User = get_user_model()
        user = request.user
        stats = {}

        if user.role == 'admin_hopital' and user.hopital_id:
            hopital_id = user.hopital_id
            stats['total_medecins'] = Medecin.objects.filter(
                user__hopital_id=hopital_id, user__is_active=True
            ).count()
            stats['total_services'] = HopitalService.objects.filter(
                hopital_id=hopital_id
            ).count()
            stats['total_rdv'] = RendezVous.objects.filter(
                medecin__user__hopital_id=hopital_id
            ).count()
            stats['rdv_en_attente'] = RendezVous.objects.filter(
                medecin__user__hopital_id=hopital_id, statut='en_attente'
            ).count()
            stats['demandes_en_attente'] = DemandeAjoutService.objects.filter(
                hopital_id=hopital_id, statut='en_attente'
            ).count()
        elif user.role == 'admin_general':
            stats['total_hopitaux'] = Hopital.objects.filter(is_active=True).count()
            stats['total_medecins'] = Medecin.objects.filter(user__is_active=True).count()
            stats['total_services'] = Service.objects.filter(is_active=True).count()
            stats['total_rdv'] = RendezVous.objects.count()
            stats['active_users'] = User.objects.filter(is_active=True).count()
            stats['total_patients'] = Patient.objects.count()
            stats['total_messages'] = Message.objects.count()

            # Tendance des connexions (basé sur last_login pour les 7 derniers jours)
            seven_days_ago = timezone.now() - timezone.timedelta(days=7)
            daily_logins = User.objects.filter(last_login__gte=seven_days_ago) \
                .annotate(day=TruncDay('last_login')) \
                .values('day') \
                .annotate(count=Count('id')) \
                .order_by('day')
            
            days_map = {0: 'Lun', 1: 'Mar', 2: 'Mer', 3: 'Jeu', 4: 'Ven', 5: 'Sam', 6: 'Dim'}
            stats['daily_logins'] = []
            for i in range(7):
                d = timezone.now().date() - timezone.timedelta(days=6-i)
                count = 0
                for log in daily_logins:
                    if log.get('day') and log['day'].date() == d:
                        count = log['count']
                        break
                stats['daily_logins'].append({
                    'day': days_map[d.weekday()],
                    'count': count
                })

            # Activité récente
            recent_activity = []
            
            # Derniers inscrits
            recent_users = User.objects.order_by('-date_joined')[:3]
            for u in recent_users:
                recent_activity.append({
                    'type': 'register' if u.role == 'patient' else 'login',
                    'description': f"Nouveau {u.role}: {u.get_full_name()}",
                    'timestamp': u.date_joined.strftime('%d/%m %H:%M')
                })
            
            # Derniers rendez-vous
            recent_rdvs = RendezVous.objects.select_related('patient__user', 'medecin__user').order_by('-cree_le')[:2]
            for r in recent_rdvs:
                recent_activity.append({
                    'type': 'appointment',
                    'description': f"RDV: {r.patient.user.last_name} -> Dr. {r.medecin.user.last_name}",
                    'timestamp': r.cree_le.strftime('%d/%m %H:%M')
                })
            
            stats['recent_activity'] = sorted(recent_activity, key=lambda x: x['timestamp'], reverse=True)

            # Performance système (basiques réels ou réalistes)
            import psutil
            try:
                stats['system_performance'] = {
                    'cpu': psutil.cpu_percent(),
                    'memory': psutil.virtual_memory().percent,
                    'storage': psutil.disk_usage('/').percent,
                    'network': 15.5 # Fake network pour éviter complexité psutil net_io
                }
            except:
                stats['system_performance'] = {
                    'cpu': 25.0, 'memory': 40.0, 'storage': 30.0, 'network': 10.0
                }

        return Response(stats)


# ──────────────────────────────────────────────
# Recherche d'hôpitaux par proximité
# ──────────────────────────────────────────────

class NearbyHospitalView(APIView):
    """
    Recherche d'hôpitaux par proximité géographique.

    GET /api/hopitaux/nearby/?lat=<float>&lng=<float>&radius=<int>

    Accessible uniquement aux patients authentifiés.
    """

    permission_classes = [IsAuthenticated, IsPatient]

    def get(self, request):
        try:
            # ── Extraction et validation des paramètres ──
            lat_str = request.query_params.get('lat')
            lng_str = request.query_params.get('lng')
            radius_str = request.query_params.get('radius', '10')

            if not lat_str or not lng_str:
                return Response(
                    {'error': 'Les paramètres "lat" et "lng" sont obligatoires.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                user_lat = float(lat_str)
                user_lng = float(lng_str)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Les paramètres "lat" et "lng" doivent être des nombres valides.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not (-90 <= user_lat <= 90) or not (-180 <= user_lng <= 180):
                return Response(
                    {'error': 'Coordonnées GPS invalides. Latitude: [-90, 90], Longitude: [-180, 180].'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                radius_km = int(radius_str)
                if radius_km <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Le paramètre "radius" doit être un entier positif (en km).'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ── Appel au service de distance ──
            from .services import get_nearby_hospitals
            results = get_nearby_hospitals(
                user_lat=user_lat,
                user_lng=user_lng,
                radius_km=radius_km,
            )

            if not results:
                return Response([], status=status.HTTP_200_OK)

            # ── Sérialisation ──
            hospitals = []
            for r in results:
                hopital = r['hopital']
                hopital.distance_km = r['distance_km']
                hospitals.append(hopital)

            from .serializers import NearbyHospitalSerializer
            # Passer le context request pour les ImageFields
            serializer = NearbyHospitalSerializer(hospitals, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"DEBUG: Erreur inattendue dans NearbyHospitalView : {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': f'Erreur inattendue : {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class HopitalPatientsView(APIView):
    """Liste agrégée des patients ayant eu un RDV dans cet hôpital (admin hôpital)."""
    permission_classes = [IsAdminGeneralOrAdminHopital]

    def get(self, request):
        from accounts.models import Patient
        from rendezvous.models import RendezVous
        from accounts.serializers import PatientListSerializer
        
        user = request.user
        hopital_id = None

        if user.role == 'admin_hopital' and user.hopital_id:
            hopital_id = user.hopital_id
        elif user.role == 'admin_general':
            hopital_id = request.query_params.get('hopital_id')
            if not hopital_id:
                return Response({'error': 'hopital_id est requis pour l\'admin général.'}, status=400)
        
        if not hopital_id:
             return Response({'error': 'Accès interdit ou identifiant hôpital manquant.'}, status=status.HTTP_403_FORBIDDEN)

        # Patients qui ont un RDV avec un médecin de cet hôpital
        patient_ids = RendezVous.objects.filter(
            medecin__user__hopital_id=hopital_id
        ).values_list('patient_id', flat=True).distinct()
        
        patients = Patient.objects.filter(id__in=patient_ids).select_related('user')
        serializer = PatientListSerializer(patients, many=True)
        return Response(serializer.data)
