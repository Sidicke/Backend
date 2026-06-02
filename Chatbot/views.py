import re
import json
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from accounts.models import Patient
from .models import ChatSession, ChatMessage
from .serializers import ChatMessageSerializer, SendMessageSerializer
from .services import openai_chat_completion
from .whatsapp_utils import format_whatsapp_phone, send_whatsapp_message as _send_wa


class WhatsAppDebugView(APIView):
    """
    Endpoint de diagnostic : trace le numéro formaté et appelle réellement le service.
    POST /api/chatbot/whatsapp-debug/  { "phone": "0197XXXXXX", "message": "Test" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        raw_phone = request.data.get('phone', '')
        message = request.data.get('message', 'Test HOPITEL debug')

        formatted = format_whatsapp_phone(raw_phone)
        wa_url = getattr(settings, 'WHATSAPP_SERVICE_URL', 'http://localhost:3001')

        result = _send_wa(raw_phone, message)

        return Response({
            'phone_brut': raw_phone,
            'phone_formate': formatted,
            'whatsapp_service_url': wa_url,
            'reponse_service': result,
        })

def extract_actions_and_clean_message(content):
    """
    Extrait le tableau d'actions JSON si présent et nettoie le message pour l'utilisateur.
    """
    actions = []
    pattern = r'```json\s*(\[.*?\])\s*```'
    
    # On cherche le bloc markdown JSON
    match = re.search(pattern, content, re.DOTALL)
    if match:
        try:
            actions = json.loads(match.group(1))
            # On retire le JSON de la réponse front
            content = content[:match.start()].strip()
        except json.JSONDecodeError:
            pass
            
    return content, actions

class ChatHistoryView(APIView):
    """Récupère l'historique complet des messages pour le patient connecté."""
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response([], status=status.HTTP_200_OK)
            
        try:
            patient = Patient.objects.get(user=request.user)
            session, _ = ChatSession.objects.get_or_create(patient=patient)
            messages = session.messages.all().order_by('timestamp')
            serializer = ChatMessageSerializer(messages, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Patient.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)


class SendMessageView(APIView):
    """Envoie un message à l'IA et retourne la réponse."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data['message']

        if not request.user.is_authenticated:
            history_for_api = [{"role": "user", "content": user_message}]
            ai_response = openai_chat_completion(history_for_api)
            
            clean_content, actions = extract_actions_and_clean_message(ai_response)
            
            return Response({
                "message": {
                    "id": 0,
                    "role": "assistant",
                    "content": clean_content,
                    "timestamp": None
                },
                "actions": actions
            }, status=status.HTTP_200_OK)

        try:
            patient = Patient.objects.get(user=request.user)
            session, _ = ChatSession.objects.get_or_create(patient=patient)

            # 1. Sauvegarder le message utilisateur
            ChatMessage.objects.create(
                session=session,
                role="user",
                content=user_message
            )

            # 2. Préparer l'historique
            past_messages = session.messages.all().order_by('-timestamp')[:20]
            history_for_api = [{"role": msg.role, "content": msg.content} for msg in reversed(past_messages)]

            # 3. Appeler l'API Groq (RAG enabled)
            ai_response = openai_chat_completion(history_for_api)
            
            # 4. Extraire les actions JSON et nettoyer le texte final
            clean_content, actions = extract_actions_and_clean_message(ai_response)

            # 5. Sauvegarder la réponse de l'IA (le texte propre)
            ai_msg_obj = ChatMessage.objects.create(
                session=session,
                role="assistant",
                content=clean_content
            )

            return Response({
                "message": ChatMessageSerializer(ai_msg_obj).data,
                "actions": actions
            }, status=status.HTTP_200_OK)
            
        except Patient.DoesNotExist:
            return Response({"error": "Profil patient introuvable."}, status=status.HTTP_403_FORBIDDEN)
