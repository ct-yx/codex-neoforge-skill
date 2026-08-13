#!/usr/bin/env python3
"""Repository wrapper for the bundled compatibility matrix validator."""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "neoforge-dev" / "scripts" / "validate_compatibility.py"), run_name="__main__")
