from rest_framework import serializers

from accounts.models import Medecin, Patient
from .models import DemandeAnalyse, Resultat


# ──────────────────────────────────────────────
# DemandeAnalyse
# ──────────────────────────────────────────────

class DemandeAnalyseSerializer(serializers.ModelSerializer):
    """Lecture d'une demande d'analyse."""

    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    laborantin_nom = serializers.CharField(source='laborantin.get_full_name', read_only=True, default=None)
    hopital_nom = serializers.CharField(source='hopital.nom', read_only=True)
    resultat_code = serializers.CharField(source='resultat.code_acces', read_only=True, default=None)

    class Meta:
        model = DemandeAnalyse
        fields = [
            'id', 'hopital', 'hopital_nom',
            'laborantin', 'laborantin_nom',
            'patient',
            'patient_nom', 'patient_prenom', 'patient_email', 'patient_telephone', 'patient_ddn',
            'type_analyse',
            'statut', 'statut_display',
            'date_inscription', 'date_cloture',
            'resultat', 'resultat_code',
        ]
        read_only_fields = ['id', 'laborantin', 'hopital', 'statut', 'date_inscription', 'date_cloture', 'resultat']


class DemandeAnalyseCreateSerializer(serializers.ModelSerializer):
    """Création d'une nouvelle demande d'analyse par un laborantin."""

    class Meta:
        model = DemandeAnalyse
        fields = [
            'patient',
            'patient_nom', 'patient_prenom', 'patient_email', 'patient_telephone', 'patient_ddn',
            'type_analyse',
        ]

    def validate(self, attrs):
        # Si le patient est lié à la plateforme, pré-remplir les infos manquantes
        patient = attrs.get('patient')
        if patient:
            if not attrs.get('patient_nom'):
                attrs['patient_nom'] = patient.user.last_name
            if not attrs.get('patient_prenom'):
                attrs['patient_prenom'] = patient.user.first_name
            if not attrs.get('patient_email'):
                attrs['patient_email'] = patient.user.email
        # L'email est obligatoire pour envoyer le code au moment du dépôt
        if not attrs.get('patient_email'):
            raise serializers.ValidationError({'patient_email': "L'email du patient est obligatoire."})
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        hopital = user.hopital
        return DemandeAnalyse.objects.create(
            laborantin=user,
            hopital=hopital,
            statut=DemandeAnalyse.Statut.EN_COURS,
            **validated_data,
        )


class DemandeAnalyseCloturerSerializer(serializers.Serializer):
    """Payload pour clôturer une demande : dépôt du fichier PDF du résultat."""

    fichier = serializers.FileField(required=True)
    titre = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_fichier(self, value):
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Seuls les fichiers PDF sont acceptés.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10 Mo.")
        return value


# ──────────────────────────────────────────────
# Resultat
# ──────────────────────────────────────────────

class ResultatSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des résultats."""

    patient_nom = serializers.SerializerMethodField()
    laborantin_nom = serializers.CharField(source='laborantin.get_full_name', read_only=True, default=None)
    consultation_id = serializers.IntegerField(source='consultation.pk', read_only=True, default=None)
    hopital_nom = serializers.CharField(source='hopital.nom', read_only=True, default=None)
    medecins_partages = serializers.SerializerMethodField()

    class Meta:
        model = Resultat
        fields = [
            'id', 'patient', 'patient_nom', 'laborantin', 'laborantin_nom',
            'hopital', 'hopital_nom',
            'consultation', 'consultation_id', 'titre', 'fichier',
            'date_analyse', 'date_depot', 'code_acces', 'laboratoire',
            'patient_nom_externe', 'patient_email_externe',
            'medecins_partages',
        ]
        read_only_fields = ['id', 'date_depot', 'code_acces', 'laborantin', 'hopital']

    def get_patient_nom(self, obj):
        return obj.patient_display_nom

    def get_medecins_partages(self, obj):
        return [
            {'id': m.pk, 'nom': m.user.get_full_name()}
            for m in obj.partages.select_related('user').all()
        ]


class ResultatCreateSerializer(serializers.ModelSerializer):
    """Serializer pour le dépôt direct d'un résultat (accès legacy conservé)."""

    patient = serializers.IntegerField(help_text="ID du patient", required=False)

    class Meta:
        model = Resultat
        fields = [
            'patient', 'consultation', 'titre', 'fichier',
            'date_analyse', 'laboratoire',
        ]

    def validate_patient(self, value):
        try:
            Patient.objects.get(pk=value, user__is_active=True)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient introuvable ou inactif.")
        return value

    def validate_fichier(self, value):
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Seuls les fichiers PDF sont acceptés.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10 Mo.")
        return value

    def create(self, validated_data):
        patient_id = validated_data.pop('patient', None)
        user = self.context['request'].user
        hopital = user.hopital

        resultat = Resultat.objects.create(
            patient_id=patient_id,
            laborantin=user,
            hopital=hopital,
            laboratoire=validated_data.get('laboratoire', ''),
            **{k: v for k, v in validated_data.items() if k != 'laboratoire'},
        )
        return resultat


