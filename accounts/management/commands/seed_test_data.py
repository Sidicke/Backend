from datetime import date

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accounts.models import Patient, Medecin, Laborantin
from hopitaux.models import Hopital, Service, HopitalService, MedecinService
from notifications.utils import create_notification

User = get_user_model()

PASSWORD = 'HOPITEL2025!'


class Command(BaseCommand):
    help = 'Crée des données de test : hôpitaux, services, utilisateurs de tous rôles.'

    def handle(self, *args, **options):
        self.stdout.write('=== Création des données de test ===\n')

        # ── Hôpitaux ──
        h1, _ = Hopital.objects.get_or_create(
            nom='CHU de Cotonou',
            defaults={
                'adresse': 'Boulevard Saint-Michel, Cotonou',
                'ville': 'Cotonou',
                'telephone': '+22921312345',
                'email': 'contact@chu-cotonou.bj',
                'description': 'Centre Hospitalier Universitaire de Cotonou',
                'latitude': 6.3654,
                'longitude': 2.4183,
            },
        )
        h2, _ = Hopital.objects.get_or_create(
            nom='Hôpital de Zone de Porto-Novo',
            defaults={
                'adresse': 'Avenue du Gouverneur, Porto-Novo',
                'ville': 'Porto-Novo',
                'telephone': '+22920215678',
                'email': 'contact@hz-portonovo.bj',
                'description': 'Hôpital de zone de référence de Porto-Novo',
                'latitude': 6.4969,
                'longitude': 2.6289,
            },
        )
        self.stdout.write(f'  Hôpitaux : {h1.nom}, {h2.nom}')

        # ── Services ──
        services_data = [
            ('Cardiologie', 'Prise en charge des maladies cardiovasculaires'),
            ('Pédiatrie', 'Soins médicaux pour les enfants'),
            ('Gynécologie', 'Santé de la femme et obstétrique'),
            ('Médecine Générale', 'Consultations de médecine générale'),
            ('Laboratoire', 'Analyses biologiques et médicales'),
        ]
        services = []
        for nom, desc in services_data:
            s, _ = Service.objects.get_or_create(nom=nom, defaults={'description': desc})
            services.append(s)
            # Associer aux deux hôpitaux
            HopitalService.objects.get_or_create(hopital=h1, service=s)
            HopitalService.objects.get_or_create(hopital=h2, service=s)

        self.stdout.write(f'  Services : {len(services)} créés / vérifiés')

        # ── Admin Général (superuser) ──
        admin_general = self._create_user(
            email='admin@HOPITEL-benin.com',
            password=PASSWORD,
            first_name='Administrateur',
            last_name='Général',
            telephone='+22990000001',
            date_naissance=date(1985, 3, 15),
            sexe='M',
            role='admin_general',
            is_staff=True,
            is_superuser=True,
        )

        # ── Admin Hôpital CHU Cotonou ──
        admin_h1 = self._create_user(
            email='admin.cotonou@HOPITEL-benin.com',
            password=PASSWORD,
            first_name='Rachid',
            last_name='Ahouansou',
            telephone='+22990000002',
            date_naissance=date(1980, 7, 22),
            sexe='M',
            role='admin_hopital',
            hopital=h1,
        )

        # ── Admin Hôpital Porto-Novo ──
        admin_h2 = self._create_user(
            email='admin.portonovo@HOPITEL-benin.com',
            password=PASSWORD,
            first_name='Amina',
            last_name='Soulé',
            telephone='+22990000003',
            date_naissance=date(1983, 11, 5),
            sexe='F',
            role='admin_hopital',
            hopital=h2,
        )

        # ── Médecins ──
        med1 = self._create_user(
            email='dr.kokou@HOPITEL-benin.com',
            password=PASSWORD,
            first_name='Kokou',
            last_name='Mensah',
            telephone='+22990000010',
            date_naissance=date(1978, 6, 12),
            sexe='M',
            role='medecin',
            hopital=h1,
        )
        if med1:
            m1, _ = Medecin.objects.get_or_create(
                user=med1,
                defaults={'numero_ordre': 'MED-BJ-001', 'biographie': 'Cardiologue, 15 ans d\'expérience.'},
            )
            MedecinService.objects.get_or_create(medecin=m1, service=services[0])  # Cardiologie

        med2 = self._create_user(
            email='dr.adje@HOPITEL-benin.com',
            password=PASSWORD,
            first_name='Fifamè',
            last_name='Adjé',
            telephone='+22990000011',
            date_naissance=date(1982, 9, 3),
            sexe='F',
            role='medecin',
            hopital=h1,
        )
        if med2:
            m2, _ = Medecin.objects.get_or_create(
                user=med2,
                defaults={'numero_ordre': 'MED-BJ-002', 'biographie': 'Pédiatre spécialisée en néonatologie.'},
            )
            MedecinService.objects.get_or_create(medecin=m2, service=services[1])  # Pédiatrie

        med3 = self._create_user(
            email='dr.houessou@HOPITEL-benin.com',
            password=PASSWORD,
            first_name='Boris',
            last_name='Houessou',
            telephone='+22990000012',
            date_naissance=date(1975, 1, 20),
            sexe='M',
            role='medecin',
            hopital=h2,
        )
        if med3:
            m3, _ = Medecin.objects.get_or_create(
                user=med3,
                defaults={'numero_ordre': 'MED-BJ-003', 'biographie': 'Médecin généraliste, Chef de service.'},
            )
            MedecinService.objects.get_or_create(medecin=m3, service=services[3])  # Médecine Générale

        # ── Laborantins ──
        lab1 = self._create_user(
            email='lab.dossou@HOPITEL-benin.com',
            password=PASSWORD,
            first_name='Hervé',
            last_name='Dossou',
            telephone='+22990000020',
            date_naissance=date(1990, 4, 18),
            sexe='M',
            role='laborantin',
            hopital=h1,
        )
        if lab1:
            Laborantin.objects.get_or_create(
                user=lab1,
                defaults={'laboratoire': 'Laboratoire Central CHU Cotonou'},
            )

        lab2 = self._create_user(
            email='lab.agbo@HOPITEL-benin.com',
            password=PASSWORD,
            first_name='Grace',
            last_name='Agbo',
            telephone='+22990000021',
            date_naissance=date(1992, 8, 25),
            sexe='F',
            role='laborantin',
            hopital=h2,
        )
        if lab2:
            Laborantin.objects.get_or_create(
                user=lab2,
                defaults={'laboratoire': 'Laboratoire HZ Porto-Novo'},
            )

        # ── Patients ──
        pat1 = self._create_user(
            email='patient1@test.com',
            password=PASSWORD,
            first_name='Jean',
            last_name='Tossou',
            telephone='+22990000030',
            date_naissance=date(1995, 2, 14),
            sexe='M',
            role='patient',
        )
        if pat1:
            Patient.objects.get_or_create(
                user=pat1,
                defaults={
                    'contact_urgence_nom': 'Marie Tossou',
                    'contact_urgence_tel': '+22990000031',
                    'groupe_sanguin': 'A+',
                    'allergies': 'Pénicilline',
                },
            )

        pat2 = self._create_user(
            email='patient2@test.com',
            password=PASSWORD,
            first_name='Chantal',
            last_name='Hounkanrin',
            telephone='+22990000032',
            date_naissance=date(1988, 12, 7),
            sexe='F',
            role='patient',
        )
        if pat2:
            Patient.objects.get_or_create(
                user=pat2,
                defaults={
                    'contact_urgence_nom': 'Paul Hounkanrin',
                    'contact_urgence_tel': '+22990000033',
                    'groupe_sanguin': 'O+',
                    'allergies': '',
                },
            )

        pat3 = self._create_user(
            email='patient3@test.com',
            password=PASSWORD,
            first_name='Abdou',
            last_name='Ibrahim',
            telephone='+22990000034',
            date_naissance=date(2000, 5, 30),
            sexe='M',
            role='patient',
        )
        if pat3:
            Patient.objects.get_or_create(
                user=pat3,
                defaults={
                    'contact_urgence_nom': 'Fatima Ibrahim',
                    'contact_urgence_tel': '+22990000035',
                    'groupe_sanguin': 'B+',
                    'allergies': 'Aspirine',
                },
            )

        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Données de test créées avec succès !'))
        self.stdout.write('=' * 50)
        self.stdout.write(f'\nMot de passe commun : {PASSWORD}')
        self.stdout.write('\nComptes créés :')
        self.stdout.write(f'  Admin Général    : admin@HOPITEL-benin.com')
        self.stdout.write(f'  Admin Hôpital 1  : admin.cotonou@HOPITEL-benin.com')
        self.stdout.write(f'  Admin Hôpital 2  : admin.portonovo@HOPITEL-benin.com')
        self.stdout.write(f'  Médecin 1        : dr.kokou@HOPITEL-benin.com')
        self.stdout.write(f'  Médecin 2        : dr.adje@HOPITEL-benin.com')
        self.stdout.write(f'  Médecin 3        : dr.houessou@HOPITEL-benin.com')
        self.stdout.write(f'  Laborantin 1     : lab.dossou@HOPITEL-benin.com')
        self.stdout.write(f'  Laborantin 2     : lab.agbo@HOPITEL-benin.com')
        self.stdout.write(f'  Patient 1        : patient1@test.com')
        self.stdout.write(f'  Patient 2        : patient2@test.com')
        self.stdout.write(f'  Patient 3        : patient3@test.com')

    def _create_user(self, email, password, first_name, last_name, telephone,
                     date_naissance, sexe, role, hopital=None,
                     is_staff=False, is_superuser=False):
        if User.objects.filter(email=email).exists():
            self.stdout.write(f'  [skip] {email} existe déjà')
            return User.objects.get(email=email)

        user = User.objects.create_user(
            email=email,
            password=password,
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
        self.stdout.write(f'  [ok] {email} ({role})')
        return user
