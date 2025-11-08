"""
Translation management for SahaBot2 using Python's gettext module.

This module provides the core translation infrastructure, including:
- Loading translation catalogs from .po/.mo files
- Fallback to English when translations are missing
- Simple API for translating strings throughout the application

The translation system is designed to be:
- Non-breaking: Missing translations fall back to the source string
- Extensible: Easy to add new languages by adding .po files
- Standard: Uses Python's built-in gettext for broad compatibility
"""

import gettext
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Path to locale files (relative to this file)
LOCALE_DIR = Path(__file__).parent / 'locales'

# Default language
DEFAULT_LANGUAGE = 'en'

# Cache for loaded translators
_translators: dict[str, gettext.GNUTranslations] = {}


def get_translator(language: str = DEFAULT_LANGUAGE) -> gettext.GNUTranslations:
    """
    Get a translator for the specified language.

    Args:
        language: Language code (e.g., 'en', 'es', 'fr')

    Returns:
        GNUTranslations object for the specified language

    Note:
        If the requested language is not available, falls back to English.
        If English is not available, returns a NullTranslations that passes
        through the original strings unchanged.
    """
    if language in _translators:
        return _translators[language]

    try:
        translator = gettext.translation(
            'messages',
            localedir=str(LOCALE_DIR),
            languages=[language],
            fallback=True
        )
        _translators[language] = translator
        logger.debug("Loaded translator for language: %s", language)
        return translator
    except Exception as e:
        logger.warning("Failed to load translator for %s: %s", language, e)
        # Return a NullTranslations that passes through strings unchanged
        return gettext.NullTranslations()


def translate(message: str, language: Optional[str] = None) -> str:
    """
    Translate a message to the specified language.

    This is the primary function used throughout the application for
    translating user-facing text.

    Args:
        message: The English message to translate
        language: Target language code (defaults to English)

    Returns:
        Translated message, or original message if translation not found

    Examples:
        >>> translate("Hello, world!")
        "Hello, world!"
        
        >>> translate("Welcome to {app_name}").format(app_name="SahaBot2")
        "Welcome to SahaBot2"
        
        >>> translate("You have {count} messages", language='es').format(count=5)
        "Tienes 5 mensajes"  # Once Spanish translations are added
    """
    if language is None:
        language = DEFAULT_LANGUAGE

    translator = get_translator(language)
    return translator.gettext(message)


# Common alias for translate function (standard gettext convention)
_ = translate
