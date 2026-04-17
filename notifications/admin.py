from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'message', 'lu', 'date_envoi')
    list_filter = ('type', 'lu', 'date_envoi')
    search_fields = ('user__email', 'message')
    ordering = ('-date_envoi',)
