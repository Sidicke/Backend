import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def format_whatsapp_phone(phone):
    """Nettoie et formate automatique le numéro pour WhatsApp (surtout Bénin)."""
    if not phone:
        return ""
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    
    # Format international déjà correct avec 229+8 chiffres (ex: 22997XXXXXX = 11 chiffres)
    if len(clean_phone) == 11 and clean_phone.startswith('229') and not clean_phone.startswith('22901'):
        return clean_phone  # Déjà bon, on ne touche pas
    # Format 229 + 01 + 8 chiffres (ex: 22901XXXXXXXX) → on retire le 01
    if len(clean_phone) == 13 and clean_phone.startswith('22901'):
        return "229" + clean_phone[5:]
    # Nouveau format Bénin 10 chiffres (ex: 0197XXXXXX)
    if len(clean_phone) == 10 and clean_phone.startswith('01'):
        return "229" + clean_phone[2:]
    # Ancien format local à 8 chiffres
    if len(clean_phone) == 8:
        return "229" + clean_phone

    return clean_phone

def send_whatsapp_message(phone, message):
    """
    Envoie un message WhatsApp via le microservice Node.js Baileys.
    """
    if not getattr(settings, 'ENABLE_WHATSAPP', True):
        return {"success": False, "error": "WhatsApp disabled in configuration"}

    # Lire l'URL dynamiquement à chaque appel (pas au démarrage du module)
    # pour prendre en compte les changements de variables d'environnement
    whatsapp_url = getattr(settings, 'WHATSAPP_SERVICE_URL', 'http://localhost:3001')

    clean_phone = format_whatsapp_phone(phone)
    
    # Redirection globale en mode soutenance
    if getattr(settings, 'SOUTENANCE_MODE', False):
        clean_phone = settings.SOUTENANCE_WHATSAPP

    if not clean_phone:
        return {"success": False, "error": "Numero de telephone invalide"}

    url = f"{whatsapp_url}/send-message"
    payload = {
        "phone": clean_phone,
        "message": message
    }
    
    try:
        # Timeout de 45s pour permettre au service Render de se réveiller
        # (Render Free Tier peut prendre jusqu'à 50s au premier appel après inactivité)
        response = requests.post(url, json=payload, timeout=45)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de l'envoi du message WhatsApp : {e}")
        return {"success": False, "error": str(e)}

