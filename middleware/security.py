"""
Security middleware for adding security headers and HTTPS enforcement.

This module provides middleware for enhancing application security through
HTTP security headers and protocol enforcement.
"""

import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    This middleware adds important security headers including:
    - Strict-Transport-Security (HSTS)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Content-Security-Policy
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(self, app: ASGIApp):
        """Initialize the security headers middleware."""
        super().__init__(app)
        self.is_production = settings.is_production

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)

        # Add security headers
        headers_to_add = self._get_security_headers()
        for header_name, header_value in headers_to_add.items():
            response.headers[header_name] = header_value

        return response

    def _get_security_headers(self) -> dict:
        """
        Get security headers to add to responses.

        Returns:
            dict: Security headers
        """
        headers = {
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",

            # Prevent clickjacking
            "X-Frame-Options": "DENY",

            # Enable browser XSS protection (legacy, but defense in depth)
            "X-XSS-Protection": "1; mode=block",

            # Control referrer information
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Restrict browser features and APIs
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",

            # Content Security Policy
            # Note: This CSP allows 'unsafe-inline' and 'unsafe-eval' which weakens XSS protection.
            # These are required for NiceGUI framework to function properly.
            # NiceGUI uses inline styles and dynamic script evaluation for its reactive UI system.
            # Consider implementing CSP nonces or strict-dynamic if moving away from NiceGUI.
            # For now, we rely on input sanitization and HTML escaping for XSS protection.
            # See: application/utils/input_validation.py for sanitization utilities
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss: https://discord.com https://racetime.gg; "
                "frame-ancestors 'none';"
            ),
        }

        # Add HSTS header in production
        if self.is_production:
            # Enable HSTS with 1 year duration and include subdomains
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return headers


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS in production.

    This middleware enforces HTTPS in production environments by redirecting
    all HTTP requests to their HTTPS equivalents.
    """

    def __init__(self, app: ASGIApp):
        """Initialize the HTTPS redirect middleware."""
        super().__init__(app)
        self.is_production = settings.is_production

    async def dispatch(self, request: Request, call_next):
        """Redirect HTTP to HTTPS in production."""
        # Only enforce HTTPS in production
        if self.is_production:
            # Check if request is not already HTTPS
            if request.url.scheme != "https":
                # Get the forwarded proto header (for reverse proxy scenarios)
                forwarded_proto = request.headers.get("X-Forwarded-Proto", "")

                # Only redirect if not already behind HTTPS proxy
                if forwarded_proto != "https":
                    # Build HTTPS URL
                    https_url = request.url.replace(scheme="https")
                    logger.info("Redirecting HTTP request to HTTPS: %s", https_url)

                    # Return permanent redirect
                    return Response(
                        status_code=301,
                        headers={"Location": str(https_url)}
                    )

        # Continue with request
        return await call_next(request)
