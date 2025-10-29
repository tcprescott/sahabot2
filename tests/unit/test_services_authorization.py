"""
Unit tests for AuthorizationService.

Tests the authorization logic.
"""

import pytest
from application.services.authorization_service import AuthorizationService
from models.user import Permission


@pytest.mark.unit
class TestAuthorizationService:
    """Test cases for AuthorizationService."""
    
    def test_can_access_admin_panel_admin(self, admin_user):
        """Test admin can access admin panel."""
        # TODO: Implement test
        pass
    
    def test_can_access_admin_panel_user(self, sample_user):
        """Test regular user cannot access admin panel."""
        # TODO: Implement test
        pass
    
    def test_can_moderate_user_moderator(self):
        """Test moderator can moderate users."""
        # TODO: Implement test
        pass
    
    def test_permission_hierarchy(self):
        """Test permission hierarchy logic."""
        # TODO: Implement test
        pass
