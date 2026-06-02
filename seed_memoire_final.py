import os
import django
from datetime import timedelta, date, time
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

def clear_data():
    """Nettoie les données existantes pour repartir sur une base propre."""
    print("--- Nettoyage complet des données de démo ---")
    
    # 1. Liste des emails à nettoyer
    emails_to_clear = [
        "admin@hopitel.com", "dr.dossou@hopitel.com", "dr.tossou@hopitel.com", 
        "dr.amoussou@hopitel.com", "labo.agbo@hopitel.com", "sidicke@hopitel.com", 
        "koffi@hopitel.com", "amina@hopitel.com", "admin.cnhu@hopitel.com",
        "admin.chud@hopitel.com", "admin.parakou@hopitel.com", "admin.calavi@hopitel.com",
        "lab.cnhu@hopitel.com", "lab.chud@hopitel.com", "lab.parakou@hopitel.com",
        "admin@esante.com", "dossou@esante.com", "tossou@esante.com", "sidicke@esante.com"
    ]
    User.objects.filter(email__in=emails_to_clear).delete()
    
    # 2. Liste des hôpitaux à nettoyer
    hosp_names = [
        "CNHU-HKM (Cotonou)", "CHUD Porto-Novo", "CHU Parakou", 
        "Hôpital de Zone (Calavi)", "Clinique Mahouna", "CNHU-HKM Cotonou", "CHD Ouémé-Plateau"
    ]
    Hopital.objects.filter(nom__in=hosp_names).delete()

