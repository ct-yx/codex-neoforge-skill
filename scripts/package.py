#!/usr/bin/env python3
"""Create a reproducible release ZIP containing the neoforge-dev skill."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "neoforge-dev"
DIST_DIR = ROOT / "dist"
ZIP_PATH = DIST_DIR / "neoforge-dev.zip"
CHECKSUM_PATH = DIST_DIR / "neoforge-dev.zip.sha256"
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def main() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py")], check=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(
        path
        for path in SKILL_DIR.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    if not files:
        raise SystemExit("No skill files found")

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(relative, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())

    digest = hashlib.sha256(ZIP_PATH.read_bytes()).hexdigest()
    CHECKSUM_PATH.write_text(f"{digest}  {ZIP_PATH.name}\n", encoding="utf-8")
    print(f"Created {ZIP_PATH}")
    print(f"SHA-256 {digest}")


if __name__ == "__main__":
    main()
