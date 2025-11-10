"""
Live race handler for RaceTime.gg integration.

Extends SahaRaceHandler to add live race-specific logic.
"""

import logging
from racetime.client import SahaRaceHandler

logger = logging.getLogger(__name__)


class AsyncLiveRaceHandler(SahaRaceHandler):
    """
    Handler for async tournament live races on RaceTime.gg.

    Extends SahaRaceHandler to add live race-specific functionality:
    - Automatic race start processing
    - Automatic result recording
    - Live race service integration
    """

    def __init__(
        self,
        bot_instance,
        live_race_id: int,
        *args,
        **kwargs,
    ):
        """
        Initialize live race handler.

        Args:
            bot_instance: The RacetimeBot instance
            live_race_id: ID of the AsyncQualifierLiveRace
            *args: Arguments for parent RaceHandler
            **kwargs: Keyword arguments for parent RaceHandler
        """
        super().__init__(bot_instance, *args, **kwargs)
        self.live_race_id = live_race_id
        self._race_started = False
        self._race_finished = False

    async def race_data(self, data):
        """
        Override race_data to process live race events.

        Calls parent to handle standard race events, then adds live race processing:
        - When race starts: Call AsyncLiveRaceService.process_race_start()
        - When race finishes: Call AsyncLiveRaceService.process_race_finish()
        """
        # Call parent to handle standard events
        await super().race_data(data)

        # Import here to avoid circular dependency
        from application.services.async_qualifiers.async_live_race_service import (
            AsyncLiveRaceService,
        )

        race_status = data.get("status", {}).get("value")

        # Process race start (transitions to 'in_progress')
        if race_status == "in_progress" and not self._race_started:
            self._race_started = True
            race_slug = data.get("name", "unknown")
            logger.info(
                "Live race %s started on RaceTime.gg (slug: %s)",
                self.live_race_id,
                race_slug,
            )

            try:
                # Get entrant racetime IDs
                entrants = data.get("entrants", [])
                participant_racetime_ids = [
                    e.get("user", {}).get("id")
                    for e in entrants
                    if e.get("user", {}).get("id")
                ]

                # Call service to create race records
                service = AsyncLiveRaceService()
                await service.process_race_start(
                    live_race_id=self.live_race_id,
                    participant_racetime_ids=participant_racetime_ids,
                )
            except Exception as e:
                logger.error(
                    "Failed to process live race start for race %s: %s",
                    self.live_race_id,
                    e,
                    exc_info=True,
                )

        # Process race finish (transitions to 'finished')
        if race_status == "finished" and not self._race_finished:
            self._race_finished = True
            race_slug = data.get("name", "unknown")
            logger.info(
                "Live race %s finished on RaceTime.gg (slug: %s)",
                self.live_race_id,
                race_slug,
            )

            try:
                # Extract results from entrants
                entrants = data.get("entrants", [])
                results = []

                for entrant in entrants:
                    racetime_id = entrant.get("user", {}).get("id")
                    status = entrant.get("status", {}).get("value")
                    finish_time = entrant.get("finish_time")

                    if racetime_id:
                        results.append(
                            {
                                "racetime_id": racetime_id,
                                "status": status,
                                "finish_time": finish_time,
                            }
                        )

                # Call service to record results
                service = AsyncLiveRaceService()
                await service.process_race_finish(
                    live_race_id=self.live_race_id,
                    results=results,
                )
            except Exception as e:
                logger.error(
                    "Failed to process live race finish for race %s: %s",
                    self.live_race_id,
                    e,
                    exc_info=True,
                )
