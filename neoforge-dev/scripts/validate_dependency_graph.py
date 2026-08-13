#!/usr/bin/env python3
"""Validate compatibility-matrix dependency and ordering graphs."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_compatibility import find_cycles, load_json, ordering_edges, text


def graph_from_entries(entries: list[dict[str, Any]]) -> tuple[dict[str, set[str]], list[str]]:
    graph = ordering_edges(entries)
    errors: list[str] = []
    known = {text(entry.get("mod_id")) for entry in entries}
    for index, entry in enumerate(entries):
        dependency_graph = entry.get("dependency_graph")
        if not isinstance(dependency_graph, dict):
            continue
        requires = dependency_graph.get("requires", [])
        if not isinstance(requires, list):
            errors.append(f"entries[{index}].dependency_graph.requires 必须是列表")
            continue
        for dependency in requires:
            dependency_id = text(dependency)
            if dependency_id and dependency_id == text(entry.get("mod_id")):
                errors.append(f"entries[{index}] 不能依赖自身：{dependency_id}")
            # A dependency may be outside this matrix (for example Minecraft or
            # the loader); keep it as a diagnostic only when it looks like a mod id.
            if dependency_id and re.fullmatch(r"[a-z][a-z0-9_]{1,63}", dependency_id) and dependency_id not in known:
                errors.append(f"entries[{index}] requires 未在当前矩阵声明：{dependency_id}")
    return graph, errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.matrix.is_file():
        raise SystemExit(f"ERROR: 矩阵不存在：{args.matrix}")
    document = load_json(args.matrix)
    entries = document.get("entries")
    errors: list[str] = []
    if not isinstance(entries, list) or not entries:
        errors.append("entries 必须是非空列表")
        entries = []
    valid_entries = [entry for entry in entries if isinstance(entry, dict)]
    graph, graph_errors = graph_from_entries(valid_entries)
    errors.extend(graph_errors)
    errors.extend(f"ordering 循环：{' -> '.join(cycle)}" for cycle in find_cycles(graph))
    result = {"matrix": str(args.matrix.resolve()), "node_count": len(graph), "ok": not errors, "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"matrix: {result['matrix']}")
        print(f"nodes: {result['node_count']}")
        for error in errors:
            print(f"ERROR: {error}")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
