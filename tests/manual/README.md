# Manual Tests

This directory contains manual test scripts that can be run directly without pytest or database setup.

## Available Tests

### `test_mystery_algorithm.py`

Standalone test of the mystery weightset algorithm without any dependencies.

**Run:**
```bash
python3 tests/manual/test_mystery_algorithm.py
```

**Tests:**
- Weighted random choice distribution
- Mystery rolling logic (preset + subweight)
- Validation logic

**Status:** ✅ All tests pass

### `test_mystery_system.py`

Comprehensive test of the mystery service (requires dependencies).

**Run:**
```bash
python3 tests/manual/test_mystery_system.py
```

**Tests:**
- Basic mystery weight rolling
- Mystery with subweights
- Mystery with entrance weights
- Mystery with customizer
- Invalid mystery validation

**Note:** This requires tortoise-orm and other dependencies to be installed.

## Purpose

These manual tests are useful for:
- Quick verification during development
- Testing without full test suite setup
- Demonstrating functionality
- Debugging specific features

## Running Full Test Suite

For the complete test suite with database fixtures:
```bash
pytest tests/unit/test_alttpr_mystery_service.py
```
