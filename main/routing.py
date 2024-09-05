from django.urls import path
from .consumers import NFCConsumer

websocket_urlpatterns = [
    path('ws/nfc/', NFCConsumer.as_asgi()),
]
