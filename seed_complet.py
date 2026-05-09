import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Patient, Medecin, Laborantin
from hopitaux.models import Hopital, Service, HopitalService, MedecinService
from rendezvous.models import RendezVous, Disponibilite, PreEnregistrement, Consultation
from resultats.models import DemandeAnalyse
from messagerie.models import Message

User = get_user_model()

def run():
    print("[START] Début du Seed Exhaustif (v3) pour E-Santé Bénin")
    
    # ─────────────────────────────────────────────────────────
    # 0. Nettoyage (Optionnel mais recommandé pour la prod)
    # ─────────────────────────────────────────────────────────
    test_emails = [
        "admin@esante-benin.com", "admin.cnhu@esante.com", "admin.chud@esante.com", 
        "admin.parakou@esante.com", "admin.calavi@esante.com",
        "sidicke@esante.com", "patient2@esante.com", "patient3@esante.com", 
        "patient4@esante.com", "patient5@esante.com", "patient6@esante.com",
        "dossou@esante.com", "tossou@esante.com", "gnonlonfoun@esante.com",
        "houessou@esante.com", "agossou@esante.com", "zannou@esante.com",
        "bio@esante.com", "sika@esante.com", "mama@esante.com",
        "kodjo@esante.com", "sossa@esante.com", "ati@esante.com",
        "lab.cnhu@esante.com", "lab.chud@esante.com", "lab.parakou@esante.com"
    ]
    print(f"Nettoyage de {len(test_emails)} comptes de test...")
    User.objects.filter(email__in=test_emails).delete()
    
    # ─────────────────────────────────────────────────────────
    # 1. Hôpitaux (4 sites)
    # ─────────────────────────────────────────────────────────
    h_cnhu, _ = Hopital.objects.get_or_create(nom="CNHU-HKM Cotonou", defaults={"adresse": "Avenue Jean-Paul II, Cotonou", "ville": "Cotonou", "latitude": 6.3667, "longitude": 2.4000, "telephone": "+229 21 30 01 02", "email": "contact@cnhu.bj"})
    h_pnovo, _ = Hopital.objects.get_or_create(nom="CHUD Ouémé Plateau (Porto-Novo)", defaults={"adresse": "Ouando, Porto-Novo", "ville": "Porto-Novo", "latitude": 6.4967, "longitude": 2.6288, "telephone": "+229 20 21 21 21", "email": "contact@chud-op.bj"})
    h_parakou, _ = Hopital.objects.get_or_create(nom="CHU Borgou (Parakou)", defaults={"adresse": "Quartier Titirou, Parakou", "ville": "Parakou", "latitude": 9.3333, "longitude": 2.6333, "telephone": "+229 23 61 01 01", "email": "contact@chu-borgou.bj"})
    h_calavi, _ = Hopital.objects.get_or_create(nom="Hôpital de Zone d'Abomey-Calavi", defaults={"adresse": "Zogbadjè, Abomey-Calavi", "ville": "Calavi", "latitude": 6.4485, "longitude": 2.3512, "telephone": "+229 21 36 00 00", "email": "contact@hz-calavi.bj"})

    # ─────────────────────────────────────────────────────────
    # 2. Services & Médecins
    # ─────────────────────────────────────────────────────────
    services_data = [("Cardiologie", "Cœur"), ("Pédiatrie", "Enfants"), ("Gynécologie", "Femmes"), ("Neurologie", "Cerveau"), ("Ophtalmologie", "Yeux"), ("Chirurgie Générale", "Bloc")]
    services = {nom: Service.objects.get_or_create(nom=nom, defaults={"description": desc})[0] for nom, desc in services_data}

    for h, s_list in [(h_cnhu, ["Cardiologie", "Pédiatrie", "Gynécologie"]), (h_pnovo, ["Pédiatrie", "Neurologie"]), (h_parakou, ["Chirurgie Générale", "Ophtalmologie"]), (h_calavi, ["Gynécologie"])]:
        for s_name in s_list: HopitalService.objects.get_or_create(hopital=h, service=services[s_name])

    def create_user(email, role, hopital=None, first_name="User", last_name="Test"):
        u, _ = User.objects.get_or_create(email=email, defaults={"role": role, "hopital": hopital, "first_name": first_name, "last_name": last_name, "telephone": "0100000000", "sexe": "M"})
        u.set_password("Esante2025!"); u.is_active = True; u.is_email_verified = True; u.save()
        return u

    # Admins
    create_user("admin@esante-benin.com", "admin_general", None, "Super", "Admin")
    create_user("admin.cnhu@esante.com", "admin_hopital", h_cnhu, "Directeur", "CNHU")
    create_user("admin.chud@esante.com", "admin_hopital", h_pnovo, "Directeur", "CHUD")
    create_user("admin.parakou@esante.com", "admin_hopital", h_parakou, "Directeur", "PARAKOU")
    create_user("admin.calavi@esante.com", "admin_hopital", h_calavi, "Directeur", "CALAVI")

    # Médecins (3 par hôpital = 12 total)
    med_list = [
        # CNHU
        (h_cnhu, "dossou@esante.com", "Jean", "DOSSOU", "Cardiologie", "MED-001"),
        (h_cnhu, "tossou@esante.com", "Marie", "TOSSOU", "Pédiatrie", "MED-002"),
        (h_cnhu, "gnonlonfoun@esante.com", "Alain", "GNONLONFOUN", "Gynécologie", "MED-003"),
        # CHUD
        (h_pnovo, "houessou@esante.com", "Marc", "HOUESSOU", "Pédiatrie", "MED-004"),
        (h_pnovo, "agossou@esante.com", "Sophie", "AGOSSOU", "Neurologie", "MED-005"),
        (h_pnovo, "zannou@esante.com", "Basile", "ZANNOU", "Pédiatrie", "MED-006"),
        # PARAKOU
        (h_parakou, "bio@esante.com", "Yacoubou", "BIO", "Chirurgie Générale", "MED-007"),
        (h_parakou, "sika@esante.com", "Félicien", "SIKA", "Ophtalmologie", "MED-008"),
        (h_parakou, "mama@esante.com", "Saidou", "MAMA", "Chirurgie Générale", "MED-009"),
        # CALAVI
        (h_calavi, "kodjo@esante.com", "René", "KODJO", "Gynécologie", "MED-010"),
        (h_calavi, "sossa@esante.com", "Pierrette", "SOSSA", "Gynécologie", "MED-011"),
        (h_calavi, "ati@esante.com", "Gérard", "ATI", "Gynécologie", "MED-012"),
    ]

    med_objs = {}
    u_med_objs = {}
    for hop, email, fn, ln, s_name, order in med_list:
        u = create_user(email, "medecin", hop, fn, ln)
        med, _ = Medecin.objects.get_or_create(user=u, defaults={"numero_ordre": order})
        MedecinService.objects.get_or_create(medecin=med, service=services[s_name])
        Disponibilite.objects.get_or_create(medecin=med, jour_semaine=1, defaults={"heure_debut": "08:00", "heure_fin": "12:00", "type": "recurrent"})
        med_objs[email] = med
        u_med_objs[email] = u

    med1 = med_objs["dossou@esante.com"]
    u_med1 = u_med_objs["dossou@esante.com"]
    med2 = med_objs["tossou@esante.com"]

    # Laborantins (3 au total)
    labos = [
        (h_cnhu, "lab.cnhu@esante.com", "Paul", "DOSSOU-LAB", "Labo CNHU"),
        (h_pnovo, "lab.chud@esante.com", "Anne", "MARIE-LAB", "Labo CHUD Porto-Novo"),
        (h_parakou, "lab.parakou@esante.com", "Abdou", "RAMANE-LAB", "Bio-Lab Parakou"),
    ]
    lab_objs = {}
    for hop, email, fn, ln, lab_name in labos:
        u = create_user(email, "laborantin", hop, fn, ln)
        Laborantin.objects.get_or_create(user=u, defaults={"laboratoire": lab_name})
        lab_objs[email] = u

    u_lab1 = lab_objs["lab.cnhu@esante.com"]

    # ─────────────────────────────────────────────────────────
    # 3. Patients (6 profils variés)
    # ─────────────────────────────────────────────────────────
    def create_patient(email, fn, ln):
        u = create_user(email, "patient", None, fn, ln)
        p, _ = Patient.objects.get_or_create(user=u, defaults={"groupe_sanguin": "O+"})
        return p

    p1 = create_patient("sidicke@esante.com", "Sidicke", "TRAORE") # Flow complet
    p2 = create_patient("patient2@esante.com", "Alice", "BENIN")   # RDV en attente
    p3 = create_patient("patient3@esante.com", "Bob", "CANCEL")    # Historique annulé
    p4 = create_patient("patient4@esante.com", "Claire", "LABO")   # Que du labo
    p5 = create_patient("patient5@esante.com", "David", "INTAKE") # Que de l'intake
    p6 = create_patient("patient6@esante.com", "Eve", "NEW")       # Nouveau né (vidé)

    # ACTIONS PATIENT 1 (Sidicke): RDV Terminé + Consultation + Message + Labo
    demain = timezone.now() + timedelta(days=1)
    hier = timezone.now() - timedelta(days=2)
    rdv_p1, _ = RendezVous.objects.get_or_create(patient=p1, medecin=med1, defaults={"date_heure": hier, "statut": "termine", "motif": "Contrôle cardio", "duree": 30})
    Consultation.objects.get_or_create(rendez_vous=rdv_p1, defaults={"compte_rendu": "Stable. Analyse NFS requise.", "prescription": "Abord cardio", "est_cloture": True})
    DemandeAnalyse.objects.get_or_create(patient=p1, hopital=h_cnhu, laborantin=u_lab1, defaults={"patient_nom": "TRAORE", "patient_prenom": "Sidicke", "type_analyse": "NFS", "statut": "termine"})
    Message.objects.get_or_create(expediteur=p1.user, destinataire=u_med1, defaults={"contenu": "Bonjour Docteur, j'ai fini mes analyses."})

    # ACTIONS PATIENT 2 (Alice): RDV en attente
    RendezVous.objects.get_or_create(patient=p2, medecin=med2, defaults={"date_heure": demain, "statut": "en_attente", "motif": "Suivi grossesse", "duree": 30})

    # ACTIONS PATIENT 3 (Bob): RDV Annulé
    RendezVous.objects.get_or_create(patient=p3, medecin=med1, defaults={"date_heure": hier, "statut": "annule", "motif": "Consultation simple", "duree": 30})

    # ACTIONS PATIENT 4 (Claire): Demande labo en cours
    DemandeAnalyse.objects.get_or_create(patient=p4, hopital=h_cnhu, laborantin=u_lab1, defaults={"patient_nom": "LABO", "patient_prenom": "Claire", "type_analyse": "Glycémie", "statut": "en_cours"})

    # ACTIONS PATIENT 5 (David): Intake (Pré-enregistrement) sur un RDV futur
    rdv_p5, _ = RendezVous.objects.get_or_create(patient=p5, medecin=med1, defaults={"date_heure": demain + timedelta(hours=2), "statut": "en_attente", "motif": "Palpitations", "duree": 30})
    PreEnregistrement.objects.get_or_create(rendez_vous=rdv_p5, defaults={"symptomes_principaux": "Cœur qui bat vite au repos", "debut_symptomes": timezone.now().date()})

    print("[SUCCESS] Seed v3 terminé. 4 Hôpitaux, 12 Médecins, 6 Patients et 3 Labos injectés avec succès.")

if __name__ == '__main__':
    run()
