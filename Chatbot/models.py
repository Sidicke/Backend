from django.db import models
from accounts.models import Patient

class ChatLog(models.Model):
    """Log anonyme des échanges avec le chatbot (pour amélioration du modèle)."""
    question = models.TextField('question')
    reponse = models.TextField('réponse')
    date = models.DateTimeField('date', auto_now_add=True)
    modele = models.CharField('modèle utilisé', max_length=100, blank=True, default='')

    class Meta:
        verbose_name = 'Log chatbot'
        verbose_name_plural = 'Logs chatbot'
        ordering = ['-date']

    def __str__(self):
        return f"{self.question[:80]}... ({self.date.strftime('%d/%m/%Y')})"

class ChatSession(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="chat_sessions")
    date_creation = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20) # 'user', 'assistant', 'system'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
