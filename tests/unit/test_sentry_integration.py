"""
Unit tests for Sentry integration.

Tests Sentry initialization and configuration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from config import settings


@pytest.mark.unit
class TestSentryIntegration:
    """Test cases for Sentry integration."""

    @patch('application.utils.sentry_init.sentry_sdk')
    def test_sentry_init_with_dsn(self, mock_sentry_sdk):
        """Test Sentry initialization when DSN is configured."""
        # Arrange
        with patch.object(settings, 'SENTRY_DSN', 'https://example@sentry.io/123'):
            with patch.object(settings, 'SENTRY_ENVIRONMENT', 'test'):
                with patch.object(settings, 'SENTRY_TRACES_SAMPLE_RATE', 1.0):
                    with patch.object(settings, 'SENTRY_PROFILES_SAMPLE_RATE', 1.0):
                        # Import here to ensure patching works
                        from application.utils.sentry_init import init_sentry

                        # Act
                        init_sentry()

                        # Assert
                        mock_sentry_sdk.init.assert_called_once()
                        call_kwargs = mock_sentry_sdk.init.call_args[1]
                        assert call_kwargs['dsn'] == 'https://example@sentry.io/123'
                        assert call_kwargs['environment'] == 'test'
                        assert call_kwargs['traces_sample_rate'] == 1.0
                        assert call_kwargs['profiles_sample_rate'] == 1.0
                        assert call_kwargs['send_default_pii'] is True
                        assert call_kwargs['attach_stacktrace'] is True

    @patch('application.utils.sentry_init.sentry_sdk')
    @patch('application.utils.sentry_init.logger')
    def test_sentry_init_without_dsn(self, mock_logger, mock_sentry_sdk):
        """Test Sentry initialization when DSN is not configured."""
        # Arrange
        with patch.object(settings, 'SENTRY_DSN', None):
            # Import here to ensure patching works
            from application.utils.sentry_init import init_sentry

            # Act
            init_sentry()

            # Assert
            mock_sentry_sdk.init.assert_not_called()
            mock_logger.info.assert_called_once()
            assert "not configured" in mock_logger.info.call_args[0][0]

    @patch('application.utils.sentry_init.sentry_sdk')
    @patch('application.utils.sentry_init.logger')
    def test_sentry_init_uses_environment_fallback(self, mock_logger, mock_sentry_sdk):
        """Test Sentry uses ENVIRONMENT setting when SENTRY_ENVIRONMENT is not set."""
        # Arrange
        with patch.object(settings, 'SENTRY_DSN', 'https://example@sentry.io/123'):
            with patch.object(settings, 'SENTRY_ENVIRONMENT', None):
                with patch.object(settings, 'ENVIRONMENT', 'production'):
                    # Import here to ensure patching works
                    from application.utils.sentry_init import init_sentry

                    # Act
                    init_sentry()

                    # Assert
                    call_kwargs = mock_sentry_sdk.init.call_args[1]
                    assert call_kwargs['environment'] == 'production'

    @patch('application.utils.sentry_init.sentry_sdk')
    @patch('application.utils.sentry_init.logger')
    def test_sentry_init_handles_exception(self, mock_logger, mock_sentry_sdk):
        """Test Sentry initialization handles exceptions gracefully."""
        # Arrange
        mock_sentry_sdk.init.side_effect = Exception("Test error")
        with patch.object(settings, 'SENTRY_DSN', 'https://example@sentry.io/123'):
            # Import here to ensure patching works
            from application.utils.sentry_init import init_sentry

            # Act - should not raise exception
            init_sentry()

            # Assert
            mock_logger.error.assert_called_once()
            assert "Failed to initialize Sentry" in mock_logger.error.call_args[0][0]

    @patch('application.utils.sentry_init.sentry_sdk')
    def test_sentry_integrations_configured(self, mock_sentry_sdk):
        """Test Sentry integrations are properly configured."""
        # Arrange
        with patch.object(settings, 'SENTRY_DSN', 'https://example@sentry.io/123'):
            # Import here to ensure patching works
            from application.utils.sentry_init import init_sentry

            # Act
            init_sentry()

            # Assert
            call_kwargs = mock_sentry_sdk.init.call_args[1]
            integrations = call_kwargs['integrations']
            assert len(integrations) == 3  # FastAPI, Asyncio, Logging
            integration_types = [type(i).__name__ for i in integrations]
            assert 'FastApiIntegration' in integration_types
            assert 'AsyncioIntegration' in integration_types
            assert 'LoggingIntegration' in integration_types
