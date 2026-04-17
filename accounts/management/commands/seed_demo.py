"""
Commande Django : python manage.py seed_demo

Crée un jeu de données complet pour démontrer TOUTES les fonctionnalités :
  1. Utilisateurs (tous rôles)
  2. Disponibilités médecins
  3. Rendez-vous (en attente, confirmés, terminé)
  4. Consultation avec compte-rendu + messagerie
  5. Demandes d'ajout de service (en attente, validée, refusée)
  6. Résultats d'analyses (avec code_acces généré)
  7. Notifications

Idempotente par emails (utilise get_or_create).
Lance avec --clean pour repartir de zéro.
"""
import os
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Laborantin, Medecin, Patient
from hopitaux.models import DemandeAjoutService, Hopital, HopitalService, MedecinService, Service
from messagerie.models import Message
from notifications.utils import create_notification
from rendezvous.models import Consultation, Disponibilite, RendezVous
from resultats.models import Resultat

User = get_user_model()
PASSWORD = 'Esante2025!'


class Command(BaseCommand):
    help = 'Crée un jeu de données complet pour démontrer toutes les fonctionnalités de la plateforme.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Supprime les comptes de démonstration avant de recharger.',
        )

    def handle(self, *args, **options):
        self._sep()
        self.stdout.write(self.style.HTTP_INFO('[DEMO] Démarrage du seeder de démonstration complet...'))
        self._sep()

        if options['clean']:
            self.stdout.write(self.style.WARNING('[DEMO] --clean : suppression des données de démo...'))
            demo_emails = [
                'admin@esante-benin.com', 'admin.cotonou@esante-benin.com',
                'admin.portonovo@esante-benin.com', 'dr.kokou@esante-benin.com',
                'dr.adje@esante-benin.com', 'dr.houessou@esante-benin.com',
                'lab.dossou@esante-benin.com', 'lab.agbo@esante-benin.com',
                'patient1@test.com', 'patient2@test.com', 'patient3@test.com',
            ]
            User.objects.filter(email__in=demo_emails).delete()
            self.stdout.write(self.style.SUCCESS('[DEMO] Données de démo supprimées.'))

        # ── 1. HÔPITAUX ──────────────────────────────────────────────────────────
        self.stdout.write('\n[DEMO] === 1. Hôpitaux ===')
        h1 = self._hopital(
            nom='CHU de Cotonou',
            adresse='Boulevard Saint-Michel, Cotonou',
            ville='Cotonou', telephone='+22921312345',
            email='contact@chu-cotonou.bj',
            description='Centre Hospitalier Universitaire de Cotonou',
            latitude=6.3654, longitude=2.4183,
        )
        h2 = self._hopital(
            nom='Hôpital de Zone de Porto-Novo',
            adresse='Avenue du Gouverneur, Porto-Novo',
            ville='Porto-Novo', telephone='+22920215678',
            email='contact@hz-portonovo.bj',
            description='Hôpital de zone de référence de Porto-Novo',
            latitude=6.4969, longitude=2.6289,
        )

        # ── 2. SERVICES ───────────────────────────────────────────────────────────
        self.stdout.write('\n[DEMO] === 2. Services ===')
        cardiologie = self._service('Cardiologie', 'Prise en charge des maladies cardiovasculaires', hopitaux=[h1])
        pediatrie = self._service('Pédiatrie', 'Soins médicaux pour les enfants', hopitaux=[h1, h2])
        medecine_gen = self._service('Médecine Générale', 'Consultations de médecine générale', hopitaux=[h1, h2])
        laboratoire_svc = self._service('Laboratoire', 'Analyses biologiques et médicales', hopitaux=[h1, h2])
        radiologie = self._service('Radiologie', 'Imagerie médicale', hopitaux=[])  # Pas encore associée

        # ── 3. UTILISATEURS ───────────────────────────────────────────────────────
        self.stdout.write('\n[DEMO] === 3. Utilisateurs ===')

        # Admin Général
        admin_gen = self._user(
            email='admin@esante-benin.com',
            first_name='Administrateur', last_name='Général',
            telephone='+22990000001', date_naissance=date(1985, 3, 15), sexe='M',
            role='admin_general', is_staff=True, is_superuser=True,
        )

        # Admins Hôpital
        admin_h1 = self._user(
            email='admin.cotonou@esante-benin.com',
            first_name='Rachid', last_name='Ahouansou',
            telephone='+22990000002', date_naissance=date(1980, 7, 22), sexe='M',
            role='admin_hopital', hopital=h1,
        )
        admin_h2 = self._user(
            email='admin.portonovo@esante-benin.com',
            first_name='Amina', last_name='Soulé',
            telephone='+22990000003', date_naissance=date(1983, 11, 5), sexe='F',
            role='admin_hopital', hopital=h2,
        )

        # Médecins
        med1_user = self._user(
            email='dr.kokou@esante-benin.com',
            first_name='Kokou', last_name='Mensah',
            telephone='+22990000010', date_naissance=date(1978, 6, 12), sexe='M',
            role='medecin', hopital=h1,
        )
        m1 = None
        if med1_user:
            m1, _ = Medecin.objects.get_or_create(
                user=med1_user,
                defaults={'numero_ordre': 'MED-BJ-001', 'biographie': "Cardiologue, 15 ans d'expérience.", 'statut': 'actif'},
            )
            MedecinService.objects.get_or_create(medecin=m1, service=cardiologie)

        med2_user = self._user(
            email='dr.adje@esante-benin.com',
            first_name='Fifamè', last_name='Adjé',
            telephone='+22990000011', date_naissance=date(1982, 9, 3), sexe='F',
            role='medecin', hopital=h1,
        )
        m2 = None
        if med2_user:
            m2, _ = Medecin.objects.get_or_create(
                user=med2_user,
                defaults={'numero_ordre': 'MED-BJ-002', 'biographie': 'Pédiatre spécialisée en néonatologie.', 'statut': 'actif'},
            )
            MedecinService.objects.get_or_create(medecin=m2, service=pediatrie)

        med3_user = self._user(
            email='dr.houessou@esante-benin.com',
            first_name='Boris', last_name='Houessou',
            telephone='+22990000012', date_naissance=date(1975, 1, 20), sexe='M',
            role='medecin', hopital=h2,
        )
        m3 = None
        if med3_user:
            m3, _ = Medecin.objects.get_or_create(
                user=med3_user,
                defaults={'numero_ordre': 'MED-BJ-003', 'biographie': 'Médecin généraliste, Chef de service.', 'statut': 'actif'},
            )
            MedecinService.objects.get_or_create(medecin=m3, service=medecine_gen)

        # Laborantins
        lab1_user = self._user(
            email='lab.dossou@esante-benin.com',
            first_name='Hervé', last_name='Dossou',
            telephone='+22990000020', date_naissance=date(1990, 4, 18), sexe='M',
            role='laborantin', hopital=h1,
        )
        lab1_profile = None
        if lab1_user:
            lab1_profile, _ = Laborantin.objects.get_or_create(
                user=lab1_user,
                defaults={'laboratoire': 'Laboratoire Central CHU Cotonou'},
            )

        lab2_user = self._user(
            email='lab.agbo@esante-benin.com',
            first_name='Grace', last_name='Agbo',
            telephone='+22990000021', date_naissance=date(1992, 8, 25), sexe='F',
            role='laborantin', hopital=h2,
        )
        if lab2_user:
            Laborantin.objects.get_or_create(
                user=lab2_user,
                defaults={'laboratoire': 'Laboratoire HZ Porto-Novo'},
            )

        # Patients
        pat1_user = self._user(
            email='patient1@test.com',
            first_name='Jean', last_name='Tossou',
            telephone='+22990000030', date_naissance=date(1995, 2, 14), sexe='M',
            role='patient',
        )
        pat1_profile = None
        if pat1_user:
            pat1_profile, _ = Patient.objects.get_or_create(
                user=pat1_user,
                defaults={
                    'contact_urgence_nom': 'Marie Tossou',
                    'contact_urgence_tel': '+22990000031',
                    'groupe_sanguin': 'A+', 'allergies': 'Pénicilline',
                },
            )

        pat2_user = self._user(
            email='patient2@test.com',
            first_name='Chantal', last_name='Hounkanrin',
            telephone='+22990000032', date_naissance=date(1988, 12, 7), sexe='F',
            role='patient',
        )
        pat2_profile = None
        if pat2_user:
            pat2_profile, _ = Patient.objects.get_or_create(
                user=pat2_user,
                defaults={
                    'contact_urgence_nom': 'Paul Hounkanrin',
                    'contact_urgence_tel': '+22990000033',
                    'groupe_sanguin': 'O+', 'allergies': '',
                },
            )

        pat3_user = self._user(
            email='patient3@test.com',
            first_name='Abdou', last_name='Ibrahim',
            telephone='+22990000034', date_naissance=date(2000, 5, 30), sexe='M',
            role='patient',
        )
        pat3_profile = None
        if pat3_user:
            pat3_profile, _ = Patient.objects.get_or_create(
                user=pat3_user,
                defaults={
                    'contact_urgence_nom': 'Fatima Ibrahim',
                    'contact_urgence_tel': '+22990000035',
                    'groupe_sanguin': 'B+', 'allergies': 'Aspirine',
                },
            )

        # ── 4. DISPONIBILITÉS MÉDECINS ────────────────────────────────────────────
        if m1:
            self.stdout.write('\n[DEMO] === 4. Disponibilités médecins ===')
            for jour in [1, 3, 5]:  # Lundi, Mercredi, Vendredi
                Disponibilite.objects.get_or_create(
                    medecin=m1, type='recurrent', jour_semaine=jour,
                    defaults={'heure_debut': time(8, 0), 'heure_fin': time(12, 0)},
                )
            self.stdout.write(f'  [ok] Disponibilités Dr. {m1.user.last_name} : Lun/Mer/Ven 8h-12h')

        if m2:
            for jour in [2, 4]:  # Mardi, Jeudi
                Disponibilite.objects.get_or_create(
                    medecin=m2, type='recurrent', jour_semaine=jour,
                    defaults={'heure_debut': time(14, 0), 'heure_fin': time(18, 0)},
                )
            self.stdout.write(f'  [ok] Disponibilités Dr. {m2.user.last_name} : Mar/Jeu 14h-18h')

        if m3:
            for jour in [1, 2, 3, 4, 5]:  # Lundi à Vendredi
                Disponibilite.objects.get_or_create(
                    medecin=m3, type='recurrent', jour_semaine=jour,
                    defaults={'heure_debut': time(7, 30), 'heure_fin': time(14, 30)},
                )
            self.stdout.write(f'  [ok] Disponibilités Dr. {m3.user.last_name} : Lun-Ven 7h30-14h30')

        # ── 5. RENDEZ-VOUS ────────────────────────────────────────────────────────
        self.stdout.write('\n[DEMO] === 5. Rendez-vous ===')

        now = timezone.now()

        # RDV 1 : en attente (patient1 → Dr. Mensah)
        rdv1 = None
        if pat1_profile and m1:
            rdv1, created = RendezVous.objects.get_or_create(
                patient=pat1_profile, medecin=m1,
                date_heure=now + timedelta(days=3, hours=2),
                defaults={'duree': 30, 'motif': 'Douleurs thoraciques récurrentes', 'statut': 'en_attente'},
            )
            self.stdout.write(f'  [ok] RDV en attente : patient={pat1_user.email} -> Dr. {m1.user.last_name}')

        # RDV 2 : confirmé (patient2 → Dr. Adjé)
        rdv2 = None
        if pat2_profile and m2:
            rdv2, created = RendezVous.objects.get_or_create(
                patient=pat2_profile, medecin=m2,
                date_heure=now + timedelta(days=1, hours=4),
                defaults={'duree': 45, 'motif': 'Consultation pédiatrique pour enfant 3 ans', 'statut': 'confirme'},
            )
            if created:
                create_notification(
                    user=pat2_user,
                    type='rdv_confirme',
                    message=f"Votre rendez-vous avec Dr. {m2.user.last_name} a été confirmé.",
                    lien=f"/api/rendezvous/{rdv2.pk}/",
                )
            self.stdout.write(f'  [ok] RDV confirme : patient={pat2_user.email} -> Dr. {m2.user.last_name}')

        # RDV 3 : terminé + consultation + messagerie (patient1 → Dr. Houessou)
        rdv3 = None
        consultation = None
        if pat1_profile and m3 and pat1_user and med3_user:
            rdv3, created = RendezVous.objects.get_or_create(
                patient=pat1_profile, medecin=m3,
                date_heure=now - timedelta(days=5),
                defaults={'duree': 30, 'motif': 'Bilan de santé annuel', 'statut': 'termine'},
            )
            self.stdout.write(f'  [ok] RDV termine : patient={pat1_user.email} -> Dr. {m3.user.last_name}')

            # Consultation associée au RDV terminé
            consultation, c_created = Consultation.objects.get_or_create(
                rendez_vous=rdv3,
                defaults={
                    'compte_rendu': 'Patient en bonne santé générale. Légère hypertension artérielle notée.',
                    'diagnostic': 'Hypertension artérielle stade 1',
                    'prescription': 'Ramipril 5mg/j - 1 comprimé le matin. Réévaluation dans 3 mois.',
                },
            )
            if c_created:
                self.stdout.write(f'  [ok] Consultation créée pour RDV {rdv3.pk}')

            # Messagerie : échange entre patient et médecin pendant la consultation
            if c_created:
                Message.objects.create(
                    consultation=consultation,
                    expediteur=med3_user,
                    destinataire=pat1_user,
                    contenu="Bonjour Jean, j'ai bien reçu votre compte rendu. Avez-vous des questions ?",
                )
                Message.objects.create(
                    consultation=consultation,
                    expediteur=pat1_user,
                    destinataire=med3_user,
                    contenu="Bonjour Docteur, oui je voulais savoir si je dois éviter le sel.",
                    lu=True,
                )
                Message.objects.create(
                    consultation=consultation,
                    expediteur=med3_user,
                    destinataire=pat1_user,
                    contenu="Oui, limitez votre consommation de sel à 5g/jour. Mangez équilibré.",
                )
                self.stdout.write(f'  [ok] 3 messages créés pour la consultation {consultation.pk}')

        # RDV 4 : refusé (patient3 → Dr. Mensah)
        if pat3_profile and m1 and pat3_user:
            rdv4, created = RendezVous.objects.get_or_create(
                patient=pat3_profile, medecin=m1,
                date_heure=now - timedelta(days=2),
                defaults={
                    'duree': 30,
                    'motif': 'Palpitations cardiaques',
                    'statut': 'refuse',
                    'commentaire_annulation': 'Créneau indisponible ce jour. Veuillez choisir un autre créneau.',
                },
            )
            if created:
                create_notification(
                    user=pat3_user,
                    type='rdv_refuse',
                    message=f"Votre rendez-vous avec Dr. {m1.user.last_name} a été refusé. Motif : Créneau indisponible.",
                    lien=f"/api/rendezvous/{rdv4.pk}/",
                )
            self.stdout.write(f'  [ok] RDV refusé avec motif')

        # ── 6. DEMANDES D'AJOUT DE SERVICE ────────────────────────────────────────
        self.stdout.write('\n[DEMO] === 6. Demandes d\'ajout de service ===')

        # Demande 1 : en attente (admin h1 demande Radiologie)
        if admin_h1:
            d1, created = DemandeAjoutService.objects.get_or_create(
                hopital=h1, service_existant=radiologie, demande_par=admin_h1,
                defaults={'statut': 'en_attente'},
            )
            if created:
                create_notification(
                    user=admin_gen,
                    type='demande_service',
                    message=f"Nouvelle demande d'ajout du service « Radiologie » de {h1.nom}.",
                    lien=f"/api/hopitaux/demandes/{d1.pk}/",
                )
            self.stdout.write(f'  [ok] Demande EN ATTENTE : Radiologie pour {h1.nom}')

        # Demande 2 : validée (admin h2 demande Neurologie)
        neurologie = self._service('Neurologie', 'Maladies du système nerveux', hopitaux=[])
        if admin_h2 and admin_gen:
            d2, created = DemandeAjoutService.objects.get_or_create(
                hopital=h2, service_existant=neurologie, demande_par=admin_h2,
                defaults={
                    'statut': 'valide',
                    'commentaire': '',
                    'traite_par': admin_gen,
                    'date_traitement': now - timedelta(days=2),
                },
            )
            if created:
                HopitalService.objects.get_or_create(hopital=h2, service=neurologie)
                create_notification(
                    user=admin_h2,
                    type='validation_service',
                    message=f"Votre demande d'ajout du service « Neurologie » a été validée.",
                )
            self.stdout.write(f'  [ok] Demande VALIDÉE : Neurologie pour {h2.nom}')

        # Demande 3 : refusée avec motif (admin h1 demande Chirurgie Plastique)
        if admin_h1 and admin_gen:
            d3, created = DemandeAjoutService.objects.get_or_create(
                hopital=h1,
                nom_nouveau_service='Chirurgie Plastique',
                demande_par=admin_h1,
                defaults={
                    'statut': 'refuse',
                    'commentaire': "Ce service n'est pas prioritaire pour le moment. Concentrez-vous sur le renforcement des services existants.",
                    'traite_par': admin_gen,
                    'date_traitement': now - timedelta(days=1),
                },
            )
            if created:
                create_notification(
                    user=admin_h1,
                    type='refus_service',
                    message=f"Votre demande d'ajout du service « Chirurgie Plastique » a été refusée.",
                )
            self.stdout.write(f'  [ok] Demande REFUSÉE avec motif : Chirurgie Plastique pour {h1.nom}')

        # ── 7. RÉSULTATS D'ANALYSES ───────────────────────────────────────────────
        self.stdout.write("\n[DEMO] === 7. Résultats d'analyses ===")

        if pat1_profile and lab1_user:
            r1, created = Resultat.objects.get_or_create(
                patient=pat1_profile,
                titre='Bilan Lipidique Complet',
                defaults={
                    'laborantin': lab1_user,
                    'consultation': consultation,
                    'date_analyse': date.today() - timedelta(days=4),
                    'laboratoire': 'Laboratoire Central CHU Cotonou',
                    'fichier': '',  # Fichier vide pour le test
                },
            )
            self.stdout.write(f'  [ok] Résultat "{r1.titre}" pour {pat1_user.get_full_name()}')
            self.stdout.write(f"       Code d'acces : {r1.code_acces}")

        if pat2_profile and lab1_user:
            r2, created = Resultat.objects.get_or_create(
                patient=pat2_profile,
                titre='Numération Formule Sanguine (NFS)',
                defaults={
                    'laborantin': lab1_user,
                    'date_analyse': date.today() - timedelta(days=2),
                    'laboratoire': 'Laboratoire Central CHU Cotonou',
                    'fichier': '',
                },
            )
            self.stdout.write(f'  [ok] Résultat "{r2.titre}" pour {pat2_user.get_full_name()}')
            self.stdout.write(f"       Code d'acces : {r2.code_acces}")

        if pat3_profile and lab2_user:
            r3, created = Resultat.objects.get_or_create(
                patient=pat3_profile,
                titre='Glycémie à jeun + HbA1c',
                defaults={
                    'laborantin': lab2_user,
                    'date_analyse': date.today() - timedelta(days=1),
                    'laboratoire': 'Laboratoire HZ Porto-Novo',
                    'fichier': '',
                },
            )
            self.stdout.write(f'  [ok] Résultat "{r3.titre}" pour {pat3_user.get_full_name()}')
            self.stdout.write(f"       Code d'acces : {r3.code_acces}")

        # ── RÉSUMÉ ────────────────────────────────────────────────────────────────
        self._sep()
        self.stdout.write(self.style.SUCCESS('[DEMO] Jeu de donnees complet cree avec succes !'))
        self._sep()
        self.stdout.write(f'\n  Mot de passe commun : {PASSWORD}\n')
        self.stdout.write(self.style.HTTP_INFO('  COMPTES :'))
        rows = [
            ('Admin Général',       'admin@esante-benin.com'),
            ('Admin CHU Cotonou',   'admin.cotonou@esante-benin.com'),
            ('Admin Porto-Novo',    'admin.portonovo@esante-benin.com'),
            ('Dr. Mensah (Cardio)', 'dr.kokou@esante-benin.com'),
            ('Dr. Adjé (Pédia)',    'dr.adje@esante-benin.com'),
            ('Dr. Houessou (MG)',   'dr.houessou@esante-benin.com'),
            ('Laborantin Cotonou',  'lab.dossou@esante-benin.com'),
            ('Laborantin P-Novo',   'lab.agbo@esante-benin.com'),
            ('Patient 1 (Jean T.)', 'patient1@test.com'),
            ('Patient 2 (Chantal H.)', 'patient2@test.com'),
            ('Patient 3 (Abdou I.)', 'patient3@test.com'),
        ]
        for role, email in rows:
            self.stdout.write(f'    {role:<28} -> {email}')
        self.stdout.write(self.style.HTTP_INFO('  SCENARIOS :'))
        self.stdout.write('    [OK] RDV en attente    -> patient1 / Dr.Mensah (dans 3 jours)')
        self.stdout.write('    [OK] RDV confirme      -> patient2 / Dr.Adje (dans 1 jour)')
        self.stdout.write('    [OK] RDV termine + consultation + chat -> patient1 / Dr.Houessou')
        self.stdout.write('    [OK] RDV refuse (avec motif) -> patient3 / Dr.Mensah')
        self.stdout.write('    [OK] Demande service en attente -> Radiologie (CHU Cotonou, admin_h1)')
        self.stdout.write('    [OK] Demande service validee   -> Neurologie (Porto-Novo, admin_h2)')
        self.stdout.write('    [OK] Demande service refusee + motif -> Chirurgie Plastique (CHU, admin_h1)')
        self.stdout.write("    [OK] 3 resultats labo avec codes d'acces (patient 1/2/3)")
        self._sep()

    # ── Helpers ──────────────────────────────────────────────────────────────────

    def _hopital(self, nom, **kwargs):
        h, created = Hopital.objects.get_or_create(nom=nom, defaults=kwargs)
        self.stdout.write(f'  [{"créé" if created else "skip"}] Hôpital : {nom}')
        return h

    def _service(self, nom, description, hopitaux=None):
        s, created = Service.objects.get_or_create(nom=nom, defaults={'description': description})
        if hopitaux:
            for h in hopitaux:
                HopitalService.objects.get_or_create(hopital=h, service=s)
        self.stdout.write(f'  [{"créé" if created else "skip"}] Service : {nom}')
        return s

    def _user(self, email, first_name, last_name, telephone, date_naissance, sexe, role,
              hopital=None, is_staff=False, is_superuser=False):
        if User.objects.filter(email=email).exists():
            self.stdout.write(f'  [skip] {email}')
            return User.objects.get(email=email)
        user = User.objects.create_user(
            email=email, password=PASSWORD,
            first_name=first_name, last_name=last_name,
            telephone=telephone, date_naissance=date_naissance,
            sexe=sexe, role=role, hopital=hopital,
            is_active=True, is_email_verified=True,
            is_staff=is_staff, is_superuser=is_superuser,
        )
        self.stdout.write(f'  [ok]   {email} ({role})')
        return user

    def _sep(self):
        self.stdout.write('[DEMO] ' + '-' * 60)
