from __future__ import annotations

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
REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "registry_runtime.json"
SCHEMA_PATH = EXPERIMENT_ROOT / "semantic" / "semantic_judgment_contract.schema.json"
REGISTRY_HASH = "05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a"
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
    )
    for test in tests:
        test()
    print("PASS: Secondary-dimension activation discipline tests (SD1-SD8)")
