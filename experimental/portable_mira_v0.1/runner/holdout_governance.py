from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal


Eligibility = Literal["HOLDOUT_ELIGIBLE", "CONTAMINATED", "ELIGIBILITY_UNKNOWN"]
GovernanceState = Literal["PASS", "REVIEW_REQUIRED", "FAIL", "UNKNOWN"]
REQUIRED_ROLES = {
    "CASE_AUTHOR",
    "EXPECTATION_AUTHOR",
    "SEMANTIC_AGENT",
    "OUTPUT_ANNOTATOR",
    "DETERMINISTIC_EVALUATOR",
    "DISAGREEMENT_REVIEWER",
    "HUMAN_DECISION",
}
DISAGREEMENT_STATES = {
    "NONE",
    "EXPECTATION_OUTPUT_DISAGREEMENT",
    "ANNOTATION_UNCERTAINTY",
    "EVALUATOR_LIMITATION",
    "NORMATIVE_HUMAN_DECISION_REQUIRED",
}
CONTAMINATION_REASONS = {
    "SEMANTIC_AGENT_SAW_EXPECTATION",
    "CASE_USED_DURING_DEVELOPMENT",
    "OUTPUT_INFLUENCED_EXPECTATION",
    "SEAL_CREATED_AFTER_OUTPUT",
    "EVALUATOR_CHANGED_AFTER_OUTPUT",
    "EXPECTED_ANSWER_IN_ADAPTER_INSTRUCTIONS",
    "MATERIALLY_IDENTICAL_PRIOR_EXECUTION",
    "SEALED_ARTIFACT_CHANGED",
    "BASELINE_MISMATCH",
}


class HoldoutGovernanceError(Exception):
    """Governance protocol or record validation failed closed."""


@dataclass(frozen=True)
class GovernanceAssessment:
    case_id: str
    eligibility: Eligibility
    governance_state: GovernanceState
    contamination_reasons: tuple[str, ...]
    disagreements: tuple[str, ...]
    role_overlaps: tuple[str, ...]
    independence_limitations: tuple[str, ...]
    model_result_preserved: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def seal_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def load_protocol(path: Path) -> dict[str, Any]:
    try:
        protocol = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HoldoutGovernanceError(f"unable to load governance protocol: {path}") from exc
    validate_protocol(protocol)
    return copy.deepcopy(protocol)


def validate_protocol(protocol: Any) -> None:
    root = _object(protocol, "protocol")
    required = {
        "protocol_version", "classification", "evaluation_baseline_commit",
        "value_intent", "roles", "expectation_format", "sealing",
        "output_preservation", "annotation", "disagreement", "eligibility",
        "small_team_configuration", "counter_challenges",
    }
    _require(root, required, "protocol")
    if root["classification"] != "GOVERNANCE_PROTOCOL_NOT_HOLDOUT_CASES":
        raise HoldoutGovernanceError("protocol must not contain holdout cases")
    roles = _object(root["roles"], "roles")
    if set(roles) != REQUIRED_ROLES:
        raise HoldoutGovernanceError("protocol roles do not match required roles")
    blocked = set(roles["SEMANTIC_AGENT"].get("must_not_receive", []))
    required_blindness = {
        "expected route", "expected triggers", "expected diagnostics",
        "evaluator labels", "prior desired answer",
    }
    if not required_blindness <= blocked:
        raise HoldoutGovernanceError("Semantic Agent blindness boundary is incomplete")
    if root["sealing"].get("algorithm") != "SHA-256":
        raise HoldoutGovernanceError("sealing algorithm must be SHA-256")
    required_seals = {
        "natural_situation", "expectation_artifact",
        "evaluation_baseline_commit", "allowed_model_input",
    }
    if set(root["sealing"].get("required_artifacts", [])) != required_seals:
        raise HoldoutGovernanceError("required sealing artifacts are incomplete")
    output = root["output_preservation"]
    if output.get("hidden_reasoning_required") is not False or output.get("hidden_reasoning_stored") is not False:
        raise HoldoutGovernanceError("hidden reasoning must not be required or stored")
    if root["disagreement"].get("automatically_model_failure") is not False:
        raise HoldoutGovernanceError("disagreement cannot automatically fail the model")


