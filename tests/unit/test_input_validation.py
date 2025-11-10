"""Tests for input validation utilities."""

import pytest
from application.utils.input_validation import (
    sanitize_html,
    sanitize_filename,
    validate_url,
    sanitize_discord_id,
    sanitize_username,
    validate_email,
    sanitize_integer,
)


class TestSanitizeHTML:
    """Tests for HTML sanitization."""

    def test_sanitize_basic_html(self):
        """Test that HTML special characters are escaped."""
        text = '<script>alert("XSS")</script>'
        result = sanitize_html(text)
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        assert "<script>" not in result

    def test_sanitize_ampersand(self):
        """Test that ampersands are escaped."""
        text = "A & B"
        result = sanitize_html(text)
        assert result == "A &amp; B"

    def test_sanitize_quotes(self):
        """Test that quotes are escaped."""
        text = 'He said "Hello"'
        result = sanitize_html(text)
        assert "&quot;" in result


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_remove_path_separators(self):
        """Test that path separators are removed."""
        filename = "../../../etc/passwd"
        result = sanitize_filename(filename)
        assert "/" not in result
        assert "\\" not in result
        assert result == "etcpasswd"

    def test_remove_null_bytes(self):
        """Test that null bytes are removed."""
        filename = "file\0.txt"
        result = sanitize_filename(filename)
        assert "\0" not in result
        assert result == "file.txt"

    def test_remove_leading_dots(self):
        """Test that leading dots are removed."""
        filename = "...hidden"
        result = sanitize_filename(filename)
        assert not result.startswith(".")

    def test_length_limit(self):
        """Test that filenames are truncated to 255 characters."""
        filename = "a" * 300 + ".txt"
        result = sanitize_filename(filename)
        assert len(result) <= 255
        assert result.endswith(".txt")

    def test_empty_filename_becomes_unnamed(self):
        """Test that empty filenames become 'unnamed'."""
        filename = "../../"
        result = sanitize_filename(filename)
        assert result == "unnamed"


class TestValidateURL:
    """Tests for URL validation."""

    def test_valid_http_url(self):
        """Test that valid HTTP URLs are accepted."""
        url = "http://example.com/path"
        assert validate_url(url) is True

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are accepted."""
        url = "https://example.com/path"
        assert validate_url(url) is True

    def test_invalid_scheme(self):
        """Test that invalid schemes are rejected."""
        url = "javascript:alert(1)"
        assert validate_url(url) is False

    def test_file_scheme_rejected(self):
        """Test that file:// URLs are rejected by default."""
        url = "file:///etc/passwd"
        assert validate_url(url) is False

    def test_custom_allowed_schemes(self):
        """Test that custom allowed schemes work."""
        url = "ftp://example.com/file"
        assert validate_url(url, allowed_schemes=["ftp"]) is True

    def test_malformed_url(self):
        """Test that malformed URLs are rejected."""
        url = "not a url"
        assert validate_url(url) is False


class TestSanitizeDiscordID:
    """Tests for Discord ID sanitization."""

    def test_valid_discord_id_string(self):
        """Test that valid Discord ID strings are converted to int."""
        discord_id = "123456789012345678"
        result = sanitize_discord_id(discord_id)
        assert result == 123456789012345678
        assert isinstance(result, int)

    def test_valid_discord_id_int(self):
        """Test that valid Discord ID ints are returned."""
        discord_id = 123456789012345678
        result = sanitize_discord_id(discord_id)
        assert result == 123456789012345678

    def test_negative_id_rejected(self):
        """Test that negative IDs are rejected."""
        discord_id = "-123"
        result = sanitize_discord_id(discord_id)
        assert result is None

    def test_zero_rejected(self):
        """Test that zero is rejected."""
        discord_id = "0"
        result = sanitize_discord_id(discord_id)
        assert result is None

    def test_invalid_string_rejected(self):
        """Test that non-numeric strings are rejected."""
        discord_id = "not a number"
        result = sanitize_discord_id(discord_id)
        assert result is None


class TestSanitizeUsername:
    """Tests for username sanitization."""

    def test_remove_control_characters(self):
        """Test that control characters are removed."""
        username = "test\x00\x01\x1fuser"
        result = sanitize_username(username)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x1f" not in result

    def test_normalize_whitespace(self):
        """Test that whitespace is normalized."""
        username = "test   user  name"
        result = sanitize_username(username)
        assert result == "test user name"

    def test_truncate_long_username(self):
        """Test that long usernames are truncated."""
        username = "a" * 100
        result = sanitize_username(username, max_length=32)
        assert len(result) == 32

    def test_strip_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        username = "  testuser  "
        result = sanitize_username(username)
        assert result == "testuser"


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test that valid emails are accepted."""
        email = "user@example.com"
        assert validate_email(email) is True

    def test_email_with_plus(self):
        """Test that emails with + are accepted."""
        email = "user+tag@example.com"
        assert validate_email(email) is True

    def test_email_with_dots(self):
        """Test that emails with dots are accepted."""
        email = "first.last@example.com"
        assert validate_email(email) is True

    def test_email_with_subdomain(self):
        """Test that emails with subdomains are accepted."""
        email = "user@mail.example.com"
        assert validate_email(email) is True

    def test_invalid_email_no_at(self):
        """Test that emails without @ are rejected."""
        email = "userexample.com"
        assert validate_email(email) is False

    def test_invalid_email_no_domain(self):
        """Test that emails without domain are rejected."""
        email = "user@"
        assert validate_email(email) is False

    def test_invalid_email_spaces(self):
        """Test that emails with spaces are rejected."""
        email = "user @example.com"
        assert validate_email(email) is False


class TestSanitizeInteger:
    """Tests for integer sanitization."""

    def test_valid_integer_string(self):
        """Test that valid integer strings are converted."""
        value = "123"
        result = sanitize_integer(value)
        assert result == 123
        assert isinstance(result, int)

    def test_valid_integer_int(self):
        """Test that valid integers are returned."""
        value = 123
        result = sanitize_integer(value)
        assert result == 123

    def test_min_value_enforced(self):
        """Test that minimum value is enforced."""
        value = "5"
        result = sanitize_integer(value, min_val=10)
        assert result is None

    def test_max_value_enforced(self):
        """Test that maximum value is enforced."""
        value = "100"
        result = sanitize_integer(value, max_val=50)
        assert result is None

    def test_value_in_range(self):
        """Test that values in range are accepted."""
        value = "25"
        result = sanitize_integer(value, min_val=10, max_val=50)
        assert result == 25

    def test_invalid_string_rejected(self):
        """Test that non-numeric strings are rejected."""
        value = "not a number"
        result = sanitize_integer(value)
        assert result is None

    def test_float_string_rejected(self):
        """Test that float strings are rejected."""
        value = "12.34"
        result = sanitize_integer(value)
        assert result is None
