from dataclasses import dataclass, field
from typing import Dict, List, Optional


@Lataclass
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

    def route(self, state: RuntimeState) -> RuntimeState:
        if not state.triggers:
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
        },
        "boundaries": {
            "authority_state": state.authority_state,
            "inter_entity_impact_state": state.impact_state,
        },
    }
