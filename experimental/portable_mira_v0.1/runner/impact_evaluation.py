from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


InterestState = Literal["RECOGNIZED", "NOT_RECOGNIZED", "UNKNOWN"]


@dataclass(frozen=True)
class EntityImpactEvidence:
    entity_id: str
    operationally_affected: bool
    independently_relevant_interests: InterestState
    material_impact_evidence: bool
    claimed_material_inter_entity_impact: bool
    represented_or_delegated_actor: bool = False


@dataclass(frozen=True)
class ImpactDiagnostic:
    operationally_affected: tuple[str, ...]
    potential_material_inter_entity_impact: tuple[str, ...]
    impact_inflation_candidates: tuple[str, ...]
    impact_misses: tuple[str, ...]
    diagnostic_only: bool = True
    changes_authority: bool = False
    changes_boundary_state: bool = False

    def to_dict(self):
        return asdict(self)


def evaluate_impact(evidence: tuple[EntityImpactEvidence, ...]) -> ImpactDiagnostic:
    entity_ids = [item.entity_id for item in evidence]
    if any(not isinstance(entity_id, str) or not entity_id for entity_id in entity_ids):
        raise ValueError("entity_id must be a non-empty string")
    if len(set(entity_ids)) != len(entity_ids):
        raise ValueError("entity_id must be unique")
    for item in evidence:
        if item.independently_relevant_interests not in {
            "RECOGNIZED",
            "NOT_RECOGNIZED",
            "UNKNOWN",
        }:
            raise ValueError("invalid independently relevant interest state")

    operational = {
        item.entity_id for item in evidence if item.operationally_affected
    }
    potential = {
        item.entity_id
        for item in evidence
        if item.independently_relevant_interests == "RECOGNIZED"
        and item.material_impact_evidence
    }
    claimed = {
        item.entity_id
        for item in evidence
        if item.claimed_material_inter_entity_impact
    }
    return ImpactDiagnostic(
        operationally_affected=tuple(sorted(operational)),
        potential_material_inter_entity_impact=tuple(sorted(potential)),
        impact_inflation_candidates=tuple(sorted(claimed - potential)),
        impact_misses=tuple(sorted(potential - claimed)),
    )
