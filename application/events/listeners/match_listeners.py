"""
Match domain event listeners.

Handles audit logging for match scheduling, updates, and completion.
"""

import logging
from application.events import (
    EventBus,
    EventPriority,
    MatchFinishedEvent,
    TournamentMatchSettingsSubmittedEvent,
)

logger = logging.getLogger(__name__)


@EventBus.on(TournamentMatchSettingsSubmittedEvent, priority=EventPriority.HIGH)
async def log_match_settings_submitted(
    event: TournamentMatchSettingsSubmittedEvent,
) -> None:
    """Log tournament match settings submission to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who submitted
    user = (
        await user_repo.get_by_id(event.submitted_by_user_id)
        if event.submitted_by_user_id
        else None
    )

    await audit_service.log_action(
        user=user,
        action="tournament_match_settings_submitted",
        details={
            "entity_id": event.entity_id,
            "match_id": event.match_id,
            "tournament_id": event.tournament_id,
            "game_number": event.game_number,
            "settings": event.settings_data,
        },
        organization_id=event.organization_id,
    )
    logger.info(
        "Logged settings submission: submission_id=%s, match_id=%s, user_id=%s",
        event.entity_id,
        event.match_id,
        event.submitted_by_user_id,
    )


@EventBus.on(MatchFinishedEvent, priority=EventPriority.HIGH)
async def log_match_finished(event: MatchFinishedEvent) -> None:
    """Log match finish to audit log."""
    from application.services.core.audit_service import AuditService
    from application.repositories.user_repository import UserRepository

    audit_service = AuditService()
    user_repo = UserRepository()

    # Get the user who finished the match
    user = await user_repo.get_by_id(event.user_id) if event.user_id else None

    await audit_service.log_action(
        user=user,
        action="match_finished",
        details={
            "entity_id": event.entity_id,
            "match_id": event.match_id,
            "tournament_id": event.tournament_id,
        },
        organization_id=event.organization_id,
    )
    logger.info("Logged match finish: match_id=%s", event.entity_id)


logger.debug("Match event listeners registered")
