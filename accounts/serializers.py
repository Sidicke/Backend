from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Patient, Medecin, Laborantin

User = get_user_model()


# ──────────────────────────────────────────────
# Serializers de base pour les profils
# ──────────────────────────────────────────────

class PatientProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil patient (champs spécifiques)."""

    class Meta:
        model = Patient
        fields = [
            'contact_urgence_nom', 'contact_urgence_tel',
            'groupe_sanguin', 'allergies', 'numero_secu',
        ]


class MedecinProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil médecin (champs spécifiques)."""

    class Meta:
        model = Medecin
        fields = ['numero_ordre', 'biographie', 'statut']
        read_only_fields = ['numero_ordre']


class LaborantinProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil laborantin (champs spécifiques)."""

    class Meta:
        model = Laborantin
        fields = ['laboratoire']


# ──────────────────────────────────────────────
# Inscription patient
# ──────────────────────────────────────────────

class PatientRegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un patient."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    contact_urgence_nom = serializers.CharField(max_length=150, required=False, allow_blank=True)
    contact_urgence_tel = serializers.CharField(max_length=20, required=False, allow_blank=True)
    sexe = serializers.ChoiceField(choices=User.Sexe.choices, required=False, default='M')

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe',
            'contact_urgence_nom', 'contact_urgence_tel',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Les mots de passe ne correspondent pas.'})
        
        # Validation et formatage du téléphone
        from .twilio_utils import validate_and_format_benin_phone
        tel = attrs.get('telephone')
        formatted_tel = validate_and_format_benin_phone(tel)
        if not formatted_tel:
            raise serializers.ValidationError({
                'telephone': "Le numéro de téléphone doit comporter 10 chiffres et commencer par '01'."
            })
        attrs['telephone'] = formatted_tel
            
        return attrs

    def create(self, validated_data):
        contact_urgence_nom = validated_data.pop('contact_urgence_nom', '')
        contact_urgence_tel = validated_data.pop('contact_urgence_tel', '')
        validated_data.pop('password_confirm', None)

        # Créer l'utilisateur (inactif, email non vérifié)
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            telephone=validated_data['telephone'],
            date_naissance=validated_data.get('date_naissance'),
            sexe=validated_data.get('sexe', 'M'),
            role='patient',
            is_active=True,           # TODO: remettre à False quand on réactive la confirmation email
            is_email_verified=True,   # TODO: remettre à False quand on réactive la confirmation email
        )

        # Créer le profil patient
        Patient.objects.create(
            user=user,
            contact_urgence_nom=contact_urgence_nom,
            contact_urgence_tel=contact_urgence_tel,
        )

        return user


# ──────────────────────────────────────────────
# Profil utilisateur connecté (me)
# ──────────────────────────────────────────────

class UserMeSerializer(serializers.ModelSerializer):
    """Serializer pour GET/PUT du profil de l'utilisateur connecté."""

    patient_profile = PatientProfileSerializer(required=False)
    medecin_profile = MedecinProfileSerializer(required=False)
    laborantin_profile = LaborantinProfileSerializer(required=False)
    hopital_nom = serializers.CharField(source='hopital.nom', read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe', 'role', 'adresse', 'photo',
            'is_active', 'is_email_verified', 'date_joined', 'last_login',
            'hopital', 'hopital_nom',
            'patient_profile', 'medecin_profile', 'laborantin_profile',
        ]
        read_only_fields = [
            'id', 'email', 'role', 'is_active', 'is_email_verified',
            'date_joined', 'last_login', 'hopital',
        ]

    def update(self, instance, validated_data):
        # Mise à jour des profils imbriqués
        patient_data = validated_data.pop('patient_profile', None)
        medecin_data = validated_data.pop('medecin_profile', None)
        laborantin_data = validated_data.pop('laborantin_profile', None)

        # Mise à jour des champs utilisateur
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Mise à jour du profil patient
        if patient_data and hasattr(instance, 'patient_profile'):
            for attr, value in patient_data.items():
                setattr(instance.patient_profile, attr, value)
            instance.patient_profile.save()

        # Mise à jour du profil médecin
        if medecin_data and hasattr(instance, 'medecin_profile'):
            for attr, value in medecin_data.items():
                setattr(instance.medecin_profile, attr, value)
            instance.medecin_profile.save()

        # Mise à jour du profil laborantin
        if laborantin_data and hasattr(instance, 'laborantin_profile'):
            for attr, value in laborantin_data.items():
                setattr(instance.laborantin_profile, attr, value)
            instance.laborantin_profile.save()

        return instance


