import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RoutingEdge:
    id: str
    from_capability: str
    to_capability: str
    trigger: str
    knowledge: List[str] = field(default_factory=list)


@dataclass
class RuntimeState:
    case_id: str
    value_intent: str
    initial_route: Optional[str] = None
    triggers: List[str] = field(default_factory=list)
    knowledge_addresses: List[str] = field(default_factory=list)
    cross_routes: List[str] = field(default_factory=list)
    authority_state: str = "UNKNOWN"
    impact_state: str = "UNKNOWN"
    routing_result: str = "UNKNOWN"
    no_route_reason: Optional[str] = None
    execution_state: str = "NOT_EXECUTED"


class RouterError(Exception):
    pass


class Router:
    """Deterministic portion of Portable MIRA semantic routing.

    This class does not judge whether a trigger is materially true.
    It applies already-established semantic triggers to a registry,
    resolves knowledge addresses, and enforces blocking boundary state.
    """

    def __init__(self, edges: List[RoutingEdge], knowledge_registry: Dict[str, dict]):
        self.edges = edges
        self.knowledge_registry = knowledge_registry

    @classmethod
    def from_registry_file(cls, registry_path: Path) -> "Router":
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise RouterError(f"Unable to load generated registry: {registry_path}") from exc

        if not isinstance(registry, dict):
            raise RouterError("Generated registry root must be an object")
        if registry.get("artifact_type") != "portable_mira.registry_runtime":
            raise RouterError("Generated registry has unexpected artifact_type")

        routing = registry.get("routing")
        knowledge = registry.get("knowledge")
        if not isinstance(routing, dict) or not isinstance(knowledge, dict):
            raise RouterError("Generated registry is missing routing or knowledge data")
        raw_edges = routing.get("normal_edges")
        resolved = knowledge.get("resolved_registry_entries")
        if not isinstance(raw_edges, list) or not isinstance(resolved, dict):
            raise RouterError("Generated registry has invalid edges or knowledge entries")

        edges = [cls._edge_from_registry(item, index) for index, item in enumerate(raw_edges)]
        router = cls(edges, resolved)
        for edge in edges:
            for address in edge.knowledge:
                router._resolve_knowledge(address)
        return router

    @staticmethod
    def _edge_from_registry(item: Any, index: int) -> RoutingEdge:
        if not isinstance(item, dict):
            raise RouterError(f"Generated routing edge at index {index} must be an object")
        for name in ("id", "from", "trigger", "to"):
            if not isinstance(item.get(name), str) or not item[name]:
                raise RouterError(
                    f"Generated routing edge at index {index} has invalid field: {name}"
                )
        addresses = item.get("knowledge", [])
        if not isinstance(addresses, list) or not all(
            isinstance(address, str) for address in addresses
        ):
            raise RouterError(
                f"Generated routing edge {item['id']} has invalid knowledge addresses"
            )
        return RoutingEdge(
            id=item["id"],
            from_capability=item["from"],
            to_capability=item["to"],
            trigger=item["trigger"],
            knowledge=list(addresses),
        )

    def route(self, state: RuntimeState) -> RuntimeState:
        if self.enforce_boundary(state) == "BLOCKED":
            state.execution_state = "BLOCKED"
            return state

        if not state.triggers:
            state.routing_result = "NO_ROUTE"
            state.no_route_reason = "no_material_trigger"
            return state

        current = state.initial_route
        for edge in self.edges:
            if edge.trigger not in state.triggers:
                continue
            if current is not None and edge.from_capability != current:
                continue
            state.cross_routes.append(edge.id)
            current = edge.to_capability
            for address in edge.knowledge:
                self._resolve_knowledge(address)
                if address not in state.knowledge_addresses:
                    state.knowledge_addresses.append(address)

        state.routing_result = "SUPPORTED" if state.cross_routes else "MISSING_EDGE"
        return state

    def _resolve_knowledge(self, address: str) -> dict:
        if address not in self.knowledge_registry:
            raise RouterError(f"Unresolved knowledge address: {address}")
        return self.knowledge_registry[address]

    @staticmethod
    def enforce_boundary(state: RuntimeState) -> str:
        if state.impact_state == "BLOCKED":
            return "BLOCKED"
        if state.authority_state == "BLOCKED":
            return "BLOCKED"
        return "CLEAR"


def build_trace(state: RuntimeState) -> dict:
    """Return observable coordination state only."""
    return {
        "case_id": state.case_id,
        "value_intent": state.value_intent,
        "routing": {
            "initial_route": state.initial_route,
            "trigger_evidence": list(state.triggers),
            "knowledge_addresses_used": list(state.knowledge_addresses),
            "cross_routes": list(state.cross_routes),
            "no_route_reason": state.no_route_reason,
            "routing_result": state.routing_result,
        },
        "boundaries": {
            "authority_check": {"state": state.authority_state},
            "inter_entity_impact_check": {"state": state.impact_state},
        },
        "action": {"execution_state": state.execution_state},
    }
