# Dark Mode Persistence Fix

## Summary
Fixed dark mode to persist across page loads using an external JavaScript module with browser localStorage. All JavaScript has been moved to external files following the project's JavaScript guidelines.

## Changes Made

### 1. JavaScript Organization (`static/js/core/dark-mode.js`)
- Created external JavaScript module for dark mode management
- Implements IIFE pattern for encapsulation
- Provides public API via `window.DarkMode`
- Auto-executes on script load to restore dark mode before page renders
- Includes error handling and fallbacks

### 2. BasePage Component (`components/base_page.py`)
- Added `get_js_version()` function for JavaScript file cache busting
- Loads dark mode script in `<head>` via `ui.add_head_html()`
- Uses version hash to ensure cache invalidation on updates
- Removed inline JavaScript in favor of external file

### 3. User Menu (`components/user_menu.py`)
- Updated dark mode toggle to use `window.DarkMode.toggle()` API
- Simplified from inline JavaScript to single API call
- Cleaner integration with external module

### 3. CSS Updates
Updated CSS selectors to support both `.body--dark` (legacy) and `.q-dark` (Quasar standard):

**Files Updated:**
- `static/css/base.css` - Changed `body:not(.body--dark)` to `body:not(.body--dark):not(.q-dark)`
- `static/css/layout.css` - Changed navbar selectors to exclude both dark mode classes
- `static/css/components.css` - Changed card component selectors to exclude both dark mode classes

These changes ensure that light mode styles are only applied when neither dark mode class is present.

## How It Works

1. **Page starts loading** - Browser receives HTML
2. **Head section loads** - CSS and JavaScript files are requested
3. **dark-mode.js executes** - Script runs immediately (IIFE in `<head>`)
4. **Check localStorage** - `localStorage.getItem('dark_mode_enabled') === 'true'`
5. **Apply immediately** - If enabled, adds `.q-dark` class to `<html>` and `<body>`
6. **Page renders** - Content appears already in dark mode (no flash!)
7. **User toggles** - Click "Toggle Dark Mode" calls `window.DarkMode.toggle()`
8. **Toggle executes** - JavaScript calls `window.Quasar.Dark.set(!current)` 
9. **Save to localStorage** - Saves new value: `localStorage.setItem('dark_mode_enabled', 'true'|'false')`
10. **CSS updates** - Variables change based on `.q-dark` class
11. **Next page load** - Steps 3-6 restore the preference instantly

## Technical Details

### External JavaScript Module (`static/js/core/dark-mode.js`)

**Public API:**
```javascript
window.DarkMode = {
    toggle: toggleDarkMode,      // Toggle dark mode on/off
    restore: restoreDarkMode,    // Restore from localStorage
    enable: enableDarkMode,      // Force enable
    disable: disableDarkMode,    // Force disable
    isActive: isDarkMode         // Get current state
};
```

**Auto-initialization:**
The script automatically calls `restoreDarkMode()` when it loads, ensuring dark mode is applied before the page renders.

### BasePage Integration
```python
# In base_page.py
js_version = get_js_version('core/dark-mode.js')
ui.add_head_html(f'<script src="/static/js/core/dark-mode.js?v={js_version}"></script>')
```

### User Menu Integration
```python
# In user_menu.py
def toggle_dark_mode():
    ui.run_javascript('window.DarkMode.toggle()')
```

## Benefits

✅ **No flash** - Dark mode applied before content is visible  
✅ **External JavaScript** - Follows project JavaScript guidelines  
✅ **Maintainable** - Dark mode logic in dedicated, testable file  
✅ **Reusable** - Public API can be used from anywhere  
✅ **Cached** - Browser caches external file for better performance  
✅ **Version controlled** - Cache busting ensures updates are loaded  
✅ **Single source of truth** - localStorage only  
✅ **Error handling** - Graceful fallbacks for edge cases  
✅ **Fast** - Minimal overhead, runs once per page load  

## JavaScript Guidelines

This implementation follows the project's JavaScript guidelines documented in `docs/JAVASCRIPT_GUIDELINES.md`:

- ✅ External file in `static/js/core/` directory
- ✅ IIFE pattern for encapsulation
- ✅ Public API exported to `window`
- ✅ JSDoc comments for all functions
- ✅ Error handling with try/catch
- ✅ Auto-initialization on script load
- ✅ Cache busting via version hash  

## CSS Selector Strategy
All dark mode styles use both selectors for compatibility:
```css
/* Dark mode styles */
.body--dark .element,
.q-dark .element {
    /* dark mode styles */
}

/* Light mode only (explicitly exclude both dark classes) */
body:not(.body--dark):not(.q-dark) .element {
    /* light mode styles */
}
```

## Testing

To test the flash-free dark mode:
1. Start the application
2. Navigate to any page
3. Click user menu → Toggle Dark Mode
4. Verify dark mode is applied smoothly
5. **Reload the page** (Cmd+R / F5)
6. ✅ Page loads directly in dark mode - **no white flash!**
7. Toggle back to light mode
8. Reload the page
9. ✅ Page loads directly in light mode - **no dark flash!**

## Related Files

- `components/base_page.py` - Dark mode initialization (head script)
- `components/user_menu.py` - Dark mode toggle
- `static/css/variables.css` - Dark mode color variables
- `static/css/base.css` - Base dark mode styles
- `static/css/layout.css` - Layout dark mode styles
- `static/css/components.css` - Component dark mode styles
- `static/css/footer.css` - Footer dark mode styles
- `static/css/sidebar-separator.css` - Sidebar dark mode styles
- `static/css/quasar-overrides.css` - Quasar component dark mode overrides
9. Verify light mode persists

## Related Files

- `main.py` - Dark mode initialization
- `components/user_menu.py` - Dark mode toggle
- `static/css/variables.css` - Dark mode color variables
- `static/css/base.css` - Base dark mode styles
- `static/css/layout.css` - Layout dark mode styles
- `static/css/components.css` - Component dark mode styles
- `static/css/footer.css` - Footer dark mode styles
- `static/css/sidebar-separator.css` - Sidebar dark mode styles
- `static/css/quasar-overrides.css` - Quasar component dark mode overrides
