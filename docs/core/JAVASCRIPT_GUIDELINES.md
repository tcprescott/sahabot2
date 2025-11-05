# JavaScript Guidelines

## Overview
All custom JavaScript in SahaBot2 should be organized in external files within the `static/js/` directory. This promotes maintainability, reusability, and proper separation of concerns.

## Principles

### 1. No Inline JavaScript
- ❌ **Don't** use inline `<script>` tags via `ui.add_head_html()`
- ❌ **Don't** use `ui.run_javascript()` for complex logic
- ✅ **Do** create external `.js` files in `static/js/`
- ✅ **Do** load JavaScript files via `ui.add_head_html('<script src="...">')`

### 2. File Organization
```
static/js/
├── README.md              # Directory documentation
├── core/                  # Core functionality loaded on every page
│   ├── dark-mode.js       # Dark mode persistence and toggle
│   └── url-manager.js     # URL/query parameter management
├── utils/                 # Utility modules loaded as needed
│   ├── clipboard.js       # Clipboard operations
│   ├── window-utils.js    # Window/DOM utilities
│   └── ...
├── features/              # Feature-specific scripts loaded conditionally
│   ├── tournaments.js     # Tournament-related functionality
│   ├── races.js           # Race management
│   └── notifications.js
└── vendor/                # Third-party libraries (if needed)
    └── ...
```

**Core vs Utils vs Features:**
- **core/**: Scripts loaded on every page (dark mode, URL management)
- **utils/**: Reusable utilities loaded on most pages (clipboard, window operations)
- **features/**: Feature-specific scripts loaded only when needed

### 3. Loading JavaScript Files

**In BasePage or page components:**
```python
# Load a JavaScript file
ui.add_head_html('<script src="/static/js/core/dark-mode.js"></script>')

# With cache busting (recommended)
from pathlib import Path
import hashlib

def get_js_version(filename: str) -> str:
    """Get cache-busting version for a JS file."""
    js_file = Path(__file__).parent.parent / 'static' / 'js' / filename
    if js_file.exists():
        content = js_file.read_bytes()
        return hashlib.md5(content).hexdigest()[:8]
    return '1'

js_version = get_js_version('core/dark-mode.js')
ui.add_head_html(f'<script src="/static/js/core/dark-mode.js?v={js_version}"></script>')
```

### 4. JavaScript File Structure

**Standard module pattern:**
```javascript
/**
 * Feature Name
 * 
 * Description of what this module does.
 */

(function() {
    'use strict';
    
    // Private variables
    const STORAGE_KEY = 'my_feature_setting';
    
    // Private functions
    function initializeFeature() {
        // Initialization logic
    }
    
    // Public API (if needed for NiceGUI integration)
    window.MyFeature = {
        initialize: initializeFeature,
        // Other public methods
    };
    
    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeFeature);
    } else {
        initializeFeature();
    }
})();
```

### 5. Integration with NiceGUI

**For features that need Python callbacks:**
```javascript
// In JavaScript file
window.MyFeature = {
    doSomething: function(data) {
        // Process data
        return result;
    }
};
```

```python
# In Python
# Call JavaScript from Python
result = await ui.run_javascript('window.MyFeature.doSomething({data})')

# Register Python callback that JavaScript can call
def my_callback(data):
    # Handle callback
    pass

ui.add_head_html('''
    <script>
        window.pythonCallback = async function(data) {
            await fetch('/api/callback', {
                method: 'POST',
                body: JSON.stringify(data)
            });
        };
    </script>
''')
```

### 6. Code Style

**Use modern JavaScript:**
- Use `const` and `let` (not `var`)
- Use arrow functions where appropriate
- Use template literals for strings
- Include JSDoc comments for functions
- Use strict mode (`'use strict';`)

**Example:**
```javascript
/**
 * Toggle a feature on/off
 * @param {boolean} enabled - Whether the feature should be enabled
 * @returns {boolean} The new state
 */
function toggleFeature(enabled) {
    'use strict';
    
    const newState = !enabled;
    localStorage.setItem('feature_enabled', newState.toString());
    return newState;
}
```

### 7. Error Handling

**Always include error handling:**
```javascript
try {
    const data = JSON.parse(localStorage.getItem('my_data'));
    processData(data);
} catch (error) {
    console.error('Failed to process data:', error);
    // Fallback behavior
}
```

### 8. Performance Considerations

**Minimize DOM operations:**
```javascript
// ❌ Bad - multiple reflows
for (let i = 0; i < items.length; i++) {
    document.body.appendChild(createItem(items[i]));
}

// ✅ Good - single reflow
const fragment = document.createDocumentFragment();
for (let i = 0; i < items.length; i++) {
    fragment.appendChild(createItem(items[i]));
}
document.body.appendChild(fragment);
```

**Debounce expensive operations:**
```javascript
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Usage
const expensiveOperation = debounce(() => {
    // Do expensive thing
}, 300);
```

## Common Patterns

### 1. Feature Detection
```javascript
if (typeof window.Quasar !== 'undefined') {
    // Quasar is available
}

if ('localStorage' in window) {
    // localStorage is available
}
```

### 2. Safe Storage Access
```javascript
function getStorageItem(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item !== null ? item : defaultValue;
    } catch (error) {
        console.warn(`Failed to read ${key} from storage:`, error);
        return defaultValue;
    }
}

