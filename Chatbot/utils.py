import requests
from django.conf import settings


SYSTEM_PROMPT = """Tu es un assistant médical virtuel pour le Bénin. Tu réponds aux questions générales sur la santé, la prévention, les symptômes courants, mais tu ne donnes jamais de diagnostic médical. Tu ne prescris jamais de médicament. Tu orientes toujours vers un professionnel de santé en cas de doute. Si la question concerne une urgence (difficulté à respirer, douleur thoracique, perte de conscience, etc.), réponds immédiatement d'appeler les secours ou de se rendre aux urgences les plus proches. Réponds en français."""


def appeler_chatbot(question):
    """
    Envoie une question au service externe (OpenAI) et retourne la réponse.
    Retourne un tuple (reponse, modele) ou lève une exception.
    """
    api_url = getattr(settings, 'CHATBOT_API_URL', 'https://api.openai.com/v1/chat/completions')
    api_key = getattr(settings, 'CHATBOT_API_KEY', '')
    model = getattr(settings, 'CHATBOT_MODEL', 'gpt-3.5-turbo')
    timeout = getattr(settings, 'CHATBOT_TIMEOUT', 30)

    if not api_key:
        raise ValueError("La clé API du chatbot n'est pas configurée.")

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    payload = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': question},
        ],
        'max_tokens': 1000,
        'temperature': 0.7,
    }

    response = requests.post(api_url, json=payload, headers=headers, timeout=timeout)
    response.raise_for_status()

    data = response.json()
    reponse_text = data['choices'][0]['message']['content'].strip()

    return reponse_text, model
