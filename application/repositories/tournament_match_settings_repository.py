"""Repository for Tournament Match Settings data access.

Enforces organization scoping for all reads and writes.
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime, timezone
import logging

from models.tournament_match_settings import TournamentMatchSettings
from models.match_schedule import Match

logger = logging.getLogger(__name__)


class TournamentMatchSettingsRepository:
    """Data access methods for TournamentMatchSettings model."""

    async def get_by_id(self, settings_id: int) -> Optional[TournamentMatchSettings]:
        """Get settings submission by ID."""
        return await TournamentMatchSettings.get_or_none(id=settings_id).prefetch_related('match', 'submitted_by')

    async def get_for_match_and_game(
        self,
        match_id: int,
        game_number: int = 1
    ) -> Optional[TournamentMatchSettings]:
        """
        Get settings submission for a specific match and game number.
        
        Args:
            match_id: Match ID
            game_number: Game number in the match series (default 1)
            
        Returns:
            Settings submission or None if not found
        """
        return await TournamentMatchSettings.get_or_none(
            match_id=match_id,
            game_number=game_number
        ).prefetch_related('match', 'submitted_by')

    async def list_for_match(self, match_id: int) -> List[TournamentMatchSettings]:
        """
        List all settings submissions for a match.
        
        Args:
            match_id: Match ID
            
        Returns:
            List of settings submissions ordered by game number
        """
        return await TournamentMatchSettings.filter(
            match_id=match_id
        ).order_by('game_number').prefetch_related('match', 'submitted_by')

    async def list_for_tournament(
        self,
        tournament_id: int,
        submitted_only: bool = False
    ) -> List[TournamentMatchSettings]:
        """
        List all settings submissions for a tournament.
        
        Args:
            tournament_id: Tournament ID
            submitted_only: If True, only return submitted settings
            
        Returns:
            List of settings submissions ordered by match creation date
        """
        query = TournamentMatchSettings.filter(
            match__tournament_id=tournament_id
        )
        
        if submitted_only:
            query = query.filter(submitted=True)
        
        return await query.order_by('-submitted_at').prefetch_related('match', 'submitted_by')

    async def create(
        self,
        match_id: int,
        submitted_by_id: int,
        settings: dict,
        game_number: int = 1,
        notes: Optional[str] = None,
        is_valid: bool = True,
        validation_error: Optional[str] = None,
    ) -> TournamentMatchSettings:
        """
        Create a settings submission.
        
        Args:
            match_id: Match ID
            submitted_by_id: User ID of submitter
            settings: Settings data (JSON dict)
            game_number: Game number in match series (default 1)
            notes: Optional notes from submitter
            is_valid: Whether settings passed validation (default True)
            validation_error: Validation error message if invalid
            
        Returns:
            Created settings submission
        """
        submission = await TournamentMatchSettings.create(
            match_id=match_id,
            submitted_by_id=submitted_by_id,
            settings=settings,
            game_number=game_number,
            notes=notes,
            submitted=True,
            is_valid=is_valid,
            validation_error=validation_error,
        )
        logger.info(
            "Created settings submission %s for match %s game %s by user %s",
            submission.id,
            match_id,
            game_number,
            submitted_by_id
        )
        return submission

    async def update(
        self,
        settings_id: int,
        **updates
    ) -> Optional[TournamentMatchSettings]:
        """
        Update a settings submission.
        
        Args:
            settings_id: Settings submission ID
            **updates: Field updates (settings, notes, is_valid, validation_error, applied, applied_at)
            
        Returns:
            Updated settings submission or None if not found
        """
        submission = await self.get_by_id(settings_id)
        if not submission:
            return None

        # Apply all provided updates
        for field, value in updates.items():
            if hasattr(submission, field):
                setattr(submission, field, value)

        await submission.save()
        logger.info("Updated settings submission %s", settings_id)
        return submission

    async def mark_applied(
        self,
        settings_id: int
    ) -> Optional[TournamentMatchSettings]:
        """
        Mark settings as applied (used to generate race).
        
        Args:
            settings_id: Settings submission ID
            
        Returns:
            Updated settings submission or None if not found
        """
        return await self.update(
            settings_id,
            applied=True,
            applied_at=datetime.now(timezone.utc)
        )

    async def delete(self, settings_id: int) -> bool:
        """
        Delete a settings submission.
        
        Args:
            settings_id: Settings submission ID
            
        Returns:
            True if deleted, False if not found
        """
        submission = await self.get_by_id(settings_id)
        if not submission:
            return False

        await submission.delete()
        logger.info("Deleted settings submission %s", settings_id)
        return True

    async def exists_for_match_and_game(
        self,
        match_id: int,
        game_number: int = 1
    ) -> bool:
        """
        Check if settings submission exists for match and game.
        
        Args:
            match_id: Match ID
            game_number: Game number (default 1)
            
        Returns:
            True if submission exists
        """
        count = await TournamentMatchSettings.filter(
            match_id=match_id,
            game_number=game_number
        ).count()
        return count > 0
