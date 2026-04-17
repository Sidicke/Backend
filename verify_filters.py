import os
import django
from django.db.models import Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Patient, Medecin, Laborantin
from rendezvous.models import RendezVous, Consultation
from messagerie.models import Message
from resultats.models import Resultat, DemandeAnalyse

User = get_user_model()

def test_filters(email):
    print(f"\n--- Testing filters for user: {email} ---")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        print(f"User {email} not found.")
        return

    # Simulate RendezVousListCreateView.get_queryset
    rdv_qs = RendezVous.objects.all()
    if user.role == 'patient':
        rdv_qs = rdv_qs.filter(patient__user=user)
    elif user.role == 'medecin':
        rdv_qs = rdv_qs.filter(medecin__user=user)
    elif user.role == 'admin_hopital':
        rdv_qs = rdv_qs.filter(medecin__user__hopital=user.hopital)
    
    print(f"RendezVous visible: {rdv_qs.count()}")

    # Simulate ResultatListCreateView.get_queryset
    res_qs = Resultat.objects.all()
    if user.role == 'patient':
        res_qs = res_qs.filter(Q(patient__user=user) | Q(patient_email_externe=user.email))
    elif user.role == 'laborantin':
        res_qs = res_qs.filter(hopital=user.hopital)
    
    print(f"Resultats visible: {res_qs.count()}")

    # Simulate ConversationListView
    msg_filter = (Q(expediteur=user) | Q(destinataire=user))
    if user.role == 'admin_hopital':
        msg_filter |= Q(consultation__rendez_vous__medecin__user__hopital=user.hopital)
    
    msg_qs = Message.objects.filter(msg_filter & Q(consultation__isnull=False))
    print(f"Consultation messages visible: {msg_qs.count()}")

# Test with Jean Tossou (patient@test.com) - has 4 RDVs
test_filters('patient@test.com')

# Test with patient1@test.com - has 3 Messages (consultation?)
test_filters('patient1@test.com')

# Test with a Laborantin
lab = User.objects.filter(role='laborantin').first()
if lab:
    test_filters(lab.email)
