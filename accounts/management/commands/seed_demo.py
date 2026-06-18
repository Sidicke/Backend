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
from rendezvous.models import Consultation, Disponibilite, RendezVous, PreEnregistrement
from resultats.models import Resultat

User = get_user_model()
PASSWORD = 'HOPITEL2025!'


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
        if options['clean']:
            self.stdout.write(self.style.WARNING('[DEMO] --clean : suppression chirurgicale des données de démo (README)...'))
            
            # Liste des noms d'hôpitaux (README + anciens noms pour nettoyage)
            demo_hopitaux_noms = [
                'CNHU-HKM (Cotonou)', 'CHUD Porto-Novo', 'CHU Parakou', 'Hôpital de Zone (Calavi)',
                # Anciens noms à supprimer pour éviter les doublons
                'CHU de Cotonou', 'Hôpital de Zone de Porto-Novo', 'Hôpital de Zone de Parakou',
                'Clinique Autonome d\'Abomey', 'CHUD Porto Novo', 'CHU de Parakou'
            ]
            # Liste des codes courts susceptibles de collision
            demo_codes = ['CC', 'CP', 'CP1', 'HDZC']
            
            # Suppression par nom (insensible à la casse et flexible) ou par code court
            from django.db.models import Q
            Hopital.objects.filter(
                Q(nom__in=demo_hopitaux_noms) | 
                Q(code_court__in=demo_codes)
            ).delete()

            # Liste des emails de démo du README
            demo_emails = [
                'admin@hopitel.com', 'admin.cnhu@hopitel.com', 'admin.chud@hopitel.com',
                'admin.parakou@hopitel.com', 'admin.calavi@hopitel.com',
                'dossou@hopitel.com', 'tossou@hopitel.com', 'gnonlonfoun@hopitel.com',
                'houessou@hopitel.com', 'agossou@hopitel.com', 'zannou@hopitel.com',
                'bio@hopitel.com', 'sika@hopitel.com', 'mama@hopitel.com',
                'kodjo@hopitel.com', 'sossa@hopitel.com', 'ati@hopitel.com',
                'lab.cnhu@hopitel.com', 'lab.chud@hopitel.com', 'lab.parakou@hopitel.com',
                'sidicke@hopitel.com', 'patient2@hopitel.com', 'patient3@hopitel.com',
                'patient4@hopitel.com', 'patient5@hopitel.com', 'patient6@hopitel.com',
            ]
            # Suppression insensible à la casse pour éviter les conflits
            for email in demo_emails:
                User.objects.filter(email__iexact=email).delete()
            
            # Nettoyage des médecins/patients qui auraient pu être créés avec ces emails mais pas encore liés
            # (Déjà géré par CASCADE si OneToOneField, mais plus sûr ici)
            Medecin.objects.filter(user__email__in=demo_emails).delete()
            Patient.objects.filter(user__email__in=demo_emails).delete()
            self.stdout.write(self.style.SUCCESS('[DEMO] Données de démo nettoyées (les autres données manuelles sont préservées).'))

        # ── 1. HÔPITAUX (README) ──────────────────────────────────────────────────
        self.stdout.write('\n[DEMO] === 1. Hôpitaux ===')
        h1 = self._hopital(
            nom='CNHU-HKM (Cotonou)',
            adresse='Cadjehoun, Cotonou',
            ville='Cotonou', telephone='+22921312345',
            email='contact@cnhu-hkm.bj',
            description='Centre National Hospitalier Universitaire Hubert Koutoukou Maga',
            latitude=6.3654, longitude=2.4183,
        )
        h2 = self._hopital(
            nom='CHUD Porto-Novo',
            adresse='Avenue du Gouverneur, Porto-Novo',
            ville='Porto-Novo', telephone='+22920215678',
            email='contact@chud-pn.bj',
            description='Centre Hospitalier Universitaire Départemental de l\'Ouémé/Plateau',
            latitude=6.4969, longitude=2.6289,
        )
        h3 = self._hopital(
            nom='CHU Parakou',
            adresse='Quartier Banikanni, Parakou',
            ville='Parakou', telephone='+22923610000',
            email='contact@chu-parakou.bj',
            description='Centre Hospitalier Universitaire de Parakou',
            latitude=9.3372, longitude=2.6303,
        )
        h4 = self._hopital(
            nom='Hôpital de Zone (Calavi)',
            adresse='Abomey-Calavi',
            ville='Calavi', telephone='+22921360000',
            email='contact@hz-calavi.bj',
            description='Hôpital de zone d\'Abomey-Calavi / Sô-Ava',
            latitude=6.4469, longitude=2.3524,
        )

        # --- 2. SERVICES & MÉDECINS (SYNC DYNAMIQUE) ---
        self.stdout.write('\n[DEMO] === 2. Services & Médecins (Sync) ===')
        
        # Définition des services globaux
        cardiologie = self._service('Cardiologie', 'Maladies cardiovasculaires')
        pediatrie = self._service('Pédiatrie', 'Soins pédiatriques')
        medecine_gen = self._service('Médecine Générale', 'Consultations générales')
        laboratoire_svc = self._service('Laboratoire', 'Analyses médicales')
        gynecologie = self._service('Gynécologie', 'Santé de la femme')
        chirurgie = self._service('Chirurgie Générale', 'Interventions chirurgicales')
        neurologie = self._service('Neurologie', 'Système nerveux')
        ophtalmo = self._service('Ophtalmologie', 'Maladies des yeux')

        # Liste des Médecins (Exactly 3 per hospital)
        docs_data = [
            (h1, 'dossou@hopitel.com', 'Jean', 'DOSSOU', cardiologie, 'MED-BJ-001'),
            (h1, 'tossou@hopitel.com', 'Marie', 'TOSSOU', pediatrie, 'MED-BJ-002'),
            (h1, 'gnonlonfoun@hopitel.com', 'Alain', 'GNONLONFOUN', gynecologie, 'MED-BJ-003'),
            (h2, 'houessou@hopitel.com', 'Marc', 'HOUESSOU', pediatrie, 'MED-BJ-004'),
            (h2, 'agossou@hopitel.com', 'Sophie', 'AGOSSOU', neurologie, 'MED-BJ-005'),
            (h2, 'zannou@hopitel.com', 'Basile', 'ZANNOU', pediatrie, 'MED-BJ-006'),
            (h3, 'bio@hopitel.com', 'Yacoubou', 'BIO', chirurgie, 'MED-BJ-007'),
            (h3, 'sika@hopitel.com', 'Félicien', 'SIKA', ophtalmo, 'MED-BJ-008'),
            (h3, 'mama@hopitel.com', 'Saidou', 'MAMA', chirurgie, 'MED-BJ-009'),
            (h4, 'kodjo@hopitel.com', 'René', 'KODJO', gynecologie, 'MED-BJ-010'),
            (h4, 'sossa@hopitel.com', 'Pierrette', 'SOSSA', medecine_gen, 'MED-BJ-011'),
            (h4, 'ati@hopitel.com', 'Gérard', 'ATI', gynecologie, 'MED-BJ-012'),
        ]

        hopital_service_requirements = {}
        for hop, mail, fn, ln, svc, num in docs_data:
            # Création de l'utilisateur médecin
            u = self._user(email=mail, first_name=fn, last_name=ln, role='medecin', hopital=hop, 
                           telephone='+22991000000', date_naissance=date(1975,1,1), sexe='M')
            if u:
                Medecin.objects.filter(numero_ordre=num).exclude(user=u).delete()
                m, _ = Medecin.objects.get_or_create(user=u, defaults={'numero_ordre': num, 'biographie': f"Spécialiste en {svc.nom}", 'statut': 'actif'})
                if m.numero_ordre != num:
                    m.numero_ordre = num
                    m.save()
                MedecinService.objects.get_or_create(medecin=m, service=svc)
                
                # Ajout de disponibilités par défaut (Lundi-Vendredi, 8h-12h, 14h-18h)
                self._seed_availabilities(m)
                
                if hop.id not in hopital_service_requirements:
                    hopital_service_requirements[hop.id] = set()
                hopital_service_requirements[hop.id].add(svc.id)

        # 2. Synchronisation des Services (Seuls ceux AVEC médecin sont gardés)
        for hopital in [h1, h2, h3, h4]:
            required_service_ids = hopital_service_requirements.get(hopital.id, set())
            for svc_id in required_service_ids:
                HopitalService.objects.get_or_create(hopital=hopital, service_id=svc_id)
            # Nettoyage automatique
            deleted, _ = HopitalService.objects.filter(hopital=hopital).exclude(service_id__in=required_service_ids).delete()
            if deleted:
                self.stdout.write(self.style.WARNING(f'  [clean] {deleted} services sans médecin retirés de {hopital.nom}'))
            self.stdout.write(f'  [sync]  {hopital.nom} : {len(required_service_ids)} services actifs.')

        # --- 3. AUTRES UTILISATEURS ---
        self.stdout.write('\n[DEMO] === 3. Autres Utilisateurs ===')
        
        # Admin Général
        self._user(email='admin@hopitel.com', first_name='Admin', last_name='Général', role='admin_general', 
                   is_staff=True, is_superuser=True, telephone='+22990000001', date_naissance=date(1985,1,1), sexe='M')

        # Admins Hôpital
        self._user(email='admin.cnhu@hopitel.com', first_name='Admin', last_name='CNHU', role='admin_hopital', hopital=h1, telephone='+22990000002', date_naissance=date(1980,1,1), sexe='M')
        self._user(email='admin.chud@hopitel.com', first_name='Admin', last_name='CHUD', role='admin_hopital', hopital=h2, telephone='+22990000003', date_naissance=date(1980,1,1), sexe='F')
        self._user(email='admin.parakou@hopitel.com', first_name='Admin', last_name='Parakou', role='admin_hopital', hopital=h3, telephone='+22990000004', date_naissance=date(1980,1,1), sexe='M')
        self._user(email='admin.calavi@hopitel.com', first_name='Admin', last_name='Calavi', role='admin_hopital', hopital=h4, telephone='+22990000005', date_naissance=date(1980,1,1), sexe='F')

        # Laborantins
        self._user(email='lab.cnhu@hopitel.com', first_name='Paul', last_name='DOSSOU-LAB', role='laborantin', hopital=h1, telephone='+22992000001', date_naissance=date(1990,1,1), sexe='M')
        self._user(email='lab.chud@hopitel.com', first_name='Anne', last_name='MARIE-LAB', role='laborantin', hopital=h2, telephone='+22992000002', date_naissance=date(1990,1,1), sexe='F')
        self._user(email='lab.parakou@hopitel.com', first_name='Abdou', last_name='RAMANE-LAB', role='laborantin', hopital=h3, telephone='+22992000003', date_naissance=date(1990,1,1), sexe='M')

        # Patients
        p_sidicke = self._user(email='sidicke@hopitel.com', first_name='Sidicke', last_name='TRAORE', role='patient', telephone='+22993000001', date_naissance=date(1995,1,1), sexe='M')
        p_alice = self._user(email='patient2@hopitel.com', first_name='Alice', last_name='BENIN', role='patient', telephone='+22993000002', date_naissance=date(1992,1,1), sexe='F')
        p_bob = self._user(email='patient3@hopitel.com', first_name='Bob', last_name='CANCEL', role='patient', telephone='+22993000003', date_naissance=date(1990,1,1), sexe='M')
        p_claire = self._user(email='patient4@hopitel.com', first_name='Claire', last_name='LABO', role='patient', telephone='+22993000004', date_naissance=date(1994,1,1), sexe='F')
        p_david = self._user(email='patient5@hopitel.com', first_name='David', last_name='INTAKE', role='patient', telephone='+22993000005', date_naissance=date(1991,1,1), sexe='M')
        p_eve = self._user(email='patient6@hopitel.com', first_name='Eve', last_name='NEW', role='patient', telephone='+22993000006', date_naissance=date(1996,1,1), sexe='F')

        # Profils Patients
        for u in [p_sidicke, p_alice, p_bob, p_claire, p_david, p_eve]:
            if u: Patient.objects.get_or_create(user=u, defaults={'groupe_sanguin': 'O+'})

        # ── 4. SCÉNARIOS (README) ─────────────────────────────────────────────────
        self.stdout.write('\n[DEMO] === 4. Scénarios de Test ===')
        now = timezone.now()
        
        # Sidicke : RDV terminé + Consultation + Chat
        sidicke_prof = Patient.objects.get(user__email__iexact='sidicke@hopitel.com')
        dr_dossou = Medecin.objects.get(user__email__iexact='dossou@hopitel.com')
        
        rdv_sid, _ = RendezVous.objects.get_or_create(
            patient=sidicke_prof, 
            medecin=dr_dossou, 
            date_heure__date=(now - timedelta(days=2)).date(), 
            defaults={'date_heure': now - timedelta(days=2), 'statut': 'termine', 'motif': 'Bilan complet', 'duree': 30}
        )
        cons, _ = Consultation.objects.get_or_create(
            rendez_vous=rdv_sid, 
            defaults={'compte_rendu': "Patient en excellente forme.", 'diagnostic': "RAS", 'prescription': "Continuer le sport."}
        )
        Message.objects.get_or_create(
            consultation=cons, expediteur=dr_dossou.user, destinataire=p_sidicke, 
            contenu="Comment vous sentez-vous ?"
        )
        Message.objects.get_or_create(
            consultation=cons, expediteur=p_sidicke, destinataire=dr_dossou.user, 
            contenu="Très bien Docteur, merci !"
        )

        # Alice : RDV en attente
        alice_prof = Patient.objects.get(user__email__iexact='patient2@hopitel.com')
        RendezVous.objects.get_or_create(
            patient=alice_prof, medecin=dr_dossou, 
            date_heure__date=(now + timedelta(days=1)).date(),
            defaults={'date_heure': now + timedelta(days=1), 'statut': 'en_attente', 'motif': 'Urgence cardiologie', 'duree': 30}
        )

        # David : Pré-enregistrement
        david_p = Patient.objects.get(user__email__iexact='patient5@hopitel.com')
        rdv_dav, _ = RendezVous.objects.get_or_create(
            patient=david_p, medecin=dr_dossou, 
            date_heure__date=(now + timedelta(days=3)).date(),
            defaults={'date_heure': now + timedelta(days=3), 'statut': 'en_attente', 'motif': 'Douleurs thoraciques', 'duree': 30}
        )
        PreEnregistrement.objects.get_or_create(
            rendez_vous=rdv_dav, 
            defaults={'symptomes_principaux': "Douleurs fortes à la poitrine", 'debut_symptomes': date.today()-timedelta(days=2)}
        )

        # Claire : Analyse en cours
        claire_prof = Patient.objects.get(user__email__iexact='patient4@hopitel.com')
        Resultat.objects.get_or_create(
            patient=claire_prof, titre='Glycémie', date_analyse=date.today(),
            defaults={'laboratoire': 'CNHU Cotonou'}
        )

        # ── 5. NOTIFICATIONS (Pour illustrations) ─────────────────────────────────
        create_notification(p_sidicke, 'rappel_rdv', 'Rappel : Vous avez un rendez-vous demain avec le Dr. DOSSOU à 10h00.', lien=f"/api/rendezvous/{rdv_sid.id}/")
        create_notification(p_claire, 'resultat_analyse', 'Vos résultats d\'analyses (Glycémie) sont disponibles. Veuillez les consulter.', lien="/api/resultats/1/")
        create_notification(dr_dossou.user, 'nouveau_message', 'Vous avez reçu un nouveau message de Sidicke TRAORE.', lien=f"/api/consultations/{cons.pk}/")

        self._sep()
        self.stdout.write(self.style.SUCCESS('[DEMO] Seed fini ! Les 4 hôpitaux ont tous des services. 🎉'))

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

    def _user(self, email, first_name, last_name, role, telephone, date_naissance, sexe, hopital=None, is_staff=False, is_superuser=False):
        if User.objects.filter(email__iexact=email).exists():
            return User.objects.get(email__iexact=email)
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

    def _seed_availabilities(self, medecin):
        """Crée des disponibilités récurrentes (Lun-Ven) pour un médecin."""
        for jour in range(1, 6): # Lundi à Vendredi
            # Matin : 08:00 - 12:00
            Disponibilite.objects.get_or_create(
                medecin=medecin, jour_semaine=jour, type='recurrent',
                heure_debut=time(8, 0), heure_fin=time(12, 0),
                defaults={'is_active': True}
            )
            # Après-midi : 14:00 - 18:00
            Disponibilite.objects.get_or_create(
                medecin=medecin, jour_semaine=jour, type='recurrent',
                heure_debut=time(14, 0), heure_fin=time(18, 0),
                defaults={'is_active': True}
            )

    def _sep(self):
        self.stdout.write('[DEMO] ' + '-' * 60)
