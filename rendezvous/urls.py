from django.urls import path

from . import views

app_name = 'rendezvous'

urlpatterns = [
    # Disponibilités
    path('disponibilites/', views.DisponibiliteListCreateView.as_view(), name='disponibilite-list-create'),
    path('disponibilites/<int:pk>/', views.DisponibiliteDetailView.as_view(), name='disponibilite-detail'),
    path('medecins/<int:medecin_pk>/disponibilites/', views.MedecinDisponibilitesView.as_view(), name='medecin-disponibilites'),
    path('medecins/<int:medecin_pk>/creneaux/', views.MedecinCreneauxView.as_view(), name='medecin-creneaux'),

    # Rendez-vous
    path('rendezvous/', views.RendezVousListCreateView.as_view(), name='rendezvous-list-create'),
    path('rendezvous/<int:pk>/', views.RendezVousDetailView.as_view(), name='rendezvous-detail'),
    path('rendezvous/<int:pk>/confirmer/', views.RendezVousConfirmerView.as_view(), name='rendezvous-confirmer'),
    path('rendezvous/<int:pk>/refuser/', views.RendezVousRefuserView.as_view(), name='rendezvous-refuser'),
    path('rendezvous/<int:pk>/annuler/', views.RendezVousAnnulerView.as_view(), name='rendezvous-annuler'),
    path('rendezvous/<int:pk>/terminer/', views.RendezVousTerminerView.as_view(), name='rendezvous-terminer'),
    path('rendezvous/<int:pk>/preenregistrement/', views.PreEnregistrementView.as_view(), name='rendezvous-preenregistrement'),

    # Consultations
    path('consultations/', views.ConsultationListView.as_view(), name='consultation-list'),
    path('consultations/<int:pk>/', views.ConsultationDetailView.as_view(), name='consultation-detail'),
    path('consultations/<int:pk>/cloturer/', views.ConsultationCloturerView.as_view(), name='consultation-cloturer'),
]
