"""
Match race handler for RaceTime.gg integration.

Provides match-specific logic as a mixin for tournament matches.
This mixin can be combined with category-specific handlers (e.g., ALTTPRRaceHandler)
to provide both match functionality and category-specific commands.
"""

import logging

logger = logging.getLogger(__name__)

# Cache for created match handler classes to avoid recreating the same class multiple times
_match_handler_class_cache = {}


class MatchRaceMixin:
    """
    Mixin for tournament match races on RaceTime.gg.

    Adds match-specific functionality to any race handler:
    - Automatic race finish processing
    - Automatic result recording for match players
    - Match service integration

    This mixin should be combined with a category-specific handler like:
        class ALTTPRMatchRaceHandler(MatchRaceMixin, ALTTPRRaceHandler):
            pass

    The mixin expects the following attributes to be available from the base handler:
    - self.data: Race data dictionary
    - self.bot: Bot instance reference
    """

    def __init__(
        self,
        *args,
        match_id: int,
        **kwargs,
    ):
        """
        Initialize match race mixin.

        Args:
            match_id: ID of the Match (must be passed as keyword argument)
            *args: Arguments for parent handler
            **kwargs: Keyword arguments for parent handler

        Note:
            The match_id parameter must always be provided as a keyword argument
            (e.g., match_id=123) due to its placement between *args and **kwargs.
            This is intentional to maintain compatibility with the parent class
            signature while ensuring match_id is always explicitly specified.
        """
        super().__init__(*args, **kwargs)
        self.match_id = match_id
        self._race_finished = False

    async def race_data(self, data):
        """
        Override race_data to process match race events.

        Calls parent to handle standard race events, then adds match processing:
        - When race finishes: Call TournamentService.process_match_race_finish()
        """
        # Call parent to handle standard events
        await super().race_data(data)

        # Import here to avoid circular dependency:
        # TournamentService imports Match model which could import handlers
        from application.services.tournaments.tournament_service import (
            TournamentService,
        )

        # After parent processes, self.data contains the unwrapped race data
        race_status = self.data.get("status", {}).get("value") if self.data else None

        # Process race finish (transitions to 'finished')
        if race_status == "finished" and not self._race_finished:
            self._race_finished = True
            race_slug = self.data.get("name", "unknown")
            logger.info(
                "Match race %s finished on RaceTime.gg (slug: %s)",
                self.match_id,
                race_slug,
            )

            try:
                # Extract results from entrants
                entrants = self.data.get("entrants", [])
                results = []

                for entrant in entrants:
                    racetime_id = entrant.get("user", {}).get("id")
                    status = entrant.get("status", {}).get("value")
                    finish_time = entrant.get("finish_time")
                    place = entrant.get("place")

                    if racetime_id:
                        results.append(
                            {
                                "racetime_id": racetime_id,
                                "status": status,
                                "finish_time": finish_time,
                                "place": place,
                            }
                        )

                # Call service to record results
                service = TournamentService()
                await service.process_match_race_finish(
                    match_id=self.match_id,
                    results=results,
                )
            except Exception as e:
                logger.error(
                    "Failed to process match race finish for match %s: %s",
                    self.match_id,
                    e,
                    exc_info=True,
                )


# Combined handler classes that mix match functionality with category-specific commands
# These allow tournament matches to use both match processing and category commands


def create_match_handler_class(base_handler_class):
    """
    Create a match handler class that combines MatchRaceMixin with a base handler.

    This function caches created classes to avoid recreating the same class multiple
    times, improving performance when handlers are created repeatedly.

    Args:
        base_handler_class: The base handler class to combine with (e.g., ALTTPRRaceHandler)

    Returns:
        A class that combines MatchRaceMixin with the base handler
    """
    # Check cache first to avoid recreating the same class
    cache_key = base_handler_class.__name__
    if cache_key in _match_handler_class_cache:
        return _match_handler_class_cache[cache_key]

    class CombinedMatchRaceHandler(MatchRaceMixin, base_handler_class):
        """
        Combined handler that provides both match functionality and category-specific commands.

        This handler is dynamically created by combining MatchRaceMixin with a category-specific
        handler like ALTTPRRaceHandler. It inherits:
        - Match processing from MatchRaceMixin (race finish handling, result recording)
        - Category commands from the base handler (!mystery, !vt, etc.)
        """

        pass

    # Set a descriptive name for the class
    base_name = base_handler_class.__name__
    CombinedMatchRaceHandler.__name__ = f"Match{base_name}"
    CombinedMatchRaceHandler.__qualname__ = f"Match{base_name}"

    # Cache the created class
    _match_handler_class_cache[cache_key] = CombinedMatchRaceHandler

    return CombinedMatchRaceHandler
