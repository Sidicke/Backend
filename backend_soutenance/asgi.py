"""
ASGI config for backend_soutenance project.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_soutenance.settings')

django_asgi_app = get_asgi_application()

from messagerie.routing import websocket_urlpatterns as chat_urlpatterns
from notifications.routing import websocket_urlpatterns as notification_urlpatterns
from messagerie.middleware import JWTAuthMiddleware

websocket_urlpatterns = chat_urlpatterns + notification_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
