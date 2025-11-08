# i18n (Internationalization) Guide

## Overview

SahaBot2 uses a centralized translation system based on Python's built-in `gettext` module. This allows all user-facing text to be easily translated to multiple languages while maintaining clean, readable code.

**Current Status**: English only (default language). Infrastructure is ready for additional languages.

## Quick Start

### Basic Usage

```python
from application.i18n import translate as _

# Simple translation
message = _("Hello, world!")

# Translation with variables
greeting = _("Welcome, {name}!").format(name=user.discord_username)

# In UI components
ui.label(_("User Settings"))
ui.button(_("Save"), on_click=save_handler)
```

### Common Patterns

#### UI Elements

```python
from nicegui import ui
from application.i18n import translate as _

# Labels
ui.label(_("Dashboard"))

# Buttons
ui.button(_("Submit"), on_click=submit_handler)
ui.button(_("Cancel"), on_click=close_dialog)

# Notifications
ui.notify(_("Changes saved successfully"), type='positive')
ui.notify(_("An error occurred"), type='negative')

# Placeholders
ui.input(label=_("Username"), placeholder=_("Enter your username"))
```

#### Dialog Titles and Messages

```python
from application.i18n import translate as _

# Dialog
self.create_dialog(
    title=_("Edit User"),
    icon='edit',
)

# Section titles
self.create_section_title(_("User Information"))
self.create_section_title(_("Account Status"))

# Info rows
self.create_info_row(_("Discord ID"), str(user.discord_id))
self.create_info_row(_("Username"), user.discord_username)
```

#### Error Messages and Notifications

```python
from application.i18n import translate as _

# Error messages
if not user:
    ui.notify(_("User not found"), type='negative')
    return

# Success messages
ui.notify(_("Profile updated successfully"), type='positive')

# Validation messages
if not name:
    return _("Name is required")
```

#### Format Strings

When you need to include variables in translated strings:

```python
from application.i18n import translate as _

# Format after translation
message = _("Found {count} results").format(count=len(results))

# Multiple variables
greeting = _("Hello {name}, you have {count} messages").format(
    name=user.name,
    count=message_count
)

# For plurals (future enhancement)
# Note: Current system doesn't support plural forms yet
items = len(items_list)
message = _("You have {count} item(s)").format(count=items)
```

## Translation System Architecture

### Directory Structure

```
application/i18n/
├── __init__.py              # Public API
├── translations.py          # Core translation logic
├── mo_compiler.py          # .po to .mo compiler
├── compile_translations.py # Compilation script
└── locales/
    ├── messages.pot        # Template file
    └── en/
        └── LC_MESSAGES/
            ├── messages.po # English translations
            └── messages.mo # Compiled binary (generated)
```

### How It Works

1. **Source Code**: Developers wrap user-facing strings with `_()` function
2. **Translation Files**: Strings are defined in `.po` files for each language
3. **Compilation**: `.po` files are compiled to `.mo` binary files
4. **Runtime**: `gettext` loads `.mo` files and provides translations

### Translation Files

#### `.pot` (Template)
- Master template file
- Contains all translatable strings
- Used as basis for creating language-specific `.po` files

#### `.po` (Portable Object)
- Human-readable translation file
- One file per language
- Contains `msgid` (source) and `msgstr` (translation) pairs

#### `.mo` (Machine Object)
- Binary compiled version of `.po` file
- Used by gettext at runtime
- Generated automatically from `.po` files

## Adding Translations

### For Developers

When adding new user-facing text to the code:

1. **Wrap the text with `_()`**:
   ```python
   from application.i18n import translate as _
   
   ui.label(_("New feature text"))
   ```

2. **Add to English `.po` file**:
   Open `application/i18n/locales/en/LC_MESSAGES/messages.po`:
   ```po
   msgid "New feature text"
   msgstr "New feature text"
   ```

3. **Compile translations**:
   ```bash
   python application/i18n/compile_translations.py
   ```

4. **Test**: Verify the text appears correctly in the UI

### For Translators (Future)

When adding a new language (e.g., Spanish):

1. **Create language directory**:
   ```bash
   mkdir -p application/i18n/locales/es/LC_MESSAGES
   ```

2. **Copy English `.po` file**:
   ```bash
   cp application/i18n/locales/en/LC_MESSAGES/messages.po \
      application/i18n/locales/es/LC_MESSAGES/messages.po
   ```

3. **Update header** in the new file:
   ```po
   "Language: es\n"
   "Language-Team: Spanish\n"
   ```

4. **Translate `msgstr` entries**:
   ```po
   msgid "Welcome to SahaBot2"
   msgstr "Bienvenido a SahaBot2"
   
   msgid "Home"
   msgstr "Inicio"
   ```

5. **Compile**:
   ```bash
   python application/i18n/compile_translations.py
   ```

## Best Practices

### Do's ✅

- **Use descriptive strings**: Use complete sentences, not abbreviated codes
  ```python
  _("Welcome to SahaBot2")  # ✅ Good
  _("welcome_msg")          # ❌ Bad - not descriptive
  ```

