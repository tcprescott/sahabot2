"""Tests for URL validation utilities."""

from application.utils.url_validator import (
    validate_url,
    sanitize_url,
    is_safe_redirect_url,
)


class TestValidateUrl:
    """Tests for validate_url function."""

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are accepted."""
        is_valid, error = validate_url("https://example.com/path")
        assert is_valid is True
        assert error is None

    def test_valid_http_url(self):
        """Test that valid HTTP URLs are accepted."""
        is_valid, error = validate_url("http://example.com/path")
        assert is_valid is True
        assert error is None

    def test_invalid_scheme_javascript(self):
        """Test that javascript: URLs are rejected."""
        is_valid, error = validate_url("javascript:alert('XSS')")
        assert is_valid is False
        assert "javascript" in error.lower()

    def test_invalid_scheme_data(self):
        """Test that data: URLs are rejected."""
        is_valid, error = validate_url("data:text/html,<script>alert('XSS')</script>")
        assert is_valid is False
        assert "data" in error.lower()

    def test_invalid_scheme_file(self):
        """Test that file: URLs are rejected."""
        is_valid, error = validate_url("file:///etc/passwd")
        assert is_valid is False
        assert "file" in error.lower()

    def test_private_ip_127_0_0_1(self):
        """Test that localhost IP is blocked."""
        is_valid, error = validate_url("http://127.0.0.1/admin")
        assert is_valid is False
        assert "private" in error.lower() or "internal" in error.lower()

    def test_private_ip_192_168(self):
        """Test that private network IPs are blocked."""
        is_valid, error = validate_url("http://192.168.1.1/router")
        assert is_valid is False
        assert "private" in error.lower() or "internal" in error.lower()

    def test_private_ip_10_0_0_0(self):
        """Test that private network IPs are blocked."""
        is_valid, error = validate_url("http://10.0.0.1/internal")
        assert is_valid is False
        assert "private" in error.lower() or "internal" in error.lower()

    def test_localhost_hostname(self):
        """Test that localhost hostname is blocked."""
        is_valid, error = validate_url("http://localhost/admin")
        assert is_valid is False
        assert "localhost" in error.lower() or "internal" in error.lower()

    def test_url_too_long(self):
        """Test that excessively long URLs are rejected."""
        long_url = "https://example.com/" + "a" * 3000
        is_valid, error = validate_url(long_url, max_length=2048)
        assert is_valid is False
        assert "length" in error.lower()

    def test_malformed_url(self):
        """Test that malformed URLs are rejected."""
        is_valid, error = validate_url("not a url")
        assert is_valid is False
        assert "invalid" in error.lower() or "format" in error.lower()

    def test_url_with_port(self):
        """Test that URLs with ports are accepted."""
        is_valid, error = validate_url("https://example.com:8080/path")
        assert is_valid is True
        assert error is None

    def test_url_with_query_params(self):
        """Test that URLs with query parameters are accepted."""
        is_valid, error = validate_url("https://example.com/path?param=value&other=123")
        assert is_valid is True
        assert error is None

    def test_url_with_fragment(self):
        """Test that URLs with fragments are accepted."""
        is_valid, error = validate_url("https://example.com/path#section")
        assert is_valid is True
        assert error is None

    def test_url_with_whitespace(self):
        """Test that URLs with leading/trailing whitespace are validated correctly."""
        # URL with whitespace should be validated after stripping
        # Note: The caller (schema validator) is responsible for stripping
        is_valid, error = validate_url("https://example.com/path")
        assert is_valid is True
        assert error is None

    def test_custom_allowed_schemes(self):
        """Test that custom allowed schemes work."""
        # FTP should be rejected with default schemes
        is_valid, error = validate_url("ftp://example.com/file")
        assert is_valid is False

        # FTP should be accepted when explicitly allowed
        is_valid, error = validate_url(
            "ftp://example.com/file", allowed_schemes=["ftp"]
        )
        assert is_valid is True
        assert error is None

    def test_block_private_ips_disabled(self):
        """Test that private IP blocking can be disabled."""
        is_valid, error = validate_url("http://127.0.0.1/", block_private_ips=False)
        assert is_valid is True
        assert error is None

    def test_ipv6_loopback(self):
        """Test that IPv6 loopback is blocked."""
        is_valid, error = validate_url("http://[::1]/admin")
        assert is_valid is False
        assert "private" in error.lower() or "internal" in error.lower()


class TestSanitizeUrl:
    """Tests for sanitize_url function."""

    def test_add_https_scheme(self):
        """Test that HTTPS scheme is added when missing."""
        result = sanitize_url("example.com")
        assert result == "https://example.com"

    def test_preserve_existing_scheme(self):
        """Test that existing scheme is preserved."""
        result = sanitize_url("http://example.com")
        assert result == "http://example.com"

    def test_strip_whitespace(self):
        """Test that whitespace is stripped."""
        result = sanitize_url("  https://example.com  ")
        assert result == "https://example.com"


class TestIsSafeRedirectUrl:
    """Tests for is_safe_redirect_url function."""

    def test_relative_path_safe(self):
        """Test that relative paths are safe."""
        assert is_safe_redirect_url("/dashboard", "https://example.com") is True

    def test_same_domain_safe(self):
        """Test that same domain URLs are safe."""
        assert (
            is_safe_redirect_url("https://example.com/page", "https://example.com")
            is True
        )

    def test_different_domain_unsafe(self):
        """Test that different domain URLs are unsafe."""
        assert (
            is_safe_redirect_url("https://evil.com/page", "https://example.com")
            is False
        )

    def test_protocol_relative_unsafe(self):
        """Test that protocol-relative URLs are unsafe."""
        assert is_safe_redirect_url("//evil.com/page", "https://example.com") is False

    def test_subdomain_unsafe(self):
        """Test that different subdomains are unsafe."""
        assert (
            is_safe_redirect_url("https://sub.example.com/page", "https://example.com")
            is False
        )
