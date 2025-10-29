#!/usr/bin/env python3
"""
Configuration policy checks for SahaBot2.

This script enforces that:
- No direct environment variable access is used in the codebase (use config.settings instead)
  Disallowed: os.environ, os.getenv, from os import environ/getenv, load_dotenv, dotenv_values

Exit code:
- 0 if all checks pass
- 1 if violations are found
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]

# Directories to scan (relative to repository root)
SCAN_DIRS = [
    "application",
    "discordbot",
    "components",
    "middleware",
    "models",
    "pages",
    "racetime",
]

# Files to include at repo root
SCAN_FILES = [
    "main.py",
    "frontend.py",
    "database.py",
]

# Files and directories to ignore (relative to root)
IGNORE_PATHS = {
    ".git",
    ".github",
    ".venv",
    ".vscode",
    "__pycache__",
    "migrations",
    "tests",
    "static",
    "config.py",  # config is allowed to define settings
}

# Disallowed patterns (regex)
PATTERNS = [
    (re.compile(r"\bos\s*\.\s*environ\b"), "Direct env access via os.environ"),
    (re.compile(r"\bos\s*\.\s*getenv\b"), "Direct env access via os.getenv"),
    (re.compile(r"from\s+os\s+import\s+(?:environ|getenv)\b"), "Importing environ/getenv from os"),
    (re.compile(r"\bload_dotenv\b"), "Loading dotenv directly (use Pydantic Settings)"),
    (re.compile(r"\bdotenv_values\b"), "Loading dotenv values directly (use Pydantic Settings)"),
]


def iter_python_files() -> Iterable[Path]:
    # Scan directories
    for d in SCAN_DIRS:
        folder = ROOT / d
        if not folder.exists():
            continue
        for path in folder.rglob("*.py"):
            if any(part in IGNORE_PATHS for part in path.parts):
                continue
            yield path

    # Scan selected top-level files
    for f in SCAN_FILES:
        p = ROOT / f
        if p.exists():
            yield p


def check_file(path: Path) -> List[Tuple[int, str]]:
    """Return list of violations as (line_number, message)."""
    violations: List[Tuple[int, str]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return violations

    for i, line in enumerate(content, start=1):
        # Skip obvious comments
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for regex, msg in PATTERNS:
            if regex.search(line):
                violations.append((i, msg))
    return violations


def main() -> int:
    all_violations: List[Tuple[Path, int, str]] = []
    for py in iter_python_files():
        rel = py.relative_to(ROOT)
        if rel.name == "config.py":
            # Config file is explicitly allowed
            continue
        for lineno, message in check_file(py):
            all_violations.append((rel, lineno, message))

    if all_violations:
        print("Config policy violations found:\n")
        for rel, lineno, message in sorted(all_violations, key=lambda t: (str(t[0]), t[1])):
            print(f"{rel}:{lineno}: {message}")
        print("\nPlease use 'from config import settings' instead of reading environment variables directly.")
        return 1

    print("Config policy checks passed: no direct environment access detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
