from rest_framework.permissions import BasePermission


class IsResultatAccessible(BasePermission):
    """Le patient propriétaire ou un médecin avec qui le résultat a été partagé."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.role == 'admin_general':
            return True
        if user.role == 'patient' and obj.patient and obj.patient.user_id == user.pk:
            return True
        if user.role == 'medecin' and obj.partages.filter(user_id=user.pk).exists():
            return True
        return False


class IsResultatOwner(BasePermission):
    """Seul le patient propriétaire du résultat."""

    def has_object_permission(self, request, view, obj):
        return (
            request.user.role == 'admin_general'
            or (request.user.role == 'patient' and obj.patient and obj.patient.user_id == request.user.pk)
        )
