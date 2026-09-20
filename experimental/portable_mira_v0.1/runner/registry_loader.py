from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class RegistryLoaderError(Exception):
    """Registry validation or deterministic compilation failure."""


@dataclass(frozen=True)
class RegistryBuildResult:
    artifact_path: Path
    artifact_hash_sha256: str
    artifact_bytes: int
    repeated_hash_sha256: str
    repeated_bytes_equal: bool
    readback_bytes_equal: bool
    readback_hash_equal: bool
    build_status: str


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_yaml_source(path: Path) -> Any:
    with path.open("rb") as source_file:
        loaded = yaml.safe_load(source_file)
    if loaded is None:
        raise RegistryLoaderError(f"YAML source is empty: {path}")
    return loaded


def compile_registries(routing_source: Any, knowledge_source: Any) -> dict[str, Any]:
    if not isinstance(routing_source, dict):
        raise RegistryLoaderError("routing_edges.yaml root must be a mapping")
    if not isinstance(knowledge_source, dict):
        raise RegistryLoaderError("knowledge_registry.yaml root must be a mapping")

    edges = routing_source.get("edges")
    if not isinstance(edges, list):
        raise RegistryLoaderError("routing_edges.yaml field 'edges' must be a list")

    value_fit_reentry = routing_source.get("value_fit_reentry")
    if not isinstance(value_fit_reentry, dict):
        raise RegistryLoaderError("routing_edges.yaml field 'value_fit_reentry' must be a mapping")

    knowledge_registry = knowledge_source.get("knowledge")
    if not isinstance(knowledge_registry, dict):
        raise RegistryLoaderError("knowledge_registry.yaml field 'knowledge' must be a mapping")

    normal_edges = [_validate_edge(edge, index) for index, edge in enumerate(edges)]
    _validate_unique_edge_ids(normal_edges)

    value_fit_runtime = _validate_value_fit_reentry(value_fit_reentry)

    referenced_addresses = _collect_referenced_knowledge(normal_edges, value_fit_runtime)
    unresolved = [address for address in referenced_addresses if address not in knowledge_registry]
    if unresolved:
        raise RegistryLoaderError(
            "Unresolved knowledge address(es): " + ", ".join(unresolved)
        )

    resolved_knowledge = {
        address: knowledge_registry[address] for address in referenced_addresses
    }

    return {
        "artifact_type": "portable_mira.registry_runtime",
        "schema_version": "0.1",
        "source_authority": {
            "generated_json_is_authority": False,
            "routing_edges": "runtime/routing_edges.yaml",
            "knowledge_registry": "runtime/knowledge_registry.yaml",
        },
        "routing": {
            "normal_edges": normal_edges,
            "value_fit_reentry": value_fit_runtime,
        },
        "knowledge": {
            "referenced_addresses": referenced_addresses,
            "resolved_registry_entries": resolved_knowledge,
        },
    }


def _validate_edge(edge: Any, index: int) -> dict[str, Any]:
    if not isinstance(edge, dict):
        raise RegistryLoaderError(f"routing edge at index {index} must be a mapping")

    for field in ("id", "from", "trigger", "to"):
        if field not in edge:
            raise RegistryLoaderError(f"routing edge at index {index} missing required field: {field}")
        if not isinstance(edge[field], str) or not edge[field]:
            raise RegistryLoaderError(
                f"routing edge at index {index} field '{field}' must be a non-empty string"
            )

    knowledge = edge.get("knowledge", [])
    if not isinstance(knowledge, list) or not all(isinstance(item, str) for item in knowledge):
        raise RegistryLoaderError(
            f"routing edge {edge['id']} field 'knowledge' must be a list of strings"
        )

    return copy.deepcopy(edge)


def _validate_unique_edge_ids(edges: list[dict[str, Any]]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for edge in edges:
        edge_id = edge["id"]
        if edge_id in seen and edge_id not in duplicates:
            duplicates.append(edge_id)
        seen.add(edge_id)
    if duplicates:
        raise RegistryLoaderError("Duplicate routing edge id(s): " + ", ".join(duplicates))


def _validate_value_fit_reentry(value_fit_reentry: dict[str, Any]) -> dict[str, Any]:
    for field in ("id", "trigger", "to"):
        if field not in value_fit_reentry:
            raise RegistryLoaderError(f"value_fit_reentry missing required field: {field}")
        if not isinstance(value_fit_reentry[field], str) or not value_fit_reentry[field]:
            raise RegistryLoaderError(
                f"value_fit_reentry field '{field}' must be a non-empty string"
            )

    knowledge = value_fit_reentry.get("knowledge", [])
    if not isinstance(knowledge, list) or not all(isinstance(item, str) for item in knowledge):
        raise RegistryLoaderError("value_fit_reentry field 'knowledge' must be a list of strings")

    return copy.deepcopy(value_fit_reentry)


def _collect_referenced_knowledge(
    normal_edges: list[dict[str, Any]], value_fit_reentry: dict[str, Any]
) -> list[str]:
    addresses: list[str] = []
    for edge in normal_edges:
        for address in edge.get("knowledge", []):
            if address not in addresses:
                addresses.append(address)
    for address in value_fit_reentry.get("knowledge", []):
        if address not in addresses:
            addresses.append(address)
    return addresses


def canonical_json_bytes(runtime: dict[str, Any]) -> bytes:
    text = json.dumps(runtime, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return (text + "\n").encode("utf-8")


def build_registry_runtime(
    routing_path: Path, knowledge_path: Path, artifact_path: Path
) -> RegistryBuildResult:
    runtime = compile_registries(load_yaml_source(routing_path), load_yaml_source(knowledge_path))
    artifact = canonical_json_bytes(runtime)
    artifact_hash = sha256(artifact)

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(artifact)

    readback = artifact_path.read_bytes()
    readback_hash = sha256(readback)
    if readback != artifact:
        raise RegistryLoaderError("Local artifact read-back changed bytes")
    if readback_hash != artifact_hash:
        raise RegistryLoaderError("Local artifact read-back SHA-256 mismatch")

    repeated_runtime = compile_registries(load_yaml_source(routing_path), load_yaml_source(knowledge_path))
    repeated_artifact = canonical_json_bytes(repeated_runtime)
    repeated_hash = sha256(repeated_artifact)
    if repeated_artifact != artifact:
        raise RegistryLoaderError("Repeated registry build changed artifact bytes")
    if repeated_hash != artifact_hash:
        raise RegistryLoaderError("Repeated registry build SHA-256 mismatch")

    return RegistryBuildResult(
        artifact_path=artifact_path,
        artifact_hash_sha256=artifact_hash,
        artifact_bytes=len(artifact),
        repeated_hash_sha256=repeated_hash,
        repeated_bytes_equal=repeated_artifact == artifact,
        readback_bytes_equal=readback == artifact,
        readback_hash_equal=readback_hash == artifact_hash,
        build_status="PASS",
    )


def default_paths(root: Path) -> tuple[Path, Path, Path]:
    return (
        root / "runtime" / "routing_edges.yaml",
        root / "runtime" / "knowledge_registry.yaml",
        root / "generated" / "registry_runtime.json",
    )


if __name__ == "__main__":
    experiment_root = Path(__file__).resolve().parents[1]
    result = build_registry_runtime(*default_paths(experiment_root))
    print(f"PASS: registry loader v0.1 {result.artifact_hash_sha256}")
