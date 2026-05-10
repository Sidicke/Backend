import os
import django
import sys

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from Chatbot.whatsapp_utils import send_whatsapp_message

def test_send(phone, text):
    print(f"🚀 Tentative d'envoi WhatsApp vers {phone}...")
    result = send_whatsapp_message(phone, text)
    if result.get('success'):
        print("✅ Message envoyé avec succès !")
    else:
        print(f"❌ Échec de l'envoi : {result.get('error')}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        test_send(sys.argv[1], sys.argv[2])
    else:
        print("Usage : python test_whatsapp.py <numero_sans_plus> <message>")
        print("Exemple : python test_whatsapp.py 22991000000 'Salut depuis HOPITEL'")
