from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentification JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Applications
    path('api/accounts/', include('accounts.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/', include('hopitaux.urls')),
    path('api/', include('rendezvous.urls')),
    path('api/', include('resultats.urls')),
    path('api/', include('messagerie.urls')),
    path('api/chatbot/', include('Chatbot.urls')),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
