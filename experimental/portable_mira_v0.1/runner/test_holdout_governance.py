from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from holdout_governance import assess_record, load_protocol, seal_payload


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = EXPERIMENT_ROOT / "evals" / "holdout" / "annotation_governance_protocol.json"
BASELINE = "cde62fdd47d7a19176d9c0d8907494d5a85787f1"


def protocol():
    return load_protocol(PROTOCOL_PATH)


def payloads():
    return {
        "natural_situation": "Synthetic governance-test situation, not a holdout case.",
        "expectation_artifact": {
            "required": ["material uncertainty preserved"],
            "forbidden": ["unsupported certainty"],
            "acceptable_or_evidence_dependent": ["more than one route representation"],
            "human_validation_required": "UNKNOWN",
        },
        "evaluation_baseline_commit": BASELINE,
        "allowed_model_input": {
            "situation_ref": "synthetic-governance-test",
            "contract": "v0.1a",
            "registered_vocabulary_only": True,
        },
    }


def valid_record():
    sealed = payloads()
    observable_output = {
        "semantic_observation": {"materiality": "MATERIAL"},
        "routing_judgment": {"decision": "ROUTE"},
    }
    return {
        "record_type": "HOLDOUT_GOVERNANCE_RECORD",
        "case_id": "SYNTHETIC-HG-TEST",
        "case_provenance": "NEW_UNEXECUTED",
        "role_assignments": {
            "CASE_AUTHOR": ["human-a"],
            "EXPECTATION_AUTHOR": ["mira-a"],
            "SEMANTIC_AGENT": ["semantic-agent-a"],
            "OUTPUT_ANNOTATOR": ["annotator-a"],
            "DETERMINISTIC_EVALUATOR": ["codex-a"],
            "DISAGREEMENT_REVIEWER": ["reviewer-a"],
            "HUMAN_DECISION": ["human-b"],
        },
        "role_overlap_declarations": [],
        "information_exposure": {
            "semantic_agent_received": ["allowed model input", "registered vocabulary", "contract schema"],
            "output_annotator_saw_expectations_before_annotation": False,
        },
        "chronology": {
            "expectation_created_at": "2026-09-20T10:00:00Z",
            "sealed_at": "2026-09-20T10:30:00Z",
            "model_output_received_at": "2026-09-20T11:00:00Z",
        },
        "seals": {name: seal_payload(value) for name, value in sealed.items()},
        "contamination_signals": {
            "evaluator_changed_after_output": False,
            "expected_answer_in_adapter_instructions": False,
            "materially_identical_prior_execution": False,
        },
        "raw_output": {
            "observable_semantic_judgment": observable_output,
            "metadata": {
                "provider": "synthetic-local-test",
                "model": "none",
                "configuration": {"network": False},
                "case_id": "SYNTHETIC-HG-TEST",
                "output_sha256": seal_payload(observable_output),
                "execution_timestamp": "2026-09-20T11:00:00Z",
                "contract_runtime_observable_result": "PASS",
                "no_hidden_reasoning_stored": True,
            },
        },
        "annotation": {
            "raw_output_sha256": seal_payload(observable_output),
            "state": "COMPLETE",
            "evidence_discipline": ["EVIDENCE_REFERENCE", "INFERENCE", "UNKNOWN"],
            "semantic_sparsity": ["MATERIALLY_RELEVANT_DIMENSION"],
            "impact_discipline": ["OPERATIONALLY_AFFECTED"],
            "human_burden": [],
        },
        "disagreement_states": ["NONE"],
        "post_hoc_reviews": [],
        "model_result": "PASS",
    }


def assess(record=None, sealed_payloads=None):
    return assess_record(record or valid_record(), protocol(), sealed_payloads or payloads())


def test_hg1_valid_role_configuration_accepted():
    result = assess()
    assert result.eligibility == "HOLDOUT_ELIGIBLE"
    assert result.governance_state == "PASS"
    assert result.role_overlaps == ()


