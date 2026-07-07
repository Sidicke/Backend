"""
Commande Django : python manage.py cleanup_data
Nettoie la base de données pour la production :
- Garde UNIQUEMENT le patient sidicke@hopitel.com
- Supprime tous les autres utilisateurs
- Supprime les hôpitaux sans service
- Supprime les médecins sans hôpital
- Supprime toutes les données orphelines associées
"""
import logging
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Nettoie la base : garde sidicke@hopitel.com, hopitaux avec services, medecins avec hopital.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation seule : affiche ce qui serait supprimé sans rien effacer.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        mode = '[DRY-RUN]' if dry_run else '[EXECUTION]'
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'  {mode} NETTOYAGE DE LA BASE DE DONNÉES')
        self.stdout.write(f'{"="*60}\n')

        if dry_run:
            self.stdout.write(self.style.WARNING(' ⚠ Mode simulation — AUCUNE suppression réelle.\n'))

        # ── 1. Garder UNIQUEMENT sidicke@hopitel.com ──────────────────────────
        self._step_title(1, 'Suppression de tous les utilisateurs sauf sidicke@hopitel.com')

        patients = User.objects.filter(email='sidicke@hopitel.com')
        if not patients.exists():
            self.stdout.write(self.style.ERROR(' ❌ Aucun utilisateur trouvé avec email sidicke@hopitel.com !'))
            self.stdout.write('    Vérifiez que le compte patient a bien été créé.')
            return

        patient_user = patients.first()
        total_users = User.objects.count()
        users_to_delete = User.objects.exclude(email='sidicke@hopitel.com')
        count_users = users_to_delete.count()

        self.stdout.write(f'    Total utilisateurs : {total_users}')
        self.stdout.write(f'    Gardé : {patient_user.email} ({patient_user.get_full_name()})')
        self.stdout.write(f'    À supprimer : {count_users} utilisateurs')

        # Liste des emails supprimés
        if count_users > 0:
            self.stdout.write('    Emails supprimés :')
            for u in users_to_delete.iterator():
                self.stdout.write(f'      - {u.email} ({u.get_full_name()}, rôle: {u.role})')

        # ── 2. Hôpitaux sans service ──────────────────────────────────────────
        self._step_title(2, 'Suppression des hôpitaux sans service')

        from hopitaux.models import Hopital
        hopitaux_sans_service = Hopital.objects.filter(hopital_services__isnull=True)
        count_hopitaux = hopitaux_sans_service.count()

        if count_hopitaux > 0:
            self.stdout.write(f'    Hôpitaux sans service ({count_hopitaux}) :')
            for h in hopitaux_sans_service.iterator():
                self.stdout.write(f'      - {h.nom} (ID: {h.id})')
        else:
            self.stdout.write('    ✅ Tous les hôpitaux ont au moins un service.')

        # ── 3. Médecins sans hôpital ─────────────────────────────────────────
        self._step_title(3, 'Suppression des médecins sans hôpital de rattachement')

        from accounts.models import Medecin
        medecins_sans_hopital = Medecin.objects.filter(user__hopital__isnull=True)
        count_medecins = medecins_sans_hopital.count()

        if count_medecins > 0:
            self.stdout.write(f'    Médecins sans hôpital ({count_medecins}) :')
            for m in medecins_sans_hopital.iterator():
                self.stdout.write(f'      - Dr. {m.user.get_full_name()} (email: {m.user.email})')
        else:
            self.stdout.write('    ✅ Tous les médecins sont rattachés à un hôpital.')

        # ── 4. Résumé avant suppression ───────────────────────────────────────
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(f'  RÉSUMÉ DES SUPPRESSIONS :')
        self.stdout.write(f'    - {count_users} utilisateurs')
        self.stdout.write(f'    - {count_hopitaux} hôpitaux sans service')
        self.stdout.write(f'    - {count_medecins} médecins sans hôpital')
        self.stdout.write(f'    - Toutes les données associées (RDV, messages, etc.)')
        self.stdout.write(f'{"="*60}\n')

        if dry_run:
            self.stdout.write(self.style.WARNING(' ⚠ Dry-run terminé — AUCUNE modification réelle.\n'))
            return

        # ── Confirmation ─────────────────────────────────────────────────────
        self.stdout.write(self.style.WARNING(' ⚠ Cette action est IRRÉVERSIBLE.'))
        confirm = input('    Taper "yes" pour confirmer la suppression : ')
        if confirm != 'yes':
            self.stdout.write(self.style.WARNING(' ❌ Annulé.'))
            return

        # ── EXÉCUTION ─────────────────────────────────────────────────────────
        with transaction.atomic():
            # Supprimer les médecins sans hôpital (et leurs users)
            for m in medecins_sans_hopital.iterator():
                user = m.user
                self.stdout.write(f'    Suppression du médecin : {user.email}')
                # Cascade supprimera : disponibilites, rendezvous, medecin_services, etc.
                user.delete()

            # Supprimer les hôpitaux sans service
            for h in hopitaux_sans_service.iterator():
                self.stdout.write(f'    Suppression de l\'hôpital : {h.nom}')
                h.delete()

            # Supprimer tous les autres utilisateurs
            for u in users_to_delete.iterator():
                self.stdout.write(f'    Suppression de l\'utilisateur : {u.email} ({u.role})')
                u.delete()

        # ── Vérification finale ──────────────────────────────────────────────
        remaining_users = User.objects.count()
        remaining_hopitaux = Hopital.objects.count()
        from accounts.models import Medecin
        remaining_medecins = Medecin.objects.count()

        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS(' ✅ NETTOYAGE TERMINÉ'))
        self.stdout.write(f'    Utilisateurs restants : {remaining_users}')
        self.stdout.write(f'    Hôpitaux restants : {remaining_hopitaux}')
        self.stdout.write(f'    Médecins restants : {remaining_medecins}')
        self.stdout.write(f'{"="*60}\n')

    def _step_title(self, num, title):
        self.stdout.write(f'\n─── Étape {num} : {title} ───────────────────────────────────────')
