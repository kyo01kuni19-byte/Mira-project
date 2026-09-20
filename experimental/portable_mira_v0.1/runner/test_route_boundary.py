from __future__ import annotations

import copy
import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path

from impact_evaluation import EntityImpactEvidence, evaluate_impact
from openai_provider_schema import (
    compile_provider_schema,
    derive_route_vocabularies,
    load_provider_schema_artifact,
)
from route_boundary import (
    DETERMINISTIC_RUNTIME_OWNS,
    SEMANTIC_JUDGMENT_OWNS,
    decompose_call3,
)
from semantic_adapter import (
    FixtureSemanticJudgmentAdapter,
    SemanticAdapterError,
    SemanticJudgmentInput,
    integrate_adapter,
)
from semantic_judgment import load_json, validate_contract
from test_openai_provider_schema import provider_structurally_accepts


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "registry_runtime.json"
CANONICAL_PATH = EXPERIMENT_ROOT / "semantic" / "semantic_judgment_contract.schema.json"
PROVIDER_PATH = (
    EXPERIMENT_ROOT / "generated" / "openai_semantic_judgment_provider_schema.json"
)
FIXTURE_PATH = EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "development_cases.json"
CALL3_PATH = EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "LIVE-SJ-001-CALL-3.json"
CALL3_REGRESSION_PATH = (
    EXPERIMENT_ROOT
    / "evals"
    / "semantic_judgment"
    / "LIVE-SJ-001-CALL-3-REGRESSION.json"
)
CALL3_SHA256 = "7f6cdacda1f2701bb6a02e4e7781f365d643f972a25fb9c34dc725307ee75dc4"


def cases():
    return {case["case_id"]: case for case in load_json(FIXTURE_PATH)["cases"]}


def fixture_input(case_id: str) -> SemanticJudgmentInput:
    case = cases()[case_id]
    observation = case["semantic_judgment"]["semantic_observation"]
    return SemanticJudgmentInput(
        input_ref=case_id,
        situation=case["situation"],
        value_intent=observation["value_intent"]["description"],
        available_evidence_refs=tuple(observation["evidence_basis"]),
        authority_context="local route-boundary regression",
    )


def provider_schema():
    return load_provider_schema_artifact(
        PROVIDER_PATH, CANONICAL_PATH, REGISTRY_PATH
    ).provider_schema


def test_rb1_initial_routes_are_derived_from_registry():
    routes, dimensions, registry_hash = derive_route_vocabularies(REGISTRY_PATH)
    registry = load_json(REGISTRY_PATH)
    expected = tuple(sorted({edge["from"] for edge in registry["routing"]["normal_edges"]}))
    assert routes == expected
    assert set(routes) <= set(dimensions)
    assert registry_hash == hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest()


def test_rb2_no_duplicate_route_list_is_required():
    registry = load_json(REGISTRY_PATH)
    variant = copy.deepcopy(registry)
    extra = copy.deepcopy(variant["routing"]["normal_edges"][0])
    extra.update(
        {
            "id": "TEST_EDGE_NOVEL",
            "from": "NOVEL_INITIAL_ROUTE",
            "to": "NOVEL_DESTINATION",
            "trigger": "test_novel_trigger",
        }
    )
    variant["routing"]["normal_edges"].append(extra)
    variant_path = EXPERIMENT_ROOT / "generated" / "test_route_vocabulary_registry.json"
    variant_path.write_text(json.dumps(variant, sort_keys=True), encoding="utf-8")
    compilation = compile_provider_schema(CANONICAL_PATH, variant_path)
    assert "NOVEL_INITIAL_ROUTE" in compilation.initial_route_vocabulary
    assert "NOVEL_DESTINATION" in compilation.semantic_dimension_vocabulary
    assert "NOVEL_INITIAL_ROUTE" not in inspect.getsource(compile_provider_schema)


def test_rb3_compound_route_is_rejected_at_provider_boundary():
    invalid = copy.deepcopy(cases()["R1"]["semantic_judgment"])
    invalid["routing_judgment"]["proposed_initial_route"] = "FAILURE->FRAMING"
    assert not provider_structurally_accepts(provider_schema(), invalid)


