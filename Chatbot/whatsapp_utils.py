import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# URL du microservice WhatsApp (Baileys)
WHATSAPP_SERVICE_URL = getattr(settings, 'WHATSAPP_SERVICE_URL', 'http://localhost:3001')

def send_whatsapp_message(phone, message):
    """
    Envoie un message WhatsApp via le microservice Node.js Baileys.
    :param phone: Numéro de téléphone au format international (ex: 22991000000)
    :param message: Contenu du message
    """
    url = f"{WHATSAPP_SERVICE_URL}/send-message"
    payload = {
        "phone": phone,
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de l'envoi du message WhatsApp : {e}")
        return {"success": False, "error": str(e)}
