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


def run():
    print("--- Début du Seed Mémoire Final (Restoration Idempotente) ---")

    # ━━━  1.  HÔPITAUX  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # LOKOSSA (Hôpital principal de la démo)
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

    # CNHU-HKM (Cotonou)
    h_cnhu, _ = Hopital.objects.update_or_create(
        nom="CNHU-HKM (Cotonou)",
        defaults=dict(
            adresse="Avenue Jean-Paul II, Cotonou", ville="Cotonou",
            latitude=6.3654, longitude=2.4183, telephone="+229 21 30 01 02", email="contact@cnhu.hopitel.com", is_active=True
        )
    )

    # CHUD Porto-Novo
    h_chud, _ = Hopital.objects.update_or_create(
        nom="CHUD Porto-Novo",
        defaults=dict(
            adresse="Ouando, Porto-Novo", ville="Porto-Novo",
            latitude=6.4969, longitude=2.6289, telephone="+229 20 21 21 21", email="contact@chud.hopitel.com", is_active=True
        )
    )

    # CHU Parakou
    h_parakou, _ = Hopital.objects.update_or_create(
        nom="CHU Parakou",
        defaults=dict(
            adresse="Quartier Banikanni, Parakou", ville="Parakou",
            latitude=9.3372, longitude=2.6303, telephone="+229 23 61 00 00", email="contact@chu-parakou.hopitel.com", is_active=True
        )
    )

    # Hôpital de Zone (Calavi)
    h_calavi, _ = Hopital.objects.update_or_create(
        nom="Hôpital de Zone (Calavi)",
        defaults=dict(
            adresse="Abomey-Calavi", ville="Calavi",
            latitude=6.4469, longitude=2.3524, telephone="+229 21 36 00 00", email="contact@hz-calavi.hopitel.com", is_active=True
        )
    )

    # Clinique Mahouna
    h_mahouna, _ = Hopital.objects.update_or_create(
        nom="Clinique Mahouna",
        defaults=dict(
            adresse="Quartier Patte d'Oie, Cotonou", ville="Cotonou",
            latitude=6.3750, longitude=2.4100, telephone="+229 21 33 44 55", email="contact@mahouna.hopitel.com", is_active=True
        )
    )

    print(f"  Hôpitaux créés : Lokossa, CNHU, CHUD, Parakou, Calavi, Mahouna.")


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

    all_hopitaux = [h_lokossa, h_cnhu, h_chud, h_parakou, h_calavi, h_mahouna]
    for h in all_hopitaux:
        for s in services_obj.values():
            HopitalService.objects.get_or_create(hopital=h, service=s)

    # ━━━  3.  UTILISATEURS (LOKOSSA & AUTRES)  ━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n--- Création des utilisateurs ---")

    # Admin général (plate-forme)
    admin = _get_or_create_user(
        email="admin@hopitel.com", password="HopitelAdmin2025*",
        role="admin_general", first_name="Ariel", last_name="Admin",
        telephone="22990000001", sexe="M", is_active=True,
    )

    # --- LOKOSSA (Comptes configurés par l'utilisateur) ---
    u_admin_lokossa = _get_or_create_user(
        email="gillmarilin4@gmail.com", password="AdminLokossa2025!",
        role="admin_hopital", first_name="Gill-Marilin", last_name="BADJI",
        hopital=h_lokossa, telephone="22990111111", sexe="F", is_active=True,
    )

    u_lokossa_med1 = _get_or_create_user(
        email="marionbdj9@gmail.com", password="MedecinCardio2025!",
        role="medecin", first_name="Marion", last_name="BADJI",
        hopital=h_lokossa, telephone="22990222222", sexe="F", is_active=True,
    )
    med_lok_1, _ = Medecin.objects.get_or_create(
        user=u_lokossa_med1, defaults={"numero_ordre": "BEN-MED-5001", "biographie": "Cardiologue interventionnelle."}
    )
    MedecinService.objects.get_or_create(medecin=med_lok_1, service=services_obj["Cardiologie"])

    u_lokossa_med2 = _get_or_create_user(
        email="akouemahogillchristmarilinbadj@gmail.com", password="MedecinPedia2025!",
        role="medecin", first_name="Akoue-Maho", last_name="GILL-CHRIST",
        hopital=h_lokossa, telephone="22990333333", sexe="M", is_active=True,
    )
    med_lok_2, _ = Medecin.objects.get_or_create(
        user=u_lokossa_med2, defaults={"numero_ordre": "BEN-MED-5002", "biographie": "Pédiatre néonatologue."}
    )
    MedecinService.objects.get_or_create(medecin=med_lok_2, service=services_obj["Pédiatrie"])

    u_lokossa_med3 = _get_or_create_user(
        email="gillbadji@gmail.com", password="MedecinNeuro2025!",
        role="medecin", first_name="Gill", last_name="BADJI",
        hopital=h_lokossa, telephone="22990444444", sexe="M", is_active=True,
    )
    med_lok_3, _ = Medecin.objects.get_or_create(
        user=u_lokossa_med3, defaults={"numero_ordre": "BEN-MED-5003", "biographie": "Neurologue."}
    )
    MedecinService.objects.get_or_create(medecin=med_lok_3, service=services_obj["Neurologie"])

    u_lab_lokossa = _get_or_create_user(
        email="marilinbadji@gmail.com", password="LaboLokossa2025!",
        role="laborantin", first_name="Marilin", last_name="BADJI",
        hopital=h_lokossa, telephone="22990555555", sexe="F", is_active=True,
    )
    Laborantin.objects.get_or_create(user=u_lab_lokossa, defaults={"laboratoire": "Laboratoire HZ Lokossa"})

    # --- AUTRES HÔPITAUX (CNHU, CHUD, MAHOUNA) ---
    u_admin_cnhu = _get_or_create_user(
        email="admin.cnhu@hopitel.com", password="AdminCnhu2025!",
        role="admin_hopital", first_name="Victor", last_name="ADEBAYO",
        hopital=h_cnhu, telephone="22990111112", sexe="M", is_active=True,
    )
    u_admin_chud = _get_or_create_user(
        email="admin.chud@hopitel.com", password="AdminChud2025!",
        role="admin_hopital", first_name="Claire", last_name="SOGLO",
        hopital=h_chud, telephone="22990222223", sexe="F", is_active=True,
    )
    u_admin_mahouna = _get_or_create_user(
        email="admin.mahouna@hopitel.com", password="AdminMahouna2025!",
        role="admin_hopital", first_name="Alain", last_name="KPONOU",
        hopital=h_mahouna, telephone="22990333334", sexe="M", is_active=True,
    )

    # Autres médecins
    u_med1 = _get_or_create_user(
        email="dr.dossou@hopitel.com", password="MedecinDossou123!", role="medecin", 
        first_name="Jean", last_name="DOSSOU", hopital=h_cnhu, telephone="22922222222", sexe="M", is_active=True
    )
    med1, _ = Medecin.objects.get_or_create(user=u_med1, defaults={"numero_ordre": "BEN-MED-1042", "biographie": "Praticien CNHU."})
    MedecinService.objects.get_or_create(medecin=med1, service=services_obj["Cardiologie"])

    u_med2 = _get_or_create_user(
        email="dr.tossou@hopitel.com", password="TossouPedia!99", role="medecin", 
        first_name="Marie", last_name="TOSSOU", hopital=h_mahouna, telephone="22933333333", sexe="F", is_active=True
    )
    med2, _ = Medecin.objects.get_or_create(user=u_med2, defaults={"numero_ordre": "BEN-MED-2055", "biographie": "Pédiatre Clinique."})
    MedecinService.objects.get_or_create(medecin=med2, service=services_obj["Pédiatrie"])
    
    u_med3 = _get_or_create_user(
        email="dr.amoussou@hopitel.com", password="AmoussouGyn!25", role="medecin", 
        first_name="Paul", last_name="AMOUSSOU", hopital=h_chud, telephone="22944444444", sexe="M", is_active=True
    )
    med3, _ = Medecin.objects.get_or_create(user=u_med3, defaults={"numero_ordre": "BEN-MED-3088", "biographie": "Gynécologue CHUD."})
    MedecinService.objects.get_or_create(medecin=med3, service=services_obj["Gynécologie"])

    # Autre laborantin
    u_lab_cnhu = _get_or_create_user(
        email="labo.agbo@hopitel.com", password="AgboLabo229#", role="laborantin", 
        first_name="Marc", last_name="AGBO", hopital=h_cnhu, telephone="22999999999", sexe="M", is_active=True
    )
    Laborantin.objects.get_or_create(user=u_lab_cnhu, defaults={"laboratoire": "BioSanté CNHU"})

    # Patients fictifs
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
    tous_medecins = [med_lok_1, med_lok_2, med_lok_3, med1, med2, med3]
    for m in tous_medecins:
        for jour in range(1, 6):  # Lundi–Vendredi
            Disponibilite.objects.get_or_create(
                medecin=m, jour_semaine=jour,
                defaults={"heure_debut": "08:00", "heure_fin": "16:00", "type": "recurrent"},
            )

    # ━━━  5.  RENDEZ-VOUS  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n--- Création des rendez-vous ---")
    now = timezone.now()

    rdv_data = [
        # Rendez-vous pour Lokossa
        (pat1, med_lok_1, now - timedelta(days=5), 'termine', "Contrôle de routine cardiaque"),
        (pat2, med_lok_1, now - timedelta(days=3), 'termine', "Douleurs thoraciques"),
        (pat3, med_lok_2, now - timedelta(days=2), 'termine', "Visite pédiatrique"),
        (pat1, med_lok_3, now - timedelta(days=1), 'termine', "Consultation neurologique"),
        
        # Rendez-vous pour les autres (CNHU, etc.)
        (pat2, med1, now + timedelta(days=1), 'en_attente', "Céphalées récurrentes"),
        (pat3, med1, now + timedelta(days=2), 'confirme', "Suivi post-traitement cardiaque"),
        (pat1, med2, now + timedelta(days=4), 'en_attente', "Vaccination enfant"),
        (pat2, med3, now + timedelta(days=5), 'confirme', "Contrôle annuel de routine"),
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
                    hopital=m.user.hopital,
                    laborantin=u_lab_lokossa if m.user.hopital == h_lokossa else u_lab_cnhu,
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
    print(f"  Hôpitaux total: {Hopital.objects.count()}")
    print(f"  Hôpital (Lokossa): {h_lokossa.nom}")
    print(f"  Admin Lokossa: gillmarilin4@gmail.com")
    print(f"  Médecins (Lokossa): marionbdj9, akouemaho, gillbadji")
    print(f"  Patients     : {Patient.objects.count()}")
    print(f"  RDV          : {RendezVous.objects.count()}")
    print(f"{'='*55}")


if __name__ == '__main__':
    run()
