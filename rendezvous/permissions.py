from rest_framework.permissions import BasePermission


class IsDisponibiliteOwner(BasePermission):
    """Le médecin ne peut gérer que ses propres disponibilités."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin_general':
            return True
        return (
            request.user.role == 'medecin'
            and obj.medecin.user_id == request.user.pk
        )


class IsRendezVousMedecin(BasePermission):
    """Seul le médecin du rendez-vous peut effectuer cette action."""

    def has_object_permission(self, request, view, obj):
        return obj.medecin.user_id == request.user.pk


class IsRendezVousParticipant(BasePermission):
    """Le patient ou le médecin concerné par le rendez-vous."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin_general':
            return True
        return (
            obj.patient.user_id == request.user.pk
            or obj.medecin.user_id == request.user.pk
        )


class IsConsultationParticipant(BasePermission):
    """Le patient ou le médecin de la consultation."""

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin_general':
            return True
        rdv = obj.rendez_vous
        return (
            rdv.patient.user_id == request.user.pk
            or rdv.medecin.user_id == request.user.pk
        )
