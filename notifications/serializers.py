from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications."""

    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'type', 'type_display', 'message', 'lu', 'date_envoi', 'lien']
        read_only_fields = ['id', 'type', 'type_display', 'message', 'date_envoi', 'lien']


class FCMDeviceSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement d'un appareil FCM."""

    class Meta:
        from .models import FCMDevice
        model = FCMDevice
        fields = ['registration_id', 'device_id']
