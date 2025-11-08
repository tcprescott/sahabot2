# i18n Module

## Overview

This module provides internationalization (i18n) support for SahaBot2 using Python's built-in `gettext` framework. It allows all user-facing text to be centralized and easily translated to multiple languages.

**Current Status**: English only (default language). Infrastructure is ready for additional languages.

## Quick Start

```python
from application.i18n import translate as _

# Simple translation
message = _("Hello, world!")

# With format strings
greeting = _("Welcome, {name}!").format(name=user.name)
```

## Directory Structure

```
application/i18n/
├── __init__.py              # Public API exports
├── translations.py          # Core translation logic
├── mo_compiler.py          # .po to .mo compiler (pure Python)
├── compile_translations.py # Compilation script
├── example_usage.py        # Usage examples
├── README.md               # This file
└── locales/
    ├── messages.pot        # Template file for new languages
    └── en/
        └── LC_MESSAGES/
            ├── messages.po # English translations (editable)
            └── messages.mo # Compiled binary (auto-generated)
```

## Files

### Core Files

- **`__init__.py`**: Public API - exports `translate()` and `get_translator()`
- **`translations.py`**: Translation manager using Python's gettext module
- **`mo_compiler.py`**: Pure Python compiler for .po → .mo conversion (no external tools needed)
- **`compile_translations.py`**: Convenience script to compile all .po files

### Translation Files

- **`.pot` (Template)**: Master template containing all translatable strings
- **`.po` (Portable Object)**: Human-readable translation files (one per language)
- **`.mo` (Machine Object)**: Binary compiled files used at runtime (generated from .po)

## Usage

### Basic Translation

```python
from application.i18n import translate as _

# In UI components
ui.label(_("Dashboard"))
ui.button(_("Save"), on_click=save_handler)
```

### With Variables

```python
# Format after translation
message = _("Found {count} results").format(count=len(results))

# Multiple variables
greeting = _("Hello {name}, you have {count} messages").format(
    name=user.name,
    count=message_count
)
```

### In Notifications

```python
ui.notify(_("Changes saved successfully"), type='positive')
ui.notify(_("An error occurred"), type='negative')
```

See `example_usage.py` for more comprehensive examples.

## Workflow

### For Developers

When adding new user-facing text:

1. **Wrap text with `_()`**:
   ```python
   ui.label(_("New feature text"))
   ```

2. **Add to English .po file**:
   Edit `locales/en/LC_MESSAGES/messages.po`:
   ```po
   msgid "New feature text"
   msgstr "New feature text"
   ```

3. **Compile**:
   ```bash
   python application/i18n/compile_translations.py
   ```

4. **Test**: Verify in UI

### For Translators (Future)

To add a new language (e.g., Spanish):

1. Create directory: `mkdir -p locales/es/LC_MESSAGES`
2. Copy English .po: `cp locales/en/LC_MESSAGES/messages.po locales/es/LC_MESSAGES/messages.po`
3. Update header (set Language: es)
4. Translate msgstr values
5. Compile: `python compile_translations.py`

## API Reference

### `translate(message, language=None)`

Translate a message to the specified language.

**Parameters**:
- `message` (str): English message to translate
- `language` (str, optional): Target language code (default: 'en')

**Returns**: Translated string, or original if translation not found

**Alias**: `_` (standard gettext convention)

### `get_translator(language='en')`

Get a translator object for a specific language.

**Parameters**:
- `language` (str): Language code (default: 'en')

**Returns**: GNUTranslations object

**Note**: Translators are cached for performance.

## Translation Catalog

Common pre-translated strings include:

**Navigation**: Home, Admin, Settings, Profile, Logout  
**Actions**: Save, Cancel, Delete, Edit, Create, Submit, Close  
**Status**: Loading..., Error, Success, Warning, Information  
**Messages**: "No data available", "Operation completed successfully"

See `locales/en/LC_MESSAGES/messages.po` for complete list.

## Best Practices

### Do's ✅

- Use complete sentences, not codes
- Keep HTML out of translatable strings
- Use format strings for variables
- Translate at display time, not at import time
- Add comments for ambiguous strings

### Don'ts ❌

- Don't split sentences across multiple translations
- Don't translate technical terms or proper names
- Don't concatenate strings
- Don't translate in module-level constants

## Technical Details

### Why Pure Python Compiler?

Our `mo_compiler.py` is a pure Python implementation that doesn't require external tools like `msgfmt` or the Babel library. This makes the build simpler and more portable.

### How gettext Works

1. Source code contains `_("English text")`
2. At runtime, gettext looks up translations in compiled .mo files
3. If translation exists, returns translated text
4. If not found, returns original English text (graceful fallback)

### Performance

- Translations are loaded once at startup
- Translator objects are cached per language
- .mo files are binary format for fast lookups
- Minimal runtime overhead

## Testing

Run the i18n tests:

```bash
poetry run pytest tests/test_i18n.py -v
```

Tests verify:
- Translation loading
- Translation retrieval
- Fallback behavior
- Format string compatibility
- Caching behavior

## Future Enhancements

The infrastructure supports:

1. **Multiple languages**: Add more .po files
2. **User preferences**: Store language choice per user
3. **Language switcher**: UI dropdown to change language
4. **Plural forms**: Different text for singular/plural
5. **Context**: Same English text, different translations

## Troubleshooting

**Translations not appearing?**
- Check .mo file exists: `ls -la locales/en/LC_MESSAGES/messages.mo`
- Recompile: `python compile_translations.py`
- Verify string in .po file

**New strings showing in English?**
- This is expected! English is the fallback language

**Compilation errors?**
- Check .po file syntax
- Ensure quotes are balanced
- Check for unescaped special characters

## Documentation

For detailed usage guide and patterns, see:
- **[I18N_GUIDE.md](../../docs/core/I18N_GUIDE.md)** - Complete developer guide
- **[example_usage.py](./example_usage.py)** - Code examples

## Standards

This implementation follows:
- [Python gettext documentation](https://docs.python.org/3/library/gettext.html)
- [GNU gettext standard](https://www.gnu.org/software/gettext/)
- [PO file format specification](https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html)
