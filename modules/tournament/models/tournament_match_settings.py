"""
Tournament Match Settings model.

This module contains the model for storing player-submitted race settings
for tournament matches. Players submit their preferred settings before a match,
which are then applied when creating the race room.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from tortoise import fields
from tortoise.models import Model

if TYPE_CHECKING:
    from modules.tournament.models.match_schedule import Match  # pragma: no cover
    from models.user import User  # pragma: no cover


class TournamentMatchSettings(Model):
    """
    Settings submission for a tournament match.

    Stores player-submitted race settings for tournament matches. Players can
    submit settings like preset selection, customizer options, or other game
    configuration before their match begins. These settings are applied when
    the race room is created.

    Based on SahasrahBot's TournamentGame model, adapted for SahaBot2's
    multi-tenant architecture.
    """

    id = fields.IntField(pk=True)
    match = fields.ForeignKeyField("models.Match", related_name="settings_submissions")

    # Game number in match series (1, 2, 3, etc. for best-of-N matches)
    game_number = fields.SmallIntField(default=1)

    # Settings data (flexible JSON structure to support different tournament types)
    # Structure varies by tournament type:
    # - Simple preset: {"preset": "standard"}
    # - Custom settings: {"preset": "custom", "glitches": "major", "swords": "randomized", ...}
    # - Mystery weightset: {"weightset": "league_season1"}
    settings = fields.JSONField()

    # Submission tracking
    submitted = fields.BooleanField(default=True)  # Always true on creation
    submitted_by = fields.ForeignKeyField(
        "models.User", related_name="tournament_settings_submissions"
    )
    submitted_at = fields.DatetimeField(auto_now_add=True)

    # Update tracking (if settings are modified after initial submission)
    updated_at = fields.DatetimeField(auto_now=True)

    # Notes from submitter (optional context or special requests)
    notes = fields.TextField(null=True)

    # Validation/review status
    is_valid = fields.BooleanField(
        default=True
    )  # Set false if settings fail validation
    validation_error = fields.TextField(null=True)  # Error message if invalid

    # Applied tracking (has this been used to generate a seed?)
    applied = fields.BooleanField(default=False)
    applied_at = fields.DatetimeField(null=True)

    class Meta:
        table = "tournament_match_settings"
        # Ensure only one submission per match + game_number combination
        unique_together = (("match", "game_number"),)

    def __str__(self) -> str:
        """String representation."""
        return f"Settings for Match {self.match_id} Game {self.game_number}"
