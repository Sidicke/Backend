import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# URL du microservice WhatsApp (Baileys)
WHATSAPP_SERVICE_URL = getattr(settings, 'WHATSAPP_SERVICE_URL', 'http://localhost:3001')

def send_whatsapp_message(phone, message):
    """
    Envoie un message WhatsApp via le microservice Node.js Baileys.
    """
    if not getattr(settings, 'ENABLE_WHATSAPP', True):
        return {"success": False, "error": "WhatsApp disabled in configuration"}

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
