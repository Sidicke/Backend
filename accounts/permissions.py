from rest_framework.permissions import BasePermission


class IsAdminGeneral(BasePermission):
    """Autorise uniquement l'administrateur général."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin_general'
        )


class IsAdminHopital(BasePermission):
    """Autorise uniquement l'administrateur d'hôpital."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin_hopital'
        )


class IsAdminGeneralOrAdminHopital(BasePermission):
    """Autorise l'admin général ou l'admin hôpital."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin_general', 'admin_hopital')
        )


class IsMedecin(BasePermission):
    """Autorise uniquement les médecins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'medecin'
        )


class IsMedecinOrAdminGeneral(BasePermission):
    """Autorise l'admin général ou les médecins."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin_general', 'medecin')
        )


class IsPatient(BasePermission):
    """Autorise uniquement les patients."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'patient'
        )


class IsOwnerOrAdmin(BasePermission):
    """Autorise le propriétaire de l'objet ou un administrateur."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin_general':
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user
