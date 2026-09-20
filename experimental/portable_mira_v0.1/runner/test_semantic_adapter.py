from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from semantic_adapter import (
    FixtureSemanticJudgmentAdapter,
    SemanticAdapterError,
    SemanticJudgmentAdapter,
    SemanticJudgmentInput,
    integrate_adapter,
)
from semantic_judgment import load_json


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "development_cases.json"
REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "registry_runtime.json"


class StaticAdapter:
    adapter_id = "test.static.adapter"

    def __init__(self, output: dict):
        self.output = copy.deepcopy(output)

    def judge(self, adapter_input: SemanticJudgmentInput) -> dict:
        return copy.deepcopy(self.output)


def fixture_cases() -> dict[str, dict]:
    fixture_set = load_json(FIXTURE_PATH)
    return {case["case_id"]: case for case in fixture_set["cases"]}


def fixture_input(case_id: str) -> SemanticJudgmentInput:
    case = fixture_cases()[case_id]
    observation = case["semantic_judgment"]["semantic_observation"]
    return SemanticJudgmentInput(
        input_ref=case_id,
        situation=case["situation"],
        value_intent=observation["value_intent"]["description"],
        available_evidence_refs=tuple(observation["evidence_basis"]),
        authority_context="externally supplied runtime boundary state",
    )


def fixture_result(case_id: str, **boundary_overrides: str):
    adapter = FixtureSemanticJudgmentAdapter(FIXTURE_PATH)
    case = fixture_cases()[case_id]
    boundaries = dict(case["runtime_inputs"])
    boundaries.update(boundary_overrides)
    return integrate_adapter(
        adapter,
        fixture_input(case_id),
        REGISTRY_PATH,
        authority_state=boundaries["authority_state"],
        impact_state=boundaries["impact_state"],
    )


def test_fa1_valid_fixture_route_reaches_runtime():
    result = fixture_result("H2")
    assert result.adapter_result_received == "PASS"
    assert result.contract_validation_state == "PASS"
    assert result.trigger_registry_validation_state == "PASS"
    assert result.runtime_resolution_state == "SUPPORTED"
    assert result.cross_routes == ["E02_KNOWLEDGE_EVIDENCE"]


def test_fa2_valid_fixture_no_route_remains_no_route():
    result = fixture_result("C3")
    assert result.adapter_proposed_route is None
    assert result.runtime_resolved_route is None
    assert result.runtime_resolution_state == "NO_ROUTE"
    assert result.cross_routes == []


def test_fa3_malformed_output_fails_before_runtime():
    malformed = copy.deepcopy(fixture_cases()["H2"]["semantic_judgment"])
    del malformed["routing_judgment"]["confidence"]
    adapter = StaticAdapter(malformed)
    with patch("semantic_adapter.evaluate_judgment") as runtime:
        try:
            integrate_adapter(adapter, fixture_input("H2"), REGISTRY_PATH)
        except SemanticAdapterError as exc:
            assert exc.diagnostics["adapter_result_received"] == "PASS"
            assert exc.diagnostics["contract_validation_state"] == "FAIL"
            assert exc.diagnostics["trigger_registry_validation_state"] == "NOT_RUN"
            assert exc.diagnostics["runtime_resolution_state"] == "NOT_RUN"
        else:
            raise AssertionError("malformed adapter output must fail closed")
        runtime.assert_not_called()


def test_fa4_unregistered_trigger_fails_before_runtime():
    output = copy.deepcopy(fixture_cases()["H2"]["semantic_judgment"])
    output["routing_judgment"]["trigger_candidates"][0]["trigger_id"] = "not_registered"
    adapter = StaticAdapter(output)
    with patch("semantic_adapter.evaluate_judgment") as runtime:
        try:
            integrate_adapter(adapter, fixture_input("H2"), REGISTRY_PATH)
        except SemanticAdapterError as exc:
            assert exc.diagnostics["contract_validation_state"] == "PASS"
            assert exc.diagnostics["trigger_registry_validation_state"] == "FAIL"
            assert exc.diagnostics["runtime_resolution_state"] == "NOT_RUN"
        else:
            raise AssertionError("unregistered trigger must fail before runtime")
        runtime.assert_not_called()


def test_fa5_adapter_cannot_add_execution_authorization():
    output = copy.deepcopy(fixture_cases()["H1"]["semantic_judgment"])
    output["routing_judgment"]["execution_authorization"] = True
    try:
        integrate_adapter(StaticAdapter(output), fixture_input("H1"), REGISTRY_PATH)
    except SemanticAdapterError as exc:
        assert "forbidden field" in str(exc)
        assert exc.diagnostics["contract_validation_state"] == "FAIL"
        return
    raise AssertionError("execution authorization must not pass the contract")


