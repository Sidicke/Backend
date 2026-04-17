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

    return notification
