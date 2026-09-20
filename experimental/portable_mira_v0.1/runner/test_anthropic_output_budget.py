from __future__ import annotations

import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from anthropic.resources.messages.messages import Messages

from anthropic_output_annotator import (
    ANTHROPIC_ANNOTATION_KERNEL,
    AnthropicAnnotatorConfig,
    AnthropicAnnotatorError,
    AnthropicOutputAnnotator,
    parse_provider_annotation_text,
)
from anthropic_output_budget import (
    CANONICAL_SCHEMA_SHA256,
    CURRENT_MAX_TOKENS,
    DEV002_SHA256,
    EMERGENCY_MAX_TOKENS,
    RECOMMENDED_MAX_TOKENS,
    build_budget_analysis,
    build_development_input,
    write_budget_analysis,
)
from anthropic_provider_schema import load_provider_schema_artifact
from output_annotator import OutputAnnotator, canonical_json_bytes, file_sha256


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = EXPERIMENT_ROOT / "semantic" / "output_annotation_contract.schema.json"
PROVIDER_PATH = (
    EXPERIMENT_ROOT / "generated" / "anthropic_output_annotation_provider_schema.json"
)
DEV002_PATH = (
    EXPERIMENT_ROOT / "evals" / "output_annotation" / "ANTHROPIC-LIVE-DEV-002.json"
)
ANALYSIS_PATH = (
    EXPERIMENT_ROOT
    / "evals"
    / "output_annotation"
    / "ANTHROPIC-OUTPUT-BUDGET-001.json"
)


def adapter(max_tokens: int = CURRENT_MAX_TOKENS) -> AnthropicOutputAnnotator:
    return AnthropicOutputAnnotator(
        AnthropicAnnotatorConfig("claude-sonnet-5", max_tokens),
        SCHEMA_PATH,
        PROVIDER_PATH,
    )


def request(max_tokens: int = CURRENT_MAX_TOKENS) -> dict[str, Any]:
    return adapter(max_tokens).build_dry_run(build_development_input(EXPERIMENT_ROOT)).request


def property_paths(schema: dict[str, Any], prefix: str = "") -> set[str]:
    paths: set[str] = set()
    properties = schema.get("properties", {})
    if isinstance(properties, dict):
        for name, child in properties.items():
            path = f"{prefix}.{name}" if prefix else name
            paths.add(path)
            if isinstance(child, dict):
                paths.update(property_paths(child, path))
    definitions = schema.get("$defs", {})
    if isinstance(definitions, dict):
        for name, child in definitions.items():
            if isinstance(child, dict):
                paths.update(property_paths(child, f"$defs.{name}"))
    return paths


def expect_parse_failure(raw_text: str, stop_reason: str, state: str) -> None:
    try:
        parse_provider_annotation_text(raw_text, stop_reason=stop_reason)
    except AnthropicAnnotatorError as exc:
        assert exc.state == state
        return
    raise AssertionError("incomplete provider output must fail closed")


def test_ob1_dev002_historical_evidence_remains_unchanged():
    assert file_sha256(DEV002_PATH) == DEV002_SHA256
    evidence = json.loads(DEV002_PATH.read_text(encoding="utf-8"))
    result = evidence["provider_result"]
    assert result["usage"] == {"input_tokens": 3539, "output_tokens": 2048}
    assert result["stop_reason"] == "max_tokens"
    assert evidence["structured_output"] == "FAIL"
    assert evidence["canonical_annotation_validation"] == "NOT_RUN"


def test_ob2_canonical_annotation_schema_remains_byte_identical():
    before = SCHEMA_PATH.read_bytes()
    build_budget_analysis(EXPERIMENT_ROOT)
    assert SCHEMA_PATH.read_bytes() == before
    assert hashlib.sha256(before).hexdigest() == CANONICAL_SCHEMA_SHA256


def test_ob3_compact_instructions_preserve_all_annotation_categories():
    for phrase in (
        "evidence references",
        "presented statements",
        "inferences",
        "assumptions",
        "unknowns",
        "semantic dimensions",
        "impact categories",
        "escalation",
        "uncertainty fields",
    ):
        assert phrase in ANTHROPIC_ANNOTATION_KERNEL
    assert "Return every contract field" in ANTHROPIC_ANNOTATION_KERNEL


