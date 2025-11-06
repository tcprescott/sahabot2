"""
Sentry browser initialization script.

This JavaScript module initializes Sentry for frontend error tracking and performance monitoring.
It is loaded by BasePage to capture JavaScript errors, unhandled promise rejections, and
client-side performance data.
"""

// Initialize Sentry for browser/frontend monitoring
(function() {
    // Get configuration from data attributes on script tag
    const script = document.currentScript;
    const sentryDsn = script?.dataset?.sentryDsn;
    const sentryEnvironment = script?.dataset?.sentryEnvironment || 'development';
    const tracesSampleRate = parseFloat(script?.dataset?.tracesSampleRate || '0.1');
    const replaysSessionSampleRate = parseFloat(script?.dataset?.replaysSessionSampleRate || '0.0');
    const replaysOnErrorSampleRate = parseFloat(script?.dataset?.replaysOnErrorSampleRate || '0.0');

    // Only initialize if DSN is provided
    if (!sentryDsn || sentryDsn === 'none') {
        console.debug('Sentry browser monitoring not configured (no DSN)');
        return;
    }

    // Dynamically load Sentry browser SDK from CDN
    const sentryScript = document.createElement('script');
    sentryScript.src = 'https://browser.sentry-cdn.com/8.40.0/bundle.tracing.replay.min.js';
    sentryScript.integrity = 'sha384-ps+lLHGHvSxLDvs7OdxW6t1bPyGqKxjgW0kJrX/H+TCKmxjOBjvdW1LBcJu7JQVJ';
    sentryScript.crossOrigin = 'anonymous';
    
    sentryScript.onload = function() {
        try {
            // Initialize Sentry
            Sentry.init({
                dsn: sentryDsn,
                environment: sentryEnvironment,
                
                // Performance Monitoring
                integrations: [
                    Sentry.browserTracingIntegration(),
                    Sentry.replayIntegration(),
                ],
                
                // Performance monitoring sample rate
                tracesSampleRate: tracesSampleRate,
                
                // Session Replay (optional, usually disabled to save quota)
                replaysSessionSampleRate: replaysSessionSampleRate,
                replaysOnErrorSampleRate: replaysOnErrorSampleRate,
                
                // Capture user interactions as breadcrumbs
                beforeBreadcrumb(breadcrumb, hint) {
                    // Filter out noisy breadcrumbs if needed
                    return breadcrumb;
                },
                
                // Add custom context
                beforeSend(event, hint) {
                    // Add custom tags
                    event.tags = event.tags || {};
                    event.tags.platform = 'browser';
                    event.tags.framework = 'nicegui';
                    
                    return event;
                },
            });
            
            console.debug('Sentry browser monitoring initialized', {
                environment: sentryEnvironment,
                tracesSampleRate: tracesSampleRate
            });
            
        } catch (error) {
            console.error('Failed to initialize Sentry:', error);
        }
    };
    
    sentryScript.onerror = function() {
        console.error('Failed to load Sentry browser SDK from CDN');
    };
    
    document.head.appendChild(sentryScript);
})();
