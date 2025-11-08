#!/usr/bin/env python3
"""
Compile translation files from .po to .mo format.

This script should be run whenever translation files are updated.
The .mo files are the binary compiled versions that gettext uses at runtime.

Usage:
    python compile_translations.py

    Or from project root:
    poetry run python application/i18n/compile_translations.py
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Get the locales directory
LOCALES_DIR = Path(__file__).parent / 'locales'


def compile_po_file(po_file: Path) -> bool:
    """
    Compile a single .po file to .mo format.

    Args:
        po_file: Path to the .po file

    Returns:
        True if compilation succeeded, False otherwise
    """
    mo_file = po_file.with_suffix('.mo')

    try:
        # Import our custom Python-based compiler
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from mo_compiler import compile_po_to_mo

        compile_po_to_mo(po_file)
        logger.info("✓ Compiled: %s -> %s", po_file.name, mo_file.name)
        return True

    except Exception as e:
        logger.error("✗ Failed to compile %s: %s", po_file.name, e)
        return False


def main():
    """Compile all .po files in the locales directory."""
    if not LOCALES_DIR.exists():
        logger.error("Locales directory not found: %s", LOCALES_DIR)
        return 1

    # Find all .po files
    po_files = list(LOCALES_DIR.rglob('*.po'))

    if not po_files:
        logger.warning("No .po files found in %s", LOCALES_DIR)
        return 0

    logger.info("Found %d translation file(s) to compile", len(po_files))
    logger.info("")

    success_count = 0
    fail_count = 0

    for po_file in po_files:
        if compile_po_file(po_file):
            success_count += 1
        else:
            fail_count += 1

    logger.info("")
    logger.info("Compilation complete: %d succeeded, %d failed", success_count, fail_count)

    return 0 if fail_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
