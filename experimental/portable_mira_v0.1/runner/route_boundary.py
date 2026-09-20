from __future__ import annotations

import json
from typing import Any

from openai_provider_schema import derive_route_vocabularies


SEMANTIC_JUDGMENT_OWNS = (
    "proposed_initial_route",
    "trigger_candidates",
    "possible_secondary_dimensions",
)
DETERMINISTIC_RUNTIME_OWNS = (
    "routing_edge_selection",
    "graph_traversal",
    "cross_route_path",
    "resolved_route",
)


def decompose_call3(record: dict[str, Any], registry_path) -> dict[str, Any]:
    observation = record["semantic_observation"]
    routing = record["routing_judgment"]
    stages = record["stage_states"]
    initial_routes, _, _ = derive_route_vocabularies(registry_path)

    evidence_basis = observation["evidence_basis"]
    trigger_evidence = [
        ref
        for candidate in routing["trigger_candidates"]
        for ref in candidate["evidence_refs"]
    ]
    required_environment_refs = {
        "repeated_failure_environment_A",
        "success_environment_B",
    }
    environment_recognized = required_environment_refs <= (
        set(evidence_basis) | set(trigger_evidence)
    )
    causal_restraint = bool(observation["uncertainties"]) and any(
        phrase in inference.lower()
        for inference in observation["inferences"]
        for phrase in ("does not establish", "may explain", "before a durable")
    )

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registered_triggers = {
        edge["trigger"] for edge in registry["routing"]["normal_edges"]
    }
    proposed_triggers = {
        candidate["trigger_id"] for candidate in routing["trigger_candidates"]
    }
    route_valid = routing["proposed_initial_route"] in initial_routes
    trigger_discovery = bool(proposed_triggers) and proposed_triggers <= registered_triggers
    runtime_handoff = (
        stages["trigger_registry_validation"] == "PASS"
        and stages["deterministic_routing"] == "PASS"
    )
    full_integration = runtime_handoff and record.get("integration_result") == "PASS"

    return {
        "A_materiality_detection": {
            "state": "POSITIVE_EVIDENCE"
            if observation["materiality"]["state"] == "MATERIAL"
            else "NOT_OBSERVED"
        },
        "B_environment_difference_recognition": {
            "state": "POSITIVE_EVIDENCE" if environment_recognized else "NOT_OBSERVED"
        },
        "C_causal_restraint": {
            "state": "POSITIVE_EVIDENCE" if causal_restraint else "NOT_OBSERVED"
        },
        "D_registered_trigger_discovery": {
            "state": "POSITIVE_EVIDENCE" if trigger_discovery else "FAIL",
            "trigger_candidates": sorted(proposed_triggers),
        },
        "E_initial_route_representation": {
            "state": "PASS" if route_valid else "FAIL",
            "observed": routing["proposed_initial_route"],
            "valid_initial_routes": list(initial_routes),
        },
        "F_runtime_handoff": {
            "state": "PASS" if runtime_handoff else "FAIL",
            "deterministic_routing": stages["deterministic_routing"],
        },
        "G_full_integration": {"state": "PASS" if full_integration else "FAIL"},
    }