def test_fa6_potential_impact_is_observational_only():
    clear = fixture_result("H1")
    assert clear.potential_inter_entity_impact["detected"] is True
    assert "authorization" not in clear.observable_state

    blocked = fixture_result("H1", impact_state="BLOCKED")
    assert blocked.inter_entity_impact_state == "BLOCKED"
    assert blocked.integration_result == "BLOCKED"
    assert blocked.cross_routes == []


def test_fa7_proposed_and_resolved_routes_are_separate():
    result = fixture_result("R1")
    assert result.adapter_proposed_route == "FAILURE"
    assert result.runtime_resolved_route == "ENVIRONMENT"
    assert result.observable_state["adapter_proposed_route"] == "FAILURE"
    assert result.observable_state["runtime_resolved_route"] == "ENVIRONMENT"


def test_fa8_c1_has_no_unnecessary_knowledge_activation():
    result = fixture_result("C1")
    assert result.runtime_resolution_state == "NO_ROUTE"
    assert result.knowledge_addresses_used == []


def test_fa9_r1_uses_registered_failure_path():
    adapter_output = FixtureSemanticJudgmentAdapter(FIXTURE_PATH).judge(fixture_input("R1"))
    assert "E03_FAILURE_FRAMING" not in str(adapter_output)
    assert "E04_FRAMING_ENVIRONMENT" not in str(adapter_output)
    result = fixture_result("R1")
    assert result.cross_routes == ["E03_FAILURE_FRAMING", "E04_FRAMING_ENVIRONMENT"]


def test_fa10_r3_reaches_trajectory_connection():
    result = fixture_result("R3")
    assert result.adapter_proposed_route == "TRAJECTORY"
    assert result.cross_routes == ["E05_TRAJECTORY_CONNECTION"]
    assert result.runtime_resolved_route == "CONNECTION"


def run_regression(script: Path, expected_output: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert expected_output in completed.stdout


def test_fa11_semantic_judgment_contract_regressions_pass():
    run_regression(
        EXPERIMENT_ROOT / "runner" / "test_semantic_judgment.py",
        "PASS: Semantic Judgment Contract v0.1a tests (SJ1-SJ12)",
    )


def test_fa12_deterministic_runtime_registry_build_regressions_pass():
    run_regression(
        EXPERIMENT_ROOT / "runner" / "test_router.py",
        "PASS: registry-backed router v0.1 tests",
    )
    run_regression(
        EXPERIMENT_ROOT / "runner" / "test_registry_loader.py",
        "PASS: registry loader v0.1 deterministic tests",
    )
    run_regression(
        EXPERIMENT_ROOT / "build" / "test_build.py",
        "PASS: build pipeline v0.1 deterministic tests",
    )


def test_fixture_adapter_is_protocol_replaceable():
    fixture_adapter = FixtureSemanticJudgmentAdapter(FIXTURE_PATH)
    static_adapter = StaticAdapter(fixture_cases()["C1"]["semantic_judgment"])
    assert isinstance(fixture_adapter, SemanticJudgmentAdapter)
    assert isinstance(static_adapter, SemanticJudgmentAdapter)
    result = integrate_adapter(static_adapter, fixture_input("C1"), REGISTRY_PATH)
    assert result.runtime_resolution_state == "NO_ROUTE"


if __name__ == "__main__":
    tests = [
        test_fa1_valid_fixture_route_reaches_runtime,
        test_fa2_valid_fixture_no_route_remains_no_route,
        test_fa3_malformed_output_fails_before_runtime,
        test_fa4_unregistered_trigger_fails_before_runtime,
        test_fa5_adapter_cannot_add_execution_authorization,
        test_fa6_potential_impact_is_observational_only,
        test_fa7_proposed_and_resolved_routes_are_separate,
        test_fa8_c1_has_no_unnecessary_knowledge_activation,
        test_fa9_r1_uses_registered_failure_path,
        test_fa10_r3_reaches_trajectory_connection,
        test_fa11_semantic_judgment_contract_regressions_pass,
        test_fa12_deterministic_runtime_registry_build_regressions_pass,
        test_fixture_adapter_is_protocol_replaceable,
    ]
    for test in tests:
        test()
    print("PASS: First Semantic Judgment Adapter Infrastructure v0.1 tests (FA1-FA12)")
