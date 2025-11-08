"""Tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from main import app
from api.schemas.common import ServiceStatus


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings with a test health check secret."""
    with patch('api.routes.health.settings') as mock:
        mock.HEALTH_CHECK_SECRET = "test-secret-123"
        yield mock


@pytest.mark.asyncio
async def test_health_endpoint_with_valid_secret(db, mock_settings):
    """Test health endpoint returns ok with valid secret."""
    with patch('api.routes.health.check_database_health', new_callable=AsyncMock) as mock_db_check:
        mock_db_check.return_value = ServiceStatus(status="ok", message="Database connection healthy")

        client = TestClient(app)
        response = client.get("/api/health?secret=test-secret-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert "services" in data
        assert "database" in data["services"]
        assert data["services"]["database"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_endpoint_with_invalid_secret(db, mock_settings):
    """Test health endpoint returns 401 with invalid secret."""
    client = TestClient(app)
    response = client.get("/api/health?secret=wrong-secret")

    assert response.status_code == 401
    data = response.json()
    assert "Invalid health check secret" in data["detail"]


@pytest.mark.asyncio
async def test_health_endpoint_without_secret(db, mock_settings):
    """Test health endpoint returns 422 without secret parameter."""
    client = TestClient(app)
    response = client.get("/api/health")

    # FastAPI returns 422 for missing required query parameters
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint_with_database_error(db, mock_settings):
    """Test health endpoint returns degraded status when database fails."""
    with patch('api.routes.health.check_database_health', new_callable=AsyncMock) as mock_db_check:
        mock_db_check.return_value = ServiceStatus(
            status="error",
            message="Database connection failed: Connection refused"
        )

        client = TestClient(app)
        response = client.get("/api/health?secret=test-secret-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["database"]["status"] == "error"
        assert "Connection refused" in data["services"]["database"]["message"]


@pytest.mark.asyncio
async def test_check_database_health_success(db):
    """Test database health check succeeds with valid connection."""
    from api.routes.health import check_database_health

    result = await check_database_health()

    assert result.status == "ok"
    assert "healthy" in result.message.lower()


@pytest.mark.asyncio
async def test_check_database_health_failure():
    """Test database health check fails with invalid connection."""
    from api.routes.health import check_database_health

    with patch('api.routes.health.Tortoise.get_connection') as mock_conn:
        mock_conn.return_value.execute_query = AsyncMock(side_effect=Exception("Connection failed"))

        result = await check_database_health()

        assert result.status == "error"
        assert "failed" in result.message.lower()
