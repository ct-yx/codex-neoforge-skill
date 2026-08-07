#!/usr/bin/env python3
"""Validate the distributable Codex skill using only the standard library."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "neoforge-dev"
SKILL_FILE = SKILL_DIR / "SKILL.md"
OPENAI_FILE = SKILL_DIR / "agents" / "openai.yaml"
REFERENCE_FILE = SKILL_DIR / "references" / "official-docs.md"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")

    try:
        frontmatter, _body = text[4:].split("\n---\n", 1)
    except ValueError:
        fail("SKILL.md frontmatter is not closed")

    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        match = re.fullmatch(r"([a-z_]+):\s*(.+)", line)
        if not match:
            fail(f"unsupported frontmatter line: {line!r}")
        fields[match.group(1)] = match.group(2).strip().strip('"')
    return fields


def main() -> None:
    if not SKILL_FILE.is_file():
        fail(f"missing {SKILL_FILE.relative_to(ROOT)}")
    if not OPENAI_FILE.is_file():
        fail(f"missing {OPENAI_FILE.relative_to(ROOT)}")
    if not REFERENCE_FILE.is_file():
        fail(f"missing {REFERENCE_FILE.relative_to(ROOT)}")

    fields = parse_frontmatter(SKILL_FILE.read_text(encoding="utf-8"))
    if set(fields) != {"name", "description"}:
        fail("frontmatter must contain exactly name and description")
    if fields["name"] != "neoforge-dev":
        fail("skill name must be neoforge-dev")
    if not fields["description"]:
        fail("skill description must not be empty")

    interface = OPENAI_FILE.read_text(encoding="utf-8")
    required_fragments = (
        'display_name: "NeoForge 模组开发"',
        "short_description:",
        'default_prompt: "使用 $neoforge-dev',
    )
    for fragment in required_fragments:
        if fragment not in interface:
            fail(f"agents/openai.yaml is missing {fragment!r}")

    forbidden = (
        "E:\\GitHub",
        "settings.local.json",
        "NeoForge开发流程师",
        "mcp__neoforge",
    )
    reference = REFERENCE_FILE.read_text(encoding="utf-8")
    combined = SKILL_FILE.read_text(encoding="utf-8") + interface
    for fragment in forbidden:
        if fragment in combined:
            fail(f"OpenCode-only residue found: {fragment!r}")

    for fragment in (
        "https://docs.neoforged.net/",
        "816c03d31ff7948179c7bd4a58d23bcfda09c18a",
        "runClientData",
        "runServerData",
    ):
        if fragment not in reference:
            fail(f"official-docs.md is missing {fragment!r}")

    print("Skill package is valid.")


if __name__ == "__main__":
    main()
