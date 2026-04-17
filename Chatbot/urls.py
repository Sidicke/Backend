from django.urls import path
from .views import ChatHistoryView, SendMessageView

app_name = 'chatbot'

urlpatterns = [
    path('history/', ChatHistoryView.as_view(), name='chat-history'),
    path('message/', SendMessageView.as_view(), name='chat-message'),
]
