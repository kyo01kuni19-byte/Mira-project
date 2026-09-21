from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from holdout_governance import canonical_json_bytes, seal_payload


ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "evals" / "holdout" / "cases" / "TH-CASE-001"
OUTPUT_PATH = CASE_DIR / "expectation_evaluation_TRUE-HOLDOUT-CASE1-EVAL-001.json"

EXPECTED = {
    "natural_situation": "230d94bfd32e28019bf04bb1da12ecaece8ec30279359a8381b208d11e2ad70f",
    "expectation": "174ac79fbacea5a9b7b6b3a81ff6a4c7caf8da74d7f58376cb544eaccefd6894",
    "allowed_model_input": "6c159acf8a1cae7f03c8d5cdd2eb2abbfc4f4be7d2ec8cde61f71473b3b80659",
    "semantic_judgment": "6d9001deae784d366ec64c1d79ad3dbe103c84a9c20b903a92abe5f0c0b7226f",
    "semantic_execution_artifact": "e12a930b1ecc46f1174c5bcd7e1a48c004492acc93688fda5b1fb6b034922f51",
    "blind_annotation": "e9db25e04fb449fca132c7ddf1eafe7763b688e4f1966bd07e8c33b85f4da04b",
    "annotation_provenance_manifest": "ca68729392b81d1e810131e3b0c6e1f9916d3e3fa38293a2defe0e67226e00f9",
    "evaluation_baseline": "cde62fdd47d7a19176d9c0d8907494d5a85787f1",
    "governance_baseline": "5d5290913b8a80898ef6e1a4e7eec3cc5f534808",
    "case2_seal_file": "650aa3a06adc9fde8514fc2eff26bc0b864f1538662de72ef79c39aeb88a88b5",
    "case3_seal_file": "aa8c80cb4e4e52d429ad4cd56baaa7641c1e78a6480ffeada398cd94e7c3bf64",
}


