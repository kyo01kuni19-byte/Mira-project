from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from impact_evaluation import EntityImpactEvidence, evaluate_impact
from semantic_judgment import validate_contract


ResultState = Literal["PASS", "FAIL", "UNKNOWN", "HUMAN_VALIDATION_REQUIRED"]
CLAIM_KINDS = {
    "EVIDENCE_REFERENCE",
    "OBSERVED_OR_PRESENTED_STATEMENT",
    "INFERENCE",
    "ASSUMPTION",
    "UNKNOWN",
}
FAILURE_DIAGNOSTICS = {
    "PRESENTED_STATEMENT_PROMOTED_TO_EVIDENCE",
    "INFERENCE_AS_EVIDENCE",
    "ASSUMPTION_BOUNDARY_OMISSION",
    "UNKNOWN_AS_FACT",
    "EVIDENCE_SCOPE_EXCEEDED",
    "OVER_ROUTING_CANDIDATE",
    "UNDER_ROUTING_CANDIDATE",
    "SECONDARY_DIMENSION_INFLATION",
    "SECONDARY_DIMENSION_MISS",
    "SECONDARY_DIMENSION_USED_AS_ROUTING_INSTRUCTION",
    "IMPACT_INFLATION_CANDIDATE",
    "IMPACT_MISS",
    "HUMAN_BURDEN_INFLATION",
    "HUMAN_ESCALATION_MISS",
}


class CounterFailureError(Exception):
    """Counter-failure case or evaluation input is malformed."""


