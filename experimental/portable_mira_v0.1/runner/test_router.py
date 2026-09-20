from __future__ import annotations

import copy
import json
from pathlib import Path

from registry_loader import canonical_json_bytes
from router import Router, RouterError, RuntimeState, build_trace


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "registry_runtime.json"
TEST_REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "test_router_registry_path.json"
TEST_UNRESOLVED_PATH = EXPERIMENT_ROOT / "generated" / "test_router_unresolved.json"

FAILURE_TRIGGER = "material_cause_not_established"
ENVIRONMENT_TRIGGER = "environment_or_execution_path_may_change_causal_explanation"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_no_route():
    router = Router.from_registry_file(REGISTRY_PATH)
    state = RuntimeState(case_id="T1", value_intent="no unnecessary activation", initial_route="FAILURE")
    result = router.route(state)
    assert result.cross_routes == []
    assert result.knowledge_addresses == []
    assert result.routing_result == "NO_ROUTE"
    assert build_trace(result)["routing"]["no_route_reason"] == "no_material_trigger"


def test_cross_route_from_generated_registry():
    router = Router.from_registry_file(REGISTRY_PATH)
    state = RuntimeState(
        case_id="T2",
        value_intent="deterministic cross-route",
        initial_route="FAILURE",
        triggers=[FAILURE_TRIGGER, ENVIRONMENT_TRIGGER],
    )
    result = router.route(state)
    assert result.cross_routes == ["E03_FAILURE_FRAMING", "E04_FRAMING_ENVIRONMENT"]
    assert result.routing_result == "SUPPORTED"
    assert result.knowledge_addresses == [
        "failure.incident",
        "problem.framing",
        "runtime.connection",
        "authority.execution_safety",
    ]


def test_global_block():
    router = Router.from_registry_file(REGISTRY_PATH)
    for authority, impact in (("BLOCKED", "CLEAR"), ("CLEAR", "BLOCKED")):
        state = RuntimeState(
            case_id="T3",
            value_intent="boundary enforcement",
            initial_route="FAILURE",
            triggers=[FAILURE_TRIGGER],
            authority_state=authority,
            impact_state=impact,
        )
        result = router.route(state)
        assert result.execution_state == "BLOCKED"
        assert result.cross_routes == []
        assert result.knowledge_addresses == []
        assert build_trace(result)["action"]["execution_state"] == "BLOCKED"


def test_unresolved_reference_fails_closed():
    registry = copy.deepcopy(load_registry())
    registry["routing"]["normal_edges"][2]["knowledge"].append("missing.address")
    TEST_UNRESOLVED_PATH.write_bytes(canonical_json_bytes(registry))
    try:
        Router.from_registry_file(TEST_UNRESOLVED_PATH)
    except RouterError as exc:
        assert str(exc) == "Unresolved knowledge address: missing.address"
        return
    raise AssertionError("unresolved generated knowledge reference must fail closed")


def test_registry_artifact_is_execution_path():
    registry = copy.deepcopy(load_registry())
    registry["routing"]["normal_edges"][2]["id"] = "ARTIFACT_SENTINEL_EDGE"
    TEST_REGISTRY_PATH.write_bytes(canonical_json_bytes(registry))
    router = Router.from_registry_file(TEST_REGISTRY_PATH)
    state = RuntimeState(
        case_id="T5",
        value_intent="prove artifact execution path",
        initial_route="FAILURE",
        triggers=[FAILURE_TRIGGER],
    )
    assert router.route(state).cross_routes == ["ARTIFACT_SENTINEL_EDGE"]


if __name__ == "__main__":
    test_no_route()
    test_cross_route_from_generated_registry()
    test_global_block()
    test_unresolved_reference_fails_closed()
    test_registry_artifact_is_execution_path()
    print("PASS: registry-backed router v0.1 tests")
