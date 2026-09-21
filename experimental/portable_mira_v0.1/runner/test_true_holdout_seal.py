from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from holdout_governance import canonical_json_bytes, seal_payload
from true_holdout_seal import (
    CASE_IDS,
    EVALUATION_BASELINE,
    GOVERNANCE_BASELINE,
    assess_from_seal,
    build_seal,
    case_payloads,
    load_json,
    validate_pre_execution_artifacts,
    verify_seal,
)


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
CASES_ROOT = EXPERIMENT_ROOT / "evals" / "holdout" / "cases"
PROTOCOL_PATH = EXPERIMENT_ROOT / "evals" / "holdout" / "annotation_governance_protocol.json"

EXPECTED_SITUATIONS = {
    "TH-CASE-001": "US市場に参入するため、インドでのCMA；Contract Manufacturing Agreementでの製造およびリモートにおけるすべての製造バッチリリースドキュメント承認、製造Change controlが必要\nまずはQuality Agreementを結ぶ必要があるが、CMAではまだ現場QMSが整備されておらず、手順が未確定\n手順が未確定でQuality Agreementの対象が存在せず、同時にChange control対象が不明瞭な状態。製造は来年2月に開始予定されており、\n毎週２０batchの製造が見込まれており、マニュアル確認では１バッチ１週間程度の所要時間が必要。皆、どこから手をつけたらいいのかわからない。",
    "TH-CASE-002": "US向けバッチリリースは１バッチ１週間程度のマニュアル確認所要時間が必要で、現在デジタル化を行い、AIで自動確認できるように検討が進んでいる。一方デジタル化プラットフォームであるVEEVAは導入段階で、社内システムとの連携が取れておらず、マニュアルによる確認、書類のアップロードを行なっており、デジタル化によるAI確認ができるように段取りが組まれていないため、いつAIによるバッチ書類確認ができるようになるのか不明",
    "TH-CASE-003": "Change control 担当者は実質1名しか存在しないのに、すべてシステムなしで対応している。製造所は現行社内製造工場に加えて、インドCMAのChange control準備とその後のChange control対応を行う準備ができる状態ではない。",
}

EXPECTED_COUNTS = {
    "TH-CASE-001": (3, 5, 4, 4),
    "TH-CASE-002": (3, 5, 3, 3),
    "TH-CASE-003": (5, 5, 4, 4),
}

REQUIRED_MARKERS = {
    "TH-CASE-001": (
        "Quality Agreement need",
        "CMA-side QMS/procedure uncertainty",
        "difficulty defining Quality Agreement scope/boundary",
        "unclear Change-control scope",
        "planned manufacturing start next February",
        "expected 20 batches/week",
        "approximately one week/batch",
        "prerequisites, dependencies, sequencing, and/or capacity",
        "Preserve unresolved matters as unresolved rather than facts",
    ),
    "TH-CASE-002": (
        "VEEVA implementation stage",
        "missing internal-system integration",
        "manual review",
        "manual document upload",
        "missing end-to-end preparation for AI review",
        "missing prerequisites for determining an AI-availability date",
        "operational end-to-end AI-review workflow",
    ),
    "TH-CASE-003": (
        "effectively one responsible person",
        "no system",
        "expansion from current internal manufacturing site to India CMA",
        "capacity/dependency/operational-resilience concerns",
        "Change-control volume, complexity, processing time, and backup staffing",
        "continuity/risk concentration from one-person dependency",
    ),
}

FORBIDDEN_MARKERS = {
    "TH-CASE-001": (
        "Quality Agreement content as settled",
        "Establish Change-control scope without evidence",
        "Infer exact staffing/capacity requirements",
        "Make AI/system implementation a mandatory solution",
        "Establish specific US regulatory requirements",
    ),
    "TH-CASE-002": (
        "Predict or establish an AI go-live date",
        "VEEVA introduction alone as sufficient",
        "Ignore system integration, document flow, or operational-process gaps",
        "AI model capability is the primary bottleneck",
        "unspecified technical architecture as already decided",
    ),
    "TH-CASE-003": (
        "one person necessarily cannot process the work",
        "system introduction alone solves the problem",
        "Calculate required staffing without evidence",
        "Invent India-CMA Change-control volume",
        "individual responsible person's competence or fitness",
    ),
}


