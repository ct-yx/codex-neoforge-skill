#!/usr/bin/env python3
"""Check the minimum layout and metadata files for a mod-loader project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_loader import LOADER_NAMES, detect_project


def exists_any(root: Path, paths: tuple[str, ...], kind: str = "file") -> bool:
    """Check alternatives by their expected filesystem type.

    A regular file named ``src/main/java`` must not satisfy the source
    directory requirement, and vice versa.  This is intentionally small and
    keeps the check useful for both Unix and Windows fixtures.
    """

    checker = Path.is_dir if kind == "dir" else Path.is_file
    return any(checker(root / path) for path in paths)


def check_project(root: Path, loader: str, include_source_layout: bool = True) -> dict[str, object]:
    required: list[tuple[str, tuple[str, ...], str]] = [
        ("Gradle wrapper", ("gradlew", "gradlew.bat"), "file"),
        ("Gradle build script", ("build.gradle", "build.gradle.kts"), "file"),
        ("Gradle settings", ("settings.gradle", "settings.gradle.kts"), "file"),
    ]
    if include_source_layout:
        required.extend(
            [
                ("Java source directory", ("src/main/java",), "dir"),
                ("resource directory", ("src/main/resources",), "dir"),
            ]
        )
    if include_source_layout and loader == "neoforge":
        required.append(("NeoForge metadata", ("src/main/resources/META-INF/neoforge.mods.toml",), "file"))
    elif include_source_layout and loader == "forge":
        required.append(("Forge metadata", ("src/main/resources/META-INF/mods.toml",), "file"))
    elif include_source_layout and loader == "cleanroom":
        required.extend(
            [
                ("gradle.properties", ("gradle.properties",), "file"),
                ("Cleanroom metadata/template", ("src/main/resources/mcmod.info", "src/main/resource-templates/mcmod.info"), "file"),
            ]
        )
    checks = [{"name": name, "paths": paths, "kind": kind, "ok": exists_any(root, paths, kind)} for name, paths, kind in required]
    missing = [item["name"] for item in checks if not item["ok"]]
    warnings: list[str] = []
    if include_source_layout and loader == "cleanroom" and (root / "gradle.properties").is_file():
        properties = (root / "gradle.properties").read_text(encoding="utf-8", errors="replace")
        for key in ("mod_id", "root_package", "mod_version"):
            if f"{key}=" not in properties and f"{key} =" not in properties:
                warnings.append(f"gradle.properties 缺少常用变量：{key}")
    active_metadata = [
        path
        for path in (
            "src/main/resources/META-INF/neoforge.mods.toml",
            "src/main/resources/META-INF/mods.toml",
            "src/main/resources/mcmod.info",
        )
        if (root / path).is_file()
    ]
    if include_source_layout and len(active_metadata) > 1:
        warnings.append(f"同时存在多套活动元数据：{', '.join(active_metadata)}")
    for optional in ("src/generated/resources", "src/main/resource-templates") if include_source_layout else ():
        if not (root / optional).is_dir():
            warnings.append(f"可选目录不存在：{optional}")
    return {"loader": loader, "checks": checks, "missing": missing, "warnings": warnings, "ok": not missing}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--loader", choices=("auto", *LOADER_NAMES), default="auto")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.project.is_dir():
        raise SystemExit(f"项目目录不存在：{args.project}")
    detection = detect_project(args.project)
    loader = detection["loader"] if args.loader == "auto" else args.loader
    if loader not in LOADER_NAMES:
        result = {"project": str(args.project.resolve()), "detection": detection, "ok": False, "error": "无法唯一识别 loader，请使用 --loader"}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else f"ERROR: {result['error']}")
        raise SystemExit(1)
    modules = detection.get("modules", []) if isinstance(detection.get("modules"), list) else []
    multi_module = len(modules) > 1 or bool(detection.get("unresolved_modules"))
    module_structures = []
    for module in modules:
        if not isinstance(module, dict) or str(module.get("loader")) in {"unknown", "ambiguous"}:
            continue
        module_path = str(module.get("project", args.project.resolve()))
        is_root_module = str(module.get("path")) == ":"
        module_structures.append(
            check_project(
                Path(module_path),
                str(module["loader"]),
                include_source_layout=not (multi_module and is_root_module),
            )
        )
    result = {
        "project": str(args.project.resolve()),
        "detection": detection,
        "structure": check_project(args.project.resolve(), str(loader), include_source_layout=not multi_module),
        "module_structures": module_structures,
    }
    result["ok"] = bool(result["structure"]["ok"])  # type: ignore[index]
    result["ok"] = bool(result["ok"]) and not detection.get("unresolved_modules") and all(bool(item["ok"]) for item in module_structures)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        structure = result["structure"]  # type: ignore[assignment]
        print(f"loader: {structure['loader']}")
        for item in structure["checks"]:
            state = "OK" if item["ok"] else "MISSING"
            print(f"{state}: {item['name']} ({', '.join(item['paths'])})")
        for warning in structure["warnings"]:
            print(f"WARNING: {warning}")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
