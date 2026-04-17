import random
import string
from datetime import datetime

from django.conf import settings
from django.db import models


def _generer_code_acces(hopital):
    """
    Génère un code d'accès signé par l'hôpital.
    Format : {CODE_COURT}-{YYYYMM}-{6 alphanum aléatoires}
    Exemple : CHUC-202504-A3F9K1
    """
    code_hopital = getattr(hopital, 'code_court', 'LAB') or 'LAB'
    periode = datetime.now().strftime('%Y%m')
    suffixe = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{code_hopital}-{periode}-{suffixe}"


class DemandeAnalyse(models.Model):
    """
    Demande d'analyse médicale inscrite par un laborantin.
    Cycle de vie : en_cours → cloture
    """

    class Statut(models.TextChoices):
        EN_COURS = 'en_cours', 'En cours'
        CLOTURE = 'cloture', 'Clôturé'

    # Hôpital
    hopital = models.ForeignKey(
        'hopitaux.Hopital', on_delete=models.CASCADE,
        related_name='demandes_analyse', verbose_name='hôpital',
    )
    # Laborantin responsable
    laborantin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='demandes_inscrites',
        verbose_name='laborantin',
    )
    # Lien vers le Patient inscrit sur la plateforme (optionnel)
    patient = models.ForeignKey(
        'accounts.Patient', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='demandes_analyse',
        verbose_name='patient (compte E-Santé)',
    )
    # Informations patient (obligatoires — pour les non-inscrits ou doublon de référence)
    patient_nom = models.CharField('nom du patient', max_length=100)
    patient_prenom = models.CharField('prénom du patient', max_length=100)
    patient_email = models.EmailField('email du patient')
    patient_telephone = models.CharField('téléphone du patient', max_length=20, blank=True, default='')
    patient_ddn = models.DateField('date de naissance du patient', null=True, blank=True)

    # Informations analyse
    type_analyse = models.CharField(
        'type d\'analyse', max_length=255,
        help_text='Ex: NFS, Glycémie à jeun, Bilan lipidique...',
    )

    # Statut et dates
    statut = models.CharField(
        'statut', max_length=20,
        choices=Statut.choices, default=Statut.EN_COURS,
    )
    date_inscription = models.DateTimeField('date d\'inscription', auto_now_add=True)
    date_cloture = models.DateTimeField('date de clôture', null=True, blank=True)

    # Résultat lié (créé lors de la clôture)
    resultat = models.OneToOneField(
        'Resultat', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='demande',
        verbose_name='résultat associé',
    )

    class Meta:
        verbose_name = 'Demande d\'analyse'
        verbose_name_plural = 'Demandes d\'analyse'
        ordering = ['-date_inscription']

    def __str__(self):
        return (
            f"{self.patient_prenom} {self.patient_nom} — "
            f"{self.type_analyse} ({self.get_statut_display()})"
        )


class Resultat(models.Model):
    """Résultat d'analyse médicale déposé lors de la clôture d'une demande."""

    patient = models.ForeignKey(
        'accounts.Patient', on_delete=models.CASCADE,
        related_name='resultats', verbose_name='patient',
        null=True, blank=True,
    )
    laborantin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='resultats_deposes',
        verbose_name='déposé par',
    )
    hopital = models.ForeignKey(
        'hopitaux.Hopital', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resultats',
        verbose_name='hôpital',
    )
    consultation = models.ForeignKey(
        'rendezvous.Consultation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='resultats',
        verbose_name='consultation associée',
    )
    titre = models.CharField('titre', max_length=255)
    fichier = models.FileField('fichier PDF', upload_to='resultats/%Y/%m/', blank=True, default='')
    date_analyse = models.DateField("date de l'analyse")
    date_depot = models.DateTimeField('date de dépôt', auto_now_add=True)
    code_acces = models.CharField(
        "code d'accès", max_length=50, unique=True, blank=True, editable=False,
    )
    # Pour les patients non-inscrits : stocker les infos directement
    patient_nom_externe = models.CharField('nom externe', max_length=100, blank=True, default='')
    patient_email_externe = models.EmailField('email externe', blank=True, default='')
    laboratoire = models.CharField('laboratoire', max_length=200, blank=True, default='')
    partages = models.ManyToManyField(
        'accounts.Medecin', blank=True,
        related_name='resultats_partages',
        verbose_name='partagé avec',
    )

    class Meta:
        verbose_name = 'Résultat'
        verbose_name_plural = 'Résultats'
        ordering = ['-date_depot']

    def save(self, *args, **kwargs):
        if not self.code_acces:
            self.code_acces = _generer_code_acces(self.hopital)
        super().save(*args, **kwargs)

    @property
    def patient_display_nom(self):
        """Retourne le nom du patient (inscrit ou externe)."""
        if self.patient:
            return self.patient.user.get_full_name()
        return f"{self.patient_nom_externe}".strip() or "Patient"

    def __str__(self):
        return f"{self.titre} — {self.patient_display_nom} ({self.date_analyse})"