function setStorageItem(key, value) {
    try {
        localStorage.setItem(key, value);
        return true;
    } catch (error) {
        console.warn(`Failed to write ${key} to storage:`, error);
        return false;
    }
}
```

### 3. Waiting for Elements
```javascript
function waitForElement(selector, callback, timeout = 5000) {
    const element = document.querySelector(selector);
    if (element) {
        callback(element);
        return;
    }
    
    const observer = new MutationObserver((mutations, obs) => {
        const element = document.querySelector(selector);
        if (element) {
            callback(element);
            obs.disconnect();
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Timeout fallback
    setTimeout(() => observer.disconnect(), timeout);
}
```

## Migration Strategy

When converting inline JavaScript to external files:

1. **Identify** inline JavaScript in the codebase
2. **Extract** to appropriately named file in `static/js/`
3. **Organize** into IIFE or module pattern
4. **Test** functionality
5. **Update** Python code to load the external file
6. **Remove** inline JavaScript

## Examples

### Example 1: Dark Mode (Core Feature)

**File: `static/js/core/dark-mode.js`**
```javascript
/**
 * Dark Mode Management
 * 
 * Handles dark mode persistence and restoration across page loads.
 * Prevents flash of unstyled content (FOUC) by applying dark mode
 * before the page renders.
 */

(function() {
    'use strict';
    
    const STORAGE_KEY = 'dark_mode_enabled';
    
    /**
     * Restore dark mode from localStorage
     * Runs immediately to prevent FOUC
     */
    function restoreDarkMode() {
        const darkModeEnabled = localStorage.getItem(STORAGE_KEY) === 'true';
        if (darkModeEnabled) {
            applyDarkMode();
        }
    }
    
    /**
     * Apply dark mode classes to the document
     */
    function applyDarkMode() {
        document.documentElement.classList.add('q-dark');
        if (document.body) {
            document.body.classList.add('q-dark');
        } else {
            // Wait for body to exist
            const observer = new MutationObserver(function(mutations, obs) {
                if (document.body) {
                    document.body.classList.add('q-dark');
                    obs.disconnect();
                }
            });
            observer.observe(document.documentElement, { childList: true });
        }
    }
    
    /**
     * Toggle dark mode on/off
     * @returns {boolean} The new dark mode state
     */
    function toggleDarkMode() {
        if (typeof window.Quasar === 'undefined') {
            console.warn('Quasar not available');
            return false;
        }
        
        const newValue = !window.Quasar.Dark.isActive;
        window.Quasar.Dark.set(newValue);
        localStorage.setItem(STORAGE_KEY, newValue.toString());
        return newValue;
    }
    
    // Public API for NiceGUI integration
    window.DarkMode = {
        toggle: toggleDarkMode,
        restore: restoreDarkMode
    };
    
    // Restore dark mode immediately (before DOM ready)
    restoreDarkMode();
})();
```

**Python usage:**
```python
# In base_page.py
ui.add_head_html('<script src="/static/js/core/dark-mode.js"></script>')

# In user_menu.py
'on_click': lambda: ui.run_javascript('window.DarkMode.toggle()')
```

### Example 2: Feature-Specific Script

**File: `static/js/features/tournament-timer.js`**
```javascript
/**
 * Tournament Timer
 * 
 * Displays countdown timers for tournament events.
 */

(function() {
    'use strict';
    
    /**
     * Format time remaining as HH:MM:SS
     * @param {number} seconds - Seconds remaining
     * @returns {string} Formatted time string
     */
    function formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    
    /**
     * Initialize tournament timer
     * @param {string} elementId - ID of the timer element
     * @param {number} targetTimestamp - Unix timestamp of target time
     */
    function initTimer(elementId, targetTimestamp) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        function updateTimer() {
            const now = Date.now() / 1000;
            const remaining = Math.max(0, targetTimestamp - now);
            
            element.textContent = formatTime(Math.floor(remaining));
            
            if (remaining > 0) {
                requestAnimationFrame(updateTimer);
            } else {
                element.textContent = 'Started!';
            }
        }
        
        updateTimer();
    }
    
    // Public API
    window.TournamentTimer = {
        init: initTimer
    };
})();
```

## Testing

**Manual testing checklist:**
- [ ] Script loads without errors (check browser console)
- [ ] Functionality works as expected
- [ ] Works after page reload
- [ ] Works in both light and dark mode
- [ ] No console errors or warnings
- [ ] Cache busting works (changes are reflected)

## Debugging

**Common issues:**

1. **Script not loading**: Check file path and permissions
2. **Function not defined**: Ensure public API is exported to `window`
3. **Timing issues**: Use `DOMContentLoaded` or MutationObserver
4. **Cache issues**: Implement version/hash-based cache busting

**Browser console debugging:**
```javascript
// Check if script loaded
console.log('Script loaded:', typeof window.MyFeature !== 'undefined');

// Debug timing
console.log('DOM ready:', document.readyState);
console.log('Body exists:', !!document.body);
```

## Benefits

✅ **Maintainability** - Easier to find, edit, and test JavaScript code  
✅ **Reusability** - Scripts can be shared across multiple pages  
✅ **Caching** - Browsers cache external files, improving performance  
✅ **Debugging** - Browser dev tools work better with external files  
✅ **Version control** - Changes are tracked more clearly in Git  
✅ **Testing** - External files can be tested independently  
✅ **Minification** - Can be minified/bundled for production  
✅ **Code review** - Easier to review JavaScript changes separately
