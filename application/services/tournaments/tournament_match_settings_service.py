"""Service layer for Tournament Match Settings management.

Contains business logic for settings submissions with authorization checks.
"""

from __future__ import annotations
from typing import Optional, List
import logging

from models import User, SYSTEM_USER_ID
from models.tournament_match_settings import TournamentMatchSettings
from models.match_schedule import Match, MatchPlayers
from application.repositories.tournament_match_settings_repository import TournamentMatchSettingsRepository
from application.repositories.tournament_repository import TournamentRepository
from application.services.organizations.organization_service import OrganizationService
from application.services.authorization.authorization_service_v2 import AuthorizationServiceV2
from application.events import EventBus, TournamentMatchSettingsSubmittedEvent

logger = logging.getLogger(__name__)


class TournamentMatchSettingsService:
    """Business logic for tournament match settings submissions."""

    def __init__(self) -> None:
        self.repo = TournamentMatchSettingsRepository()
        self.tournament_repo = TournamentRepository()
        self.org_service = OrganizationService()
        self.auth = AuthorizationServiceV2()

    async def _validate_match_access(
        self,
        user: Optional[User],
        match: Match
    ) -> bool:
        """
        Validate user has access to match (is a player or has tournament management permission).

        Args:
            user: User to check
            match: Match to validate access for

        Returns:
            True if user has access, False otherwise
        """
        if not user:
            return False

        # Fetch tournament to get organization_id
        await match.fetch_related('tournament')
        tournament = match.tournament
        organization_id = tournament.organization_id

        # Check if user is a player in this match
        is_player = await MatchPlayers.filter(match_id=match.id, user_id=user.id).exists()
        if is_player:
            return True

        # Check if user has tournament management permission
        can_manage = await self.auth.can(
            user,
            action=self.auth.get_action_for_operation("tournament", "update"),
            resource=self.auth.get_resource_identifier("tournament", str(tournament.id)),
            organization_id=organization_id
        )
        return can_manage

    async def get_match_for_submission(
        self,
        user: Optional[User],
        match_id: int
    ) -> Optional[Match]:
        """
        Get match details for settings submission with authorization check.

        Args:
            user: Current user
            match_id: Match ID

        Returns:
            Match object with related data or None if not found/unauthorized
        """
        # Get the match with related data
        match = await Match.get_or_none(id=match_id).prefetch_related('tournament', 'players')
        if not match:
            logger.warning("Match %s not found", match_id)
            return None

        # Validate access
        has_access = await self._validate_match_access(user, match)
        if not has_access:
            logger.warning(
                "Unauthorized access to match %s by user %s",
                match_id,
                getattr(user, 'id', None)
            )
            return None

        return match

    async def get_submission(
        self,
        user: Optional[User],
        match_id: int,
        game_number: int = 1
    ) -> Optional[TournamentMatchSettings]:
        """
        Get settings submission for a match and game number.

        Args:
            user: Current user
            match_id: Match ID
            game_number: Game number in series (default 1)

        Returns:
            Settings submission or None if not found/unauthorized
        """
        # Get the match first
        match = await Match.get_or_none(id=match_id)
        if not match:
            logger.warning("Match %s not found", match_id)
            return None

        # Validate access
        has_access = await self._validate_match_access(user, match)
        if not has_access:
            logger.warning(
                "Unauthorized get_submission by user %s for match %s",
                getattr(user, 'id', None),
                match_id
            )
            return None

        return await self.repo.get_for_match_and_game(match_id, game_number)

    async def list_submissions_for_match(
        self,
        user: Optional[User],
        match_id: int
    ) -> List[TournamentMatchSettings]:
        """
        List all settings submissions for a match.

        Args:
            user: Current user
            match_id: Match ID

        Returns:
            List of settings submissions (empty if unauthorized)
        """
        # Get the match first
        match = await Match.get_or_none(id=match_id)
        if not match:
            logger.warning("Match %s not found", match_id)
            return []

        # Validate access
        has_access = await self._validate_match_access(user, match)
        if not has_access:
            logger.warning(
                "Unauthorized list_submissions_for_match by user %s for match %s",
                getattr(user, 'id', None),
                match_id
            )
            return []

        return await self.repo.list_for_match(match_id)

    async def submit_settings(
        self,
        user: User,
        match_id: int,
        settings: dict,
        game_number: int = 1,
        notes: Optional[str] = None
    ) -> Optional[TournamentMatchSettings]:
        """
        Submit settings for a tournament match.

        Args:
            user: User submitting settings (must be a player or have tournament management permission)
            match_id: Match ID
            settings: Settings data (dict)
            game_number: Game number in series (default 1)
            notes: Optional notes from submitter

        Returns:
            Created/updated settings submission or None if unauthorized/validation failed
        """
        # Get the match
        match = await Match.get_or_none(id=match_id)
        if not match:
            logger.warning("Match %s not found for settings submission", match_id)
            return None

        # Validate access
        has_access = await self._validate_match_access(user, match)
        if not has_access:
            logger.warning(
                "Unauthorized submit_settings by user %s for match %s",
                user.id,
                match_id
            )
            return None

        # Validate settings structure (basic validation - can be extended)
        if not isinstance(settings, dict) or not settings:
            logger.warning("Invalid settings data for match %s: %s", match_id, settings)
            return None

        # Check if submission already exists for this match/game
        existing = await self.repo.get_for_match_and_game(match_id, game_number)
        
        if existing:
            # Update existing submission
            submission = await self.repo.update(
                existing.id,
                settings=settings,
                notes=notes,
                submitted_by_id=user.id,
                is_valid=True,
                validation_error=None
            )
            logger.info(
                "Updated settings submission %s for match %s game %s by user %s",
                submission.id,
                match_id,
                game_number,
                user.id
            )
        else:
            # Create new submission
            submission = await self.repo.create(
                match_id=match_id,
                submitted_by_id=user.id,
                settings=settings,
                game_number=game_number,
                notes=notes,
                is_valid=True
            )
            logger.info(
                "Created settings submission %s for match %s game %s by user %s",
                submission.id,
                match_id,
                game_number,
                user.id
            )

        # Emit event for notification system
        await match.fetch_related('tournament')
        await EventBus.emit(TournamentMatchSettingsSubmittedEvent(
            user_id=user.id,
            organization_id=match.tournament.organization_id,
            entity_id=submission.id,
            match_id=match_id,
            tournament_id=match.tournament_id,
            game_number=game_number,
            submitted_by_user_id=user.id,
            settings_data=settings
        ))

        return submission

    async def delete_submission(
        self,
        user: User,
        submission_id: int
    ) -> bool:
        """
        Delete a settings submission.

        Args:
            user: User requesting deletion
            submission_id: Settings submission ID

        Returns:
            True if deleted, False if not found/unauthorized
        """
        # Get the submission
        submission = await self.repo.get_by_id(submission_id)
        if not submission:
            logger.warning("Settings submission %s not found", submission_id)
            return False

        # Get the match to check access
        await submission.fetch_related('match')
        match = submission.match

        # Validate access
        has_access = await self._validate_match_access(user, match)
        if not has_access:
            logger.warning(
                "Unauthorized delete_submission by user %s for submission %s",
                user.id,
                submission_id
            )
            return False

        return await self.repo.delete(submission_id)

    async def mark_settings_applied(
        self,
        submission_id: int,
        applied_by: Optional[User] = None
    ) -> Optional[TournamentMatchSettings]:
        """
        Mark settings as applied (used to generate race).

        This is typically called by automated systems when creating race rooms.

        Args:
            submission_id: Settings submission ID
            applied_by: User or system marking as applied (can be None for system)

        Returns:
            Updated submission or None if not found
        """
        user_id = applied_by.id if applied_by else SYSTEM_USER_ID
        logger.info(
            "Marking settings submission %s as applied by user %s",
            submission_id,
            user_id
        )
        return await self.repo.mark_applied(submission_id)

    async def validate_settings(
        self,
        settings: dict,
        tournament_id: int
    ) -> tuple[bool, Optional[str]]:
        """
        Validate settings structure and content.

        This is a basic validation - can be extended based on tournament type
        and specific requirements.

        Args:
            settings: Settings data to validate
            tournament_id: Tournament ID (for tournament-specific validation)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation
        if not isinstance(settings, dict):
            return False, "Settings must be a dictionary"

        if not settings:
            return False, "Settings cannot be empty"

        # Tournament-specific validation can be added here
        # For now, accept any non-empty dict
        return True, None
