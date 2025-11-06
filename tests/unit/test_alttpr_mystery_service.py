"""
Tests for ALTTPR Mystery Service.
"""

import pytest
from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService


class TestALTTPRMysteryService:
    """Test suite for ALTTPR mystery service."""

    @pytest.fixture
    def service(self):
        """Create a mystery service instance."""
        return ALTTPRMysteryService()

    @pytest.fixture
    def basic_mystery_weights(self):
        """Create basic mystery weights for testing."""
        return {
            'weights': {
                'open': 10,
                'standard': 5,
                'inverted': 3
            }
        }

    @pytest.fixture
    def mystery_weights_with_subweights(self):
        """Create mystery weights with subweights."""
        return {
            'weights': {
                'open': 10,
                'standard': 5
            },
            'subweights': {
                'open': {
                    'normal': 5,
                    'hard': 3
                }
            }
        }

    @pytest.fixture
    def mystery_weights_with_entrance(self):
        """Create mystery weights with entrance shuffle."""
        return {
            'weights': {
                'open': 10
            },
            'entrance_weights': {
                'none': 5,
                'simple': 3,
                'restricted': 1
            }
        }

    @pytest.fixture
    def mystery_weights_with_customizer(self):
        """Create mystery weights with customizer settings."""
        return {
            'weights': {
                'open': 10
            },
            'customizer': {
                'eq': {
                    'progressive': 5,
                    'basic': 3
                },
                'item_pool': {
                    'normal': 7,
                    'hard': 2
                }
            }
        }

    def test_validate_mystery_weights_basic(self, service, basic_mystery_weights):
        """Test validation of basic mystery weights."""
        is_valid, error = service.validate_mystery_weights(basic_mystery_weights)
        assert is_valid is True
        assert error is None

    def test_validate_mystery_weights_empty(self, service):
        """Test validation fails for empty weights."""
        is_valid, error = service.validate_mystery_weights({})
        assert is_valid is False
        assert error is not None

    def test_validate_mystery_weights_invalid_type(self, service):
        """Test validation fails for non-dict weights."""
        is_valid, error = service.validate_mystery_weights("not a dict")
        assert is_valid is False
        assert error is not None

    def test_validate_mystery_weights_with_subweights(self, service, mystery_weights_with_subweights):
        """Test validation of mystery weights with subweights."""
        is_valid, error = service.validate_mystery_weights(mystery_weights_with_subweights)
        assert is_valid is True
        assert error is None

    def test_validate_mystery_weights_with_entrance(self, service, mystery_weights_with_entrance):
        """Test validation of mystery weights with entrance shuffle."""
        is_valid, error = service.validate_mystery_weights(mystery_weights_with_entrance)
        assert is_valid is True
        assert error is None

    def test_validate_mystery_weights_with_customizer(self, service, mystery_weights_with_customizer):
        """Test validation of mystery weights with customizer."""
        is_valid, error = service.validate_mystery_weights(mystery_weights_with_customizer)
        assert is_valid is True
        assert error is None

    def test_roll_mystery_settings_basic(self, service, basic_mystery_weights):
        """Test rolling basic mystery settings."""
        settings, description = service._roll_mystery_settings(basic_mystery_weights)

        # Should have rolled a preset
        assert 'preset' in description
        assert description['preset'] in ['open', 'standard', 'inverted']

        # Settings should be a dict (may be empty for basic weights)
        assert isinstance(settings, dict)

    def test_roll_mystery_settings_with_subweights(self, service, mystery_weights_with_subweights):
        """Test rolling mystery settings with subweights."""
        # Roll multiple times to check consistency
        for _ in range(5):
            settings, description = service._roll_mystery_settings(mystery_weights_with_subweights)

            # Should have rolled a preset
            assert 'preset' in description
            assert description['preset'] in ['open', 'standard']

            # If preset is 'open', should have rolled subweight
            if description['preset'] == 'open':
                assert 'subweight' in description
                assert description['subweight'] in ['normal', 'hard']

    def test_roll_mystery_settings_with_entrance(self, service, mystery_weights_with_entrance):
        """Test rolling mystery settings with entrance shuffle."""
        settings, description = service._roll_mystery_settings(mystery_weights_with_entrance)

        # Should have rolled entrance
        if 'entrance' in description:
            assert description['entrance'] in ['none', 'simple', 'restricted']
            if description['entrance'] != 'none':
                assert 'entrance_shuffle' in settings

    def test_roll_mystery_settings_with_customizer(self, service, mystery_weights_with_customizer):
        """Test rolling mystery settings with customizer."""
        settings, description = service._roll_mystery_settings(mystery_weights_with_customizer)

        # Should have rolled customizer settings
        if 'customizer' in description:
            assert description['customizer'] == 'yes'
            # At least one customizer setting should be in settings
            assert any(key in settings for key in ['eq', 'item_pool'])

    def test_weighted_random_choice(self, service):
        """Test weighted random choice."""
        weights = {
            'option_a': 10,
            'option_b': 5,
            'option_c': 1
        }

        # Test that it returns valid options
        for _ in range(10):
            choice = service._weighted_random_choice(weights)
            assert choice in ['option_a', 'option_b', 'option_c']

    def test_weighted_random_choice_empty_raises(self, service):
        """Test weighted random choice raises on empty weights."""
        with pytest.raises(ValueError):
            service._weighted_random_choice({})

    def test_weighted_random_choice_zero_weights_raises(self, service):
        """Test weighted random choice raises on zero weights."""
        with pytest.raises(ValueError):
            service._weighted_random_choice({'option': 0})

    def test_roll_weighted_preset_basic(self, service):
        """Test rolling weighted preset with numeric weights."""
        weights = {
            'open': 10,
            'standard': 5
        }

        preset_name, settings = service._roll_weighted_preset(weights)
        assert preset_name in ['open', 'standard']
        assert isinstance(settings, dict)

    def test_roll_weighted_preset_with_settings(self, service):
        """Test rolling weighted preset with settings dicts."""
        weights = {
            'open': {'weight': 10, 'mode': 'open', 'goal': 'ganon'},
            'standard': {'weight': 5, 'mode': 'standard', 'goal': 'ganon'}
        }

        preset_name, settings = service._roll_weighted_preset(weights)
        assert preset_name in ['open', 'standard']
        assert isinstance(settings, dict)
        if preset_name == 'open':
            assert settings.get('mode') == 'open'

    def test_roll_weighted_value(self, service):
        """Test rolling weighted value."""
        weights = {
            'value_a': 10,
            'value_b': 5
        }

        value = service._roll_weighted_value(weights)
        assert value in ['value_a', 'value_b']

    def test_roll_weighted_value_empty(self, service):
        """Test rolling weighted value with empty weights returns None."""
        value = service._roll_weighted_value({})
        assert value is None

    def test_roll_customizer_settings(self, service):
        """Test rolling customizer settings."""
        customizer = {
            'eq': {
                'progressive': 5,
                'basic': 3
            },
            'item_pool': {
                'normal': 7,
                'hard': 2
            }
        }

        settings = service._roll_customizer_settings(customizer)
        assert isinstance(settings, dict)
        # Should have rolled settings for each section
        if 'eq' in settings:
            assert settings['eq'] in ['progressive', 'basic']
        if 'item_pool' in settings:
            assert settings['item_pool'] in ['normal', 'hard']
