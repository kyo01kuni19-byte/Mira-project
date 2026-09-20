from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

from output_annotator import canonical_json_bytes


DECISION_ID = "ANTHROPIC-LIVE-DEV-003-HUMAN-DECISION"
HASHES = {
    "call4": "63789644d8d06e00ea7a7d2b89631b4d86e79fe41df68f74e296a5c45d26a0c3",
    "dev001": "cb6287853ab92fc801e6e89f85f9618566b74197211d201095991a99ac6d64fa",
    "dev002": "225e0fbfb72bd03006b0a51055648fb87b0c1df7b5b65fd3a347c288a6c87942",
    "dev003": "c4dd0ad52d67b58aa6a68d3692327477a9867e27c17ff9f350cb850d44af2605",
    "raw_annotation": "55739d4596f1715bc65cc91289db5505151f7a9642119d24a464c2daf870e905",
    "raw_annotation_text": "823393dc624b1220ed997a64c50fe447e2133e4eac3021f3fb9be7909943c956",
    "review": "008157cb740de9ecc2f371524bd4cf0b36ffc646ff74b26cdde5d78ab4a8fc49",
    "budget_analysis": "18ace596070c5c5a5eb5aae03aeb710b2a07512f9b47a06c04a7aef71579a23c",
    "governance": "2504bdc8bd46202b8ae3e9a18728666523eac3297284dee7ce72e0bf3c3f86f1",
    "counter_failure_cases": "b18dada362ce77c3819b80f44236aa6810ce350ad24579280a6ab5043bab5f7a",
    "canonical_schema": "7f5a606cb2f347b854f1f85085427beb0c5e75053b8af6f952bccaf8d8cd7b1d",
    "provider_artifact": "0c26c4d6ba03d722e2588d46ddfdfe376bc68e2c197b6a60deb13b8b615ea2d7",
}


class AnthropicCheckpointError(Exception):
    pass


