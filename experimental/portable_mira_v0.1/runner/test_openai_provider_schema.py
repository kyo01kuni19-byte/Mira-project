from __future__ import annotations

import copy
import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from openai._utils._transform import maybe_transform
from openai.resources.responses.responses import Responses
from openai.types.responses import response_create_params
from pydantic import TypeAdapter

from openai_provider_schema import (
    CANONICAL_SCHEMA_SHA256,
    COMPILER_ID,
    ProviderSchemaCompilationError,
    compile_provider_schema,
    load_provider_schema_artifact,
    write_provider_schema_artifact,
)
from openai_schema_audit import (
    LOCALLY_UNKNOWN,
    PROVIDER_INCOMPATIBLE,
    SDK_LOCAL_ACCEPTANCE_PRINCIPLE,
    audit_schema_constructs,
    collect_schema_constructs,
)
from openai_semantic_adapter import OpenAIAdapterConfig, OpenAISemanticJudgmentAdapter
from semantic_adapter import SemanticJudgmentInput
from semantic_judgment import SemanticJudgmentError, load_json, validate_contract


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = EXPERIMENT_ROOT / "semantic" / "semantic_judgment_contract.schema.json"
PROVIDER_ARTIFACT_PATH = (
    EXPERIMENT_ROOT / "generated" / "openai_semantic_judgment_provider_schema.json"
)
REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "registry_runtime.json"
FIXTURE_PATH = EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "development_cases.json"
FAILURE_PATH = FIXTURE_PATH.parent / "LIVE-SJ-001-TRANSPORT-400.json"
REGISTRY_HASH = "05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a"


def cases() -> dict[str, dict[str, Any]]:
    return {case["case_id"]: case for case in load_json(FIXTURE_PATH)["cases"]}


def provider_schema() -> dict[str, Any]:
    return load_provider_schema_artifact(
        PROVIDER_ARTIFACT_PATH, CANONICAL_PATH, REGISTRY_PATH
    ).provider_schema


def resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise AssertionError(f"unsupported test ref: {ref}")
    value: Any = root
    for part in ref[2:].split("/"):
        value = value[part]
    assert isinstance(value, dict)
    return value


def provider_structurally_accepts(schema: dict[str, Any], value: Any) -> bool:
    root = schema

    def accepts(node: dict[str, Any], candidate: Any) -> bool:
        if "$ref" in node:
            return accepts(resolve_ref(root, node["$ref"]), candidate)
        allowed_type = node.get("type")
        if allowed_type is not None:
            types = allowed_type if isinstance(allowed_type, list) else [allowed_type]
            checks = {
                "object": lambda item: isinstance(item, dict),
                "array": lambda item: isinstance(item, list),
                "string": lambda item: isinstance(item, str),
                "boolean": lambda item: isinstance(item, bool),
                "null": lambda item: item is None,
            }
            if not any(checks[kind](candidate) for kind in types):
                return False
        if "enum" in node and candidate not in node["enum"]:
            return False
        if "const" in node and candidate != node["const"]:
            return False
        if isinstance(candidate, str) and len(candidate) < node.get("minLength", 0):
            return False
        if isinstance(candidate, list):
            if len(candidate) < node.get("minItems", 0):
                return False
            if "maxItems" in node and len(candidate) > node["maxItems"]:
                return False
            if "items" in node and not all(accepts(node["items"], item) for item in candidate):
                return False
        if isinstance(candidate, dict) and "properties" in node:
            properties = node["properties"]
            if any(key not in candidate for key in node.get("required", [])):
                return False
            if node.get("additionalProperties") is False and any(
                key not in properties for key in candidate
            ):
                return False
            for key, child in properties.items():
                if key in candidate and not accepts(child, candidate[key]):
                    return False
        return all(accepts(child, candidate) for child in node.get("allOf", []))

    return accepts(schema, value)


