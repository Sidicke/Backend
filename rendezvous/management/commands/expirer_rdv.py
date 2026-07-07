from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from rendezvous.models import RendezVous


class Command(BaseCommand):
    help = "Marque comme expirés les rendez-vous en attente dont l'heure est dépassée de 2h"

    def add_arguments(self, parser):
        parser.add_argument(
            '--delai-heures',
            type=int,
            default=2,
            help="Nombre d'heures après l'heure du RDV pour le marquer expiré (défaut: 2)",
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simule sans appliquer les modifications',
        )

    def handle(self, *args, **options):
        delai = options['delai_heures']
        dry_run = options['dry_run']
        maintenant = timezone.now()
        date_limite = maintenant - timedelta(hours=delai)

        rdvs_a_expirer = RendezVous.objects.filter(
            statut=RendezVous.Statut.EN_ATTENTE,
            date_heure__lte=date_limite,
        )

        total = rdvs_a_expirer.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Aucun rendez-vous à expirer.'))
            return

        self.stdout.write(f"{total} rendez-vous en attente vont être marqués comme expirés.")

        for rdv in rdvs_a_expirer:
            self.stdout.write(
                f"  - RDV #{rdv.id}: {rdv.patient.user.last_name} → "
                f"Dr. {rdv.medecin.user.last_name} le "
                f"{rdv.date_heure.strftime('%d/%m/%Y %H:%M')}"
            )

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run : aucune modification appliquée.'))
            return

        nb_expires = rdvs_a_expirer.update(
            statut=RendezVous.Statut.EXPIRE,
            modifie_le=timezone.now(),
        )
        self.stdout.write(self.style.SUCCESS(f'{nb_expires} rendez-vous marqués comme expirés.'))