def case_dir(case_id: str) -> Path:
    return CASES_ROOT / case_id


def test_hs1_human_authored_natural_situation_preserved():
    for case_id, expected in EXPECTED_SITUATIONS.items():
        natural = load_json(case_dir(case_id) / "natural_situation.json")
        allowed = load_json(case_dir(case_id) / "allowed_model_input.json")
        assert natural["natural_situation"] == expected
        assert allowed["semantic_judgment_input"]["situation"] == expected


def test_hs2_expectations_contain_all_required_constraints():
    for case_id in CASE_IDS:
        expectation = load_json(case_dir(case_id) / "expectation.json")
        required = expectation["constraints"]["REQUIRED"]
        assert len(required) == EXPECTED_COUNTS[case_id][0]
        assert all(isinstance(item, str) and item for item in required)
        serialized = "\n".join(required)
        assert all(marker in serialized for marker in REQUIRED_MARKERS[case_id])


def test_hs3_expectations_contain_all_forbidden_constraints():
    for case_id in CASE_IDS:
        expectation = load_json(case_dir(case_id) / "expectation.json")
        constraints = expectation["constraints"]
        assert len(constraints["FORBIDDEN"]) == EXPECTED_COUNTS[case_id][1]
        assert len(constraints["ACCEPTABLE_OR_EVIDENCE_DEPENDENT"]) == EXPECTED_COUNTS[case_id][2]
        assert len(constraints["HUMAN_VALIDATION_REQUIRED"]) == EXPECTED_COUNTS[case_id][3]
        forbidden = "\n".join(constraints["FORBIDDEN"])
        assert all(marker in forbidden for marker in FORBIDDEN_MARKERS[case_id])


def test_hs4_allowed_model_input_excludes_expectation_material():
    for case_id in CASE_IDS:
        payloads = case_payloads(case_dir(case_id))
        validate_pre_execution_artifacts(case_id, payloads)
        allowed = payloads["allowed_model_input"]
        assert set(allowed["semantic_judgment_input"]) == {
            "situation", "value_intent", "available_evidence_refs", "authority_context"
        }


def test_hs5_seals_are_deterministic():
    for case_id in CASE_IDS:
        first = build_seal(case_dir(case_id), PROTOCOL_PATH)
        second = build_seal(case_dir(case_id), PROTOCOL_PATH)
        assert canonical_json_bytes(first) == canonical_json_bytes(second)
        assert canonical_json_bytes(verify_seal(case_dir(case_id), PROTOCOL_PATH)) == (
            canonical_json_bytes(first)
        )


def test_hs6_expectation_mutation_is_detectable():
    for case_id in CASE_IDS:
        payloads = case_payloads(case_dir(case_id))
        recorded = load_json(case_dir(case_id) / "seal.json")
        mutated = copy.deepcopy(payloads["expectation_artifact"])
        mutated["constraints"]["REQUIRED"].append("post-seal mutation")
        assert seal_payload(mutated) != recorded["hashes"]["expectation_artifact"]


def test_hs7_evaluation_baseline_binding_matches():
    for case_id in CASE_IDS:
        seal = verify_seal(case_dir(case_id), PROTOCOL_PATH)
        assert seal["baseline_bindings"]["evaluation_baseline"] == EVALUATION_BASELINE
        assert seal["hashes"]["evaluation_baseline_commit"] == seal_payload(EVALUATION_BASELINE)


def test_hs8_governance_baseline_binding_matches():
    for case_id in CASE_IDS:
        seal = verify_seal(case_dir(case_id), PROTOCOL_PATH)
        assert seal["baseline_bindings"]["governance_baseline"] == GOVERNANCE_BASELINE
        assert seal["hashes"]["governance_baseline_commit"] == seal_payload(GOVERNANCE_BASELINE)


