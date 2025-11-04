/**
 * Clipboard Utilities Module
 * Provides clipboard operations with error handling
 * 
 * Public API:
 * - window.ClipboardUtils.copy(text) - Copy text to clipboard (returns Promise)
 * - window.ClipboardUtils.copyWithFallback(text) - Copy with fallback for older browsers
 */

(function() {
    'use strict';

    /**
     * Copy text to clipboard using modern Clipboard API
     * @param {string} text - Text to copy
     * @returns {Promise<boolean>} Promise that resolves to true if successful
     */
    async function copyToClipboard(text) {
        try {
            if (!navigator.clipboard) {
                console.warn('Clipboard API not available, using fallback');
                return copyWithFallback(text);
            }
            
            await navigator.clipboard.writeText(text);
            console.log('Text copied to clipboard:', text.substring(0, 50) + (text.length > 50 ? '...' : ''));
            return true;
        } catch (err) {
            console.error('Failed to copy text:', err);
            return false;
        }
    }

    /**
     * Fallback copy method for browsers without Clipboard API
     * Creates a temporary textarea element to perform copy operation
     * @param {string} text - Text to copy
     * @returns {boolean} True if successful
     */
    function copyWithFallback(text) {
        try {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.top = '0';
            textarea.style.left = '0';
            textarea.style.opacity = '0';
            
            document.body.appendChild(textarea);
            textarea.focus();
            textarea.select();
            
            const successful = document.execCommand('copy');
            document.body.removeChild(textarea);
            
            if (successful) {
                console.log('Text copied to clipboard (fallback):', text.substring(0, 50) + (text.length > 50 ? '...' : ''));
            }
            
            return successful;
        } catch (err) {
            console.error('Fallback copy failed:', err);
            return false;
        }
    }

    // Export public API
    window.ClipboardUtils = {
        copy: copyToClipboard,
        copyWithFallback: copyWithFallback
    };

})();
