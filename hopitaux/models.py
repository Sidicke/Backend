from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
import re


def _generer_code_court(nom):
    """Génère un code court de 4-6 lettres majuscules à partir du nom de l'hôpital."""
    mots = re.sub(r'[^a-zA-Z\s]', '', nom).split()
    if len(mots) >= 2:
        code = ''.join(m[0].upper() for m in mots[:4])
    else:
        code = nom[:4].upper().replace(' ', '')
    return code or 'HOSP'


class Hopital(models.Model):
    """Établissement de santé enregistré sur la plateforme."""

    nom = models.CharField('nom', max_length=255)
    code_court = models.CharField(
        'code court', max_length=10, unique=True, blank=True,
        help_text="Code court unique (ex: CHUC, HZPN). Utilisé dans les codes d'accès aux résultats.",
    )
    adresse = models.TextField('adresse', blank=True, default='')
    ville = models.CharField('ville', max_length=100, blank=True, default='')
    telephone = models.CharField('téléphone', max_length=20, blank=True, default='')
    email = models.EmailField('email de contact', blank=True, default='')
    site_web = models.URLField('site web', blank=True, default='')
    description = models.TextField('description', blank=True, default='')
    logo = models.ImageField('logo', upload_to='hopitaux/logos/', blank=True, null=True)
    latitude = models.FloatField('latitude', null=True, blank=True)
    longitude = models.FloatField('longitude', null=True, blank=True)
    is_active = models.BooleanField('actif', default=True)
    date_creation = models.DateTimeField('date de création', auto_now_add=True)

    class Meta:
        verbose_name = 'Hôpital'
        verbose_name_plural = 'Hôpitaux'
        ordering = ['nom']

    def clean(self):
        """Valide les coordonnées GPS si elles sont renseignées."""
        super().clean()
        errors = {}
        if self.latitude is not None and not (-90 <= self.latitude <= 90):
            errors['latitude'] = 'La latitude doit être comprise entre -90 et 90.'
        if self.longitude is not None and not (-180 <= self.longitude <= 180):
            errors['longitude'] = 'La longitude doit être comprise entre -180 et 180.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.code_court:
            base = _generer_code_court(self.nom)
            # Garantir l'unicité si collision
            code = base
            n = 1
            while Hopital.objects.filter(code_court=code).exclude(pk=self.pk).exists():
                code = f"{base}{n}"
                n += 1
            self.code_court = code
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class Service(models.Model):
    """Service médical / spécialité (entité globale)."""

    nom = models.CharField('nom', max_length=100, unique=True)
    description = models.TextField('description', blank=True, default='')
    icone = models.CharField('icône', max_length=100, blank=True, default='',
                             help_text="Classe CSS, emoji ou nom d'icône")
    image = models.ImageField('image', upload_to='services/images/', blank=True, null=True)
    is_active = models.BooleanField('actif', default=True)
    date_creation = models.DateTimeField('date de création', auto_now_add=True)

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class HopitalService(models.Model):
    """Association entre un hôpital et un service qu'il propose."""

    hopital = models.ForeignKey(Hopital, on_delete=models.CASCADE, related_name='hopital_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_hopitaux')
    description_locale = models.TextField('description locale', blank=True, default='')
    date_ajout = models.DateTimeField('date d\'ajout', auto_now_add=True)

    class Meta:
        verbose_name = 'Service d\'hôpital'
        verbose_name_plural = 'Services d\'hôpitaux'
        unique_together = ('hopital', 'service')

    def __str__(self):
        return f"{self.hopital.nom} — {self.service.nom}"


class MedecinService(models.Model):
    """Association entre un médecin et un service qu'il exerce."""

    medecin = models.ForeignKey(
        'accounts.Medecin', on_delete=models.CASCADE, related_name='medecin_services'
    )
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_medecins')
    date_ajout = models.DateTimeField('date d\'ajout', auto_now_add=True)

    class Meta:
        verbose_name = 'Service du médecin'
        verbose_name_plural = 'Services des médecins'
        unique_together = ('medecin', 'service')

    def __str__(self):
        return f"Dr. {self.medecin.user.get_full_name()} — {self.service.nom}"


class DemandeAjoutService(models.Model):
    """Demande d'ajout d'un service à un hôpital, soumise par l'admin hôpital."""

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        VALIDE = 'valide', 'Validé'
        REFUSE = 'refuse', 'Refusé'

    hopital = models.ForeignKey(
        Hopital, on_delete=models.CASCADE, related_name='demandes_service'
    )
    # Si le service existe déjà dans la base globale
    service_existant = models.ForeignKey(
        Service, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='demandes',
        verbose_name='service existant',
    )
    # Si l'admin hôpital propose un nouveau service
    nom_nouveau_service = models.CharField(
        'nom du nouveau service', max_length=100, blank=True, default=''
    )
    description_nouveau_service = models.TextField(
        'description du nouveau service', blank=True, default=''
    )
    statut = models.CharField(
        'statut', max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE
    )
    date_demande = models.DateTimeField('date de la demande', auto_now_add=True)
    date_traitement = models.DateTimeField('date de traitement', null=True, blank=True)
    commentaire = models.TextField('commentaire', blank=True, default='')
    traite_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='demandes_traitees',
        verbose_name='traité par',
    )
    demande_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='demandes_soumises',
        verbose_name='demandé par',
    )

    class Meta:
        verbose_name = 'Demande d\'ajout de service'
        verbose_name_plural = 'Demandes d\'ajout de service'
        ordering = ['-date_demande']

    def __str__(self):
        service_nom = self.service_existant.nom if self.service_existant else self.nom_nouveau_service
        return f"{self.hopital.nom} — {service_nom} ({self.get_statut_display()})"
