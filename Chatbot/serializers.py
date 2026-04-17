from rest_framework import serializers
from .models import ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'timestamp']

class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(required=True, error_messages={
        'required': "Le message ne peut pas être vide.",
        'blank': "Le message ne peut pas être vide."
    })
