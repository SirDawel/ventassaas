import os
from dotenv import load_dotenv
from pathlib import Path

# Obtener el directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno con codificación UTF-8
load_dotenv(os.path.join(BASE_DIR, '.env'), encoding='utf-8')

DATABASES = {
    'default': {
        'ENGINE': os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASS"),
        'HOST': os.getenv("DB_HOST", "localhost"),
        'PORT': os.getenv("DB_PORT", "5432"),
    }
}