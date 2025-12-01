"""
Repositories for the Presets plugin.

This module re-exports preset-related repositories from the core application
for backwards compatibility and provides a unified import interface.
"""

# Re-export from core repositories for backwards compatibility
from application.repositories.preset_namespace_repository import (
    PresetNamespaceRepository,
)
from application.repositories.randomizer_preset_repository import (
    RandomizerPresetRepository,
)

__all__ = [
    "PresetNamespaceRepository",
    "RandomizerPresetRepository",
]
