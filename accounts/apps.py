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
            backend_url = os.environ.get('BACKEND_URL', 'https://backend-soutenance-1et0.onrender.com')
            requests.get(f"{backend_url.rstrip('/')}/api/", timeout=5)
            
            # 2. Ping le microservice WhatsApp
            wa_url = os.environ.get('WHATSAPP_SERVICE_URL', 'https://whatsapp-service-o5rs.onrender.com')
            requests.get(f"{wa_url.rstrip('/')}/health", timeout=5)
        except Exception:
            pass
        
        time.sleep(600)

class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            thread = threading.Thread(target=ping_services, daemon=True)
            thread.start()