def expect_canonical_failure(judgment: dict[str, Any], text: str) -> None:
    try:
        validate_contract(judgment)
    except SemanticJudgmentError as exc:
        assert text in str(exc)
        return
    raise AssertionError("canonical MIRA validator must fail closed")


def test_ps1_canonical_schema_remains_byte_identical():
    before = CANONICAL_PATH.read_bytes()
    compile_provider_schema(CANONICAL_PATH, REGISTRY_PATH)
    after = CANONICAL_PATH.read_bytes()
    assert before == after
    assert hashlib.sha256(after).hexdigest() == CANONICAL_SCHEMA_SHA256


def test_ps2_compilation_is_byte_and_hash_deterministic():
    first = write_provider_schema_artifact(
        CANONICAL_PATH, REGISTRY_PATH, PROVIDER_ARTIFACT_PATH
    )
    first_bytes = PROVIDER_ARTIFACT_PATH.read_bytes()
    second = write_provider_schema_artifact(
        CANONICAL_PATH, REGISTRY_PATH, PROVIDER_ARTIFACT_PATH
    )
    assert PROVIDER_ARTIFACT_PATH.read_bytes() == first_bytes
    assert first.provider_schema_sha256 == second.provider_schema_sha256
    assert first.compiler_id == second.compiler_id == COMPILER_ID


def test_ps3_provider_schema_excludes_unsupported_conditionals():
    constructs = collect_schema_constructs(provider_schema())
    assert not {"if", "then", "else"} & constructs


def test_ps4_canonical_schema_keeps_conditional_rules():
    constructs = collect_schema_constructs(load_json(CANONICAL_PATH))
    assert {"if", "then"} <= constructs
    audit = audit_schema_constructs(load_json(CANONICAL_PATH))
    assert audit["if"] == PROVIDER_INCOMPATIBLE
    assert audit["then"] == PROVIDER_INCOMPATIBLE
    assert LOCALLY_UNKNOWN in audit.values()


def test_ps5_valid_route_passes_provider_structure_and_canonical_validation():
    judgment = cases()["R1"]["semantic_judgment"]
    assert provider_structurally_accepts(provider_schema(), judgment)
    assert validate_contract(judgment) == judgment


def test_ps6_weaker_provider_route_still_fails_canonical_validation():
    invalid = copy.deepcopy(cases()["R1"]["semantic_judgment"])
    invalid["routing_judgment"]["trigger_candidates"] = []
    assert provider_structurally_accepts(provider_schema(), invalid)
    expect_canonical_failure(invalid, "ROUTE requires at least one trigger candidate")


def test_ps7_no_route_semantics_remain_canonical():
    valid = cases()["C1"]["semantic_judgment"]
    assert provider_structurally_accepts(provider_schema(), valid)
    assert validate_contract(valid) == valid
    invalid = copy.deepcopy(valid)
    invalid["routing_judgment"]["proposed_initial_route"] = "FAILURE"
    assert provider_structurally_accepts(provider_schema(), invalid)
    expect_canonical_failure(invalid, "NO_ROUTE requires proposed_initial_route to be null")


def test_ps8_provider_schema_rejects_added_execution_authorization():
    invalid = copy.deepcopy(cases()["R1"]["semantic_judgment"])
    invalid["routing_judgment"]["execution_authorization"] = True
    assert not provider_structurally_accepts(provider_schema(), invalid)
    expect_canonical_failure(invalid, "forbidden field")


