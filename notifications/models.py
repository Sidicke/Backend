from django.conf import settings
from django.db import models


class Notification(models.Model):
    """Modèle pour les notifications de la plateforme."""

    class Type(models.TextChoices):
        RAPPEL_RDV = 'rappel_rdv', 'Rappel de rendez-vous'
        NOUVEAU_RDV = 'nouveau_rdv', 'Nouveau rendez-vous'
        RDV_CONFIRME = 'rdv_confirme', 'Rendez-vous confirmé'
        RDV_REFUSE = 'rdv_refuse', 'Rendez-vous refusé'
        RDV_ANNULE = 'rdv_annule', 'Rendez-vous annulé'
        CONSULTATION_AJOUTEE = 'consultation_ajoutee', 'Consultation ajoutée'
        NOUVEAU_RESULTAT = 'nouveau_resultat', 'Nouveau résultat'
        NOUVEAU_MESSAGE = 'nouveau_message', 'Nouveau message'
        COMPTE_CREE = 'compte_cree', 'Compte créé'
        DEMANDE_SERVICE = 'demande_service', 'Demande de service'
        VALIDATION_SERVICE = 'validation_service', 'Validation de service'
        REFUS_SERVICE = 'refus_service', 'Refus de service'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='destinataire',
    )
    type = models.CharField('type', max_length=30, choices=Type.choices)
    message = models.TextField('message')
    lu = models.BooleanField('lu', default=False)
    date_envoi = models.DateTimeField('date d\'envoi', auto_now_add=True)
    lien = models.CharField('lien', max_length=500, blank=True, default='')

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-date_envoi']

    def __str__(self):
        return f"[{self.get_type_display()}] {self.user.email} - {self.message[:50]}"
