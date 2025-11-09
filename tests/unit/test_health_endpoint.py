"""Tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from main import app
from api.schemas.common import ServiceStatus
from api.routes.health import (
    check_database_health,
    check_discord_health,
    check_racetime_health,
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings with a test health check secret."""
    with patch("api.routes.health.settings") as mock:
        mock.HEALTH_CHECK_SECRET = "test-secret-123"
        yield mock


@pytest.mark.asyncio
async def test_health_endpoint_with_valid_secret(db, mock_settings, client):
    """Test health endpoint returns ok with valid secret."""
    with patch(
        "api.routes.health.check_database_health", new_callable=AsyncMock
    ) as mock_db_check, patch(
        "api.routes.health.check_discord_health", new_callable=AsyncMock
    ) as mock_discord_check, patch(
        "api.routes.health.check_racetime_health", new_callable=AsyncMock
    ) as mock_racetime_check:
        mock_db_check.return_value = ServiceStatus(
            status="ok", message="Database connection healthy"
        )
        mock_discord_check.return_value = ServiceStatus(
            status="ok", message="Discord bot connected and ready"
        )
        mock_racetime_check.return_value = ServiceStatus(
            status="ok", message="2 RaceTime bot(s) running"
        )

        response = client.get("/api/health?secret=test-secret-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert "services" in data
        assert "database" in data["services"]
        assert data["services"]["database"]["status"] == "ok"
        assert "discord" in data["services"]
        assert data["services"]["discord"]["status"] == "ok"
        assert "racetime" in data["services"]
        assert data["services"]["racetime"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_endpoint_with_invalid_secret(db, mock_settings, client):
    """Test health endpoint returns 401 with invalid secret."""
    response = client.get("/api/health?secret=wrong-secret")

    assert response.status_code == 401
    data = response.json()
    assert "Invalid health check secret" in data["detail"]


@pytest.mark.asyncio
async def test_health_endpoint_without_secret(db, mock_settings, client):
    """Test health endpoint returns 422 without secret parameter."""
    response = client.get("/api/health")

    # FastAPI returns 422 for missing required query parameters
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint_with_database_error(db, mock_settings, client):
    """Test health endpoint returns degraded status when database fails."""
    with patch(
        "api.routes.health.check_database_health", new_callable=AsyncMock
    ) as mock_db_check, patch(
        "api.routes.health.check_discord_health", new_callable=AsyncMock
    ) as mock_discord_check, patch(
        "api.routes.health.check_racetime_health", new_callable=AsyncMock
    ) as mock_racetime_check:
        mock_db_check.return_value = ServiceStatus(
            status="error", message="Database connection failed: Connection refused"
        )
        mock_discord_check.return_value = ServiceStatus(
            status="ok", message="Discord bot connected and ready"
        )
        mock_racetime_check.return_value = ServiceStatus(
            status="ok", message="2 RaceTime bot(s) running"
        )

        response = client.get("/api/health?secret=test-secret-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["database"]["status"] == "error"
        assert "Connection refused" in data["services"]["database"]["message"]


@pytest.mark.asyncio
async def test_check_database_health_success(db):
    """Test database health check succeeds with valid connection."""
    result = await check_database_health()

    assert result.status == "ok"
    assert "healthy" in result.message.lower()


@pytest.mark.asyncio
async def test_check_database_health_failure():
    """Test database health check fails with invalid connection."""
    with patch("api.routes.health.Tortoise.get_connection") as mock_conn:
        mock_conn.return_value.execute_query = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        result = await check_database_health()

        assert result.status == "error"
        assert "failed" in result.message.lower()


@pytest.mark.asyncio
async def test_check_discord_health_bot_ready():
    """Test Discord health check when bot is ready."""
    with patch("api.routes.health.get_bot_instance") as mock_get_bot:
        mock_bot = MagicMock()
        mock_bot.is_ready.return_value = True
        mock_get_bot.return_value = mock_bot

        result = await check_discord_health()

        assert result.status == "ok"
        assert "ready" in result.message.lower()


@pytest.mark.asyncio
async def test_check_discord_health_bot_not_ready():
    """Test Discord health check when bot is not ready."""
    with patch("api.routes.health.get_bot_instance") as mock_get_bot:
        mock_bot = MagicMock()
        mock_bot.is_ready.return_value = False
        mock_get_bot.return_value = mock_bot

        result = await check_discord_health()

        assert result.status == "error"
        assert "not ready" in result.message.lower()


@pytest.mark.asyncio
async def test_check_discord_health_bot_not_started():
    """Test Discord health check when bot is not started."""
    with patch("api.routes.health.get_bot_instance") as mock_get_bot:
        mock_get_bot.return_value = None

        result = await check_discord_health()

        assert result.status == "error"
        assert "not started" in result.message.lower()


@pytest.mark.asyncio
async def test_check_racetime_health_bots_running():
    """Test RaceTime health check when bots are running."""
    with patch("api.routes.health.get_all_racetime_bot_instances") as mock_get_bots:
        mock_get_bots.return_value = {"alttpr": MagicMock(), "smz3": MagicMock()}

        result = await check_racetime_health()

        assert result.status == "ok"
        assert "2 RaceTime bot(s)" in result.message
        assert "alttpr" in result.message
        assert "smz3" in result.message


@pytest.mark.asyncio
async def test_check_racetime_health_no_bots():
    """Test RaceTime health check when no bots are running."""
    with patch("api.routes.health.get_all_racetime_bot_instances") as mock_get_bots:
        mock_get_bots.return_value = {}

        result = await check_racetime_health()

        assert result.status == "error"
        assert "no" in result.message.lower()


@pytest.mark.asyncio
async def test_health_endpoint_with_discord_error(db, mock_settings, client):
    """Test health endpoint returns degraded status when Discord fails."""
    with patch(
        "api.routes.health.check_database_health", new_callable=AsyncMock
    ) as mock_db_check, patch(
        "api.routes.health.check_discord_health", new_callable=AsyncMock
    ) as mock_discord_check, patch(
        "api.routes.health.check_racetime_health", new_callable=AsyncMock
    ) as mock_racetime_check:
        mock_db_check.return_value = ServiceStatus(
            status="ok", message="Database connection healthy"
        )
        mock_discord_check.return_value = ServiceStatus(
            status="error", message="Discord bot not ready"
        )
        mock_racetime_check.return_value = ServiceStatus(
            status="ok", message="2 RaceTime bot(s) running"
        )

        response = client.get("/api/health?secret=test-secret-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["discord"]["status"] == "error"


@pytest.mark.asyncio
async def test_health_endpoint_with_racetime_error(db, mock_settings, client):
    """Test health endpoint returns degraded status when RaceTime fails."""
    with patch(
        "api.routes.health.check_database_health", new_callable=AsyncMock
    ) as mock_db_check, patch(
        "api.routes.health.check_discord_health", new_callable=AsyncMock
    ) as mock_discord_check, patch(
        "api.routes.health.check_racetime_health", new_callable=AsyncMock
    ) as mock_racetime_check:
        mock_db_check.return_value = ServiceStatus(
            status="ok", message="Database connection healthy"
        )
        mock_discord_check.return_value = ServiceStatus(
            status="ok", message="Discord bot connected and ready"
        )
        mock_racetime_check.return_value = ServiceStatus(
            status="error", message="No RaceTime bots running"
        )

        response = client.get("/api/health?secret=test-secret-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["racetime"]["status"] == "error"
