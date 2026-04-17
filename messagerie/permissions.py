from rest_framework.permissions import BasePermission


class IsConsultationParticipant(BasePermission):
    """Vérifie que l'utilisateur est le patient ou le médecin de la consultation."""

    def has_permission(self, request, view):
        consultation_id = (
            request.data.get('consultation')
            or request.query_params.get('consultation')
        )
        if not consultation_id:
            return True  # La vue gérera le filtrage

        from rendezvous.models import Consultation
        try:
            consultation = Consultation.objects.select_related(
                'rendez_vous__patient__user', 'rendez_vous__medecin__user'
            ).get(pk=consultation_id)
        except Consultation.DoesNotExist:
            return False

        rdv = consultation.rendez_vous
        return request.user.pk in (rdv.patient.user_id, rdv.medecin.user_id)


class IsMessageDestinataire(BasePermission):
    """Seul le destinataire peut marquer un message comme lu."""

    def has_object_permission(self, request, view, obj):
        return obj.destinataire_id == request.user.pk
