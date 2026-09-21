from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from holdout_governance import (
    GovernanceAssessment,
    assess_record,
    canonical_json_bytes,
    load_protocol,
    seal_payload,
)


ARCHITECTURE_BASELINE = "e6f619d25bd120c7110ab9ede72b8c78ebeaa096"
EVALUATION_BASELINE = "cde62fdd47d7a19176d9c0d8907494d5a85787f1"
GOVERNANCE_BASELINE = "5d5290913b8a80898ef6e1a4e7eec3cc5f534808"
OUTPUT_ANNOTATOR_BASELINE = "023ed3ceb35974b532c1cc9a1cf3af6cdca33783"
CASE_IDS = ("TH-CASE-001", "TH-CASE-002", "TH-CASE-003")


class TrueHoldoutSealError(Exception):
    """A true-holdout candidate could not be sealed or verified."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TrueHoldoutSealError(f"unable to load JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise TrueHoldoutSealError(f"artifact must be a JSON object: {path}")
    return value


def write_canonical_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical_json_bytes(value))


def case_payloads(case_dir: Path) -> dict[str, Any]:
    return {
        "natural_situation": load_json(case_dir / "natural_situation.json"),
        "expectation_artifact": load_json(case_dir / "expectation.json"),
        "evaluation_baseline_commit": EVALUATION_BASELINE,
        "allowed_model_input": load_json(case_dir / "allowed_model_input.json"),
        "governance_baseline_commit": GOVERNANCE_BASELINE,
    }


def validate_pre_execution_artifacts(case_id: str, payloads: dict[str, Any]) -> None:
    natural = payloads["natural_situation"]
    expectation = payloads["expectation_artifact"]
    allowed = payloads["allowed_model_input"]

    if natural.get("artifact_type") != "HUMAN_AUTHORED_NATURAL_SITUATION":
        raise TrueHoldoutSealError("natural situation artifact type is invalid")
    if natural.get("case_author_role") != "HUMAN":
        raise TrueHoldoutSealError("case author must be HUMAN")
    if expectation.get("artifact_type") != "PRE_EXECUTION_EXPECTATION":
        raise TrueHoldoutSealError("expectation artifact type is invalid")
    if expectation.get("expectation_author_role") != "MIRA":
        raise TrueHoldoutSealError("expectation author must be MIRA")
    if expectation.get("expectation_created_before_model_output") is not True:
        raise TrueHoldoutSealError("expectation must predate model output")
    if allowed.get("artifact_type") != "ALLOWED_MODEL_INPUT":
        raise TrueHoldoutSealError("allowed model input artifact type is invalid")

    for artifact in (natural, expectation, allowed):
        if artifact.get("case_id") != case_id:
            raise TrueHoldoutSealError("case identifier mismatch")
    if natural.get("case_set_type") != "TRUE_HOLDOUT_CANDIDATE":
        raise TrueHoldoutSealError("natural situation must remain a candidate")
    if expectation.get("case_set_type") != "TRUE_HOLDOUT_CANDIDATE":
        raise TrueHoldoutSealError("expectation must remain a candidate")

    constraints = expectation.get("constraints")
    required_classes = {
        "REQUIRED",
        "FORBIDDEN",
        "ACCEPTABLE_OR_EVIDENCE_DEPENDENT",
        "HUMAN_VALIDATION_REQUIRED",
    }
    if not isinstance(constraints, dict) or set(constraints) != required_classes:
        raise TrueHoldoutSealError("expectation constraint classes are incomplete")
    if any(not isinstance(constraints[name], list) or not constraints[name] for name in required_classes):
        raise TrueHoldoutSealError("every expectation constraint class must be non-empty")

    allowed_keys = {
        "artifact_type",
        "case_id",
        "semantic_judgment_contract_version",
        "semantic_judgment_input",
    }
    if set(allowed) != allowed_keys:
        raise TrueHoldoutSealError("allowed model input contains an unauthorized field")
    model_input = allowed.get("semantic_judgment_input")
    if not isinstance(model_input, dict) or set(model_input) != {
        "situation",
        "value_intent",
        "available_evidence_refs",
        "authority_context",
    }:
        raise TrueHoldoutSealError("semantic judgment input shape is invalid")
    if model_input["situation"] != natural.get("natural_situation"):
        raise TrueHoldoutSealError("allowed input changed the Human-authored situation")
    if model_input["value_intent"] is not None:
        raise TrueHoldoutSealError("an unsupplied value intent was added")
    if model_input["available_evidence_refs"] != []:
        raise TrueHoldoutSealError("unsupplied evidence references were added")
    if model_input["authority_context"] is not None:
        raise TrueHoldoutSealError("an unsupplied authority context was added")

    serialized = json.dumps(allowed, ensure_ascii=False, sort_keys=True)
    prohibited = (
        "REQUIRED",
        "FORBIDDEN",
        "ACCEPTABLE_OR_EVIDENCE_DEPENDENT",
        "HUMAN_VALIDATION_REQUIRED",
        "expected_route",
        "expected_trigger",
        "expected_diagnostic",
        "evaluator_result",
        "desired_answer",
    )
    if any(item in serialized for item in prohibited):
        raise TrueHoldoutSealError("allowed input exposes expectation material")


def pre_execution_governance_record(
    case_id: str, seals: dict[str, str]
) -> dict[str, Any]:
    empty_output: dict[str, Any] = {}
    empty_output_hash = seal_payload(empty_output)
    return {
        "record_type": "HOLDOUT_GOVERNANCE_RECORD",
        "case_id": case_id,
        "case_provenance": "UNKNOWN",
        "role_assignments": {
            "CASE_AUTHOR": ["HUMAN"],
            "EXPECTATION_AUTHOR": ["MIRA"],
            "SEMANTIC_AGENT": ["OPENAI_SEMANTIC_ADAPTER_NOT_EXECUTED"],
            "OUTPUT_ANNOTATOR": ["TO_BE_SELECTED"],
            "DETERMINISTIC_EVALUATOR": ["CODEX"],
            "DISAGREEMENT_REVIEWER": ["MIRA"],
            "HUMAN_DECISION": ["HUMAN"],
        },
        "role_overlap_declarations": [
            {
                "actor_id": "HUMAN",
                "roles": ["CASE_AUTHOR", "HUMAN_DECISION"],
                "independence_effect": "LIMITED_NOT_INDEPENDENT",
            },
            {
                "actor_id": "MIRA",
                "roles": ["EXPECTATION_AUTHOR", "DISAGREEMENT_REVIEWER"],
                "independence_effect": "LIMITED_NOT_INDEPENDENT",
            },
        ],
        "information_exposure": {
            "semantic_agent_received": [],
            "output_annotator_saw_expectations_before_annotation": False,
        },
        "chronology": {
            "expectation_created_at": "PRE_MODEL_EXECUTION",
            "sealed_at": "PRE_MODEL_EXECUTION",
            "model_output_received_at": None,
        },
        "seals": {
            "natural_situation": seals["natural_situation"],
            "expectation_artifact": seals["expectation_artifact"],
            "evaluation_baseline_commit": seals["evaluation_baseline_commit"],
            "allowed_model_input": seals["allowed_model_input"],
        },
        "contamination_signals": {
            "evaluator_changed_after_output": False,
            "expected_answer_in_adapter_instructions": False,
            "materially_identical_prior_execution": False,
        },
        "raw_output": {
            "observable_semantic_judgment": empty_output,
            "metadata": {
                "provider": "NOT_EXECUTED",
                "model": "NOT_EXECUTED",
                "configuration": {"execution_authorized": False},
                "case_id": case_id,
                "output_sha256": empty_output_hash,
                "execution_timestamp": None,
                "contract_runtime_observable_result": "NOT_EXECUTED",
                "no_hidden_reasoning_stored": True,
            },
        },
        "annotation": {
            "raw_output_sha256": empty_output_hash,
            "state": "NOT_STARTED",
            "evidence_discipline": [],
            "semantic_sparsity": [],
            "impact_discipline": [],
            "human_burden": [],
        },
        "disagreement_states": ["NONE"],
        "post_hoc_reviews": [],
        "model_result": "NOT_EXECUTED",
    }


def build_seal(case_dir: Path, protocol_path: Path) -> dict[str, Any]:
    case_id = case_dir.name
    if case_id not in CASE_IDS:
        raise TrueHoldoutSealError(f"unexpected case identifier: {case_id}")
    payloads = case_payloads(case_dir)
    validate_pre_execution_artifacts(case_id, payloads)
    hashes = {name: seal_payload(value) for name, value in payloads.items()}
    protocol = load_protocol(protocol_path)
    record = pre_execution_governance_record(case_id, hashes)
    assessment = assess_record(record, protocol, payloads)
    if assessment.eligibility != "ELIGIBILITY_UNKNOWN":
        raise TrueHoldoutSealError("pre-execution eligibility must remain unknown")
    if assessment.contamination_reasons:
        raise TrueHoldoutSealError("known contamination detected")
    return {
        "artifact_type": "TRUE_HOLDOUT_PRE_EXECUTION_SEAL",
        "seal_version": "portable_mira.true_holdout_seal.v0.1",
        "case_id": case_id,
        "algorithm": "SHA-256",
        "canonicalization": "UTF-8 JSON; sorted keys; separators comma/colon; one LF",
        "hashes": hashes,
        "baseline_bindings": {
            "architecture_baseline": ARCHITECTURE_BASELINE,
            "evaluation_baseline": EVALUATION_BASELINE,
            "governance_baseline": GOVERNANCE_BASELINE,
            "output_annotator_baseline": OUTPUT_ANNOTATOR_BASELINE,
            "anthropic_annotator_checkpoint": ARCHITECTURE_BASELINE,
        },
        "sealed_before_model_execution": True,
        "model_execution_count": 0,
        "execution_authorized": False,
        "available_evidence_contamination_check": "NO_KNOWN_CONTAMINATION",
        "global_novelty": "NOT_PROVEN",
        "governance_assessment": assessment.to_dict(),
    }


def write_seal(case_dir: Path, protocol_path: Path) -> dict[str, Any]:
    seal = build_seal(case_dir, protocol_path)
    write_canonical_json(case_dir / "seal.json", seal)
    return copy.deepcopy(seal)


def verify_seal(case_dir: Path, protocol_path: Path) -> dict[str, Any]:
    recorded = load_json(case_dir / "seal.json")
    expected = build_seal(case_dir, protocol_path)
    if canonical_json_bytes(recorded) != canonical_json_bytes(expected):
        raise TrueHoldoutSealError(f"seal mismatch or mutation detected: {case_dir.name}")
    return copy.deepcopy(recorded)


def assess_from_seal(case_dir: Path, protocol_path: Path) -> GovernanceAssessment:
    seal = verify_seal(case_dir, protocol_path)
    payloads = case_payloads(case_dir)
    record = pre_execution_governance_record(case_dir.name, seal["hashes"])
    return assess_record(record, load_protocol(protocol_path), payloads)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    cases_root = root / "evals" / "holdout" / "cases"
    protocol = root / "evals" / "holdout" / "annotation_governance_protocol.json"
    for identifier in CASE_IDS:
        result = write_seal(cases_root / identifier, protocol)
        print(identifier, result["governance_assessment"]["eligibility"])
