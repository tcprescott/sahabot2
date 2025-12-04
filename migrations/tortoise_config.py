"""
Tortoise ORM configuration for Aerich migrations.

This configuration dynamically discovers all model modules from the models/ directory,
so you don't need to manually update the list every time you add a new model.
"""

from pathlib import Path
from config import settings


def get_model_modules():
    """
    Automatically discover all model modules in the models/ directory and
    tournament modules under modules/tournament/models and async qualifier
    modules under modules/async_qualifier/models.

    Returns:
        Sorted list of model module paths (e.g., ['models.user', 'modules.tournament.models.match_schedule', ...])
    """

    project_root = Path(__file__).parent.parent
    model_locations = [
        (project_root / "models", "models"),
        (project_root / "modules" / "tournament" / "models", "modules.tournament.models"),
        (project_root / "modules" / "async_qualifier" / "models", "modules.async_qualifier.models"),
    ]

    model_modules: list[str] = []

    for directory, module_prefix in model_locations:
        if not directory.exists():
            continue

        for file in directory.glob("*.py"):
            # Skip __init__.py and any private files
            if file.stem.startswith("_"):
                continue

            model_modules.append(f"{module_prefix}.{file.stem}")

    model_modules = sorted(set(model_modules))

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
