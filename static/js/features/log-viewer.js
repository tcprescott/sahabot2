/**
 * Log Viewer JavaScript functionality
 *
 * Provides client-side functionality for the admin log viewer,
 * including scroll management and file downloads.
 */

window.LogViewer = {
    /**
     * Scroll a container element to the bottom.
     *
     * @param {number} elementId - The NiceGUI element ID to scroll
     */
    scrollToBottom: function(elementId) {
        const element = getElement(elementId);
        if (element) {
            element.scrollTop = element.scrollHeight;
        }
    },

    /**
     * Download content as a text file.
     *
     * @param {string} content - The text content to download
     * @param {string} filename - The filename for the download
     */
    downloadAsFile: function(content, filename) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
};
