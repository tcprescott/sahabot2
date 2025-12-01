"""
Models for the Presets plugin.

This module re-exports preset-related models from the core application
for backwards compatibility and provides a unified import interface.
"""

# Re-export from core models for backwards compatibility
from models.preset_namespace import PresetNamespace
from models.randomizer_preset import RandomizerPreset

__all__ = [
    "PresetNamespace",
    "RandomizerPreset",
]
