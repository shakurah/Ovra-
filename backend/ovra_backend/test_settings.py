# Minimal test settings that import base settings and force SQLite DB for tests.
import os
from .settings import *  # noqa: F401,F403

# Force test DB to sqlite to avoid psycopg dependency during tests
BASE_DIR = globals().get("BASE_DIR", os.path.dirname(os.path.dirname(__file__)))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "test_db.sqlite3"),
    }
}

# Defensive deduplication / conflict resolution for INSTALLED_APPS.
# Prefer packages under "apps." if both "apps.boe" and "boe" (or similar duplicates) appear.
_seen = set()
_dedup = []
for app in INSTALLED_APPS:
    # drop plain 'boe' if 'apps.boe' is present later — handle common duplicate pattern
    if app == "boe" and "apps.boe" in INSTALLED_APPS:
        continue
    if app not in _seen:
        _seen.add(app)
        _dedup.append(app)
INSTALLED_APPS = _dedup

# Optional: disable external services during tests by overriding settings here
# e.g. disable Celery tasks, external API clients, etc.
CELERY_TASK_ALWAYS_EAGER = True

# Disable migrations for test-only run for the 'agent' app so sqlite test DB is created automatically.
# Use app label 'agent' (matches app_label in apps/agent/models/test_models.py Meta).
MIGRATION_MODULES = getattr(globals(), "MIGRATION_MODULES", {})
MIGRATION_MODULES.update({
    "agent": None,
})