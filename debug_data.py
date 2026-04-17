import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Patient, Medecin, Laborantin
from rendezvous.models import RendezVous, Consultation
from messagerie.models import Message

User = get_user_model()

print("--- Database Stats ---")
print(f"Users: {User.objects.count()}")
print(f"Patients: {Patient.objects.count()}")
print(f"Medecins: {Medecin.objects.count()}")
print(f"Laborantins: {Laborantin.objects.count()}")
print(f"RendezVous: {RendezVous.objects.count()}")
print(f"Consultations: {Consultation.objects.count()}")
print(f"Messages: {Message.objects.count()}")

print("\n--- Orphan Check ---")
orphans_rdv = RendezVous.objects.filter(patient__user__isnull=True).count()
print(f"RendezVous without linked Patient User: {orphans_rdv}")

orphans_msg = Message.objects.filter(expediteur__isnull=True).count()
print(f"Messages without expediteur: {orphans_msg}")

print("\n--- Sample Patient ---")
p = Patient.objects.first()
if p:
    print(f"Patient: {p.user.get_full_name()} ({p.user.email})")
    print(f"RDVs for this patient: {RendezVous.objects.filter(patient=p).count()}")
    print(f"Messages for this user: {Message.objects.filter(expediteur=p.user).count() + Message.objects.filter(destinataire=p.user).count()}")
else:
    print("No patient found.")

print("\n--- Sample Medecin ---")
m = Medecin.objects.first()
if m:
    print(f"Medecin: {m.user.get_full_name()} ({m.user.email})")
    print(f"RDVs for this medecin: {RendezVous.objects.filter(medecin=m).count()}")
else:
    print("No medecin found.")
