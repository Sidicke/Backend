import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def format_whatsapp_phone(phone):
    """Nettoie et formate automatiquement le numéro pour WhatsApp (surtout Bénin)."""
    if not phone:
        return ""
    clean = "".join(filter(str.isdigit, str(phone)))
    
    # Strip l'indicatif 229 s'il est présent
    if clean.startswith("229"):
        clean = clean[3:]
        
    # Strip le préfixe 01 s'il est présent
    if clean.startswith("01"):
        clean = clean[2:]
        
    # À ce stade, pour un numéro béninois valide, on doit avoir 8 chiffres
    if len(clean) == 8:
        return "229" + clean
        
    # Si le format ne correspond pas à 8 chiffres (numéro étranger ou autre)
    # on retourne simplement les chiffres initiaux
    return "".join(filter(str.isdigit, str(phone)))

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

