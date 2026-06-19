import os
import django
from datetime import timedelta
from django.utils import timezone
import random

# Initialisation de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Patient, Medecin, Laborantin
from hopitaux.models import Hopital, Service, HopitalService, MedecinService
from rendezvous.models import RendezVous, Disponibilite, PreEnregistrement, Consultation
from resultats.models import DemandeAnalyse
from messagerie.models import Message
from notifications.models import Notification

User = get_user_model()


def _get_or_create_user(email, password, **fields):
    """Crée un utilisateur ou retourne l'existant (idempotent)."""
    user, created = User.objects.get_or_create(
        email=email,
        defaults={**fields},
    )
    if created:
        user.set_password(password)
        user.save(update_fields=['password'])
        print(f"  [NEW]  {email} ({fields.get('role', 'n/a')})")
    else:
        # Met à jour les champs si l'utilisateur existe déjà
        changed = False
        for k, v in fields.items():
            if getattr(user, k, None) != v:
                setattr(user, k, v)
                changed = True
        if changed:
            user.save()
        print(f"  [EXIST] {email}")
    return user


def clear_data():
    """Nettoie les données existantes pour repartir sur une base propre."""
    print("--- Nettoyage complet des données de démo ---")

    # 1. Anciens emails de démo (seed précédents)
    old_emails = [
        "admin@hopitel.com", "dr.dossou@hopitel.com", "dr.tossou@hopitel.com",
        "dr.amoussou@hopitel.com", "labo.agbo@hopitel.com", "sidicke@hopitel.com",
        "koffi@hopitel.com", "amina@hopitel.com", "admin.cnhu@hopitel.com",
        "admin.chud@hopitel.com", "admin.parakou@hopitel.com", "admin.calavi@hopitel.com",
        "lab.cnhu@hopitel.com", "lab.chud@hopitel.com", "lab.parakou@hopitel.com",
        "admin@esante.com", "dossou@esante.com", "tossou@esante.com", "sidicke@esante.com",
        "admin.mahouna@hopitel.com", "dr.kodjo@hopitel.com",
    ]
    deleted, _ = User.objects.filter(email__in=old_emails).delete()
    if deleted:
        print(f"  Supprimé {deleted} ancien(s) utilisateur(s) de démo")

    # 2. Anciens hôpitaux de démo
    old_hosps = [
        "CNHU-HKM (Cotonou)", "CHUD Porto-Novo", "CHU Parakou",
        "Hôpital de Zone (Calavi)", "Clinique Mahouna", "CNHU-HKM Cotonou",
        "CHD Ouémé-Plateau",
    ]
    Hopital.objects.filter(nom__in=old_hosps).delete()


