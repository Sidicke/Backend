from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    # Inscription et vérification email
    path('register/', views.PatientRegisterView.as_view(), name='register'),
    path('register/resend-code/', views.ResendCodeView.as_view(), name='resend-code'),
    path('activate-code/', views.ActivateByCodeView.as_view(), name='activate-code'),
    path('verify-code/', views.ActivateByCodeView.as_view(), name='verify-code'),
    path('resend-code/', views.ResendCodeView.as_view(), name='resend-code-alt'),
    path('request-password-reset/', views.RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('reset-password-confirm/', views.ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    path('reset-password/<str:token>/', views.PasswordResetHTMLView.as_view(), name='password-reset-html'),

    # Profil utilisateur connecté
    path('users/me/', views.UserMeView.as_view(), name='user-me'),

    # Gestion des médecins
    path('medecins/', views.MedecinListCreateView.as_view(), name='medecin-list-create'),
    path('medecins/import/', views.MedecinCSVImportView.as_view(), name='medecin-csv-import'),
    path('medecins/import-template/', views.MedecinCSVTemplateView.as_view(), name='medecin-csv-template'),
    path('medecins/<int:pk>/', views.MedecinDetailView.as_view(), name='medecin-detail'),
    path('medecins/<int:pk>/desactiver/', views.MedecinDesactiverView.as_view(), name='medecin-desactiver'),

    # Gestion des laborantins
    path('laborantins/', views.LaborantinListCreateView.as_view(), name='laborantin-list-create'),
    path('laborantins/<int:pk>/', views.LaborantinDetailView.as_view(), name='laborantin-detail'),

    # Gestion des patients (admin général)
    path('patients/', views.PatientListView.as_view(), name='patient-list'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient-detail'),

    # Gestion des admins hôpitaux (admin général)
    path('admin-hopitaux/', views.AdminHopitalListCreateView.as_view(), name='admin-hopital-list-create'),
    path('admin-hopitaux/<int:pk>/', views.AdminHopitalDetailView.as_view(), name='admin-hopital-detail'),
]
