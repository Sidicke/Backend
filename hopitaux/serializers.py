from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from rest_framework import serializers

from accounts.utils import send_account_created_email
from .models import Hopital, Service, HopitalService, MedecinService, DemandeAjoutService

User = get_user_model()


# ──────────────────────────────────────────────
# Services globaux
# ──────────────────────────────────────────────

class ServiceSerializer(serializers.ModelSerializer):
    """Serializer pour les services médicaux globaux."""

    class Meta:
        model = Service
        fields = ['id', 'nom', 'description', 'icone', 'image', 'is_active', 'date_creation']
        read_only_fields = ['id', 'date_creation']


# ──────────────────────────────────────────────
# Hôpitaux
# ──────────────────────────────────────────────

class HopitalListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste publique des hôpitaux."""

    services = serializers.SerializerMethodField()

    class Meta:
        model = Hopital
        fields = [
            'id', 'nom', 'adresse', 'ville', 'telephone', 'email',
            'site_web', 'description', 'logo', 'latitude', 'longitude',
            'is_active', 'date_creation', 'services',
        ]

    def get_services(self, obj):
        """Retourne la liste des services proposés par l'hôpital."""
        return ServiceSerializer(
            Service.objects.filter(service_hopitaux__hopital=obj),
            many=True,
        ).data


class HopitalCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un hôpital + son admin_hopital."""

    # Champs de l'admin hôpital
    admin_email = serializers.EmailField(write_only=True)
    admin_first_name = serializers.CharField(max_length=150, write_only=True)
    admin_last_name = serializers.CharField(max_length=150, write_only=True)
    admin_telephone = serializers.CharField(max_length=20, write_only=True)
    admin_date_naissance = serializers.DateField(write_only=True)
    admin_sexe = serializers.ChoiceField(choices=User.Sexe.choices, write_only=True)

    # Services initiaux (liste d'IDs)
    services_initiaux = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=[],
    )

    class Meta:
        model = Hopital
        fields = [
            'id', 'nom', 'adresse', 'ville', 'telephone', 'email',
            'site_web', 'description', 'logo', 'latitude', 'longitude',
            'admin_email', 'admin_first_name', 'admin_last_name',
            'admin_telephone', 'admin_date_naissance', 'admin_sexe',
            'services_initiaux',
        ]
        read_only_fields = ['id']

    def validate_admin_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value

    def validate_services_initiaux(self, value):
        """Vérifie que tous les IDs de services existent."""
        if value:
            existants = set(Service.objects.filter(id__in=value, is_active=True).values_list('id', flat=True))
            invalides = set(value) - existants
            if invalides:
                raise serializers.ValidationError(f"Services introuvables : {list(invalides)}")
        return value

    def create(self, validated_data):
        # Extraire les données admin et services
        admin_data = {
            'email': validated_data.pop('admin_email'),
            'first_name': validated_data.pop('admin_first_name'),
            'last_name': validated_data.pop('admin_last_name'),
            'telephone': validated_data.pop('admin_telephone'),
            'date_naissance': validated_data.pop('admin_date_naissance'),
            'sexe': validated_data.pop('admin_sexe'),
        }
        services_ids = validated_data.pop('services_initiaux')

        # Créer l'hôpital
        hopital = Hopital.objects.create(**validated_data)

        # Créer le compte admin_hopital
        password = get_random_string(length=12)
        admin_user = User.objects.create_user(
            **admin_data,
            password=password,
            role='admin_hopital',
            hopital=hopital,
            is_active=True,
            is_email_verified=True,
        )

        # Associer les services initiaux
        for service_id in services_ids:
            HopitalService.objects.create(hopital=hopital, service_id=service_id)

        # Envoyer l'email avec les identifiants
        send_account_created_email(admin_user, password)

        # Notification à l'admin hôpital
        from notifications.utils import create_notification
        create_notification(
            user=admin_user,
            type='compte_cree',
            message=f"Bienvenue ! Votre compte administrateur pour l'hôpital {hopital.nom} a été créé.",
        )

        return hopital


class HopitalUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un hôpital."""

    class Meta:
        model = Hopital
        fields = [
            'nom', 'adresse', 'ville', 'telephone', 'email',
            'site_web', 'description', 'logo', 'latitude', 'longitude',
        ]