def test_hg2_semantic_agent_expectation_exposure_contaminates():
    record = valid_record()
    record["information_exposure"]["semantic_agent_received"].append("expected route")
    result = assess(record)
    assert result.eligibility == "CONTAMINATED"
    assert "SEMANTIC_AGENT_SAW_EXPECTATION" in result.contamination_reasons


def test_hg3_expectation_after_output_contaminates():
    record = valid_record()
    record["chronology"]["expectation_created_at"] = "2026-09-20T12:00:00Z"
    result = assess(record)
    assert "OUTPUT_INFLUENCED_EXPECTATION" in result.contamination_reasons


def test_seal_created_after_output_contaminates():
    record = valid_record()
    record["chronology"]["sealed_at"] = "2026-09-20T12:00:00Z"
    result = assess(record)
    assert "SEAL_CREATED_AFTER_OUTPUT" in result.contamination_reasons


def test_hg4_sealed_expectation_modification_detected():
    changed = payloads()
    changed["expectation_artifact"]["required"].append("post-output requirement")
    result = assess(sealed_payloads=changed)
    assert "SEALED_ARTIFACT_CHANGED" in result.contamination_reasons


def test_hg5_frozen_evaluator_baseline_mismatch_detected():
    record = valid_record()
    changed = payloads()
    changed["evaluation_baseline_commit"] = "0" * 40
    record["seals"]["evaluation_baseline_commit"] = seal_payload(
        changed["evaluation_baseline_commit"]
    )
    result = assess(record, changed)
    assert result.contamination_reasons == ("BASELINE_MISMATCH",)


def test_hg6_annotation_cannot_replace_raw_output():
    record = valid_record()
    record["annotation"]["raw_output_sha256"] = seal_payload({"replacement": True})
    result = assess(record)
    assert "SEALED_ARTIFACT_CHANGED" in result.contamination_reasons
    assert record["raw_output"]["observable_semantic_judgment"] == valid_record()["raw_output"]["observable_semantic_judgment"]


def test_hg7_annotator_uncertainty_is_representable():
    record = valid_record()
    record["annotation"]["state"] = "ANNOTATOR_UNCERTAIN"
    result = assess(record)
    assert result.eligibility == "HOLDOUT_ELIGIBLE"
    assert result.governance_state == "REVIEW_REQUIRED"
    assert "ANNOTATION_UNCERTAINTY" in result.disagreements


def test_hg8_disagreement_does_not_automatically_fail_model():
    record = valid_record()
    record["disagreement_states"] = ["EXPECTATION_OUTPUT_DISAGREEMENT"]
    result = assess(record)
    assert result.governance_state == "REVIEW_REQUIRED"
    assert result.model_result_preserved == "PASS"


def test_hg9_post_hoc_correction_preserves_original_expectation():
    record = valid_record()
    original = record["seals"]["expectation_artifact"]
    record["post_hoc_reviews"] = [{
        "review_id": "review-1",
        "original_expectation_sha256": original,
        "proposed_expectation_sha256": seal_payload({"post_hoc": "proposal"}),
        "reason": "Original expectation may have been too narrow.",
    }]
    record["disagreement_states"] = ["EXPECTATION_OUTPUT_DISAGREEMENT"]
    result = assess(record)
    assert result.governance_state == "REVIEW_REQUIRED"
    assert record["seals"]["expectation_artifact"] == original


def test_hg10_development_case_cannot_be_true_holdout():
    record = valid_record()
    record["case_provenance"] = "DEVELOPMENT_CASE"
    result = assess(record)
    assert result.eligibility == "CONTAMINATED"
    assert "CASE_USED_DURING_DEVELOPMENT" in result.contamination_reasons


def test_hg11_materially_identical_prior_case_is_contaminated():
    record = valid_record()
    record["case_provenance"] = "PRIOR_EXECUTED_MATERIALLY_IDENTICAL"
    result = assess(record)
    assert "MATERIALLY_IDENTICAL_PRIOR_EXECUTION" in result.contamination_reasons


