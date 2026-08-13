#!/usr/bin/env python3
"""Generate a deterministic Markdown compatibility report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_compatibility import load_json, validate_document, text


def render(document: dict, result: dict) -> str:
    lines = [
        "# Mod 联动兼容性报告",
        "",
        f"- Schema：`{result.get('schema_version')}`",
        f"- 项目 Mod：`{text(document.get('project_mod_id')) or 'unknown'}`",
        f"- 矩阵行：`{result.get('entry_count')}`（筛选后 `{result.get('selected_count')}`）",
        f"- 总体状态：`{'PASS' if result.get('ok') else 'FAIL'}`",
        "",
        "## 诊断",
        "",
    ]
    if result.get("errors"):
        lines.extend(f"- ❌ {error}" for error in result["errors"])
    if result.get("warnings"):
        lines.extend(f"- ⚠️ {warning}" for warning in result["warnings"])
    if not result.get("errors") and not result.get("warnings"):
        lines.append("- ✅ 无诊断信息")
    lines.extend(["", "## 矩阵行", "", "| Mod | 源 → 目标 | 构件版本 | 状态 | 证据类型 |", "| --- | --- | --- | --- | --- |"])
    for entry in document.get("entries", []):
        if not isinstance(entry, dict):
            continue
        source = entry.get("source", {})
        target = entry.get("target", {})
        source_label = f"{text(source.get('loader'))}:{text(source.get('minecraft'))}"
        target_label = f"{text(target.get('loader'))}:{text(target.get('minecraft'))}"
        versions = f"{text(entry.get('resolved_source_version')) or 'TODO'} → {text(entry.get('resolved_target_version')) or 'TODO'}"
        evidence = ", ".join(sorted({text(item.get("type")) for item in entry.get("evidence", []) if isinstance(item, dict)})) or "none"
        lines.append(f"| `{text(entry.get('mod_id'))}` | `{source_label}` → `{target_label}` | `{versions}` | `{text(entry.get('status'))}` | `{evidence}` |")
    lines.extend(["", "## 验收规则", "", "`verified` 必须同时具备 observed 构建证据和 observed 客户端/服务端/启动/GameTest 组合证据。构件版本与 SHA-256 应来自 artifact lock。", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source")
    parser.add_argument("--target")
    parser.add_argument("--mod-id")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--artifact-lock", type=Path)
    args = parser.parse_args()
    if not args.matrix.is_file():
        raise SystemExit(f"ERROR: 矩阵不存在：{args.matrix}")
    document = load_json(args.matrix)
    from validate_compatibility import parse_endpoint

    result = validate_document(
        document,
        args.matrix,
        parse_endpoint(args.source, "source"),
        parse_endpoint(args.target, "target"),
        args.mod_id,
        args.artifact_lock,
        args.project,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(document, result), encoding="utf-8")
    print(f"Wrote {args.output}")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
