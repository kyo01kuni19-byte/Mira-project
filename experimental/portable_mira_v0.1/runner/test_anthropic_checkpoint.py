from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from anthropic_checkpoint import DECISION_ID, HASHES, build_human_decision


ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = (
    ROOT
    / "evals"
    / "output_annotation"
    / "ANTHROPIC-LIVE-DEV-003-HUMAN-DECISION.json"
)
MANIFEST_PATH = ROOT / "ANTHROPIC_OUTPUT_ANNOTATOR_CHECKPOINT_CANDIDATE_v0.1.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cp1_source_evidence_is_immutable():
    assert sha256(
        ROOT / "evals" / "output_annotation" / "ANTHROPIC-LIVE-DEV-003.json"
    ) == HASHES["dev003"]
    assert sha256(
        ROOT
        / "evals"
        / "output_annotation"
        / "ANTHROPIC-LIVE-DEV-003-DISAGREEMENT-REVIEW.json"
    ) == HASHES["review"]


def test_cp2_human_decision_references_without_embedding_annotation():
    decision = build_human_decision(ROOT)
    assert decision["decision_id"] == DECISION_ID
    serialized = json.dumps(decision, sort_keys=True)
    assert "raw_provider_annotation" not in serialized
    assert "validated_annotation" not in serialized


def test_cp3_human_decisions_match_authorized_bounded_form():
    decisions = build_human_decision(ROOT)["human_decisions"]
    assert decisions["A_human_escalation"]["classification"] == (
        "HUMAN_BURDEN_INFLATION_CANDIDATE"
    )
    assert decisions["B_secondary_dimensions"]["selected_option"] == "OPTION_2"
    entity = decisions["C_entity_impact"]
    assert entity["case_classifications"]["ai_agent"] == "OPERATIONALLY_AFFECTED"
    assert entity["future_non_human_entity_possible"] is True


def test_cp4_evidence_chain_preserves_all_layers():
    layers = [layer["layer"] for layer in build_human_decision(ROOT)["evidence_chain"]]
    assert layers == [
        "OPENAI_SEMANTIC_AGENT_OUTPUT",
        "PRESERVED_CALL4_OBSERVABLE_EVIDENCE",
        "CLAUDE_BLIND_OUTPUT_ANNOTATION",
        "CANONICAL_ANNOTATION_VALIDATION",
        "HASH_BINDING",
        "FROZEN_COUNTER_FAILURE_EVALUATION",
        "DISAGREEMENT_REVIEW",
        "HUMAN_DECISION",
    ]


def test_cp5_claims_remain_bounded():
    decision = build_human_decision(ROOT)
    controls = decision["preservation_controls"]
    assert controls["independent_ground_truth_claimed"] is False
    assert controls["general_capability_claimed"] is False
    assert "does not establish independent truth" in decision["bounded_claims"][
        "independence"
    ]


def test_cp6_manifest_preserves_checkpoint_boundary():
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    assert "EXPERIMENTAL CHECKPOINT CANDIDATE — NOT APPROVED" in text
    assert "Artifact exists" in text
    assert "General capability verified" in text
    assert "Approved capability" in text
    assert "true-holdout performance" in text


def test_cp7_inventory_excludes_unrelated_and_transient_files():
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    assert ".cursor/mcp.json" not in text
    assert "__pycache__" not in text
    assert ".pyc" not in text


def test_cp8_historical_evidence_remains_byte_identical():
    assert sha256(
        ROOT / "evals" / "output_annotation" / "ANTHROPIC-LIVE-DEV-001.json"
    ) == HASHES["dev001"]
    assert sha256(
        ROOT / "evals" / "output_annotation" / "ANTHROPIC-LIVE-DEV-002.json"
    ) == HASHES["dev002"]
    assert sha256(
        ROOT / "evals" / "output_annotation" / "ANTHROPIC-LIVE-DEV-003.json"
    ) == HASHES["dev003"]


def test_cp9_all_existing_regressions_pass():
    completed = subprocess.run(
        [sys.executable, str(ROOT / "runner" / "test_disagreement_review.py")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PASS: Anthropic disagreement review tests (DR1-DR12)" in completed.stdout


if __name__ == "__main__":
    tests = (
        test_cp1_source_evidence_is_immutable,
        test_cp2_human_decision_references_without_embedding_annotation,
        test_cp3_human_decisions_match_authorized_bounded_form,
        test_cp4_evidence_chain_preserves_all_layers,
        test_cp5_claims_remain_bounded,
        test_cp6_manifest_preserves_checkpoint_boundary,
        test_cp7_inventory_excludes_unrelated_and_transient_files,
        test_cp8_historical_evidence_remains_byte_identical,
        test_cp9_all_existing_regressions_pass,
    )
    for test in tests:
        test()
    print("PASS: Anthropic checkpoint candidate tests (CP1-CP9)")
