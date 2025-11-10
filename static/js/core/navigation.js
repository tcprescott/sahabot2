/**
 * Navigation Module
 * Handles client-side navigation operations including view path updates
 * 
 * Public API:
 * - window.Navigation.updateViewPath(viewKey) - Update URL path with new view segment
 */

(function() {
    'use strict';

    /**
     * Update the URL path to reflect a new view segment
     * Intelligently replaces the last path segment if it's a view identifier (non-numeric)
     * while preserving numeric IDs in the path
     * 
     * @param {string} viewKey - The view identifier to add to the path
     */
    function updateViewPath(viewKey) {
        const currentPath = window.location.pathname;
        const pathParts = currentPath.split('/').filter(p => p);
        
        // Remove last part if it's not purely numeric (i.e., it's likely a view identifier)
        // View identifiers are typically kebab-case or snake_case strings
        if (pathParts.length > 0) {
            const lastPart = pathParts[pathParts.length - 1];
            // If last part is not a pure number, remove it (it's likely a previous view)
            if (isNaN(parseInt(lastPart)) || lastPart !== String(parseInt(lastPart))) {
                pathParts.pop();
            }
        }
        
        pathParts.push(viewKey);
        const newPath = '/' + pathParts.join('/');
        window.history.pushState({}, '', newPath);
    }

    // Export public API
    window.Navigation = {
        updateViewPath: updateViewPath
    };

})();