class PartageSerializer(serializers.Serializer):
    """Serializer pour partager un résultat avec un médecin."""

    medecin = serializers.IntegerField()

    def validate_medecin(self, value):
        try:
            Medecin.objects.get(pk=value, statut='actif', user__is_active=True)
        except Medecin.DoesNotExist:
            raise serializers.ValidationError("Médecin introuvable ou inactif.")
        return value


class ResultatPublicSerializer(serializers.ModelSerializer):
    """Serializer pour l'accès public via code (informations limitées)."""

    patient_nom = serializers.SerializerMethodField()

    class Meta:
        model = Resultat
        fields = [
            'id', 'patient_nom', 'titre', 'fichier',
            'date_analyse', 'date_depot', 'laboratoire', 'code_acces',
        ]

    def get_patient_nom(self, obj):
        return obj.patient_display_nom



class ResultatSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des résultats."""

    patient_nom = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    laborantin_nom = serializers.CharField(source='laborantin.get_full_name', read_only=True, default=None)
    consultation_id = serializers.IntegerField(source='consultation.pk', read_only=True, default=None)
    medecins_partages = serializers.SerializerMethodField()

    class Meta:
        model = Resultat
        fields = [
            'id', 'patient', 'patient_nom', 'laborantin', 'laborantin_nom',
            'consultation', 'consultation_id', 'titre', 'fichier',
            'date_analyse', 'date_depot', 'code_acces', 'laboratoire',
            'medecins_partages',
        ]
        read_only_fields = ['id', 'date_depot', 'code_acces', 'laborantin']

    def get_medecins_partages(self, obj):
        return [
            {'id': m.pk, 'nom': m.user.get_full_name()}
            for m in obj.partages.select_related('user').all()
        ]


class ResultatCreateSerializer(serializers.ModelSerializer):
    """Serializer pour le dépôt d'un résultat par un laborantin."""

    patient = serializers.IntegerField(help_text="ID du patient")

    class Meta:
        model = Resultat
        fields = [
            'patient', 'consultation', 'titre', 'fichier',
            'date_analyse', 'laboratoire',
        ]

    def validate_patient(self, value):
        try:
            Patient.objects.get(pk=value, user__is_active=True)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient introuvable ou inactif.")
        return value

    def validate_fichier(self, value):
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Seuls les fichiers PDF sont acceptés.")
        # Limite de taille : 10 Mo
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Le fichier ne doit pas dépasser 10 Mo.")
        return value

    def create(self, validated_data):
        patient_id = validated_data.pop('patient')
        user = self.context['request'].user

        resultat = Resultat.objects.create(
            patient_id=patient_id,
            laborantin=user,
            laboratoire=validated_data.get('laboratoire', '') or getattr(user, 'laborantin_profile', None) and user.laborantin_profile.laboratoire or '',
            **{k: v for k, v in validated_data.items() if k != 'laboratoire'},
        )

        # Envoi d'email avec le code d'accès
        from django.core.mail import send_mail
        from django.conf import settings
        patient_email = resultat.patient.user.email
        message = (
            f"Bonjour {resultat.patient.user.first_name},\n\n"
            f"Vos résultats d'analyse '{resultat.titre}' sont disponibles.\n"
            f"Votre code d'accès secret est : {resultat.code_acces}\n\n"
            f"Rendez-vous sur la plateforme pour les consulter.\n"
        )
        send_mail(
            subject="Vos résultats d'analyse - E-Santé Bénin",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[patient_email],
            fail_silently=True,
        )

        # Notifier le patient
        from notifications.utils import create_notification
        create_notification(
            user=resultat.patient.user,
            type='nouveau_resultat',
            message=f"Un nouveau résultat d'analyse « {resultat.titre} » a été déposé.",
            lien=f"/api/resultats/{resultat.pk}/",
        )

        return resultat


class PartageSerializer(serializers.Serializer):
    """Serializer pour partager un résultat avec un médecin."""

    medecin = serializers.IntegerField()

    def validate_medecin(self, value):
        try:
            Medecin.objects.get(pk=value, statut='actif', user__is_active=True)
        except Medecin.DoesNotExist:
            raise serializers.ValidationError("Médecin introuvable ou inactif.")
        return value


class ResultatPublicSerializer(serializers.ModelSerializer):
    """Serializer pour l'accès public via code (informations limitées)."""

    patient_nom = serializers.CharField(source='patient.user.get_full_name', read_only=True)

    class Meta:
        model = Resultat
        fields = [
            'id', 'patient_nom', 'titre', 'fichier',
            'date_analyse', 'date_depot', 'laboratoire',
        ]
