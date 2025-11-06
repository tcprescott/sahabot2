"""Tests for security middleware."""

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from middleware.security import SecurityHeadersMiddleware, HTTPSRedirectMiddleware
from config import settings


@pytest.fixture
def app_with_security():
    """Create a test app with security middleware."""
    app = FastAPI()

    # Add security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(HTTPSRedirectMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    return app


def test_security_headers_added(app_with_security):
    """Test that security headers are added to responses."""
    client = TestClient(app_with_security)
    response = client.get("/test")

    # Check that security headers are present
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

    assert "X-XSS-Protection" in response.headers
    assert response.headers["X-XSS-Protection"] == "1; mode=block"

    assert "Referrer-Policy" in response.headers
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    assert "Permissions-Policy" in response.headers
    assert "Content-Security-Policy" in response.headers


def test_hsts_header_in_production(app_with_security):
    """Test that HSTS header is added in production."""
    client = TestClient(app_with_security)

    with patch.object(settings, 'ENVIRONMENT', 'production'):
        response = client.get("/test")
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
        assert "includeSubDomains" in response.headers["Strict-Transport-Security"]


def test_hsts_header_not_in_development(app_with_security):
    """Test that HSTS header is not added in development."""
    client = TestClient(app_with_security)

    with patch.object(settings, 'ENVIRONMENT', 'development'):
        response = client.get("/test")
        assert "Strict-Transport-Security" not in response.headers


def test_https_redirect_in_production():
    """Test that HTTP is redirected to HTTPS in production."""
    app = FastAPI()
    app.add_middleware(HTTPSRedirectMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app, base_url="http://example.com")

    with patch.object(settings, 'ENVIRONMENT', 'production'):
        response = client.get("/test", follow_redirects=False)

        # Should get a redirect
        assert response.status_code == 301
        assert response.headers["Location"].startswith("https://")


def test_https_not_redirected_in_development():
    """Test that HTTP is not redirected in development."""
    app = FastAPI()
    app.add_middleware(HTTPSRedirectMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app, base_url="http://example.com")

    with patch.object(settings, 'ENVIRONMENT', 'development'):
        response = client.get("/test")

        # Should get successful response
        assert response.status_code == 200
        assert response.json() == {"message": "test"}


def test_https_redirect_respects_forwarded_proto():
    """Test that HTTPS redirect respects X-Forwarded-Proto header."""
    app = FastAPI()
    app.add_middleware(HTTPSRedirectMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app, base_url="http://example.com")

    with patch.object(settings, 'ENVIRONMENT', 'production'):
        # Request with X-Forwarded-Proto: https should not redirect
        response = client.get(
            "/test",
            headers={"X-Forwarded-Proto": "https"}
        )

        # Should get successful response (no redirect)
        assert response.status_code == 200
        assert response.json() == {"message": "test"}


def test_csp_header_content():
    """Test that CSP header contains expected directives."""
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.get("/test")

    csp = response.headers.get("Content-Security-Policy", "")

    # Check for key directives
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "script-src" in csp
    assert "style-src" in csp
