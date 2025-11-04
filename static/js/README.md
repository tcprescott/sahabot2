# JavaScript Directory

This directory contains all custom JavaScript for the SahaBot2 application.

## Organization

## Directory Structure

```
static/js/
├── README.md           # This file
├── core/              # Core functionality that loads on every page
│   ├── dark-mode.js   # Dark mode persistence and toggle
│   └── url-manager.js # URL/query parameter management
└── utils/             # Utility modules loaded as needed
    ├── clipboard.js      # Clipboard operations
    └── window-utils.js   # Window/DOM utilities
```

## Core Scripts

Core scripts are loaded on every page via `base_page.py` and provide essential functionality:

### dark-mode.js
Manages dark mode persistence using localStorage and Quasar Dark API.
- **API**: `window.DarkMode`
- **Methods**: `toggle()`, `enable()`, `disable()`, `isActive()`, `restore()`
- **Load**: Must load in `<head>` to prevent flash

### url-manager.js
Handles URL query parameter operations and navigation.
- **API**: `window.URLManager`
- **Methods**: 
  - `getParams()` - Get all query parameters as object
  - `getParam(name)` - Get single parameter value
  - `setParam(name, value)` - Set parameter and update URL
  - `removeParam(name)` - Remove parameter from URL
  - `setParams(params)` - Set multiple parameters at once
- **Load**: In `<head>` with core modules

## Utility Scripts

Utility scripts provide common operations used across multiple features:

### clipboard.js
Provides clipboard operations with error handling and fallback support.
- **API**: `window.ClipboardUtils`
- **Methods**:
  - `copy(text)` - Copy text to clipboard (returns Promise<boolean>)
  - `copyWithFallback(text)` - Copy with fallback for older browsers
- **Load**: In `<head>` with core modules
- **Usage**: All clipboard operations should use this module

### window-utils.js
Handles window and DOM-related operations.
- **API**: `window.WindowUtils`
- **Methods**:
  - `open(url, target, features)` - Open new window/tab
  - `dispatchResize(delay)` - Dispatch window resize event
  - `confirm(message)` - Show native confirm dialog
- **Load**: In `<head>` with core modules
- **Usage**: All window.open, confirm dialogs, and resize events should use this module

## Guidelines

**All JavaScript should follow the patterns documented in [`docs/JAVASCRIPT_GUIDELINES.md`](../../docs/JAVASCRIPT_GUIDELINES.md).**

Key principles:
- ✅ **External files only** - No inline `<script>` tags
- ✅ **IIFE pattern** - Encapsulate code to avoid global pollution
- ✅ **Public APIs** - Export to `window` for NiceGUI integration
- ✅ **Error handling** - Use try/catch blocks
- ✅ **Documentation** - Include JSDoc comments
- ✅ **Cache busting** - Load with version hashes in Python

## Core Scripts

### dark-mode.js
Manages dark mode persistence across page loads.

**Public API:**
- `window.DarkMode.toggle()` - Toggle dark/light mode
- `window.DarkMode.enable()` - Force enable dark mode
- `window.DarkMode.disable()` - Force disable dark mode
- `window.DarkMode.isActive()` - Get current dark mode state
- `window.DarkMode.restore()` - Restore from localStorage (auto-called)

**Usage in Python:**
```python
## Usage Examples

### Using Dark Mode
```python
# In Python component
ui.button('Toggle Dark Mode', on_click=lambda: ui.run_javascript('window.DarkMode.toggle()'))
```

### Using URL Manager
```python
# Get query parameters
params = await ui.run_javascript('return window.URLManager.getParams();')

# Set a parameter
ui.run_javascript("window.URLManager.setParam('view', 'settings');")

# Get single parameter
view = await ui.run_javascript("return window.URLManager.getParam('view');")
```

### Using Clipboard Utils
```python
# Copy text to clipboard
async def copy_text():
    success = await ui.run_javascript(
        f'return window.ClipboardUtils.copy("{text}");'
    )
    if success:
        ui.notify('Copied!', type='positive')
    else:
        ui.notify('Failed to copy', type='negative')
```

### Using Window Utils
```python
# Open new window
ui.run_javascript(f'window.WindowUtils.open("{url}");')

# Dispatch resize event with delay
ui.run_javascript('window.WindowUtils.dispatchResize(100);')

# Show confirmation dialog
result = await ui.run_javascript(
    'return window.WindowUtils.confirm("Are you sure?");'
)
```
```

## Adding New Scripts

When adding new JavaScript functionality:

1. **Create the file** in the appropriate subdirectory:
   - `core/` for essential features used on every page
   - `features/` for specific features (tournaments, races, etc.)

2. **Follow the template:**
```javascript
/**
 * Feature Name
 * 
 * Description of functionality.
 */

(function() {
    'use strict';
    
    // Private functions
    function doSomething() {
        // Implementation
    }
    
    // Public API
    window.MyFeature = {
        doSomething: doSomething
    };
    
    // Auto-initialize if needed
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', doSomething);
    } else {
        doSomething();
    }
})();
```

3. **Load in Python** with cache busting:
```python
js_version = get_js_version('features/my-feature.js')
ui.add_head_html(f'<script src="/static/js/features/my-feature.js?v={js_version}"></script>')
```

4. **Document** the public API in this README

## Testing

Test all JavaScript in:
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Both light and dark modes
- ✅ Page reload scenarios

Check the browser console for errors after making changes.
