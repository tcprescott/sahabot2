"""
Built-in plugins for SahaBot2.

This package contains core plugins that ship with the application.
Built-in plugins cannot be uninstalled but can be disabled per-organization.

Plugins in this package:
- tournament: Live tournament management
- async_qualifier: Asynchronous qualifier races
- presets: Preset namespace and management
- alttpr: A Link to the Past Randomizer
- sm: Super Metroid Randomizer (VARIA/DASH)
- smz3: SMZ3 Combo Randomizer
- ootr: Ocarina of Time Randomizer
- aosr: Aria of Sorrow Randomizer
- z1r: Zelda 1 Randomizer
- ffr: Final Fantasy Randomizer
- smb3r: Super Mario Bros 3 Randomizer
- ctjets: Chrono Trigger Jets of Time
- bingosync: Bingosync room management
- avianart: Avianart Door Randomizer
"""

from plugins.builtin.tournament import TournamentPlugin
from plugins.builtin.async_qualifier import AsyncQualifierPlugin
from plugins.builtin.presets import PresetsPlugin
from plugins.builtin.alttpr import ALTTPRPlugin
from plugins.builtin.sm import SMPlugin
from plugins.builtin.smz3 import SMZ3Plugin
from plugins.builtin.ootr import OOTRPlugin
from plugins.builtin.aosr import AOSRPlugin
from plugins.builtin.z1r import Z1RPlugin
from plugins.builtin.ffr import FFRPlugin
from plugins.builtin.smb3r import SMB3RPlugin
from plugins.builtin.ctjets import CTJetsPlugin
from plugins.builtin.bingosync import BingosyncPlugin
from plugins.builtin.avianart import AvianartPlugin

# List of built-in plugin classes
# Order matters: presets must be loaded before randomizer plugins
BUILTIN_PLUGINS = [
    # Core plugins
    TournamentPlugin,
    AsyncQualifierPlugin,
    PresetsPlugin,
    # Randomizer plugins (high priority)
    ALTTPRPlugin,
    SMPlugin,
    SMZ3Plugin,
    # Randomizer plugins (medium priority)
    OOTRPlugin,
    # Randomizer plugins (lower priority)
    AOSRPlugin,
    Z1RPlugin,
    FFRPlugin,
    SMB3RPlugin,
    CTJetsPlugin,
    # Special plugins
    BingosyncPlugin,
    AvianartPlugin,
]

__all__ = [
    "BUILTIN_PLUGINS",
    "TournamentPlugin",
    "AsyncQualifierPlugin",
    "PresetsPlugin",
    "ALTTPRPlugin",
    "SMPlugin",
    "SMZ3Plugin",
    "OOTRPlugin",
    "AOSRPlugin",
    "Z1RPlugin",
    "FFRPlugin",
    "SMB3RPlugin",
    "CTJetsPlugin",
    "BingosyncPlugin",
    "AvianartPlugin",
]
