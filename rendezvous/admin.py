from django.contrib import admin
from .models import Disponibilite, RendezVous, Consultation, PreEnregistrement

@admin.register(Disponibilite)
class DisponibiliteAdmin(admin.ModelAdmin):
    list_display = ('medecin', 'type', 'jour_semaine', 'date_specifique', 'heure_debut', 'heure_fin', 'is_active')
    list_filter = ('type', 'is_active', 'jour_semaine')
    search_fields = ('medecin__user__first_name', 'medecin__user__last_name')

@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'medecin', 'date_heure', 'duree', 'statut')
    list_filter = ('statut',)
    search_fields = ('patient__user__last_name', 'medecin__user__last_name')

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('rendez_vous', 'date_consultation', 'est_cloture')
    list_filter = ('est_cloture', 'date_consultation')
    search_fields = ('rendez_vous__patient__user__last_name', 'rendez_vous__medecin__user__last_name')

@admin.register(PreEnregistrement)
class PreEnregistrementAdmin(admin.ModelAdmin):
    list_display = ('rendez_vous', 'soumis_le', 'mis_a_jour_le')
    search_fields = ('rendez_vous__patient__user__last_name', 'symptomes_principaux')
