/**
 * Window Utilities Module
 * Handles window and DOM-related operations
 * 
 * Public API:
 * - window.WindowUtils.open(url, target, features) - Open new window/tab
 * - window.WindowUtils.dispatchResize() - Dispatch window resize event
 * - window.WindowUtils.confirm(message) - Show native confirm dialog
 */

(function() {
    'use strict';

    /**
     * Open a new window or tab
     * @param {string} url - URL to open
     * @param {string} target - Target window name (default: '_blank')
     * @param {string} features - Window features string (optional)
     * @returns {Window|null} Reference to opened window, or null if blocked
     */
    function openWindow(url, target = '_blank', features = '') {
        try {
            const newWindow = window.open(url, target, features);
            if (!newWindow) {
                console.warn('Window.open blocked by popup blocker');
            }
            return newWindow;
        } catch (err) {
            console.error('Failed to open window:', err);
            return null;
        }
    }

    /**
     * Dispatch a window resize event
     * Useful for triggering responsive layout recalculations
     * @param {number} delay - Delay in milliseconds before dispatching (default: 0)
     */
    function dispatchResize(delay = 0) {
        if (delay > 0) {
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, delay);
        } else {
            window.dispatchEvent(new Event('resize'));
        }
    }

    /**
     * Show native confirmation dialog
     * @param {string} message - Confirmation message
     * @returns {boolean} True if user clicked OK, false if cancelled
     */
    function confirmDialog(message) {
        return window.confirm(message);
    }

    // Export public API
    window.WindowUtils = {
        open: openWindow,
        dispatchResize: dispatchResize,
        confirm: confirmDialog
    };

})();
