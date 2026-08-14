#!/usr/bin/env python3
"""Validate a versioned cross-loader/cross-mod compatibility matrix.

The validator is deliberately dependency-free.  It validates the normalized
schema, loader metadata, Maven ranges, ordering cycles, optional artifact
locks, and (when ``--project`` is supplied) the target project's Gradle and
metadata declarations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

LOADERS = {"neoforge", "forge", "cleanroom"}
GAMES = {"neoforge": "1.21.1", "forge": "1.20.1", "cleanroom": "1.12.2"}
JAVAS = {"neoforge": {"21"}, "forge": {"17"}, "cleanroom": {"25"}}
STATUSES = {"planned", "implemented", "built", "launched", "verified", "blocked"}
SCOPES = {"compile", "runtime", "compile_runtime", "optional"}
SURFACES = {
    "registry", "event", "capability", "attachment", "payload", "command", "data",
    "render", "storage", "config", "mixin", "access_transformer",
}
SIDES = {"common", "server", "client"}
METADATA_SIDES = {"CLIENT", "SERVER", "BOTH"}
ORDERINGS = {"BEFORE", "AFTER", "NONE"}
EVIDENCE_TYPES = {
    "official_docs", "source", "javadoc", "artifact", "static", "build", "launch",
    "client", "server", "game_test", "save", "network", "manual",
}
RUNTIME_EVIDENCE_TYPES = {"client", "server", "launch", "game_test"}
VERIFICATION_PROFILES: dict[str, set[str] | None] = {
    "build_client_server": {"build", "client", "server"},
    "build_launch_gametest": {"build", "launch", "game_test"},
    "build_client_only": {"build", "client"},
    "build_server_only": {"build", "server"},
    "build_launch_only": {"build", "launch"},
    "custom": None,
}
REQUIRED_VERIFICATION_FIELDS = {"profile", "required", "not_applicable", "reason"}
REQUIRED_ENTRY_FIELDS = {
    "source", "target", "mod_id", "source_version_range", "target_version_range",
    "resolved_source_version", "resolved_target_version", "source_artifact", "target_artifact",
    "source_sha256", "target_sha256", "license", "artifact_repository", "maven_version_range",
    "dependency_scope", "sides", "loader_metadata", "integration_surfaces", "runtime_checks",
    "adapter", "dependency_graph", "save_schema", "network_schema", "fallback_behavior",
    "verification_requirements", "evidence", "status",
}


def text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def is_placeholder(value: Any) -> bool:
    value = text(value)
    bracket_placeholder = bool(re.fullmatch(r"\[[^,\]]+\]", value))
    return not value or bracket_placeholder or "example.invalid" in value or value in {"TODO", "PLACEHOLDER"}


def endpoint_label(value: Any) -> str:
    if not isinstance(value, dict):
        return "unknown"
    return f"{text(value.get('loader'))}:{text(value.get('minecraft'))}"


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
    java = text(value.get("java"))
    if not java:
        errors.append(f"{name}.java 不能为空")
    elif loader in JAVAS and java not in JAVAS[loader]:
        errors.append(f"{name}.java={java} 不在 {loader} 的允许集合 {sorted(JAVAS[loader])} 中")
    unknown = set(value) - {"loader", "minecraft", "java"}
    if unknown:
        errors.append(f"{name} 包含未知字段：{sorted(unknown)}")
    return errors


def valid_mod_id(value: Any) -> bool:
    return bool(re.fullmatch(r"[a-z][a-z0-9_]{1,63}", text(value)))


def valid_sha(value: Any) -> bool:
    return value is None or bool(re.fullmatch(r"[A-Fa-f0-9]{64}", text(value)))


def valid_maven_range(value: Any) -> bool:
    raw = text(value)
    if is_placeholder(raw):
        return False
    if raw == "":
        return True
    # Accept a single version and the normal Maven interval forms.  This is a
    # syntax check only; the loader resolves the actual range semantics.
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+_-]*", raw):
        return True
    return bool(re.fullmatch(r"[\[(][^,\[\]()]*,[^\[\]()]*[\])]", raw))


def validate_endpoint_pair(entry: dict[str, Any], prefix: str) -> list[str]:
    return [f"{prefix}: {error}" for error in validate_endpoint(entry.get(prefix), prefix)]


def validate_nested_schema(entry: dict[str, Any], field: str, required: Iterable[str]) -> list[str]:
    value = entry.get(field)
    prefix = f"{field}"
    if not isinstance(value, dict):
        return [f"{prefix} 必须是对象"]
    errors = [f"{prefix} 缺少字段：{key}" for key in required if key not in value]
    return errors


def validate_evidence(value: Any, prefix: str) -> list[str]:
    if not isinstance(value, list) or not value:
        return [f"{prefix} 必须是非空对象列表"]
    errors: list[str] = []
    for index, item in enumerate(value):
        path = f"{prefix}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path} 必须是对象")
            continue
        missing = {"type", "source", "status"} - item.keys()
        errors.extend(f"{path} 缺少字段：{field}" for field in sorted(missing))
        if text(item.get("type")) not in EVIDENCE_TYPES:
            errors.append(f"{path}.type 必须是 {sorted(EVIDENCE_TYPES)} 之一")
        if not text(item.get("source")):
            errors.append(f"{path}.source 不能为空")
        if text(item.get("status")) not in {"observed", "planned", "blocked"}:
            errors.append(f"{path}.status 必须是 observed/planned/blocked")
        if item.get("commit") is not None and not text(item.get("commit")):
            errors.append(f"{path}.commit 为空时应使用 null")
    return errors


def validate_verification_requirements(value: Any, prefix: str) -> list[str]:
    """Validate the explicit evidence profile for one matrix row.

    A row must declare whether client/server/launch/GameTest evidence applies;
    a generic ``any one of`` rule is intentionally not accepted.  Known
    profiles provide reproducible combinations, while ``custom`` still needs
    build plus at least one runtime type.
    """

    if not isinstance(value, dict):
        return [f"{prefix} 必须是对象"]
    errors: list[str] = []
    missing = REQUIRED_VERIFICATION_FIELDS - value.keys()
    errors.extend(f"{prefix} 缺少字段：{field}" for field in sorted(missing))
    profile = text(value.get("profile"))
    if profile not in VERIFICATION_PROFILES:
        errors.append(f"{prefix}.profile 必须是 {sorted(VERIFICATION_PROFILES)} 之一")

    def parse_types(field: str, allow_empty: bool = False) -> set[str]:
        raw = value.get(field)
        if not isinstance(raw, list) or (not allow_empty and not raw) or len(set(raw)) != len(raw) or not all(text(item) in EVIDENCE_TYPES for item in raw):
            errors.append(f"{prefix}.{field} 必须是不重复的 evidence type 列表" if allow_empty else f"{prefix}.{field} 必须是非空且不重复的 evidence type 列表")
            return set()
        return {text(item) for item in raw}

    required = parse_types("required")
    not_applicable_set = parse_types("not_applicable", allow_empty=True)
    overlap = required & not_applicable_set
    if overlap:
        errors.append(f"{prefix}.required 与 not_applicable 不能重复：{sorted(overlap)}")
    if not text(value.get("reason")):
        errors.append(f"{prefix}.reason 不能为空")

    expected = VERIFICATION_PROFILES.get(profile)
    if expected is not None and required != expected:
        errors.append(f"{prefix}.required 必须与 profile={profile} 一致：{sorted(expected)}")
    if "build" not in required:
        errors.append(f"{prefix}.required 必须包含 build")
    if not (required & RUNTIME_EVIDENCE_TYPES):
        errors.append(f"{prefix}.required 至少包含一种客户端/服务端/启动/GameTest 证据")
    partition = RUNTIME_EVIDENCE_TYPES - (required | not_applicable_set)
    if partition:
        errors.append(f"{prefix} 必须明确声明适用或不适用的运行证据：{sorted(partition)}")
    return errors


def validate_entry(entry: Any, index: int, expected_source: dict[str, str] | None, expected_target: dict[str, str] | None) -> list[str]:
    prefix = f"entries[{index}]"
    if not isinstance(entry, dict):
        return [f"{prefix} 必须是对象"]
    errors: list[str] = []
    missing = sorted(REQUIRED_ENTRY_FIELDS - entry.keys())
    errors.extend(f"{prefix} 缺少字段：{field}" for field in missing)
    errors.extend(f"{prefix}: {error}" for error in validate_endpoint(entry.get("source"), "source"))
    errors.extend(f"{prefix}: {error}" for error in validate_endpoint(entry.get("target"), "target"))
    source = entry.get("source") if isinstance(entry.get("source"), dict) else {}
    target = entry.get("target") if isinstance(entry.get("target"), dict) else {}
    if expected_source and any(source.get(key) != value for key, value in expected_source.items()):
        errors.append(f"{prefix}: source 与命令行期望不匹配")
    if expected_target and any(target.get(key) != value for key, value in expected_target.items()):
        errors.append(f"{prefix}: target 与命令行期望不匹配")

    mod_id = text(entry.get("mod_id"))
    if not valid_mod_id(mod_id):
        errors.append(f"{prefix}.mod_id 必须是小写 ASCII/数字/下划线且以字母开头")
    for field in ("source_version_range", "target_version_range", "license", "artifact_repository", "adapter"):
        if not text(entry.get(field)):
            errors.append(f"{prefix}.{field} 不能为空")
    for field in ("source_version_range", "target_version_range", "maven_version_range"):
        if not valid_maven_range(entry.get(field)):
            if text(entry.get("status")) in {"planned", "blocked"} and is_placeholder(entry.get(field)):
                pass
            else:
                errors.append(f"{prefix}.{field} 不是有效 Maven version range")
    for field in ("source_sha256", "target_sha256"):
        if not valid_sha(entry.get(field)):
            errors.append(f"{prefix}.{field} 必须是 64 位十六进制或 null")

    scope = text(entry.get("dependency_scope"))
    if scope not in SCOPES:
        errors.append(f"{prefix}.dependency_scope 必须是 {sorted(SCOPES)} 之一")
    sides = entry.get("sides")
    if not isinstance(sides, list) or not sides or len(set(sides)) != len(sides) or not all(text(item) in SIDES for item in sides):
        errors.append(f"{prefix}.sides 必须是非空且不重复的 {sorted(SIDES)} 列表")
    surfaces = entry.get("integration_surfaces")
    if not isinstance(surfaces, list) or not surfaces or len(set(surfaces)) != len(surfaces) or not all(text(item) in SURFACES for item in surfaces):
        errors.append(f"{prefix}.integration_surfaces 包含未知值或为空；允许 {sorted(SURFACES)}")
    runtime = entry.get("runtime_checks")
    if not isinstance(runtime, list) or not runtime or not all(text(item) for item in runtime):
        errors.append(f"{prefix}.runtime_checks 必须是非空字符串列表")

    metadata = entry.get("loader_metadata")
    required_metadata = {"mod_id", "mandatory", "version_range", "ordering", "side"}
    if not isinstance(metadata, dict):
        errors.append(f"{prefix}.loader_metadata 必须是对象")
    else:
        errors.extend(f"{prefix}.loader_metadata 缺少字段：{field}" for field in sorted(required_metadata - metadata.keys()))
        if text(metadata.get("mod_id")) != mod_id:
            errors.append(f"{prefix}.loader_metadata.mod_id 必须等于 mod_id")
        if not isinstance(metadata.get("mandatory"), bool):
            errors.append(f"{prefix}.loader_metadata.mandatory 必须是布尔值")
        if text(metadata.get("version_range")) != text(entry.get("target_version_range")):
            errors.append(f"{prefix}.loader_metadata.version_range 必须与 target_version_range 一致")
        if not valid_maven_range(metadata.get("version_range")) and not (text(entry.get("status")) in {"planned", "blocked"} and is_placeholder(metadata.get("version_range"))):
            errors.append(f"{prefix}.loader_metadata.version_range 不是有效 Maven version range")
        if text(metadata.get("ordering")) not in ORDERINGS:
            errors.append(f"{prefix}.loader_metadata.ordering 必须是 BEFORE/AFTER/NONE")
        if text(metadata.get("side")) not in METADATA_SIDES:
            errors.append(f"{prefix}.loader_metadata.side 必须是 CLIENT/SERVER/BOTH")
        if metadata.get("mandatory") is True and scope == "optional":
            errors.append(f"{prefix}: optional scope 不能设置 mandatory=true")
        if text(metadata.get("side")) == "CLIENT" and "client" not in sides:
            errors.append(f"{prefix}: metadata.side=CLIENT 但 sides 未包含 client")
        if text(metadata.get("side")) == "SERVER" and "server" not in sides:
            errors.append(f"{prefix}: metadata.side=SERVER 但 sides 未包含 server")
        raw_fields = metadata.get("raw_fields")
        if raw_fields is not None and not isinstance(raw_fields, dict):
            errors.append(f"{prefix}.loader_metadata.raw_fields 必须是对象")

    for field in ("dependency_graph", "save_schema", "network_schema", "fallback_behavior"):
        errors.extend(f"{prefix}: {error}" for error in validate_nested_schema(entry, field, {
            "dependency_graph": {"requires", "ordering", "conflicts"},
            "save_schema": {"format", "version", "migration"},
            "network_schema": {"format", "version", "migration"},
            "fallback_behavior": {"missing_mod", "wrong_version", "side_mismatch"},
        }[field]))
    graph = entry.get("dependency_graph")
    if isinstance(graph, dict):
        for key in ("requires", "ordering", "conflicts"):
            if not isinstance(graph.get(key), list) or not all(text(item) for item in graph.get(key, [])):
                errors.append(f"{prefix}.dependency_graph.{key} 必须是字符串列表")

    evidence_errors = validate_evidence(entry.get("evidence"), f"{prefix}.evidence")
    errors.extend(evidence_errors)
    errors.extend(validate_verification_requirements(entry.get("verification_requirements"), f"{prefix}.verification_requirements"))
    status = text(entry.get("status"))
    if status not in STATUSES:
        errors.append(f"{prefix}.status 必须是 {sorted(STATUSES)} 之一")
    if status == "verified":
        evidence_types = {item.get("type") for item in entry.get("evidence", []) if isinstance(item, dict) and item.get("status") == "observed"}
        requirements = entry.get("verification_requirements") if isinstance(entry.get("verification_requirements"), dict) else {}
        required = {text(item) for item in requirements.get("required", []) if text(item)}
        missing = sorted(required - evidence_types)
        if missing:
            errors.append(f"{prefix}: verified 缺少 declared required observed evidence：{', '.join(missing)}")
        contradictory = sorted(evidence_types & {text(item) for item in requirements.get("not_applicable", []) if text(item)})
        if contradictory:
            errors.append(f"{prefix}: verified 出现标记为 not_applicable 的 observed evidence：{', '.join(contradictory)}")
    if status == "blocked":
        joined = " ".join(text(item) for item in runtime) if isinstance(runtime, list) else ""
        if "blocked" not in joined.casefold() and "缺失" not in joined and "阻塞" not in joined:
            errors.append(f"{prefix}: blocked 必须在 runtime_checks 中说明阻塞原因")
    if status in {"built", "launched", "verified"}:
        for field in ("resolved_source_version", "resolved_target_version", "source_sha256", "target_sha256"):
            if entry.get(field) in (None, ""):
                errors.append(f"{prefix}: {status} 状态必须填写 {field}")
        if is_placeholder(entry.get("source_artifact")) or is_placeholder(entry.get("target_artifact")):
            errors.append(f"{prefix}: {status} 状态不能使用占位构件 URL")
    return errors


def ordering_edges(entries: Iterable[dict[str, Any]]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for entry in entries:
        graph.setdefault(text(entry.get("mod_id")), set())
        dependency_graph = entry.get("dependency_graph")
        values = dependency_graph.get("ordering", []) if isinstance(dependency_graph, dict) else []
        for statement in values:
            match = re.fullmatch(r"([^\s]+)\s+(BEFORE|AFTER)\s+([^\s]+)", text(statement), re.IGNORECASE)
            if not match:
                continue
            left, ordering, right = match.groups()
            graph.setdefault(left, set())
            graph.setdefault(right, set())
            if ordering.upper() == "BEFORE":
                graph[left].add(right)
            else:
                graph[right].add(left)
    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    state: dict[str, int] = {}
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for child in sorted(graph.get(node, set())):
            if state.get(child, 0) == 0:
                visit(child)
            elif state.get(child) == 1 and child in stack:
                cycles.append(stack[stack.index(child):] + [child])
        stack.pop()
        state[node] = 2

    for node in sorted(graph):
        if state.get(node, 0) == 0:
            visit(node)
    return cycles


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ERROR: 无法读取 JSON：{exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("ERROR: JSON 根节点必须是对象")
    return value


def load_artifact_lock(matrix_path: Path, document: dict[str, Any], explicit: Path | None) -> tuple[dict[str, Any] | None, list[str]]:
    reference = explicit
    if reference is None and text(document.get("artifact_lock")):
        reference = Path(text(document["artifact_lock"]))
    if reference is None:
        return None, []
    if not reference.is_absolute():
        reference = matrix_path.parent / reference
    if not reference.is_file():
        return None, [f"artifact lock 不存在：{reference}"]
    return load_json(reference), []


def validate_lock(lock: dict[str, Any], matrix_path: Path) -> list[str]:
    errors: list[str] = []
    artifacts = lock.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return ["artifact lock 的 artifacts 必须是非空列表"]
    seen: set[str] = set()
    for index, artifact in enumerate(artifacts):
        prefix = f"artifact_lock.artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{prefix} 必须是对象")
            continue
        artifact_id = text(artifact.get("artifact_id"))
        if not artifact_id or artifact_id in seen:
            errors.append(f"{prefix}.artifact_id 必须非空且唯一")
        seen.add(artifact_id)
        if text(artifact.get("loader")) not in LOADERS:
            errors.append(f"{prefix}.loader 无效")
        if not text(artifact.get("minecraft")):
            errors.append(f"{prefix}.minecraft 不能为空")
        if artifact.get("sha256") is not None and not valid_sha(artifact.get("sha256")):
            errors.append(f"{prefix}.sha256 必须是 64 位十六进制或 null")
        if not text(artifact.get("license")):
            errors.append(f"{prefix}.license 不能为空")
        local = text(artifact.get("path")) or text(artifact.get("url"))
        if local and "://" not in local and not local.startswith("mvn:"):
            artifact_path = Path(local)
            if not artifact_path.is_absolute():
                artifact_path = matrix_path.parent / artifact_path
            if artifact_path.is_file() and artifact.get("sha256"):
                digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
                if digest.casefold() != text(artifact.get("sha256")).casefold():
                    errors.append(f"{prefix}: 本地构件 SHA-256 不匹配")
    return errors


def validate_entry_locks(lock: dict[str, Any], entries: list[dict[str, Any]]) -> list[str]:
    """Ensure every resolved artifact reference points at the right lock row."""
    by_id = {
        text(item.get("artifact_id")): item
        for item in lock.get("artifacts", [])
        if isinstance(item, dict) and text(item.get("artifact_id"))
    }
    errors: list[str] = []
    for index, entry in enumerate(entries):
        for side in ("source", "target"):
            ref = text(entry.get(f"{side}_artifact_ref"))
            if not ref:
                if text(entry.get("status")) in {"built", "launched", "verified"}:
                    errors.append(f"entries[{index}].{side}_artifact_ref 不能为空（已进入构建/运行状态）")
                continue
            artifact = by_id.get(ref)
            if artifact is None:
                errors.append(f"entries[{index}].{side}_artifact_ref 未在 artifact lock 中找到：{ref}")
                continue
            status = text(entry.get("status"))
            if status in {"built", "launched", "verified"}:
                if not text(artifact.get("resolved_version")):
                    errors.append(f"entries[{index}].{side}_artifact_ref 缺少锁定 resolved_version")
                if not valid_sha(artifact.get("sha256")) or artifact.get("sha256") is None:
                    errors.append(f"entries[{index}].{side}_artifact_ref 缺少锁定 sha256")
                if is_placeholder(artifact.get("url")) and is_placeholder(artifact.get("coordinate")):
                    errors.append(f"entries[{index}].{side}_artifact_ref 缺少真实构件来源")
            endpoint = entry.get(side) if isinstance(entry.get(side), dict) else {}
            for key in ("mod_id", "loader", "minecraft"):
                expected = text(entry.get("mod_id")) if key == "mod_id" else text(endpoint.get(key))
                if text(artifact.get(key)) != expected:
                    errors.append(f"entries[{index}].{side}_artifact_ref 的 {key} 与矩阵不一致")
            resolved = entry.get(f"resolved_{side}_version")
            locked = artifact.get("resolved_version")
            if resolved not in (None, "") and locked not in (None, "") and text(resolved) != text(locked):
                errors.append(f"entries[{index}].{side} resolved_version 与 artifact lock 不一致")
            checksum = entry.get(f"{side}_sha256")
            locked_checksum = artifact.get("sha256")
            if checksum not in (None, "") and locked_checksum not in (None, "") and text(checksum).casefold() != text(locked_checksum).casefold():
                errors.append(f"entries[{index}].{side}_sha256 与 artifact lock 不一致")
    return errors


def parse_endpoint(value: str | None, name: str) -> dict[str, str] | None:
    if not value:
        return None
    parts = value.split(":")
    if len(parts) != 2 or parts[0] not in LOADERS or parts[1] != GAMES[parts[0]]:
        raise SystemExit(f"ERROR: --{name} 必须是 loader:minecraft，例如 neoforge:1.21.1")
    return {"loader": parts[0], "minecraft": parts[1]}


def inspect_project(project: Path, target: dict[str, str], entries: list[dict[str, Any]]) -> list[str]:
    """Check the active target project without changing it."""
    errors: list[str] = []
    if not project.is_dir():
        return [f"project 不存在：{project}"]
    try:
        from validate_loader import detect_project
        detection = detect_project(project)
        if detection.get("loader") != target.get("loader"):
            errors.append(f"project loader={detection.get('loader')} 与 target={target.get('loader')} 不一致")
        if detection.get("minecraft") and detection.get("minecraft") != target.get("minecraft"):
            errors.append(f"project Minecraft={detection.get('minecraft')} 与 target={target.get('minecraft')} 不一致")
    except Exception as exc:  # pragma: no cover - a diagnostic path
        errors.append(f"project loader 检查失败：{exc}")

    files = [path for path in project.rglob("*") if path.is_file() and ".git" not in path.parts and "build" not in path.parts and ".gradle" not in path.parts]
    texts: list[tuple[Path, str]] = []
    for path in files:
        if path.suffix in {".gradle", ".kts", ".toml", ".json", ".properties", ".java"} or path.name in {"mcmod.info"}:
            try:
                texts.append((path, path.read_text(encoding="utf-8", errors="replace")))
            except OSError:
                pass
    joined = "\n".join(content for _path, content in texts)
    source_files = [path for path, _content in texts if path.suffix == ".java"]
    source_joined = "\n".join(content for path, content in texts if path.suffix == ".java")
    target_loader = text(target.get("loader"))
    forbidden_imports = {
        "neoforge": ("net.minecraftforge.", "com.cleanroommc."),
        "forge": ("net.neoforged.", "com.cleanroommc."),
        "cleanroom": ("net.neoforged.",),
    }.get(target_loader, ())
    for forbidden in forbidden_imports:
        if forbidden in source_joined:
            errors.append(f"target {target_loader} 源码发现跨 loader import：{forbidden}")
    if target_loader == "neoforge" and "mods.toml" in "\n".join(path.name for path, _content in texts) and "neoforge.mods.toml" not in "\n".join(path.name for path, _content in texts):
        errors.append("NeoForge target 缺少 neoforge.mods.toml")
    if target_loader == "forge" and "neoforge.mods.toml" in "\n".join(path.name for path, _content in texts):
        errors.append("Forge target 不应使用 neoforge.mods.toml")
    if target_loader == "cleanroom" and ("fg.deobf" in joined or "rfg.deobf" in joined):
        errors.append("Cleanroom target 不应使用 fg.deobf()/rfg.deobf()")
    for entry in entries:
        mod_id = text(entry.get("mod_id"))
        scope = text(entry.get("dependency_scope"))
        if scope != "optional" and mod_id not in joined:
            errors.append(f"project 未发现非 optional 联动依赖 {mod_id}")
        metadata = entry.get("loader_metadata")
        metadata_name = "neoforge.mods.toml" if target.get("loader") == "neoforge" else "mods.toml" if target.get("loader") == "forge" else "mcmod.info"
        metadata_files = [path for path, content in texts if path.name == metadata_name]
        if metadata_files and mod_id not in "\n".join(content for path, content in texts if path.name == metadata_name):
            if scope != "optional":
                errors.append(f"{metadata_name} 未声明联动 Mod {mod_id}")
        adapter = text(entry.get("adapter"))
        adapter_path = project / adapter
        if text(entry.get("status")) in {"implemented", "built", "launched", "verified"} and not adapter_path.exists():
            errors.append(f"adapter 路径不存在：{adapter_path}")
        if text(entry.get("status")) in {"implemented", "built", "launched", "verified"} and adapter and not any(path == adapter_path or adapter_path in path.parents for path in source_files):
            errors.append(f"adapter 路径未包含 Java 源文件：{adapter_path}")
        if isinstance(metadata, dict) and metadata.get("side") == "CLIENT":
            if "client" not in entry.get("sides", []):
                errors.append(f"{mod_id}: CLIENT metadata 与 sides 不一致")
    return errors


def validate_document(document: dict[str, Any], matrix_path: Path, expected_source: dict[str, str] | None = None, expected_target: dict[str, str] | None = None, mod_id_filter: str | None = None, artifact_lock: Path | None = None, project: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    schema_version = document.get("schema_version")
    if schema_version != 2:
        errors.append(f"schema_version 必须为 2，实际为 {schema_version!r}；请迁移到 v2 字段")
    project_mod_id = text(document.get("project_mod_id"))
    if not valid_mod_id(project_mod_id):
        errors.append("project_mod_id 必须是小写 ASCII/数字/下划线且以字母开头")
    entries = document.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("entries 必须是非空列表")
        entries = []
    selected = [entry for entry in entries if isinstance(entry, dict) and (not mod_id_filter or entry.get("mod_id") == mod_id_filter) and (not expected_source or isinstance(entry.get("source"), dict) and all(entry["source"].get(k) == v for k, v in expected_source.items())) and (not expected_target or isinstance(entry.get("target"), dict) and all(entry["target"].get(k) == v for k, v in expected_target.items()))]
    if not selected:
        errors.append("没有匹配命令行筛选条件的矩阵行")
    for index, entry in enumerate(entries):
        if entry in selected:
            errors.extend(validate_entry(entry, index, expected_source, expected_target))

    seen: set[tuple[str, str, str]] = set()
    for index, entry in enumerate(selected):
        if not isinstance(entry, dict):
            continue
        key = (text(entry.get("mod_id")), endpoint_label(entry.get("source")), endpoint_label(entry.get("target")))
        if key in seen:
            errors.append(f"重复矩阵行：entries[{index}] {key[0]} {key[1]} -> {key[2]}")
        seen.add(key)
    cycles = find_cycles(ordering_edges(entry for entry in selected if isinstance(entry, dict)))
    if cycles:
        errors.extend(f"dependency_graph.ordering 存在循环：{' -> '.join(cycle)}" for cycle in cycles)

    lock, lock_errors = load_artifact_lock(matrix_path, document, artifact_lock)
    errors.extend(lock_errors)
    if lock is not None:
        errors.extend(validate_lock(lock, matrix_path))
        errors.extend(validate_entry_locks(lock, [entry for entry in selected if isinstance(entry, dict)]))
    if project is not None:
        inferred_targets = {
            (text(entry.get("target", {}).get("loader")), text(entry.get("target", {}).get("minecraft")))
            for entry in selected if isinstance(entry, dict) and isinstance(entry.get("target"), dict)
        }
        project_target = expected_target
        if project_target is None and len(inferred_targets) == 1:
            loader, minecraft = next(iter(inferred_targets))
            project_target = {"loader": loader, "minecraft": minecraft}
        if project_target is None:
            errors.append("--project 需要 --target，或矩阵筛选后只能剩余一个 target")
        else:
            errors.extend(inspect_project(project.resolve(), project_target, [entry for entry in selected if isinstance(entry, dict)]))
    for entry in selected:
        if isinstance(entry, dict) and text(entry.get("status")) == "planned":
            if is_placeholder(entry.get("source_artifact")) or is_placeholder(entry.get("target_artifact")):
                warnings.append(f"{entry.get('mod_id')}: planned 行仍使用占位构件，完成构件锁定后再升级状态")
    return {
        "matrix": str(matrix_path.resolve()),
        "schema_version": schema_version,
        "entry_count": len(entries),
        "selected_count": len(selected),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matrix", type=Path, help="compatibility-matrix.json")
    parser.add_argument("--source", help="限制有向源端，例如 neoforge:1.21.1")
    parser.add_argument("--target", help="限制有向目标端，例如 forge:1.20.1")
    parser.add_argument("--mod-id", help="只检查指定联动 Mod")
    parser.add_argument("--project", type=Path, help="可选：检查目标项目的 Gradle、metadata 和 adapter")
    parser.add_argument("--artifact-lock", type=Path, help="可选：覆盖 matrix 中的 artifact_lock 文件")
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果")
    args = parser.parse_args()
    if not args.matrix.is_file():
        raise SystemExit(f"ERROR: 矩阵不存在：{args.matrix}")
    document = load_json(args.matrix)
    result = validate_document(document, args.matrix, parse_endpoint(args.source, "source"), parse_endpoint(args.target, "target"), args.mod_id, args.artifact_lock, args.project)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"matrix: {result['matrix']}")
        print(f"schema: {result['schema_version']}")
        print(f"entries: {result['entry_count']} (selected={result['selected_count']})")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")
        for error in result["errors"]:
            print(f"ERROR: {error}")
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
