#!/usr/bin/env python3
"""Repository wrapper for the bundled documentation crawler."""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "neoforge-dev" / "scripts" / "crawl_docs.py"), run_name="__main__")