- **Keep strings simple**: Avoid complex formatting in the translatable string
  ```python
  # ✅ Good
  _("You have {count} messages").format(count=n)
  
  # ❌ Bad - HTML in translatable string
  _("<strong>You have {count} messages</strong>")
  ```

- **Use format strings for variables**: Never concatenate strings
  ```python
  # ✅ Good
  _("Hello, {name}!").format(name=user.name)
  
  # ❌ Bad
  _("Hello, ") + user.name + _("!")
  ```

- **Provide context in comments**: Add comments for ambiguous strings
  ```python
  # Button text for saving user profile
  ui.button(_("Save"), on_click=save_profile)
  
  # Button text for saving tournament settings
  ui.button(_("Save"), on_click=save_tournament)
  ```

### Don'ts ❌

- **Don't split sentences**:
  ```python
  # ❌ Bad - loses context for translators
  ui.label(_("You have ") + str(count) + _(" messages"))
  
  # ✅ Good
  ui.label(_("You have {count} messages").format(count=count))
  ```

- **Don't translate technical terms**: Keep API names, code terms untranslated
  ```python
  # ✅ Good - "RaceTime" is a proper name
  _("Connected to RaceTime.gg")
  
  # ❌ Bad - translating proper names
  _("Connected to {service}").format(service=_("RaceTime.gg"))
  ```

- **Don't translate in constants**: Translate at usage time
  ```python
  # ❌ Bad - translates at import time
  WELCOME_MESSAGE = _("Welcome!")
  
  # ✅ Good - translates when displayed
  def show_welcome():
      ui.label(_("Welcome!"))
  ```

## Language Switching (Future Enhancement)

The infrastructure is ready for multi-language support. To enable language switching:

1. **User preference**: Add language preference to User model
2. **Session storage**: Store user's language choice in session
3. **Pass language parameter**: Update `translate()` calls to use user's language
4. **UI selector**: Add language dropdown in settings

Example (future):
```python
# Get user's preferred language from session/database
user_language = user.language_preference or 'en'

# Use it in translations
greeting = translate("Welcome!", language=user_language)
```

## Troubleshooting

### Translations not appearing

1. **Check .mo file exists**:
   ```bash
   ls -la application/i18n/locales/en/LC_MESSAGES/messages.mo
   ```

2. **Recompile translations**:
   ```bash
   python application/i18n/compile_translations.py
   ```

3. **Verify string in .po file**:
   Open `messages.po` and search for your string

### New strings showing as English

This is expected! English is the default language. New strings automatically fall back to their source text.

### Compilation errors

If compilation fails:
- Check `.po` file syntax
- Ensure quotes are balanced
- Look for special characters that need escaping

## Common Translation Strings

Here are commonly used strings already in the system:

**Navigation**:
- `"Home"`, `"Admin"`, `"Settings"`, `"Profile"`

**Actions**:
- `"Save"`, `"Cancel"`, `"Delete"`, `"Edit"`, `"Create"`, `"Submit"`
- `"Close"`, `"Search"`, `"Filter"`, `"Back"`, `"Next"`, `"Previous"`

**Status**:
- `"Loading..."`, `"Error"`, `"Success"`, `"Warning"`, `"Information"`

**Messages**:
- `"No data available"`
- `"Operation completed successfully"`
- `"An error occurred"`
- `"You do not have permission to view this page"`

**User Interface**:
- `"User Menu"`, `"View Profile"`, `"Sign Out"`
- `"Permission Level"`, `"Active Account"`

See `application/i18n/locales/en/LC_MESSAGES/messages.po` for the complete list.

## Migration Strategy

The i18n system has been added in a non-breaking way:

1. **Gradual adoption**: Not required to translate everything at once
2. **Backwards compatible**: Untranslated strings display as-is
3. **No breaking changes**: Existing code continues to work
4. **Optional usage**: Use `_()` wrapper only when convenient

**Recommended approach**:
- Start with new features: Wrap all strings in new code
- Update iteratively: Gradually add translations to existing code
- Focus on user-visible text: Internal logs/debug messages can remain untranslated

## Tools and Commands

### Compile translations
```bash
python application/i18n/compile_translations.py
```

### Find untranslated strings
```bash
# Search for ui.label, ui.button without _()
grep -r "ui.label\|ui.button" pages/ views/ components/ | grep -v "_("
```

### Extract strings (future with gettext tools)
```bash
# If you install gettext tools
xgettext --language=Python --keyword=_ --output=messages.pot **/*.py
```

## References

- [Python gettext documentation](https://docs.python.org/3/library/gettext.html)
- [GNU gettext manual](https://www.gnu.org/software/gettext/manual/)
- [PO file format](https://www.gnu.org/software/gettext/manual/html_node/PO-Files.html)

## Support

For questions or issues with the i18n system:
1. Check this guide
2. Review example usage in tests: `tests/test_i18n.py`
3. Examine the implementation: `application/i18n/translations.py`
