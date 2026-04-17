import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')
django.setup()

from Chatbot.services import openai_chat_completion

print("Envoi d'un message test à OpenAI...")
try:
    response = openai_chat_completion([
        {"role": "user", "content": "Bonjour ! C'est un test pour valider l'intégration OpenAI. Réponds par 'Test validé avec succès' si tu reçois ça."}
    ])
    print("\n✅ RÉPONSE OPENAI :\n")
    print(response)
    print("\n✅ TEST RÉUSSI !")
except Exception as e:
    print("\n❌ ERREUR LORS DU TEST :")
    print(str(e))
