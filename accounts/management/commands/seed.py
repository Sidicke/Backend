"""
Commande Django : python manage.py seed
Insère les données initiales (hôpitaux, services, utilisateurs).
Idempotente : ne fait rien si la base contient déjà des utilisateurs.
Utiliser --force pour forcer même si la base n'est pas vide.
"""
import logging
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import Laborantin, Medecin, Patient
from hopitaux.models import Hopital, HopitalService, MedecinService, Service
from resultats.models import DemandeAnalyse

logger = logging.getLogger(__name__)

User = get_user_model()

# Mot de passe commun pour tous les comptes de test
SEED_PASSWORD = 'HOPITEL2025!'


class Command(BaseCommand):
    help = (
        'Insère les données initiales (hôpitaux, services, utilisateurs). '
        'Idempotente : ne fait rien si la base contient déjà des utilisateurs. '
        'Utiliser --force pour forcer le seed même si la base n\'est pas vide.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer le seed même si la base contient déjà des utilisateurs.',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Effacer toutes les données existantes avant de recharger.',
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Effacer toutes les données SAUF l\'administrateur général.',
        )
        parser.add_argument(
            '--test-data',
            action='store_true',
            help='Inclure des données de test (Hôpitaux, Médecins, Patients).',
        )

    def handle(self, *args, **options):
        self._log_separator()
        self.stdout.write(self.style.HTTP_INFO('[SEED] Demarrage de la commande seed...'))

        # ── Nettoyage ───────────────────────────────────────────────────────────
        if options['clean']:
            self.stdout.write(self.style.WARNING('[SEED] --clean activé : suppression de toutes les données...'))
            User.objects.all().delete()
            Hopital.objects.all().delete()
            Service.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('[SEED] Données nettoyées avec succès.'))

        if options['reset']:
            self.stdout.write(self.style.WARNING('[SEED] --reset activé : suppression de tout SAUF Super Admin...'))
            # Supprimer tout sauf les admins généraux (superuser ou role='admin_general')
            User.objects.exclude(role='admin_general').exclude(is_superuser=True).delete()
            Hopital.objects.all().delete()
            Service.objects.all().delete()
            from rendezvous.models import RendezVous, Consultation
            from messagerie.models import Message
            from resultats.models import Resultat
            RendezVous.objects.all().delete()
            Consultation.objects.all().delete()
            Message.objects.all().delete()
            Resultat.objects.all().delete()
            DemandeAnalyse.objects.all().delete()
            from accounts.models import Medecin, Patient, Laborantin
            Medecin.objects.all().delete()
            Patient.objects.all().delete()
            Laborantin.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS('[SEED] Base de données réinitialisée (Admins préservés).'))
            if not options['force']:
                 return # Arrêter ici si on ne veut que reset

        # ── Vérification : base vide ? ──────────────────────────────────────────
        if User.objects.exists() and not (options['force'] or options['clean']):
            self.stdout.write(
                self.style.WARNING(
                    '[SEED] [ATTENTION] La base contient deja des utilisateurs. '
                    'Seed ignoré. (utilisez --force ou --clean)'
                )
            )
            logger.warning('SEED ignoré : des utilisateurs existent déjà dans la base.')
            return

        if options['force'] and not options['clean']:
            self.stdout.write(self.style.WARNING('[SEED] --force activé : seed forcé sans nettoyage préalable.'))

        self.stdout.write('[SEED] Insertion des données initiales...\n')
        logger.info('SEED démarré.')

        # ── Hôpitaux ────────────────────────────────────────────────────────────
        h1 = self._create_hopital(
            nom='CHU de Cotonou',
            adresse='Boulevard Saint-Michel, Cotonou',
            ville='Cotonou',
            telephone='0121312345',
            email='contact@chu-cotonou.bj',
            description='Centre Hospitalier Universitaire de Cotonou',
            latitude=6.3654,
            longitude=2.4183,
        )
        h2 = self._create_hopital(
            nom='Hôpital de Zone de Porto-Novo',
            adresse='Avenue du Gouverneur, Porto-Novo',
            ville='Porto-Novo',
            telephone='0120215678',
            email='contact@hz-portonovo.bj',
            description='Hôpital de zone de référence de Porto-Novo',
            latitude=6.4969,
            longitude=2.6289,
        )
        h3 = self._create_hopital(
            nom='Hôpital de Zone de Parakou',
            adresse='Quartier Ladji Farani, Parakou',
            ville='Parakou',
            telephone='0123610123',
            email='contact@hz-parakou.bj',
            description='Hôpital de référence du Nord Bénin',
            latitude=9.3372,
            longitude=2.6303,
        )
        h4 = self._create_hopital(
            nom='Hôpital de Calavi',
            adresse='Abomey-Calavi, Route Nationale',
            ville='Abomey-Calavi',
            telephone='0121360011',
            email='contact@hopital-calavi.bj',
            description='Établissement moderne de la commune d\'Abomey-Calavi',
            latitude=6.4481,
            longitude=2.3533,
        )
        self.stdout.write(f'[SEED] [OK] Hopitaux : {h1.nom} | {h2.nom} | {h3.nom} | {h4.nom}')

        # ── Services ────────────────────────────────────────────────────────────
        services_data = [
            ('Cardiologie',       'Prise en charge des maladies cardiovasculaires', 'cardiologie'),
            ('Pédiatrie',         'Soins médicaux pour les enfants',               'pédiatrie'),
            ('Gynécologie',       'Santé de la femme et obstétrique',              'gynécologie'),
            ('Médecine Générale', 'Consultations de médecine générale',            'médecine générale'),
            ('Laboratoire',       'Analyses biologiques et médicales',             'laboratoire'),
            ('Ophtalmologie',     'Soins des yeux et de la vision',                'ophtalmologie'),
            ('Dermatologie',      'Soins de la peau et des muqueuses',             'dermatologie'),
            ('Urgences',          'Prise en charge des cas critiques 24h/24',      'urgences'),
            ('Neurologie',        'Maladies du système nerveux',                   'neurologie'),
            ('Radiologie',        'Imagerie médicale et radiographie',             'radiologie'),
        ]
        services = []
        for nom, desc, icone in services_data:
            s, created = Service.objects.update_or_create(
                nom=nom, 
                defaults={'description': desc, 'icone': icone}
            )
            services.append(s)
            
            # Associer à plusieurs hôpitaux de manière intelligente
            HopitalService.objects.get_or_create(hopital=h1, service=s)
            HopitalService.objects.get_or_create(hopital=h2, service=s)
            if nom in ['Urgences', 'Médecine Générale', 'Laboratoire']:
                HopitalService.objects.get_or_create(hopital=h3, service=s)
                HopitalService.objects.get_or_create(hopital=h4, service=s)
            
            status = '[OK] cree/mis a jour'
            self.stdout.write(f'[SEED]   Service {status} : {nom}')

        self.stdout.write(f'[SEED] [OK] {len(services)} services traites\n')

        # ── Admin Général (superuser) ────────────────────────────────────────────
        self._create_user(
            email='admin@hopitel.com',
            first_name='Administrateur',
            last_name='Général',
            telephone='0190000001',
            date_naissance=date(1985, 3, 15),
            sexe='M',
            role='admin_general',
            is_staff=True,
            is_superuser=True,
        )

        # Si l'utilisateur veut aussi des données de test
        if options.get('test_data'):
            self._insert_test_data(services)

        self.stdout.write(f'[SEED] [OK] Services traites : {len(services)}\n')
        self.stdout.write(self.style.SUCCESS('[SEED] [OK] Super Admin : admin@hopitel.com'))
        self.stdout.write(self.style.SUCCESS('[SEED] Mot de passe : ' + SEED_PASSWORD))
        
        logger.info('SEED termine avec succes.')

    def _insert_test_data(self, services):
        self.stdout.write('[SEED] Insertion des données de test (Médecins & Laborantins)...\n')
        
        # ── Hôpitaux ────────────────────────────────────────────────────────────
        h1 = Hopital.objects.get(nom='CHU de Cotonou')
        h2 = Hopital.objects.get(nom='Hôpital de Zone de Porto-Novo')
        h3 = Hopital.objects.get(nom='Hôpital de Zone de Parakou')

        # ── Médecins ─────────────────────────────────────────────────────────────
        # Dr. Kokou (CHU Cotonou - Cardiologie)
        med1 = self._create_user(
            email='dr.kokou@hopitel.com', 
            first_name='Kokou', last_name='Mensah', 
            role='medecin', hopital=h1, telephone='0190000010',
            date_naissance=date(1978, 6, 12), sexe='M'
        )
        if med1:
            m1, _ = Medecin.objects.get_or_create(user=med1, defaults={'numero_ordre': 'MED-BJ-001'})
            # Cardiologie = services[0] (basé sur l'ordre dans handle)
            MedecinService.objects.get_or_create(medecin=m1, service=Service.objects.get(nom='Cardiologie'))

        # Dr. Amina (CHU Cotonou - Gynécologie)
        med2 = self._create_user(
            email='dr.amina@hopitel.com', 
            first_name='Amina', last_name='Saliou', 
            role='medecin', hopital=h1, telephone='0190000011',
            date_naissance=date(1982, 4, 25), sexe='F'
        )
        if med2:
            m2, _ = Medecin.objects.get_or_create(user=med2, defaults={'numero_ordre': 'MED-BJ-002'})
            MedecinService.objects.get_or_create(medecin=m2, service=Service.objects.get(nom='Gynécologie'))

        # Dr. Brice (Porto-Novo - Pédiatrie)
        med3 = self._create_user(
            email='dr.brice@hopitel.com', 
            first_name='Brice', last_name='Houndé', 
            role='medecin', hopital=h2, telephone='0190000012',
            date_naissance=date(1985, 9, 30), sexe='M'
        )
        if med3:
            m3, _ = Medecin.objects.get_or_create(user=med3, defaults={'numero_ordre': 'MED-BJ-003'})
            MedecinService.objects.get_or_create(medecin=m3, service=Service.objects.get(nom='Pédiatrie'))

        # ── Laborantins ────────────────────────────────────────────────────────
        # Labo 1 (CHU Cotonou)
        lab1 = self._create_user(
            email='labo.cotonou@hopitel.com', 
            first_name='Marc', last_name='Dossou', 
            role='laborantin', hopital=h1, telephone='0190000020',
            date_naissance=date(1988, 11, 5), sexe='M'
        )
        if lab1:
            Laborantin.objects.get_or_create(user=lab1, defaults={'laboratoire': 'BioTrack Cotonou'})

        # Labo 2 (Porto-Novo)
        lab2 = self._create_user(
            email='labo.portonovo@hopitel.com', 
            first_name='Sophie', last_name='Gnon', 
            role='laborantin', hopital=h2, telephone='0190000021',
            date_naissance=date(1990, 1, 20), sexe='F'
        )
        if lab2:
            Laborantin.objects.get_or_create(user=lab2, defaults={'laboratoire': 'BioTrack Porto-Novo'})

        # ── Admin Hôpitaux ───────────────────────────────────────────────────
        # Admin CHU Cotonou
        self._create_user(
            email='admin.chu@hopitel.com', 
            first_name='Admin', last_name='CHU', 
            role='admin_hopital', hopital=h1, telephone='0190000040',
            date_naissance=date(1975, 5, 10), sexe='M'
        )

        self.stdout.write('[SEED] [OK] Données de test (Médecins, Laborantins, Admins) insérées.')

    # ── Helpers privés ───────────────────────────────────────────────────────────

    def _create_hopital(self, nom, **defaults):
        hopital, created = Hopital.objects.get_or_create(nom=nom, defaults=defaults)
        status = '[OK] cree' if created else '[EXISTANT] existant'
        self.stdout.write(f'[SEED]   Hopital {status} : {nom}')
        return hopital

    def _create_user(self, email, first_name, last_name, telephone,
                     date_naissance, sexe, role, hopital=None,
                     is_staff=False, is_superuser=False):
        if User.objects.filter(email=email).exists():
            self.stdout.write(f'[SEED]   [EXISTANT] Utilisateur existant : {email}')
            logger.debug('SEED skip user (already exists): %s', email)
            return User.objects.get(email=email)

        user = User.objects.create_user(
            email=email,
            password=SEED_PASSWORD,
            first_name=first_name,
            last_name=last_name,
            telephone=telephone,
            date_naissance=date_naissance,
            sexe=sexe,
            role=role,
            hopital=hopital,
            is_active=True,
            is_email_verified=True,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        self.stdout.write(f'[SEED]   [OK] Cree : {email} ({role})')
        logger.info('SEED created user: %s (%s)', email, role)
        return user

    def _log_separator(self):
        self.stdout.write('[SEED] ' + '-' * 55)
