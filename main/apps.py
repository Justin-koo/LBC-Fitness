from django.apps import AppConfig
import threading
import nfc
from django.core.cache import cache

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'