def assess_record(
    record: dict[str, Any], protocol: dict[str, Any], sealed_payloads: dict[str, Any]
) -> GovernanceAssessment:
    validate_protocol(protocol)
    _validate_record_shape(record)
    contamination: set[str] = set()
    limitations: set[str] = set()

    assignments = record["role_assignments"]
    actors_by_role = {role: tuple(actors) for role, actors in assignments.items()}
    if set(actors_by_role) != REQUIRED_ROLES:
        raise HoldoutGovernanceError("record must assign every required role")
    actor_roles: dict[str, list[str]] = {}
    for role, actors in actors_by_role.items():
        if not actors:
            raise HoldoutGovernanceError(f"role has no actor: {role}")
        for actor in actors:
            actor_roles.setdefault(actor, []).append(role)
    overlaps = tuple(
        f"{actor}:{','.join(sorted(roles))}"
        for actor, roles in sorted(actor_roles.items()) if len(roles) > 1
    )
    declared = {
        item["actor_id"]: set(item["roles"])
        for item in record["role_overlap_declarations"]
    }
    for actor, roles in actor_roles.items():
        if len(roles) > 1 and declared.get(actor) != set(roles):
            raise HoldoutGovernanceError(f"role overlap is not fully declared: {actor}")
    if overlaps:
        limitations.add("ROLE_OVERLAP_LIMITS_INDEPENDENCE")

    exposure = record["information_exposure"]
    prohibited = set(protocol["roles"]["SEMANTIC_AGENT"]["must_not_receive"])
    if prohibited & set(exposure["semantic_agent_received"]):
        contamination.add("SEMANTIC_AGENT_SAW_EXPECTATION")
    if exposure["output_annotator_saw_expectations_before_annotation"]:
        limitations.add("ANNOTATOR_NOT_BLIND_TO_EXPECTATIONS")

    chronology = record["chronology"]
    expectation_time = chronology["expectation_created_at"]
    sealed_time = chronology["sealed_at"]
    output_time = chronology["model_output_received_at"]
    if expectation_time is None or sealed_time is None or output_time is None:
        eligibility_unknown = True
    else:
        eligibility_unknown = False
        if expectation_time >= output_time:
            contamination.add("OUTPUT_INFLUENCED_EXPECTATION")
        if sealed_time >= output_time:
            contamination.add("SEAL_CREATED_AFTER_OUTPUT")

    for artifact in protocol["sealing"]["required_artifacts"]:
        expected_hash = record["seals"].get(artifact)
        if artifact not in sealed_payloads or not isinstance(expected_hash, str):
            eligibility_unknown = True
            continue
        if seal_payload(sealed_payloads[artifact]) != expected_hash:
            contamination.add("SEALED_ARTIFACT_CHANGED")
    baseline = protocol["evaluation_baseline_commit"]
    if sealed_payloads.get("evaluation_baseline_commit") != baseline:
        contamination.add("BASELINE_MISMATCH")

    origin = record["case_provenance"]
    if origin == "DEVELOPMENT_CASE":
        contamination.add("CASE_USED_DURING_DEVELOPMENT")
    elif origin == "PRIOR_EXECUTED_MATERIALLY_IDENTICAL":
        contamination.add("MATERIALLY_IDENTICAL_PRIOR_EXECUTION")
    elif origin == "UNKNOWN":
        eligibility_unknown = True

    signals = record["contamination_signals"]
    for key, diagnostic in (
        ("evaluator_changed_after_output", "EVALUATOR_CHANGED_AFTER_OUTPUT"),
        ("expected_answer_in_adapter_instructions", "EXPECTED_ANSWER_IN_ADAPTER_INSTRUCTIONS"),
        ("materially_identical_prior_execution", "MATERIALLY_IDENTICAL_PRIOR_EXECUTION"),
    ):
        if signals[key]:
            contamination.add(diagnostic)

    raw = record["raw_output"]
    metadata = _object(raw.get("metadata"), "raw_output.metadata")
    required_metadata = set(protocol["output_preservation"]["required_metadata"])
    _require(metadata, required_metadata, "raw_output.metadata")
    if metadata["case_id"] != record["case_id"]:
        raise HoldoutGovernanceError("raw output case_id does not match governance record")
    raw_hash = seal_payload(raw["observable_semantic_judgment"])
    if raw_hash != metadata["output_sha256"]:
        contamination.add("SEALED_ARTIFACT_CHANGED")
    if metadata["no_hidden_reasoning_stored"] is not True:
        raise HoldoutGovernanceError("raw output record must exclude hidden reasoning")
    annotation = record["annotation"]
    if annotation["raw_output_sha256"] != raw_hash:
        contamination.add("SEALED_ARTIFACT_CHANGED")
    if annotation["state"] == "ANNOTATOR_UNCERTAIN":
        disagreements = set(record["disagreement_states"]) | {"ANNOTATION_UNCERTAINTY"}
    else:
        disagreements = set(record["disagreement_states"])
    if not disagreements <= DISAGREEMENT_STATES:
        raise HoldoutGovernanceError("invalid disagreement state")
    annotation_vocabulary = protocol["annotation"]
    for field in (
        "evidence_discipline", "semantic_sparsity", "impact_discipline", "human_burden"
    ):
        values = annotation.get(field)
        if not isinstance(values, list) or not set(values) <= set(annotation_vocabulary[field]):
            raise HoldoutGovernanceError(f"annotation.{field} contains invalid values")

    for review in record["post_hoc_reviews"]:
        if review["original_expectation_sha256"] != record["seals"]["expectation_artifact"]:
            raise HoldoutGovernanceError("post-hoc review does not preserve original expectation")
        if review["proposed_expectation_sha256"] == review["original_expectation_sha256"]:
            raise HoldoutGovernanceError("post-hoc review must be a separate proposed artifact")

    unknown_reasons = contamination - CONTAMINATION_REASONS
    if unknown_reasons:
        raise HoldoutGovernanceError("unknown contamination reason")
    if contamination:
        eligibility: Eligibility = "CONTAMINATED"
    elif eligibility_unknown:
        eligibility = "ELIGIBILITY_UNKNOWN"
    else:
        eligibility = "HOLDOUT_ELIGIBLE"

    active_disagreements = disagreements - {"NONE"}
    if active_disagreements:
        governance_state: GovernanceState = "REVIEW_REQUIRED"
    elif eligibility == "ELIGIBILITY_UNKNOWN":
        governance_state = "UNKNOWN"
    elif eligibility == "CONTAMINATED":
        governance_state = "FAIL"
    else:
        governance_state = "PASS"
    return GovernanceAssessment(
        case_id=record["case_id"],
        eligibility=eligibility,
        governance_state=governance_state,
        contamination_reasons=tuple(sorted(contamination)),
        disagreements=tuple(sorted(disagreements)),
        role_overlaps=overlaps,
        independence_limitations=tuple(sorted(limitations)),
        model_result_preserved=record["model_result"],
    )


def _validate_record_shape(record: Any) -> None:
    root = _object(record, "record")
    required = {
        "record_type", "case_id", "case_provenance", "role_assignments",
        "role_overlap_declarations", "information_exposure", "chronology",
        "seals", "contamination_signals", "raw_output", "annotation",
        "disagreement_states", "post_hoc_reviews", "model_result",
    }
    _require(root, required, "record")
    if root["record_type"] != "HOLDOUT_GOVERNANCE_RECORD":
        raise HoldoutGovernanceError("invalid governance record type")
    if not isinstance(root["case_id"], str) or not root["case_id"]:
        raise HoldoutGovernanceError("case_id must be non-empty")
    if root["annotation"].get("state") not in {"COMPLETE", "ANNOTATOR_UNCERTAIN", "NOT_STARTED"}:
        raise HoldoutGovernanceError("invalid annotation state")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HoldoutGovernanceError(f"{path} must be an object")
    return value


def _require(value: dict[str, Any], keys: set[str], path: str) -> None:
    missing = sorted(keys - value.keys())
    if missing:
        raise HoldoutGovernanceError(f"{path} missing required field(s): {', '.join(missing)}")
