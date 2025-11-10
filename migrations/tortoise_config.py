"""
Tortoise ORM configuration for Aerich migrations.

This configuration dynamically discovers all model modules from the models/ directory,
so you don't need to manually update the list every time you add a new model.
"""

from pathlib import Path
from config import settings


def get_model_modules():
    """
    Automatically discover all model modules in the models/ directory.

    Returns:
        List of model module paths (e.g., ['models.user', 'models.organizations', ...])
    """
    models_dir = Path(__file__).parent.parent / "models"
    model_modules = []

    for file in models_dir.glob("*.py"):
        # Skip __init__.py and any private files
        if file.stem.startswith("_"):
            continue

        # Add the module path
        model_modules.append(f"models.{file.stem}")

    # Sort for consistency
    model_modules.sort()

    # Always add aerich.models at the end
    model_modules.append("aerich.models")

    return model_modules


TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": get_model_modules(),
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}
