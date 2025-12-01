"""
Services for the Presets plugin.

This module re-exports preset-related services from the core application
for backwards compatibility and provides a unified import interface.
"""

# Re-export from core services for backwards compatibility
from application.services.randomizer.preset_namespace_service import (
    PresetNamespaceService,
    NamespaceValidationError,
)
from application.services.randomizer.randomizer_preset_service import (
    RandomizerPresetService,
    PresetValidationError,
)

__all__ = [
    "PresetNamespaceService",
    "NamespaceValidationError",
    "RandomizerPresetService",
    "PresetValidationError",
]
