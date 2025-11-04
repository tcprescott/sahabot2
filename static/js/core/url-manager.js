/**
 * URL Manager Module
 * Handles URL query parameter operations and navigation
 * 
 * Public API:
 * - window.URLManager.getParams() - Get all query parameters as object
 * - window.URLManager.getParam(name) - Get single parameter value
 * - window.URLManager.setParam(name, value) - Set parameter and update URL
 * - window.URLManager.removeParam(name) - Remove parameter from URL
 * - window.URLManager.setParams(params) - Set multiple parameters at once
 */

(function() {
    'use strict';

    /**
     * Get all query parameters from current URL
     * @returns {Object} Object with parameter names as keys
     */
    function getQueryParams() {
        const params = new URLSearchParams(window.location.search);
        const result = {};
        
        for (const [key, value] of params.entries()) {
            result[key] = value;
        }
        
        return result;
    }

    /**
     * Get a single query parameter value
     * @param {string} name - Parameter name
     * @returns {string|null} Parameter value or null if not found
     */
    function getQueryParam(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    }

    /**
     * Set a query parameter and update the URL
     * @param {string} name - Parameter name
     * @param {string} value - Parameter value
     * @param {boolean} replace - Use replaceState instead of pushState (default: false)
     */
    function setQueryParam(name, value, replace = false) {
        const url = new URL(window.location);
        url.searchParams.set(name, value);
        
        if (replace) {
            window.history.replaceState({}, '', url);
        } else {
            window.history.pushState({}, '', url);
        }
    }

    /**
     * Remove a query parameter from the URL
     * @param {string} name - Parameter name
     * @param {boolean} replace - Use replaceState instead of pushState (default: false)
     */
    function removeQueryParam(name, replace = false) {
        const url = new URL(window.location);
        url.searchParams.delete(name);
        
        if (replace) {
            window.history.replaceState({}, '', url);
        } else {
            window.history.pushState({}, '', url);
        }
    }

    /**
     * Set multiple query parameters at once
     * @param {Object} params - Object with parameter names and values
     * @param {boolean} replace - Use replaceState instead of pushState (default: false)
     */
    function setQueryParams(params, replace = false) {
        const url = new URL(window.location);
        
        for (const [name, value] of Object.entries(params)) {
            if (value === null || value === undefined) {
                url.searchParams.delete(name);
            } else {
                url.searchParams.set(name, value);
            }
        }
        
        if (replace) {
            window.history.replaceState({}, '', url);
        } else {
            window.history.pushState({}, '', url);
        }
    }

    // Export public API
    window.URLManager = {
        getParams: getQueryParams,
        getParam: getQueryParam,
        setParam: setQueryParam,
        removeParam: removeQueryParam,
        setParams: setQueryParams
    };

})();
