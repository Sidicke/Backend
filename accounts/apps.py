import os
import threading
import time
import requests
from django.apps import AppConfig

def ping_services():
    """Pingue les services Render toutes les 10 minutes (600s) pour empêcher la mise en veille du plan gratuit."""
    while True:
        try:
            # 1. Ping le backend Django lui-même
            backend_url = os.environ.get('BACKEND_URL', 'https://backend-soutenance.onrender.com')
            # Optionnel: On met un timeout très court pour ne pas bloquer le thread si le service est lent
            requests.get(f"{backend_url.rstrip('/')}/api/", timeout=5)
            
            # 2. Ping le microservice WhatsApp
            wa_url = os.environ.get('WHATSAPP_SERVICE_URL', 'https://whatsapp-service-o5rs.onrender.com')
            requests.get(f"{wa_url.rstrip('/')}/health", timeout=5)
        except Exception:
            # Silence total : si ça échoue (pas de réseau, serveur éteint), on s'en moque, on réessaiera
            pass
        
        # Attendre 10 minutes (Render met en veille après 15 minutes d'inactivité)
        time.sleep(600)

class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # Pour éviter de lancer le thread deux fois avec le "runserver" de Django local
        if os.environ.get('RUN_MAIN', None) != 'true':
            # Lance le script de maintien en vie en arrière-plan sans bloquer le serveur
            thread = threading.Thread(target=ping_services, daemon=True)
            thread.start()
