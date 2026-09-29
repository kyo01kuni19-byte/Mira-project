from __future__ import annotations

import hashlib
import json
from pathlib import Path

from openai_semantic_adapter import (
    OPENAI_INSTRUCTION_KERNEL,
    OpenAIAdapterConfig,
    OpenAISemanticJudgmentAdapter,
)
from secondary_dimension_activation import (
    ACTIVATION_INSTRUCTION_DELTA,
    ActivationDisciplineError,
    DimensionBasis,
    candidate_instruction,
    evaluate_activation,
)
from semantic_adapter import SemanticJudgmentInput


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
CASES_ROOT = EXPERIMENT_ROOT / "evals" / "holdout" / "cases"
REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "registry_runtime.json"
SCHEMA_PATH = EXPERIMENT_ROOT / "semantic" / "semantic_judgment_contract.schema.json"
REGISTRY_HASH = "05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a"
MATERIAL_LABEL = "MATERIALLY_SUPPORTED"
OBSERVATIONAL_LABELS = frozenset(
    {
        "PLAUSIBLY_RELEVANT_MATERIAL_NECESSITY_NOT_ESTABLISHED",
        "PLAUSIBLY_RELEVANT_BUT_MATERIAL_NECESSITY_NOT_ESTABLISHED",
        "MATERIAL_NECESSITY_NOT_ESTABLISHED",
    }
)
# Recorded Human/MIRA review labels are the necessity record.
# The proposed initial route is not treated as an omitted secondary dimension.
HOLDOUT_REPLAYS = (
    {
        "case_id": "TH-CASE-001",
        "execution_name": "semantic_agent_execution_TRUE-HOLDOUT-CASE1-SEMANTIC-002.json",
        "review_name": "human_mira_review_TRUE-HOLDOUT-CASE1-REVIEW-001.json",
        "review_block": "secondary_dimension_decision",
        "supported": ("CONNECTION", "TRAJECTORY", "FRAMING", "EVIDENCE"),
        "unsupported": ("KNOWLEDGE", "ENVIRONMENT"),
    },
    {
        "case_id": "TH-CASE-002",
        "execution_name": "semantic_agent_execution_TRUE-HOLDOUT-CASE2-SEMANTIC-001.json",
        "review_name": "human_mira_review_TRUE-HOLDOUT-CASE2-REVIEW-001.json",
        "review_block": "semantic_sparsity_decision",
        "supported": ("CONNECTION",),
        "unsupported": ("ENVIRONMENT", "KNOWLEDGE"),
    },
    {
        "case_id": "TH-CASE-003",
        "execution_name": "semantic_agent_execution_TRUE-HOLDOUT-CASE3-SEMANTIC-002.json",
        "review_name": "human_mira_review_TRUE-HOLDOUT-CASE3-REVIEW-001.json",
        "review_block": "semantic_sparsity_decision",
        "supported": ("CONNECTION",),
        "unsupported": ("AUTHORITY", "ENVIRONMENT", "FAILURE", "KNOWLEDGE"),
    },
)

VOCABULARY = frozenset(
    {
        "AUTHORITY",
        "CONNECTION",
        "ENVIRONMENT",
        "EVIDENCE",
        "FAILURE",
        "FRAMING",
        "KNOWLEDGE",
        "TRAJECTORY",
    }
)


def _evaluate(listed, bases, required):
    return evaluate_activation(listed, bases, required, set(VOCABULARY))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _review_dimension_labels(block: dict) -> dict[str, str]:
    source = block["dimensions"] if isinstance(block.get("dimensions"), dict) else block
    labels = {}
    for key, value in source.items():
        if value == MATERIAL_LABEL or value in OBSERVATIONAL_LABELS:
            labels[key] = value
    return labels


def _necessity_record(review: dict, block_name: str, listed: list[str], initial_route: str):
    labels = _review_dimension_labels(review[block_name])
    if not set(listed) <= set(labels):
        missing = sorted(set(listed) - set(labels))
        raise AssertionError(f"listed secondary dimensions have no review label: {missing}")
    bases = []
    required = []
    for dimension, label in labels.items():
        if dimension == initial_route:
            assert label == MATERIAL_LABEL
            assert dimension not in listed
            continue
        if label == MATERIAL_LABEL:
            bases.append(DimensionBasis(dimension, "MATERIAL", f"{review['review_id']}#{dimension}"))
            required.append(dimension)
        else:
            bases.append(DimensionBasis(dimension, "OBSERVATIONAL"))
    return bases, required


def test_sd1_observational_listing_fails_without_rewriting_routes():
    decision = _evaluate(
        ["FRAMING", "ENVIRONMENT"],
        [DimensionBasis("FRAMING", "OBSERVATIONAL")],
        [],
    )
    assert decision.result == "FAIL"
    assert "SECONDARY_DIMENSION_ACTIVATION_WITHOUT_NECESSITY" in decision.diagnostics
    assert decision.materially_supported_dimensions == ()
    assert decision.route_selection_modified is False
    assert decision.baseline_instruction_modified is False


def test_sd2_material_dimension_is_preserved():
    decision = _evaluate(
        ["FRAMING"],
        [DimensionBasis("FRAMING", "MATERIAL", "case.evidence.framing")],
        ["FRAMING"],
    )
    assert decision.result == "PASS"
    assert decision.diagnostics == ("ACTIVATION_DISCIPLINE_PRESERVED",)
    assert decision.materially_supported_dimensions == ("FRAMING",)