def test_ps9_adapter_request_uses_derived_artifact_schema():
    adapter = OpenAISemanticJudgmentAdapter(
        OpenAIAdapterConfig(model_id="gpt-5.6-sol", reasoning_effort="medium"),
        REGISTRY_PATH,
        CANONICAL_PATH,
        REGISTRY_HASH,
    )
    request, metadata = adapter.build_request(
        SemanticJudgmentInput(
            input_ref="LOCAL-PS9",
            situation="local request reconstruction",
            value_intent=None,
            available_evidence_refs=(),
            authority_context=None,
        )
    )
    artifact = load_json(PROVIDER_ARTIFACT_PATH)
    assert request["text"]["format"]["schema"] == artifact["provider_schema"]
    assert request["text"]["format"]["schema"] != load_json(CANONICAL_PATH)
    assert metadata["provider_schema_sha256"] == artifact["provider_schema_sha256"]
    assert request["model"] == "gpt-5.6-sol"
    assert request["reasoning"] == {"effort": "medium"}
    assert request["tools"] == []
    assert request["store"] is False
    assert adapter.config.transport_max_retries == 0


def test_ps10_sdk_acceptance_is_local_only():
    adapter = OpenAISemanticJudgmentAdapter(
        OpenAIAdapterConfig(model_id="gpt-5.6-sol"),
        REGISTRY_PATH,
        CANONICAL_PATH,
        REGISTRY_HASH,
    )
    request, _ = adapter.build_request(
        SemanticJudgmentInput("LOCAL-PS10", "local", None, (), None)
    )
    validated = TypeAdapter(
        response_create_params.ResponseCreateParamsNonStreaming
    ).validate_python(request)
    transformed = maybe_transform(
        validated, response_create_params.ResponseCreateParamsNonStreaming
    )
    assert transformed["text"]["format"]["strict"] is True
    assert '"/responses"' in inspect.getsource(Responses.create)
    assert SDK_LOCAL_ACCEPTANCE_PRINCIPLE == (
        "SDK_LOCAL_ACCEPTANCE != PROVIDER_SERVER_ACCEPTANCE"
    )


def test_ps11_historical_failure_cause_remains_unknown():
    record = load_json(FAILURE_PATH)
    assert record["unknown"]["rejected_server_parameter"] == "UNKNOWN"
    learning = record["subsequent_failure_learning"]
    assert learning["historical_cause_state"] == "UNKNOWN"
    assert "candidate cause" in learning["learning_hypothesis"]
    assert learning["capability_state"] == "NOT_VERIFIED"


def test_ps12_all_existing_regressions_pass():
    checks = (
        ("runner/test_openai_error_diagnostics.py", "PASS: OpenAI first-error diagnostics"),
        ("runner/test_openai_semantic_adapter.py", "PASS: OpenAI Semantic Judgment Adapter"),
        ("runner/test_semantic_adapter.py", "PASS: First Semantic Judgment Adapter"),
        ("runner/test_semantic_judgment.py", "PASS: Semantic Judgment Contract"),
        ("runner/test_router.py", "PASS: registry-backed router"),
        ("runner/test_registry_loader.py", "PASS: registry loader"),
        ("build/test_build.py", "PASS: build pipeline"),
    )
    for relative_path, expected in checks:
        completed = subprocess.run(
            [sys.executable, str(EXPERIMENT_ROOT / relative_path)],
            cwd=EXPERIMENT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert expected in completed.stdout


if __name__ == "__main__":
    tests = [
        test_ps1_canonical_schema_remains_byte_identical,
        test_ps2_compilation_is_byte_and_hash_deterministic,
        test_ps3_provider_schema_excludes_unsupported_conditionals,
        test_ps4_canonical_schema_keeps_conditional_rules,
        test_ps5_valid_route_passes_provider_structure_and_canonical_validation,
        test_ps6_weaker_provider_route_still_fails_canonical_validation,
        test_ps7_no_route_semantics_remain_canonical,
        test_ps8_provider_schema_rejects_added_execution_authorization,
        test_ps9_adapter_request_uses_derived_artifact_schema,
        test_ps10_sdk_acceptance_is_local_only,
        test_ps11_historical_failure_cause_remains_unknown,
        test_ps12_all_existing_regressions_pass,
    ]
    for test in tests:
        test()
    print("PASS: OpenAI Provider Schema Compiler v0.2 tests (PS1-PS12)")
