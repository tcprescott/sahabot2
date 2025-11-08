"""Repository for async tournament data access."""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import logging

from models.async_tournament import (
    AsyncTournament,
    AsyncTournamentPool,
    AsyncTournamentPermalink,
    AsyncTournamentRace,
    AsyncTournamentAuditLog,
)

logger = logging.getLogger(__name__)


class AsyncTournamentRepository:
    """Data access methods for async tournaments."""

    async def list_by_org(self, organization_id: int) -> List[AsyncTournament]:
        """List all async tournaments for an organization."""
        return await AsyncTournament.filter(organization_id=organization_id).all()

    async def list_active_by_org(self, organization_id: int) -> List[AsyncTournament]:
        """List active async tournaments for an organization."""
        return await AsyncTournament.filter(organization_id=organization_id, is_active=True).all()

    async def get_by_id(self, tournament_id: int, organization_id: int) -> Optional[AsyncTournament]:
        """Get an async tournament by ID, scoped to organization."""
        return await AsyncTournament.get_or_none(id=tournament_id, organization_id=organization_id)

    async def create(
        self,
        organization_id: int,
        name: str,
        description: Optional[str],
        is_active: bool = True,
        hide_results: bool = False,
        discord_channel_id: Optional[int] = None,
        runs_per_pool: int = 1,
    ) -> AsyncTournament:
        """Create a new async tournament."""
        tournament = await AsyncTournament.create(
            organization_id=organization_id,
            name=name,
            description=description,
            is_active=is_active,
            hide_results=hide_results,
            discord_channel_id=discord_channel_id,
            runs_per_pool=runs_per_pool,
        )
        logger.info("Created async tournament %s for org %s", tournament.id, organization_id)
        return tournament

    async def update(
        self,
        tournament_id: int,
        organization_id: int,
        **fields
    ) -> Optional[AsyncTournament]:
        """Update an async tournament."""
        tournament = await self.get_by_id(tournament_id, organization_id)
        if not tournament:
            return None

        for field, value in fields.items():
            if value is not None and hasattr(tournament, field):
                setattr(tournament, field, value)

        await tournament.save()
        logger.info("Updated async tournament %s", tournament_id)
        return tournament

    async def delete(self, tournament_id: int, organization_id: int) -> bool:
        """Delete an async tournament."""
        tournament = await self.get_by_id(tournament_id, organization_id)
        if not tournament:
            return False

        await tournament.delete()
        logger.info("Deleted async tournament %s", tournament_id)
        return True

    # Pool methods

    async def list_pools(self, tournament_id: int, organization_id: int) -> List[AsyncTournamentPool]:
        """List pools for a tournament."""
        tournament = await self.get_by_id(tournament_id, organization_id)
        if not tournament:
            return []
        return await AsyncTournamentPool.filter(tournament_id=tournament_id).all()

    async def create_pool(
        self,
        tournament_id: int,
        organization_id: int,
        name: str,
        description: Optional[str] = None,
    ) -> Optional[AsyncTournamentPool]:
        """Create a pool for a tournament."""
        tournament = await self.get_by_id(tournament_id, organization_id)
        if not tournament:
            return None

        pool = await AsyncTournamentPool.create(
            tournament_id=tournament_id,
            name=name,
            description=description,
        )
        logger.info("Created pool %s for tournament %s", pool.id, tournament_id)
        return pool

    async def get_pool_by_id(
        self,
        pool_id: int,
        organization_id: int
    ) -> Optional[AsyncTournamentPool]:
        """Get a pool by ID, verifying organization ownership."""
        pool = await AsyncTournamentPool.get_or_none(id=pool_id).prefetch_related('tournament')
        if not pool:
            return None

        # Verify org ownership through tournament
        if pool.tournament.organization_id != organization_id:
            return None

        return pool

    async def update_pool(
        self,
        pool_id: int,
        organization_id: int,
        **fields
    ) -> Optional[AsyncTournamentPool]:
        """Update a pool."""
        pool = await self.get_pool_by_id(pool_id, organization_id)
        if not pool:
            return None

        for field, value in fields.items():
            if hasattr(pool, field):
                setattr(pool, field, value)

        await pool.save()
        logger.info("Updated pool %s", pool_id)
        return pool

    async def delete_pool(
        self,
        pool_id: int,
        organization_id: int
    ) -> bool:
        """Delete a pool and all associated permalinks and races."""
        pool = await self.get_pool_by_id(pool_id, organization_id)
        if not pool:
            return False

        # Cascading delete will handle permalinks and races
        await pool.delete()
        logger.info("Deleted pool %s", pool_id)
        return True

    # Permalink methods

    async def list_permalinks(self, pool_id: int, organization_id: int) -> List[AsyncTournamentPermalink]:
        """List permalinks for a pool."""
        pool = await AsyncTournamentPool.get_or_none(id=pool_id)
        if not pool:
            return []

        # Verify org ownership through tournament
        tournament = await self.get_by_id(pool.tournament_id, organization_id)
        if not tournament:
            return []

        return await AsyncTournamentPermalink.filter(pool_id=pool_id).all()

    async def create_permalink(
        self,
        pool_id: int,
        organization_id: int,
        url: str,
        notes: Optional[str] = None,
    ) -> Optional[AsyncTournamentPermalink]:
        """Create a permalink for a pool."""
        pool = await AsyncTournamentPool.get_or_none(id=pool_id)
        if not pool:
            return None

        # Verify org ownership through tournament
        tournament = await self.get_by_id(pool.tournament_id, organization_id)
        if not tournament:
            return None

        permalink = await AsyncTournamentPermalink.create(
            pool_id=pool_id,
            url=url,
            notes=notes,
        )
        logger.info("Created permalink %s for pool %s", permalink.id, pool_id)
        return permalink

    async def get_permalink_by_id(
        self,
        permalink_id: int,
        organization_id: int
    ) -> Optional[AsyncTournamentPermalink]:
        """Get a permalink by ID, verifying organization ownership."""
        permalink = await AsyncTournamentPermalink.get_or_none(id=permalink_id).prefetch_related('pool__tournament')
        if not permalink:
            return None

        # Verify org ownership through pool -> tournament
        if permalink.pool.tournament.organization_id != organization_id:
            return None

        return permalink

    async def update_permalink(
        self,
        permalink_id: int,
        organization_id: int,
        **fields
    ) -> Optional[AsyncTournamentPermalink]:
        """Update a permalink."""
        permalink = await self.get_permalink_by_id(permalink_id, organization_id)
        if not permalink:
            return None

        for field, value in fields.items():
            if hasattr(permalink, field):
                setattr(permalink, field, value)

        await permalink.save()
        logger.info("Updated permalink %s", permalink_id)
        return permalink

    async def delete_permalink(
        self,
        permalink_id: int,
        organization_id: int
    ) -> bool:
        """Delete a permalink and all associated races."""
        permalink = await self.get_permalink_by_id(permalink_id, organization_id)
        if not permalink:
            return False

        # Cascading delete will handle races
        await permalink.delete()
        logger.info("Deleted permalink %s", permalink_id)
        return True

    # Race methods

    async def list_races(
        self,
        tournament_id: int,
        organization_id: int,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[AsyncTournamentRace]:
        """List races for a tournament with optional filters."""
        tournament = await self.get_by_id(tournament_id, organization_id)
        if not tournament:
            return []

        filters = {'tournament_id': tournament_id}
        if user_id is not None:
            filters['user_id'] = user_id
        if status is not None:
            filters['status'] = status

        return await AsyncTournamentRace.filter(**filters).prefetch_related('permalink').all()

    async def get_race_by_id(
        self,
        race_id: int,
        organization_id: int
    ) -> Optional[AsyncTournamentRace]:
        """Get a race by ID, verifying organization ownership."""
        race = await AsyncTournamentRace.get_or_none(id=race_id).prefetch_related('tournament')
        if not race:
            return None

        # Verify org ownership
        if race.tournament.organization_id != organization_id:
            return None

        return race

    async def get_race_by_thread_id(
        self,
        discord_thread_id: int
    ) -> Optional[AsyncTournamentRace]:
        """Get a race by Discord thread ID."""
        race = await AsyncTournamentRace.get_or_none(
            discord_thread_id=discord_thread_id
        ).prefetch_related('user', 'tournament')
        return race

    async def create_race(
        self,
        tournament_id: int,
        organization_id: int,
        permalink_id: int,
        user_id: int,
        discord_thread_id: Optional[int] = None,
    ) -> Optional[AsyncTournamentRace]:
        """Create a new race."""
        tournament = await self.get_by_id(tournament_id, organization_id)
        if not tournament:
            return None

        race = await AsyncTournamentRace.create(
            tournament_id=tournament_id,
            permalink_id=permalink_id,
            user_id=user_id,
            discord_thread_id=discord_thread_id,
            thread_open_time=datetime.now(timezone.utc) if discord_thread_id else None,
        )
        logger.info("Created race %s for user %s in tournament %s", race.id, user_id, tournament_id)
        return race

    async def update_race(
        self,
        race_id: int,
        organization_id: int,
        **fields
    ) -> Optional[AsyncTournamentRace]:
        """Update a race."""
        race = await self.get_race_by_id(race_id, organization_id)
        if not race:
            return None

        for field, value in fields.items():
            if hasattr(race, field):
                setattr(race, field, value)

        await race.save()
        logger.info("Updated race %s", race_id)

        # Refetch with all related fields to avoid N+1 queries
        race = await AsyncTournamentRace.get(id=race_id).prefetch_related(
            'user', 'reviewed_by', 'permalink__pool', 'tournament'
        )
        return race

    # Audit log methods

    async def create_audit_log(
        self,
        tournament_id: int,
        action: str,
        details: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> AsyncTournamentAuditLog:
        """Create an audit log entry."""
        audit_log = await AsyncTournamentAuditLog.create(
            tournament_id=tournament_id,
            action=action,
            details=details,
            user_id=user_id,
        )
        logger.info("Created audit log %s for tournament %s: %s", audit_log.id, tournament_id, action)
        return audit_log

    # Review methods

    async def get_review_queue(
        self,
        tournament_id: int,
        organization_id: int,
        status: Optional[str] = None,
        review_status: Optional[str] = None,
        reviewed_by_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AsyncTournamentRace]:
        """
        Get races in the review queue for a tournament.

        Args:
            tournament_id: Tournament ID
            organization_id: Organization ID (for verification)
            status: Optional race status filter (e.g., 'finished')
            review_status: Optional review status filter (e.g., 'pending', 'accepted', 'rejected')
            reviewed_by_id: Optional filter by reviewer
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            List of races matching the filters
        """
        # Verify tournament belongs to organization
        tournament = await self.get_by_id(tournament_id, organization_id)
        if not tournament:
            return []

        query = AsyncTournamentRace.filter(
            tournament_id=tournament_id,
            reattempted=False  # Don't include reattempted races
        ).prefetch_related('user', 'reviewed_by', 'permalink', 'permalink__pool')

        if status:
            query = query.filter(status=status)

        if review_status:
            query = query.filter(review_status=review_status)

        if reviewed_by_id is not None:
            if reviewed_by_id == -1:  # Special value for unreviewed
                query = query.filter(reviewed_by_id__isnull=True)
            else:
                query = query.filter(reviewed_by_id=reviewed_by_id)

        races = await query.offset(skip).limit(limit).order_by('-created_at')
        return list(races)

    async def update_race_review(
        self,
        race_id: int,
        organization_id: int,
        review_status: str,
        reviewer_id: int,
        reviewer_notes: Optional[str] = None,
        elapsed_time_override: Optional[timedelta] = None,
    ) -> Optional[AsyncTournamentRace]:
        """
        Update the review status and notes for a race.

        Args:
            race_id: Race ID
            organization_id: Organization ID (for verification)
            review_status: New review status ('pending', 'accepted', 'rejected')
            reviewer_id: ID of the reviewing user
            reviewer_notes: Optional notes from the reviewer
            elapsed_time_override: Optional elapsed time override (for corrections)

        Returns:
            Updated race or None if not found/unauthorized
        """
        race = await self.get_race_by_id(race_id, organization_id)
        if not race:
            return None

        # Update review fields
        race.review_status = review_status
        race.reviewed_by_id = reviewer_id
        race.reviewed_at = datetime.now(timezone.utc)

        if reviewer_notes is not None:
            race.reviewer_notes = reviewer_notes

        # If elapsed time override provided, update start/end times
        if elapsed_time_override and race.end_time:
            race.start_time = race.end_time - elapsed_time_override

        await race.save()
        logger.info("Updated review for race %s: %s by user %s", race_id, review_status, reviewer_id)
        return race
