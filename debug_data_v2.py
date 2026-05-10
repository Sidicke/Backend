import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Patient, Medecin, Laborantin
from rendezvous.models import RendezVous, Consultation
from messagerie.models import Message

User = get_user_model()

print("--- Patients & RDVs ---")
for p in Patient.objects.all():
    count = RendezVous.objects.filter(patient=p).count()
    print(f"Patient: {p.user.get_full_name()} ({p.user.email}) -> {count} RDVs")

print("\n--- Medecins & RDVs ---")
for m in Medecin.objects.all():
    count = RendezVous.objects.filter(medecin=m).count()
    print(f"Medecin: {m.user.get_full_name()} ({m.user.email}) -> {count} RDVs")

print("\n--- All RDVs ---")
for r in RendezVous.objects.all():
    p_name = r.patient.user.get_full_name() if r.patient else "None"
    m_name = r.medecin.user.get_full_name() if r.medecin else "None"
    print(f"RDV ID {r.id}: Patient {p_name}, Medecin {m_name}, Date {r.date_heure}, Statut {r.statut}")

print("\n--- All Messages ---")
for msg in Message.objects.all():
    print(f"Msg ID {msg.id}: {msg.expediteur.email} -> {msg.destinataire.email} : {msg.contenu[:30]}")
