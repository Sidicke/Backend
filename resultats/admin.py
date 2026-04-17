from django.contrib import admin

from .models import Resultat


@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = ('titre', 'patient', 'laborantin', 'date_analyse', 'date_depot', 'code_acces')
    list_filter = ('date_analyse', 'date_depot')
    search_fields = ('titre', 'patient__user__last_name', 'patient__user__first_name', 'code_acces')
    filter_horizontal = ('partages',)
