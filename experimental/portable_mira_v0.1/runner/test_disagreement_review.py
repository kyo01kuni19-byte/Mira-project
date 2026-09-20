from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from disagreement_review import (
    COUNTER_FAILURE_CASES_SHA256,
    REVIEW_ID,
    SOURCE_SHA256,
    build_review,
    validate_review,
    write_review,
)
from output_annotator import payload_sha256


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = (
    EXPERIMENT_ROOT
    / "evals"
    / "output_annotation"
    / "ANTHROPIC-LIVE-DEV-003.json"
)
REVIEW_PATH = (
    EXPERIMENT_ROOT
    / "evals"
    / "output_annotation"
    / "ANTHROPIC-LIVE-DEV-003-DISAGREEMENT-REVIEW.json"
)
CASES_PATH = (
    EXPERIMENT_ROOT / "evals" / "counter_failure" / "counter_failure_cases.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def issues() -> dict[str, dict[str, Any]]:
    return {issue["issue_id"]: issue for issue in build_review(EXPERIMENT_ROOT)["issues"]}


def test_dr1_dev003_historical_evidence_remains_byte_identical():
    assert sha256(SOURCE_PATH) == SOURCE_SHA256


def test_dr2_review_references_source_instead_of_replacing_it():
    review = build_review(EXPERIMENT_ROOT)
    assert review["review_id"] == REVIEW_ID
    assert review["source_hash"] == SOURCE_SHA256
    assert "raw_provider_annotation" not in review
    assert "validated_annotation" not in review


def test_dr3_claude_annotation_remains_unchanged():
    before = SOURCE_PATH.read_bytes()
    review = write_review(EXPERIMENT_ROOT, REVIEW_PATH)
    assert SOURCE_PATH.read_bytes() == before
    source = json.loads(before)
    assert payload_sha256(source["raw_provider_annotation"]) == review[
        "raw_annotation_hash"
    ]


def test_dr4_disagreement_does_not_automatically_equal_annotator_fail():
    review = validate_review(build_review(EXPERIMENT_ROOT))
    assert review["review_status"] == "HUMAN_VALIDATION_REQUIRED"
    assert all(issue["state"] != "FAIL" for issue in review["issues"])


def test_dr5_escalation_inflation_candidate_does_not_change_authority():
    issue = issues()["DRC1_HUMAN_ESCALATION"]
    assert issue["review_interpretation"] == "HUMAN_BURDEN_INFLATION_CANDIDATE"
    assert build_review(EXPERIMENT_ROOT)["preservation_controls"][
        "authority_state_modified"
    ] is False


def test_dr6_description_is_separate_from_registered_dimension_evaluation():
    issue = issues()["DRC2_SECONDARY_DIMENSION_INTERPRETATION"]
    assert issue["state"] == "EVALUATOR_LIMITATION"
    assert issue["review_interpretation"].startswith("OPTION_2_")
    roles = build_review(EXPERIMENT_ROOT)["role_boundary_learning"]
    assert roles["output_annotator"] == "DESCRIBES_OBSERVABLE_SEMANTIC_STRUCTURE"
    assert roles["annotator_executes_routes"] is False


def test_dr7_contextual_objects_are_not_automatic_independent_interests():
    issue = issues()["DRC3_ENTITY_IMPACT_CLASSIFICATION"]
    assert issue["review_interpretation"] == (
        "CONTEXTUAL_OBJECTS_ARE_NOT_AUTOMATIC_INDEPENDENT_INTEREST_ENTITIES"
    )
    assert "contextual objects" in issue["rationale"]


def test_dr8_future_non_human_independent_interest_remains_representable():
    controls = build_review(EXPERIMENT_ROOT)["preservation_controls"]
    assert controls["future_non_human_independent_interest_representable"] is True
    assert "may still qualify" in issues()["DRC3_ENTITY_IMPACT_CLASSIFICATION"][
        "rationale"
    ]


def test_dr9_review_cannot_modify_frozen_evaluator_criteria():
    before = CASES_PATH.read_bytes()
    write_review(EXPERIMENT_ROOT, REVIEW_PATH)
    assert CASES_PATH.read_bytes() == before
    assert sha256(CASES_PATH) == COUNTER_FAILURE_CASES_SHA256
    assert build_review(EXPERIMENT_ROOT)["preservation_controls"][
        "frozen_evaluator_criteria_modified"
    ] is False


def test_dr10_review_cannot_change_holdout_eligibility_or_authority():
    controls = build_review(EXPERIMENT_ROOT)["preservation_controls"]
    assert controls["holdout_eligibility_modified"] is False
    assert controls["authority_state_modified"] is False
    assert "not independent ground truth or holdout evidence" in build_review(
        EXPERIMENT_ROOT
    )["evidence_claim"]


def test_dr11_no_aggregate_score_is_introduced():
    review = build_review(EXPERIMENT_ROOT)
    serialized = json.dumps(review, sort_keys=True)
    for forbidden in ('"score"', '"quality_score"', '"aggregate_score"'):
        assert forbidden not in serialized
    assert review["preservation_controls"]["aggregate_quality_score_present"] is False


def test_dr12_all_existing_regressions_pass():
    completed = subprocess.run(
        [
            sys.executable,
            str(EXPERIMENT_ROOT / "runner" / "test_anthropic_output_budget.py"),
        ],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PASS: Anthropic output budget tests (OB1-OB12)" in completed.stdout


if __name__ == "__main__":
    tests = (
        test_dr1_dev003_historical_evidence_remains_byte_identical,
        test_dr2_review_references_source_instead_of_replacing_it,
        test_dr3_claude_annotation_remains_unchanged,
        test_dr4_disagreement_does_not_automatically_equal_annotator_fail,
        test_dr5_escalation_inflation_candidate_does_not_change_authority,
        test_dr6_description_is_separate_from_registered_dimension_evaluation,
        test_dr7_contextual_objects_are_not_automatic_independent_interests,
        test_dr8_future_non_human_independent_interest_remains_representable,
        test_dr9_review_cannot_modify_frozen_evaluator_criteria,
        test_dr10_review_cannot_change_holdout_eligibility_or_authority,
        test_dr11_no_aggregate_score_is_introduced,
        test_dr12_all_existing_regressions_pass,
    )
    for test in tests:
        test()
    print("PASS: Anthropic disagreement review tests (DR1-DR12)")
