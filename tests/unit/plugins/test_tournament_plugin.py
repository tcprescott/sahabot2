"""
Tests for the Tournament plugin.
"""

import pytest
from plugins.builtin.tournament import TournamentPlugin
from application.plugins.manifest import PluginType, PluginCategory


class TestTournamentPlugin:
    """Tests for TournamentPlugin class."""

    @pytest.fixture
    def plugin(self):
        """Create a TournamentPlugin instance."""
        return TournamentPlugin()

    def test_plugin_id(self, plugin):
        """Test that plugin ID is correct."""
        assert plugin.plugin_id == "tournament"

    def test_manifest_id_matches_plugin_id(self, plugin):
        """Test that manifest ID matches plugin_id property."""
        assert plugin.manifest.id == plugin.plugin_id

    def test_manifest_type(self, plugin):
        """Test that plugin is marked as built-in."""
        assert plugin.manifest.type == PluginType.BUILTIN

    def test_manifest_category(self, plugin):
        """Test that plugin is categorized as competition."""
        assert plugin.manifest.category == PluginCategory.COMPETITION

    def test_enabled_by_default(self, plugin):
        """Test that plugin is enabled by default."""
        assert plugin.manifest.enabled_by_default is True

    def test_not_global_plugin(self, plugin):
        """Test that plugin is organization-scoped (not global)."""
        assert plugin.manifest.global_plugin is False

    def test_authorization_actions(self, plugin):
        """Test that authorization actions are defined."""
        actions = plugin.get_authorization_actions()

        assert "tournament:create" in actions
        assert "tournament:read" in actions
        assert "tournament:update" in actions
        assert "tournament:delete" in actions
        assert "match:create" in actions
        assert "crew:manage" in actions

    def test_menu_items(self, plugin):
        """Test that menu items are defined."""
        items = plugin.get_menu_items()

        assert len(items) == 2

        # Check tournament list item
        tournament_item = next((i for i in items if i["label"] == "Tournaments"), None)
        assert tournament_item is not None
        assert tournament_item["path"] == "/org/{org_id}/tournaments"

        # Check admin item
        admin_item = next((i for i in items if i["label"] == "Tournament Admin"), None)
        assert admin_item is not None
        assert admin_item["path"] == "/org/{org_id}/tournament-admin"

    def test_config_schema(self, plugin):
        """Test that config schema is defined."""
        schema = plugin.manifest.config_schema

        assert "properties" in schema
        assert "enable_racetime_integration" in schema["properties"]
        assert "enable_speedgaming_sync" in schema["properties"]

    @pytest.mark.asyncio
    async def test_on_load(self, plugin):
        """Test that on_load completes without error."""
        await plugin.on_load()

    @pytest.mark.asyncio
    async def test_on_unload(self, plugin):
        """Test that on_unload completes without error."""
        await plugin.on_unload()

    def test_repr(self, plugin):
        """Test string representation."""
        repr_str = repr(plugin)

        assert "TournamentPlugin" in repr_str
        assert "tournament" in repr_str
        assert "1.0.0" in repr_str

    # ─────────────────────────────────────────────────────────────
    # Full Implementation Tests
    # ─────────────────────────────────────────────────────────────

    def test_get_models_returns_models(self, plugin):
        """Test that get_models returns tournament models."""
        models = plugin.get_models()

        assert len(models) == 8

        model_names = [m.__name__ for m in models]
        assert "Tournament" in model_names
        assert "Match" in model_names
        assert "MatchPlayers" in model_names
        assert "MatchSeed" in model_names
        assert "TournamentPlayers" in model_names
        assert "StreamChannel" in model_names
        assert "Crew" in model_names
        assert "TournamentMatchSettings" in model_names

    def test_get_api_router_returns_router(self, plugin):
        """Test that get_api_router returns a FastAPI router."""
        router = plugin.get_api_router()

        assert router is not None
        # Check it's a FastAPI router
        from fastapi import APIRouter

        assert isinstance(router, APIRouter)

    def test_get_pages_returns_pages(self, plugin):
        """Test that get_pages returns page definitions."""
        pages = plugin.get_pages()

        assert len(pages) == 4

        paths = [p["path"] for p in pages]
        assert "/org/{org_id}/tournaments" in paths
        assert "/org/{org_id}/tournaments/{tournament_id}" in paths
        assert "/org/{org_id}/tournament-admin" in paths
        assert "/org/{org_id}/tournament-admin/{tournament_id}" in paths

    def test_get_event_types_returns_events(self, plugin):
        """Test that get_event_types returns event classes."""
        events = plugin.get_event_types()

        assert len(events) == 14

        event_names = [e.__name__ for e in events]
        assert "TournamentCreatedEvent" in event_names
        assert "TournamentUpdatedEvent" in event_names
        assert "TournamentDeletedEvent" in event_names
        assert "MatchScheduledEvent" in event_names
        assert "MatchCompletedEvent" in event_names
        assert "CrewAddedEvent" in event_names
        assert "CrewApprovedEvent" in event_names
        assert "CrewRemovedEvent" in event_names
