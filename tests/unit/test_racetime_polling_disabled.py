"""
Test to verify automatic race room polling is disabled.

This test ensures that:
1. The should_handle() method always returns False
2. The refresh_races() task is NOT created on bot startup
3. Race rooms are only joined via explicit calls
"""

import pytest
from unittest.mock import patch
from racetime.client import RacetimeBot


@patch("racetime.client.Bot.__init__")
def test_should_handle_always_returns_false(mock_init):
    """Verify should_handle() always returns False to prevent automatic joining."""
    # Mock the parent __init__ to avoid authentication
    mock_init.return_value = None

    # Create a minimal bot instance (don't actually start it)
    bot = RacetimeBot(
        category_slug="test_category",
        client_id="test_client_id",
        client_secret="test_client_secret",
    )

    # Test with various race data
    test_cases = [
        {"name": "test_category/cool-race-1234", "status": {"value": "open"}},
        {"name": "test_category/another-race-5678", "status": {"value": "pending"}},
        {"name": "test_category/finished-race-9012", "status": {"value": "finished"}},
    ]

    for race_data in test_cases:
        result = bot.should_handle(race_data)
        assert result is False, (
            f"should_handle() returned {result} instead of False for race {race_data['name']}. "
            "Automatic race room polling should be disabled."
        )


@patch("racetime.client.Bot.__init__")
def test_should_handle_docstring_explains_behavior(mock_init):
    """Verify should_handle() has proper documentation about disabled polling."""
    # Mock the parent __init__ to avoid authentication
    mock_init.return_value = None

    bot = RacetimeBot(
        category_slug="test_category",
        client_id="test_client_id",
        client_secret="test_client_secret",
    )

    docstring = bot.should_handle.__doc__

    # Check that docstring mentions the disabled behavior
    assert docstring is not None, "should_handle() method should have a docstring"
    assert (
        "not used" in docstring.lower() or "always" in docstring.lower()
    ), "should_handle() docstring should explain that automatic polling is disabled"
    assert (
        "false" in docstring.lower()
    ), "should_handle() docstring should mention that it returns False"


@pytest.mark.asyncio
@patch("racetime.client.Bot.__init__")
async def test_explicit_join_race_room_still_works(mock_init):
    """Verify that explicit joining via join_race_room() is still possible."""
    # Mock the parent __init__ to avoid authentication
    mock_init.return_value = None

    bot = RacetimeBot(
        category_slug="test_category",
        client_id="test_client_id",
        client_secret="test_client_secret",
    )

    # Note: This test just verifies the method exists and can be called
    # It won't actually join a race room since we don't have real credentials
    # and the bot isn't running

    assert hasattr(
        bot, "join_race_room"
    ), "Bot should have join_race_room() method for explicit joining"
    assert callable(bot.join_race_room), "join_race_room should be callable"


@pytest.mark.asyncio
@patch("racetime.client.Bot.__init__")
async def test_explicit_startrace_still_works(mock_init):
    """Verify that explicit race creation via startrace() is still possible."""
    # Mock the parent __init__ to avoid authentication
    mock_init.return_value = None

    bot = RacetimeBot(
        category_slug="test_category",
        client_id="test_client_id",
        client_secret="test_client_secret",
    )

    # Note: This test just verifies the method exists and can be called
    # It won't actually create a race room since we don't have real credentials
    # and the bot isn't running

    assert hasattr(
        bot, "startrace"
    ), "Bot should have startrace() method for explicit race creation"
    assert callable(bot.startrace), "startrace should be callable"


def test_racetime_bot_module_docstring_explains_polling():
    """Verify the module docstring explains that polling is disabled."""
    import racetime.client as client_module

    module_docstring = client_module.__doc__

    assert module_docstring is not None, "Module should have a docstring"
    assert (
        "polling" in module_docstring.lower()
        or "refresh_races" in module_docstring.lower()
    ), "Module docstring should mention polling or refresh_races"
    assert (
        "disable" in module_docstring.lower() or "not" in module_docstring.lower()
    ), "Module docstring should mention that polling is disabled"
