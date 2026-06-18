import os
from django.conf import settings

from .models import Notification


def create_notification(user, type, message, lien=''):
    """
    Crée une notification pour un utilisateur et la diffuse via WebSocket.
    """
    notification = Notification.objects.create(
        user=user,
        type=type,
        message=message,
        lien=lien,
    )

    # Diffusion Temps Réel (WebSockets)
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from .serializers import NotificationSerializer

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_notifications_{user.pk}",
            {
                'type': 'notify',
                'notification': NotificationSerializer(notification).data
            }
        )
    except Exception:
        pass # Ne pas bloquer si Redis est HS

    # Diffusion Push (Firebase FCM)
    _send_fcm_push(user, type, message, lien)

    return notification


def _send_fcm_push(user, n_type, message, lien=''):
    """Envoie une notification push via Firebase aux appareils de l'utilisateur."""
    try:
        import firebase_admin
        from firebase_admin import messaging, credentials
        from .models import FCMDevice
        import json

        # Initialisation si nécessaire
        if not firebase_admin._apps:
            # On cherche le fichier de clé dans le dossier de configuration
            cred_path = os.path.join(settings.BASE_DIR, 'firebase-service-account.json')
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            elif os.getenv('FIREBASE_CREDENTIALS'):
                cred_dict = json.loads(os.getenv('FIREBASE_CREDENTIALS'))
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                return  # Pas de config, pas d'envoi

        tokens = list(FCMDevice.objects.filter(user=user, active=True).values_list('registration_id', flat=True))
        if not tokens:
            return

        # Construction du message
        multicast_msg = messaging.MulticastMessage(
            notification=messaging.Notification(
                title='HOPITEL',
                body=message,
            ),
            data={
                'type': n_type,
                'lien': str(lien),
            },
            tokens=tokens,
        )
        
        response = messaging.send_multicast(multicast_msg)
        print(f"FCM: {response.success_count} success, {response.failure_count} failure")
        
    except Exception as e:
        print(f"FCM Error: {e}")
