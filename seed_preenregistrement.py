import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from rendezvous.models import RendezVous, PreEnregistrement
from accounts.models import Patient

def run():
    print("Démarrage du seeding pour PreEnregistrement...")

    # Trouver des RDV en attente ou confirmés n'ayant pas encore de préenregistrement
    rdvs = RendezVous.objects.filter(statut__in=['en_attente', 'confirme'], pre_enregistrement__isnull=True).order_by('-date_heure')[:3]

    if not rdvs.exists():
        print("Aucun RDV valide (en_attente/confirme) trouvé pour le seed. Tentative de génération avec n'importe quel RDV futur...")
        rdvs = RendezVous.objects.filter(pre_enregistrement__isnull=True).order_by('-date_heure')[:3]
    
    if not rdvs.exists():
        print("Erreur: Absolument aucun RDV disponible en base de données.")
        return

    maux = [
        ("Maux de tête intenses depuis 3 jours, légères nausées le matin.", "Paracétamol 1000mg", "Pas d'autres antécédents notables."),
        ("Douleurs abdominales aiguës, surtout après les repas.", "Spasfon", "Le patient semble stressé récemment."),
        ("Fièvre à 39°C depuis hier soir, fatigue généralisée.", "Aucun", "Suspicion de paludisme ou grippe."),
    ]

    compt = 0
    for rdv, data in zip(rdvs, maux):
        symptomes, traitements, obs = data
        
        PreEnregistrement.objects.create(
            rendez_vous=rdv,
            symptomes_principaux=symptomes,
            debut_symptomes=timezone.now().date() - timedelta(days=3),
            traitements_en_cours=traitements,
            observations=obs
        )
        print(f"Preenregistrement cree pour le RDV ID={rdv.pk} (Patient: {rdv.patient.user.last_name})")
        compt += 1

    print(f"Seed terminé. {compt} formulaires injectés.")

if __name__ == '__main__':
    run()
