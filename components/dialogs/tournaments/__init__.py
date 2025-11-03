"""Tournament-related dialogs."""

from components.dialogs.tournaments.match_seed_dialog import MatchSeedDialog
from components.dialogs.tournaments.edit_match_dialog import EditMatchDialog
from components.dialogs.tournaments.submit_match_dialog import SubmitMatchDialog
from components.dialogs.tournaments.register_player_dialog import RegisterPlayerDialog
from components.dialogs.tournaments.pool_dialog import PoolDialog
from components.dialogs.tournaments.permalink_dialog import PermalinkDialog
from components.dialogs.tournaments.async_tournament_dialog import AsyncTournamentDialog
from components.dialogs.tournaments.race_review_dialog import RaceReviewDialog

__all__ = [
    'MatchSeedDialog',
    'EditMatchDialog',
    'SubmitMatchDialog',
    'RegisterPlayerDialog',
    'PoolDialog',
    'PermalinkDialog',
    'AsyncTournamentDialog',
    'RaceReviewDialog',
]
