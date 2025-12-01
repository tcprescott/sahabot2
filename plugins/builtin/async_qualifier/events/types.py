"""
AsyncQualifier plugin event types.

Event types for async qualifier operations are defined in the core application
at application.events.types. They are part of the core event bus infrastructure.

This file is kept for reference. Import events directly from application.events:

    from application.events import (
        RaceSubmittedEvent,
        RaceApprovedEvent,
        RaceRejectedEvent,
        AsyncLiveRaceCreatedEvent,
        AsyncLiveRaceUpdatedEvent,
        AsyncLiveRaceRoomOpenedEvent,
        AsyncLiveRaceStartedEvent,
        AsyncLiveRaceFinishedEvent,
        AsyncLiveRaceCancelledEvent,
    )
"""

# Events are defined in application.events.types
# Import them directly from there

__all__: list[str] = []
