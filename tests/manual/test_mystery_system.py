#!/usr/bin/env python3
"""
Simple test script to verify mystery weightset system functionality.

This script tests the mystery generation logic without requiring database access.
"""

import sys
import os

# Add parent directory to path so we can import from application
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from application.services.randomizer.alttpr_mystery_service import ALTTPRMysteryService


def test_basic_mystery():
    """Test basic mystery weight rolling."""
    print("Testing basic mystery weight rolling...")

    service = ALTTPRMysteryService()

    mystery_weights = {
        'weights': {
            'open': 10,
            'standard': 5,
            'inverted': 3
        }
    }

    # Validate
    is_valid, error = service.validate_mystery_weights(mystery_weights)
    print(f"  Validation: {'✓ PASS' if is_valid else '✗ FAIL'}")
    if error:
        print(f"  Error: {error}")
        return False

    # Roll settings 5 times
    print("  Rolling 5 times:")
    for i in range(5):
        settings, description = service._roll_mystery_settings(mystery_weights)
        print(f"    Roll {i+1}: {description}")

    return True


def test_mystery_with_subweights():
    """Test mystery with subweights."""
    print("\nTesting mystery with subweights...")

    service = ALTTPRMysteryService()

    mystery_weights = {
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

    # Validate
    is_valid, error = service.validate_mystery_weights(mystery_weights)
    print(f"  Validation: {'✓ PASS' if is_valid else '✗ FAIL'}")
    if error:
        print(f"  Error: {error}")
        return False

    # Roll settings 5 times
    print("  Rolling 5 times:")
    for i in range(5):
        settings, description = service._roll_mystery_settings(mystery_weights)
        print(f"    Roll {i+1}: {description}")

    return True


def test_mystery_with_entrance():
    """Test mystery with entrance weights."""
    print("\nTesting mystery with entrance weights...")

    service = ALTTPRMysteryService()

    mystery_weights = {
        'weights': {
            'open': 10
        },
        'entrance_weights': {
            'none': 5,
            'simple': 3,
            'restricted': 1
        }
    }

    # Validate
    is_valid, error = service.validate_mystery_weights(mystery_weights)
    print(f"  Validation: {'✓ PASS' if is_valid else '✗ FAIL'}")
    if error:
        print(f"  Error: {error}")
        return False

    # Roll settings 5 times
    print("  Rolling 5 times:")
    for i in range(5):
        settings, description = service._roll_mystery_settings(mystery_weights)
        print(f"    Roll {i+1}: {description}")

    return True


def test_mystery_with_customizer():
    """Test mystery with customizer settings."""
    print("\nTesting mystery with customizer...")

    service = ALTTPRMysteryService()

    mystery_weights = {
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

    # Validate
    is_valid, error = service.validate_mystery_weights(mystery_weights)
    print(f"  Validation: {'✓ PASS' if is_valid else '✗ FAIL'}")
    if error:
        print(f"  Error: {error}")
        return False

    # Roll settings 5 times
    print("  Rolling 5 times:")
    for i in range(5):
        settings, description = service._roll_mystery_settings(mystery_weights)
        print(f"    Roll {i+1}: {description}")

    return True


def test_invalid_mystery():
    """Test validation of invalid mystery weights."""
    print("\nTesting invalid mystery validation...")

    service = ALTTPRMysteryService()

    # Empty mystery
    is_valid, error = service.validate_mystery_weights({})
    print(f"  Empty mystery: {'✓ PASS (correctly rejected)' if not is_valid else '✗ FAIL (should reject)'}")
    if error:
        print(f"    Error message: {error}")

    # Non-dict mystery
    is_valid, error = service.validate_mystery_weights("not a dict")
    print(f"  Non-dict mystery: {'✓ PASS (correctly rejected)' if not is_valid else '✗ FAIL (should reject)'}")
    if error:
        print(f"    Error message: {error}")

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("MYSTERY WEIGHTSET SYSTEM VERIFICATION")
    print("=" * 60)

    tests = [
        test_basic_mystery,
        test_mystery_with_subweights,
        test_mystery_with_entrance,
        test_mystery_with_customizer,
        test_invalid_mystery,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    return all(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
