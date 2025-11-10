"""
Example working test to demonstrate test structure.

This test can be run immediately to verify the test setup works.
"""

import pytest


@pytest.mark.unit
class TestExample:
    """Example test class to verify pytest is working."""

    def test_example_passes(self):
        """Simple test that always passes."""
        assert True

    def test_example_math(self):
        """Test basic math operations."""
        assert 1 + 1 == 2
        assert 2 * 3 == 6

    @pytest.mark.asyncio
    async def test_example_async(self):
        """Test async functionality works."""

        async def async_function():
            return "async works"

        result = await async_function()
        assert result == "async works"

    def test_example_with_fixture(self, discord_user_payload):
        """Test using a fixture from conftest."""
        assert discord_user_payload["id"] == "123456789012345678"
        assert discord_user_payload["username"] == "testuser"
