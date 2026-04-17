from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('expediteur', 'destinataire', 'consultation', 'date_envoi', 'lu')
    list_filter = ('lu', 'date_envoi')
    search_fields = ('expediteur__email', 'destinataire__email', 'contenu')
