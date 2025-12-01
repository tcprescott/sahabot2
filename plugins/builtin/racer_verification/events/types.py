"""
RacerVerification Plugin event types.

This module defines event types for racer verification operations.
"""

from dataclasses import dataclass

from application.events.base import BaseEvent


@dataclass(frozen=True)
class RacerVerifiedEvent(BaseEvent):
    """Emitted when a user is verified as a racer."""

    verification_id: int = 0
    race_count: int = 0
    role_granted: bool = False
    categories: str = ""  # Comma-separated list

    @property
    def event_type(self) -> str:
        return "racer_verification.user.verified"


@dataclass(frozen=True)
class RacerVerificationCreatedEvent(BaseEvent):
    """Emitted when a racer verification configuration is created."""

    verification_id: int = 0
    guild_id: int = 0
    role_id: int = 0
    role_name: str = ""
    minimum_races: int = 0

    @property
    def event_type(self) -> str:
        return "racer_verification.config.created"


@dataclass(frozen=True)
class RacerVerificationUpdatedEvent(BaseEvent):
    """Emitted when a racer verification configuration is updated."""

    verification_id: int = 0
    updated_fields: str = ""  # Comma-separated list of updated field names

    @property
    def event_type(self) -> str:
        return "racer_verification.config.updated"
