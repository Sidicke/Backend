from django.conf import settings
from django.db import models


class Disponibilite(models.Model):
    """Plage de disponibilité d'un médecin (récurrente, exception ou indisponibilité)."""

    class TypeDispo(models.TextChoices):
        RECURRENT = 'recurrent', 'Récurrent'
        EXCEPTION = 'exception', 'Exception (créneau ponctuel)'
        INDISPONIBLE = 'indisponible', 'Indisponible (congé, absence)'

    class JourSemaine(models.IntegerChoices):
        LUNDI = 1, 'Lundi'
        MARDI = 2, 'Mardi'
        MERCREDI = 3, 'Mercredi'
        JEUDI = 4, 'Jeudi'
        VENDREDI = 5, 'Vendredi'
        SAMEDI = 6, 'Samedi'
        DIMANCHE = 7, 'Dimanche'

    medecin = models.ForeignKey(
        'accounts.Medecin', on_delete=models.CASCADE, related_name='disponibilites'
    )
    type = models.CharField('type', max_length=20, choices=TypeDispo.choices, default=TypeDispo.RECURRENT)
    jour_semaine = models.IntegerField(
        'jour de la semaine', choices=JourSemaine.choices,
        null=True, blank=True,
        help_text="1=Lundi à 7=Dimanche. Obligatoire pour les plages récurrentes.",
    )
    date_specifique = models.DateField(
        'date spécifique', null=True, blank=True,
        help_text="Pour les exceptions et indisponibilités ponctuelles.",
    )
    heure_debut = models.TimeField('heure de début')
    heure_fin = models.TimeField('heure de fin')
    is_active = models.BooleanField('actif', default=True)
    date_creation = models.DateTimeField('date de création', auto_now_add=True)

    class Meta:
        verbose_name = 'Disponibilité'
        verbose_name_plural = 'Disponibilités'
        ordering = ['jour_semaine', 'heure_debut']

    def __str__(self):
        if self.type == 'recurrent':
            return f"Dr. {self.medecin.user.last_name} — {self.get_jour_semaine_display()} {self.heure_debut}-{self.heure_fin}"
        return f"Dr. {self.medecin.user.last_name} — {self.date_specifique} {self.heure_debut}-{self.heure_fin} ({self.get_type_display()})"


class RendezVous(models.Model):
    """Rendez-vous entre un patient et un médecin."""

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        CONFIRME = 'confirme', 'Confirmé'
        ANNULE = 'annule', 'Annulé'
        REFUSE = 'refuse', 'Refusé'
        TERMINE = 'termine', 'Terminé'

    patient = models.ForeignKey(
        'accounts.Patient', on_delete=models.CASCADE, related_name='rendezvous'
    )
    medecin = models.ForeignKey(
        'accounts.Medecin', on_delete=models.CASCADE, related_name='rendezvous'
    )
    date_heure = models.DateTimeField('date et heure du rendez-vous')
    duree = models.PositiveIntegerField('durée (minutes)')
    motif = models.TextField('motif', blank=True, default='')
    statut = models.CharField(
        'statut', max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE
    )
    commentaire_annulation = models.TextField(
        'motif d\'annulation/refus', blank=True, default=''
    )
    cree_le = models.DateTimeField('créé le', auto_now_add=True)
    modifie_le = models.DateTimeField('modifié le', auto_now=True)

    class Meta:
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        ordering = ['-date_heure']

    def __str__(self):
        return (
            f"RDV {self.patient.user.last_name} → Dr. {self.medecin.user.last_name} "
            f"le {self.date_heure.strftime('%d/%m/%Y %H:%M')} ({self.get_statut_display()})"
        )


class Consultation(models.Model):
    """Consultation effectuée suite à un rendez-vous terminé."""

    rendez_vous = models.OneToOneField(
        RendezVous, on_delete=models.CASCADE, primary_key=True, related_name='consultation'
    )
    compte_rendu = models.TextField('compte rendu', blank=True, default='')
    diagnostic = models.TextField('diagnostic', blank=True, default='')
    prescription = models.TextField('prescription', blank=True, default='')
    date_consultation = models.DateTimeField('date de la consultation', auto_now_add=True)
    est_cloture = models.BooleanField('est clôturée', default=False)
    date_cloture = models.DateTimeField('date de clôture', null=True, blank=True)

    class Meta:
        verbose_name = 'Consultation'
        verbose_name_plural = 'Consultations'
        ordering = ['-date_consultation']

    def __str__(self):
        return f"Consultation du {self.date_consultation.strftime('%d/%m/%Y')} — {self.rendez_vous}"


class PreEnregistrement(models.Model):
    """Préenregistrement (Intake) soumis par le patient avant la date de la consultation."""

    rendez_vous = models.OneToOneField(
        RendezVous, on_delete=models.CASCADE, primary_key=True, related_name='pre_enregistrement'
    )
    symptomes_principaux = models.TextField('symptômes principaux')
    debut_symptomes = models.DateField('début des symptômes', null=True, blank=True)
    traitements_en_cours = models.TextField('traitements en cours', blank=True, default='')
    observations = models.TextField('autres observations', blank=True, default='')
    soumis_le = models.DateTimeField('soumis le', auto_now_add=True)
    mis_a_jour_le = models.DateTimeField('mis à jour le', auto_now=True)

    class Meta:
        verbose_name = 'Préenregistrement'
        verbose_name_plural = 'Préenregistrements'

    def __str__(self):
        return f"Préenregistrement — {self.rendez_vous}"