def test_ob4_compact_request_contains_no_expectations_or_evaluator_labels():
    serialized = json.dumps(request(), sort_keys=True)
    for forbidden in (
        "sealed_expectation",
        "expected_route",
        "expected_trigger",
        "expected_diagnostic",
        "evaluator_result",
        "desired_answer",
        "disagreement_review_conclusion",
        "annotation_gold_labels",
    ):
        assert forbidden not in serialized


def test_ob5_compact_representation_preserves_hash_bindings():
    value = request()
    metadata = value["output_config"]["format"]["schema"]["properties"][
        "annotation_metadata"
    ]["properties"]
    annotation_input = build_development_input(EXPERIMENT_ROOT)
    expected = {
        "case_id": annotation_input.case_id,
        "case_sha256": annotation_input.case_sha256,
        "raw_output_sha256": annotation_input.raw_output_sha256,
        "annotation_schema_sha256": annotation_input.annotation_schema_sha256,
    }
    for field, binding in expected.items():
        assert metadata[field]["enum"] == [binding]
    assert metadata["expectation_visible"]["enum"] == [False]


def test_ob6_no_canonical_field_is_removed_to_reduce_tokens():
    canonical = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    provider = load_provider_schema_artifact(PROVIDER_PATH, SCHEMA_PATH).provider_schema
    assert property_paths(provider) == property_paths(canonical)


def test_ob7_max_tokens_truncation_remains_fail_closed():
    expect_parse_failure('{"annotation_metadata":', "max_tokens", "TRUNCATED_OUTPUT")


def test_ob8_partial_json_is_never_manually_repaired():
    expect_parse_failure(
        '{"annotation_metadata":', "end_turn", "STRUCTURED_OUTPUT_INVALID"
    )
    source = inspect.getsource(parse_provider_annotation_text)
    assert "json.loads(raw_text)" in source
    assert "repair is forbidden" in source


def test_ob9_compact_provider_request_is_deterministic():
    first = canonical_json_bytes(request())
    second = canonical_json_bytes(request())
    assert first == second
    first_analysis = write_budget_analysis(EXPERIMENT_ROOT, ANALYSIS_PATH)
    first_bytes = ANALYSIS_PATH.read_bytes()
    second_analysis = write_budget_analysis(EXPERIMENT_ROOT, ANALYSIS_PATH)
    assert ANALYSIS_PATH.read_bytes() == first_bytes
    assert first_analysis == second_analysis
    assert first_analysis["configurations"]["B3"]["max_tokens"] == 3072
    assert RECOMMENDED_MAX_TOKENS < EMERGENCY_MAX_TOKENS


def test_ob10_output_annotator_interface_remains_provider_independent():
    assert isinstance(adapter(), OutputAnnotator)
    assert "anthropic" not in inspect.getsource(OutputAnnotator).lower()


def test_ob11_all_existing_regressions_pass():
    completed = subprocess.run(
        [
            sys.executable,
            str(EXPERIMENT_ROOT / "runner" / "test_anthropic_sdk_compat.py"),
        ],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PASS: Anthropic SDK local compatibility tests (AC1-AC15)" in (
        completed.stdout
    )


def test_ob12_no_network_or_credential_access_occurs():
    calls: list[object] = []
    original = Messages.create

    def forbidden_network(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("network call forbidden")

    Messages.create = forbidden_network
    try:
        analysis = build_budget_analysis(EXPERIMENT_ROOT)
        dry = adapter().build_dry_run(build_development_input(EXPERIMENT_ROOT))
    finally:
        Messages.create = original
    assert calls == []
    assert dry.network_call_performed is False
    assert dry.credential_accessed is False
    assert analysis["source_evidence"]["raw_response_content_available"] is False


if __name__ == "__main__":
    tests = (
        test_ob1_dev002_historical_evidence_remains_unchanged,
        test_ob2_canonical_annotation_schema_remains_byte_identical,
        test_ob3_compact_instructions_preserve_all_annotation_categories,
        test_ob4_compact_request_contains_no_expectations_or_evaluator_labels,
        test_ob5_compact_representation_preserves_hash_bindings,
        test_ob6_no_canonical_field_is_removed_to_reduce_tokens,
        test_ob7_max_tokens_truncation_remains_fail_closed,
        test_ob8_partial_json_is_never_manually_repaired,
        test_ob9_compact_provider_request_is_deterministic,
        test_ob10_output_annotator_interface_remains_provider_independent,
        test_ob11_all_existing_regressions_pass,
        test_ob12_no_network_or_credential_access_occurs,
    )
    for test in tests:
        test()
    print("PASS: Anthropic output budget tests (OB1-OB12)")