def run():
    clear_data()
    print("--- Début du Seed Mémoire Final (Restoration complète) ---")
    
    # 1. HÔPITAUX ET SERVICES
    h_cnhu = Hopital.objects.create(
        nom="CNHU-HKM (Cotonou)", adresse="Avenue Jean-Paul II, Cotonou", ville="Cotonou",
        latitude=6.3654, longitude=2.4183, telephone="+229 21 30 01 02", email="contact@cnhu.hopitel.com", is_active=True
    )
    h_chud = Hopital.objects.create(
        nom="CHUD Porto-Novo", adresse="Ouando, Porto-Novo", ville="Porto-Novo",
        latitude=6.4969, longitude=2.6289, telephone="+229 20 21 21 21", email="contact@chud.hopitel.com", is_active=True
    )
    h_parakou = Hopital.objects.create(
        nom="CHU Parakou", adresse="Quartier Banikanni, Parakou", ville="Parakou",
        latitude=9.3372, longitude=2.6303, telephone="+229 23 61 00 00", email="contact@chu-parakou.hopitel.com", is_active=True
    )
    h_calavi = Hopital.objects.create(
        nom="Hôpital de Zone (Calavi)", adresse="Abomey-Calavi", ville="Calavi",
        latitude=6.4469, longitude=2.3524, telephone="+229 21 36 00 00", email="contact@hz-calavi.hopitel.com", is_active=True
    )
    h_mahouna = Hopital.objects.create(
        nom="Clinique Mahouna", adresse="Quartier Patte d'Oie, Cotonou", ville="Cotonou",
        latitude=6.3750, longitude=2.4100, telephone="+229 21 33 44 55", email="contact@mahouna.hopitel.com", is_active=True
    )

    services_data = [
        ("Cardiologie", "Maladies du cœur."),
        ("Pédiatrie", "Médecine des enfants."),
        ("Gynécologie", "Santé de la femme."),
        ("Ophtalmologie", "Maladies des yeux."),
        ("Chirurgie Générale", "Interventions chirurgicales."),
        ("Neurologie", "Système nerveux.")
    ]
    
    services_obj = {}
    for nom, desc in services_data:
        s, _ = Service.objects.get_or_create(nom=nom, defaults={"description": desc, "is_active": True})
        services_obj[nom] = s

    for h in [h_cnhu, h_chud, h_parakou, h_calavi, h_mahouna]:
        for s in services_obj.values():
            HopitalService.objects.create(hopital=h, service=s)

    # 2. UTILISATEURS
    admin = User.objects.create_user(email="admin@hopitel.com", password="HopitelAdmin2025*", role="admin_general", 
                                     first_name="Ariel", last_name="Admin", telephone="22990000001", sexe="M", is_active=True)

    # Admin Hôpitaux
    u_admin_cnhu = User.objects.create_user(email="admin.cnhu@hopitel.com", password="AdminCnhu2025!", role="admin_hopital", 
                                     first_name="Victor", last_name="ADEBAYO", hopital=h_cnhu, telephone="22990111111", sexe="M", is_active=True)
    
    u_admin_chud = User.objects.create_user(email="admin.chud@hopitel.com", password="AdminChud2025!", role="admin_hopital", 
                                     first_name="Claire", last_name="SOGLO", hopital=h_chud, telephone="22990222222", sexe="F", is_active=True)
                                     
    u_admin_mahouna = User.objects.create_user(email="admin.mahouna@hopitel.com", password="AdminMahouna2025!", role="admin_hopital", 
                                     first_name="Alain", last_name="KPONOU", hopital=h_mahouna, telephone="22990333333", sexe="M", is_active=True)

    # Médecins (CNHU)
    u_med1 = User.objects.create_user(email="dr.dossou@hopitel.com", password="MedecinDossou123!", role="medecin", 
                                     first_name="Jean", last_name="DOSSOU", hopital=h_cnhu, telephone="22922222222", sexe="M", is_active=True)
    med1 = Medecin.objects.create(user=u_med1, numero_ordre="BEN-MED-1042", biographie="Expert en cardiologie interventionnelle.")
    MedecinService.objects.create(medecin=med1, service=services_obj["Cardiologie"])

    u_med1b = User.objects.create_user(email="dr.kodjo@hopitel.com", password="MedecinKodjo123!", role="medecin", 
                                     first_name="Fabrice", last_name="KODJO", hopital=h_cnhu, telephone="22922222223", sexe="M", is_active=True)
    med1b = Medecin.objects.create(user=u_med1b, numero_ordre="BEN-MED-1043", biographie="Spécialiste de la chirurgie mini-invasive.")
    MedecinService.objects.create(medecin=med1b, service=services_obj["Chirurgie Générale"])

    # Médecin (Mahouna)
    u_med2 = User.objects.create_user(email="dr.tossou@hopitel.com", password="TossouPedia!99", role="medecin", 
                                     first_name="Marie", last_name="TOSSOU", hopital=h_mahouna, telephone="22933333333", sexe="F", is_active=True)
    med2 = Medecin.objects.create(user=u_med2, numero_ordre="BEN-MED-2055", biographie="Spécialisée en médecine néonatale.")
    MedecinService.objects.create(medecin=med2, service=services_obj["Pédiatrie"])

    # Médecin (CHUD)
    u_med3 = User.objects.create_user(email="dr.amoussou@hopitel.com", password="AmoussouGyn!25", role="medecin", 
                                     first_name="Paul", last_name="AMOUSSOU", hopital=h_chud, telephone="22944444444", sexe="M", is_active=True)
    med3 = Medecin.objects.create(user=u_med3, numero_ordre="BEN-MED-3088", biographie="Excellente prise en charge des grossesses à risque.")
    MedecinService.objects.create(medecin=med3, service=services_obj["Gynécologie"])

    # Patients
    u_pat1 = User.objects.create_user(email="sidicke@hopitel.com", password="PatientSidicke01", role="patient", 
                                     first_name="Sidicke", last_name="TRAORÉ", telephone="22990000005", sexe="M", is_active=True)
    pat1 = Patient.objects.create(user=u_pat1, groupe_sanguin="O+", npi="1029384756")

    u_pat2 = User.objects.create_user(email="koffi@hopitel.com", password="PatientKoffi02", role="patient", 
                                     first_name="Koffi", last_name="MENSAH", telephone="22990000006", sexe="M", is_active=True)
    pat2 = Patient.objects.create(user=u_pat2, groupe_sanguin="A+", npi="2938475610")

    u_pat3 = User.objects.create_user(email="amina@hopitel.com", password="PatientAmina03", role="patient", 
                                     first_name="Amina", last_name="SALIU", telephone="22990000007", sexe="F", is_active=True)
    pat3 = Patient.objects.create(user=u_pat3, groupe_sanguin="B-", npi="9384756102")

    # Laborantin (CNHU)
    u_lab = User.objects.create_user(email="labo.agbo@hopitel.com", password="AgboLabo229#", role="laborantin", 
                                     first_name="Marc", last_name="AGBO", hopital=h_cnhu, telephone="22999999999", sexe="M", is_active=True)
    laborantin = Laborantin.objects.create(user=u_lab, laboratoire="BioSanté CNHU")

    # 3. DISPONIBILITÉS & RDV
    medecins = [med1, med1b, med2, med3]
    patients = [pat1, pat2, pat3]
    
    # Création des disponibilités (Lundi à Vendredi)
    for m in medecins:
        for jour in range(1, 6):
            Disponibilite.objects.create(medecin=m, jour_semaine=jour, heure_debut="08:00", heure_fin="16:00", type="recurrent")

    # Création de RDV Historiques et Futurs pour garnir les tableaux de bord
    now = timezone.now()
    
    rdv_data = [
        # RDV Terminés
        (pat1, med1, now - timedelta(days=5), 'termine', "Contrôle de routine cardiaque"),
        (pat2, med1, now - timedelta(days=3), 'termine', "Douleurs thoraciques"),
        (pat3, med2, now - timedelta(days=2), 'termine', "Visite pédiatrique pour le petit"),
        (pat1, med3, now - timedelta(days=1), 'termine', "Consultation de suivi gyncélogique"),
        # RDV en attente / prévus
        (pat2, med1b, now + timedelta(days=1), 'en_attente', "Préparation intervention chirurgicale"),
        (pat3, med1, now + timedelta(days=2), 'confirme', "Suivi post-traitement"),
        (pat1, med2, now + timedelta(days=4), 'en_attente', "Vaccination enfant"),
        (pat2, med3, now + timedelta(days=5), 'confirme', "Contrôle annuel"),
        # RDV Annulés
        (pat3, med1b, now + timedelta(days=6), 'annule', "Annulé par le patient"),
    ]

    for p, m, dt, statut, motif in rdv_data:
        rdv = RendezVous.objects.create(
            patient=p, medecin=m, statut=statut, duree=30,
            date_heure=dt.replace(hour=random.choice([9, 10, 11, 14, 15])), motif=motif
        )
        
        # Création de consultation pour les RDV terminés
        if statut == 'termine':
            compte_rendu = "Le patient présente des paramètres vitaux stables. Prescription d'un traitement léger et repos recommandé."
            cons = Consultation.objects.create(rendez_vous=rdv, compte_rendu=compte_rendu, est_cloture=True)
            
            # Pour certains terminés, on génère une Demande d'analyse au labo
            if random.choice([True, False]):
                DemandeAnalyse.objects.create(
                    hopital=m.user.hopital,
                    laborantin=u_lab,
                    patient=p,
                    patient_nom=p.user.last_name,
                    patient_prenom=p.user.first_name,
                    patient_email=p.user.email,
                    patient_telephone=p.user.telephone or '',
                    type_analyse="NFS et Bilan lipidique",
                    statut='en_cours'
                )

    print(f"--- [SUCCESS] Seed Final Exécuté ---")
    print(f"Hôpitaux : {Hopital.objects.count()} (CNHU, CHUD, Parakou, Calavi, Mahouna)")
    print(f"Admins Hôpital créés pour CNHU, CHUD et Mahouna")
    print(f"Patients: {Patient.objects.count()} | Médecins: {Medecin.objects.count()} | RDV: {RendezVous.objects.count()}")

if __name__ == '__main__':
    run()
