import re
import logging
from django.conf import settings
from twilio.rest import Client

logger = logging.getLogger(__name__)

def validate_and_format_benin_phone(phone_number):
    """
    Valide que le numéro fait 10 chiffres et commence par '01'.
    Retourne le format international +229XXXXXXXXXX ou None si invalide.
    """
    if not phone_number:
        return None
        
    # Nettoyer le numéro (garder uniquement les chiffres)
    clean_number = re.sub(r'\D', '', phone_number)
    
    # Vérifier le format : 10 chiffres commençant par 01
    if len(clean_number) == 10 and clean_number.startswith('01'):
        return f"+229{clean_number}"
    
    # Cas où l'utilisateur saisit déjà le format international par erreur
    if (len(clean_number) == 13 and clean_number.startswith('22901')):
        return f"+{clean_number}"
        
    return None

def send_twilio_sms(to_number, body):
    """Envoie un SMS via Twilio."""
    formatted_number = validate_and_format_benin_phone(to_number)
    if not formatted_number:
        logger.error(f"Numéro invalide pour Twilio : {to_number}")
        return False
        
    try:
        # En développement local sans Twilio configuré, on logue simplement
        if settings.TWILIO_ACCOUNT_SID == 'AC2db7785d7aad99f25c5c52da4930d622' and not settings.DEBUG:
            # Si on est sur Render, Twilio doit être fonctionnel
            pass

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=formatted_number
        )
        logger.info(f"SMS envoyé avec succès à {formatted_number} (SID: {message.sid})")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du SMS Twilio à {formatted_number}: {str(e)}")
        return False
