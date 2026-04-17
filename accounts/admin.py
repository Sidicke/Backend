from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Patient, Medecin, Laborantin


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administration du modèle User personnalisé."""

    list_display = ('email', 'first_name', 'last_name', 'role', 'hopital', 'is_active', 'is_email_verified')
    list_filter = ('role', 'is_active', 'is_email_verified', 'sexe')
    search_fields = ('email', 'first_name', 'last_name', 'telephone')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'telephone', 'date_naissance', 'sexe', 'adresse', 'photo'),
        }),
        ('Rôle et rattachement', {
            'fields': ('role', 'hopital'),
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_email_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2',
                'first_name', 'last_name', 'telephone',
                'date_naissance', 'sexe', 'role', 'hopital',
            ),
        }),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact_urgence_nom', 'contact_urgence_tel', 'groupe_sanguin')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


@admin.register(Medecin)
class MedecinAdmin(admin.ModelAdmin):
    list_display = ('user', 'numero_ordre', 'statut')
    list_filter = ('statut',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'numero_ordre')


@admin.register(Laborantin)
class LaborantinAdmin(admin.ModelAdmin):
    list_display = ('user', 'laboratoire')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
