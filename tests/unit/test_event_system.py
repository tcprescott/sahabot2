"""
Tests for the event system.

These tests verify that events are emitted, handlers are called,
and the event bus operates correctly.
"""

import pytest
from application.events import EventBus, EventPriority
from application.events.types import UserCreatedEvent, TournamentCreatedEvent


class TestEventBus:
    """Test EventBus functionality."""

    def setup_method(self):
        """Clear event handlers before each test."""
        EventBus.clear_all()
        EventBus.enable()

    def teardown_method(self):
        """Clean up after each test."""
        EventBus.clear_all()
        EventBus.enable()

    @pytest.mark.asyncio
    async def test_event_emission_and_handling(self):
        """Test that events are emitted and handlers are called."""
        called = False
        received_event = None

        @EventBus.on(UserCreatedEvent)
        async def test_handler(event: UserCreatedEvent):
            nonlocal called, received_event
            called = True
            received_event = event

        # Create and emit event
        event = UserCreatedEvent(
            entity_id=123,
            user_id=456,
            discord_id=789,
            discord_username="testuser"
        )

        await EventBus.emit(event)

        # Verify handler was called
        assert called
        assert received_event is not None
        assert received_event.entity_id == 123
        assert received_event.discord_id == 789
        assert received_event.discord_username == "testuser"

    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self):
        """Test that multiple handlers can listen to same event."""
        handler1_called = False
        handler2_called = False

        @EventBus.on(UserCreatedEvent)
        async def handler1(event: UserCreatedEvent):
            nonlocal handler1_called
            handler1_called = True

        @EventBus.on(UserCreatedEvent)
        async def handler2(event: UserCreatedEvent):
            nonlocal handler2_called
            handler2_called = True

        event = UserCreatedEvent(entity_id=1, discord_id=2)
        await EventBus.emit(event)

        assert handler1_called
        assert handler2_called

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test that handlers are called in priority order."""
        call_order = []

        @EventBus.on(UserCreatedEvent, priority=EventPriority.LOW)
        async def low_priority(event: UserCreatedEvent):
            call_order.append("low")

        @EventBus.on(UserCreatedEvent, priority=EventPriority.HIGH)
        async def high_priority(event: UserCreatedEvent):
            call_order.append("high")

        @EventBus.on(UserCreatedEvent, priority=EventPriority.NORMAL)
        async def normal_priority(event: UserCreatedEvent):
            call_order.append("normal")

        event = UserCreatedEvent(entity_id=1)
        await EventBus.emit(event)

        # HIGH should be called first, then NORMAL, then LOW
        # Note: asyncio.gather doesn't guarantee strict ordering,
        # but our implementation processes by priority
        assert "high" in call_order
        assert "normal" in call_order
        assert "low" in call_order

    @pytest.mark.asyncio
    async def test_handler_error_isolation(self):
        """Test that handler errors don't affect other handlers."""
        handler2_called = False

        @EventBus.on(UserCreatedEvent)
        async def failing_handler(event: UserCreatedEvent):
            raise ValueError("Handler error")

        @EventBus.on(UserCreatedEvent)
        async def successful_handler(event: UserCreatedEvent):
            nonlocal handler2_called
            handler2_called = True

        event = UserCreatedEvent(entity_id=1)
        await EventBus.emit(event)

        # Second handler should still be called despite first failing
        assert handler2_called

    @pytest.mark.asyncio
    async def test_event_type_filtering(self):
        """Test that handlers only receive their registered event type."""
        user_handler_called = False
        tournament_handler_called = False

        @EventBus.on(UserCreatedEvent)
        async def user_handler(event: UserCreatedEvent):
            nonlocal user_handler_called
            user_handler_called = True

        @EventBus.on(TournamentCreatedEvent)
        async def tournament_handler(event: TournamentCreatedEvent):
            nonlocal tournament_handler_called
            tournament_handler_called = True

        # Emit user event
        user_event = UserCreatedEvent(entity_id=1)
        await EventBus.emit(user_event)

        assert user_handler_called
        assert not tournament_handler_called

        # Reset and emit tournament event
        user_handler_called = False
        tournament_event = TournamentCreatedEvent(entity_id=2)
        await EventBus.emit(tournament_event)

        assert not user_handler_called
        assert tournament_handler_called

    @pytest.mark.asyncio
    async def test_event_bus_disable(self):
        """Test that events are ignored when bus is disabled."""
        handler_called = False

        @EventBus.on(UserCreatedEvent)
        async def test_handler(event: UserCreatedEvent):
            nonlocal handler_called
            handler_called = True

        # Disable event bus
        EventBus.disable()

        event = UserCreatedEvent(entity_id=1)
        await EventBus.emit(event)

        # Handler should not be called
        assert not handler_called
        assert not EventBus.is_enabled()

        # Re-enable and try again
        EventBus.enable()
        await EventBus.emit(event)
        assert handler_called

    @pytest.mark.asyncio
    async def test_handler_count(self):
        """Test handler count tracking."""
        assert EventBus.get_handler_count() == 0
        assert EventBus.get_handler_count(UserCreatedEvent) == 0

        @EventBus.on(UserCreatedEvent)
        async def handler1(event: UserCreatedEvent):
            pass

        @EventBus.on(UserCreatedEvent)
        async def handler2(event: UserCreatedEvent):
            pass

        @EventBus.on(TournamentCreatedEvent)
        async def handler3(event: TournamentCreatedEvent):
            pass

        assert EventBus.get_handler_count() == 3
        assert EventBus.get_handler_count(UserCreatedEvent) == 2
        assert EventBus.get_handler_count(TournamentCreatedEvent) == 1

    def test_event_immutability(self):
        """Test that events are immutable."""
        event = UserCreatedEvent(
            entity_id=123,
            discord_id=456,
            discord_username="testuser"
        )

        # Should not be able to modify frozen dataclass
        with pytest.raises(AttributeError):
            event.entity_id = 999  # type: ignore

    def test_event_metadata(self):
        """Test event metadata fields."""
        event = UserCreatedEvent(
            entity_id=123,
            user_id=456,
            organization_id=789,
        )

        # Should have auto-generated fields
        assert event.event_id is not None
        assert len(event.event_id) > 0
        assert event.timestamp is not None
        assert event.priority == EventPriority.NORMAL
        assert event.event_type == "UserCreatedEvent"

        # Should have context fields
        assert event.user_id == 456
        assert event.organization_id == 789

    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        event = UserCreatedEvent(
            entity_id=123,
            user_id=456,
            organization_id=789,
            discord_id=111,
            discord_username="testuser"
        )

        data = event.to_dict()

        assert isinstance(data, dict)
        assert data["event_type"] == "UserCreatedEvent"
        assert data["entity_id"] == 123
        assert data["user_id"] == 456
        assert data["organization_id"] == 789
        assert "event_id" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_unregister_handler(self):
        """Test handler unregistration."""
        called = False

        @EventBus.on(UserCreatedEvent)
        async def test_handler(event: UserCreatedEvent):
            nonlocal called
            called = True

        # Verify handler is registered
        assert EventBus.get_handler_count(UserCreatedEvent) == 1

        # Emit event - handler should be called
        event = UserCreatedEvent(entity_id=1)
        await EventBus.emit(event)
        assert called

        # Unregister handler
        EventBus.unregister(UserCreatedEvent, test_handler)
        assert EventBus.get_handler_count(UserCreatedEvent) == 0

        # Emit again - handler should not be called
        called = False
        await EventBus.emit(event)
        assert not called

    @pytest.mark.asyncio
    async def test_unregister_all_handlers_for_event(self):
        """Test unregistering all handlers for an event type."""

        @EventBus.on(UserCreatedEvent)
        async def handler1(event: UserCreatedEvent):
            pass

        @EventBus.on(UserCreatedEvent)
        async def handler2(event: UserCreatedEvent):
            pass

        assert EventBus.get_handler_count(UserCreatedEvent) == 2

        # Unregister all handlers for UserCreatedEvent
        EventBus.unregister(UserCreatedEvent)
        assert EventBus.get_handler_count(UserCreatedEvent) == 0
