"""
Preset management pages.

This module provides UI pages for managing presets and namespaces.
"""

import logging
from nicegui import ui, app
from components.base_page import BasePage
from views.presets import (
    PresetListView,
    PresetEditView,
    PresetNamespaceView
)
from application.services.preset_service import PresetService

logger = logging.getLogger(__name__)


def register():
    """Register preset pages."""

    @ui.page('/presets')
    async def presets_list():
        """List all public presets."""
        base = BasePage.simple_page(
            title="Presets",
            active_nav="presets"
        )

        async def content(page: BasePage):
            """Render presets list content."""
            service = PresetService()

            # Get current user if authenticated
            user = None
            if app.storage.user.get('discord_id'):
                from models.user import User
                user = await User.get_or_none(discord_id=app.storage.user['discord_id'])

            view = PresetListView(service, user)
            await view.render()

        await base.render(content)()

    @ui.page('/presets/my')
    async def my_presets():
        """List user's personal presets."""
        base = BasePage.authenticated_page(
            title="My Presets",
            active_nav="presets"
        )

        async def content(page: BasePage):
            """Render user's presets."""
            service = PresetService()

            # Get user's namespace
            namespace_name = page.user.discord_username
            namespace = await service.get_or_create_namespace(namespace_name, page.user)

            view = PresetNamespaceView(service, namespace, page.user)
            await view.render()

        await base.render(content)()

    @ui.page('/presets/namespace/{namespace_name}')
    async def namespace_view(namespace_name: str):
        """View presets in a specific namespace."""
        base = BasePage.simple_page(
            title=f"Namespace: {namespace_name}",
            active_nav="presets"
        )

        async def content(page: BasePage):
            """Render namespace view."""
            service = PresetService()

            # Get current user if authenticated
            user = None
            if app.storage.user.get('discord_id'):
                from models.user import User
                user = await User.get_or_none(discord_id=app.storage.user['discord_id'])

            # Get namespace
            namespace = await service.get_namespace(namespace_name)
            if not namespace:
                ui.label(f'Namespace "{namespace_name}" not found.').classes('text-lg text-center mt-8')
                return

            # Check if namespace is accessible
            if not namespace.is_public:
                if not user or not service.is_namespace_owner(user, namespace):
                    ui.label('This namespace is private.').classes('text-lg text-center mt-8')
                    return

            view = PresetNamespaceView(service, namespace, user)
            await view.render()

        await base.render(content)()

    @ui.page('/presets/edit/{preset_id}')
    async def edit_preset(preset_id: int):
        """Edit a specific preset."""
        base = BasePage.authenticated_page(
            title="Edit Preset",
            active_nav="presets"
        )

        async def content(page: BasePage):
            """Render preset editor."""
            service = PresetService()

            # Get preset
            from application.repositories.preset_repository import PresetRepository
            repository = PresetRepository()
            preset = await repository.get_preset_by_id(preset_id)

            if not preset:
                ui.label('Preset not found.').classes('text-lg text-center mt-8')
                return

            # Check permissions
            await preset.fetch_related('namespace')
            if not await service.can_edit_namespace(page.user, preset.namespace):
                ui.label('You do not have permission to edit this preset.').classes(
                    'text-lg text-center mt-8'
                )
                return

            view = PresetEditView(service, preset, page.user)
            await view.render()

        await base.render(content)()

    @ui.page('/presets/create')
    async def create_preset():
        """Create a new preset."""
        base = BasePage.authenticated_page(
            title="Create Preset",
            active_nav="presets"
        )

        async def content(page: BasePage):
            """Render preset creation form."""
            service = PresetService()

            # Get user's namespace (default)
            namespace_name = page.user.discord_username
            namespace = await service.get_or_create_namespace(namespace_name, page.user)

            # Use empty preset for creation
            from models.preset import Preset
            preset = Preset(
                namespace=namespace,
                preset_name="",
                randomizer="alttpr",
                content=""
            )

            view = PresetEditView(service, preset, page.user, is_create=True)
            await view.render()

        await base.render(content)()

    logger.info("Preset pages registered")
