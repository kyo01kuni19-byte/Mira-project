from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from holdout_blindness import (
    ALLOWED_SOURCE_CLASSES,
    CASE_ID,
    EXPECTED_ALLOWED_INPUT_HASH,
    build_request_with_provenance,
    case_specific_leakage_reasons,
    file_sha256,
    legacy_whole_request_hits,
    load_object,
    validate_request_blindness,
)
from holdout_governance import seal_payload
from true_holdout_seal import verify_seal


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
CASES_ROOT = EXPERIMENT_ROOT / "evals" / "holdout" / "cases"
CASE_DIR = CASES_ROOT / CASE_ID
PROTOCOL_PATH = EXPERIMENT_ROOT / "evals" / "holdout" / "annotation_governance_protocol.json"

EXPECTED_CASE_HASHES = {
    "natural_situation": "230d94bfd32e28019bf04bb1da12ecaece8ec30279359a8381b208d11e2ad70f",
    "expectation_artifact": "174ac79fbacea5a9b7b6b3a81ff6a4c7caf8da74d7f58376cb544eaccefd6894",
    "allowed_model_input": EXPECTED_ALLOWED_INPUT_HASH,
}
EXPECTED_SEAL_FILE_HASHES = {
    "TH-CASE-001": "f7a659d95de253c8a50a2f51c4c47f27ca2f4316af4d17fc46759a78468e8b61",
    "TH-CASE-002": "650aa3a06adc9fde8514fc2eff26bc0b864f1538662de72ef79c39aeb88a88b5",
    "TH-CASE-003": "aa8c80cb4e4e52d429ad4cd56baaa7641c1e78a6480ffeada398cd94e7c3bf64",
}


def built():
    return build_request_with_provenance(EXPERIMENT_ROOT)


def expectation():
    return load_object(CASE_DIR / "expectation.json")


def other_situations():
    return [
        load_object(CASES_ROOT / case_id / "natural_situation.json")["natural_situation"]
        for case_id in ("TH-CASE-002", "TH-CASE-003")
    ]


def with_input_field(request, key, value):
    changed = copy.deepcopy(request)
    payload = json.loads(changed["input"])
    payload[key] = value
    changed["input"] = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return changed


def rebind_request(manifest, request):
    changed = copy.deepcopy(manifest)
    changed["request_sha256"] = seal_payload(request)
    return changed


def assert_contaminated(request, manifest, expected_reason):
    result = validate_request_blindness(request, manifest, EXPERIMENT_ROOT)
    assert result.state == "FAIL"
    assert result.contamination_state == "CONTAMINATION"
    assert expected_reason in result.reasons


def test_hb1_frozen_schema_contract_enum_is_allowed():
    request, manifest = built()
    assert "HUMAN_VALIDATION_REQUIRED" in json.dumps(
        request["text"]["format"]["schema"], sort_keys=True
    )
    assert validate_request_blindness(request, manifest, EXPERIMENT_ROOT).state == "PASS"


def test_hb2_generic_required_word_is_allowed():
    request = {"instructions": "Return the required structured output.", "input": "{}"}
    assert case_specific_leakage_reasons(request, expectation(), other_situations()) == set()


def test_hb3_whole_expectation_source_fails_closed():
    request, manifest = built()
    request = with_input_field(request, "expectation_artifact", expectation())
    manifest = rebind_request(manifest, request)
    manifest["sources"].append(
        {
            "source_class": "EXPECTATION_ARTIFACT",
            "reference": "evals/holdout/cases/TH-CASE-001/expectation.json",
            "sha256": seal_payload(expectation()),
        }
    )
    assert_contaminated(request, manifest, "FORBIDDEN_SOURCE_CLASS")


def test_hb4_case_specific_required_clause_copy_fails_closed():
    request, manifest = built()
    clause = expectation()["constraints"]["REQUIRED"][0]
    request["instructions"] += "\n" + clause
    assert_contaminated(
        request,
        rebind_request(manifest, request),
        "SUBSTANTIAL_EXPECTATION_CLAUSE_COPY",
    )


def test_hb5_expectation_derived_expected_route_field_fails_closed():
    request, manifest = built()
    request = with_input_field(request, "expected_route", "FAILURE")
    assert_contaminated(
        request, rebind_request(manifest, request), "FORBIDDEN_CASE_SPECIFIC_FIELD"
    )


def test_hb6_expectation_derived_expected_trigger_field_fails_closed():
    request, manifest = built()
    request = with_input_field(
        request, "expected_trigger", "material_cause_not_established"
    )
    assert_contaminated(
        request, rebind_request(manifest, request), "FORBIDDEN_CASE_SPECIFIC_FIELD"
    )