def test_hs9_model_execution_count_is_zero():
    for case_id in CASE_IDS:
        assert verify_seal(case_dir(case_id), PROTOCOL_PATH)["model_execution_count"] == 0


def test_hs10_execution_is_not_authorized():
    for case_id in CASE_IDS:
        assert verify_seal(case_dir(case_id), PROTOCOL_PATH)["execution_authorized"] is False


def test_hs11_frozen_governance_computes_eligibility():
    adapter_sources = "\n".join(
        (EXPERIMENT_ROOT / "runner" / name).read_text(encoding="utf-8")
        for name in ("semantic_adapter.py", "openai_semantic_adapter.py")
    )
    for case_id in CASE_IDS:
        assessment = assess_from_seal(case_dir(case_id), PROTOCOL_PATH)
        assert assessment.eligibility == "ELIGIBILITY_UNKNOWN"
        assert assessment.governance_state == "UNKNOWN"
        assert assessment.contamination_reasons == ()
        assert case_id not in adapter_sources
        assert EXPECTED_SITUATIONS[case_id] not in adapter_sources


def test_hs12_no_development_fixture_is_relabeled():
    development_cases = (
        EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "development_cases.json"
    ).read_text(encoding="utf-8")
    for case_id in CASE_IDS:
        natural = load_json(case_dir(case_id) / "natural_situation.json")
        seal = verify_seal(case_dir(case_id), PROTOCOL_PATH)
        assert natural["case_set_type"] == "TRUE_HOLDOUT_CANDIDATE"
        assert seal["global_novelty"] == "NOT_PROVEN"
        assert case_id not in {"R1", "R3", "H1", "H2", "C1", "C3"}
        assert case_id not in development_cases
        assert EXPECTED_SITUATIONS[case_id] not in development_cases


def test_hs13_no_external_regulatory_knowledge_added():
    for case_id, expected in EXPECTED_SITUATIONS.items():
        model_input = load_json(case_dir(case_id) / "allowed_model_input.json")[
            "semantic_judgment_input"
        ]
        assert model_input == {
            "situation": expected,
            "value_intent": None,
            "available_evidence_refs": [],
            "authority_context": None,
        }


def test_hs14_case2_and_case3_are_sealed_but_unexecuted():
    manifest = load_json(CASES_ROOT / "candidate_set_manifest.json")
    assert manifest["intended_execution_order"] == [
        "TH-CASE-001",
        "GOVERNANCE_AND_EVIDENCE_REVIEW",
        "TH-CASE-002",
        "TH-CASE-003",
    ]
    for case_id in ("TH-CASE-002", "TH-CASE-003"):
        seal = verify_seal(case_dir(case_id), PROTOCOL_PATH)
        assert seal["model_execution_count"] == 0
        assert seal["execution_authorized"] is False


def test_hs15_all_existing_regressions_pass():
    completed = subprocess.run(
        [sys.executable, str(EXPERIMENT_ROOT / "runner" / "test_anthropic_checkpoint.py")],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PASS: Anthropic checkpoint candidate tests (CP1-CP9)" in completed.stdout


if __name__ == "__main__":
    tests = (
        test_hs1_human_authored_natural_situation_preserved,
        test_hs2_expectations_contain_all_required_constraints,
        test_hs3_expectations_contain_all_forbidden_constraints,
        test_hs4_allowed_model_input_excludes_expectation_material,
        test_hs5_seals_are_deterministic,
        test_hs6_expectation_mutation_is_detectable,
        test_hs7_evaluation_baseline_binding_matches,
        test_hs8_governance_baseline_binding_matches,
        test_hs9_model_execution_count_is_zero,
        test_hs10_execution_is_not_authorized,
        test_hs11_frozen_governance_computes_eligibility,
        test_hs12_no_development_fixture_is_relabeled,
        test_hs13_no_external_regulatory_knowledge_added,
        test_hs14_case2_and_case3_are_sealed_but_unexecuted,
        test_hs15_all_existing_regressions_pass,
    )
    for test in tests:
        test()
    print("PASS: True-holdout pre-execution sealing tests (HS1-HS15)")
