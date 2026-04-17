from django.contrib import admin

from .models import ChatLog


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ('question_courte', 'modele', 'date')
    list_filter = ('modele', 'date')
    search_fields = ('question', 'reponse')

    def question_courte(self, obj):
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
    question_courte.short_description = 'Question'
