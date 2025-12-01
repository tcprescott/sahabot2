"""
Chrono Trigger Jets of Time (CTJets) Randomizer service.

DEPRECATED: This module is a backward-compatibility re-export.
Import from plugins.builtin.ctjets.services instead.

This service handles generation of Chrono Trigger randomizer seeds via ctjot.com.
"""

# Re-export from plugin for backward compatibility
from plugins.builtin.ctjets.services.ctjets_service import CTJetsService

__all__ = ["CTJetsService"]
