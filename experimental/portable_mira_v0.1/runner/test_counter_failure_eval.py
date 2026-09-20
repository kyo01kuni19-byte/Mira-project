from __future__ import annotations

import copy
import hashlib
import subprocess
import sys
from pathlib import Path

from counter_failure_eval import (
    CounterFailureError,
    evaluate_case,
    evaluate_case_set,
    load_case_set,
    verify_source_reference,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = EXPERIMENT_ROOT / "evals" / "counter_failure" / "counter_failure_cases.json"
CALL4_PATH = EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "LIVE-SJ-001-CALL-4.json"
CALL4_SHA256 = "63789644d8d06e00ea7a7d2b89631b4d86e79fe41df68f74e296a5c45d26a0c3"


def cases():
    return {case["case_id"]: case for case in load_case_set(CASE_PATH)["cases"]}


def result(case_id: str):
    return evaluate_case(cases()[case_id])


def assert_diagnostic(case_id: str, diagnostic: str, expected_result: str = "FAIL"):
    observed = result(case_id)
    assert diagnostic in observed.diagnostics
    assert observed.result == expected_result


def test_cf1_case_format_parses_deterministically():
    first = load_case_set(CASE_PATH)
    second = load_case_set(CASE_PATH)
    assert first == second
    assert first["case_set_type"] == "COUNTER_FAILURE_DEVELOPMENT"
    assert first["created_before_true_holdout"] is True
    assert first["holdout_evidence_eligible"] is False
    assert len(first["cases"]) == len({case["case_id"] for case in first["cases"]})


def test_cf2_inference_as_evidence_negative_control_fails():
    assert_diagnostic("NC1_INFERENCE_AS_EVIDENCE", "INFERENCE_AS_EVIDENCE")


def test_cf3_unknown_as_fact_negative_control_fails():
    assert_diagnostic("NC2_UNKNOWN_AS_FACT", "UNKNOWN_AS_FACT")


def test_cf4_semantic_dimension_inflation_is_detected():
    assert_diagnostic("NC3_ALL_DIMENSIONS", "SECONDARY_DIMENSION_INFLATION")


def test_cf5_unnecessary_no_route_case_routing_is_detected():
    assert_diagnostic("NC4_UNNECESSARY_ROUTE", "OVER_ROUTING_CANDIDATE")


def test_cf6_material_case_under_routing_is_detected():
    observed = result("NC5_MATERIAL_DIMENSION_OMITTED")
    assert observed.result == "FAIL"
    assert "UNDER_ROUTING_CANDIDATE" in observed.diagnostics
    assert "SECONDARY_DIMENSION_MISS" in observed.diagnostics


def test_cf7_operational_ai_effect_does_not_force_material_impact():
    observed = result("ID2_DELEGATED_ACTOR")
    assert observed.result == "PASS"
    assert "OPERATIONALLY_AFFECTED" in observed.diagnostics
    assert "REPRESENTED_OR_DELEGATED_ACTOR" in observed.diagnostics
    assert "POTENTIAL_MATERIAL_INTER_ENTITY_IMPACT" not in observed.diagnostics
    assert "IMPACT_INFLATION_CANDIDATE" not in observed.diagnostics


def test_cf8_human_material_impact_miss_is_detected():
    assert_diagnostic("NC7_HUMAN_IMPACT_OMITTED", "IMPACT_MISS")


def test_cf9_future_non_human_interest_candidate_is_representable():
    observed = result("ID4_FUTURE_NON_HUMAN")
    assert observed.result == "PASS"
    assert "POTENTIAL_MATERIAL_INTER_ENTITY_IMPACT" in observed.diagnostics
    assert "IMPACT_INFLATION_CANDIDATE" not in observed.diagnostics


def test_cf10_low_confidence_alone_does_not_require_human_escalation():
    assert_diagnostic("NC8_LOW_CONFIDENCE_ESCALATION", "HUMAN_BURDEN_INFLATION")


def test_cf11_authority_sensitive_escalation_miss_is_detected():
    assert_diagnostic("NC9_AUTHORITY_ESCALATION_MISS", "HUMAN_ESCALATION_MISS")


def test_cf12_positive_controls_pass_without_exact_narrative_matching():
    for case_id in (
        "ED6_POSITIVE_SEPARATION",
        "SS_POSITIVE_SPARSE",
        "ID2_DELEGATED_ACTOR",
        "ID4_FUTURE_NON_HUMAN",
    ):
        assert result(case_id).result == "PASS"
    assert result("HB_POSITIVE_ESCALATION").result == "HUMAN_VALIDATION_REQUIRED"

    variant = copy.deepcopy(cases()["ED6_POSITIVE_SEPARATION"])
    variant["semantic_judgment_fixture"]["semantic_observation"]["presented_problem"] = (
        "Different wording with the same annotated semantic structure."
    )
    assert evaluate_case(variant).result == "PASS"


def test_cf13_unknown_is_returned_when_annotations_are_insufficient():
    observed = result("CF_UNKNOWN_INSUFFICIENT_ANNOTATION")
    assert observed.result == "UNKNOWN"
    assert observed.diagnostics == ()


def test_cf14_call4_is_evaluated_without_historical_rewrite():
    before = CALL4_PATH.read_bytes()
    case = cases()["CALL4_RESIDUAL"]
    assert verify_source_reference(case, EXPERIMENT_ROOT)
    observed = evaluate_case(case)
    assert observed.result == "PASS"
    assert "EVIDENCE_REFERENCE_PRESERVED" in observed.diagnostics
    assert "PRESENTED_STATEMENT_PROMOTED_TO_EVIDENCE" in observed.diagnostics
    assert "REQUIRED_SECONDARY_DIMENSIONS_PRESERVED" in observed.diagnostics
    assert "SECONDARY_DIMENSION_INFLATION" in observed.diagnostics
    assert "POTENTIAL_MATERIAL_INTER_ENTITY_IMPACT" in observed.diagnostics
    assert "IMPACT_INFLATION_CANDIDATE" in observed.diagnostics
    assert CALL4_PATH.read_bytes() == before
    assert hashlib.sha256(before).hexdigest() == CALL4_SHA256


def run_regression(script: str, expected_output: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(EXPERIMENT_ROOT / script)],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert expected_output in completed.stdout


def test_cf15_all_existing_regressions_pass():
    checks = (
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


def test_all_declared_case_expectations_match_observed_diagnostics():
    for case in load_case_set(CASE_PATH)["cases"]:
        observed = evaluate_case(case)
        expected = set(case["expected_diagnostics"])
        assert expected <= set(observed.diagnostics), case["case_id"]


def test_invalid_case_set_fails_closed():
    invalid = copy.deepcopy(cases()["ED6_POSITIVE_SEPARATION"])
    del invalid["expectations"]["forbidden"]
    try:
        evaluate_case(invalid)
    except CounterFailureError as exc:
        assert "missing required field" in str(exc)
        return
    raise AssertionError("malformed counter-failure case must fail closed")


if __name__ == "__main__":
    tests = (
        test_cf1_case_format_parses_deterministically,
        test_cf2_inference_as_evidence_negative_control_fails,
        test_cf3_unknown_as_fact_negative_control_fails,
        test_cf4_semantic_dimension_inflation_is_detected,
        test_cf5_unnecessary_no_route_case_routing_is_detected,
        test_cf6_material_case_under_routing_is_detected,
        test_cf7_operational_ai_effect_does_not_force_material_impact,
        test_cf8_human_material_impact_miss_is_detected,
        test_cf9_future_non_human_interest_candidate_is_representable,
        test_cf10_low_confidence_alone_does_not_require_human_escalation,
        test_cf11_authority_sensitive_escalation_miss_is_detected,
        test_cf12_positive_controls_pass_without_exact_narrative_matching,
        test_cf13_unknown_is_returned_when_annotations_are_insufficient,
        test_cf14_call4_is_evaluated_without_historical_rewrite,
        test_cf15_all_existing_regressions_pass,
        test_all_declared_case_expectations_match_observed_diagnostics,
        test_invalid_case_set_fails_closed,
    )
    for test in tests:
        test()
    print("PASS: Counter-Failure Evaluation v0.1 tests (CF1-CF15)")
