"""
Tests for the AsyncQualifier plugin.
"""

import pytest
from plugins.builtin.async_qualifier import AsyncQualifierPlugin
from application.plugins.manifest import PluginType, PluginCategory


class TestAsyncQualifierPlugin:
    """Tests for AsyncQualifierPlugin class."""

    @pytest.fixture
    def plugin(self):
        """Create an AsyncQualifierPlugin instance."""
        return AsyncQualifierPlugin()

    def test_plugin_id(self, plugin):
        """Test that plugin ID is correct."""
        assert plugin.plugin_id == "async_qualifier"

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

        assert "async_qualifier:create" in actions
        assert "async_qualifier:read" in actions
        assert "async_qualifier:update" in actions
        assert "async_qualifier:delete" in actions
        assert "async_race:submit" in actions
        assert "async_race:review" in actions
        assert "async_live_race:create" in actions
        assert "async_live_race:manage" in actions

    def test_menu_items(self, plugin):
        """Test that menu items are defined."""
        items = plugin.get_menu_items()

        assert len(items) == 2

        # Check async qualifier list item
        async_item = next((i for i in items if i["label"] == "Async Qualifiers"), None)
        assert async_item is not None
        assert async_item["path"] == "/org/{org_id}/async"

        # Check admin item
        admin_item = next((i for i in items if i["label"] == "Async Admin"), None)
        assert admin_item is not None
        assert admin_item["path"] == "/org/{org_id}/async-admin"

    def test_config_schema(self, plugin):
        """Test that config schema is defined."""
        schema = plugin.manifest.config_schema

        assert "properties" in schema
        assert "enable_live_races" in schema["properties"]
        assert "enable_discord_integration" in schema["properties"]
        assert "default_runs_per_pool" in schema["properties"]
        assert "race_timeout_minutes" in schema["properties"]

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

        assert "AsyncQualifierPlugin" in repr_str
        assert "async_qualifier" in repr_str
        assert "1.0.0" in repr_str

    # ─────────────────────────────────────────────────────────────
    # Full Implementation Tests
    # ─────────────────────────────────────────────────────────────

    def test_get_models_returns_models(self, plugin):
        """Test that get_models returns async qualifier models."""
        models = plugin.get_models()

        assert len(models) == 6

        model_names = [m.__name__ for m in models]
        assert "AsyncQualifier" in model_names
        assert "AsyncQualifierPool" in model_names
        assert "AsyncQualifierPermalink" in model_names
        assert "AsyncQualifierRace" in model_names
        assert "AsyncQualifierLiveRace" in model_names
        assert "AsyncQualifierAuditLog" in model_names

    def test_get_api_router_returns_router(self, plugin):
        """Test that get_api_router returns a FastAPI router."""
        router = plugin.get_api_router()

        assert router is not None
        # Check it's a FastAPI router
        from fastapi import APIRouter

        assert isinstance(router, APIRouter)

    def test_get_additional_routers(self, plugin):
        """Test that get_additional_routers returns the live races router."""
        routers = plugin.get_additional_routers()

        assert len(routers) == 1
        from fastapi import APIRouter

        assert isinstance(routers[0], APIRouter)

    def test_get_pages_returns_pages(self, plugin):
        """Test that get_pages returns page definitions."""
        pages = plugin.get_pages()

        assert len(pages) == 4

        paths = [p["path"] for p in pages]
        assert "/org/{org_id}/async" in paths
        assert "/org/{org_id}/async/{qualifier_id}" in paths
        assert "/org/{org_id}/async-admin" in paths
        assert "/org/{org_id}/async-admin/{qualifier_id}" in paths

    def test_get_event_types_returns_events(self, plugin):
        """Test that get_event_types returns event classes."""
        events = plugin.get_event_types()

        assert len(events) == 9

        event_names = [e.__name__ for e in events]
        assert "RaceSubmittedEvent" in event_names
        assert "RaceApprovedEvent" in event_names
        assert "RaceRejectedEvent" in event_names
        assert "AsyncLiveRaceCreatedEvent" in event_names
        assert "AsyncLiveRaceStartedEvent" in event_names
        assert "AsyncLiveRaceFinishedEvent" in event_names
        assert "AsyncLiveRaceCancelledEvent" in event_names

    def test_get_discord_commands_returns_empty(self, plugin):
        """Test that get_discord_commands returns empty (not migrated yet)."""
        commands = plugin.get_discord_commands()

        # Commands not migrated yet
        assert commands == []
