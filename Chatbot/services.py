import requests
import json
from django.conf import settings
import logging
from .rag_tools import TOOLS_SCHEMA, execute_tool_call

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un Assistant Médical Intelligent développé pour E-Santé Bénin.
Tu es là pour guider les patients, les conseiller de manière extrêmement professionnelle, et les aider à trouver un médecin, un hôpital, ou un créneau de RDV.

RÈGLES STRICTES :
1. Tu parles EXCLUSIVEMENT aux patients.
2. Si le patient cherche un médecin ou un hôpital, EXÉCUTE la fonction associée.
3. Si le patient cherche une disponibilité pour un médecin après que tu aies obtenu la liste, EXÉCUTE la fonction de recherche de disponibilité.
4. SOIS RASSURANT ET PROFESSIONNEL. Donne des conseils de vie sains, mais AJOUTE TOUJOURS : "Je suis une IA, veuillez valider ces conseils avec un professionnel de la santé." si l'utilisateur décrit des symptômes.
5. AUCUN DIAGNOSTIC MÉDICAL.
6. Ne communique AUCUNE donnée personnelle issue de dossiers.
7. Quand tu proposes de prendre RDV suite à une recherche, si c'est possible, précise que l'utilisateur peut accomplir cette action dans l'application.
8. Si tu as trouvé des résultats (Hôpitaux, Medecins...) et que tu veux proposer une navigation à l'utilisateur, ajoute STRICTEMENT à la toute fin de ton message un bloc JSON au format suivant (sans commentaires) :
```json
[
  {"type": "redirect", "label": "Prendre RDV avec Dr. Nom", "url": "/medecins/ID/rendezvous"},
  {"type": "redirect", "label": "Voir Hôpital", "url": "/hopitaux/ID"}
]
```
N'ajoute ce bloc QUE SI des IDs valides ont été renvoyés par tes outils.

IMPORTANT: Ta réponse doit être claire, formatée proprement (Markdown autorisé), courte et rassurante.
"""

def openai_chat_completion(history_messages):
    """
    Appelle l'API Groq (OpenAI-compatible) avec support du RAG / Function Calling.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.CHATBOT_API_KEY}"
    }

    # Préparation du payload initial
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history_messages
    
    payload = {
        "model": settings.CHATBOT_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "tools": TOOLS_SCHEMA,
        "tool_choice": "auto"
    }

    try:
        response = requests.post(
            settings.CHATBOT_API_URL,
            json=payload,
            headers=headers,
            timeout=getattr(settings, "CHATBOT_TIMEOUT", 30)
        )
        
        if not response.ok:
            logger.warning(f"Échec Groq: {response.text}")
            response.raise_for_status()

        data = response.json()
        if "choices" not in data or len(data["choices"]) == 0:
            raise ValueError(f"Format de réponse inattendu: {data}")

        message = data["choices"][0]["message"]
        
        # Vérifier si l'IA veut appeler un ou plusieurs outils
        if message.get("tool_calls"):
            # On ajoute le message de l'assistant (avec les tool_calls) à l'historique
            messages.append(message)
            
            for tool_call in message["tool_calls"]:
                tool_call_id = tool_call.get("id")
                function_call = tool_call.get("function", {})
                
                # Exécution du tool localement
                tool_result = execute_tool_call(function_call)
                
                # Ajout du résultat en tant que `role: tool`
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": function_call.get("name"),
                    "content": tool_result
                })
                
            # Deuxième appel à Groq pour générer la réponse finale avec le contexte intégré
            final_payload = {
                "model": settings.CHATBOT_MODEL,
                "messages": messages,
                "temperature": 0.5
            }
            
            final_response = requests.post(
                settings.CHATBOT_API_URL,
                json=final_payload,
                headers=headers,
                timeout=getattr(settings, "CHATBOT_TIMEOUT", 30)
            )
            
            if not final_response.ok:
                logger.warning(f"Échec Groq Final: {final_response.text}")
                final_response.raise_for_status()
                
            final_data = final_response.json()
            return final_data["choices"][0]["message"]["content"]
            
        else:
            # Réponse directe sans RAG
            return message.get("content", "")

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur requête Groq: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Détails Groq: {e.response.text}")
        return "Je suis désolé, je rencontre actuellement un problème technique avec l'assistant. Veuillez réessayer plus tard."
    except Exception as e:
        logger.error(f"Erreur inattendue Groq (RAG): {str(e)}")
        return "Une erreur inattendue s'est produite lors de la recherche des données. Veuillez contacter le support."

