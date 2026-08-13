#!/usr/bin/env python3
"""Validate a versioned cross-mod compatibility matrix."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


LOADERS = {"neoforge", "forge", "cleanroom"}
GAMES = {"neoforge": "1.21.1", "forge": "1.20.1", "cleanroom": "1.12.2"}
JAVAS = {"neoforge": "21", "forge": "17", "cleanroom": None}
STATUSES = {"planned", "implemented", "verified", "blocked"}
SCOPES = {"compile", "runtime", "compile_runtime", "optional"}
SURFACES = {"registry", "event", "capability", "attachment", "payload", "command", "data", "render", "storage", "config"}
SIDES = {"common", "server", "client"}
REQUIRED_FIELDS = {
    "source_version_range",
    "target_version_range",
    "source_artifact",
    "target_artifact",
    "dependency_scope",
    "sides",
    "integration_surfaces",
    "runtime_checks",
    "adapter",
    "evidence",
    "status",
}
METADATA_FIELDS = {"mandatory", "ordering", "side"}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def validate_endpoint(value: Any, name: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{name} 必须是对象"]
    loader = text(value.get("loader"))
    if loader not in LOADERS:
        errors.append(f"{name}.loader 必须是 {sorted(LOADERS)} 之一")
    minecraft = text(value.get("minecraft"))
    if loader in GAMES and minecraft != GAMES[loader]:
        errors.append(f"{name}.minecraft={minecraft or 'missing'} 与 {loader} 的目标 {GAMES[loader]} 不匹配")
    if not text(value.get("java")):
        errors.append(f"{name}.java 不能为空")
    return errors


def path_like(value: Any) -> bool:
    return text(value) not in {"", "[adapter-path]"}


def endpoint_matches(actual: Any, expected: dict[str, str] | None) -> bool:
    if expected is None:
        return True
    if not isinstance(actual, dict):
        return False
    return all(actual.get(key) == value for key, value in expected.items())


def validate_entry(entry: Any, index: int, expected_source: dict[str, str] | None, expected_target: dict[str, str] | None) -> list[str]:
    prefix = f"entries[{index}]"
    if not isinstance(entry, dict):
        return [f"{prefix} 必须是对象"]
    errors: list[str] = []
    errors.extend(f"{prefix}: {error}" for error in validate_endpoint(entry.get("source"), "source"))
    errors.extend(f"{prefix}: {error}" for error in validate_endpoint(entry.get("target"), "target"))
    source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
    target = entry.get("target") if isinstance(entry.get("target"), dict) else {}
    if expected_source and any(source.get(key) != value for key, value in expected_source.items()):
        errors.append(f"{prefix}: source 与命令行期望不匹配")
    if expected_target and any(target.get(key) != value for key, value in expected_target.items()):
        errors.append(f"{prefix}: target 与命令行期望不匹配")

    mod_id = text(entry.get("mod_id"))
    if not re.fullmatch(r"[a-z0-9_]+", mod_id):
        errors.append(f"{prefix}.mod_id 必须是小写 ASCII/数字/下划线")
    missing = sorted(REQUIRED_FIELDS - entry.keys())
    errors.extend(f"{prefix} 缺少字段：{field}" for field in missing)
    for field in ("source_version_range", "target_version_range"):
        if not text(entry.get(field)):
            errors.append(f"{prefix}.{field} 不能为空")
    for field in ("source_artifact", "target_artifact"):
        if not text(entry.get(field)):
            errors.append(f"{prefix}.{field} 不能为空；未知构件请明确写 blocked 依据")
    scope = text(entry.get("dependency_scope"))
    if scope not in SCOPES:
        errors.append(f"{prefix}.dependency_scope 必须是 {sorted(SCOPES)} 之一")
    sides = entry.get("sides")
    metadata = entry.get("loader_metadata")
    if not isinstance(metadata, dict):
        errors.append(f"{prefix}.loader_metadata 必须是对象，记录目标 loader 的依赖字段")
    else:
        if not isinstance(metadata.get("mandatory"), bool):
            errors.append(f"{prefix}.loader_metadata.mandatory 必须是布尔值")
        if text(metadata.get("ordering")) not in {"BEFORE", "AFTER", "NONE"}:
            errors.append(f"{prefix}.loader_metadata.ordering 必须是 BEFORE/AFTER/NONE")
        if text(metadata.get("side")) not in {"CLIENT", "SERVER", "BOTH"}:
            errors.append(f"{prefix}.loader_metadata.side 必须是 CLIENT/SERVER/BOTH")
        unknown_metadata = set(metadata) - METADATA_FIELDS
        if unknown_metadata:
            errors.append(f"{prefix}.loader_metadata 包含未知字段：{sorted(unknown_metadata)}")
        if scope == "optional" and metadata.get("mandatory") is True:
            errors.append(f"{prefix}: optional scope 不能设置 loader_metadata.mandatory=true")
        if "client" not in [text(side) for side in sides or []] and text(metadata.get("side")) == "CLIENT":
            errors.append(f"{prefix}: metadata.side=CLIENT 但 sides 未包含 client")
        if "server" not in [text(side) for side in sides or []] and text(metadata.get("side")) == "SERVER":
            errors.append(f"{prefix}: metadata.side=SERVER 但 sides 未包含 server")
    sides = entry.get("sides")
    if not isinstance(sides, list) or not sides or not all(text(item) in SIDES for item in sides):
        errors.append(f"{prefix}.sides 必须是非空 {sorted(SIDES)} 列表")
    surfaces = entry.get("integration_surfaces")
    if not isinstance(surfaces, list) or not surfaces or not all(text(item) in SURFACES for item in surfaces):
        errors.append(f"{prefix}.integration_surfaces 必须是非空 {sorted(SURFACES)} 列表")
    for field in ("runtime_checks", "evidence"):
        values = entry.get(field)
        if not isinstance(values, list) or not values or not all(text(item) for item in values):
            errors.append(f"{prefix}.{field} 必须是非空字符串列表")
    if not path_like(entry.get("adapter")):
        errors.append(f"{prefix}.adapter 必须填写适配层路径或明确原因")
    status = text(entry.get("status"))
    if status not in STATUSES:
        errors.append(f"{prefix}.status 必须是 {sorted(STATUSES)} 之一")
    if status == "verified" and len(entry.get("evidence", [])) < 2:
        errors.append(f"{prefix}: verified 至少需要两条证据（例如构建 + 组合运行）")
    if status == "blocked" and not any("blocked" in text(item).casefold() or "缺失" in text(item) for item in entry.get("runtime_checks", [])):
        errors.append(f"{prefix}: blocked 必须在 runtime_checks 中说明阻塞原因")
    return errors


def load_matrix(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"无法读取 JSON：{exc}")
    if not isinstance(document, dict):
        fail("矩阵根节点必须是对象")
    return document


def parse_endpoint(value: str | None, name: str) -> dict[str, str] | None:
    if not value:
        return None
    parts = value.split(":")
    if len(parts) != 2 or parts[0] not in LOADERS or parts[1] != GAMES[parts[0]]:
        fail(f"--{name} 必须是 loader:minecraft，例如 neoforge:1.21.1")
    return {"loader": parts[0], "minecraft": parts[1]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path, help="compatibility-matrix.json")
    parser.add_argument("--source", help="限制有向源端，例如 neoforge:1.21.1")
    parser.add_argument("--target", help="限制有向目标端，例如 forge:1.20.1")
    parser.add_argument("--mod-id", help="只检查指定联动 Mod")
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果")
    args = parser.parse_args()
    if not args.matrix.is_file():
        fail(f"矩阵不存在：{args.matrix}")
    document = load_matrix(args.matrix)
    entries = document.get("entries")
    if not isinstance(entries, list) or not entries:
        fail("entries 必须是非空列表")
    expected_source = parse_endpoint(args.source, "source")
    expected_target = parse_endpoint(args.target, "target")
    selected = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and (not args.mod_id or entry.get("mod_id") == args.mod_id)
        and endpoint_matches(entry.get("source"), expected_source)
        and endpoint_matches(entry.get("target"), expected_target)
    ]
    errors: list[str] = []
    if not selected:
        errors.append("没有匹配命令行筛选条件的矩阵行")
    for index, entry in enumerate(entries):
        if entry in selected:
            errors.extend(validate_entry(entry, index, expected_source, expected_target))

    seen_keys: set[tuple[str, str, str]] = set()
    for index, entry in enumerate(selected):
        if not isinstance(entry, dict):
            continue
        source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
        target = entry.get("target") if isinstance(entry.get("target"), dict) else {}
        key = (text(entry.get("mod_id")), f"{source.get('loader')}:{source.get('minecraft')}", f"{target.get('loader')}:{target.get('minecraft')}")
        if key in seen_keys:
            errors.append(f"重复矩阵行：entries[{index}] {key[0]} {key[1]} -> {key[2]}")
        seen_keys.add(key)

    result = {"matrix": str(args.matrix.resolve()), "entry_count": len(entries), "selected_count": len(selected), "ok": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"matrix: {result['matrix']}")
        print(f"entries: {result['entry_count']} (selected={result['selected_count']})")
        for error in errors:
            print(f"ERROR: {error}")
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
