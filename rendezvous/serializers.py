from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from accounts.models import Medecin, Patient
from .models import Disponibilite, RendezVous, Consultation, PreEnregistrement


class PreEnregistrementSerializer(serializers.ModelSerializer):
    """Serializer pour le formulaire de préenregistrement clinique du patient."""
    class Meta:
        model = PreEnregistrement
        fields = [
            'symptomes_principaux', 'debut_symptomes', 
            'traitements_en_cours', 'observations', 
            'soumis_le', 'mis_a_jour_le'
        ]
        read_only_fields = ['soumis_le', 'mis_a_jour_le']


# ──────────────────────────────────────────────
# Disponibilités
# ──────────────────────────────────────────────

class DisponibiliteSerializer(serializers.ModelSerializer):
    """Serializer pour les plages de disponibilité."""

    medecin_nom = serializers.CharField(source='medecin.user.get_full_name', read_only=True)
    jour_semaine_display = serializers.CharField(source='get_jour_semaine_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Disponibilite
        fields = [
            'id', 'medecin', 'medecin_nom', 'type', 'type_display',
            'jour_semaine', 'jour_semaine_display', 'date_specifique',
            'heure_debut', 'heure_fin', 'is_active', 'date_creation',
        ]
        read_only_fields = ['id', 'date_creation']

    def validate(self, attrs):
        type_dispo = attrs.get('type', getattr(self.instance, 'type', None))
        jour = attrs.get('jour_semaine', getattr(self.instance, 'jour_semaine', None))
        date_spec = attrs.get('date_specifique', getattr(self.instance, 'date_specifique', None))
        heure_debut = attrs.get('heure_debut', getattr(self.instance, 'heure_debut', None))
        heure_fin = attrs.get('heure_fin', getattr(self.instance, 'heure_fin', None))

        # Validation type récurrent → jour_semaine obligatoire
        if type_dispo == 'recurrent' and jour is None:
            raise serializers.ValidationError(
                {'jour_semaine': "Le jour de la semaine est obligatoire pour une plage récurrente."}
            )

        # Validation exception/indisponible → date_specifique obligatoire
        if type_dispo in ('exception', 'indisponible') and date_spec is None:
            raise serializers.ValidationError(
                {'date_specifique': "La date spécifique est obligatoire pour une exception ou indisponibilité."}
            )

        # Heure de fin > heure de début
        if heure_debut and heure_fin and heure_fin <= heure_debut:
            raise serializers.ValidationError(
                {'heure_fin': "L'heure de fin doit être après l'heure de début."}
            )

        # Vérification des chevauchements
        medecin = attrs.get('medecin', getattr(self.instance, 'medecin', None))
        if medecin and heure_debut and heure_fin:
            queryset = Disponibilite.objects.filter(
                medecin=medecin, is_active=True,
                heure_debut__lt=heure_fin, heure_fin__gt=heure_debut,
            )

            if type_dispo == 'recurrent' and jour:
                queryset = queryset.filter(type='recurrent', jour_semaine=jour)
            elif date_spec:
                queryset = queryset.filter(date_specifique=date_spec)
            else:
                queryset = queryset.none()

            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "Cette plage chevauche une disponibilité existante pour ce médecin."
                )

        return attrs


class DisponibiliteCreateSerializer(DisponibiliteSerializer):
    """Serializer pour la création — le médecin est déduit de l'utilisateur connecté."""

    class Meta(DisponibiliteSerializer.Meta):
        read_only_fields = ['id', 'date_creation', 'medecin']


# ──────────────────────────────────────────────
# Créneaux libres (lecture seule)
# ──────────────────────────────────────────────

class CreneauSerializer(serializers.Serializer):
    """Serializer pour un créneau avec son statut (libre, occupé, indisponible)."""

    date = serializers.DateField()
    heure_debut = serializers.TimeField()
    heure_fin = serializers.TimeField()
    statut = serializers.ChoiceField(
        choices=['libre', 'occupe', 'indisponible'],
        default='libre',
    )


# ──────────────────────────────────────────────
# Rendez-vous
# ──────────────────────────────────────────────

class RendezVousSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des rendez-vous."""

    patient_nom = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    medecin_nom = serializers.CharField(source='medecin.user.get_full_name', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    has_consultation = serializers.SerializerMethodField()
    consultation_id = serializers.SerializerMethodField()
    pre_enregistrement = PreEnregistrementSerializer(read_only=True)

    class Meta:
        model = RendezVous
        fields = [
            'id', 'patient', 'patient_nom',            'medecin', 'medecin_nom',
            'date_heure', 'duree', 'motif', 'statut',
            'statut_display', 'commentaire_annulation', 'cree_le', 'modifie_le',
            'has_consultation', 'consultation_id', 'pre_enregistrement',
        ]
        read_only_fields = [
            'id', 'patient', 'duree', 'statut',
            'commentaire_annulation', 'cree_le', 'modifie_le',
        ]

    def get_has_consultation(self, obj):
        return hasattr(obj, 'consultation')

    def get_consultation_id(self, obj):
        if hasattr(obj, 'consultation'):
            return obj.consultation.pk
        return None


class RendezVousCreateSerializer(serializers.Serializer):
    """Serializer pour la prise de rendez-vous par un patient."""

    medecin = serializers.IntegerField()
    date_heure = serializers.DateTimeField()
    motif = serializers.CharField(required=False, default='', allow_blank=True)

    def validate_medecin(self, value):
        try:
            medecin = Medecin.objects.get(pk=value, statut='actif', user__is_active=True)
        except Medecin.DoesNotExist:
            raise serializers.ValidationError("Médecin introuvable ou inactif.")
        # Stocker pour éviter un second SELECT dans validate()
        self._medecin_cache = medecin
        return value

    def validate_date_heure(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("La date du rendez-vous doit être dans le futur.")
        return value

    def validate(self, attrs):
        from django.db.models import F, ExpressionWrapper, DateTimeField
        
        medecin = self._medecin_cache  # Réutilise le cache (0 requête)
        date_heure = attrs['date_heure']
        duree = medecin.duree_rdv_default
        fin_rdv = date_heure + timedelta(minutes=duree)
        patient = self.context['request'].user.patient_profile

        # Vérifier conflit médecin en SQL pur (1 seule requête)
        conflit_medecin = RendezVous.objects.filter(
            medecin=medecin,
            statut__in=['en_attente', 'confirme'],
            date_heure__lt=fin_rdv,  # Le RDV existant commence avant la fin du nouveau
        ).annotate(
            fin_existant=ExpressionWrapper(
                F('date_heure') + timedelta(minutes=1) * F('duree'),
                output_field=DateTimeField(),
            )
        ).filter(
            fin_existant__gt=date_heure,  # Le RDV existant finit après le début du nouveau
        ).exists()

        if conflit_medecin:
            raise serializers.ValidationError(
                {'date_heure': "Le médecin a déjà un rendez-vous à cette heure."}
            )

        # Vérifier conflit patient en SQL pur (1 seule requête)
        conflit_patient = RendezVous.objects.filter(
            patient=patient,
            statut__in=['en_attente', 'confirme'],
            date_heure__lt=fin_rdv,
        ).annotate(
            fin_existant=ExpressionWrapper(
                F('date_heure') + timedelta(minutes=1) * F('duree'),
                output_field=DateTimeField(),
            )
        ).filter(
            fin_existant__gt=date_heure,
        ).exists()

        if conflit_patient:
            raise serializers.ValidationError(
                {'date_heure': "Vous avez déjà un rendez-vous à cette heure."}
            )

        attrs['_medecin'] = medecin
        attrs['_patient'] = patient
        attrs['_duree'] = duree
        return attrs

    def create(self, validated_data):
        rdv = RendezVous.objects.create(
            patient=validated_data['_patient'],
            medecin=validated_data['_medecin'],
            date_heure=validated_data['date_heure'],
            duree=validated_data['_duree'],
            motif=validated_data.get('motif', ''),
            statut='en_attente',
        )

        # Notifier le médecin
        from notifications.utils import create_notification
        from accounts.utils import send_appointment_request_email
        from Chatbot.whatsapp_utils import send_whatsapp_message
        create_notification(
            user=rdv.medecin.user,
            type='nouveau_rdv',
            message=(
                f"Nouveau rendez-vous de {rdv.patient.user.get_full_name()} "
                f"le {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')}."
            ),
            lien=f"/api/rendezvous/{rdv.pk}/",
        )
        
        # Envoi de l'email au médecin
        try:
            send_appointment_request_email(rdv)
        except Exception:
            pass

        # Envoi WhatsApp au patient (confirmation de la demande)
        try:
            patient_tel = rdv.patient.user.telephone
            if patient_tel:
                clean_phone = "".join(filter(str.isdigit, str(patient_tel)))
                msg = (
                    f"📅 Demande de RDV envoyée !\n\n"
                    f"Votre demande de rendez-vous avec Dr. {rdv.medecin.user.last_name} "
                    f"le {rdv.date_heure.strftime('%d/%m/%Y à %H:%M')} a été transmise.\n"
                    f"Vous recevrez une confirmation dès que le médecin aura répondu.\n"
                    f"Lieu : {rdv.medecin.user.hopital.nom}"
                )
                send_whatsapp_message(clean_phone, msg)
        except Exception:
            pass

        return rdv

    def to_representation(self, instance):
        """Utilise le serializer complet pour la réponse après création."""
        return RendezVousSerializer(instance, context=self.context).data


class CommentaireSerializer(serializers.Serializer):
    """Serializer pour les actions nécessitant un commentaire (refus, annulation)."""

    commentaire = serializers.CharField(max_length=1000)


# ──────────────────────────────────────────────
# Consultations
# ──────────────────────────────────────────────

class ConsultationSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des consultations."""

    patient_nom = serializers.CharField(source='rendez_vous.patient.user.get_full_name', read_only=True)
    medecin_nom = serializers.CharField(source='rendez_vous.medecin.user.get_full_name', read_only=True)
    date_rdv = serializers.DateTimeField(source='rendez_vous.date_heure', read_only=True)
    motif = serializers.CharField(source='rendez_vous.motif', read_only=True)

    class Meta:
        model = Consultation
        fields = [
            'rendez_vous', 'patient_nom', 'medecin_nom', 'date_rdv', 'motif',
            'compte_rendu', 'diagnostic', 'prescription',
            'date_consultation', 'est_cloture', 'date_cloture',
        ]
        read_only_fields = ['date_consultation', 'est_cloture', 'date_cloture']


class ConsultationUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour d'une consultation par le médecin."""

    class Meta:
        model = Consultation
        fields = ['compte_rendu', 'diagnostic', 'prescription']
