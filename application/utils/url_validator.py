"""
URL validation utilities for preventing SSRF and XSS attacks.

This module provides utilities for validating URLs to prevent:
- Server-Side Request Forgery (SSRF) attacks
- XSS attacks via javascript: URLs
- Access to internal network resources
"""

import re
import ipaddress
import logging
from typing import Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Private IP ranges to block for SSRF protection
PRIVATE_IP_RANGES = [
    ipaddress.IPv4Network('10.0.0.0/8'),
    ipaddress.IPv4Network('172.16.0.0/12'),
    ipaddress.IPv4Network('192.168.0.0/16'),
    ipaddress.IPv4Network('127.0.0.0/8'),  # Loopback
    ipaddress.IPv4Network('169.254.0.0/16'),  # Link-local
    ipaddress.IPv4Network('0.0.0.0/8'),  # Current network
    ipaddress.IPv6Network('::1/128'),  # IPv6 loopback
    ipaddress.IPv6Network('fe80::/10'),  # IPv6 link-local
    ipaddress.IPv6Network('fc00::/7'),  # IPv6 unique local
]


def validate_url(
    url: str,
    allowed_schemes: Optional[List[str]] = None,
    block_private_ips: bool = True,
    max_length: int = 2048
) -> tuple[bool, Optional[str]]:
    """
    Validate that a URL is safe and uses allowed schemes.

    This function validates URLs to prevent:
    - XSS attacks (javascript:, data:, vbscript: URLs)
    - SSRF attacks (file:, gopher:, internal IPs)
    - Malformed URLs
    - Excessively long URLs

    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])
        block_private_ips: Whether to block private/internal IP addresses (default: True)
        max_length: Maximum allowed URL length (default: 2048)

    Returns:
        tuple[bool, Optional[str]]: (is_valid, error_message)
            - (True, None) if URL is valid
            - (False, error_message) if URL is invalid
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    # Check URL length
    if len(url) > max_length:
        return False, f"URL exceeds maximum length of {max_length} characters"

    # Check for dangerous schemes first (before pattern matching)
    # These schemes should NEVER be allowed, even if pattern matches
    dangerous_schemes = ['javascript', 'data', 'vbscript', 'file', 'gopher']
    
    # Extract scheme if present (check before full pattern match)
    scheme_match = re.match(r'^([a-z][a-z0-9+\-.]*):(.*)$', url, re.IGNORECASE)
    if scheme_match:
        scheme = scheme_match.group(1).lower()
        if scheme in dangerous_schemes:
            return False, f"URL scheme '{scheme}' is not allowed for security reasons"

    # Basic URL pattern matching (supports IPv4, IPv6, and hostnames)
    url_pattern = re.compile(
        r'^(?P<scheme>[a-z][a-z0-9+\-.]*):\/\/'  # Scheme
        r'(?:[^\s:@\/]+(?::[^\s:@\/]*)?@)?'  # Optional user:pass
        r'(?P<host>(\[[0-9a-fA-F:]+\]|[^\s\/:?#\[\]]+))'  # Host (IPv6 in brackets or regular)
        r'(?::(?P<port>\d+))?'  # Optional port
        r'(?P<path>\/[^\s?#]*)?'  # Optional path
        r'(?:\?[^\s#]*)?'  # Optional query
        r'(?:#[^\s]*)?$',  # Optional fragment
        re.IGNORECASE
    )

    match = url_pattern.match(url)
    if not match:
        return False, "Invalid URL format"

    # Check scheme against allowed list
    scheme = match.group('scheme').lower()
    if scheme not in allowed_schemes:
        return False, f"URL scheme '{scheme}' not allowed. Allowed schemes: {', '.join(allowed_schemes)}"

    # Parse URL to get hostname for SSRF checks
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False, "URL must contain a hostname"

        # Check if hostname is an IP address
        if block_private_ips:
            try:
                # Handle IPv6 addresses (remove brackets if present)
                hostname_clean = hostname.strip('[]')
                
                # Try to parse as IP address
                ip = ipaddress.ip_address(hostname_clean)

                # Check if IP is in private range
                for private_range in PRIVATE_IP_RANGES:
                    if ip in private_range:
                        logger.warning("Blocked URL with private IP address: %s", url)
                        return False, "URLs with private/internal IP addresses are not allowed"

            except ValueError:
                # Not an IP address, check for localhost keywords
                hostname_lower = hostname.lower()
                blocked_hostnames = [
                    'localhost',
                    'localhost.localdomain',
                    'broadcasthost',
                    'local',
                ]

                if hostname_lower in blocked_hostnames:
                    logger.warning("Blocked URL with localhost hostname: %s", url)
                    return False, "URLs with localhost/internal hostnames are not allowed"

# (Removed ineffective DNS rebinding check)
    except Exception as e:
        logger.error("Error parsing URL %s: %s", url, e)
        return False, "Failed to parse URL"

    return True, None


def sanitize_url(url: str) -> str:
    """
    Sanitize a URL by ensuring it has a valid scheme and format.

    This is a lightweight sanitization that:
    - Adds https:// prefix if no scheme is present
    - Strips whitespace
    - Normalizes the URL

    Note: This does NOT validate the URL. Always call validate_url() first.

    Args:
        url: URL to sanitize

    Returns:
        str: Sanitized URL
    """
    # Strip whitespace
    url = url.strip()

    # Add scheme if missing
    if not re.match(r'^[a-z][a-z0-9+\-.]*://', url, re.IGNORECASE):
        url = f"https://{url}"

    return url


def is_safe_redirect_url(url: str, base_url: str) -> bool:
    """
    Check if a URL is safe for redirect (to prevent open redirect vulnerabilities).

    A URL is considered safe if:
    - It's a relative path (starts with /)
    - It's an absolute URL with the same domain as base_url

    Args:
        url: URL to check
        base_url: Base URL of the application

    Returns:
        bool: True if URL is safe for redirect, False otherwise
    """
    # Allow relative paths
    if url.startswith('/') and not url.startswith('//'):
        return True

    # Parse both URLs
    try:
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)

        # Check if same domain
        if parsed_url.netloc and parsed_base.netloc:
            return parsed_url.netloc.lower() == parsed_base.netloc.lower()

    except Exception as e:
        logger.error("Error parsing URLs for redirect check: %s", e)

    return False
