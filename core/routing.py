from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Import WebSocket routing
from apps.comments.routing import websocket_urlpatterns as comments_websocket_urlpatterns

# Combine all WebSocket URL patterns
websocket_urlpatterns = [
    *comments_websocket_urlpatterns,
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})