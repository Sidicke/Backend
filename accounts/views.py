import csv
import io
from django.db.models import Q

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.crypto import get_random_string
from rest_framework import generics, status, filters
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views import View

from .models import Patient, Medecin, Laborantin
from .permissions import IsAdminGeneral, IsAdminGeneralOrAdminHopital
from .serializers import (
    PatientRegisterSerializer, UserMeSerializer,
    MedecinCreateSerializer, MedecinListSerializer, MedecinUpdateSerializer,
    LaborantinCreateSerializer, LaborantinListSerializer, LaborantinUpdateSerializer,
    PatientListSerializer, PatientUpdateSerializer,
    AdminHopitalCreateSerializer, AdminHopitalListSerializer, AdminHopitalUpdateSerializer,
    MedecinCSVImportSerializer,
)
from .utils import generate_secure_token, send_verification_email, send_account_created_email, send_password_reset_email
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature

signer = TimestampSigner()
User = get_user_model()


# ──────────────────────────────────────────────
# Inscription et vérification email
# ──────────────────────────────────────────────

class PatientRegisterView(generics.CreateAPIView):
    """Inscription d'un nouveau patient."""

    serializer_class = PatientRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_active = False  # Désactiver jusqu'à vérification
        user.save(update_fields=['is_active'])

        # Générer et envoyer le token de vérification (valide 24h)
        token = generate_secure_token(user.pk)
        try:
            send_verification_email(user, token)
        except Exception:
            # On ne supprime pas l'utilisateur, mais on prévient l'UI
            return Response(
                {'error': "Erreur Gmail : Impossible d'envoyer l'e-mail de vérification. Vérifiez la configuration SMTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'message': "Inscription réussie ! Veuillez vérifier votre boîte mail pour valider votre compte avant de vous connecter."},
            status=status.HTTP_201_CREATED,
        )


from django.shortcuts import render

class VerifyEmailView(APIView):
    """Vérification de l'adresse email du patient (retourne une page HTML pour les mobiles)."""

    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            # Vérifier le token avec une validité de 24h (86400 secondes)
            user_pk = signer.unsign(token, max_age=86400)
            user = User.objects.get(pk=user_pk)
        except SignatureExpired:
            return render(request, 'accounts/activation_invalid.html', {'error': "Le lien de vérification a expiré (plus de 24h)."}, status=status.HTTP_400_BAD_REQUEST)
        except (BadSignature, User.DoesNotExist):
            return render(request, 'accounts/activation_invalid.html', {'error': "Le lien de vérification est invalide ou corrompu."}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_active and getattr(user, 'is_email_verified', False):
            # Si le compte est déjà activé, on affiche quand même le succès
            return render(request, 'accounts/activation_success.html', status=status.HTTP_200_OK)

        user.is_active = True
        user.is_email_verified = True
        user.save(update_fields=['is_active', 'is_email_verified'])

        # Créer une notification de bienvenue
        from notifications.utils import create_notification
        create_notification(
            user=user,
            type='compte_cree',
            message=f"Bienvenue {user.first_name} ! Votre compte a été activé avec succès.",
        )

        return render(request, 'accounts/activation_success.html', status=status.HTTP_200_OK)

# ──────────────────────────────────────────────
# Réinitialisation de mot de passe
# ──────────────────────────────────────────────

class RequestPasswordResetView(APIView):
    """Demander un lien de réinitialisation de mot de passe."""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': "L'adresse email est requise."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                return Response({'error': "Ce compte n'est pas actif."}, status=status.HTTP_400_BAD_REQUEST)
            
            token = generate_secure_token(user.pk)
            try:
                send_password_reset_email(user, token)
            except Exception:
                return Response(
                    {'error': "Erreur Gmail : Impossible d'envoyer l'e-mail. Vérifiez la configuration SMTP."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {'message': "Un lien de réinitialisation vous a été envoyé par e-mail."},
                status=status.HTTP_200_OK,
            )
        except User.DoesNotExist:
            return Response(
                {'error': "Aucun compte n'est associé à cette adresse e-mail."},
                status=status.HTTP_404_NOT_FOUND,
            )

class ResetPasswordConfirmView(APIView):
    """Confirmer la réinitialisation avec le token et définir un nouveau mot de passe."""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password') or request.data.get('password')

        if not token or not new_password:
            return Response({'error': "Le token et le nouveau mot de passe sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validité du token de 15 minutes (900 secondes)
            user_pk = signer.unsign(token, max_age=900)
            user = User.objects.get(pk=user_pk)
            
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            return Response({'message': "Votre mot de passe a été réinitialisé avec succès."}, status=status.HTTP_200_OK)
            
        except SignatureExpired:
            return Response({'error': "Le lien de réinitialisation a expiré (validité de 15min)."}, status=status.HTTP_400_BAD_REQUEST)
        except (BadSignature, User.DoesNotExist):
            return Response({'error': "Lien de réinitialisation invalide."}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetHTMLView(View):
    """Vue HTML pour la réinitialisation de mot de passe hors application."""

    def get(self, request, token):
        return render(request, 'accounts/password_reset_form.html', {'token': token})

    def post(self, request, token):
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not new_password or new_password != confirm_password:
            return render(request, 'accounts/password_reset_form.html', {
                'token': token,
                'error': "Les mots de passe ne correspondent pas ou sont vides."
            })

        try:
            # Récupérer l'utilisateur à partir du token (15min validité)
            user_pk = signer.unsign(token, max_age=900)
            user = User.objects.get(pk=user_pk)
            user.set_password(new_password)
            user.save(update_fields=['password'])
            return render(request, 'accounts/password_reset_form.html', {'success': True})

        except SignatureExpired:
            return render(request, 'accounts/password_reset_form.html', {
                'token': token, 'error': "Le lien a expiré (15 min de validité)."
            })
        except (BadSignature, User.DoesNotExist):
            return render(request, 'accounts/password_reset_form.html', {
                'token': token, 'error': "Lien de réinitialisation invalide."
            })



# ──────────────────────────────────────────────
# Profil utilisateur connecté
# ──────────────────────────────────────────────

class UserMeView(generics.RetrieveUpdateAPIView):
    """Récupération et mise à jour du profil de l'utilisateur connecté."""

    serializer_class = UserMeSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# ──────────────────────────────────────────────
# Gestion des médecins
# ──────────────────────────────────────────────

class MedecinListCreateView(generics.ListCreateAPIView):
    """Liste publique des médecins actifs / Création par admin."""

    filter_backends = [filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'numero_ordre']

    def get_queryset(self):
        queryset = Medecin.objects.select_related('user', 'user__hopital').filter(
            user__is_active=True, statut='actif'
        )
        hopital_id = self.request.query_params.get('hopital')
        if hopital_id:
            queryset = queryset.filter(user__hopital_id=hopital_id)
            
        service_id = self.request.query_params.get('service')
        if service_id:
            queryset = queryset.filter(medecin_services__service_id=service_id).distinct()
            
        # L'admin hôpital ne voit par défaut que les médecins de son hôpital
        if self.request.user.is_authenticated and self.request.user.role == 'admin_hopital':
            queryset = queryset.filter(user__hopital_id=self.request.user.hopital_id)
            
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MedecinCreateSerializer
        return MedecinListSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminGeneralOrAdminHopital()]

    def perform_create(self, serializer):
        medecin = serializer.save()
        
        # Envoi de l'email pour configuration du mot de passe
        token = generate_secure_token(medecin.user.pk)
        send_account_created_email(medecin.user, reset_token=token)

        from notifications.utils import create_notification
        create_notification(
            user=medecin.user,
            type='compte_cree',
            message=f"Bienvenue Dr. {medecin.user.last_name} ! Votre compte médecin a été créé.",
        )


class MedecinDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et désactivation d'un médecin."""

    queryset = Medecin.objects.select_related('user', 'user__hopital')
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return MedecinUpdateSerializer
        return MedecinListSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminGeneralOrAdminHopital()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        # L'admin hôpital ne peut modifier que les médecins de son hôpital
        if request.method in ('PUT', 'PATCH', 'DELETE'):
            if request.user.role == 'admin_hopital' and obj.user.hopital_id != request.user.hopital_id:
                self.permission_denied(request, message="Vous ne pouvez gérer que les médecins de votre hôpital.")

    def perform_destroy(self, instance):
        """Désactivation au lieu de suppression."""
        instance.user.is_active = False
        instance.user.save(update_fields=['is_active'])
        instance.statut = 'inactif'
        instance.save(update_fields=['statut'])


class MedecinDesactiverView(APIView):
    """Désactiver un médecin (admin hôpital ou admin général)."""

    permission_classes = [IsAdminGeneralOrAdminHopital]

    def post(self, request, pk):
        try:
            medecin = Medecin.objects.select_related('user').get(pk=pk)
        except Medecin.DoesNotExist:
            return Response(
                {'error': 'Médecin introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == 'admin_hopital' and medecin.user.hopital_id != request.user.hopital_id:
            return Response(
                {'error': "Vous ne pouvez gérer que les médecins de votre hôpital."},
                status=status.HTTP_403_FORBIDDEN,
            )

        medecin.user.is_active = False
        medecin.user.save(update_fields=['is_active'])
        medecin.statut = 'inactif'
        medecin.save(update_fields=['statut'])

        return Response({'message': 'Médecin désactivé avec succès.'}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
# Gestion des laborantins
# ──────────────────────────────────────────────

class LaborantinListCreateView(generics.ListCreateAPIView):
    """Liste et création des laborantins."""

    filter_backends = [filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name']

    def get_queryset(self):
        queryset = Laborantin.objects.select_related('user', 'user__hopital').filter(user__is_active=True)
        hopital_id = self.request.query_params.get('hopital')
        if hopital_id:
            queryset = queryset.filter(user__hopital_id=hopital_id)

        # L'admin hôpital ne voit que les laborantins de son hôpital
        if self.request.user.is_authenticated and self.request.user.role == 'admin_hopital':
            queryset = queryset.filter(user__hopital_id=self.request.user.hopital_id)

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LaborantinCreateSerializer
        return LaborantinListSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAdminGeneralOrAdminHopital()]
        return [IsAdminGeneralOrAdminHopital()]

    def perform_create(self, serializer):
        laborantin = serializer.save()
        
        # Envoi de l'email pour configuration du mot de passe
        token = generate_secure_token(laborantin.user.pk)
        send_account_created_email(laborantin.user, reset_token=token)

        from notifications.utils import create_notification
        create_notification(
            user=laborantin.user,
            type='compte_cree',
            message=f"Bienvenue {laborantin.user.first_name} ! Votre compte laborantin a été créé.",
        )


class LaborantinDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et désactivation d'un laborantin."""

    queryset = Laborantin.objects.select_related('user', 'user__hopital')
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return LaborantinUpdateSerializer
        return LaborantinListSerializer

    def get_permissions(self):
        return [IsAdminGeneralOrAdminHopital()]

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method in ('PUT', 'PATCH', 'DELETE'):
            if request.user.role == 'admin_hopital' and obj.user.hopital_id != request.user.hopital_id:
                self.permission_denied(request, message="Vous ne pouvez gérer que les laborantins de votre hôpital.")

    def perform_destroy(self, instance):
        """Désactivation au lieu de suppression."""
        instance.user.is_active = False
        instance.user.save(update_fields=['is_active'])


# ──────────────────────────────────────────────
# Gestion des patients (admin général)
# ──────────────────────────────────────────────

class PatientListView(generics.ListAPIView):
    """Liste des patients (tous pour admin général, filtré pour admin hôpital et laborantin)."""

    serializer_class = PatientListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin_general':
            return Patient.objects.select_related('user').all()
        elif user.role == 'medecin':
            return Patient.objects.filter(
                rendezvous__medecin__user=user
            ).distinct().select_related('user')
        elif user.role in ['admin_hopital', 'laborantin'] and user.hopital_id:
            # Pour le laborantin/admin_hopital, on limite aux patients ayant eu un RDV ou une analyse dans cet hôpital
            return Patient.objects.filter(
                Q(rendezvous__medecin__user__hopital_id=user.hopital_id) |
                Q(demandes_analyse__hopital_id=user.hopital_id)
            ).distinct().select_related('user')
        return Patient.objects.none()


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et désactivation d'un patient (admin général)."""

    queryset = Patient.objects.select_related('user')
    permission_classes = [IsAdminGeneral]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PatientUpdateSerializer
        return PatientListSerializer

    def perform_destroy(self, instance):
        """Désactivation au lieu de suppression."""
        instance.user.is_active = False
        instance.user.save(update_fields=['is_active'])


# ──────────────────────────────────────────────
# Gestion des admins hôpitaux (admin général)
# ──────────────────────────────────────────────

class AdminHopitalListCreateView(generics.ListCreateAPIView):
    """Liste et création des admins hôpitaux (admin général uniquement)."""

    permission_classes = [IsAdminGeneral]

    def get_queryset(self):
        return User.objects.filter(role='admin_hopital').select_related('hopital')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AdminHopitalCreateSerializer
        return AdminHopitalListSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        
        # Envoi de l'email pour configuration du mot de passe
        token = generate_secure_token(user.pk)
        send_account_created_email(user, reset_token=token)

        from notifications.utils import create_notification
        create_notification(
            user=user,
            type='compte_cree',
            message=f"Bienvenue {user.first_name} ! Votre compte administrateur d'hôpital a été créé.",
        )


class AdminHopitalDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Détail, modification et désactivation d'un admin hôpital (admin général)."""

    permission_classes = [IsAdminGeneral]
    lookup_field = 'pk'

    def get_queryset(self):
        return User.objects.filter(role='admin_hopital').select_related('hopital')

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return AdminHopitalUpdateSerializer
        return AdminHopitalListSerializer

    def perform_destroy(self, instance):
        """Désactivation au lieu de suppression."""
        instance.is_active = False
        instance.save(update_fields=['is_active'])


# ──────────────────────────────────────────────
# Import CSV de médecins
# ──────────────────────────────────────────────

class MedecinCSVImportView(APIView):
    """Import de médecins via fichier CSV."""

    permission_classes = [IsAdminGeneralOrAdminHopital]
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = MedecinCSVImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        fichier = serializer.validated_data['fichier']

        try:
            decoded_file = fichier.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response(
                {'error': "Le fichier doit être encodé en UTF-8."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reader = csv.DictReader(io.StringIO(decoded_file), delimiter=';')
        required_columns = {'email', 'first_name', 'last_name', 'telephone', 'date_naissance', 'sexe', 'numero_ordre'}

        if not required_columns.issubset(set(reader.fieldnames or [])):
            return Response(
                {'error': f"Colonnes manquantes. Colonnes requises : {', '.join(sorted(required_columns))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultats = {'crees': 0, 'erreurs': []}

        for i, row in enumerate(reader, start=2):
            try:
                # Vérifier que l'email n'existe pas déjà
                if User.objects.filter(email=row['email']).exists():
                    resultats['erreurs'].append(f"Ligne {i}: Email {row['email']} existe déjà.")
                    continue

                if Medecin.objects.filter(numero_ordre=row['numero_ordre']).exists():
                    resultats['erreurs'].append(f"Ligne {i}: Numéro d'ordre {row['numero_ordre']} existe déjà.")
                    continue

                # Déterminer l'hôpital
                if request.user.role == 'admin_hopital':
                    hopital_id = request.user.hopital_id
                else:
                    hopital_id = row.get('hopital_id')
                    if not hopital_id:
                        resultats['erreurs'].append(f"Ligne {i}: hopital_id manquant pour l'admin général.")
                        continue

                password = get_random_string(length=12)

                user = User.objects.create_user(
                    email=row['email'],
                    password=password,
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    telephone=row['telephone'],
                    date_naissance=row['date_naissance'],
                    sexe=row['sexe'],
                    role='medecin',
                    hopital_id=hopital_id,
                    is_active=True,
                    is_email_verified=True,
                )

                Medecin.objects.create(
                    user=user,
                    numero_ordre=row['numero_ordre'],
                    biographie=row.get('biographie', ''),
                )

                send_account_created_email(user, password)
                resultats['crees'] += 1

            except Exception as e:
                resultats['erreurs'].append(f"Ligne {i}: {str(e)}")

        return Response(resultats, status=status.HTTP_200_OK)


class MedecinCSVTemplateView(APIView):
    """Téléchargement du modèle CSV pour l'import de médecins."""

    permission_classes = [IsAdminGeneralOrAdminHopital]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="modele_import_medecins.csv"'
        response.write('\ufeff')  # BOM pour Excel

        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'email', 'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe', 'numero_ordre', 'biographie', 'hopital_id',
        ])
        writer.writerow([
            'exemple@email.com', 'Jean', 'Dupont', '+22990000000',
            '1980-01-15', 'M', 'MED-001', 'Spécialiste en cardiologie', '1',
        ])

        return response