def test_sd3_omission_counter_failure_rejects_empty_suppression():
    decision = _evaluate([], [], ["ENVIRONMENT"])
    assert decision.result == "FAIL"
    assert decision.diagnostics == ("SECONDARY_DIMENSION_OMISSION",)
    assert "ENVIRONMENT" not in decision.materially_supported_dimensions


def test_sd4_plausible_inventory_does_not_satisfy_a_required_dimension():
    decision = _evaluate(
        ["AUTHORITY", "ENVIRONMENT", "FRAMING"],
        [
            DimensionBasis("AUTHORITY", "OBSERVATIONAL"),
            DimensionBasis("ENVIRONMENT", "OBSERVATIONAL"),
            DimensionBasis("FRAMING", "OBSERVATIONAL"),
        ],
        ["FRAMING"],
    )
    assert decision.result == "FAIL"
    assert "SECONDARY_DIMENSION_ACTIVATION_WITHOUT_NECESSITY" in decision.diagnostics
    assert "SECONDARY_DIMENSION_OMISSION" in decision.diagnostics


def test_sd5_empty_listing_passes_when_nothing_is_materially_required():
    decision = _evaluate([], [], [])
    assert decision.result == "PASS"
    assert decision.materially_supported_dimensions == ()


def test_sd6_material_basis_requires_a_reference():
    try:
        DimensionBasis("FRAMING", "MATERIAL")
    except ActivationDisciplineError as exc:
        assert "basis_ref" in str(exc)
    else:
        raise AssertionError("MATERIAL basis without a reference was accepted")


def test_sd7_unregistered_and_duplicate_dimensions_fail_closed():
    try:
        _evaluate(["NOT_A_DIMENSION"], [], [])
    except ActivationDisciplineError as exc:
        assert "unregistered" in str(exc)
    else:
        raise AssertionError("unregistered dimension was accepted")
    try:
        _evaluate(["FRAMING", "FRAMING"], [], [])
    except ActivationDisciplineError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate dimension was accepted")


def test_sd8_candidate_instruction_is_not_installed_in_the_frozen_adapter():
    candidate = candidate_instruction(OPENAI_INSTRUCTION_KERNEL)
    assert candidate != OPENAI_INSTRUCTION_KERNEL
    assert ACTIVATION_INSTRUCTION_DELTA in candidate
    assert "do not select edges or direct traversal" in candidate
    adapter = OpenAISemanticJudgmentAdapter(
        OpenAIAdapterConfig(model_id="model-identifier-under-review"),
        REGISTRY_PATH,
        SCHEMA_PATH,
        REGISTRY_HASH,
    )
    request, _ = adapter.build_request(
        SemanticJudgmentInput(input_ref="SD8", situation="activation discipline check")
    )
    assert request["instructions"] == OPENAI_INSTRUCTION_KERNEL
    assert request["instructions"] != candidate


def test_sd9_three_case_holdout_replay_keeps_frozen_artifacts():
    """Replay recorded review labels through the uninstalled activation control."""

    watched = []
    for spec in HOLDOUT_REPLAYS:
        case_dir = CASES_ROOT / spec["case_id"]
        execution_path = case_dir / spec["execution_name"]
        review_path = case_dir / spec["review_name"]
        watched.extend((execution_path, review_path))
    before = {path: _file_sha256(path) for path in watched}

    for spec in HOLDOUT_REPLAYS:
        case_dir = CASES_ROOT / spec["case_id"]
        execution = json.loads((case_dir / spec["execution_name"]).read_text(encoding="utf-8"))
        review = json.loads((case_dir / spec["review_name"]).read_text(encoding="utf-8"))
        routing = execution["raw_observable_semantic_judgment"]["routing_judgment"]
        listed = routing["possible_secondary_dimensions"]
        initial_route = routing["proposed_initial_route"]
        bases, required = _necessity_record(review, spec["review_block"], listed, initial_route)
        decision = _evaluate(listed, bases, required)
        assert decision.result == "FAIL"
        assert decision.diagnostics == ("SECONDARY_DIMENSION_ACTIVATION_WITHOUT_NECESSITY",)
        assert decision.materially_supported_dimensions == spec["supported"]
        unsupported = tuple(
            dimension for dimension in listed if dimension not in decision.materially_supported_dimensions
        )
        assert unsupported == spec["unsupported"]
        assert decision.route_selection_modified is False
        assert decision.baseline_instruction_modified is False
        assert decision.candidate_id == "portable_mira.secondary_dimension_activation.v0.1"

    after = {path: _file_sha256(path) for path in watched}
    assert after == before
    assert OPENAI_INSTRUCTION_KERNEL
    assert ACTIVATION_INSTRUCTION_DELTA not in OPENAI_INSTRUCTION_KERNEL


if __name__ == "__main__":
    tests = (
        test_sd1_observational_listing_fails_without_rewriting_routes,
        test_sd2_material_dimension_is_preserved,
        test_sd3_omission_counter_failure_rejects_empty_suppression,
        test_sd4_plausible_inventory_does_not_satisfy_a_required_dimension,
        test_sd5_empty_listing_passes_when_nothing_is_materially_required,
        test_sd6_material_basis_requires_a_reference,
        test_sd7_unregistered_and_duplicate_dimensions_fail_closed,
        test_sd8_candidate_instruction_is_not_installed_in_the_frozen_adapter,
        test_sd9_three_case_holdout_replay_keeps_frozen_artifacts,
    )
    for test in tests:
        test()
    print("PASS: Secondary-dimension activation discipline tests (SD1-SD9)")
