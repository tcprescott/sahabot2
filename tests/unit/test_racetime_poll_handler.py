"""
Tests for RaceTime race room polling task handler.

This test verifies that the handler correctly polls for open race rooms
and joins them based on configuration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from application.services.tasks.task_handlers import (
    handle_racetime_poll_open_rooms,
    register_task_handlers,
)
from models.scheduled_task import TaskType, ScheduleType


@pytest.fixture(autouse=True)
def ensure_handlers_registered():
    """Ensure task handlers are registered before each test."""
    register_task_handlers()
    yield


@pytest.mark.asyncio
@patch("application.services.tasks.task_handlers.get_all_racetime_bot_instances")
async def test_handle_racetime_poll_no_bots(mock_get_bots):
    """Test handler when no bots are running."""
    # Mock: No bots running
    mock_get_bots.return_value = {}

    # Create a pseudo-task
    task = MagicMock()
    task.id = "builtin:racetime_poll_open_rooms"
    task.name = "RaceTime - Poll Open Race Rooms"
    task.task_config = {"enabled_statuses": ["open", "invitational"]}

    # Execute handler - should not raise an error
    await handle_racetime_poll_open_rooms(task)


@pytest.mark.asyncio
@patch("application.services.tasks.task_handlers.get_all_racetime_bot_instances")
async def test_handle_racetime_poll_with_bots_no_races(mock_get_bots):
    """Test handler when bots are running but no races found."""
    # Create mock bot
    mock_bot = MagicMock()
    mock_bot.category_slug = "test_category"
    mock_bot.http_uri = MagicMock(
        return_value="http://localhost/test_category/races/data"
    )
    mock_bot.ssl_context = None
    mock_bot.handlers = {}

    # Mock HTTP response
    mock_http = AsyncMock()
    mock_bot.http = mock_http
    mock_bot.http.closed = False

    # Mock the response context manager
    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={"races": []})
    mock_http.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    # Mock: One bot running
    mock_get_bots.return_value = {"test_category": mock_bot}

    # Create a pseudo-task
    task = MagicMock()
    task.id = "builtin:racetime_poll_open_rooms"
    task.name = "RaceTime - Poll Open Race Rooms"
    task.task_config = {"enabled_statuses": ["open", "invitational"]}

    # Execute handler
    await handle_racetime_poll_open_rooms(task)

    # Verify HTTP request was made
    mock_http.get.assert_called_once()


@pytest.mark.asyncio
@patch("application.services.tasks.task_handlers.get_all_racetime_bot_instances")
async def test_handle_racetime_poll_joins_open_race(mock_get_bots):
    """Test handler joins an open race room."""
    # Create mock bot
    mock_bot = MagicMock()
    mock_bot.category_slug = "test_category"
    mock_bot.http_uri = MagicMock(
        return_value="http://localhost/test_category/races/data"
    )
    mock_bot.ssl_context = None
    mock_bot.handlers = {}
    mock_bot.should_handle = MagicMock(
        return_value=False
    )  # Always False (disabled polling)

    # Mock join_race_room to return a handler
    mock_handler = MagicMock()
    mock_bot.join_race_room = AsyncMock(return_value=mock_handler)

    # Mock HTTP response with one open race
    mock_http = AsyncMock()
    mock_bot.http = mock_http
    mock_bot.http.closed = False

    race_data = {
        "name": "test_category/cool-race-1234",
        "status": {"value": "open"},
        "goal": {"name": "Beat the game"},
    }

    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={"races": [race_data]})
    mock_http.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    # Mock: One bot running
    mock_get_bots.return_value = {"test_category": mock_bot}

    # Create a pseudo-task
    task = MagicMock()
    task.id = "builtin:racetime_poll_open_rooms"
    task.name = "RaceTime - Poll Open Race Rooms"
    task.task_config = {"enabled_statuses": ["open", "invitational"]}

    # Execute handler
    await handle_racetime_poll_open_rooms(task)

    # Verify join_race_room was called
    mock_bot.join_race_room.assert_called_once_with(
        "test_category/cool-race-1234", force=True
    )


@pytest.mark.asyncio
@patch("application.services.tasks.task_handlers.get_all_racetime_bot_instances")
async def test_handle_racetime_poll_skips_closed_race(mock_get_bots):
    """Test handler skips races not in enabled_statuses."""
    # Create mock bot
    mock_bot = MagicMock()
    mock_bot.category_slug = "test_category"
    mock_bot.http_uri = MagicMock(
        return_value="http://localhost/test_category/races/data"
    )
    mock_bot.ssl_context = None
    mock_bot.handlers = {}

    # Mock join_race_room (should not be called)
    mock_bot.join_race_room = AsyncMock()

    # Mock HTTP response with one finished race
    mock_http = AsyncMock()
    mock_bot.http = mock_http
    mock_bot.http.closed = False

    race_data = {
        "name": "test_category/finished-race-5678",
        "status": {"value": "finished"},  # Not in enabled_statuses
        "goal": {"name": "Beat the game"},
    }

    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={"races": [race_data]})
    mock_http.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    # Mock: One bot running
    mock_get_bots.return_value = {"test_category": mock_bot}

    # Create a pseudo-task
    task = MagicMock()
    task.id = "builtin:racetime_poll_open_rooms"
    task.name = "RaceTime - Poll Open Race Rooms"
    task.task_config = {"enabled_statuses": ["open", "invitational"]}

    # Execute handler
    await handle_racetime_poll_open_rooms(task)

    # Verify join_race_room was NOT called
    mock_bot.join_race_room.assert_not_called()


@pytest.mark.asyncio
@patch("application.services.tasks.task_handlers.get_all_racetime_bot_instances")
async def test_handle_racetime_poll_skips_already_handled(mock_get_bots):
    """Test handler skips races we're already handling."""
    # Create mock bot
    mock_bot = MagicMock()
    mock_bot.category_slug = "test_category"
    mock_bot.http_uri = MagicMock(
        return_value="http://localhost/test_category/races/data"
    )
    mock_bot.ssl_context = None
    mock_bot.handlers = {
        "test_category/cool-race-1234": MagicMock()
    }  # Already handling

    # Mock join_race_room (should not be called)
    mock_bot.join_race_room = AsyncMock()

    # Mock HTTP response with one open race we're already handling
    mock_http = AsyncMock()
    mock_bot.http = mock_http
    mock_bot.http.closed = False

    race_data = {
        "name": "test_category/cool-race-1234",
        "status": {"value": "open"},
        "goal": {"name": "Beat the game"},
    }

    mock_response = AsyncMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={"races": [race_data]})
    mock_http.get = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response))
    )

    # Mock: One bot running
    mock_get_bots.return_value = {"test_category": mock_bot}

    # Create a pseudo-task
    task = MagicMock()
    task.id = "builtin:racetime_poll_open_rooms"
    task.name = "RaceTime - Poll Open Race Rooms"
    task.task_config = {"enabled_statuses": ["open", "invitational"]}

    # Execute handler
    await handle_racetime_poll_open_rooms(task)

    # Verify join_race_room was NOT called (already handling)
    mock_bot.join_race_room.assert_not_called()


def test_builtin_task_exists():
    """Test that the builtin task is properly configured."""
    from application.services.tasks.builtin_tasks import get_builtin_task

    task = get_builtin_task("racetime_poll_open_rooms")

    assert task is not None, "Builtin task 'racetime_poll_open_rooms' should exist"
    assert task.name == "RaceTime - Poll Open Race Rooms"
    assert task.task_type == TaskType.RACETIME_POLL_OPEN_ROOMS
    assert task.schedule_type == ScheduleType.INTERVAL
    assert task.is_global is True
    assert task.is_active is True
    assert task.interval_seconds == 60  # Every minute


def test_task_handler_registered():
    """Test that the handler is registered with the scheduler."""
    from application.services.tasks.task_scheduler_service import TaskSchedulerService

    # The handler should be registered in the _task_handlers dict
    assert (
        TaskType.RACETIME_POLL_OPEN_ROOMS in TaskSchedulerService._task_handlers
    ), "Handler for RACETIME_POLL_OPEN_ROOMS should be registered"
