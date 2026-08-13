#!/usr/bin/env python3
"""Validate the distributable Codex skill using only the standard library."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README_FILE = ROOT / "README.md"
CONTRIBUTING_FILE = ROOT / "CONTRIBUTING.md"
NOTICE_FILE = ROOT / "NOTICE.md"
SKILL_DIR = ROOT / "neoforge-dev"
SKILL_FILE = SKILL_DIR / "SKILL.md"
OPENAI_FILE = SKILL_DIR / "agents" / "openai.yaml"
REFERENCE_FILE = SKILL_DIR / "references" / "official-docs.md"
REFERENCE_FILES = (
    SKILL_DIR / "references" / "baseline-gate.md",
    SKILL_DIR / "references" / "common" / "java-style.md",
    SKILL_DIR / "references" / "common" / "package-structure.md",
    SKILL_DIR / "references" / "common" / "resources-layout.md",
    SKILL_DIR / "references" / "common" / "testing-validation.md",
    SKILL_DIR / "references" / "neoforge" / "1.21.1.md",
    SKILL_DIR / "references" / "forge" / "1.20.1.md",
    SKILL_DIR / "references" / "cleanroom" / "1.12.2.md",
    SKILL_DIR / "references" / "migration" / "neoforge-to-forge.md",
    SKILL_DIR / "references" / "migration" / "forge-to-cleanroom.md",
    SKILL_DIR / "references" / "migration" / "neoforge-to-cleanroom.md",
    SKILL_DIR / "references" / "migration" / "forge-to-neoforge.md",
    SKILL_DIR / "references" / "migration" / "cleanroom-to-forge.md",
    SKILL_DIR / "references" / "migration" / "cleanroom-to-neoforge.md",
    SKILL_DIR / "references" / "compatibility" / "mod-compatibility.md",
    SKILL_DIR / "references" / "compatibility" / "compatibility-matrix.example.json",
)
BUNDLED_SCRIPTS = (
    SKILL_DIR / "scripts" / "crawl_docs.py",
    SKILL_DIR / "scripts" / "build_doc_index.py",
    SKILL_DIR / "scripts" / "validate_loader.py",
    SKILL_DIR / "scripts" / "validate_structure.py",
    SKILL_DIR / "scripts" / "validate_compatibility.py",
)


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
    for root_doc in (README_FILE, CONTRIBUTING_FILE, NOTICE_FILE):
        if not root_doc.is_file():
            fail(f"missing {root_doc.relative_to(ROOT)}")
        if not root_doc.read_text(encoding="utf-8").strip():
            fail(f"empty root document {root_doc.relative_to(ROOT)}")
    if not SKILL_FILE.is_file():
        fail(f"missing {SKILL_FILE.relative_to(ROOT)}")
    if not OPENAI_FILE.is_file():
        fail(f"missing {OPENAI_FILE.relative_to(ROOT)}")
    for reference_path in (REFERENCE_FILE, *REFERENCE_FILES):
        if not reference_path.is_file():
            fail(f"missing {reference_path.relative_to(ROOT)}")
        if not reference_path.read_text(encoding="utf-8").strip():
            fail(f"empty reference {reference_path.relative_to(ROOT)}")
    for script_path in BUNDLED_SCRIPTS:
        if not script_path.is_file():
            fail(f"missing {script_path.relative_to(ROOT)}")

    fields = parse_frontmatter(SKILL_FILE.read_text(encoding="utf-8"))
    if set(fields) != {"name", "description"}:
        fail("frontmatter must contain exactly name and description")
    if fields["name"] != "neoforge-dev":
        fail("skill name must be neoforge-dev")
    if not fields["description"]:
        fail("skill description must not be empty")

    interface = OPENAI_FILE.read_text(encoding="utf-8")
    required_fragments = (
        'display_name: "Minecraft 模组开发"',
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
        "87526dd760129b356e88f130550d646d4eb2fa31",
        "89314645e4e8b713688ba49ea6f84cbffd30cac7",
    ):
        if fragment not in reference:
            fail(f"official-docs.md is missing {fragment!r}")

    skill = SKILL_FILE.read_text(encoding="utf-8")
    for fragment in (
        "NeoForge 1.21.1",
        "Java 21",
        "BASELINE_GATE:",
        "基线未完成时，只记录迁移资料，不执行 Forge/Cleanroom 移植设计或代码修改。",
        "只有基线验收完成且用户明确指定目标加载器和版本后，才进入移植任务。",
        "Forge 1.20.1",
        "Cleanroom 1.12.2",
        "validate_loader.py",
        "validate_structure.py",
        "validate_compatibility.py",
        "compatibility-matrix.json",
        "联动 Mod",
        "六条有向迁移路径",
    ):
        if fragment not in skill:
            fail(f"SKILL.md is missing {fragment!r}")

    readme = README_FILE.read_text(encoding="utf-8")
    for fragment in (
        "NeoForge 1.21.1 / Java 21",
        "BASELINE_GATE:",
        "Forge 1.20.1",
        "Cleanroom 1.12.2",
        "releases/latest/download/neoforge-dev.zip",
        "CONTRIBUTING.md",
        "compatibility-matrix",
        "联动 Mod",
    ):
        if fragment not in readme:
            fail(f"README.md is missing {fragment!r}")

    notice = NOTICE_FILE.read_text(encoding="utf-8")
    for fragment in (
        "cnlimiter/opencode-neoforge-skill",
        "6b1b55cefaa0be602ad1f96b678d9a4cd26eb67c",
        "official-docs.md",
    ):
        if fragment not in notice:
            fail(f"NOTICE.md is missing {fragment!r}")

    print("Skill package is valid.")


if __name__ == "__main__":
    main()
