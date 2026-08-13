#!/usr/bin/env python3
"""Detect Minecraft loader/version from a project without modifying files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LOADER_NAMES = ("neoforge", "forge", "cleanroom")
LOADER_ALIASES = {
    "neoforge": "neoforge",
    "neo forge": "neoforge",
    "neo-forge": "neoforge",
    "forge": "forge",
    "cleanroom": "cleanroom",
    "clean room": "cleanroom",
}

SCAN_NAMES = {
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gradle.properties",
    "neoforge.mods.toml",
    "mods.toml",
    "mcmod.info",
}


def canonical_loader(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().casefold().replace("_", " "))
    return LOADER_ALIASES.get(normalized, normalized)


def scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "build" in path.parts or ".gradle" in path.parts:
            continue
        if path.name in SCAN_NAMES or path.suffix in {".gradle", ".kts"}:
            files.append(path)
    return sorted(files)


def detect_project(root: Path) -> dict[str, object]:
    root = root.resolve()
    scores = {name: 0 for name in LOADER_NAMES}
    evidence: list[dict[str, object]] = []
    texts: list[tuple[Path, str]] = []
    for path in scan_files(root):
        relative = str(path.relative_to(root))
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        texts.append((path, text))
        lower = text.casefold()
        name = path.name
        if name == "neoforge.mods.toml":
            scores["neoforge"] += 8
            evidence.append({"loader": "neoforge", "weight": 8, "file": relative, "reason": "neoforge.mods.toml"})
        if name == "mods.toml":
            scores["forge"] += 8
            evidence.append({"loader": "forge", "weight": 8, "file": relative, "reason": "mods.toml"})
        if name == "mcmod.info":
            scores["cleanroom"] += 6
            evidence.append({"loader": "cleanroom", "weight": 6, "file": relative, "reason": "mcmod.info"})
        markers = (
            ("neoforge", "neoforge", 4),
            ("net.neoforged", "neoforge", 5),
            ("forgegradle", "forge", 4),
            ("net.minecraftforge", "forge", 5),
            ("cleanroomgradle", "cleanroom", 5),
            ("cleanroom", "cleanroom", 4),
            ("unimined", "cleanroom", 3),
        )
        for marker, loader, weight in markers:
            if marker in lower:
                scores[loader] += weight
                evidence.append({"loader": loader, "weight": weight, "file": relative, "reason": f"contains {marker}"})

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    detected = ordered[0][0] if ordered and ordered[0][1] else "unknown"
    conflict = len([value for value in scores.values() if value]) > 1
    if conflict and len(ordered) > 1 and ordered[0][1] == ordered[1][1]:
        detected = "ambiguous"

    version_candidates: list[dict[str, object]] = []
    version_patterns = (
        re.compile(r"(?im)^\s*minecraft_version\s*[=:]\s*[\"']?([0-9]+(?:\.[0-9]+){1,2})"),
        re.compile(r"(?im)^\s*minecraftVersion\s*[=:]\s*[\"']?([0-9]+(?:\.[0-9]+){1,2})"),
        re.compile(r"(?im)^\s*minecraft\s*[=:]\s*[\"']?([0-9]+(?:\.[0-9]+){1,2})"),
        re.compile(r"(?i)\bminecraft_version_range\b[^\n\r]*?([0-9]+(?:\.[0-9]+){1,2})"),
    )
    java_patterns = (
        re.compile(r"(?im)^\s*(?:java_version|javaVersion)\s*[=:]\s*[\"']?(\d{2})"),
        re.compile(r"(?i)languageVersion\s*\.of\s*\(\s*(\d{2})\s*\)"),
        re.compile(r"(?i)JavaLanguageVersion\.of\(\s*(\d{2})\s*\)"),
    )
    for path, text in texts:
        relative = str(path.relative_to(root))
        for pattern in version_patterns:
            for match in pattern.finditer(text):
                version_candidates.append({"value": match.group(1), "file": relative, "kind": "minecraft"})
        for pattern in java_patterns:
            for match in pattern.finditer(text):
                version_candidates.append({"value": match.group(1), "file": relative, "kind": "java"})
        # Cleanroom's current Unimined template declares the game version as
        # `unimined.minecraft { version "1.12.2" }`, unlike the modern
        # minecraft_version Gradle property used by NeoForge/Forge.
        if "unimined.minecraft" in text:
            match = re.search(r"unimined\.minecraft\s*\{[\s\S]{0,500}?\bversion\s*[=:]?\s*[\"']([0-9]+(?:\.[0-9]+){1,2})", text)
            if match:
                version_candidates.append({"value": match.group(1), "file": relative, "kind": "minecraft"})

    def first_kind(kind: str) -> str | None:
        return next((str(item["value"]) for item in version_candidates if item["kind"] == kind), None)

    return {
        "project": str(root),
        "loader": detected,
        "scores": scores,
        "minecraft": first_kind("minecraft"),
        "java": first_kind("java"),
        "version_candidates": version_candidates,
        "evidence": evidence,
        "conflict": conflict,
        "scanned_files": [str(path.relative_to(root)) for path, _text in texts],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--expect-loader", choices=LOADER_NAMES)
    parser.add_argument("--expect-minecraft")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.project.is_dir():
        raise SystemExit(f"项目目录不存在：{args.project}")
    result = detect_project(args.project)
    problems: list[str] = []
    if result["loader"] in {"unknown", "ambiguous"}:
        problems.append(f"loader 检测结果为 {result['loader']}")
    if args.expect_loader and result["loader"] != canonical_loader(args.expect_loader):
        problems.append(f"期望 loader={args.expect_loader}，实际为 {result['loader']}")
    if args.expect_minecraft and result["minecraft"] != args.expect_minecraft:
        problems.append(f"期望 Minecraft={args.expect_minecraft}，实际为 {result['minecraft'] or 'unknown'}")
    result["ok"] = not problems
    result["problems"] = problems
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"project: {result['project']}")
        print(f"loader: {result['loader']} (scores={result['scores']})")
        print(f"minecraft: {result['minecraft'] or 'unknown'}")
        print(f"java: {result['java'] or 'unknown'}")
        for item in result["evidence"]:  # type: ignore[index]
            print(f"evidence: {item['loader']} +{item['weight']} {item['file']} ({item['reason']})")
        for problem in problems:
            print(f"ERROR: {problem}")
    raise SystemExit(0 if not problems else 1)


if __name__ == "__main__":
    main()
