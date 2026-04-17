from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Modèle utilisateur personnalisé. Authentification par email."""

    class Role(models.TextChoices):
        PATIENT = 'patient', 'Patient'
        MEDECIN = 'medecin', 'Médecin'
        ADMIN_HOPITAL = 'admin_hopital', 'Administrateur Hôpital'
        ADMIN_GENERAL = 'admin_general', 'Administrateur Général'
        LABORANTIN = 'laborantin', 'Laborantin'

    class Sexe(models.TextChoices):
        MASCULIN = 'M', 'Masculin'
        FEMININ = 'F', 'Féminin'
        AUTRE = 'Autre', 'Autre'

    # Suppression du champ username
    username = None

    email = models.EmailField('adresse email', unique=True)
    telephone = models.CharField('téléphone', max_length=20)
    date_naissance = models.DateField('date de naissance', null=True, blank=True)
    sexe = models.CharField('sexe', max_length=10, choices=Sexe.choices)
    role = models.CharField('rôle', max_length=20, choices=Role.choices, default=Role.PATIENT)
    hopital = models.ForeignKey(
        'hopitaux.Hopital',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='personnels',
        verbose_name='hôpital de rattachement',
    )
    adresse = models.TextField('adresse', blank=True, default='')
    photo = models.ImageField('photo de profil', upload_to='photos_profil/', blank=True, null=True)
    is_email_verified = models.BooleanField('email vérifié', default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'telephone', 'sexe']

    objects = UserManager()

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"


class Patient(models.Model):
    """Profil spécifique au patient."""

    class GroupeSanguin(models.TextChoices):
        A_POSITIF = 'A+', 'A+'
        A_NEGATIF = 'A-', 'A-'
        B_POSITIF = 'B+', 'B+'
        B_NEGATIF = 'B-', 'B-'
        AB_POSITIF = 'AB+', 'AB+'
        AB_NEGATIF = 'AB-', 'AB-'
        O_POSITIF = 'O+', 'O+'
        O_NEGATIF = 'O-', 'O-'

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='patient_profile')
    contact_urgence_nom = models.CharField("nom du contact d'urgence", max_length=150)
    contact_urgence_tel = models.CharField("téléphone du contact d'urgence", max_length=20)
    groupe_sanguin = models.CharField('groupe sanguin', max_length=5, choices=GroupeSanguin.choices, blank=True, default='')
    allergies = models.TextField('allergies', blank=True, default='')
    numero_secu = models.CharField('numéro de sécurité sociale', max_length=50, blank=True, default='')

    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'

    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"


class Medecin(models.Model):
    """Profil spécifique au médecin."""

    class Statut(models.TextChoices):
        ACTIF = 'actif', 'Actif'
        INACTIF = 'inactif', 'Inactif'

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='medecin_profile')
    numero_ordre = models.CharField("numéro d'ordre professionnel", max_length=100, unique=True)
    biographie = models.TextField('biographie', blank=True, default='')
    statut = models.CharField('statut', max_length=10, choices=Statut.choices, default=Statut.ACTIF)
    duree_rdv_default = models.PositiveIntegerField(
        'durée par défaut d\'un RDV (minutes)', default=30
    )

    class Meta:
        verbose_name = 'Médecin'
        verbose_name_plural = 'Médecins'

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"


class Laborantin(models.Model):
    """Profil spécifique au laborantin."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='laborantin_profile')
    laboratoire = models.CharField('nom du laboratoire', max_length=200, blank=True, default='')

    class Meta:
        verbose_name = 'Laborantin'
        verbose_name_plural = 'Laborantins'

    def __str__(self):
        return f"Laborantin: {self.user.get_full_name()}"
