"""
i18n (Internationalization) support for SahaBot2.

This module provides centralized translation management using Python's
built-in gettext module. All user-facing text should be wrapped with
translation functions to enable future localization.

Usage:
    from application.i18n import translate as _
    
    # Simple translation
    message = _("Hello, world!")
    
    # Translation with variables (use format strings)
    greeting = _("Hello, {name}!").format(name=user.name)
"""

from application.i18n.translations import translate, get_translator

__all__ = ['translate', 'get_translator']
