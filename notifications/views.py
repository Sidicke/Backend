from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, FCMDevice
from .serializers import NotificationSerializer, FCMDeviceSerializer


class NotificationListView(generics.ListAPIView):
    """Liste des notifications de l'utilisateur connecté (triées par date descendante)."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(user=user)

        # Filtrer par statut (lu/non lu)
        lu = self.request.query_params.get('lu')
        if lu is not None:
            queryset = queryset.filter(lu=lu.lower() == 'true')

        # Filtrer par type
        notif_type = self.request.query_params.get('type')
        if notif_type:
            queryset = queryset.filter(type=notif_type)

        return queryset


class NotificationMarkReadView(APIView):
    """Marquer une notification comme lue."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification introuvable.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.lu = True
        notification.save(update_fields=['lu'])

        return Response({'message': 'Notification marquée comme lue.'}, status=status.HTTP_200_OK)


class NotificationMarkAllReadView(APIView):
    """Marquer toutes les notifications de l'utilisateur comme lues."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(user=request.user, lu=False).update(lu=True)
        return Response(
            {'message': f'{count} notification(s) marquée(s) comme lue(s).'},
            status=status.HTTP_200_OK,
        )


class FCMDeviceRegisterView(generics.CreateAPIView):
    """Enregistrer un appareil FCM pour l'utilisateur connecté."""
    serializer_class = FCMDeviceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        registration_id = serializer.validated_data['registration_id']
        FCMDevice.objects.update_or_create(
            registration_id=registration_id,
            defaults={
                'user': self.request.user,
                'device_id': serializer.validated_data.get('device_id'),
                'active': True
            }
        )