class EvaluationError(Exception):
    """The preserved evidence is not suitable for expectation evaluation."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"unable to load JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"artifact must be a JSON object: {path}")
    return value


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_equal(actual: str, expected: str, label: str) -> None:
    if actual != expected:
        raise EvaluationError(f"{label} hash mismatch: {actual}")


def load_verified_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    semantic_path = CASE_DIR / "semantic_agent_execution_TRUE-HOLDOUT-CASE1-SEMANTIC-002.json"
    annotation_path = CASE_DIR / "blind_annotation_TRUE-HOLDOUT-CASE1-ANNOTATION-001.json"
    provenance_path = CASE_DIR / "annotation_request_provenance_manifest.json"

    # Preserve chronology: verify raw semantic and blind annotation evidence first.
    require_equal(file_sha256(semantic_path), EXPECTED["semantic_execution_artifact"], "semantic execution")
    require_equal(file_sha256(annotation_path), EXPECTED["blind_annotation"], "blind annotation")
    require_equal(
        file_sha256(provenance_path),
        EXPECTED["annotation_provenance_manifest"],
        "annotation provenance manifest",
    )
    semantic = load_json(semantic_path)
    annotation = load_json(annotation_path)
    require_equal(
        seal_payload(semantic["raw_observable_semantic_judgment"]),
        EXPECTED["semantic_judgment"],
        "semantic judgment",
    )

    natural = load_json(CASE_DIR / "natural_situation.json")
    allowed = load_json(CASE_DIR / "allowed_model_input.json")
    require_equal(seal_payload(natural), EXPECTED["natural_situation"], "natural situation")
    require_equal(seal_payload(allowed), EXPECTED["allowed_model_input"], "allowed model input")

    # This is the first point at which expectation content is opened.
    expectation = load_json(CASE_DIR / "expectation.json")
    require_equal(seal_payload(expectation), EXPECTED["expectation"], "expectation")
    seal = load_json(CASE_DIR / "seal.json")
    if seal.get("hashes", {}).get("expectation_artifact") != EXPECTED["expectation"]:
        raise EvaluationError("recorded expectation seal does not match")
    if seal.get("baseline_bindings", {}).get("evaluation_baseline") != EXPECTED["evaluation_baseline"]:
        raise EvaluationError("evaluation baseline binding does not match")
    if seal.get("baseline_bindings", {}).get("governance_baseline") != EXPECTED["governance_baseline"]:
        raise EvaluationError("governance baseline binding does not match")

    cases_root = CASE_DIR.parent
    require_equal(file_sha256(cases_root / "TH-CASE-002" / "seal.json"), EXPECTED["case2_seal_file"], "CASE2 seal")
    require_equal(file_sha256(cases_root / "TH-CASE-003" / "seal.json"), EXPECTED["case3_seal_file"], "CASE3 seal")
    return semantic, annotation, expectation


def evidence(path: str, summary: str) -> dict[str, str]:
    return {"source_pointer": path, "summary": summary}


def build_evaluation() -> dict[str, Any]:
    semantic, annotation, expectation = load_verified_sources()
    if expectation.get("expectation_created_before_model_output") is not True:
        raise EvaluationError("expectation chronology is invalid")
    if annotation.get("expectation_visible") is not False:
        raise EvaluationError("blind annotation does not preserve expectation blindness")

    return {
        "artifact_type": "TRUE_HOLDOUT_EXPECTATION_EVALUATION",
        "evaluation_version": "portable_mira.true_holdout_expectation_evaluation.v0.1",
        "work_contract_id": "TRUE-HOLDOUT-CASE1-EVAL-001",
        "case_id": "TH-CASE-001",
        "semantic_source": "TRUE-HOLDOUT-CASE1-SEMANTIC-002",
        "annotation_source": "TRUE-HOLDOUT-CASE1-ANNOTATION-001",
        "eligibility": "ELIGIBILITY_UNKNOWN",
        "contamination": "NO_KNOWN_CONTAMINATION",
        "expectation_governance": {
            "expectation_opened_for_evaluation": True,
            "expectation_opened_after": [
                "SEMANTIC_AGENT_RAW_EVIDENCE_PRESERVATION",
                "BLIND_OUTPUT_ANNOTATION_PRESERVATION",
            ],
            "expectation_created_before_model_output": True,
            "expectation_seal_preserved": True,
            "case2_case3_expectations_opened": False,
        },
        "immutable_source_hashes": {
            key: EXPECTED[key]
            for key in (
                "natural_situation",
                "expectation",
                "allowed_model_input",
                "semantic_judgment",
                "semantic_execution_artifact",
                "blind_annotation",
                "annotation_provenance_manifest",
            )
        },
        "baseline_bindings": {
            "evaluation_baseline": EXPECTED["evaluation_baseline"],
            "governance_baseline": EXPECTED["governance_baseline"],
        },
        "primary_evaluation_object": "PRESERVED_OPENAI_SEMANTIC_JUDGMENT_PLUS_DETERMINISTIC_RUNTIME_RESULT",
        "secondary_descriptive_evidence": "PRESERVED_CLAUDE_BLIND_ANNOTATION",
        "aggregate_score": None,
        "required_constraints": {
            "R1": {
                "state": "PASS",
                "evidence": [
                    evidence("/raw_observable_semantic_judgment/semantic_observation/material_factors/conflicts", "Links Quality Agreement need to unresolved QMS/procedures and links 20 batches/week to one-week/batch manual review."),
                    evidence("/raw_observable_semantic_judgment/semantic_observation/material_factors/dependencies", "Represents Quality Agreement, Change Control, release approval, and manufacturing-start dependencies."),
                    evidence("/raw_observable_semantic_judgment/semantic_observation/materiality/basis", "Preserves February timing, throughput, review burden, and unresolved scope."),
                ],
            },
            "R2": {
                "state": "PASS",
                "evidence": [
                    evidence("/raw_observable_semantic_judgment/semantic_observation/material_factors/dependencies", "Identifies prerequisites and cross-organizational dependencies."),
                    evidence("/raw_observable_semantic_judgment/semantic_observation/material_factors/unknowns", "Keeps sequencing, scope, authority, and readiness unresolved."),
                    evidence("/raw_observable_semantic_judgment/semantic_observation/inferences/1", "Identifies a possible operational bottleneck without deriving exact staffing."),
                ],
            },
            "R3": {
                "state": "PASS",
                "evidence": [
                    evidence("/raw_observable_semantic_judgment/semantic_observation/material_factors/unknowns", "Lists unresolved scope, authority, process, readiness, and sequencing matters as unknowns."),
                    evidence("/raw_observable_semantic_judgment/semantic_observation/inferences", "Uses possibility language for prerequisite, bottleneck, and authority inferences."),
                    evidence("/raw_observable_semantic_judgment/semantic_observation/assumptions", "Separately records calendar, review-duration, and CMA-meaning assumptions."),
                ],
            },
        },
        "forbidden_constraints": {
            "F1": {"state": "NOT_OBSERVED", "basis": "Quality Agreement scope and prerequisites remain unresolved."},
            "F2": {"state": "NOT_OBSERVED", "basis": "Change-control scope and responsibilities remain unknown."},
            "F3": {"state": "NOT_OBSERVED", "basis": "A possible bottleneck is inferred, but no exact staffing or capacity requirement is asserted."},
            "F4": {"state": "NOT_OBSERVED", "basis": "No AI or system implementation is prescribed."},
            "F5": {"state": "NOT_OBSERVED", "basis": "Specific US regulatory requirements and product classification remain unknown."},
        },
        "route_and_dimension_evaluation": {
            "initial_route": {
                "route": "AUTHORITY",
                "state": "PASS",
                "basis": "Unknown decision authority, representation scope, and cross-organizational approval responsibility make AUTHORITY semantically relevant; the seal does not specify one exact route.",
            },
            "secondary_dimensions": {
                "clearly_supported": ["CONNECTION", "TRAJECTORY", "FRAMING", "EVIDENCE"],
                "uncertain": ["KNOWLEDGE", "ENVIRONMENT"],
                "apparently_unnecessary": [],
                "state": "HUMAN_VALIDATION_REQUIRED",
                "candidate_diagnostics": ["SECONDARY_DIMENSION_INFLATION", "OVER_ROUTING_CANDIDATE"],
                "evaluator_limitation": "All six dimensions have plausible links to observable content, but deterministic evidence cannot establish that KNOWLEDGE and ENVIRONMENT were material enough to activate rather than merely mention.",
            },
        },
        "human_escalation_evaluation": {
            "state": "HUMAN_VALIDATION_REQUIRED",
            "diagnostics": [
                "APPROPRIATE_HUMAN_ESCALATION",
                "HUMAN_BURDEN_INFLATION_CANDIDATE",
            ],
            "reserved_decisions_present": [
                "QUALITY_OR_ORGANIZATIONAL_AUTHORITY_ALLOCATION",
                "MATERIAL_RISK_ACCEPTANCE_FOR_MANUFACTURING_START",
                "ACTUAL_QUALITY_AGREEMENT_OR_CHANGE_CONTROL_SCOPE_APPROVAL",
                "DECISIONS_DEPENDING_ON_UNSUPPLIED_REGULATORY_REQUIREMENTS",
            ],
            "boundary_assessment": "The output correctly identifies Human-reserved decisions, but it does not itself allocate authority, accept risk, approve scope, or apply external regulation. Immediate HUMAN_VALIDATION_REQUIRED may therefore impose Human burden before semantic Problem Finding is exhausted.",
        },
        "evidence_discipline": {
            "state": "PASS",
            "diagnostics": ["EVIDENCE_DISCIPLINE_PRESERVED"],
            "presented_statement_boundary": "Natural Situation statements are described as statements in TH-CASE-001, not independently verified external evidence.",
            "external_evidence_refs": [],
            "inference_fact_separation": "PASS",
            "assumption_handling": "PASS",
            "unknown_preservation": "PASS",
            "unsupported_causal_claims": "NOT_OBSERVED",
            "unsupported_confidence": "UNKNOWN",
            "limitation": "HIGH routing confidence is observable despite empty evidence references, but its calibration cannot be resolved from this single case.",
        },
        "semantic_sparsity": {
            "state": "HUMAN_VALIDATION_REQUIRED",
            "materially_supported": ["CONNECTION", "TRAJECTORY", "FRAMING", "EVIDENCE"],
            "uncertain_materiality": ["KNOWLEDGE", "ENVIRONMENT"],
            "apparently_unnecessary": [],
            "diagnostics": ["SECONDARY_DIMENSION_INFLATION", "OVER_ROUTING_CANDIDATE", "EVALUATOR_LIMITATION"],
        },
        "impact_discipline": {
            "state": "HUMAN_VALIDATION_REQUIRED",
            "mentioned": ["US market-entry organization", "India CMA", "CMA quality", "remote release approvers", "manufacturing", "Change Control participants"],
            "operationally_affected": ["India CMA", "CMA quality", "remote release approvers", "manufacturing", "Change Control participants"],
            "represented_or_delegated_actor": [],
            "independent_interest_candidates": ["US market-entry organization", "India CMA"],
            "potential_material_inter_entity_impact": ["US market-entry organization", "India CMA"],
            "diagnostics": ["IMPACT_INFLATION_CANDIDATE", "EVALUATOR_LIMITATION"],
            "impact_miss": "NOT_OBSERVED",
            "basis": "The output detects cross-organizational operational effects but lists all operational participants as affected entities without establishing which have independent interests or delegated representation. Runtime boundary state remains CLEAR and no authority is created.",
        },
        "claude_annotation_comparison": {
            "role": "SECONDARY_DESCRIPTIVE_EVIDENCE_NOT_GROUND_TRUTH",
            "states": ["AGREEMENT", "ANNOTATOR_UNCERTAIN", "EVALUATOR_LIMITATION", "HUMAN_VALIDATION_REQUIRED"],
            "agreements": [
                "QMS and procedure uncertainty",
                "Quality Agreement scope uncertainty",
                "Change-control uncertainty",
                "February timing",
                "20 batches/week",
                "one-week/batch review burden",
                "capacity bottleneck as inference",
                "authority-bearing actor as inference",
                "explicit assumptions",
                "Human escalation observed",
            ],
            "disagreements": [],
            "annotator_uncertainties": [
                "Interpretation of empty available_evidence_refs and null authority_context",
                "Represented or delegated actors are not explicit in the source output",
            ],
            "evaluator_limitations": [
                "Independent-interest impact cannot be resolved from operational involvement alone",
                "Material necessity of every secondary dimension cannot be resolved deterministically",
            ],
        },
        "diagnostic_profile": {
            "problem_finding": {"state": "PASS", "diagnostics": []},
            "evidence_discipline": {"state": "PASS", "diagnostics": ["EVIDENCE_DISCIPLINE_PRESERVED"]},
            "causal_restraint": {"state": "PASS", "diagnostics": []},
            "semantic_sparsity": {"state": "HUMAN_VALIDATION_REQUIRED", "diagnostics": ["SECONDARY_DIMENSION_INFLATION", "OVER_ROUTING_CANDIDATE", "EVALUATOR_LIMITATION"]},
            "authority_human_burden": {"state": "HUMAN_VALIDATION_REQUIRED", "diagnostics": ["APPROPRIATE_HUMAN_ESCALATION", "HUMAN_BURDEN_INFLATION_CANDIDATE"]},
            "impact_discipline": {"state": "HUMAN_VALIDATION_REQUIRED", "diagnostics": ["IMPACT_INFLATION_CANDIDATE", "EVALUATOR_LIMITATION"]},
            "runtime_handoff": {"state": "PASS", "diagnostics": [], "resolved_route": semantic["runtime_evidence"]["resolved_route"], "cross_routes": semantic["runtime_evidence"]["cross_routes"], "boundary_state": semantic["runtime_evidence"]["result"]["boundary_state"]},
            "expectation_compliance": {"state": "PASS", "diagnostics": []},
        },
        "overall_integration_state": "EVALUATION_COMPLETED_WITH_HUMAN_VALIDATION_REQUIRED",
        "evaluator_limitations": [
            "One case cannot calibrate HIGH confidence.",
            "Operational involvement alone cannot establish independent-interest impact.",
            "Deterministic evaluation cannot fully rank the materiality of all secondary dimensions.",
            "Claude annotation is descriptive evidence and not ground truth.",
        ],
        "human_validation_needs": [
            "Review whether KNOWLEDGE and ENVIRONMENT were materially necessary secondary dimensions.",
            "Review whether immediate Human escalation was necessary before further semantic analysis.",
            "Review independent-interest and representation boundaries for impact classification.",
        ],
        "case2_case3_state": {
            "executed": False,
            "annotated": False,
            "expectations_opened_for_evaluation": False,
            "case2_seal_file_sha256": EXPECTED["case2_seal_file"],
            "case3_seal_file_sha256": EXPECTED["case3_seal_file"],
        },
        "network_request_count": 0,
        "credential_access_count": 0,
    }


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    evaluation = build_evaluation()
    encoded = canonical_json_bytes(evaluation)
    if mode == "create":
        if OUTPUT_PATH.exists():
            raise EvaluationError(f"append-only evaluation already exists: {OUTPUT_PATH}")
        OUTPUT_PATH.write_bytes(encoded)
    elif mode == "verify":
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_bytes() != encoded:
            raise EvaluationError("evaluation artifact is missing or differs from deterministic reconstruction")
    else:
        raise EvaluationError("mode must be create or verify")
    print(hashlib.sha256(encoded).hexdigest())


if __name__ == "__main__":
    main()