def build_human_decision(experiment_root: Path) -> dict[str, Any]:
    paths = {
        "call4": experiment_root
        / "evals"
        / "semantic_judgment"
        / "LIVE-SJ-001-CALL-4.json",
        "dev001": experiment_root
        / "evals"
        / "output_annotation"
        / "ANTHROPIC-LIVE-DEV-001.json",
        "dev002": experiment_root
        / "evals"
        / "output_annotation"
        / "ANTHROPIC-LIVE-DEV-002.json",
        "dev003": experiment_root
        / "evals"
        / "output_annotation"
        / "ANTHROPIC-LIVE-DEV-003.json",
        "review": experiment_root
        / "evals"
        / "output_annotation"
        / "ANTHROPIC-LIVE-DEV-003-DISAGREEMENT-REVIEW.json",
        "budget_analysis": experiment_root
        / "evals"
        / "output_annotation"
        / "ANTHROPIC-OUTPUT-BUDGET-001.json",
        "governance": experiment_root
        / "evals"
        / "holdout"
        / "annotation_governance_protocol.json",
        "counter_failure_cases": experiment_root
        / "evals"
        / "counter_failure"
        / "counter_failure_cases.json",
        "canonical_schema": experiment_root
        / "semantic"
        / "output_annotation_contract.schema.json",
        "provider_artifact": experiment_root
        / "generated"
        / "anthropic_output_annotation_provider_schema.json",
    }
    for name, path in paths.items():
        if _file_sha256(path) != HASHES[name]:
            raise AnthropicCheckpointError(f"checkpoint source changed: {name}")

    decision = {
        "artifact_type": "ANTHROPIC_OUTPUT_ANNOTATOR_HUMAN_DECISION",
        "decision_id": DECISION_ID,
        "work_contract_id": "ANTHROPIC-CHECKPOINT-001",
        "status": "HUMAN_DECISION_RECORDED",
        "source_references": {
            "dev003": {
                "path": "evals/output_annotation/ANTHROPIC-LIVE-DEV-003.json",
                "sha256": HASHES["dev003"],
                "raw_annotation_sha256": HASHES["raw_annotation"],
                "raw_annotation_text_sha256": HASHES["raw_annotation_text"],
            },
            "disagreement_review": {
                "path": (
                    "evals/output_annotation/"
                    "ANTHROPIC-LIVE-DEV-003-DISAGREEMENT-REVIEW.json"
                ),
                "sha256": HASHES["review"],
            },
            "governance_baseline": {
                "path": "evals/holdout/annotation_governance_protocol.json",
                "sha256": HASHES["governance"],
                "commit": "5d5290913b8a80898ef6e1a4e7eec3cc5f534808",
            },
            "counter_failure_baseline": {
                "path": "evals/counter_failure/counter_failure_cases.json",
                "sha256": HASHES["counter_failure_cases"],
                "commit": "cde62fdd47d7a19176d9c0d8907494d5a85787f1",
                "case_id": "CALL4_RESIDUAL",
            },
        },
        "human_decisions": {
            "A_human_escalation": {
                "classification": "HUMAN_BURDEN_INFLATION_CANDIDATE",
                "decision": (
                    "Routing, trigger candidates, and absence of execution authorization "
                    "do not by themselves establish that Human escalation is required."
                ),
                "analysis_without_execution_authority": (
                    "Analysis or observation that neither executes nor authorizes an "
                    "action does not require execution authorization merely because "
                    "execution authority is absent."
                ),
                "human_escalation_may_still_be_required_when": [
                    "an Authority-sensitive action or decision is proposed or reached",
                    "a normative decision reserved to Human is reached",
                    "another existing boundary explicitly requires Human decision",
                ],
                "forbidden_generalization": (
                    "absence of authority never requires escalation"
                ),
                "authority_semantics_modified": False,
            },
            "B_secondary_dimensions": {
                "selected_option": "OPTION_2",
                "output_annotator_responsibility": (
                    "describe observable semantic structure"
                ),
                "descriptive_examples": [
                    "causal attribution",
                    "evidence sufficiency",
                    "environment comparison",
                    "workflow impact",
                ],
                "registered_dimension_mapping_owner": (
                    "OUTSIDE_OUTPUT_ANNOTATOR_ROLE"
                ),
                "registered_dimension_examples": [
                    "FRAMING",
                    "EVIDENCE",
                    "ENVIRONMENT",
                ],
                "evaluator_limitation": (
                    "The current deterministic evaluator does not fully consume "
                    "descriptive annotation into registered-dimension mapping."
                ),
                "first_holdout_poc_limitation_accepted": True,
                "silently_resolved": False,
            },
            "C_entity_impact": {
                "case_classifications": {
                    "environment": "CONTEXTUAL_OR_OPERATIONAL_OBJECT",
                    "generated_file": "CONTEXTUAL_OR_OPERATIONAL_OBJECT",
                    "team": "INDEPENDENTLY_REPRESENTABLE_AFFECTED_RECIPIENT",
                    "future_workflow_participants": (
                        "INDEPENDENTLY_REPRESENTABLE_IMPACT_CANDIDATE"
                    ),
                    "ai_agent": "OPERATIONALLY_AFFECTED",
                },
                "not_established_for_ai_agent": [
                    "INDEPENDENT_INTEREST_CANDIDATE",
                    "MATERIAL_INTER_ENTITY_IMPACT_RECIPIENT",
                ],
                "forbidden_generalization": "AI can never be an Entity",
                "future_non_human_entity_possible": True,
                "qualification_basis": (
                    "independent Value, agency, or viability interests plus material-"
                    "impact evidence"
                ),
            },
        },
        "evidence_chain": [
            {
                "layer": "OPENAI_SEMANTIC_AGENT_OUTPUT",
                "ref": "evals/semantic_judgment/LIVE-SJ-001-CALL-4.json",
                "sha256": HASHES["call4"],
                "status": "EXPERIMENTAL_LIVE_DEVELOPMENT_EVIDENCE",
            },
            {
                "layer": "PRESERVED_CALL4_OBSERVABLE_EVIDENCE",
                "ref": "DEV-003 source_semantic_agent_output_sha256",
                "sha256": "e51815480211712d597ea455cbb3924ec79c99778f9aebd8bfb57f45c9a5ac9f",
                "status": "HASH_BOUND_PRESERVED_SUBSET",
            },
            {
                "layer": "CLAUDE_BLIND_OUTPUT_ANNOTATION",
                "ref": "ANTHROPIC-LIVE-DEV-003 raw annotation",
                "sha256": HASHES["raw_annotation"],
                "status": "ONE_CASE_DEVELOPMENT_EVIDENCE",
            },
            {
                "layer": "CANONICAL_ANNOTATION_VALIDATION",
                "ref": "ANTHROPIC-LIVE-DEV-003 canonical_annotation_validation",
                "sha256": HASHES["canonical_schema"],
                "status": "PASS_TESTED_SCOPE",
            },
            {
                "layer": "HASH_BINDING",
                "ref": "ANTHROPIC-LIVE-DEV-003 hash_binding",
                "sha256": HASHES["dev003"],
                "status": "PASS_TESTED_SCOPE",
            },
            {
                "layer": "FROZEN_COUNTER_FAILURE_EVALUATION",
                "ref": "CALL4_RESIDUAL",
                "sha256": HASHES["counter_failure_cases"],
                "status": "PASS_INDEPENDENT_FROZEN_EVALUATION",
            },
            {
                "layer": "DISAGREEMENT_REVIEW",
                "ref": (
                    "evals/output_annotation/"
                    "ANTHROPIC-LIVE-DEV-003-DISAGREEMENT-REVIEW.json"
                ),
                "sha256": HASHES["review"],
                "status": "HUMAN_VALIDATION_REQUIRED_REVIEW_COMPLETED",
            },
            {
                "layer": "HUMAN_DECISION",
                "ref": DECISION_ID,
                "sha256": None,
                "status": "RECORDED_WITHOUT_RETROACTIVE_REWRITE",
            },
        ],
        "bounded_claims": {
            "provider_integration": (
                "Local compatibility, authenticated live generation, structured-output "
                "completion, canonical validation, and hash binding are evidenced for "
                "the tested development configuration."
            ),
            "blind_annotation": (
                "One development case evidences expectation-blind different-provider "
                "canonical annotation from preserved Semantic Agent output."
            ),
            "review_flow": (
                "One development case traversed blind annotation, frozen evaluation, "
                "disagreement review, and Human decision without source rewrite."
            ),
            "independence": (
                "Different provider may reduce direct coupling but does not establish "
                "independent truth or unbiased annotation."
            ),
        },
        "preservation_controls": {
            "prior_layers_modified": False,
            "authority_semantics_modified": False,
            "frozen_evaluator_modified": False,
            "holdout_created": False,
            "independent_ground_truth_claimed": False,
            "general_capability_claimed": False,
        },
    }
    validate_human_decision(decision)
    return decision


