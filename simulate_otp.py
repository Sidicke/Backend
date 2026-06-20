import os
import django
import sys
import random

# Initialisation de Django pour utiliser les composants du projet
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from Chatbot.whatsapp_utils import send_whatsapp_message, format_whatsapp_phone

def main():
    if len(sys.argv) < 2:
        print("\n❌ Erreur : Numéro de téléphone manquant.")
        print("💡 Usage : python simulate_otp.py <numero_telephone>")
        print("💡 Exemple : python simulate_otp.py 0190333333\n")
        sys.exit(1)

    phone = sys.argv[1]
    
    # Génération d'un OTP aléatoire à 6 chiffres
    otp = f"{random.randint(0, 999999):06d}"
    
    # Message type OTP
    message = (
        f"🔐 *HOPITEL - Sécurité*\n\n"
        f"Votre code de vérification est : *{otp}*\n\n"
        f"Ne le partagez avec personne."
    )
    
    formatted_phone = format_whatsapp_phone(phone)
    
    print("=" * 40)
    print(f"📱 Numéro saisi    : {phone}")
    print(f"🛠 Numéro formaté   : +{formatted_phone}")
    print(f"🔑 OTP Généré      : {otp}")
    print("=" * 40)
    print("⏳ Envoi du message en cours...")
    
    # Appel de la fonction d'envoi du microservice Node.js
    result = send_whatsapp_message(phone, message)
    
    if result.get("success"):
        print(f"\n✅ SUCCÈS : OTP envoyé avec succès sur WhatsApp au {formatted_phone} !")
    else:
        error_msg = result.get("error", "Erreur inconnue")
        print(f"\n❌ ÉCHEC : Impossible d'envoyer le message.")
        print(f"Détail : {error_msg}")

if __name__ == '__main__':
    main()
