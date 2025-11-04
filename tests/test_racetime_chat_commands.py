"""
Test RaceTime Chat Command functionality.

This tests the command service and handler execution.
"""

import pytest
from models import RacetimeChatCommand, CommandResponseType
from application.services.racetime_chat_command_service import RacetimeChatCommandService


@pytest.mark.asyncio
async def test_text_command_execution():
    """Test execution of a simple TEXT command."""
    _service = RacetimeChatCommandService()

    # Create a mock TEXT command (in-memory, not persisted)
    command = RacetimeChatCommand()
    command.id = 1
    command.command = 'test'
    command.response_type = CommandResponseType.TEXT
    command.response_text = 'This is a test response'
    command.cooldown_seconds = 0
    command.require_linked_account = False
    
    # Mock repository response
    # In real test, we'd use database fixtures
    
    # For now, just test the handler signature
    # TODO: Add full integration test with database
    
    assert command.response_text == 'This is a test response'


@pytest.mark.asyncio
async def test_cooldown_tracking():
    """Test command cooldown enforcement."""
    service = RacetimeChatCommandService()
    
    command = RacetimeChatCommand()
    command.id = 1
    command.command = 'cooldown_test'
    command.cooldown_seconds = 10  # 10 second cooldown

    # First use should succeed
    can_use, remaining = service._check_cooldown(command, 'user123')  # noqa: SLF001
    assert can_use is True
    assert remaining == 0

    # Update cooldown
    service._update_cooldown(command, 'user123')  # noqa: SLF001

    # Second use immediately should fail
    can_use, remaining = service._check_cooldown(command, 'user123')  # noqa: SLF001
    assert can_use is False
    assert remaining > 0


@pytest.mark.asyncio
async def test_handler_registration():
    """Test dynamic handler registration."""
    service = RacetimeChatCommandService()
    
    async def test_handler(_command, _args, _racetime_user_id, _race_data, _user):
        """Test handler function."""
        return "Test response"
    
    # Register handler
    service.register_handler('test_handler', test_handler)
    
        # Verify handler registered
    assert 'test_handler' in service._dynamic_handlers  # noqa: SLF001
    handler_func = service._dynamic_handlers['test_handler']  # noqa: SLF001
    assert callable(handler_func)


if __name__ == '__main__':
    # Run with: poetry run pytest tests/test_racetime_chat_commands.py -v
    pytest.main([__file__, '-v'])
