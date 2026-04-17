from django.contrib import admin

from .models import Hopital, Service, HopitalService, MedecinService, DemandeAjoutService


@admin.register(Hopital)
class HopitalAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'telephone', 'email', 'latitude', 'longitude', 'is_active', 'date_creation')
    list_filter = ('is_active', 'ville')
    search_fields = ('nom', 'ville', 'adresse')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'is_active', 'date_creation')
    list_filter = ('is_active',)
    search_fields = ('nom',)


@admin.register(HopitalService)
class HopitalServiceAdmin(admin.ModelAdmin):
    list_display = ('hopital', 'service', 'date_ajout')
    list_filter = ('hopital',)


@admin.register(MedecinService)
class MedecinServiceAdmin(admin.ModelAdmin):
    list_display = ('medecin', 'service', 'date_ajout')
    list_filter = ('service',)


@admin.register(DemandeAjoutService)
class DemandeAjoutServiceAdmin(admin.ModelAdmin):
    list_display = ('hopital', 'statut', 'date_demande', 'traite_par')
    list_filter = ('statut',)
    search_fields = ('hopital__nom', 'nom_nouveau_service')