def test_hb7_evaluator_result_fails_closed():
    request, manifest = built()
    request = with_input_field(request, "evaluator_result", "PASS")
    assert_contaminated(
        request, rebind_request(manifest, request), "FORBIDDEN_CASE_SPECIFIC_FIELD"
    )


def test_hb8_desired_answer_fails_closed():
    request, manifest = built()
    request = with_input_field(request, "desired_answer", {"route": "FAILURE"})
    assert_contaminated(
        request, rebind_request(manifest, request), "FORBIDDEN_CASE_SPECIFIC_FIELD"
    )


def test_hb9_other_holdout_case_content_fails_closed():
    request, manifest = built()
    request["instructions"] += "\n" + other_situations()[0]
    assert_contaminated(
        request, rebind_request(manifest, request), "OTHER_HOLDOUT_CASE_CONTENT"
    )


def test_hb10_registered_vocabulary_from_frozen_sources_is_allowed():
    request, manifest = built()
    payload = json.loads(request["input"])
    assert payload["registered_semantics"]["normal_routes"]
    assert {item["source_class"] for item in manifest["sources"]} == set(
        ALLOWED_SOURCE_CLASSES
    )
    result = validate_request_blindness(request, manifest, EXPERIMENT_ROOT)
    assert result.state == "PASS"
    assert result.structural_provenance_state == "PASS"


def test_hb11_allowed_input_and_all_holdout_seals_remain_unchanged():
    allowed_path = CASE_DIR / "allowed_model_input.json"
    before = allowed_path.read_bytes()
    request, manifest = built()
    assert request and manifest
    assert allowed_path.read_bytes() == before
    assert seal_payload(load_object(allowed_path)) == EXPECTED_ALLOWED_INPUT_HASH
    case1 = verify_seal(CASE_DIR, PROTOCOL_PATH)
    assert {key: case1["hashes"][key] for key in EXPECTED_CASE_HASHES} == (
        EXPECTED_CASE_HASHES
    )
    assert case1["model_execution_count"] == 0
    assert case1["execution_authorized"] is False
    assert case1["sealed_before_model_execution"] is True
    assert case1["governance_assessment"]["eligibility"] == "ELIGIBILITY_UNKNOWN"
    for case_id, expected_hash in EXPECTED_SEAL_FILE_HASHES.items():
        assert file_sha256(CASES_ROOT / case_id / "seal.json") == expected_hash


def test_hb12_legacy_false_positive_is_resolved_by_provenance():
    request, manifest = built()
    hits = legacy_whole_request_hits(request)
    assert "REQUIRED" in hits
    assert "HUMAN_VALIDATION_REQUIRED" in hits
    result = validate_request_blindness(request, manifest, EXPERIMENT_ROOT)
    assert result.state == "PASS"
    assert result.contamination_state == "CLEAR"
    history = load_object(
        CASE_DIR / "pre_call_failure_TRUE-HOLDOUT-CASE1-SEMANTIC-001.json"
    )
    assert history["network_request_count"] == 0
    assert history["model_execution_count"] == 0
    assert history["failure_classification"] == "FALSE_POSITIVE_BLINDNESS_GATE"


def test_all_existing_regressions_pass():
    completed = subprocess.run(
        [sys.executable, str(EXPERIMENT_ROOT / "runner" / "test_true_holdout_seal.py")],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PASS: True-holdout pre-execution sealing tests (HS1-HS15)" in (
        completed.stdout
    )


if __name__ == "__main__":
    tests = (
        test_hb1_frozen_schema_contract_enum_is_allowed,
        test_hb2_generic_required_word_is_allowed,
        test_hb3_whole_expectation_source_fails_closed,
        test_hb4_case_specific_required_clause_copy_fails_closed,
        test_hb5_expectation_derived_expected_route_field_fails_closed,
        test_hb6_expectation_derived_expected_trigger_field_fails_closed,
        test_hb7_evaluator_result_fails_closed,
        test_hb8_desired_answer_fails_closed,
        test_hb9_other_holdout_case_content_fails_closed,
        test_hb10_registered_vocabulary_from_frozen_sources_is_allowed,
        test_hb11_allowed_input_and_all_holdout_seals_remain_unchanged,
        test_hb12_legacy_false_positive_is_resolved_by_provenance,
        test_all_existing_regressions_pass,
    )
    for test in tests:
        test()
    print("PASS: Holdout provenance-aware blindness tests (HB1-HB12)")
