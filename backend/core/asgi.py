"""
ASGI Configuration برای app Platform
پشتیبانی از HTTP و WebSocket
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import WebSocket routing after Django setup
from chat import routing as chat_routing

application = ProtocolTypeRouter({
    # HTTP handler
    "http": django_asgi_app,
    
    # WebSocket handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                # WebSocket routes for chat
                *chat_routing.websocket_urlpatterns,
            ])
        )
    ),
})
