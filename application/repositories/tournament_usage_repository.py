"""
Repository for tournament usage tracking.

This repository handles data access for tournament usage history.
"""

import logging
from models import TournamentUsage, User, Tournament

logger = logging.getLogger(__name__)


class TournamentUsageRepository:
    """Repository for tournament usage tracking operations."""

    async def record_usage(
        self,
        user: User,
        tournament: Tournament,
        organization_id: int,
        organization_name: str,
    ) -> TournamentUsage:
        """
        Record or update tournament usage for a user.

        This uses update_or_create to ensure only one record per user-tournament pair.
        Updates last_accessed timestamp and denormalized fields.

        Args:
            user: User accessing the tournament
            tournament: Tournament being accessed
            organization_id: ID of the organization
            organization_name: Name of the organization

        Returns:
            TournamentUsage: Created or updated usage record
        """
        usage, created = await TournamentUsage.update_or_create(
            user=user,
            tournament=tournament,
            defaults={
                'organization_id': organization_id,
                'organization_name': organization_name,
                'tournament_name': tournament.name,
                # last_accessed auto-updates via auto_now
            }
        )
        
        action = "Created" if created else "Updated"
        logger.info(
            "%s tournament usage tracking for user %s, tournament %s",
            action,
            user.id,
            tournament.id
        )
        
        return usage

    async def get_recent_tournaments(
        self,
        user: User,
        limit: int = 5
    ) -> list[TournamentUsage]:
        """
        Get user's most recently accessed tournaments.

        Args:
            user: User to fetch history for
            limit: Maximum number of tournaments to return (default 5)

        Returns:
            list[TournamentUsage]: Recent tournament usage records, most recent first
        """
        usages = await TournamentUsage.filter(user=user).order_by('-last_accessed').limit(limit)
        
        logger.debug(
            "Retrieved %d recent tournaments for user %s",
            len(usages),
            user.id
        )
        
        return usages

    async def clear_tournament_usage(self, tournament_id: int) -> int:
        """
        Clear all usage records for a tournament.

        This is useful when a tournament is deleted.

        Args:
            tournament_id: ID of tournament to clear usage for

        Returns:
            int: Number of records deleted
        """
        deleted_count = await TournamentUsage.filter(tournament_id=tournament_id).delete()
        
        logger.info(
            "Cleared %d usage records for tournament %s",
            deleted_count,
            tournament_id
        )
        
        return deleted_count

    async def clear_user_usage(self, user_id: int) -> int:
        """
        Clear all usage records for a user.

        Args:
            user_id: ID of user to clear usage for

        Returns:
            int: Number of records deleted
        """
        deleted_count = await TournamentUsage.filter(user_id=user_id).delete()
        
        logger.info(
            "Cleared %d usage records for user %s",
            deleted_count,
            user_id
        )
        
        return deleted_count

    async def cleanup_old_entries(self, days_to_keep: int = 90) -> int:
        """
        Remove tournament usage entries older than specified days.

        This helps prevent the table from growing indefinitely.

        Args:
            days_to_keep: Number of days to keep entries (default 90)

        Returns:
            int: Number of records deleted
        """
        from datetime import datetime, timedelta, timezone
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        deleted_count = await TournamentUsage.filter(last_accessed__lt=cutoff_date).delete()
        
        logger.info(
            "Cleaned up %d tournament usage entries older than %d days",
            deleted_count,
            days_to_keep
        )
        
        return deleted_count

    async def cleanup_excess_per_user(self, keep_per_user: int = 10) -> int:
        """
        Remove excess tournament usage entries per user, keeping only the most recent N.

        This prevents users with high activity from accumulating too many records.

        Args:
            keep_per_user: Number of most recent entries to keep per user (default 10)

        Returns:
            int: Number of records deleted
        """
        # Get all users with usage records
        users_with_usage = await TournamentUsage.all().distinct().values_list('user_id', flat=True)
        
        total_deleted = 0
        for user_id in users_with_usage:
            # Get all usage records for this user, ordered by most recent first
            all_usage = await TournamentUsage.filter(user_id=user_id).order_by('-last_accessed').values_list('id', flat=True)
            
            # If user has more than keep_per_user records, delete the excess
            if len(all_usage) > keep_per_user:
                ids_to_delete = all_usage[keep_per_user:]  # Get IDs beyond the limit
                deleted = await TournamentUsage.filter(id__in=ids_to_delete).delete()
                total_deleted += deleted
                
                logger.debug(
                    "Cleaned up %d excess tournament usage entries for user %s",
                    deleted,
                    user_id
                )
        
        logger.info(
            "Cleaned up %d excess tournament usage entries across all users (keeping %d per user)",
            total_deleted,
            keep_per_user
        )
        
        return total_deleted
