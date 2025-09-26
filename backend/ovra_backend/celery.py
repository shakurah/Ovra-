# ovra_backend/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ovra_backend.settings")

app = Celery("ovra_backend")

# Load config from Django settings, using CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks.py in each Django app
app.autodiscover_tasks()