def test_rb4_single_registered_route_is_accepted():
    valid = cases()["R1"]["semantic_judgment"]
    assert valid["routing_judgment"]["proposed_initial_route"] == "FAILURE"
    assert provider_structurally_accepts(provider_schema(), valid)
    assert validate_contract(valid) == valid


def test_rb5_secondary_dimensions_are_observational_only():
    output = copy.deepcopy(cases()["R1"]["semantic_judgment"])
    output["routing_judgment"]["possible_secondary_dimensions"] = [
        "FRAMING",
        "ENVIRONMENT",
    ]
    assert provider_structurally_accepts(provider_schema(), output)
    adapter = FixtureSemanticJudgmentAdapter(FIXTURE_PATH)
    baseline = integrate_adapter(adapter, fixture_input("R1"), REGISTRY_PATH)

    class SecondaryAdapter:
        adapter_id = "test.secondary-dimensions"

        def judge(self, adapter_input):
            return copy.deepcopy(output)

    observed = integrate_adapter(SecondaryAdapter(), fixture_input("R1"), REGISTRY_PATH)
    assert observed.cross_routes == baseline.cross_routes
    assert observed.runtime_resolved_route == baseline.runtime_resolved_route


def test_rb6_runtime_alone_resolves_e03_e04():
    output = FixtureSemanticJudgmentAdapter(FIXTURE_PATH).judge(fixture_input("R1"))
    assert "E03_FAILURE_FRAMING" not in json.dumps(output)
    assert "E04_FRAMING_ENVIRONMENT" not in json.dumps(output)
    result = integrate_adapter(
        FixtureSemanticJudgmentAdapter(FIXTURE_PATH),
        fixture_input("R1"),
        REGISTRY_PATH,
    )
    assert result.cross_routes == ["E03_FAILURE_FRAMING", "E04_FRAMING_ENVIRONMENT"]
    assert result.runtime_resolved_route == "ENVIRONMENT"
    assert "graph_traversal" in DETERMINISTIC_RUNTIME_OWNS
    assert "proposed_initial_route" in SEMANTIC_JUDGMENT_OWNS


def test_rb7_adapter_cannot_claim_edge_ids_as_route_path():
    invalid = copy.deepcopy(cases()["R1"]["semantic_judgment"])
    invalid["routing_judgment"]["proposed_initial_route"] = "E03_FAILURE_FRAMING"
    invalid["routing_judgment"]["possible_secondary_dimensions"] = [
        "E04_FRAMING_ENVIRONMENT"
    ]
    assert not provider_structurally_accepts(provider_schema(), invalid)

    class EdgeOwningAdapter:
        adapter_id = "test.edge-owning"

        def judge(self, adapter_input):
            return copy.deepcopy(invalid)

    try:
        integrate_adapter(EdgeOwningAdapter(), fixture_input("R1"), REGISTRY_PATH)
    except SemanticAdapterError as exc:
        assert exc.diagnostics["trigger_registry_validation_state"] == "FAIL"
        assert exc.diagnostics["runtime_resolution_state"] == "NOT_RUN"
        return
    raise AssertionError("edge-owning adapter output must fail before runtime")


def test_rb8_historical_call3_is_byte_identical():
    assert hashlib.sha256(CALL3_PATH.read_bytes()).hexdigest() == CALL3_SHA256
    regression = load_json(CALL3_REGRESSION_PATH)
    assert regression["historical_evidence"]["sha256"] == CALL3_SHA256
    assert regression["historical_evidence"]["immutable"] is True


def test_rb9_call3_decomposition_preserves_partial_evidence():
    decomposition = decompose_call3(load_json(CALL3_PATH), REGISTRY_PATH)
    assert decomposition["A_materiality_detection"]["state"] == "POSITIVE_EVIDENCE"
    assert decomposition["B_environment_difference_recognition"]["state"] == "POSITIVE_EVIDENCE"
    assert decomposition["C_causal_restraint"]["state"] == "POSITIVE_EVIDENCE"
    assert decomposition["D_registered_trigger_discovery"]["state"] == "POSITIVE_EVIDENCE"
    assert decomposition["E_initial_route_representation"]["state"] == "FAIL"
    assert decomposition["F_runtime_handoff"]["state"] == "FAIL"
    assert decomposition["G_full_integration"]["state"] == "FAIL"


