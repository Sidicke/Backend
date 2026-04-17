from django.urls import path

from . import views

app_name = 'hopitaux'

urlpatterns = [
    # Hôpitaux
    path('hopitaux/mes-services/', views.HopitalMesServicesView.as_view(), name='hopital-mes-services'),
    path('hopitaux/mes-services/<int:pk>/', views.HopitalServiceUpdateView.as_view(), name='hopital-service-update'),
    path('hopitaux/statistiques/', views.HopitalStatistiquesView.as_view(), name='hopital-statistiques'),
    path('hopitaux/patients/', views.HopitalPatientsView.as_view(), name='hopital-patients'),
    path('hopitaux/nearby/', views.NearbyHospitalView.as_view(), name='hopital-nearby'),
    path('hopitaux/', views.HopitalListCreateView.as_view(), name='hopital-list-create'),
    path('hopitaux/<int:pk>/', views.HopitalDetailView.as_view(), name='hopital-detail'),

    # Services globaux
    path('services/', views.ServiceListCreateView.as_view(), name='service-list-create'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service-detail'),

    # Services d'un hôpital
    path('hopitaux/<int:hopital_pk>/services/', views.HopitalServiceListView.as_view(), name='hopital-services'),

    # Demandes d'ajout de service
    path('hopitaux/<int:hopital_pk>/demandes/', views.DemandeCreateView.as_view(), name='demande-create'),
    path('demandes/', views.DemandeListView.as_view(), name='demande-list'),
    path('demandes/<int:pk>/valider/', views.DemandeValiderView.as_view(), name='demande-valider'),
    path('demandes/<int:pk>/refuser/', views.DemandeRefuserView.as_view(), name='demande-refuser'),

    # Services d'un médecin
    path('medecins/<int:medecin_pk>/services/', views.MedecinServiceListCreateView.as_view(), name='medecin-services'),
    path('medecins/<int:medecin_pk>/services/<int:service_pk>/', views.MedecinServiceDeleteView.as_view(), name='medecin-service-delete'),
]
