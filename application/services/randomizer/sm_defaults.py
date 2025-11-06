"""
Default settings and configuration for Super Metroid randomizers.

This module provides shared default settings for VARIA and DASH randomizers
used across Discord commands and RaceTime.gg handlers.
"""

# VARIA default presets
VARIA_DEFAULTS = {
    'standard': {
        'logic': 'casual',
        'itemProgression': 'normal',
        'morphPlacement': 'early',
        'progressionSpeed': 'medium',
        'energyQty': 'normal'
    },
    'casual': {
        'logic': 'casual',
        'itemProgression': 'normal',
        'morphPlacement': 'early',
        'progressionSpeed': 'medium',
        'energyQty': 'normal'
    },
    'master': {
        'logic': 'master',
        'itemProgression': 'fast',
        'morphPlacement': 'random',
        'progressionSpeed': 'fast',
        'energyQty': 'low'
    },
    'expert': {
        'logic': 'expert',
        'itemProgression': 'fast',
        'morphPlacement': 'random',
        'progressionSpeed': 'veryfast',
        'energyQty': 'verylow'
    }
}

# DASH default presets
DASH_DEFAULTS = {
    'standard': {
        'area_rando': False,
        'major_minor_split': True,
        'boss_rando': False,
        'item_progression': 'normal'
    },
    'area': {
        'area_rando': True,
        'major_minor_split': True,
        'boss_rando': False,
        'item_progression': 'normal'
    },
    'total': {
        'area_rando': True,
        'major_minor_split': True,
        'boss_rando': True,
        'item_progression': 'fast'
    }
}


def get_varia_settings(preset_name: str = 'standard') -> dict:
    """
    Get VARIA settings for a preset.

    Args:
        preset_name: Name of the preset

    Returns:
        Dictionary of VARIA settings
    """
    return VARIA_DEFAULTS.get(preset_name, VARIA_DEFAULTS['standard']).copy()


def get_dash_settings(preset_name: str = 'standard') -> dict:
    """
    Get DASH settings for a preset.

    Args:
        preset_name: Name of the preset

    Returns:
        Dictionary of DASH settings
    """
    return DASH_DEFAULTS.get(preset_name, DASH_DEFAULTS['standard']).copy()
