"""
Unit tests for BasePage component.

Tests the helper methods and functionality of the BasePage class.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from components.base_page import BasePage


@pytest.mark.unit
class TestBasePage:
    """Test BasePage helper methods."""

    @pytest.mark.asyncio
    async def test_load_view_into_container_with_async_render(self):
        """Test load_view_into_container with an async render method."""
        # Create a BasePage instance
        page = BasePage(title="Test Page")

        # Create a mock container
        mock_container = Mock()
        mock_container.clear = Mock()
        page._dynamic_content_container = mock_container

        # Create a mock view with async render
        mock_view = Mock()
        mock_view.render = AsyncMock()

        # Mock the context manager for 'with container'
        mock_container.__enter__ = Mock(return_value=mock_container)
        mock_container.__exit__ = Mock(return_value=None)

        # Call the method
        await page.load_view_into_container(mock_view)

        # Verify container was cleared
        mock_container.clear.assert_called_once()

        # Verify render was called
        mock_view.render.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_view_into_container_with_sync_render(self):
        """Test load_view_into_container with a synchronous render method."""
        # Create a BasePage instance
        page = BasePage(title="Test Page")

        # Create a mock container
        mock_container = Mock()
        mock_container.clear = Mock()
        page._dynamic_content_container = mock_container

        # Create a mock view with sync render
        mock_view = Mock()
        mock_view.render = Mock()

        # Mock the context manager for 'with container'
        mock_container.__enter__ = Mock(return_value=mock_container)
        mock_container.__exit__ = Mock(return_value=None)

        # Call the method
        await page.load_view_into_container(mock_view)

        # Verify container was cleared
        mock_container.clear.assert_called_once()

        # Verify render was called
        mock_view.render.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_view_into_container_no_container(self):
        """Test load_view_into_container when no container exists."""
        # Create a BasePage instance
        page = BasePage(title="Test Page")
        page._dynamic_content_container = None

        # Create a mock view
        mock_view = Mock()
        mock_view.render = AsyncMock()

        # Call the method - should handle gracefully
        await page.load_view_into_container(mock_view)

        # Verify render was not called since no container
        mock_view.render.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_view_into_container_no_render_method(self):
        """Test load_view_into_container with a view that has no render method."""
        # Create a BasePage instance
        page = BasePage(title="Test Page")

        # Create a mock container
        mock_container = Mock()
        mock_container.clear = Mock()
        page._dynamic_content_container = mock_container

        # Create a mock view without render method
        mock_view = Mock(spec=[])

        # Mock the context manager for 'with container'
        mock_container.__enter__ = Mock(return_value=mock_container)
        mock_container.__exit__ = Mock(return_value=None)

        # Call the method - should handle gracefully
        await page.load_view_into_container(mock_view)

        # Verify container was cleared
        mock_container.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_dynamic_content_container(self):
        """Test getting the dynamic content container."""
        page = BasePage(title="Test Page")

        # Initially should be None
        assert page.get_dynamic_content_container() is None

        # Set a container
        mock_container = Mock()
        page._dynamic_content_container = mock_container

        # Should return the container
        assert page.get_dynamic_content_container() is mock_container
