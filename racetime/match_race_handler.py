"""
Match race handler for RaceTime.gg integration.

Extends SahaRaceHandler to add match-specific logic for tournament matches.
"""

import logging
from racetime.client import SahaRaceHandler

logger = logging.getLogger(__name__)


class MatchRaceHandler(SahaRaceHandler):
    """
    Handler for tournament match races on RaceTime.gg.

    Extends SahaRaceHandler to add match-specific functionality:
    - Automatic race finish processing
    - Automatic result recording for match players
    - Match service integration
    """

    def __init__(
        self,
        bot_instance,
        match_id: int,
        *args,
        **kwargs,
    ):
        """
        Initialize match race handler.

        Args:
            bot_instance: The RacetimeBot instance
            match_id: ID of the Match
            *args: Arguments for parent RaceHandler
            **kwargs: Keyword arguments for parent RaceHandler
        """
        super().__init__(bot_instance, *args, **kwargs)
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