def test_hg12_role_overlap_is_recorded_not_independent():
    record = valid_record()
    record["role_assignments"]["HUMAN_DECISION"] = ["human-a"]
    record["role_overlap_declarations"] = [{
        "actor_id": "human-a",
        "roles": ["CASE_AUTHOR", "HUMAN_DECISION"],
        "independence_effect": "LIMITED_NOT_INDEPENDENT",
    }]
    result = assess(record)
    assert result.role_overlaps == ("human-a:CASE_AUTHOR,HUMAN_DECISION",)
    assert "ROLE_OVERLAP_LIMITS_INDEPENDENCE" in result.independence_limitations


def test_hg13_unknown_and_eligibility_unknown_are_valid():
    record = valid_record()
    record["case_provenance"] = "UNKNOWN"
    record["chronology"]["expectation_created_at"] = None
    result = assess(record)
    assert result.eligibility == "ELIGIBILITY_UNKNOWN"
    assert result.governance_state == "UNKNOWN"
    assert protocol()["expectation_format"]["unknown_allowed"] is True


def test_hg14_hidden_reasoning_is_not_required_or_stored():
    current = protocol()
    output = current["output_preservation"]
    assert output["hidden_reasoning_required"] is False
    assert output["hidden_reasoning_stored"] is False
    assert valid_record()["raw_output"]["metadata"]["no_hidden_reasoning_stored"] is True
    assert "hidden_chain_of_thought" not in json.dumps(valid_record())


def run_regression(script: str, expected_output: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(EXPERIMENT_ROOT / script)],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert expected_output in completed.stdout


def test_hg15_all_existing_regressions_pass():
    checks = (
        ("runner/test_counter_failure_eval.py", "PASS: Counter-Failure Evaluation"),
        ("runner/test_route_boundary.py", "PASS: Semantic route vocabulary boundary"),
        ("runner/test_openai_provider_schema.py", "PASS: OpenAI Provider Schema Compiler"),
        ("runner/test_openai_error_diagnostics.py", "PASS: OpenAI first-error diagnostics"),
        ("runner/test_openai_semantic_adapter.py", "PASS: OpenAI Semantic Judgment Adapter"),
        ("runner/test_semantic_adapter.py", "PASS: First Semantic Judgment Adapter"),
        ("runner/test_semantic_judgment.py", "PASS: Semantic Judgment Contract"),
        ("runner/test_router.py", "PASS: registry-backed router"),
        ("runner/test_registry_loader.py", "PASS: registry loader"),
        ("build/test_build.py", "PASS: build pipeline"),
    )
    for script, expected in checks:
        run_regression(script, expected)


def test_protocol_survives_required_counter_challenges():
    current = protocol()
    challenges = current["counter_challenges"]
    assert len(challenges) == 7
    assert current["expectation_format"]["exact_narrative_required"] is False
    assert current["small_team_configuration"]["independence_claim"] == "LIMITED_NOT_INDEPENDENT"
    assert current["disagreement"]["post_hoc_review_replaces_original_expectation"] is False
    assert current["eligibility"]["retain_contaminated_cases"] is True


if __name__ == "__main__":
    tests = (
        test_hg1_valid_role_configuration_accepted,
        test_hg2_semantic_agent_expectation_exposure_contaminates,
        test_hg3_expectation_after_output_contaminates,
        test_seal_created_after_output_contaminates,
        test_hg4_sealed_expectation_modification_detected,
        test_hg5_frozen_evaluator_baseline_mismatch_detected,
        test_hg6_annotation_cannot_replace_raw_output,
        test_hg7_annotator_uncertainty_is_representable,
        test_hg8_disagreement_does_not_automatically_fail_model,
        test_hg9_post_hoc_correction_preserves_original_expectation,
        test_hg10_development_case_cannot_be_true_holdout,
        test_hg11_materially_identical_prior_case_is_contaminated,
        test_hg12_role_overlap_is_recorded_not_independent,
        test_hg13_unknown_and_eligibility_unknown_are_valid,
        test_hg14_hidden_reasoning_is_not_required_or_stored,
        test_hg15_all_existing_regressions_pass,
        test_protocol_survives_required_counter_challenges,
    )
    for test in tests:
        test()
    print("PASS: Holdout Annotation Governance Protocol v0.1 tests (HG1-HG15)")