# ──────────────────────────────────────────────
# Services d'un hôpital
# ──────────────────────────────────────────────

class HopitalServiceSerializer(serializers.ModelSerializer):
    """Serializer pour l'association hôpital-service."""

    service_nom = serializers.CharField(source='service.nom', read_only=True)
    service_description = serializers.CharField(source='service.description', read_only=True)
    service_icone = serializers.CharField(source='service.icone', read_only=True)
    service_image = serializers.ImageField(source='service.image', read_only=True)

    class Meta:
        model = HopitalService
        fields = ['id', 'hopital', 'service', 'service_nom', 'service_description', 'service_icone', 'service_image', 'description_locale', 'date_ajout']
        read_only_fields = ['id', 'date_ajout']


# ──────────────────────────────────────────────
# Services d'un médecin
# ──────────────────────────────────────────────

class MedecinServiceSerializer(serializers.ModelSerializer):
    """Serializer pour l'association médecin-service."""

    service_nom = serializers.CharField(source='service.nom', read_only=True)

    class Meta:
        model = MedecinService
        fields = ['id', 'service', 'service_nom', 'date_ajout']
        read_only_fields = ['id', 'date_ajout']


class MedecinServiceCreateSerializer(serializers.Serializer):
    """Serializer pour associer un service à un médecin."""

    service = serializers.IntegerField()

    def validate_service(self, value):
        if not Service.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Service introuvable ou inactif.")
        return value


# ──────────────────────────────────────────────
# Demandes d'ajout de service
# ──────────────────────────────────────────────

class DemandeAjoutServiceSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des demandes."""

    hopital_nom = serializers.CharField(source='hopital.nom', read_only=True)
    service_existant_nom = serializers.CharField(source='service_existant.nom', read_only=True, default=None)
    demande_par_nom = serializers.CharField(source='demande_par.get_full_name', read_only=True)
    traite_par_nom = serializers.CharField(source='traite_par.get_full_name', read_only=True, default=None)

    class Meta:
        model = DemandeAjoutService
        fields = [
            'id', 'hopital', 'hopital_nom',
            'service_existant', 'service_existant_nom',
            'nom_nouveau_service', 'description_nouveau_service',
            'statut', 'date_demande', 'date_traitement',
            'commentaire', 'traite_par', 'traite_par_nom',
            'demande_par', 'demande_par_nom',
        ]


class DemandeAjoutServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'une demande d'ajout de service."""

    class Meta:
        model = DemandeAjoutService
        fields = ['service_existant', 'nom_nouveau_service', 'description_nouveau_service']

    def validate(self, attrs):
        service_existant = attrs.get('service_existant')
        nom_nouveau = attrs.get('nom_nouveau_service', '').strip()

        # Il faut soit un service existant, soit un nom de nouveau service
        if not service_existant and not nom_nouveau:
            raise serializers.ValidationError(
                "Vous devez sélectionner un service existant ou proposer un nom de nouveau service."
            )
        if service_existant and nom_nouveau:
            raise serializers.ValidationError(
                "Vous ne pouvez pas à la fois sélectionner un service existant et proposer un nouveau nom."
            )

        return attrs


class DemandeRefusSerializer(serializers.Serializer):
    """Serializer pour le refus d'une demande (commentaire optionnel)."""

    commentaire = serializers.CharField(required=False, default='', allow_blank=True)


# ──────────────────────────────────────────────
# Hôpitaux à proximité
# ──────────────────────────────────────────────

class NearbyHospitalSerializer(serializers.ModelSerializer):
    """Serializer pour la réponse de l'endpoint de proximité."""

    distance_km = serializers.FloatField(read_only=True)

    services = serializers.SerializerMethodField()

    class Meta:
        model = Hopital
        fields = [
            'id', 'nom', 'adresse', 'ville', 'telephone', 'email',
            'site_web', 'description', 'logo', 'latitude', 'longitude',
            'is_active', 'date_creation', 'distance_km', 'services',
        ]

    def get_services(self, obj):
        return ServiceSerializer(
            Service.objects.filter(service_hopitaux__hopital=obj),
            many=True,
        ).data

