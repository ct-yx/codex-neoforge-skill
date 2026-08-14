#!/usr/bin/env python3
"""Repository wrapper for the bundled dependency graph validator."""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "minecraft-mod-dev" / "scripts" / "validate_dependency_graph.py"), run_name="__main__")
