"""
Tests for the i18n (internationalization) system.

These tests verify that:
- Translation loading works correctly
- Translation retrieval returns expected values
- Fallback behavior works when translations are missing
- The system gracefully handles missing locale files
"""

import pytest
from application.i18n import translate, get_translator


class TestTranslationSystem:
    """Test the translation system infrastructure."""

    def test_translate_returns_string(self):
        """Test that translate returns a string."""
        result = translate("Test message")
        assert isinstance(result, str)

    def test_translate_with_english(self):
        """Test translating to English (default language)."""
        result = translate("Welcome to SahaBot2", language='en')
        assert result == "Welcome to SahaBot2"

    def test_translate_common_ui_elements(self):
        """Test translating common UI elements."""
        # These are in our English .po file
        assert translate("Home") == "Home"
        assert translate("Admin") == "Admin"
        assert translate("Save") == "Save"
        assert translate("Cancel") == "Cancel"
        assert translate("Delete") == "Delete"

    def test_translate_header_elements(self):
        """Test translating header/navigation elements."""
        assert translate("SahasrahBot") == "SahasrahBot"
        assert translate("Open navigation menu") == "Open navigation menu"
        assert translate("Go to home page") == "Go to home page"

    def test_translate_user_menu(self):
        """Test translating user menu elements."""
        assert translate("User Menu") == "User Menu"
        assert translate("View Profile") == "View Profile"
        assert translate("Sign Out") == "Sign Out"

    def test_translate_missing_key_returns_original(self):
        """Test that missing translations return the original string."""
        # This key doesn't exist in our translation file
        original = "This is a completely new untranslated string xyz123"
        result = translate(original)
        assert result == original

    def test_translate_with_format_strings(self):
        """Test that translations work with Python format strings."""
        template = translate("Welcome to SahaBot2")
        # Can use format after translation
        assert "SahaBot2" in template

    def test_get_translator_returns_translator(self):
        """Test that get_translator returns a valid translator object."""
        translator = get_translator('en')
        assert translator is not None
        # Should have a gettext method
        assert hasattr(translator, 'gettext')

    def test_get_translator_caches_translators(self):
        """Test that translators are cached."""
        translator1 = get_translator('en')
        translator2 = get_translator('en')
        # Should return the same object (cached)
        assert translator1 is translator2

    def test_translate_with_invalid_language_fallback(self):
        """Test that invalid languages fall back gracefully."""
        # Using a language that doesn't exist should not crash
        result = translate("Home", language='zz')
        # Should return the original string
        assert result == "Home"

    def test_translate_empty_string(self):
        """Test translating an empty string."""
        result = translate("")
        assert result == ""

    def test_translate_multiline_string(self):
        """Test translating strings with newlines."""
        multiline = "Line 1\nLine 2\nLine 3"
        result = translate(multiline)
        # Should preserve newlines
        assert "\n" in result
        assert result == multiline


class TestTranslationUsage:
    """Test practical usage patterns of the translation system."""

    def test_format_string_with_variables(self):
        """Test using format strings with translated text."""
        # Common pattern: translate then format
        welcome = translate("Welcome to SahaBot2")
        # Can use in string operations
        assert "SahaBot2" in welcome

        # Simulate formatting a translated string
        message_template = "Hello, {name}!"
        translated = translate(message_template)
        formatted = translated.format(name="Alice")
        assert formatted == "Hello, Alice!"

    def test_translation_in_conditionals(self):
        """Test using translations in conditional logic."""
        error_msg = translate("Error")
        success_msg = translate("Success")

        # Should be usable in conditions
        assert error_msg != success_msg
        assert len(error_msg) > 0

    def test_translation_with_special_characters(self):
        """Test that special characters are preserved."""
        # Test with punctuation
        question = "What is your name?"
        result = translate(question)
        assert "?" in result

    def test_multiple_translations_in_sequence(self):
        """Test translating multiple strings in sequence."""
        translations = [
            translate("Home"),
            translate("Admin"),
            translate("Settings"),
            translate("Profile")
        ]
        # All should succeed
        assert all(t for t in translations)
        assert len(translations) == 4


class TestTranslationImport:
    """Test that translations can be imported as expected."""

    def test_translate_function_importable(self):
        """Test that translate function can be imported."""
        from application.i18n import translate
        assert callable(translate)

    def test_get_translator_importable(self):
        """Test that get_translator can be imported."""
        from application.i18n import get_translator
        assert callable(get_translator)

    def test_can_import_with_underscore_alias(self):
        """Test that the standard _ alias works."""
        from application.i18n import translate as _
        result = _("Home")
        assert result == "Home"
