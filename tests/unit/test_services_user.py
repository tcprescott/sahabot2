"""
Unit tests for UserService.

Tests the business logic layer for User operations.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from application.services.user_service import UserService
from models import User, Permission


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserService:
    """Test cases for UserService."""

    async def test_get_all_users(self):
        """Test retrieving all users."""
        # TODO: Implement test with mocked repository
        pass

    async def test_get_user_by_id(self):
        """Test retrieving user by ID."""
        # TODO: Implement test with mocked repository
        pass

    async def test_get_user_by_discord_id(self):
        """Test retrieving user by Discord ID."""
        # TODO: Implement test with mocked repository
        pass

    async def test_create_user_from_discord(self):
        """Test creating user from Discord data."""
        # TODO: Implement test with mocked repository
        pass

    async def test_update_user_permission(self):
        """Test updating user permission."""
        # TODO: Implement test with mocked repository
        pass

    async def test_deactivate_user(self):
        """Test deactivating a user."""
        # TODO: Implement test with mocked repository
        pass

    async def test_update_user_email_valid(self):
        """Test updating user email with valid email address."""
        service = UserService()

        # Create mock user
        user = MagicMock(spec=User)
        user.id = 1
        user.email = None
        user.email_verified = False
        user.email_verification_token = None
        user.email_verified_at = None
        user.save = AsyncMock()

        # Update email
        result = await service.update_user_email(user, "test@example.com")

        # Verify email was set and normalized
        assert user.email == "test@example.com"
        assert user.email_verified is True  # Auto-verified in stub
        assert user.email_verified_at is not None
        assert user.save.called

    async def test_update_user_email_invalid_format(self):
        """Test updating user email with invalid format raises ValueError."""
        service = UserService()

        # Create mock user
        user = MagicMock(spec=User)
        user.id = 1
        user.save = AsyncMock()

        # Test various invalid formats
        invalid_emails = [
            "not-an-email",  # No @ symbol
            "@example.com",  # No local part
            "user@",  # No domain
            "user@@example.com",  # Multiple @ symbols
            "user@domain",  # No TLD
        ]

        for invalid_email in invalid_emails:
            with pytest.raises(ValueError, match="Invalid email format"):
                await service.update_user_email(user, invalid_email)

    async def test_update_user_email_invalid_type(self):
        """Test updating user email with non-string type raises ValueError."""
        service = UserService()

        # Create mock user
        user = MagicMock(spec=User)
        user.id = 1
        user.save = AsyncMock()

        # Test invalid types
        with pytest.raises(ValueError, match="Email must be a string"):
            await service.update_user_email(user, 123)

        with pytest.raises(ValueError, match="Email must be a string"):
            await service.update_user_email(user, ["email@example.com"])

    async def test_update_user_email_clear(self):
        """Test clearing user email."""
        service = UserService()

        # Create mock user with existing email
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "old@example.com"
        user.email_verified = True
        user.email_verification_token = "token"
        user.email_verified_at = datetime.now(timezone.utc)
        user.save = AsyncMock()

        # Clear email
        result = await service.update_user_email(user, None)

        # Verify email was cleared
        assert user.email is None
        assert user.email_verified is False
        assert user.email_verification_token is None
        assert user.email_verified_at is None
        assert user.save.called

    async def test_update_user_email_normalization(self):
        """Test email normalization (lowercase, trimmed)."""
        service = UserService()

        # Create mock user
        user = MagicMock(spec=User)
        user.id = 1
        user.save = AsyncMock()

        # Update with mixed case and whitespace
        result = await service.update_user_email(user, "  TeSt@ExAmPlE.CoM  ")

        # Verify normalization
        assert user.email == "test@example.com"

    async def test_initiate_email_verification_auto_verifies(self):
        """Test email verification initiation (stubbed to auto-verify)."""
        service = UserService()

        # Create mock user with email
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.email_verified = False
        user.save = AsyncMock()

        # Initiate verification
        token = await service.initiate_email_verification(user)

        # Verify auto-verification happened
        assert user.email_verified is True
        assert user.email_verified_at is not None
        assert user.email_verification_token is None  # Token not stored in stub
        assert user.save.called
        assert token is not None  # Token returned even if not stored

    async def test_initiate_email_verification_no_email(self):
        """Test email verification fails if no email set."""
        service = UserService()

        # Create mock user without email
        user = MagicMock(spec=User)
        user.id = 1
        user.email = None
        user.save = AsyncMock()

        # Attempt to verify
        with pytest.raises(ValueError, match="User has no email address set"):
            await service.initiate_email_verification(user)

    async def test_verify_email_stubbed(self):
        """Test email verification (stubbed to always succeed)."""
        service = UserService()

        # Create mock user
        user = MagicMock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.email_verified = False
        user.save = AsyncMock()

        # Verify email with any token
        result = await service.verify_email(user, "any-token")

        # Verify verification happened
        assert result is True
        assert user.email_verified is True
        assert user.email_verified_at is not None
        assert user.save.called