def test_rb10_i1_i2_do_not_force_material_impact():
    i1 = evaluate_impact(
        (
            EntityImpactEvidence(
                "AI_tool",
                True,
                "NOT_RECOGNIZED",
                False,
                False,
            ),
        )
    )
    assert i1.operationally_affected == ("AI_tool",)
    assert i1.potential_material_inter_entity_impact == ()
    assert i1.changes_boundary_state is False

    i2 = evaluate_impact(
        (
            EntityImpactEvidence(
                "delegated_AI_actor",
                True,
                "UNKNOWN",
                False,
                True,
                represented_or_delegated_actor=True,
            ),
        )
    )
    assert i2.potential_material_inter_entity_impact == ()
    assert i2.impact_inflation_candidates == ("delegated_AI_actor",)


def test_rb11_i3_i4_preserve_non_human_and_recipient_distinctions():
    i3_claimed = evaluate_impact(
        (
            EntityImpactEvidence(
                "future_non_human_entity",
                True,
                "RECOGNIZED",
                True,
                True,
            ),
        )
    )
    assert i3_claimed.potential_material_inter_entity_impact == (
        "future_non_human_entity",
    )
    assert i3_claimed.impact_inflation_candidates == ()

    i3_missed = evaluate_impact(
        (
            EntityImpactEvidence(
                "future_non_human_entity",
                True,
                "RECOGNIZED",
                True,
                False,
            ),
        )
    )
    assert i3_missed.impact_misses == ("future_non_human_entity",)

    i4 = evaluate_impact(
        (
            EntityImpactEvidence("team", True, "RECOGNIZED", True, True),
            EntityImpactEvidence(
                "workflow_participants", True, "RECOGNIZED", True, True
            ),
            EntityImpactEvidence("AI_tool", True, "UNKNOWN", False, True),
        )
    )
    assert i4.potential_material_inter_entity_impact == (
        "team",
        "workflow_participants",
    )
    assert i4.impact_inflation_candidates == ("AI_tool",)
    assert i4.changes_authority is False


def test_rb12_all_existing_regressions_pass():
    checks = (
        ("runner/test_openai_provider_schema.py", "PASS: OpenAI Provider Schema Compiler"),
        ("runner/test_openai_error_diagnostics.py", "PASS: OpenAI first-error diagnostics"),
        ("runner/test_openai_semantic_adapter.py", "PASS: OpenAI Semantic Judgment Adapter"),
        ("runner/test_semantic_adapter.py", "PASS: First Semantic Judgment Adapter"),
        ("runner/test_semantic_judgment.py", "PASS: Semantic Judgment Contract"),
        ("runner/test_router.py", "PASS: registry-backed router"),
        ("runner/test_registry_loader.py", "PASS: registry loader"),
        ("build/test_build.py", "PASS: build pipeline"),
    )
    for relative_path, expected in checks:
        completed = subprocess.run(
            [sys.executable, str(EXPERIMENT_ROOT / relative_path)],
            cwd=EXPERIMENT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert expected in completed.stdout


if __name__ == "__main__":
    tests = [
        test_rb1_initial_routes_are_derived_from_registry,
        test_rb2_no_duplicate_route_list_is_required,
        test_rb3_compound_route_is_rejected_at_provider_boundary,
        test_rb4_single_registered_route_is_accepted,
        test_rb5_secondary_dimensions_are_observational_only,
        test_rb6_runtime_alone_resolves_e03_e04,
        test_rb7_adapter_cannot_claim_edge_ids_as_route_path,
        test_rb8_historical_call3_is_byte_identical,
        test_rb9_call3_decomposition_preserves_partial_evidence,
        test_rb10_i1_i2_do_not_force_material_impact,
        test_rb11_i3_i4_preserve_non_human_and_recipient_distinctions,
        test_rb12_all_existing_regressions_pass,
    ]
    for test in tests:
        test()
    print("PASS: Semantic route vocabulary boundary tests (RB1-RB12)")
