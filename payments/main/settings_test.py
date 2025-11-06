"""
Settings de prueba - Usa SQLite en memoria para tests
"""
from .settings import *

# Usar SQLite en memoria para tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
