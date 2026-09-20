from __future__ import annotations

import copy
from pathlib import Path

from registry_loader import (
    RegistryLoaderError,
    build_registry_runtime,
    canonical_json_bytes,
    compile_registries,
    default_paths,
    load_yaml_source,
    sha256,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
ROUTING_PATH, KNOWLEDGE_PATH, ARTIFACT_PATH = default_paths(EXPERIMENT_ROOT)


def test_valid_current_registries_parse_successfully():
    runtime = compile_registries(load_yaml_source(ROUTING_PATH), load_yaml_source(KNOWLEDGE_PATH))
    assert runtime["schema_version"] == "0.1"
    assert len(runtime["routing"]["normal_edges"]) == 6
    assert runtime["routing"]["value_fit_reentry"]["id"] == "V01_VALUE_CONNECTION"


def test_repeated_builds_are_byte_identical():
    artifact = EXPERIMENT_ROOT / "generated" / "test_registry_runtime_repeated.json"
    first = build_registry_runtime(ROUTING_PATH, KNOWLEDGE_PATH, artifact)
    first_bytes = artifact.read_bytes()
    second = build_registry_runtime(ROUTING_PATH, KNOWLEDGE_PATH, artifact)
    second_bytes = artifact.read_bytes()
    assert first_bytes == second_bytes
    assert first.artifact_hash_sha256 == second.artifact_hash_sha256
    assert sha256(first_bytes) == first.artifact_hash_sha256


def test_duplicate_edge_id_fails_closed():
    routing = load_yaml_source(ROUTING_PATH)
    knowledge = load_yaml_source(KNOWLEDGE_PATH)
    duplicate = copy.deepcopy(routing["edges"][0])
    routing["edges"].append(duplicate)
    try:
        compile_registries(routing, knowledge)
    except RegistryLoaderError as exc:
        assert "Duplicate routing edge id" in str(exc)
        return
    raise AssertionError("duplicate edge id must fail closed")


def test_unresolved_knowledge_address_fails_closed():
    routing = load_yaml_source(ROUTING_PATH)
    knowledge = load_yaml_source(KNOWLEDGE_PATH)
    routing["edges"][0]["knowledge"].append("missing.knowledge.address")
    try:
        compile_registries(routing, knowledge)
    except RegistryLoaderError as exc:
        assert "Unresolved knowledge address" in str(exc)
        return
    raise AssertionError("unresolved knowledge address must fail closed")


def test_value_fit_reentry_remains_distinct_from_normal_edges():
    runtime = compile_registries(load_yaml_source(ROUTING_PATH), load_yaml_source(KNOWLEDGE_PATH))
    normal_ids = {edge["id"] for edge in runtime["routing"]["normal_edges"]}
    value_fit_id = runtime["routing"]["value_fit_reentry"]["id"]
    assert value_fit_id == "V01_VALUE_CONNECTION"
    assert value_fit_id not in normal_ids


def test_input_yaml_files_remain_byte_identical_after_compilation():
    before_routing = ROUTING_PATH.read_bytes()
    before_knowledge = KNOWLEDGE_PATH.read_bytes()
    artifact = EXPERIMENT_ROOT / "generated" / "test_registry_runtime_source_unchanged.json"
    build_registry_runtime(ROUTING_PATH, KNOWLEDGE_PATH, artifact)
    assert ROUTING_PATH.read_bytes() == before_routing
    assert KNOWLEDGE_PATH.read_bytes() == before_knowledge


def test_canonical_json_policy_is_stable():
    runtime = compile_registries(load_yaml_source(ROUTING_PATH), load_yaml_source(KNOWLEDGE_PATH))
    artifact = canonical_json_bytes(runtime)
    assert artifact.endswith(b"\n")
    assert canonical_json_bytes(runtime) == artifact


if __name__ == "__main__":
    test_valid_current_registries_parse_successfully()
    test_repeated_builds_are_byte_identical()
    test_duplicate_edge_id_fails_closed()
    test_unresolved_knowledge_address_fails_closed()
    test_value_fit_reentry_remains_distinct_from_normal_edges()
    test_input_yaml_files_remain_byte_identical_after_compilation()
    test_canonical_json_policy_is_stable()
    result = build_registry_runtime(ROUTING_PATH, KNOWLEDGE_PATH, ARTIFACT_PATH)
    print(f"PASS: registry loader v0.1 deterministic tests {result.artifact_hash_sha256}")
