"""
AsyncQualifier Plugin for SahaBot2.

This plugin provides async qualifier functionality including:
- Async qualifier creation and management
- Pool and permalink management
- Race submission and scoring
- Live race events with RaceTime.gg integration
- Discord command integration

This is a built-in plugin that ships with SahaBot2.

Usage:
    from plugins.builtin.async_qualifier import AsyncQualifierPlugin
    from plugins.builtin.async_qualifier.models import AsyncQualifier, AsyncQualifierRace
    from plugins.builtin.async_qualifier.services import AsyncQualifierService
    from plugins.builtin.async_qualifier.events import RaceSubmittedEvent
"""

from plugins.builtin.async_qualifier.plugin import AsyncQualifierPlugin

__all__ = ["AsyncQualifierPlugin"]
