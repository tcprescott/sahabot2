#!/usr/bin/env python3
"""
Test script for preset functionality.

This script verifies the preset implementation structure without requiring database.
"""

import sys
import inspect
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_files_exist():
    """Test that all required files exist."""
    print("\n=== Testing File Structure ===")

    base_path = Path(__file__).parent.parent

    required_files = [
        'models/randomizer_preset.py',
        'application/repositories/preset_repository.py',
        'application/services/preset_service.py',
    ]

    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✓ File exists: {file_path}")
        else:
            print(f"✗ File missing: {file_path}")
            sys.exit(1)

    print("\nAll required files exist!")


def test_model_structure():
    """Test the preset model structure."""
    print("\n=== Testing Model Structure ===")

    # Read the model file
    model_path = Path(__file__).parent.parent / 'models' / 'randomizer_preset.py'
    content = model_path.read_text()

    # Check for required components
    checks = {
        'class RandomizerPreset': 'RandomizerPreset class definition',
        'id = fields.IntField': 'id field',
        'organization = fields.ForeignKeyField': 'organization FK',
        'name = fields.CharField': 'name field',
        'randomizer = fields.CharField': 'randomizer field',
        'settings = fields.JSONField': 'settings JSON field',
        'description = fields.TextField': 'description field',
        'is_active = fields.BooleanField': 'is_active field',
        'created_at = fields.DatetimeField': 'created_at field',
        'updated_at = fields.DatetimeField': 'updated_at field',
    }

    for check, description in checks.items():
        if check in content:
            print(f"✓ {description} found")
        else:
            print(f"✗ {description} missing")
            sys.exit(1)

    print("\nModel structure is correct!")


def test_repository_structure():
    """Test the repository structure."""
    print("\n=== Testing Repository Structure ===")

    repo_path = Path(__file__).parent.parent / 'application' / 'repositories' / 'preset_repository.py'
    content = repo_path.read_text()

    checks = {
        'class PresetRepository': 'PresetRepository class',
        'async def get_by_id': 'get_by_id method',
        'async def get_by_name': 'get_by_name method',
        'async def list_by_organization': 'list_by_organization method',
        'async def create': 'create method',
        'async def update': 'update method',
        'async def delete': 'delete method',
        'organization_id': 'organization_id parameter (tenant isolation)',
    }

    for check, description in checks.items():
        if check in content:
            print(f"✓ {description} found")
        else:
            print(f"✗ {description} missing")
            sys.exit(1)

    print("\nRepository structure is correct!")


def test_service_structure():
    """Test the service structure."""
    print("\n=== Testing Service Structure ===")

    service_path = Path(__file__).parent.parent / 'application' / 'services' / 'preset_service.py'
    content = service_path.read_text()

    checks = {
        'class PresetService': 'PresetService class',
        'async def get_preset': 'get_preset method',
        'async def get_preset_by_name': 'get_preset_by_name method',
        'async def list_presets': 'list_presets method',
        'async def create_preset': 'create_preset method',
        'async def update_preset': 'update_preset method',
        'async def delete_preset': 'delete_preset method',
        'async def get_preset_settings': 'get_preset_settings convenience method',
        'organization_id': 'organization_id parameter (tenant isolation)',
    }

    for check, description in checks.items():
        if check in content:
            print(f"✓ {description} found")
        else:
            print(f"✗ {description} missing")
            sys.exit(1)

    print("\nService structure is correct!")


def test_alttpr_integration():
    """Test ALTTPR service integration."""
    print("\n=== Testing ALTTPR Integration ===")

    alttpr_path = Path(__file__).parent.parent / 'application' / 'services' / 'randomizer' / 'alttpr_service.py'
    content = alttpr_path.read_text()

    checks = {
        'async def generate_from_preset': 'generate_from_preset method',
        'preset_name': 'preset_name parameter',
        'organization_id': 'organization_id parameter',
        'PresetService': 'PresetService import/usage',
        'get_preset_settings': 'get_preset_settings call',
    }

    for check, description in checks.items():
        if check in content:
            print(f"✓ {description} found")
        else:
            print(f"✗ {description} missing")
            sys.exit(1)

    print("\nALTTPR integration is correct!")


def test_database_config():
    """Test database configuration updates."""
    print("\n=== Testing Database Configuration ===")

    # Check migrations config
    migrations_path = Path(__file__).parent.parent / 'migrations' / 'tortoise_config.py'
    migrations_content = migrations_path.read_text()

    if 'models.randomizer_preset' in migrations_content:
        print("✓ randomizer_preset added to migrations config")
    else:
        print("✗ randomizer_preset missing from migrations config")
        sys.exit(1)

    # Check database.py
    db_path = Path(__file__).parent.parent / 'database.py'
    db_content = db_path.read_text()

    if 'models.randomizer_preset' in db_content:
        print("✓ randomizer_preset added to database.py")
    else:
        print("✗ randomizer_preset missing from database.py")
        sys.exit(1)

    # Check models/__init__.py
    models_init_path = Path(__file__).parent.parent / 'models' / '__init__.py'
    models_init_content = models_init_path.read_text()

    if 'from models.randomizer_preset import RandomizerPreset' in models_init_content:
        print("✓ RandomizerPreset imported in models/__init__.py")
    else:
        print("✗ RandomizerPreset not imported in models/__init__.py")
        sys.exit(1)

    if "'RandomizerPreset'" in models_init_content:
        print("✓ RandomizerPreset exported in __all__")
    else:
        print("✗ RandomizerPreset not exported in __all__")
        sys.exit(1)

    print("\nDatabase configuration is correct!")


def main():
    """Run all tests."""
    print("Testing Preset Implementation")
    print("=" * 50)

    try:
        test_files_exist()
        test_model_structure()
        test_repository_structure()
        test_service_structure()
        test_alttpr_integration()
        test_database_config()

        print("\n" + "=" * 50)
        print("✓ All structure tests passed!")
        print("\nImplementation Summary:")
        print("- Database model: RandomizerPreset (multi-tenant)")
        print("- Repository layer: PresetRepository (data access)")
        print("- Service layer: PresetService (business logic)")
        print("- ALTTPR integration: generate_from_preset() method")
        print("\nNext steps:")
        print("- Run database migration to create tables")
        print("- Add unit tests with database mocking")
        print("- Test end-to-end with actual database")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
