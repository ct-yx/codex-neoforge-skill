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

UNSUPPORTED_LOADER_VERSIONS = {
    ("forge", "1.12.2"): "Minecraft 1.12.2 仅支持 Cleanroom；Forge 1.12.2 不在本 skill 支持范围",
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


def scan_files(root: Path, excluded_dirs: set[Path] | None = None) -> list[Path]:
    excluded_dirs = {path.resolve() for path in (excluded_dirs or set())}
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(parent.resolve() in excluded_dirs for parent in (path, *path.parents)):
            continue
        if not path.is_file() or ".git" in path.parts or "build" in path.parts or ".gradle" in path.parts:
            continue
        if path.name in SCAN_NAMES or path.suffix in {".gradle", ".kts"}:
            files.append(path)
    return sorted(files)


def gradle_settings(root: Path) -> tuple[Path | None, str]:
    settings = next((root / name for name in ("settings.gradle", "settings.gradle.kts") if (root / name).is_file()), None)
    if settings is None:
        return None, ""
    try:
        return settings, settings.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return settings, ""


def discover_modules(root: Path) -> list[tuple[str, Path]]:
    """Return the root and Gradle subprojects declared by settings.gradle.

    Gradle project paths use ``:a:b`` while the conventional on-disk layout
    is ``a/b``.  Included-but-not-yet-created projects stay visible in the
    result and are reported as unresolved instead of being silently folded
    into the root project.
    """

    root = root.resolve()
    modules: list[tuple[str, Path]] = [(":", root)]
    settings, content = gradle_settings(root)
    if settings is None:
        return modules
    included = re.findall(r"\binclude\s*(?:\(([^)]*)\)|([^\n\r]*))", content, flags=re.IGNORECASE)
    paths: list[str] = []
    for parenthesized, remainder in included:
        for raw_path in re.findall(r"['\"]([^'\"]+)['\"]", parenthesized or remainder):
            project_path = raw_path if raw_path.startswith(":") else f":{raw_path}"
            if project_path not in paths:
                paths.append(project_path)
    for project_path in paths:
        if project_path == ":" or not project_path.startswith(":"):
            continue
        module_dir = root.joinpath(*[part for part in project_path.split(":") if part])
        # Keep unresolved includes visible to callers.  They are not scanned,
        # but prevent the detector from claiming a complete single-module
        # project.
        modules.append((project_path, module_dir))
    return sorted(set(modules), key=lambda item: (item[0].count(":"), item[0]))


def module_for_file(path: Path, module_dirs: set[Path], project_root: Path) -> str:
    """Resolve a scanned file to its nearest declared Gradle module."""

    resolved = path.resolve()
    candidates = [directory for directory in module_dirs if resolved == directory or directory in resolved.parents]
    if not candidates:
        return ":"
    nearest = max(candidates, key=lambda directory: len(directory.parts))
    if nearest == project_root:
        return ":"
    relative = nearest.relative_to(project_root)
    return ":" + ":".join(relative.parts)


def detect_module(module_path: str, module_root: Path, project_root: Path, excluded_dirs: set[Path]) -> dict[str, object]:
    """Detect one Gradle project without absorbing sibling subprojects."""

    root = module_root.resolve()
    scores = {name: 0 for name in LOADER_NAMES}
    evidence: list[dict[str, object]] = []
    texts: list[tuple[Path, str]] = []
    module_excluded = {path for path in excluded_dirs if path != root and root in path.parents}
    for path in scan_files(root, module_excluded):
        relative = str(path.relative_to(project_root))
        evidence_module = module_for_file(path, excluded_dirs | {root}, project_root)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        texts.append((path, text))
        lower = text.casefold()
        name = path.name
        if name == "neoforge.mods.toml":
            scores["neoforge"] += 8
            evidence.append({"loader": "neoforge", "weight": 8, "file": relative, "module": evidence_module, "reason": "neoforge.mods.toml"})
        if name == "mods.toml":
            scores["forge"] += 8
            evidence.append({"loader": "forge", "weight": 8, "file": relative, "module": evidence_module, "reason": "mods.toml"})
        if name == "mcmod.info":
            scores["cleanroom"] += 6
            evidence.append({"loader": "cleanroom", "weight": 6, "file": relative, "module": evidence_module, "reason": "mcmod.info"})
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
                evidence.append({"loader": loader, "weight": weight, "file": relative, "module": evidence_module, "reason": f"contains {marker}"})

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
        relative = str(path.relative_to(project_root))
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

    active_loaders = [name for name, score in scores.items() if score]
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    detected = ordered[0][0] if active_loaders else "unknown"
    conflict = len(active_loaders) > 1
    if conflict:
        detected = "ambiguous"

    def values_for(kind: str) -> list[str]:
        return sorted({str(item["value"]) for item in version_candidates if item["kind"] == kind})

    minecraft_values = values_for("minecraft")
    java_values = values_for("java")

    return {
        "path": module_path,
        "project": str(root),
        "loader": detected,
        "scores": scores,
        "minecraft": minecraft_values[0] if len(minecraft_values) == 1 else ("ambiguous" if minecraft_values else None),
        "java": java_values[0] if len(java_values) == 1 else ("ambiguous" if java_values else None),
        "minecraft_candidates": minecraft_values,
        "java_candidates": java_values,
        "version_candidates": version_candidates,
        "evidence": evidence,
        "conflict": conflict,
        "scanned_files": [str(path.relative_to(project_root)) for path, _text in texts],
    }


def detect_project(root: Path) -> dict[str, object]:
    root = root.resolve()
    module_specs = discover_modules(root)
    module_dirs = {path.resolve() for _name, path in module_specs}
    modules: list[dict[str, object]] = []
    unresolved: list[str] = []
    for module_path, path in module_specs:
        if not path.is_dir():
            unresolved.append(module_path)
            continue
        modules.append(detect_module(module_path, path, root, module_dirs))

    active_loaders = {
        str(module["loader"])
        for module in modules
        if str(module.get("loader")) not in {"unknown", "ambiguous"}
    }
    module_conflict = bool(unresolved) or any(module.get("conflict") or module.get("loader") == "ambiguous" for module in modules)
    if module_conflict or len(active_loaders) > 1:
        detected = "ambiguous"
    elif len(active_loaders) == 1:
        detected = next(iter(active_loaders))
    else:
        detected = "unknown"

    def aggregate_values(key: str) -> list[str]:
        return sorted({str(value) for module in modules for value in module.get(key, []) if value})

    minecraft_values = aggregate_values("minecraft_candidates")
    java_values = aggregate_values("java_candidates")
    scores = {name: sum(int(module.get("scores", {}).get(name, 0)) for module in modules) for name in LOADER_NAMES}
    evidence = [item for module in modules for item in module.get("evidence", [])]
    version_candidates = [item for module in modules for item in module.get("version_candidates", [])]
    scanned_files = [item for module in modules for item in module.get("scanned_files", [])]
    return {
        "project": str(root),
        "loader": detected,
        "scores": scores,
        "minecraft": minecraft_values[0] if len(minecraft_values) == 1 else ("ambiguous" if minecraft_values else None),
        "java": java_values[0] if len(java_values) == 1 else ("ambiguous" if java_values else None),
        "minecraft_candidates": minecraft_values,
        "java_candidates": java_values,
        "version_candidates": version_candidates,
        "evidence": evidence,
        "conflict": module_conflict or len(active_loaders) > 1,
        "scanned_files": scanned_files,
        "modules": modules,
        "unresolved_modules": unresolved,
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
    unsupported_message = UNSUPPORTED_LOADER_VERSIONS.get((result["loader"], result["minecraft"]))
    if unsupported_message:
        problems.append(unsupported_message)
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
        for module in result["modules"]:  # type: ignore[index]
            print(f"module: {module['path']} loader={module['loader']} minecraft={module['minecraft'] or 'unknown'} java={module['java'] or 'unknown'}")
        for module_path in result.get("unresolved_modules", []):
            print(f"module: {module_path} unresolved")
        for problem in problems:
            print(f"ERROR: {problem}")
    raise SystemExit(0 if not problems else 1)


if __name__ == "__main__":
    main()
