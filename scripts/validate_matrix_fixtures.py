#!/usr/bin/env python3
"""Repository wrapper for the bundled matrix fixture tests."""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "minecraft-mod-dev" / "scripts" / "validate_matrix_fixtures.py"), run_name="__main__")