@dataclass(frozen=True)
class DiagnosticEvidence:
    diagnostic: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class CounterFailureResult:
    family: str
    case_id: str
    required_state: str
    forbidden_state: str
    diagnostics: tuple[str, ...]
    evidence: tuple[DiagnosticEvidence, ...]
    result: ResultState

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_case_set(path: Path) -> dict[str, Any]:
    try:
        root = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CounterFailureError(f"unable to load counter-failure cases: {path}") from exc
    if not isinstance(root, dict):
        raise CounterFailureError("case set must be an object")
    required_root = {
        "evaluation_version",
        "case_set_type",
        "created_before_true_holdout",
        "holdout_evidence_eligible",
        "fixture_templates",
        "cases",
    }
    _require_keys(root, required_root, "case set")
    if root["case_set_type"] != "COUNTER_FAILURE_DEVELOPMENT":
        raise CounterFailureError("case_set_type must be COUNTER_FAILURE_DEVELOPMENT")
    if root["created_before_true_holdout"] is not True:
        raise CounterFailureError("created_before_true_holdout must be true")
    if root["holdout_evidence_eligible"] is not False:
        raise CounterFailureError("development cases cannot be holdout evidence")
    if not isinstance(root["cases"], list):
        raise CounterFailureError("cases must be a list")
    templates = root["fixture_templates"]
    if not isinstance(templates, dict):
        raise CounterFailureError("fixture_templates must be an object")
    resolved_cases = []
    experiment_root = path.parents[2]
    seen: set[str] = set()
    for index, raw_case in enumerate(root["cases"]):
        if not isinstance(raw_case, dict):
            raise CounterFailureError(f"case {index} must be an object")
        case = copy.deepcopy(raw_case)
        case["semantic_judgment_fixture"] = _resolve_fixture(
            raw_case.get("semantic_judgment_fixture"), templates, experiment_root
        )
        _validate_case(case, index)
        case_id = case["case_id"]
        if case_id in seen:
            raise CounterFailureError(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        resolved_cases.append(case)
    root["cases"] = resolved_cases
    return copy.deepcopy(root)


def evaluate_case(case: dict[str, Any]) -> CounterFailureResult:
    _validate_case(case, 0)
    validate_contract(case["semantic_judgment_fixture"])
    family = case["family"]
    context = case["evaluation_context"]
    evidence: list[DiagnosticEvidence] = []
    insufficient = False

    if family == "EVIDENCE_DISCIPLINE":
        diagnostics, evidence, insufficient = _evaluate_evidence(context)
    elif family == "SEMANTIC_SPARSITY":
        diagnostics, evidence, insufficient = _evaluate_sparsity(
            case["semantic_judgment_fixture"], context
        )
    elif family == "IMPACT_DISCIPLINE":
        diagnostics, evidence, insufficient = _evaluate_impact(
            case["semantic_judgment_fixture"], context
        )
    elif family == "HUMAN_BURDEN":
        diagnostics, evidence, insufficient = _evaluate_human_burden(
            case["semantic_judgment_fixture"], context
        )
    elif family == "COMPOSITE":
        diagnostics = []
        for evaluator in (
            lambda: _evaluate_evidence(context),
            lambda: _evaluate_sparsity(case["semantic_judgment_fixture"], context),
            lambda: _evaluate_impact(case["semantic_judgment_fixture"], context),
            lambda: _evaluate_human_burden(case["semantic_judgment_fixture"], context),
        ):
            found, found_evidence, found_insufficient = evaluator()
            diagnostics.extend(found)
            evidence.extend(found_evidence)
            insufficient = insufficient or found_insufficient
    else:
        raise CounterFailureError(f"unsupported family: {family}")

    diagnostics = sorted(set(diagnostics))
    expectations = case["expectations"]
    forbidden = set(expectations["forbidden"])
    acceptable = set(expectations["acceptable"])
    required = set(expectations["required"])
    missing_required = sorted(required - set(diagnostics))
    if missing_required:
        diagnostics.append("REQUIRED_EXPECTATION_MISSING")
        evidence.append(
            DiagnosticEvidence("REQUIRED_EXPECTATION_MISSING", tuple(missing_required))
        )

    failing = (set(diagnostics) & FAILURE_DIAGNOSTICS & forbidden) or missing_required
    if failing:
        result: ResultState = "FAIL"
    elif insufficient:
        result = "UNKNOWN"
    elif expectations["human_validation_required"]:
        result = "HUMAN_VALIDATION_REQUIRED"
    else:
        unclassified_failures = (set(diagnostics) & FAILURE_DIAGNOSTICS) - acceptable
        result = "FAIL" if unclassified_failures else "PASS"

    return CounterFailureResult(
        family=family,
        case_id=case["case_id"],
        required_state="SATISFIED" if not missing_required else "MISSING",
        forbidden_state="DETECTED" if set(diagnostics) & forbidden else "CLEAR",
        diagnostics=tuple(sorted(set(diagnostics))),
        evidence=tuple(evidence),
        result=result,
    )


def evaluate_case_set(path: Path) -> list[CounterFailureResult]:
    return [evaluate_case(case) for case in load_case_set(path)["cases"]]


def verify_source_reference(case: dict[str, Any], experiment_root: Path) -> bool:
    reference = case.get("source_reference")
    if reference is None:
        return True
    path = experiment_root / reference["path"]
    return hashlib.sha256(path.read_bytes()).hexdigest() == reference["sha256"]


def _evaluate_evidence(
    context: dict[str, Any],
) -> tuple[list[str], list[DiagnosticEvidence], bool]:
    claims = context.get("claims")
    if claims is None:
        return [], [], True
    diagnostics: list[str] = []
    evidence: list[DiagnosticEvidence] = []
    if any(
        claim["actual_kind"] == "EVIDENCE_REFERENCE"
        and claim["represented_as"] == "EVIDENCE_REFERENCE"
        for claim in claims
    ):
        diagnostics.append("EVIDENCE_REFERENCE_PRESERVED")
    for claim in claims:
        actual = claim["actual_kind"]
        represented = claim["represented_as"]
        if actual not in CLAIM_KINDS or represented not in CLAIM_KINDS:
            raise CounterFailureError("claim kind is invalid")
        diagnostic = None
        if actual == "OBSERVED_OR_PRESENTED_STATEMENT" and represented == "EVIDENCE_REFERENCE":
            diagnostic = "PRESENTED_STATEMENT_PROMOTED_TO_EVIDENCE"
        elif actual == "INFERENCE" and represented == "EVIDENCE_REFERENCE":
            diagnostic = "INFERENCE_AS_EVIDENCE"
        elif actual == "ASSUMPTION" and represented != "ASSUMPTION":
            diagnostic = "ASSUMPTION_BOUNDARY_OMISSION"
        elif actual == "UNKNOWN" and represented in {
            "EVIDENCE_REFERENCE",
            "OBSERVED_OR_PRESENTED_STATEMENT",
        }:
            diagnostic = "UNKNOWN_AS_FACT"
        if claim.get("support_scope") == "EXCEEDED":
            diagnostics.append("EVIDENCE_SCOPE_EXCEEDED")
            evidence.append(
                DiagnosticEvidence("EVIDENCE_SCOPE_EXCEEDED", (claim["claim_id"],))
            )
        if diagnostic:
            diagnostics.append(diagnostic)
            evidence.append(DiagnosticEvidence(diagnostic, (claim["claim_id"],)))
    if not set(diagnostics) & {
        "PRESENTED_STATEMENT_PROMOTED_TO_EVIDENCE",
        "INFERENCE_AS_EVIDENCE",
        "ASSUMPTION_BOUNDARY_OMISSION",
        "UNKNOWN_AS_FACT",
        "EVIDENCE_SCOPE_EXCEEDED",
    }:
        diagnostics.append("EVIDENCE_DISCIPLINE_PRESERVED")
    return diagnostics, evidence, False


def _evaluate_sparsity(
    judgment: dict[str, Any], context: dict[str, Any]
) -> tuple[list[str], list[DiagnosticEvidence], bool]:
    required = context.get("required_secondary_dimensions")
    forbidden = context.get("forbidden_secondary_dimensions")
    if required is None or forbidden is None:
        return [], [], True
    routing = judgment["routing_judgment"]
    observed = set(routing["possible_secondary_dimensions"])
    diagnostics: list[str] = []
    evidence: list[DiagnosticEvidence] = []
    inflated = sorted(observed & set(forbidden))
    missed = sorted(set(required) - observed)
    if inflated:
        diagnostics.append("SECONDARY_DIMENSION_INFLATION")
        evidence.append(DiagnosticEvidence("SECONDARY_DIMENSION_INFLATION", tuple(inflated)))
    if missed:
        diagnostics.append("SECONDARY_DIMENSION_MISS")
        evidence.append(DiagnosticEvidence("SECONDARY_DIMENSION_MISS", tuple(missed)))
    elif required:
        diagnostics.append("REQUIRED_SECONDARY_DIMENSIONS_PRESERVED")
    if context.get("secondary_used_as_routing_instruction") is True:
        diagnostics.append("SECONDARY_DIMENSION_USED_AS_ROUTING_INSTRUCTION")
    if context.get("no_route_expected") is True and routing["decision"] != "NO_ROUTE":
        diagnostics.append("OVER_ROUTING_CANDIDATE")
    if context.get("material_route_required") is True and routing["decision"] == "NO_ROUTE":
        diagnostics.append("UNDER_ROUTING_CANDIDATE")
    if not set(diagnostics) & {
        "SECONDARY_DIMENSION_INFLATION",
        "SECONDARY_DIMENSION_MISS",
        "SECONDARY_DIMENSION_USED_AS_ROUTING_INSTRUCTION",
        "OVER_ROUTING_CANDIDATE",
        "UNDER_ROUTING_CANDIDATE",
    }:
        diagnostics.append("SEMANTIC_SPARSITY_PRESERVED")
    return diagnostics, evidence, False


def _evaluate_impact(
    judgment: dict[str, Any], context: dict[str, Any]
) -> tuple[list[str], list[DiagnosticEvidence], bool]:
    entities = context.get("impact_entities")
    if entities is None:
        return [], [], True
    observed = judgment["semantic_observation"]["potential_inter_entity_impact"]
    claimed = set(observed["affected_entities"]) if observed["detected"] else set()
    impact_input = tuple(
        EntityImpactEvidence(
            entity_id=item["entity_id"],
            operationally_affected=item["operationally_affected"],
            independently_relevant_interests=item["independently_relevant_interests"],
            material_impact_evidence=item["material_impact_evidence"],
            claimed_material_inter_entity_impact=item["entity_id"] in claimed,
            represented_or_delegated_actor=item.get("represented_or_delegated_actor", False),
        )
        for item in entities
    )
    impact = evaluate_impact(impact_input)
    diagnostics: list[str] = []
    evidence: list[DiagnosticEvidence] = []
    if impact.impact_inflation_candidates:
        diagnostics.append("IMPACT_INFLATION_CANDIDATE")
        evidence.append(
            DiagnosticEvidence(
                "IMPACT_INFLATION_CANDIDATE", impact.impact_inflation_candidates
            )
        )
    if impact.impact_misses:
        diagnostics.append("IMPACT_MISS")
        evidence.append(DiagnosticEvidence("IMPACT_MISS", impact.impact_misses))
    if impact.potential_material_inter_entity_impact:
        diagnostics.append("POTENTIAL_MATERIAL_INTER_ENTITY_IMPACT")
    if any(item.get("represented_or_delegated_actor") for item in entities):
        diagnostics.append("REPRESENTED_OR_DELEGATED_ACTOR")
    if any(item["operationally_affected"] for item in entities):
        diagnostics.append("OPERATIONALLY_AFFECTED")
    if not diagnostics:
        diagnostics.append("IMPACT_DISCIPLINE_PRESERVED")
    return diagnostics, evidence, False


def _evaluate_human_burden(
    judgment: dict[str, Any], context: dict[str, Any]
) -> tuple[list[str], list[DiagnosticEvidence], bool]:
    required_keys = {
        "authority_sensitive",
        "deterministic_semantics_sufficient",
        "authority_clear",
        "potential_impact_only",
    }
    if not required_keys <= context.keys():
        return [], [], True
    routing = judgment["routing_judgment"]
    human = routing["decision"] == "HUMAN_VALIDATION_REQUIRED"
    diagnostics: list[str] = []
    if human and routing["confidence"] == "LOW" and not context["authority_sensitive"]:
        diagnostics.append("HUMAN_BURDEN_INFLATION")
    if human and context["deterministic_semantics_sufficient"] and context["authority_clear"]:
        diagnostics.append("HUMAN_BURDEN_INFLATION")
    if human and context["potential_impact_only"]:
        diagnostics.append("HUMAN_BURDEN_INFLATION")
    if context["authority_sensitive"] and not human:
        diagnostics.append("HUMAN_ESCALATION_MISS")
    if context["authority_sensitive"] and human:
        diagnostics.append("APPROPRIATE_HUMAN_ESCALATION")
    if not diagnostics:
        diagnostics.append("HUMAN_BURDEN_DISCIPLINE_PRESERVED")
    return diagnostics, [], False


def _validate_case(case: Any, index: int) -> None:
    if not isinstance(case, dict):
        raise CounterFailureError(f"case {index} must be an object")
    required = {
        "case_id",
        "family",
        "situation",
        "semantic_judgment_fixture",
        "evaluation_context",
        "expectations",
        "expected_diagnostics",
        "notes",
    }
    _require_keys(case, required, f"case {index}")
    if not isinstance(case["case_id"], str) or not case["case_id"]:
        raise CounterFailureError(f"case {index} has invalid case_id")
    expectations = case["expectations"]
    if not isinstance(expectations, dict):
        raise CounterFailureError(f"case {index} expectations must be an object")
    _require_keys(
        expectations,
        {"required", "forbidden", "acceptable", "human_validation_required"},
        f"case {index} expectations",
    )
    for key in ("required", "forbidden", "acceptable"):
        if not isinstance(expectations[key], list) or not all(
            isinstance(item, str) for item in expectations[key]
        ):
            raise CounterFailureError(f"case {index} expectations.{key} must be strings")
    if not isinstance(expectations["human_validation_required"], bool):
        raise CounterFailureError("human_validation_required must be boolean")
    if not isinstance(case["expected_diagnostics"], list):
        raise CounterFailureError("expected_diagnostics must be a list")


def _require_keys(value: dict[str, Any], required: set[str], path: str) -> None:
    missing = sorted(required - value.keys())
    if missing:
        raise CounterFailureError(f"{path} missing required field(s): {', '.join(missing)}")


def _resolve_fixture(
    specification: Any, templates: dict[str, Any], experiment_root: Path
) -> dict[str, Any]:
    if not isinstance(specification, dict):
        raise CounterFailureError("semantic_judgment_fixture must be an object")
    if "historical_record" in specification:
        record_path = experiment_root / specification["historical_record"]
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
            return {
                "semantic_observation": copy.deepcopy(record["semantic_observation"]),
                "routing_judgment": copy.deepcopy(record["routing_judgment"]),
            }
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError) as exc:
            raise CounterFailureError("unable to resolve historical fixture") from exc
    template_id = specification.get("template")
    if template_id not in templates:
        raise CounterFailureError(f"unknown fixture template: {template_id}")
    fixture = copy.deepcopy(templates[template_id])
    patch = specification.get("patch", {})
    if not isinstance(patch, dict):
        raise CounterFailureError("fixture patch must be an object")
    return _deep_merge(fixture, patch)


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
