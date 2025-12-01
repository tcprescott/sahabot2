"""
AsyncQualifier plugin events.

Event types for async qualifier operations are defined in the core application
at application.events.types. They are part of the core event bus infrastructure
and are imported directly from there.

Available events:
- RaceSubmittedEvent: Emitted when a race is submitted
- RaceApprovedEvent: Emitted when a race is approved
- RaceRejectedEvent: Emitted when a race is rejected
- AsyncLiveRaceCreatedEvent: Emitted when a live race is created
- AsyncLiveRaceUpdatedEvent: Emitted when a live race is updated
- AsyncLiveRaceRoomOpenedEvent: Emitted when a race room is opened
- AsyncLiveRaceStartedEvent: Emitted when a live race starts
- AsyncLiveRaceFinishedEvent: Emitted when a live race finishes
- AsyncLiveRaceCancelledEvent: Emitted when a live race is cancelled

Usage:
    from application.events import (
        EventBus,
        RaceSubmittedEvent,
        AsyncLiveRaceCreatedEvent,
    )
"""

# Events are imported directly from application.events
# No re-exports needed - import from application.events directly

__all__: list[str] = []
