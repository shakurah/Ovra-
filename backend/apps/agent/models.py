# This file initializes the agent module.

# Ensure test_models (test-only models) are registered during test discovery
try:
    # import side-effect registers models in apps.agent
    from .models.test_models import *  # noqa: F401,F403
except Exception:
    # non-fatal: if the submodule isn't present or import fails, continue
    pass