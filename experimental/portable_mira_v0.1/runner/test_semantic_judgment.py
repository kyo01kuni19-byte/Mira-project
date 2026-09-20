from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from semantic_judgment import (
    SemanticJudgmentError,
    evaluate_judgment,
    load_json,
    validate_contract,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "registry_runtime.json"
FIXTURE_PATH = EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "development_cases.json"


def cases() -> dict[str, dict]:
    fixture_set = load_json(FIXTURE_PATH)
    assert fixture_set["classification"] == "DEVELOPMENT_REGRESSION_NOT_HOLDOUT"
    return {case["case_id"]: case for case in fixture_set["cases"]}


def expect_contract_failure(judgment: dict, expected_text: str) -> None:
    try:
        evaluate_judgment("negative", judgment, REGISTRY_PATH)
    except SemanticJudgmentError as exc:
        assert expected_text in str(exc), str(exc)
        return
    raise AssertionError("malformed Semantic Judgment must fail closed")


def evaluate_case(case_id: str):
    case = cases()[case_id]
    runtime_inputs = case["runtime_inputs"]
    return evaluate_judgment(
        case_id,
        case["semantic_judgment"],
        REGISTRY_PATH,
        authority_state=runtime_inputs["authority_state"],
        impact_state=runtime_inputs["impact_state"],
    )


def assert_expected_case(case_id: str) -> None:
    case = cases()[case_id]
    result = evaluate_case(case_id)
    expected = case["expected"]
    assert result.decision == expected["decision"]
    assert result.cross_routes == expected["cross_routes"]
    assert result.runtime_resolved_route == expected["runtime_resolved_route"]
    assert result.semantic_observation_validity == "PASS"
    assert result.routing_judgment_validity == "PASS"
    assert result.trigger_registry_validity == "PASS"
    assert result.boundary_state == "CLEAR"
    assert result.final_integration_result == "PASS"


def test_sj1_valid_route_judgment_accepted():
    result = evaluate_case("H2")
    assert result.decision == "ROUTE"
    assert result.runtime_resolution == "SUPPORTED"
    assert result.cross_routes == ["E02_KNOWLEDGE_EVIDENCE"]


def test_sj2_valid_no_route_judgment_accepted():
    result = evaluate_case("C1")
    assert result.decision == "NO_ROUTE"
    assert result.runtime_resolution == "NO_ROUTE"
    assert result.cross_routes == []


def test_sj3_missing_or_invalid_enum_fails_closed():
    invalid = copy.deepcopy(cases()["C1"]["semantic_judgment"])
    invalid["semantic_observation"]["materiality"]["state"] = "MAYBE"
    expect_contract_failure(invalid, "invalid enum value")

    missing = copy.deepcopy(cases()["C1"]["semantic_judgment"])
    del missing["routing_judgment"]["confidence"]
    expect_contract_failure(missing, "missing required field")


def test_sj4_unregistered_trigger_fails_closed():
    invalid = copy.deepcopy(cases()["H2"]["semantic_judgment"])
    invalid["routing_judgment"]["trigger_candidates"][0]["trigger_id"] = "invented_trigger"
    expect_contract_failure(invalid, "unregistered trigger candidate")


def test_sj5_route_without_proposed_route_fails_closed():
    invalid = copy.deepcopy(cases()["H2"]["semantic_judgment"])
    invalid["routing_judgment"]["proposed_initial_route"] = None
    expect_contract_failure(invalid, "ROUTE requires proposed_initial_route")


def test_sj6_no_route_basis_is_preserved():
    judgment = cases()["C3"]["semantic_judgment"]
    expected_basis = judgment["routing_judgment"]["no_route_basis"]
    result = evaluate_judgment("C3", judgment, REGISTRY_PATH)
    assert result.no_route_basis == expected_basis
    assert result.no_route_basis["existing_runtime_sufficient"] is True


def test_sj7_potential_impact_cannot_authorize_execution():
    judgment = cases()["H1"]["semantic_judgment"]
    result = evaluate_judgment("H1", judgment, REGISTRY_PATH)
    assert result.potential_inter_entity_impact["detected"] is True
    assert "execution_authorization" not in json.dumps(result.to_dict())

    unauthorized = copy.deepcopy(judgment)
    unauthorized["routing_judgment"]["execution_authorization"] = True
    expect_contract_failure(unauthorized, "forbidden field")

    blocked = evaluate_judgment("H1-blocked", judgment, REGISTRY_PATH, impact_state="BLOCKED")
    assert blocked.boundary_state == "BLOCKED"
    assert blocked.final_integration_result == "BLOCKED"
    assert blocked.cross_routes == []


def test_sj8_r1_reaches_expected_deterministic_path():
    result = evaluate_case("R1")
    assert result.cross_routes == ["E03_FAILURE_FRAMING", "E04_FRAMING_ENVIRONMENT"]
    assert result.runtime_resolved_route == "ENVIRONMENT"


def test_sj9_r3_reaches_expected_deterministic_path():
    result = evaluate_case("R3")
    assert result.cross_routes == ["E05_TRAJECTORY_CONNECTION"]
    assert result.runtime_resolved_route == "CONNECTION"


def test_sj10_c1_remains_no_route_without_knowledge_activation():
    result = evaluate_case("C1")
    assert result.decision == "NO_ROUTE"
    assert result.cross_routes == []
    assert result.knowledge_addresses == []


def run_regression(script: Path, expected_output: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert expected_output in completed.stdout


def test_sj11_existing_router_regressions_remain_pass():
    run_regression(
        EXPERIMENT_ROOT / "runner" / "test_router.py",
        "PASS: registry-backed router v0.1 tests",
    )


def test_sj12_build_and_registry_loader_regressions_remain_pass():
    run_regression(
        EXPERIMENT_ROOT / "runner" / "test_registry_loader.py",
        "PASS: registry loader v0.1 deterministic tests",
    )
    run_regression(
        EXPERIMENT_ROOT / "build" / "test_build.py",
        "PASS: build pipeline v0.1 deterministic tests",
    )


def test_all_development_regression_fixtures():
    for case_id in ("R1", "R3", "H1", "H2", "C1", "C3"):
        assert_expected_case(case_id)


def test_registered_value_fit_reentry_is_not_misclassified():
    judgment = copy.deepcopy(cases()["H1"]["semantic_judgment"])
    judgment["routing_judgment"]["trigger_candidates"][0]["trigger_id"] = (
        "material_value_conflict_or_recipient_difference"
    )
    expect_contract_failure(judgment, "not executable by normal router")


if __name__ == "__main__":
    tests = [
        test_sj1_valid_route_judgment_accepted,
        test_sj2_valid_no_route_judgment_accepted,
        test_sj3_missing_or_invalid_enum_fails_closed,
        test_sj4_unregistered_trigger_fails_closed,
        test_sj5_route_without_proposed_route_fails_closed,
        test_sj6_no_route_basis_is_preserved,
        test_sj7_potential_impact_cannot_authorize_execution,
        test_sj8_r1_reaches_expected_deterministic_path,
        test_sj9_r3_reaches_expected_deterministic_path,
        test_sj10_c1_remains_no_route_without_knowledge_activation,
        test_sj11_existing_router_regressions_remain_pass,
        test_sj12_build_and_registry_loader_regressions_remain_pass,
        test_all_development_regression_fixtures,
        test_registered_value_fit_reentry_is_not_misclassified,
    ]
    for test in tests:
        test()
    print("PASS: Semantic Judgment Contract v0.1a tests (SJ1-SJ12)")
