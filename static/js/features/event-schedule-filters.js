/**
 * Event Schedule Filter Persistence
 * 
 * Saves and restores filter selections in localStorage for the event schedule view.
 * Filters are stored per organization to maintain separate state for different orgs.
 */

(function() {
    'use strict';
    
    const STORAGE_PREFIX = 'event_schedule_filters_';
    
    /**
     * Get storage key for organization
     * @param {number} organizationId - Organization ID
     * @returns {string} Storage key
     */
    function getStorageKey(organizationId) {
        return STORAGE_PREFIX + organizationId;
    }
    
    /**
     * Save filters to localStorage
     * @param {number} organizationId - Organization ID
     * @param {object} filters - Filter state object
     * @param {Array<string>} filters.states - Selected status states
     * @param {Array<number>} filters.tournaments - Selected tournament IDs
     */
    function saveFilters(organizationId, filters) {
        try {
            const key = getStorageKey(organizationId);
            const data = JSON.stringify(filters);
            localStorage.setItem(key, data);
            console.log('Saved event schedule filters for org', organizationId, filters);
            return true;
        } catch (error) {
            console.warn('Failed to save event schedule filters:', error);
            return false;
        }
    }
    
    /**
     * Load filters from localStorage
     * @param {number} organizationId - Organization ID
     * @returns {object|null} Filter state object or null if not found
     */
    function loadFilters(organizationId) {
        try {
            const key = getStorageKey(organizationId);
            const data = localStorage.getItem(key);
            
            if (!data) {
                return null;
            }
            
            const filters = JSON.parse(data);
            console.log('Loaded event schedule filters for org', organizationId, filters);
            return filters;
        } catch (error) {
            console.warn('Failed to load event schedule filters:', error);
            return null;
        }
    }
    
    /**
     * Clear filters from localStorage
     * @param {number} organizationId - Organization ID
     */
    function clearFilters(organizationId) {
        try {
            const key = getStorageKey(organizationId);
            localStorage.removeItem(key);
            console.log('Cleared event schedule filters for org', organizationId);
            return true;
        } catch (error) {
            console.warn('Failed to clear event schedule filters:', error);
            return false;
        }
    }
    
    /**
     * Get default filter state
     * @returns {object} Default filter state
     */
    function getDefaultFilters() {
        return {
            states: ['pending', 'scheduled', 'checked_in'],
            tournaments: []
        };
    }
    
    // Public API
    window.EventScheduleFilters = {
        save: saveFilters,
        load: loadFilters,
        clear: clearFilters,
        getDefault: getDefaultFilters
    };
    
})();
