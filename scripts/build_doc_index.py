#!/usr/bin/env python3
"""Repository wrapper for the bundled documentation indexer."""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "minecraft-mod-dev" / "scripts" / "build_doc_index.py"), run_name="__main__")