def validate_human_decision(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AnthropicCheckpointError("Human decision must be an object")
    if value.get("decision_id") != DECISION_ID:
        raise AnthropicCheckpointError("unexpected Human decision id")
    if value.get("status") != "HUMAN_DECISION_RECORDED":
        raise AnthropicCheckpointError("Human decision status is invalid")
    layers = value.get("evidence_chain")
    expected_layers = [
        "OPENAI_SEMANTIC_AGENT_OUTPUT",
        "PRESERVED_CALL4_OBSERVABLE_EVIDENCE",
        "CLAUDE_BLIND_OUTPUT_ANNOTATION",
        "CANONICAL_ANNOTATION_VALIDATION",
        "HASH_BINDING",
        "FROZEN_COUNTER_FAILURE_EVALUATION",
        "DISAGREEMENT_REVIEW",
        "HUMAN_DECISION",
    ]
    if not isinstance(layers, list) or [layer.get("layer") for layer in layers] != (
        expected_layers
    ):
        raise AnthropicCheckpointError("evidence chain changed")
    controls = value.get("preservation_controls")
    if not isinstance(controls, dict) or any(controls.values()):
        raise AnthropicCheckpointError("checkpoint preservation control violated")
    if "raw_provider_annotation" in value or "validated_annotation" in value:
        raise AnthropicCheckpointError("Human decision must reference annotation")
    return copy.deepcopy(value)


def write_human_decision(experiment_root: Path, path: Path) -> dict[str, Any]:
    decision = build_human_decision(experiment_root)
    content = canonical_json_bytes(decision)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    if path.read_bytes() != content:
        raise AnthropicCheckpointError("Human decision read-back mismatch")
    return decision


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    output = (
        root
        / "evals"
        / "output_annotation"
        / "ANTHROPIC-LIVE-DEV-003-HUMAN-DECISION.json"
    )
    result = write_human_decision(root, output)
    print(hashlib.sha256(canonical_json_bytes(result)).hexdigest())
