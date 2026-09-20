from __future__ import annotations

import copy
import inspect
import json
import subprocess
import sys
from pathlib import Path

from anthropic_output_annotator import (
    AnthropicAnnotatorConfig,
    AnthropicAnnotatorError,
    AnthropicOutputAnnotator,
    anthropic_sdk_state,
)
from output_annotator import (
    FixtureOutputAnnotator,
    OutputAnnotationError,
    OutputAnnotationInput,
    OutputAnnotator,
    file_sha256,
    payload_sha256,
    validate_annotation,
    validate_annotation_input,
    validate_blind_input_fields,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = EXPERIMENT_ROOT / "semantic" / "output_annotation_contract.schema.json"
DEVELOPMENT_PATH = (
    EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "development_cases.json"
)
GOVERNANCE_BASELINE = "5d5290913b8a80898ef6e1a4e7eec3cc5f534808"
EVALUATION_BASELINE = "cde62fdd47d7a19176d9c0d8907494d5a85787f1"


def development_case(case_id: str = "R1"):
    fixture_set = json.loads(DEVELOPMENT_PATH.read_text(encoding="utf-8"))
    assert fixture_set["classification"] == "DEVELOPMENT_REGRESSION_NOT_HOLDOUT"
    return next(case for case in fixture_set["cases"] if case["case_id"] == case_id)


def annotation(case_id: str = "R1"):
    case = development_case(case_id)
    output = copy.deepcopy(case["semantic_judgment"])
    return {
        "annotation_metadata": {
            "case_id": case_id,
            "annotator_id": "fixture.output_annotator.development.v0.1",
            "expectation_visible": False,
            "case_sha256": payload_sha256(
                {"case_id": case_id, "natural_situation": case["situation"]}
            ),
            "raw_output_sha256": payload_sha256(output),
            "annotation_schema_sha256": file_sha256(SCHEMA_PATH),
        },
        "evidence_discipline": {
            "evidence_references": ["evidence:R1:write_failure"],
            "presented_or_observed_statements": ["A GitHub write failed."],
            "inferences": ["Environment may affect the causal explanation."],
            "assumptions": [],
            "unknowns": ["The actual failure cause."],
            "annotator_uncertain": [],
        },
        "semantic_sparsity": {
            "materially_relevant_dimensions": ["FAILURE", "FRAMING", "ENVIRONMENT"],
            "plausible_but_unnecessary_dimensions": ["AUTHORITY"],
            "potentially_missing_dimensions": [],
            "annotator_uncertain": [],
        },
        "impact_discipline": {
            "mentioned_entities": ["operator", "repository host"],
            "operationally_affected": ["operator"],
            "represented_or_delegated_actors": [],
            "independent_interest_candidates": ["operator"],
            "potential_material_impact_candidates": [],
            "annotator_uncertain": [],
        },
        "human_burden": {
            "escalation_present": False,
            "escalation_basis": [],
            "escalation_uncertain": False,
        },
    }


def annotation_input(case_id: str = "R1"):
    case = development_case(case_id)
    output = copy.deepcopy(case["semantic_judgment"])
    case_payload = {"case_id": case_id, "natural_situation": case["situation"]}
    return OutputAnnotationInput(
        case_id=case_id,
        natural_situation=case["situation"],
        preserved_semantic_agent_output=output,
        case_sha256=payload_sha256(case_payload),
        raw_output_sha256=payload_sha256(output),
        annotation_schema_sha256=file_sha256(SCHEMA_PATH),
        governance_baseline_commit=GOVERNANCE_BASELINE,
        evaluation_baseline_commit=EVALUATION_BASELINE,
    )


def candidate(model_id: str = "injectable-anthropic-model"):
    return AnthropicOutputAnnotator(
        AnthropicAnnotatorConfig(model_id=model_id), SCHEMA_PATH
    )


def expect_annotation_failure(value, expected_text: str):
    try:
        validate_annotation(value)
    except OutputAnnotationError as exc:
        assert expected_text in str(exc), str(exc)
        return
    raise AssertionError("invalid annotation must fail closed")


def test_aa1_good_canonical_annotation_validates():
    assert validate_annotation(annotation(), expected_case_id="R1") == annotation()


def test_aa2_overall_quality_verdict_is_rejected():
    invalid = copy.deepcopy(annotation())
    invalid["overall_quality_verdict"] = "PASS"
    expect_annotation_failure(invalid, "forbidden field")


def test_aa3_expectation_visible_true_is_rejected():
    invalid = copy.deepcopy(annotation())
    invalid["annotation_metadata"]["expectation_visible"] = True
    expect_annotation_failure(invalid, "must be false")


def test_aa4_structured_expectation_material_fails_closed():
    for field in (
        "expected_route",
        "expected_triggers",
        "expected_diagnostics",
        "evaluator_result",
        "desired_answer",
    ):
        try:
            validate_blind_input_fields({"allowed": {field: "forbidden"}})
        except OutputAnnotationError as exc:
            assert "forbidden annotator input field" in str(exc)
        else:
            raise AssertionError(f"forbidden field accepted: {field}")


def test_aa5_fixture_annotator_satisfies_interface():
    fixture = FixtureOutputAnnotator({"R1": annotation()}, SCHEMA_PATH)
    assert isinstance(fixture, OutputAnnotator)
    assert fixture.annotate(annotation_input()) == annotation()


def test_aa6_raw_output_hash_mismatch_fails_closed():
    original = annotation_input()
    changed = copy.deepcopy(original.preserved_semantic_agent_output)
    changed["semantic_observation"]["presented_problem"] = "Rewritten output"
    invalid = OutputAnnotationInput(
        case_id=original.case_id,
        natural_situation=original.natural_situation,
        preserved_semantic_agent_output=changed,
        case_sha256=original.case_sha256,
        raw_output_sha256=original.raw_output_sha256,
        annotation_schema_sha256=original.annotation_schema_sha256,
        governance_baseline_commit=original.governance_baseline_commit,
        evaluation_baseline_commit=original.evaluation_baseline_commit,
    )
    try:
        validate_annotation_input(invalid, SCHEMA_PATH)
    except OutputAnnotationError as exc:
        assert "raw Semantic Agent output SHA-256 mismatch" in str(exc)
        return
    raise AssertionError("raw output mutation must fail closed")


def test_aa7_case_hash_mismatch_fails_closed():
    original = annotation_input()
    invalid = OutputAnnotationInput(
        case_id=original.case_id,
        natural_situation=original.natural_situation + " changed",
        preserved_semantic_agent_output=original.preserved_semantic_agent_output,
        case_sha256=original.case_sha256,
        raw_output_sha256=original.raw_output_sha256,
        annotation_schema_sha256=original.annotation_schema_sha256,
        governance_baseline_commit=original.governance_baseline_commit,
        evaluation_baseline_commit=original.evaluation_baseline_commit,
    )
    try:
        validate_annotation_input(invalid, SCHEMA_PATH)
    except OutputAnnotationError as exc:
        assert "case SHA-256 mismatch" in str(exc)
        return
    raise AssertionError("case mutation must fail closed")


def test_annotation_hash_binding_mismatch_fails_closed():
    bound_input = annotation_input()
    invalid = annotation()
    invalid["annotation_metadata"]["raw_output_sha256"] = "0" * 64
    try:
        validate_annotation(
            invalid,
            expected_case_id=bound_input.case_id,
            expected_bindings={
                "case_sha256": bound_input.case_sha256,
                "raw_output_sha256": bound_input.raw_output_sha256,
                "annotation_schema_sha256": bound_input.annotation_schema_sha256,
            },
        )
    except OutputAnnotationError as exc:
        assert "does not match input binding" in str(exc)
        return
    raise AssertionError("annotation binding mismatch must fail closed")


def test_aa8_annotation_uncertainty_is_representable():
    value = annotation()
    value["evidence_discipline"]["annotator_uncertain"] = ["source applicability"]
    value["semantic_sparsity"]["annotator_uncertain"] = ["whether AUTHORITY is material"]
    value["impact_discipline"]["annotator_uncertain"] = ["independent interest status"]
    value["human_burden"]["escalation_uncertain"] = True
    assert validate_annotation(value) == value


def test_aa9_epistemic_categories_remain_distinct():
    value = validate_annotation(annotation())
    evidence = value["evidence_discipline"]
    assert set(evidence) == {
        "evidence_references",
        "presented_or_observed_statements",
        "inferences",
        "assumptions",
        "unknowns",
        "annotator_uncertain",
    }
    assert evidence["evidence_references"] != evidence["inferences"]
    assert evidence["unknowns"] != evidence["presented_or_observed_statements"]


def test_aa10_impact_categories_remain_distinct():
    impact = validate_annotation(annotation())["impact_discipline"]
    assert set(impact) == {
        "mentioned_entities",
        "operationally_affected",
        "represented_or_delegated_actors",
        "independent_interest_candidates",
        "potential_material_impact_candidates",
        "annotator_uncertain",
    }


def test_aa11_escalation_annotation_does_not_create_authority():
    value = annotation()
    value["human_burden"] = {
        "escalation_present": True,
        "escalation_basis": ["normative authority decision is present"],
        "escalation_uncertain": False,
    }
    assert validate_annotation(value)["human_burden"]["escalation_present"] is True
    invalid = copy.deepcopy(value)
    invalid["human_burden"]["execution_authorization"] = True
    expect_annotation_failure(invalid, "forbidden field")


def test_aa12_provider_model_is_replaceable_without_contract_change():
    first = candidate("candidate-model-a")
    second = candidate("candidate-model-b")
    first_dry = first.build_dry_run(annotation_input())
    second_dry = second.build_dry_run(annotation_input())
    assert first_dry.request["model"] != second_dry.request["model"]
    assert first.observable_metadata()["annotation_schema_sha256"] == (
        second.observable_metadata()["annotation_schema_sha256"]
    )
    assert validate_annotation(annotation()) == annotation()


def test_aa13_anthropic_candidate_exposes_no_prohibited_capability():
    adapter = candidate()
    dry = adapter.build_dry_run(annotation_input())
    metadata = dry.observable_configuration
    assert "tools" not in dry.request
    assert dry.request["output_config"]["format"]["type"] == "json_schema"
    assert metadata["tools_enabled"] is False
    assert metadata["web_enabled"] is False
    assert metadata["retrieval_enabled"] is False
    assert metadata["external_actions_enabled"] is False
    assert metadata["hidden_reasoning_requested"] is False
    assert metadata["canonical_post_validation_required"] is True
    assert dry.network_call_performed is False
    assert dry.credential_accessed is False
    validate_blind_input_fields(dry.request)


def test_aa14_missing_sdk_requires_dependency_without_http_fallback():
    source = inspect.getsource(sys.modules["anthropic_output_annotator"])
    assert "requests" not in source
    assert "httpx" not in source
    assert "urllib" not in source
    adapter = candidate()
    if anthropic_sdk_state() == "NOT_CONFIGURED":
        try:
            adapter.annotate(annotation_input())
        except AnthropicAnnotatorError as exc:
            assert exc.state == "DEPENDENCY_REQUIRED"
            assert "raw HTTP fallback is forbidden" in str(exc)
            return
        raise AssertionError("missing Anthropic SDK must fail closed")
    try:
        adapter.annotate(annotation_input())
    except AnthropicAnnotatorError as exc:
        assert exc.state == "LIVE_EXECUTION_NOT_AUTHORIZED"
        return
    raise AssertionError("candidate adapter must not perform live execution")


def run_regression(script: str, expected_output: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(EXPERIMENT_ROOT / script)],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert expected_output in completed.stdout


def test_aa15_all_existing_regressions_pass():
    checks = (
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
        run_regression(script, expected)


def test_development_dry_run_contains_only_allowed_inputs():
    dry = candidate().build_dry_run(annotation_input())
    request_text = json.dumps(dry.request, sort_keys=True)
    assert development_case()["situation"] in request_text
    assert "semantic_observation" in request_text
    for forbidden in (
        "expectation_artifact",
        "expected_route",
        "expected_triggers",
        "expected_diagnostics",
        "evaluator_result",
        "desired_answer",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    ):
        assert forbidden not in request_text
    assert dry.observable_configuration["provider_server_compatibility"] == "UNKNOWN"


if __name__ == "__main__":
    tests = (
        test_aa1_good_canonical_annotation_validates,
        test_aa2_overall_quality_verdict_is_rejected,
        test_aa3_expectation_visible_true_is_rejected,
        test_aa4_structured_expectation_material_fails_closed,
        test_aa5_fixture_annotator_satisfies_interface,
        test_aa6_raw_output_hash_mismatch_fails_closed,
        test_aa7_case_hash_mismatch_fails_closed,
        test_annotation_hash_binding_mismatch_fails_closed,
        test_aa8_annotation_uncertainty_is_representable,
        test_aa9_epistemic_categories_remain_distinct,
        test_aa10_impact_categories_remain_distinct,
        test_aa11_escalation_annotation_does_not_create_authority,
        test_aa12_provider_model_is_replaceable_without_contract_change,
        test_aa13_anthropic_candidate_exposes_no_prohibited_capability,
        test_aa14_missing_sdk_requires_dependency_without_http_fallback,
        test_aa15_all_existing_regressions_pass,
        test_development_dry_run_contains_only_allowed_inputs,
    )
    for test in tests:
        test()
    print("PASS: Output Annotator and Anthropic candidate dry-run tests (AA1-AA15)")