# ──────────────────────────────────────────────
# Création de médecin (par admin)
# ──────────────────────────────────────────────

class MedecinCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un médecin par un admin."""

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    telephone = serializers.CharField(max_length=20)
    date_naissance = serializers.DateField(required=False, allow_null=True)
    sexe = serializers.ChoiceField(choices=User.Sexe.choices, required=False, default='M')
    numero_ordre = serializers.CharField(max_length=100, required=False, allow_blank=True)
    biographie = serializers.CharField(required=False, allow_blank=True)
    hopital = serializers.IntegerField(required=False, help_text="ID de l'hôpital (obligatoire pour admin_general)")
    service_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True,
        help_text="Liste des ID de services à associer immédiatement au médecin."
    )

    class Meta:
        model = Medecin
        fields = [
            'email', 'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe', 'hopital',
            'numero_ordre', 'biographie', 'service_ids',
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value

    def validate(self, attrs):
        request = self.context['request']
        user = request.user

        # L'admin hôpital ne peut créer que pour son propre hôpital
        if user.role == 'admin_hopital':
            if 'hopital' in attrs and attrs['hopital'] != user.hopital_id:
                raise serializers.ValidationError(
                    {'hopital': "Vous ne pouvez créer des médecins que pour votre propre hôpital."}
                )
            attrs['hopital'] = user.hopital_id

        # L'admin général doit préciser l'hôpital
        if user.role == 'admin_general' and 'hopital' not in attrs:
            raise serializers.ValidationError(
                {'hopital': "L'hôpital est obligatoire pour la création par l'admin général."}
            )

        # Validation et formatage du téléphone
        from .twilio_utils import validate_and_format_benin_phone
        tel = attrs.get('telephone')
        formatted_tel = validate_and_format_benin_phone(tel)
        if not formatted_tel:
            raise serializers.ValidationError({
                'telephone': "Le numéro de téléphone doit comporter 10 chiffres et commencer par '01'."
            })
        attrs['telephone'] = formatted_tel

        return attrs

    def create(self, validated_data):
        from django.utils.crypto import get_random_string
        from .utils import send_account_created_email
        from hopitaux.models import MedecinService

        hopital_id = validated_data.pop('hopital')
        service_ids = validated_data.pop('service_ids', [])
        password = get_random_string(length=12)

        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            telephone=validated_data['telephone'],
            date_naissance=validated_data.get('date_naissance'),
            sexe=validated_data.get('sexe', 'M'),
            role='medecin',
            hopital_id=hopital_id,
            is_active=True,
            is_email_verified=True,
        )

        numero_ordre = validated_data.get('numero_ordre', '')
        if not numero_ordre:
            numero_ordre = f"ORD-{get_random_string(length=8).upper()}"

        medecin = Medecin.objects.create(
            user=user,
            numero_ordre=numero_ordre,
            biographie=validated_data.get('biographie', ''),
        )

        for s_id in service_ids:
            MedecinService.objects.create(medecin=medecin, service_id=s_id)

        # Envoyer l'email avec le mot de passe
        send_account_created_email(user, password)

        return medecin

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'numero_ordre': instance.numero_ordre,
            'email': instance.user.email,
            'first_name': instance.user.first_name,
            'last_name': instance.user.last_name,
            'telephone': instance.user.telephone,
            'sexe': instance.user.sexe,
            'hopital': instance.user.hopital_id,
        }


class MedecinListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste publique des médecins."""

    id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    telephone = serializers.CharField(source='user.telephone', read_only=True)
    date_naissance = serializers.DateField(source='user.date_naissance', read_only=True)
    sexe = serializers.CharField(source='user.sexe', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    adresse = serializers.CharField(source='user.adresse', read_only=True, default='')
    hopital = serializers.PrimaryKeyRelatedField(source='user.hopital', read_only=True)
    hopital_nom = serializers.CharField(source='user.hopital.nom', read_only=True, default=None)
    photo = serializers.ImageField(source='user.photo', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    is_email_verified = serializers.BooleanField(source='user.is_email_verified', read_only=True, default=False)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    last_login = serializers.DateTimeField(source='user.last_login', read_only=True)

    class Meta:
        model = Medecin
        fields = [
            'id', 'email', 'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe', 'role', 'adresse',
            'hopital', 'hopital_nom', 'photo',
            'is_active', 'is_email_verified', 'date_joined', 'last_login',
            'numero_ordre', 'biographie', 'statut',
        ]


class MedecinUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'un médecin par un admin."""

    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    telephone = serializers.CharField(source='user.telephone', required=False)
    date_naissance = serializers.DateField(source='user.date_naissance', required=False)
    sexe = serializers.ChoiceField(source='user.sexe', choices=User.Sexe.choices, required=False)
    adresse = serializers.CharField(source='user.adresse', required=False)

    class Meta:
        model = Medecin
        fields = [
            'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe', 'adresse',
            'biographie', 'statut',
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        if user_data:
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ──────────────────────────────────────────────
# Création de laborantin (par admin)
# ──────────────────────────────────────────────

class LaborantinCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un laborantin par un admin."""

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    telephone = serializers.CharField(max_length=20)
    date_naissance = serializers.DateField()
    sexe = serializers.ChoiceField(choices=User.Sexe.choices)
    hopital = serializers.IntegerField(required=False, help_text="ID de l'hôpital (obligatoire pour admin_general)")

    class Meta:
        model = Laborantin
        fields = [
            'email', 'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe', 'hopital', 'laboratoire',
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value

    def validate(self, attrs):
        request = self.context['request']
        user = request.user

        if user.role == 'admin_hopital':
            if 'hopital' in attrs and attrs['hopital'] != user.hopital_id:
                raise serializers.ValidationError(
                    {'hopital': "Vous ne pouvez créer des laborantins que pour votre propre hôpital."}
                )
            attrs['hopital'] = user.hopital_id

        if user.role == 'admin_general' and 'hopital' not in attrs:
            raise serializers.ValidationError(
                {'hopital': "L'hôpital est obligatoire pour la création par l'admin général."}
            )

        # Validation et formatage du téléphone
        from .twilio_utils import validate_and_format_benin_phone
        tel = attrs.get('telephone')
        formatted_tel = validate_and_format_benin_phone(tel)
        if not formatted_tel:
            raise serializers.ValidationError({
                'telephone': "Le numéro de téléphone doit comporter 10 chiffres et commencer par '01'."
            })
        attrs['telephone'] = formatted_tel

        return attrs

    def create(self, validated_data):
        from django.utils.crypto import get_random_string
        from .utils import send_account_created_email

        hopital_id = validated_data.pop('hopital')
        password = get_random_string(length=12)

        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            telephone=validated_data['telephone'],
            date_naissance=validated_data['date_naissance'],
            sexe=validated_data['sexe'],
            role='laborantin',
            hopital_id=hopital_id,
            is_active=True,
            is_email_verified=True,
        )

        laborantin = Laborantin.objects.create(
            user=user,
            laboratoire=validated_data.get('laboratoire', ''),
        )

        send_account_created_email(user, password)

        return laborantin


class LaborantinListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des laborantins."""

    id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    telephone = serializers.CharField(source='user.telephone', read_only=True)
    sexe = serializers.CharField(source='user.sexe', read_only=True)
    hopital = serializers.PrimaryKeyRelatedField(source='user.hopital', read_only=True)
    hopital_nom = serializers.CharField(source='user.hopital.nom', read_only=True, default=None)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)

    class Meta:
        model = Laborantin
        fields = [
            'id', 'user_id', 'email', 'first_name', 'last_name', 'telephone',
            'sexe', 'hopital', 'hopital_nom', 'laboratoire', 'is_active',
        ]


class LaborantinUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'un laborantin par un admin."""

    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    telephone = serializers.CharField(source='user.telephone', required=False)
    date_naissance = serializers.DateField(source='user.date_naissance', required=False)
    sexe = serializers.ChoiceField(source='user.sexe', choices=User.Sexe.choices, required=False)
    adresse = serializers.CharField(source='user.adresse', required=False)

    class Meta:
        model = Laborantin
        fields = [
            'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe', 'adresse', 'laboratoire',
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        if user_data:
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ──────────────────────────────────────────────
# Gestion des patients (par admin général)
# ──────────────────────────────────────────────

class PatientListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des patients (admin général)."""

    id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    telephone = serializers.CharField(source='user.telephone', read_only=True)
    sexe = serializers.CharField(source='user.sexe', read_only=True)
    is_active = serializers.BooleanField(source='user.is_active', read_only=True)
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'user_id', 'email', 'first_name', 'last_name', 'telephone',
            'sexe', 'contact_urgence_nom', 'contact_urgence_tel',
            'groupe_sanguin', 'allergies', 'numero_secu',
            'is_active', 'date_joined',
        ]


class PatientUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un patient par l'admin général."""

    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    telephone = serializers.CharField(source='user.telephone', required=False)

    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'telephone',
            'contact_urgence_nom', 'contact_urgence_tel',
            'groupe_sanguin', 'allergies', 'numero_secu',
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        if user_data:
            instance.user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ──────────────────────────────────────────────
# Gestion des admins hôpitaux (par admin général)
# ──────────────────────────────────────────────

class AdminHopitalCreateSerializer(serializers.Serializer):
    """Serializer pour la création d'un admin hôpital par l'admin général."""

    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    telephone = serializers.CharField(max_length=20)
    date_naissance = serializers.DateField()
    sexe = serializers.ChoiceField(choices=User.Sexe.choices)
    hopital = serializers.IntegerField(help_text="ID de l'hôpital")

    def validate(self, attrs):
        # Validation et formatage du téléphone
        from .twilio_utils import validate_and_format_benin_phone
        tel = attrs.get('telephone')
        formatted_tel = validate_and_format_benin_phone(tel)
        if not formatted_tel:
            raise serializers.ValidationError({
                'telephone': "Le numéro de téléphone doit comporter 10 chiffres et commencer par '01'."
            })
        attrs['telephone'] = formatted_tel
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un utilisateur avec cet email existe déjà.")
        return value

    def create(self, validated_data):
        from django.utils.crypto import get_random_string
        from .utils import send_account_created_email

        password = get_random_string(length=12)

        user = User.objects.create_user(
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            telephone=validated_data['telephone'],
            date_naissance=validated_data['date_naissance'],
            sexe=validated_data['sexe'],
            role='admin_hopital',
            hopital_id=validated_data['hopital'],
            is_active=True,
            is_email_verified=True,
        )

        send_account_created_email(user, password)

        return user


class AdminHopitalListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des admins hôpitaux."""

    hopital_nom = serializers.CharField(source='hopital.nom', read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe', 'hopital', 'hopital_nom',
            'is_active', 'date_joined',
        ]


class AdminHopitalUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la modification d'un admin hôpital."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'telephone',
            'date_naissance', 'sexe', 'adresse', 'hopital',
        ]


# ──────────────────────────────────────────────
# Import CSV de médecins
# ──────────────────────────────────────────────

class MedecinCSVImportSerializer(serializers.Serializer):
    """Serializer pour l'import CSV de médecins."""

    fichier = serializers.FileField(help_text="Fichier CSV contenant les médecins à importer.")
