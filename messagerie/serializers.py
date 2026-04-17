from rest_framework import serializers

from rendezvous.models import Consultation
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des messages."""

    expediteur_nom = serializers.CharField(source='expediteur.get_full_name', read_only=True)
    destinataire_nom = serializers.CharField(source='destinataire.get_full_name', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'consultation', 'expediteur', 'expediteur_nom',
            'destinataire', 'destinataire_nom', 'contenu',
            'date_envoi', 'lu', 'piece_jointe', 'type_message', 'audio',
        ]
        read_only_fields = [
            'id', 'expediteur', 'destinataire', 'date_envoi', 'lu',
        ]


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer pour l'envoi d'un message (lié à une consultation ou direct)."""

    class Meta:
        model = Message
        fields = ['consultation', 'destinataire', 'contenu', 'piece_jointe', 'type_message', 'audio']
        extra_kwargs = {
            'destinataire': {'required': False, 'allow_null': True},
            'contenu': {'required': False, 'allow_blank': True, 'default': ''},
        }

    def validate(self, attrs):
        consultation = attrs.get('consultation')
        destinataire = attrs.get('destinataire')
        user = self.context['request'].user
        type_msg = attrs.get('type_message', 'texte')

        # Validation : un message texte doit avoir du contenu
        if type_msg == 'texte' and not attrs.get('contenu', '').strip():
            raise serializers.ValidationError({'contenu': "Le contenu du message ne peut pas être vide."})

        # Validation : un message vocal doit avoir un fichier audio
        if type_msg == 'vocal' and not attrs.get('audio'):
            raise serializers.ValidationError({'audio': "Un fichier audio est requis pour un message vocal."})

        if consultation:
            # Message lié à une consultation
            # ── Vérifier que la consultation n'est PAS clôturée ──
            if consultation.est_cloture:
                raise serializers.ValidationError(
                    "Cette consultation est clôturée. Vous ne pouvez plus envoyer de messages."
                )

            if rdv := consultation.rendez_vous:
                if rdv.statut != 'termine':
                    raise serializers.ValidationError("Le rendez-vous associé n'est pas terminé.")
                if user.pk not in (rdv.patient.user_id, rdv.medecin.user_id):
                    raise serializers.ValidationError("Vous n'êtes pas participant de cette consultation.")

                # Définir le destinataire automatiquement si non fourni
                if not destinataire:
                    attrs['destinataire'] = rdv.medecin.user if user.pk == rdv.patient.user_id else rdv.patient.user
            else:
                raise serializers.ValidationError("Consultation invalide.")
        else:
            # Message direct (interne)
            if not destinataire:
                raise serializers.ValidationError("Vous devez spécifier un destinataire pour un message direct.")
            if destinataire == user:
                raise serializers.ValidationError("Vous ne pouvez pas vous envoyer un message à vous-même.")

        return attrs

    def create(self, validated_data):
        user = validated_data.pop('expediteur', self.context['request'].user)
        destinataire = validated_data['destinataire']
        consultation = validated_data.get('consultation')

        message = Message.objects.create(
            expediteur=user,
            **validated_data
        )

        # Notifier le destinataire
        from notifications.utils import create_notification
        msg_context = f"concernant votre consultation" if consultation else "direct"
        create_notification(
            user=destinataire,
            type='nouveau_message',
            message=f"Nouveau message de {user.get_full_name()} ({msg_context}).",
            lien=f"/api/messages/?consultation={consultation.pk if consultation else ''}",
        )

        return message


class ConversationSerializer(serializers.Serializer):
    """Serializer pour la liste des conversations (regroupées par consultation)."""

    consultation_id = serializers.IntegerField(allow_null=True)
    destinataire_id = serializers.IntegerField()
    titre = serializers.CharField()
    dernier_message = serializers.CharField()
    date_dernier_message = serializers.DateTimeField()
    non_lus = serializers.IntegerField()
    type = serializers.CharField()
    est_cloture = serializers.BooleanField()
