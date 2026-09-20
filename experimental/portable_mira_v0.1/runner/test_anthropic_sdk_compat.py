from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import anthropic
from anthropic._utils import maybe_transform
from anthropic.resources.messages.messages import Messages
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.output_config_param import OutputConfigParam
from anthropic.types.json_output_format_param import JSONOutputFormatParam
from pydantic import TypeAdapter

from anthropic_output_annotator import (
    AnthropicAnnotatorConfig,
    AnthropicAnnotatorError,
    AnthropicOutputAnnotator,
)
from anthropic_provider_schema import (
    CANONICAL_SCHEMA_SHA256,
    LOCALLY_UNKNOWN,
    PROVIDER_COMPATIBLE,
    PROVIDER_INCOMPATIBLE,
    PROVIDER_TRANSFORMABLE,
    SDK_LOCAL_ACCEPTANCE_PRINCIPLE,
    audit_schema_constructs,
    collect_schema_constructs,
    compile_provider_schema,
    load_provider_schema_artifact,
    write_provider_schema_artifact,
)
from output_annotator import (
    OutputAnnotationInput,
    OutputAnnotator,
    file_sha256,
    payload_sha256,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = EXPERIMENT_ROOT / "semantic" / "output_annotation_contract.schema.json"
PROVIDER_ARTIFACT_PATH = (
    EXPERIMENT_ROOT / "generated" / "anthropic_output_annotation_provider_schema.json"
)
DEVELOPMENT_PATH = (
    EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "development_cases.json"
)


def development_input() -> OutputAnnotationInput:
    cases = json.loads(DEVELOPMENT_PATH.read_text(encoding="utf-8"))
    assert cases["classification"] == "DEVELOPMENT_REGRESSION_NOT_HOLDOUT"
    case = next(item for item in cases["cases"] if item["case_id"] == "R1")
    output = case["semantic_judgment"]
    case_payload = {"case_id": "R1", "natural_situation": case["situation"]}
    return OutputAnnotationInput(
        case_id="R1",
        natural_situation=case["situation"],
        preserved_semantic_agent_output=output,
        case_sha256=payload_sha256(case_payload),
        raw_output_sha256=payload_sha256(output),
        annotation_schema_sha256=file_sha256(CANONICAL_PATH),
        governance_baseline_commit="5d5290913b8a80898ef6e1a4e7eec3cc5f534808",
        evaluation_baseline_commit="cde62fdd47d7a19176d9c0d8907494d5a85787f1",
    )


def candidate(model_id: str = "claude-sonnet-5") -> AnthropicOutputAnnotator:
    return AnthropicOutputAnnotator(
        AnthropicAnnotatorConfig(model_id=model_id),
        CANONICAL_PATH,
        PROVIDER_ARTIFACT_PATH,
    )


def request() -> dict[str, Any]:
    return candidate().build_dry_run(development_input()).request


def test_ac1_official_anthropic_sdk_imports():
    assert anthropic.__name__ == "anthropic"
    assert Path(anthropic.__file__).resolve().is_relative_to(
        (EXPERIMENT_ROOT.parents[1] / ".venv").resolve()
    )


def test_ac2_installed_sdk_version_is_observable():
    assert anthropic.__version__ == "1.7.0"
    assert candidate().build_dry_run(development_input()).observable_configuration[
        "anthropic_sdk_version"
    ] == "1.7.0"


def test_ac3_candidate_model_remains_injectable():
    assert candidate("claude-sonnet-5").build_dry_run(development_input()).request[
        "model"
    ] == "claude-sonnet-5"
    assert candidate("injectable-model").build_dry_run(development_input()).request[
        "model"
    ] == "injectable-model"


def test_ac4_installed_sdk_accepts_messages_request_shape_locally():
    value = request()
    assert "temperature" not in value
    assert "temperature" not in inspect.signature(Messages.create).parameters
    TypeAdapter(MessageCreateParamsNonStreaming).validate_python(value)
    transformed = maybe_transform(value, MessageCreateParamsNonStreaming)
    assert transformed["output_config"]["format"]["type"] == "json_schema"
    assert set(value) <= set(inspect.signature(Messages.create).parameters)


def test_ac5_structured_output_mechanism_is_locally_verified():
    value = request()
    output_config = value["output_config"]
    TypeAdapter(OutputConfigParam).validate_python(output_config)
    TypeAdapter(JSONOutputFormatParam).validate_python(output_config["format"])
    assert "output_config" in inspect.signature(Messages.create).parameters
    assert hasattr(Messages, "parse")
    assert "output_format" in inspect.signature(Messages.parse).parameters
    assert callable(anthropic.transform_schema)


def test_ac6_canonical_annotation_contract_remains_byte_identical():
    before = CANONICAL_PATH.read_bytes()
    compile_provider_schema(CANONICAL_PATH)
    assert CANONICAL_PATH.read_bytes() == before
    assert hashlib.sha256(before).hexdigest() == CANONICAL_SCHEMA_SHA256


def test_ac7_provider_representation_is_deterministic():
    first = write_provider_schema_artifact(CANONICAL_PATH, PROVIDER_ARTIFACT_PATH)
    first_bytes = PROVIDER_ARTIFACT_PATH.read_bytes()
    second = write_provider_schema_artifact(CANONICAL_PATH, PROVIDER_ARTIFACT_PATH)
    assert PROVIDER_ARTIFACT_PATH.read_bytes() == first_bytes
    assert first.provider_schema_sha256 == second.provider_schema_sha256
    loaded = load_provider_schema_artifact(PROVIDER_ARTIFACT_PATH, CANONICAL_PATH)
    assert loaded.artifact() == first.artifact()


def test_ac8_provider_transformation_cannot_bypass_canonical_validation():
    artifact = load_provider_schema_artifact(PROVIDER_ARTIFACT_PATH, CANONICAL_PATH)
    assert artifact.artifact()["canonical_post_validation_required"] is True
    try:
        candidate().validate_provider_output(
            {"provider_shape_only": True}, annotation_input=development_input()
        )
    except AnthropicAnnotatorError as exc:
        assert exc.state == "CANONICAL_VALIDATION_FAILED"
        return
    raise AssertionError("provider-shaped output must not bypass canonical validation")


def test_ac9_blindness_survives_actual_request_construction():
    value = request()
    content = json.loads(value["messages"][0]["content"])
    assert set(content) == {
        "natural_situation",
        "preserved_semantic_agent_output",
    }
    serialized = json.dumps(value, sort_keys=True)
    for forbidden in (
        "sealed_expectation",
        "expected_route",
        "expected_trigger",
        "expected_diagnostic",
        "evaluator_result",
        "desired_answer",
        "disagreement_review_conclusion",
    ):
        assert forbidden not in serialized


def test_ac10_no_prohibited_provider_capability_is_configured():
    value = request()
    assert set(value) == {
        "model",
        "max_tokens",
        "system",
        "messages",
        "output_config",
    }
    assert [message["role"] for message in value["messages"]] == ["user"]
    for key in (
        "tools",
        "tool_choice",
        "thinking",
        "citations",
        "web_search",
        "retrieval",
    ):
        assert key not in value


def test_ac11_compatibility_requires_and_accesses_no_credential():
    source = inspect.getsource(sys.modules["anthropic_output_annotator"])
    assert "ANTHROPIC_API_KEY" not in source
    assert "os.environ" not in source
    assert "getenv" not in source
    dry = candidate().build_dry_run(development_input())
    assert dry.credential_accessed is False


def test_ac12_local_compatibility_performs_no_network_request():
    calls: list[object] = []
    original = Messages.create

    def forbidden_network(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Messages.create must not be called")

    Messages.create = forbidden_network
    try:
        dry = candidate().build_dry_run(development_input())
    finally:
        Messages.create = original
    assert calls == []
    assert dry.network_call_performed is False


def test_ac13_output_annotator_remains_provider_independent():
    assert isinstance(candidate(), OutputAnnotator)
    assert "anthropic" not in inspect.getsource(OutputAnnotator).lower()


def test_ac14_sdk_acceptance_and_server_acceptance_remain_distinct():
    metadata = candidate().build_dry_run(development_input()).observable_configuration
    assert SDK_LOCAL_ACCEPTANCE_PRINCIPLE == (
        "SDK_LOCAL_ACCEPTANCE != PROVIDER_SERVER_ACCEPTANCE"
    )
    assert metadata["provider_server_compatibility"] == "UNKNOWN"
    assert metadata["sdk_acceptance_principle"] == SDK_LOCAL_ACCEPTANCE_PRINCIPLE
    schema = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
    audit = audit_schema_constructs(schema)
    assert set(audit) == collect_schema_constructs(schema)
    assert audit["type"] == PROVIDER_COMPATIBLE
    assert audit["const"] == PROVIDER_TRANSFORMABLE
    assert audit["minLength"] == PROVIDER_INCOMPATIBLE
    assert audit["pattern"] == PROVIDER_INCOMPATIBLE
    assert LOCALLY_UNKNOWN not in audit.values()


def test_ac15_all_frozen_regressions_pass():
    checks = (
        ("runner/test_output_annotator.py", "PASS: Output Annotator"),
        ("runner/test_holdout_governance.py", "PASS: Holdout Annotation Governance"),
        ("runner/test_counter_failure_eval.py", "PASS: Counter-Failure Evaluation"),
        ("runner/test_route_boundary.py", "PASS: Semantic route vocabulary boundary"),
        ("runner/test_openai_provider_schema.py", "PASS: OpenAI Provider Schema Compiler"),
        ("runner/test_openai_error_diagnostics.py", "PASS: OpenAI first-error diagnostics"),
        ("runner/test_openai_semantic_adapter.py", "PASS: OpenAI Semantic Judgment Adapter"),
        ("runner/test_semantic_adapter.py", "PASS: First Semantic Judgment Adapter"),
        ("runner/test_semantic_judgment.py", "PASS: Semantic Judgment Contract"),
        ("runner/test_router.py", "PASS: registry-backed router"),
        ("runner/test_registry_loader.py", "PASS: registry loader"),
        ("build/test_build.py", "PASS: build pipeline"),
    )
    for script, expected in checks:
        completed = subprocess.run(
            [sys.executable, str(EXPERIMENT_ROOT / script)],
            cwd=EXPERIMENT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert expected in completed.stdout


if __name__ == "__main__":
    tests = (
        test_ac1_official_anthropic_sdk_imports,
        test_ac2_installed_sdk_version_is_observable,
        test_ac3_candidate_model_remains_injectable,
        test_ac4_installed_sdk_accepts_messages_request_shape_locally,
        test_ac5_structured_output_mechanism_is_locally_verified,
        test_ac6_canonical_annotation_contract_remains_byte_identical,
        test_ac7_provider_representation_is_deterministic,
        test_ac8_provider_transformation_cannot_bypass_canonical_validation,
        test_ac9_blindness_survives_actual_request_construction,
        test_ac10_no_prohibited_provider_capability_is_configured,
        test_ac11_compatibility_requires_and_accesses_no_credential,
        test_ac12_local_compatibility_performs_no_network_request,
        test_ac13_output_annotator_remains_provider_independent,
        test_ac14_sdk_acceptance_and_server_acceptance_remain_distinct,
        test_ac15_all_frozen_regressions_pass,
    )
    for test in tests:
        test()
    print("PASS: Anthropic SDK local compatibility tests (AC1-AC15)")
