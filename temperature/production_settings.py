import os
from .settings import *

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "yourdomain.com").split(",")
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
