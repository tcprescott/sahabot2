"""
Input validation and sanitization utilities.

This module provides utilities for validating and sanitizing user input
to prevent security vulnerabilities.
"""

import re
from typing import Optional, Union
from html import escape


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML by escaping special characters.

    This prevents XSS attacks by converting HTML special characters
    to their entity equivalents.

    Args:
        text: Text that may contain HTML

    Returns:
        str: Text with HTML special characters escaped
    """
    return escape(text)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal attacks.

    Removes path separators and other potentially dangerous characters.

    Args:
        filename: Original filename

    Returns:
        str: Sanitized filename safe for filesystem operations
    """
    # Remove any path separators
    filename = filename.replace('/', '').replace('\\', '')

    # Remove null bytes
    filename = filename.replace('\0', '')

    # Remove leading dots (hidden files)
    filename = filename.lstrip('.')

    # Keep only alphanumeric, spaces, hyphens, underscores, and dots
    filename = re.sub(r'[^\w\s\-\.]', '', filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename or 'unnamed'


def validate_url(url: str, allowed_schemes: Optional[list] = None) -> bool:
    """
    Validate that a URL is safe and uses allowed schemes.

    Args:
        url: URL to validate
        allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])

    Returns:
        bool: True if URL is valid and safe, False otherwise
    """
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']

    # Basic URL pattern matching
    url_pattern = re.compile(
        r'^(?P<scheme>[a-z][a-z0-9+\-.]*):\/\/'  # Scheme
        r'(?:[^\s:@\/]+(?::[^\s:@\/]*)?@)?'  # Optional user:pass
        r'(?P<host>[^\s\/:?#]+)'  # Host
        r'(?::(?P<port>\d+))?'  # Optional port
        r'(?P<path>\/[^\s?#]*)?'  # Optional path
        r'(?:\?[^\s#]*)?'  # Optional query
        r'(?:#[^\s]*)?$',  # Optional fragment
        re.IGNORECASE
    )

    match = url_pattern.match(url)
    if not match:
        return False

    # Check scheme
    scheme = match.group('scheme').lower()
    if scheme not in allowed_schemes:
        return False

    return True


def sanitize_discord_id(discord_id: Union[str, int]) -> Optional[int]:
    """
    Sanitize and validate a Discord ID.

    Discord IDs are 64-bit integers (snowflakes).

    Args:
        discord_id: Discord ID as string or int

    Returns:
        Optional[int]: Validated Discord ID as integer, or None if invalid
    """
    try:
        id_int = int(discord_id)
        # Discord IDs are positive integers
        if id_int > 0:
            return id_int
    except (ValueError, TypeError):
        pass
    return None


def sanitize_username(username: str, max_length: int = 32) -> str:
    """
    Sanitize a username for display.

    Removes control characters and excessive whitespace.

    Args:
        username: Username to sanitize
        max_length: Maximum allowed length (default: 32)

    Returns:
        str: Sanitized username
    """
    # Remove control characters
    username = ''.join(char for char in username if ord(char) >= 32)

    # Normalize whitespace
    username = ' '.join(username.split())

    # Truncate to max length
    if len(username) > max_length:
        username = username[:max_length]

    return username.strip()


def validate_email(email: str) -> bool:
    """
    Basic email validation.

    This is not RFC 5322 compliant, but catches common issues.

    Args:
        email: Email address to validate

    Returns:
        bool: True if email appears valid, False otherwise
    """
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    return bool(email_pattern.match(email))


def sanitize_integer(value: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> Optional[int]:
    """
    Sanitize and validate an integer input.

    Args:
        value: Value to convert to integer
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)

    Returns:
        Optional[int]: Validated integer, or None if invalid
    """
    try:
        int_val = int(value)

        if min_val is not None and int_val < min_val:
            return None

        if max_val is not None and int_val > max_val:
            return None

        return int_val
    except (ValueError, TypeError):
        return None
