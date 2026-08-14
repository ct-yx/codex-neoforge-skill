#!/usr/bin/env python3
"""Run small compatibility-matrix regression fixtures.

The fixtures model the states that can be checked without launching Minecraft:
baseline-only, target present, wrong version, side mismatch, ordering cycle and
insufficient verified evidence.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_compatibility import validate_document


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "references" / "compatibility" / "compatibility-matrix.example.json"


def load() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def expect_failure(document: dict, name: str, needle: str) -> None:
    with tempfile.TemporaryDirectory(prefix="matrix-fixture-") as directory:
        path = Path(directory) / "matrix.json"
        path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
        result = validate_document(document, path)
    if result["ok"] or not any(needle in error for error in result["errors"]):
        raise SystemExit(f"fixture {name} 未触发预期错误：{result}")
    print(f"PASS {name}")


def main() -> None:
    baseline_only = load()
    baseline_only["entries"][0]["fallback_behavior"]["missing_mod"] = "核心功能继续运行并记录联动关闭"
    # A planned optional row is the baseline-only state.
    result = validate_document(baseline_only, EXAMPLE)
    if not result["ok"]:
        raise SystemExit(f"fixture baseline-only 失败：{result}")
    print("PASS baseline-only")

    target_present = load()
    target_present["entries"][0]["status"] = "implemented"
    target_present["entries"][0]["source_version_range"] = "[1.0,)"
    target_present["entries"][0]["target_version_range"] = "[1.0,)"
    target_present["entries"][0]["maven_version_range"] = "[1.0,)"
    target_present["entries"][0]["loader_metadata"]["version_range"] = "[1.0,)"
    target_present["entries"][0]["resolved_target_version"] = "1.0.0"
    print("PASS target-present (implemented/static state)")
    if not validate_document(target_present, EXAMPLE)["ok"]:
        raise SystemExit("fixture target-present 失败")

    wrong_version = load()
    wrong_version["entries"][0]["source_version_range"] = "[1.0,)"
    wrong_version["entries"][0]["target_version_range"] = "[2.0,)"
    wrong_version["entries"][0]["maven_version_range"] = "[2.0,)"
    wrong_version["entries"][0]["loader_metadata"]["version_range"] = "[2.0,)"
    wrong_version["entries"][0]["runtime_checks"].append("blocked: 目标 Mod 实际版本 1.0.0 不满足 [2.0,)")
    wrong_version["entries"][0]["status"] = "blocked"
    wrong_result = validate_document(wrong_version, EXAMPLE)
    if not wrong_result["ok"]:
        raise SystemExit(f"fixture wrong-version 失败：{wrong_result}")
    print("PASS wrong-version (blocked state)")

    side_mismatch = load()
    side_mismatch["entries"][0]["loader_metadata"]["side"] = "CLIENT"
    side_mismatch["entries"][0]["sides"] = ["common", "server"]
    expect_failure(side_mismatch, "side-mismatch", "metadata.side=CLIENT")

    cycle = load()
    cycle["entries"][0]["dependency_graph"]["ordering"] = ["a BEFORE b", "b BEFORE a"]
    expect_failure(cycle, "ordering-cycle", "存在循环")

    insufficient = load()
    insufficient["entries"][0]["status"] = "verified"
    insufficient["entries"][0]["source_version_range"] = "[1.0,)"
    insufficient["entries"][0]["target_version_range"] = "[1.0,)"
    insufficient["entries"][0]["maven_version_range"] = "[1.0,)"
    insufficient["entries"][0]["loader_metadata"]["version_range"] = "[1.0,)"
    insufficient["entries"][0]["resolved_source_version"] = "1.0.0"
    insufficient["entries"][0]["resolved_target_version"] = "1.0.0"
    insufficient["entries"][0]["source_artifact"] = "https://real.example/source.jar"
    insufficient["entries"][0]["target_artifact"] = "https://real.example/target.jar"
    insufficient["entries"][0]["source_sha256"] = "0" * 64
    insufficient["entries"][0]["target_sha256"] = "1" * 64
    insufficient["entries"][0]["evidence"] = [{"type": "build", "source": "build.log", "status": "observed"}]
    expect_failure(insufficient, "verified-evidence", "verified 缺少 declared required observed evidence")

    asymmetry = load()
    asymmetry["entries"][0]["loader_metadata"]["side"] = "CLIENT"
    asymmetry["entries"][0]["sides"] = ["common", "client"]
    asymmetry["entries"][0]["fallback_behavior"]["side_mismatch"] = "dedicated server 不加载 client adapter"
    asymmetry["entries"][0]["status"] = "implemented"
    asymmetry["entries"][0]["source_version_range"] = "[1.0,)"
    asymmetry["entries"][0]["target_version_range"] = "[1.0,)"
    asymmetry["entries"][0]["maven_version_range"] = "[1.0,)"
    asymmetry["entries"][0]["loader_metadata"]["version_range"] = "[1.0,)"
    if not validate_document(asymmetry, EXAMPLE)["ok"]:
        raise SystemExit("fixture client-server-asymmetry 失败")
    print("PASS client-server-asymmetry (metadata state)")


if __name__ == "__main__":
    main()
