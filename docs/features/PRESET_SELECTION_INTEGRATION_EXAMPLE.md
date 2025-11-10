# Preset Selection - Integration Example

This document shows a concrete example of integrating the PresetSelectionService with the existing seed generation flow.

## Current Flow (Before Integration)

Currently, seed generation in `views/tournaments/event_schedule.py` directly uses the tournament's randomizer preset:

```python
async def generate_seed(self):
    """Generate a seed for the match."""
    if not self.tournament.randomizer_preset:
        ui.notify('No randomizer preset configured', type='negative')
        return
    
    # Load preset settings
    preset = await self.tournament.randomizer_preset
    settings = preset.settings or {}
    
    # Generate seed via randomizer service
    randomizer_service = RandomizerService()
    result = await randomizer_service.generate_seed(
        randomizer_type=self.tournament.randomizer,
        settings=settings
    )
    
    # Display result...
```

## Updated Flow (With Conditional Selection)

With preset selection rules, we need to:
1. Check if the tournament has selection rules configured
2. Evaluate rules to determine which preset to use
3. Fall back to tournament default if no rules or no match

### Modified Seed Generation

```python
from application.services.tournaments.preset_selection_service import PresetSelectionService

async def generate_seed(self):
    """Generate a seed for the match."""
    # Determine which preset to use based on rules
    preset_id = await self._select_preset_for_match()
    
    if not preset_id:
        ui.notify('No randomizer preset configured', type='negative')
        return
    
    # Load the selected preset
    preset = await RandomizerPreset.get_or_none(id=preset_id)
    if not preset:
        ui.notify('Selected preset not found', type='negative')
        return
    
    settings = preset.settings or {}
    
    # Generate seed via randomizer service
    randomizer_service = RandomizerService()
    result = await randomizer_service.generate_seed(
        randomizer_type=self.tournament.randomizer,
        settings=settings
    )
    
    # Display result...

async def _select_preset_for_match(self) -> Optional[int]:
    """
    Determine which preset to use for this match.
    
    Uses PresetSelectionService to evaluate rules if configured,
    otherwise returns tournament default preset.
    
    Returns:
        Preset ID to use, or None if no preset available
    """
    # Get player settings submission if exists
    player_settings = None
    if self.current_user:
        settings_service = TournamentMatchSettingsService()
        player_settings = await settings_service.get_submission(
            match_id=self.match.id,
            user_id=self.current_user.id,
            game_number=1  # TODO: Support multi-game series
        )
    
    # Use PresetSelectionService to evaluate rules
    selection_service = PresetSelectionService()
    preset_id = await selection_service.select_preset_for_match(
        match=self.match,
        tournament=self.tournament,
        game_number=1,
        player_settings=player_settings
    )
    
    return preset_id
```

## API Endpoint Example

For API-based seed generation, modify `api/routes/seeds.py`:

```python
from fastapi import APIRouter, Depends
from application.services.tournaments.preset_selection_service import PresetSelectionService
from application.services.randomizer_service import RandomizerService
from models import Match, Tournament, RandomizerPreset

router = APIRouter(prefix="/seeds", tags=["seeds"])

@router.post("/matches/{match_id}/generate")
async def generate_seed_for_match(
    match_id: int,
    game_number: int = 1,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a seed for a match.
    
    Automatically selects the appropriate preset based on tournament rules.
    """
    # Load match and tournament
    match = await Match.get_or_none(id=match_id).prefetch_related('tournament')
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    tournament = match.tournament
    
    # Get player settings if submitted
    settings_service = TournamentMatchSettingsService()
    player_settings = await settings_service.get_submission(
        match_id=match_id,
        user_id=current_user.id,
        game_number=game_number
    )
    
    # Select preset using rules
    selection_service = PresetSelectionService()
    preset_id = await selection_service.select_preset_for_match(
        match=match,
        tournament=tournament,
        game_number=game_number,
        player_settings=player_settings
    )
    
    if not preset_id:
        raise HTTPException(
            status_code=400,
            detail="No preset configured for this tournament"
        )
    
    # Load preset
    preset = await RandomizerPreset.get_or_none(id=preset_id)
    if not preset:
        raise HTTPException(
            status_code=500,
            detail="Selected preset not found"
        )
    
    # Generate seed
    randomizer_service = RandomizerService()
    result = await randomizer_service.generate_seed(
        randomizer_type=tournament.randomizer,
        settings=preset.settings or {}
    )
    
    return {
        "seed": result.seed,
        "permalink": result.permalink,
        "preset_used": {
            "id": preset.id,
            "name": preset.name,
        }
    }
```