def run():
    clear_data()
    print("--- Début du Seed Mémoire Final (Restoration complète) ---")

    # ━━━  1.  HÔPITAL  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    h_lokossa, _ = Hopital.objects.update_or_create(
        nom="Hôpital de Zone de Lokossa",
        defaults=dict(
            adresse="Route de Lokossa, Lokossa",
            ville="Lokossa",
            latitude=6.6334096,
            longitude=1.7141026,
            telephone="+229 22 41 10 29",
            email="contact@hz-lokossa.hopitel.com",
            is_active=True,
        ),
    )
    print(f"  Hôpital : {h_lokossa.nom} (lat={h_lokossa.latitude}, lng={h_lokossa.longitude})")

    # ━━━  2.  SERVICES  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    services_data = [
        ("Cardiologie", "Maladies du cœur et du système vasculaire."),
        ("Pédiatrie", "Médecine des enfants et des nourrissons."),
        ("Gynécologie", "Santé de la femme et suivi obstétrical."),
        ("Ophtalmologie", "Maladies des yeux."),
        ("Chirurgie Générale", "Interventions chirurgicales courantes."),
        ("Neurologie", "Pathologies du système nerveux."),
    ]
    services_obj = {}
    for nom, desc in services_data:
        s, _ = Service.objects.get_or_create(nom=nom, defaults={"description": desc, "is_active": True})
        services_obj[nom] = s

    for s in services_obj.values():
        HopitalService.objects.get_or_create(hopital=h_lokossa, service=s)

    # ━━━  3.  UTILISATEURS  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n--- Création des utilisateurs ---")

    # 3a. Admin général (plate-forme)
    admin = _get_or_create_user(
        email="admin@hopitel.com", password="HopitelAdmin2025*",
        role="admin_general", first_name="Ariel", last_name="Admin",
        telephone="22990000001", sexe="M", is_active=True,
    )

    # 3b. Admin Hôpital de Zone de Lokossa
    u_admin = _get_or_create_user(
        email="gillmarilin4@gmail.com", password="AdminLokossa2025!",
        role="admin_hopital", first_name="Gill-Marilin", last_name="BADJI",
        hopital=h_lokossa, telephone="22990111111", sexe="F", is_active=True,
    )

    # 3c. Médecin 1 — Cardiologue
    u_med1 = _get_or_create_user(
        email="marionbdj9@gmail.com", password="MedecinCardio2025!",
        role="medecin", first_name="Marion", last_name="BADJI",
        hopital=h_lokossa, telephone="22990222222", sexe="F", is_active=True,
    )
    med1, _ = Medecin.objects.get_or_create(
        user=u_med1,
        defaults={"numero_ordre": "BEN-MED-5001", "biographie": "Cardiologue interventionnelle, spécialisée en échocardiographie et cathétérisme cardiaque."},
    )
    MedecinService.objects.get_or_create(medecin=med1, service=services_obj["Cardiologie"])

    # 3d. Médecin 2 — Pédiatre
    u_med2 = _get_or_create_user(
        email="akouemahogillchristmarilinbadj@gmail.com", password="MedecinPedia2025!",
        role="medecin", first_name="Akoue-Maho", last_name="GILL-CHRIST",
        hopital=h_lokossa, telephone="22990333333", sexe="M", is_active=True,
    )
    med2, _ = Medecin.objects.get_or_create(
        user=u_med2,
        defaults={"numero_ordre": "BEN-MED-5002", "biographie": "Pédiatre néonatologue, prise en charge des nouveau-nés et enfants."},
    )
    MedecinService.objects.get_or_create(medecin=med2, service=services_obj["Pédiatrie"])

    # 3e. Médecin 3 — Neurologue
    u_med3 = _get_or_create_user(
        email="gillbadji@gmail.com", password="MedecinNeuro2025!",
        role="medecin", first_name="Gill", last_name="BADJI",
        hopital=h_lokossa, telephone="22990444444", sexe="M", is_active=True,
    )
    med3, _ = Medecin.objects.get_or_create(
        user=u_med3,
        defaults={"numero_ordre": "BEN-MED-5003", "biographie": "Neurologue, spécialisé en électroencéphalographie et maladies neurodégénératives."},
    )
    MedecinService.objects.get_or_create(medecin=med3, service=services_obj["Neurologie"])

    # 3f. Laborantin
    u_lab = _get_or_create_user(
        email="marilinbadji@gmail.com", password="LaboLokossa2025!",
        role="laborantin", first_name="Marilin", last_name="BADJI",
        hopital=h_lokossa, telephone="22990555555", sexe="F", is_active=True,
    )
    laborantin, _ = Laborantin.objects.get_or_create(
        user=u_lab,
        defaults={"laboratoire": "Laboratoire HZ Lokossa"},
    )

    # 3g. Patients fictifs (pour les démos de RDV)
    patients_data = [
        ("sidicke@hopitel.com", "PatientSidicke01", "Sidicke", "TRAORÉ", "M", "O+", "1029384756"),
        ("koffi@hopitel.com", "PatientKoffi02", "Koffi", "MENSAH", "M", "A+", "2938475610"),
        ("amina@hopitel.com", "PatientAmina03", "Amina", "SALIU", "F", "B-", "9384756102"),
    ]
    patients = []
    for p_email, p_pwd, fn, ln, sx, gs, npi in patients_data:
        u_pat = _get_or_create_user(
            email=p_email, password=p_pwd, role="patient",
            first_name=fn, last_name=ln, telephone="22990000005", sexe=sx, is_active=True,
        )
        pat, _ = Patient.objects.get_or_create(
            user=u_pat,
            defaults={"groupe_sanguin": gs, "npi": npi},
        )
        patients.append(pat)

    pat1, pat2, pat3 = patients

    # ━━━  4.  DISPONIBILITÉS  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n--- Création des disponibilités ---")
    medecins = [med1, med2, med3]
    for m in medecins:
        for jour in range(1, 6):  # Lundi–Vendredi
            Disponibilite.objects.get_or_create(
                medecin=m, jour_semaine=jour,
                defaults={"heure_debut": "08:00", "heure_fin": "16:00", "type": "recurrent"},
            )

    # ━━━  5.  RENDEZ-VOUS  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n--- Création des rendez-vous ---")
    now = timezone.now()

    rdv_data = [
        # Terminés
        (pat1, med1, now - timedelta(days=5), 'termine', "Contrôle de routine cardiaque"),
        (pat2, med1, now - timedelta(days=3), 'termine', "Douleurs thoraciques"),
        (pat3, med2, now - timedelta(days=2), 'termine', "Visite pédiatrique"),
        (pat1, med3, now - timedelta(days=1), 'termine', "Consultation neurologique"),
        # En attente / Confirmés
        (pat2, med3, now + timedelta(days=1), 'en_attente', "Céphalées récurrentes"),
        (pat3, med1, now + timedelta(days=2), 'confirme', "Suivi post-traitement cardiaque"),
        (pat1, med2, now + timedelta(days=4), 'en_attente', "Vaccination enfant"),
        (pat2, med1, now + timedelta(days=5), 'confirme', "Contrôle annuel cardiologie"),
        # Annulé
        (pat3, med3, now + timedelta(days=6), 'annule', "Annulé par le patient"),
    ]

    for p, m, dt, statut, motif in rdv_data:
        rdv, rdv_created = RendezVous.objects.get_or_create(
            patient=p, medecin=m, motif=motif,
            defaults={
                "statut": statut,
                "duree": 30,
                "date_heure": dt.replace(hour=random.choice([9, 10, 11, 14, 15])),
            },
        )

        if rdv_created and statut == 'termine':
            compte_rendu = (
                "Le patient présente des paramètres vitaux stables. "
                "Prescription d'un traitement léger et repos recommandé."
            )
            Consultation.objects.create(rendez_vous=rdv, compte_rendu=compte_rendu, est_cloture=True)

            if random.choice([True, False]):
                DemandeAnalyse.objects.create(
                    hopital=h_lokossa,
                    laborantin=u_lab,
                    patient=p,
                    patient_nom=p.user.last_name,
                    patient_prenom=p.user.first_name,
                    patient_email=p.user.email,
                    patient_telephone=p.user.telephone or '',
                    type_analyse="NFS et Bilan lipidique",
                    statut='en_cours',
                )

    # ━━━  RÉSUMÉ  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print(f"\n{'='*55}")
    print(f"  ✅  Seed Final Exécuté avec Succès !")
    print(f"{'='*55}")
    print(f"  Hôpital      : {h_lokossa.nom}")
    print(f"  Admin Hôpital: gillmarilin4@gmail.com")
    print(f"  Médecins     : marionbdj9 (Cardio), akouemaho (Pédia), gillbadji (Neuro)")
    print(f"  Laborantin   : marilinbadji@gmail.com")
    print(f"  Patients     : {Patient.objects.count()}")
    print(f"  RDV          : {RendezVous.objects.count()}")
    print(f"{'='*55}")


if __name__ == '__main__':
    run()
