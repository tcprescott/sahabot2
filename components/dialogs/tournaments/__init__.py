"""Tournament-related dialogs."""

from components.dialogs.tournaments.match_seed_dialog import MatchSeedDialog
from components.dialogs.tournaments.edit_match_dialog import EditMatchDialog
from components.dialogs.tournaments.create_match_dialog import CreateMatchDialog
from components.dialogs.tournaments.submit_match_dialog import SubmitMatchDialog
from components.dialogs.tournaments.register_player_dialog import RegisterPlayerDialog
from components.dialogs.tournaments.pool_dialog import PoolDialog
from components.dialogs.tournaments.permalink_dialog import PermalinkDialog
from components.dialogs.tournaments.async_tournament_dialog import AsyncTournamentDialog
from components.dialogs.tournaments.race_review_dialog import RaceReviewDialog
from components.dialogs.tournaments.add_crew_dialog import AddCrewDialog
from components.dialogs.tournaments.create_live_race_dialog import CreateLiveRaceDialog
from components.dialogs.tournaments.match_winner_dialog import MatchWinnerDialog
from components.dialogs.tournaments.check_in_dialog import CheckInDialog

__all__ = [
    "MatchSeedDialog",
    "EditMatchDialog",
    "CreateMatchDialog",
    "SubmitMatchDialog",
    "RegisterPlayerDialog",
    "PoolDialog",
    "PermalinkDialog",
    "AsyncTournamentDialog",
    "RaceReviewDialog",
    "AddCrewDialog",
    "CreateLiveRaceDialog",
    "MatchWinnerDialog",
    "CheckInDialog",
]
