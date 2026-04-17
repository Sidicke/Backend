from rest_framework.permissions import BasePermission


class IsAdminHopitalOwner(BasePermission):
    """
    Vérifie que l'admin hôpital est bien l'admin de l'hôpital concerné.
    Utilisé pour les actions sur un hôpital spécifique.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin_general':
            return True
        if request.user.role == 'admin_hopital':
            # obj peut être un Hopital ou un objet avec un champ hopital
            hopital = obj if hasattr(obj, 'nom') else getattr(obj, 'hopital', None)
            return hopital and request.user.hopital_id == hopital.pk
        return False
