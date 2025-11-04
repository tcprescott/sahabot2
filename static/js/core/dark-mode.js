/**
 * Dark Mode Management
 * 
 * Handles dark mode persistence and restoration across page loads.
 * Prevents flash of unstyled content (FOUC) by applying dark mode
 * before the page renders.
 * 
 * Storage: Uses localStorage with key 'dark_mode_enabled'
 * Classes: Applies 'q-dark' class to <html> and <body>
 */

(function() {
    'use strict';
    
    const STORAGE_KEY = 'dark_mode_enabled';
    
    /**
     * Restore dark mode from localStorage
     * Runs immediately to prevent FOUC
     */
    function restoreDarkMode() {
        try {
            const darkModeEnabled = localStorage.getItem(STORAGE_KEY) === 'true';
            if (darkModeEnabled) {
                applyDarkMode();
            }
        } catch (error) {
            console.warn('Failed to restore dark mode:', error);
        }
    }
    
    /**
     * Apply dark mode classes to the document
     */
    function applyDarkMode() {
        // Apply to html element immediately
        document.documentElement.classList.add('q-dark');
        
        // Apply to body (with fallback for timing)
        if (document.body) {
            document.body.classList.add('q-dark');
        } else {
            // Wait for body to exist using MutationObserver
            const observer = new MutationObserver(function(mutations, obs) {
                if (document.body) {
                    document.body.classList.add('q-dark');
                    obs.disconnect();
                }
            });
            observer.observe(document.documentElement, { 
                childList: true,
                subtree: false
            });
        }
    }
    
    /**
     * Remove dark mode classes from the document
     */
    function removeDarkMode() {
        document.documentElement.classList.remove('q-dark');
        if (document.body) {
            document.body.classList.remove('q-dark');
        }
    }
    
    /**
     * Toggle dark mode on/off
     * @returns {boolean} The new dark mode state
     */
    function toggleDarkMode() {
        try {
            // Get current state
            const isDark = document.documentElement.classList.contains('q-dark');
            const newValue = !isDark;
            
            // Toggle the classes
            if (newValue) {
                applyDarkMode();
            } else {
                removeDarkMode();
            }
            
            // Save to localStorage
            localStorage.setItem(STORAGE_KEY, newValue.toString());
            
            // If Quasar is available, sync with Quasar's dark mode
            if (typeof window.Quasar !== 'undefined' && window.Quasar.Dark) {
                window.Quasar.Dark.set(newValue);
            }
            
            return newValue;
        } catch (error) {
            console.error('Failed to toggle dark mode:', error);
            return false;
        }
    }
    
    /**
     * Get current dark mode state
     * @returns {boolean} Whether dark mode is currently enabled
     */
    function isDarkMode() {
        if (typeof window.Quasar !== 'undefined') {
            return window.Quasar.Dark.isActive;
        }
        return document.documentElement.classList.contains('q-dark');
    }
    
    /**
     * Enable dark mode
     */
    function enableDarkMode() {
        applyDarkMode();
        localStorage.setItem(STORAGE_KEY, 'true');
        
        // Sync with Quasar if available
        if (typeof window.Quasar !== 'undefined' && window.Quasar.Dark) {
            window.Quasar.Dark.set(true);
        }
    }
    
    /**
     * Disable dark mode
     */
    function disableDarkMode() {
        removeDarkMode();
        localStorage.setItem(STORAGE_KEY, 'false');
        
        // Sync with Quasar if available
        if (typeof window.Quasar !== 'undefined' && window.Quasar.Dark) {
            window.Quasar.Dark.set(false);
        }
    }
    
    // Public API for NiceGUI integration
    window.DarkMode = {
        toggle: toggleDarkMode,
        restore: restoreDarkMode,
        enable: enableDarkMode,
        disable: disableDarkMode,
        isActive: isDarkMode
    };
    
    // Restore dark mode immediately (runs as soon as script loads in <head>)
    restoreDarkMode();
})();
