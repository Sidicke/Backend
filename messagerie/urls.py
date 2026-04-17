from django.urls import path

from . import views

app_name = 'messagerie'

urlpatterns = [
    path('conversations/', views.ConversationListView.as_view(), name='conversation-list'),
    path('messages/', views.MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<int:pk>/mark-read/', views.MessageMarkReadView.as_view(), name='message-mark-read'),
]