## Discord Bot Command Example

For Discord bot integration in `discordbot/commands/tournaments.py`:

```python
from discord import app_commands
import discord
from application.services.tournaments.preset_selection_service import PresetSelectionService

@app_commands.command(name="genseed", description="Generate a seed for your match")
async def generate_seed_command(
    interaction: discord.Interaction,
    match_id: int,
    game_number: int = 1
):
    """
    Generate a seed for a tournament match.
    
    Automatically selects preset based on tournament rules.
    """
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Load match and tournament
        match = await Match.get_or_none(id=match_id).prefetch_related('tournament')
        if not match:
            await interaction.followup.send("Match not found", ephemeral=True)
            return
        
        tournament = match.tournament
        
        # Get player settings (lookup Discord user in database)
        user = await User.get_or_none(discord_id=interaction.user.id)
        player_settings = None
        if user:
            settings_service = TournamentMatchSettingsService()
            player_settings = await settings_service.get_submission(
                match_id=match_id,
                user_id=user.id,
                game_number=game_number
            )
        
        # Select preset
        selection_service = PresetSelectionService()
        preset_id = await selection_service.select_preset_for_match(
            match=match,
            tournament=tournament,
            game_number=game_number,
            player_settings=player_settings
        )
        
        if not preset_id:
            await interaction.followup.send(
                "No preset configured for this tournament",
                ephemeral=True
            )
            return
        
        # Load preset
        preset = await RandomizerPreset.get_or_none(id=preset_id)
        if not preset:
            await interaction.followup.send(
                "Selected preset not found",
                ephemeral=True
            )
            return
        
        # Generate seed
        randomizer_service = RandomizerService()
        result = await randomizer_service.generate_seed(
            randomizer_type=tournament.randomizer,
            settings=preset.settings or {}
        )
        
        # Create embed response
        embed = discord.Embed(
            title=f"Seed Generated for {match.title}",
            color=discord.Color.green()
        )
        embed.add_field(name="Seed", value=f"`{result.seed}`", inline=False)
        embed.add_field(name="Permalink", value=result.permalink, inline=False)
        embed.add_field(name="Preset Used", value=preset.name, inline=False)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error("Error generating seed: %s", e, exc_info=True)
        await interaction.followup.send(
            f"Error generating seed: {str(e)}",
            ephemeral=True
        )
```

## Testing Example

Example test cases for the integration:

```python
import pytest
from datetime import datetime, timezone
from models import Match, Tournament, RandomizerPreset, TournamentMatchSettings
from application.services.tournaments.preset_selection_service import PresetSelectionService

@pytest.mark.asyncio
async def test_preset_selection_with_round_condition(tournament, match, preset_beginner, preset_advanced):
    """Test preset selection based on round number."""
    # Configure rules: use beginner preset for rounds 1-2, advanced for 3+
    tournament.preset_selection_rules = {
        "rules": [
            {
                "name": "Beginner rounds",
                "conditions": {
                    "type": "condition",
                    "field": "match.round_number",
                    "operator": "<=",
                    "value": 2
                },
                "preset_id": preset_beginner.id
            },
            {
                "name": "Advanced rounds",
                "conditions": {
                    "type": "condition",
                    "field": "match.round_number",
                    "operator": ">",
                    "value": 2
                },
                "preset_id": preset_advanced.id
            }
        ]
    }
    await tournament.save()
    
    # Test round 1 - should use beginner
    match.round_number = 1
    await match.save()
    
    service = PresetSelectionService()
    preset_id = await service.select_preset_for_match(
        match=match,
        tournament=tournament,
        game_number=1
    )
    
    assert preset_id == preset_beginner.id
    
    # Test round 4 - should use advanced
    match.round_number = 4
    await match.save()
    
    preset_id = await service.select_preset_for_match(
        match=match,
        tournament=tournament,
        game_number=1
    )
    
    assert preset_id == preset_advanced.id

@pytest.mark.asyncio
async def test_preset_selection_with_player_settings(tournament, match, preset_normal, preset_hard, user):
    """Test preset selection based on player-submitted settings."""
    # Configure rules: use hard preset if player selected hard difficulty
    tournament.preset_selection_rules = {
        "rules": [
            {
                "name": "Hard mode requested",
                "conditions": {
                    "type": "condition",
                    "field": "settings.difficulty",
                    "operator": "equals",
                    "value": "hard"
                },
                "preset_id": preset_hard.id
            }
        ]
    }
    await tournament.save()
    
    # Create player settings submission with hard difficulty
    player_settings = await TournamentMatchSettings.create(
        match=match,
        game_number=1,
        submitted_by=user,
        settings={"difficulty": "hard", "other_option": "value"}
    )
    
    service = PresetSelectionService()
    preset_id = await service.select_preset_for_match(
        match=match,
        tournament=tournament,
        game_number=1,
        player_settings=player_settings
    )
    
    assert preset_id == preset_hard.id

@pytest.mark.asyncio
async def test_preset_selection_with_complex_conditions(tournament, match, preset_weekend, preset_default):
    """Test preset selection with complex AND/OR conditions."""
    # Configure rules: use weekend preset if it's Saturday or Sunday after 6 PM
    tournament.preset_selection_rules = {
        "rules": [
            {
                "name": "Weekend evening",
                "conditions": {
                    "type": "AND",
                    "conditions": [
                        {
                            "type": "OR",
                            "conditions": [
                                {
                                    "type": "condition",
                                    "field": "match.scheduled_at.day_of_week",
                                    "operator": "equals",
                                    "value": "Saturday"
                                },
                                {
                                    "type": "condition",
                                    "field": "match.scheduled_at.day_of_week",
                                    "operator": "equals",
                                    "value": "Sunday"
                                }
                            ]
                        },
                        {
                            "type": "condition",
                            "field": "match.scheduled_at.hour",
                            "operator": ">=",
                            "value": 18
                        }
                    ]
                },
                "preset_id": preset_weekend.id
            }
        ]
    }
    await tournament.save()
    
    # Test Saturday at 7 PM - should use weekend preset
    match.scheduled_at = datetime(2025, 11, 15, 19, 0, 0, tzinfo=timezone.utc)  # Saturday
    await match.save()
    
    service = PresetSelectionService()
    preset_id = await service.select_preset_for_match(
        match=match,
        tournament=tournament,
        game_number=1
    )
    
    assert preset_id == preset_weekend.id
    
    # Test Saturday at 4 PM - should use default
    match.scheduled_at = datetime(2025, 11, 15, 16, 0, 0, tzinfo=timezone.utc)
    await match.save()
    
    preset_id = await service.select_preset_for_match(
        match=match,
        tournament=tournament,
        game_number=1
    )
    
    assert preset_id == tournament.randomizer_preset_id  # Default
```

## Summary

The integration approach:

1. **Service Layer**: PresetSelectionService encapsulates all rule evaluation logic
2. **Minimal Changes**: Existing seed generation code needs small modifications
3. **Consistent Pattern**: Same pattern works for UI, API, and Discord bot
4. **Graceful Fallback**: Always falls back to tournament default preset
5. **Testable**: Clear separation makes testing straightforward

The key insight is that preset selection happens **before** seed generation, making it a clean separation of concerns:
- **PresetSelectionService**: "Which preset should we use?"
- **RandomizerService**: "Generate a seed with these settings"
