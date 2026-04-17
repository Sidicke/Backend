from django.urls import path

from . import views

app_name = 'resultats'

urlpatterns = [
    # ── BioTrack : Demandes d'analyse ─────────────────────────────────────────
    path('analyses/', views.DemandeAnalyseListCreateView.as_view(), name='analyse-list-create'),
    path('analyses/<int:pk>/cloturer/', views.DemandeAnalyseCloturerView.as_view(), name='analyse-cloturer'),
    path('laborantins/patients/', views.LaborantinPatientListView.as_view(), name='laborantin-patient-list'),

    # ── Résultats ─────────────────────────────────────────────────────────────
    path('resultats/', views.ResultatListCreateView.as_view(), name='resultat-list-create'),
    path('resultats/<int:pk>/', views.ResultatDetailView.as_view(), name='resultat-detail'),
    path('resultats/<int:pk>/telecharger/', views.ResultatTelechargerView.as_view(), name='resultat-telecharger'),
    path('resultats/<int:pk>/partager/', views.ResultatPartagerView.as_view(), name='resultat-partager'),
    path('resultats/<int:pk>/partager/<int:medecin_pk>/', views.ResultatRetirerPartageView.as_view(), name='resultat-retirer-partage'),
    path('resultats/acces/<str:code>/', views.ResultatAccesCodeView.as_view(), name='resultat-acces-code'),
]
