from django.conf import settings
from django.db import models


class Message(models.Model):
    """Message échangé entre un patient et un médecin dans le cadre d'une consultation."""

    class TypeMessage(models.TextChoices):
        TEXTE = 'texte', 'Texte'
        VOCAL = 'vocal', 'Message vocal'
        FICHIER = 'fichier', 'Fichier'

    consultation = models.ForeignKey(
        'rendezvous.Consultation', on_delete=models.CASCADE,
        related_name='messages', verbose_name='consultation',
        null=True, blank=True,
    )
    expediteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='messages_envoyes', verbose_name='expéditeur',
    )
    destinataire = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='messages_recus', verbose_name='destinataire',
    )
    contenu = models.TextField('contenu', blank=True, default='')
    type_message = models.CharField(
        'type de message', max_length=10,
        choices=TypeMessage.choices, default=TypeMessage.TEXTE,
    )
    audio = models.FileField(
        'message vocal', upload_to='messages/audio/%Y/%m/',
        blank=True, null=True,
        help_text='Fichier audio pour les messages vocaux.',
    )
    date_envoi = models.DateTimeField("date d'envoi", auto_now_add=True)
    lu = models.BooleanField('lu', default=False)
    piece_jointe = models.FileField(
        'pièce jointe', upload_to='messages/%Y/%m/', blank=True, null=True,
    )

    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['date_envoi']

    def __str__(self):
        return f"{self.expediteur.get_full_name()} → {self.destinataire.get_full_name()} ({self.date_envoi.strftime('%d/%m/%Y %H:%M')})"
