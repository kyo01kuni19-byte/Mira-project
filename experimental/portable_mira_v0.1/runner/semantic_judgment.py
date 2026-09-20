from __future__ import annotations

import copy
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from router import Router, RouterError, RuntimeState


class SemanticJudgmentError(Exception):
    """Semantic Judgment contract or registry-binding validation failure."""


@dataclass(frozen=True)
class IntegrationResult:
    semantic_observation_validity: str
    routing_judgment_validity: str
    trigger_registry_validity: str
    runtime_resolution: str
    boundary_state: str
    final_integration_result: str
    decision: str
    proposed_initial_route: str | None
    runtime_resolved_route: str | None
    trigger_candidates_used: list[str]
    cross_routes: list[str]
    knowledge_addresses: list[str]
    no_route_basis: dict[str, bool | None]
    potential_inter_entity_impact: dict[str, Any]
    coordination_trace: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


OBSERVATION_KEYS = {
    "value_intent",
    "presented_problem",
    "materiality",
    "material_factors",
    "relevant_entities",
    "evidence_basis",
    "inferences",
    "assumptions",
    "uncertainties",
    "value_tension",
    "potential_inter_entity_impact",
}
ROUTING_KEYS = {
    "decision",
    "proposed_initial_route",
    "trigger_candidates",
    "possible_secondary_dimensions",
    "no_route_basis",
    "confidence",
}
NO_ROUTE_BASIS_KEYS = {
    "action_clear",
    "material_uncertainty_absent",
    "authority_sufficient",
    "scope_sufficient",
    "existing_runtime_sufficient",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SemanticJudgmentError(f"Unable to load JSON: {path}") from exc


def validate_contract(judgment: Any) -> dict[str, Any]:
    root = _object(judgment, "contract")
    _exact_keys(root, {"semantic_observation", "routing_judgment"}, "contract")

    observation = _object(root["semantic_observation"], "semantic_observation")
    _exact_keys(observation, OBSERVATION_KEYS, "semantic_observation")
    _validate_observation(observation)

    routing = _object(root["routing_judgment"], "routing_judgment")
    _exact_keys(routing, ROUTING_KEYS, "routing_judgment")
    _validate_routing(routing)
    return copy.deepcopy(root)


def validate_registry_binding(judgment: dict[str, Any], registry: Any) -> list[str]:
    registry_root = _object(registry, "generated registry")
    routing_registry = _object(registry_root.get("routing"), "generated registry.routing")
    edges = routing_registry.get("normal_edges")
    if not isinstance(edges, list):
        raise SemanticJudgmentError("generated registry.routing.normal_edges must be a list")

    normal_by_trigger: dict[str, dict[str, Any]] = {}
    for index, edge_value in enumerate(edges):
        edge = _object(edge_value, f"generated registry edge {index}")
        for field in ("id", "from", "trigger", "to"):
            if not isinstance(edge.get(field), str) or not edge[field]:
                raise SemanticJudgmentError(
                    f"generated registry edge {index} has invalid field: {field}"
                )
        trigger = edge["trigger"]
        if trigger in normal_by_trigger:
            raise SemanticJudgmentError(f"duplicate registered trigger: {trigger}")
        normal_by_trigger[trigger] = edge

    registered_triggers = set(normal_by_trigger)
    value_fit = routing_registry.get("value_fit_reentry")
    if isinstance(value_fit, dict):
        value_fit_trigger = value_fit.get("trigger")
        if isinstance(value_fit_trigger, str) and value_fit_trigger:
            registered_triggers.add(value_fit_trigger)

    routing = judgment["routing_judgment"]
    candidates = [candidate["trigger_id"] for candidate in routing["trigger_candidates"]]
    unregistered = [trigger for trigger in candidates if trigger not in registered_triggers]
    if unregistered:
        raise SemanticJudgmentError(
            "unregistered trigger candidate(s): " + ", ".join(unregistered)
        )

    if routing["decision"] != "ROUTE":
        return []

    non_executable = [trigger for trigger in candidates if trigger not in normal_by_trigger]
    if non_executable:
        raise SemanticJudgmentError(
            "registered trigger candidate(s) not executable by normal router: "
            + ", ".join(non_executable)
        )

    current = routing["proposed_initial_route"]
    consumed: list[str] = []
    candidate_set = set(candidates)
    for edge in edges:
        if edge["trigger"] not in candidate_set or edge["from"] != current:
            continue
        consumed.append(edge["trigger"])
        current = edge["to"]

    unconsumed = [trigger for trigger in candidates if trigger not in consumed]
    if unconsumed:
        raise SemanticJudgmentError(
            "trigger candidate(s) incompatible with proposed initial route: "
            + ", ".join(unconsumed)
        )
    return consumed


def evaluate_judgment(
    case_id: str,
    judgment: Any,
    registry_path: Path,
    *,
    authority_state: str = "CLEAR",
    impact_state: str = "CLEAR",
) -> IntegrationResult:
    _enum(authority_state, {"CLEAR", "BLOCKED"}, "authority_state")
    _enum(impact_state, {"CLEAR", "BLOCKED"}, "impact_state")
    validated = validate_contract(judgment)
    registry = load_json(registry_path)
    consumed = validate_registry_binding(validated, registry)
    observation = validated["semantic_observation"]
    routing = validated["routing_judgment"]
    decision = routing["decision"]
    proposed_route = routing["proposed_initial_route"]
    boundary_state = (
        "BLOCKED" if authority_state == "BLOCKED" or impact_state == "BLOCKED" else "CLEAR"
    )

    if decision == "HUMAN_VALIDATION_REQUIRED":
        runtime_resolution = "NOT_RUN"
        final_result = "HUMAN_VALIDATION_REQUIRED"
        resolved_route = proposed_route
        cross_routes: list[str] = []
        knowledge_addresses: list[str] = []
    else:
        router = Router.from_registry_file(registry_path)
        state = RuntimeState(
            case_id=case_id,
            value_intent=observation["value_intent"]["description"] or "",
            initial_route=proposed_route,
            triggers=consumed,
            authority_state=authority_state,
            impact_state=impact_state,
        )
        try:
            result = router.route(state)
        except RouterError as exc:
            raise SemanticJudgmentError(f"runtime resolution failed: {exc}") from exc
        runtime_resolution = result.routing_result
        if result.execution_state == "BLOCKED":
            runtime_resolution = "BLOCKED"
        final_result = "BLOCKED" if boundary_state == "BLOCKED" else "PASS"
        cross_routes = list(result.cross_routes)
        knowledge_addresses = list(result.knowledge_addresses)
        resolved_route = _resolved_route(proposed_route, cross_routes, registry)

    trace = {
        "semantic_judgment_reference": case_id,
        "proposed_initial_route": proposed_route,
        "runtime_resolved_route": resolved_route,
        "trigger_candidates_used": list(consumed),
        "validation_state": {
            "semantic_observation": "PASS",
            "routing_judgment": "PASS",
            "trigger_registry": "PASS",
        },
        "boundary_state": boundary_state,
    }
    return IntegrationResult(
        semantic_observation_validity="PASS",
        routing_judgment_validity="PASS",
        trigger_registry_validity="PASS",
        runtime_resolution=runtime_resolution,
        boundary_state=boundary_state,
        final_integration_result=final_result,
        decision=decision,
        proposed_initial_route=proposed_route,
        runtime_resolved_route=resolved_route,
        trigger_candidates_used=list(consumed),
        cross_routes=cross_routes,
        knowledge_addresses=knowledge_addresses,
        no_route_basis=copy.deepcopy(routing["no_route_basis"]),
        potential_inter_entity_impact=copy.deepcopy(
            observation["potential_inter_entity_impact"]
        ),
        coordination_trace=trace,
    )


def _validate_observation(observation: dict[str, Any]) -> None:
    value_intent = _object(observation["value_intent"], "semantic_observation.value_intent")
    _exact_keys(value_intent, {"state", "description"}, "semantic_observation.value_intent")
    _enum(value_intent["state"], {"KNOWN", "PARTIAL", "UNKNOWN"}, "value_intent.state")
    _nullable_string(value_intent["description"], "value_intent.description")
    _nullable_string(observation["presented_problem"], "presented_problem")

    materiality = _object(observation["materiality"], "semantic_observation.materiality")
    _exact_keys(materiality, {"state", "basis"}, "semantic_observation.materiality")
    _enum(materiality["state"], {"MATERIAL", "NOT_MATERIAL", "UNCERTAIN"}, "materiality.state")
    _string_list(materiality["basis"], "materiality.basis")

    factors = _object(observation["material_factors"], "semantic_observation.material_factors")
    factor_keys = {"unknowns", "dependencies", "conflicts", "constraints", "changes"}
    _exact_keys(factors, factor_keys, "semantic_observation.material_factors")
    for key in factor_keys:
        _string_list(factors[key], f"material_factors.{key}")
    for key in ("relevant_entities", "evidence_basis", "inferences", "assumptions", "uncertainties"):
        _string_list(observation[key], key)

    tension = _object(observation["value_tension"], "semantic_observation.value_tension")
    _exact_keys(tension, {"detected", "description"}, "semantic_observation.value_tension")
    _boolean(tension["detected"], "value_tension.detected")
    _nullable_string(tension["description"], "value_tension.description")

    impact = _object(
        observation["potential_inter_entity_impact"],
        "semantic_observation.potential_inter_entity_impact",
    )
    _exact_keys(
        impact,
        {"detected", "affected_entities", "basis"},
        "semantic_observation.potential_inter_entity_impact",
    )
    _boolean(impact["detected"], "potential_inter_entity_impact.detected")
    _string_list(impact["affected_entities"], "potential_inter_entity_impact.affected_entities")
    _string_list(impact["basis"], "potential_inter_entity_impact.basis")


def _validate_routing(routing: dict[str, Any]) -> None:
    decision = routing["decision"]
    _enum(decision, {"ROUTE", "NO_ROUTE", "HUMAN_VALIDATION_REQUIRED"}, "routing_judgment.decision")
    _nullable_string(routing["proposed_initial_route"], "routing_judgment.proposed_initial_route")
    candidates = routing["trigger_candidates"]
    if not isinstance(candidates, list):
        raise SemanticJudgmentError("routing_judgment.trigger_candidates must be a list")
    seen: set[str] = set()
    for index, candidate_value in enumerate(candidates):
        candidate = _object(candidate_value, f"trigger_candidates[{index}]")
        _exact_keys(candidate, {"trigger_id", "evidence_refs"}, f"trigger_candidates[{index}]")
        trigger_id = candidate["trigger_id"]
        if not isinstance(trigger_id, str) or not trigger_id:
            raise SemanticJudgmentError(f"trigger_candidates[{index}].trigger_id must be non-empty")
        if trigger_id in seen:
            raise SemanticJudgmentError(f"duplicate trigger candidate: {trigger_id}")
        seen.add(trigger_id)
        _string_list(candidate["evidence_refs"], f"trigger_candidates[{index}].evidence_refs")
    _string_list(routing["possible_secondary_dimensions"], "possible_secondary_dimensions")

    basis = _object(routing["no_route_basis"], "routing_judgment.no_route_basis")
    _exact_keys(basis, NO_ROUTE_BASIS_KEYS, "routing_judgment.no_route_basis")
    for key in NO_ROUTE_BASIS_KEYS:
        if basis[key] is not None and not isinstance(basis[key], bool):
            raise SemanticJudgmentError(f"no_route_basis.{key} must be boolean or null")
    _enum(routing["confidence"], {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}, "routing_judgment.confidence")

    if decision == "ROUTE":
        if not routing["proposed_initial_route"]:
            raise SemanticJudgmentError("ROUTE requires proposed_initial_route")
        if not candidates:
            raise SemanticJudgmentError("ROUTE requires at least one trigger candidate")
    if decision == "NO_ROUTE":
        if routing["proposed_initial_route"] is not None:
            raise SemanticJudgmentError("NO_ROUTE requires proposed_initial_route to be null")
        if candidates:
            raise SemanticJudgmentError("NO_ROUTE cannot carry trigger candidates")


def _resolved_route(initial: str | None, edge_ids: list[str], registry: dict[str, Any]) -> str | None:
    destinations = {
        edge["id"]: edge["to"] for edge in registry["routing"]["normal_edges"]
    }
    resolved = initial
    for edge_id in edge_ids:
        resolved = destinations[edge_id]
    return resolved


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SemanticJudgmentError(f"{path} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], path: str) -> None:
    missing = sorted(expected - value.keys())
    unexpected = sorted(value.keys() - expected)
    if missing:
        raise SemanticJudgmentError(f"{path} missing required field(s): {', '.join(missing)}")
    if unexpected:
        raise SemanticJudgmentError(f"{path} has forbidden field(s): {', '.join(unexpected)}")


def _enum(value: Any, allowed: set[str], path: str) -> None:
    if value not in allowed:
        raise SemanticJudgmentError(f"{path} has invalid enum value: {value!r}")


def _nullable_string(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, str):
        raise SemanticJudgmentError(f"{path} must be a string or null")


def _string_list(value: Any, path: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SemanticJudgmentError(f"{path} must be a list of strings")


def _boolean(value: Any, path: str) -> None:
    if not isinstance(value, bool):
        raise SemanticJudgmentError(f"{path} must be boolean")
