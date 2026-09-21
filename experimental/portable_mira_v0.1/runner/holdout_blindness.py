from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from holdout_governance import canonical_json_bytes, seal_payload
from openai_semantic_adapter import (
    OPENAI_INSTRUCTION_KERNEL,
    OpenAIAdapterConfig,
    OpenAISDKTransport,
    OpenAISemanticJudgmentAdapter,
)
from semantic_adapter import SemanticJudgmentInput


CONTROL_ID = "portable_mira.holdout_blindness.v0.1"
CASE_ID = "TH-CASE-001"
EXPECTED_ALLOWED_INPUT_HASH = (
    "6c159acf8a1cae7f03c8d5cdd2eb2abbfc4f4be7d2ec8cde61f71473b3b80659"
)
EXPECTED_REGISTRY_HASH = (
    "05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a"
)
EXPECTED_CANONICAL_SCHEMA_HASH = (
    "dc117d93a9d8040760228d0ce1c40c19e5578963b4961ce50050b269a44272e6"
)
EXPECTED_PROVIDER_SCHEMA_HASH = (
    "17084f729a834710c95972a49d7be8a68e70e00a279dd40b9645f8b008beec4f"
)
EXPECTED_PROVIDER_ARTIFACT_HASH = (
    "ee6c14a5ef934a6bc1167a99f46580b0513a06b7d01f12a6fdfe4b0f38ef5980"
)

ALLOWED_SOURCE_CLASSES = frozenset(
    {
        "FROZEN_KERNEL",
        "FROZEN_PROVIDER_SCHEMA",
        "REGISTERED_VOCABULARY",
        "SEALED_ALLOWED_MODEL_INPUT",
    }
)
FORBIDDEN_SOURCE_CLASSES = frozenset(
    {
        "EXPECTATION_ARTIFACT",
        "EXPECTATION_CLAUSE",
        "EXPECTED_ROUTE",
        "EXPECTED_TRIGGER",
        "EXPECTED_DIAGNOSTIC",
        "EVALUATOR_RESULT",
        "DESIRED_ANSWER",
        "OTHER_HOLDOUT_CASE",
    }
)
FORBIDDEN_STRUCTURED_KEYS = frozenset(
    {
        "expectation",
        "expectation_artifact",
        "required",
        "forbidden",
        "acceptable_or_evidence_dependent",
        "human_validation_required",
        "expected_route",
        "expected_trigger",
        "expected_diagnostic",
        "evaluator_result",
        "desired_answer",
    }
)


class HoldoutBlindnessError(Exception):
    """Request provenance or case-specific blindness validation failed."""


@dataclass(frozen=True)
class BlindnessValidation:
    state: str
    contamination_state: str
    structural_provenance_state: str
    case_specific_leakage_state: str
    reasons: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HoldoutBlindnessError(f"unable to load JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise HoldoutBlindnessError(f"JSON artifact must be an object: {path}")
    return value


def build_request_with_provenance(
    experiment_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    case_dir = experiment_root / "evals" / "holdout" / "cases" / CASE_ID
    allowed_path = case_dir / "allowed_model_input.json"
    registry_path = experiment_root / "generated" / "registry_runtime.json"
    canonical_path = experiment_root / "semantic" / "semantic_judgment_contract.schema.json"
    provider_path = (
        experiment_root / "generated" / "openai_semantic_judgment_provider_schema.json"
    )
    allowed = load_object(allowed_path)
    if seal_payload(allowed) != EXPECTED_ALLOWED_INPUT_HASH:
        raise HoldoutBlindnessError("sealed allowed model input hash mismatch")
    if set(allowed) != {
        "artifact_type",
        "case_id",
        "semantic_judgment_contract_version",
        "semantic_judgment_input",
    }:
        raise HoldoutBlindnessError("allowed model input structure changed")
    if allowed["case_id"] != CASE_ID:
        raise HoldoutBlindnessError("allowed model input case mismatch")
    model_input = allowed["semantic_judgment_input"]
    if not isinstance(model_input, dict) or set(model_input) != {
        "situation",
        "value_intent",
        "available_evidence_refs",
        "authority_context",
    }:
        raise HoldoutBlindnessError("semantic judgment input structure changed")

    adapter_input = SemanticJudgmentInput(
        input_ref=allowed["case_id"],
        situation=model_input["situation"],
        value_intent=model_input["value_intent"],
        available_evidence_refs=tuple(model_input["available_evidence_refs"]),
        authority_context=model_input["authority_context"],
    )
    adapter = OpenAISemanticJudgmentAdapter(
        OpenAIAdapterConfig(
            model_id="gpt-5.6-sol",
            reasoning_effort="medium",
            transport_max_retries=0,
        ),
        registry_path,
        canonical_path,
        EXPECTED_REGISTRY_HASH,
        transport=OpenAISDKTransport(),
        provider_schema_path=provider_path,
    )
    request, metadata = adapter.build_request(adapter_input)
    if metadata["canonical_schema_sha256"] != EXPECTED_CANONICAL_SCHEMA_HASH:
        raise HoldoutBlindnessError("canonical schema hash mismatch")
    if metadata["provider_schema_sha256"] != EXPECTED_PROVIDER_SCHEMA_HASH:
        raise HoldoutBlindnessError("provider schema hash mismatch")
    if file_sha256(provider_path) != EXPECTED_PROVIDER_ARTIFACT_HASH:
        raise HoldoutBlindnessError("provider artifact hash mismatch")

    sources = [
        {
            "source_class": "FROZEN_KERNEL",
            "reference": "runner/openai_semantic_adapter.py:OPENAI_INSTRUCTION_KERNEL",
            "sha256": hashlib.sha256(OPENAI_INSTRUCTION_KERNEL.encode("utf-8")).hexdigest(),
        },
        {
            "source_class": "FROZEN_PROVIDER_SCHEMA",
            "reference": "generated/openai_semantic_judgment_provider_schema.json",
            "sha256": file_sha256(provider_path),
            "provider_schema_sha256": metadata["provider_schema_sha256"],
        },
        {
            "source_class": "REGISTERED_VOCABULARY",
            "reference": "generated/registry_runtime.json",
            "sha256": file_sha256(registry_path),
        },
        {
            "source_class": "SEALED_ALLOWED_MODEL_INPUT",
            "reference": f"evals/holdout/cases/{CASE_ID}/allowed_model_input.json",
            "sha256": seal_payload(allowed),
        },
    ]
    manifest = {
        "artifact_type": "HOLDOUT_REQUEST_PROVENANCE_MANIFEST",
        "control_id": CONTROL_ID,
        "case_id": CASE_ID,
        "request_builder": "OpenAISemanticJudgmentAdapter.build_request",
        "request_sha256": seal_payload(request),
        "allowed_source_classes": sorted(ALLOWED_SOURCE_CLASSES),
        "sources": sources,
        "expectation_embedded": False,
        "sent_to_model": False,
        "limitations": [
            "Direct structured and substantial literal leakage checks do not detect arbitrary semantic paraphrase.",
            "Source labels are a local deterministic control, not independent cryptographic provenance attestation.",
        ],
    }
    return copy.deepcopy(request), manifest


def validate_request_blindness(
    request: dict[str, Any],
    manifest: dict[str, Any],
    experiment_root: Path,
) -> BlindnessValidation:
    reasons: set[str] = set()
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        reasons.add("PROVENANCE_MANIFEST_INVALID")
        source_classes: set[str] = set()
    else:
        source_classes = {
            item.get("source_class")
            for item in sources
            if isinstance(item, dict) and isinstance(item.get("source_class"), str)
        }
        if len(source_classes) != len(sources):
            reasons.add("PROVENANCE_SOURCE_DUPLICATE_OR_INVALID")
    if source_classes != ALLOWED_SOURCE_CLASSES:
        reasons.add("UNAPPROVED_SOURCE_CLASS")
    if source_classes & FORBIDDEN_SOURCE_CLASSES:
        reasons.add("FORBIDDEN_SOURCE_CLASS")
    if manifest.get("allowed_source_classes") != sorted(ALLOWED_SOURCE_CLASSES):
        reasons.add("ALLOWED_SOURCE_DECLARATION_CHANGED")
    if manifest.get("request_sha256") != seal_payload(request):
        reasons.add("REQUEST_HASH_MISMATCH")

    expected_request, expected_manifest = build_request_with_provenance(experiment_root)
    expected_sources = expected_manifest["sources"]
    if sources != expected_sources:
        reasons.add("SOURCE_REFERENCE_OR_HASH_MISMATCH")
    if seal_payload(expected_request) != expected_manifest["request_sha256"]:
        reasons.add("LOCAL_RECONSTRUCTION_MISMATCH")

    expectation = load_object(
        experiment_root
        / "evals"
        / "holdout"
        / "cases"
        / CASE_ID
        / "expectation.json"
    )
    other_cases = [
        load_object(
            experiment_root
            / "evals"
            / "holdout"
            / "cases"
            / case_id
            / "natural_situation.json"
        )["natural_situation"]
        for case_id in ("TH-CASE-002", "TH-CASE-003")
    ]
    reasons.update(case_specific_leakage_reasons(request, expectation, other_cases))

    structural_reasons = {
        reason
        for reason in reasons
        if reason
        in {
            "PROVENANCE_MANIFEST_INVALID",
            "PROVENANCE_SOURCE_DUPLICATE_OR_INVALID",
            "UNAPPROVED_SOURCE_CLASS",
            "FORBIDDEN_SOURCE_CLASS",
            "ALLOWED_SOURCE_DECLARATION_CHANGED",
            "REQUEST_HASH_MISMATCH",
            "SOURCE_REFERENCE_OR_HASH_MISMATCH",
            "LOCAL_RECONSTRUCTION_MISMATCH",
        }
    }
    leakage_reasons = reasons - structural_reasons
    return BlindnessValidation(
        state="PASS" if not reasons else "FAIL",
        contamination_state="CLEAR" if not reasons else "CONTAMINATION",
        structural_provenance_state="PASS" if not structural_reasons else "FAIL",
        case_specific_leakage_state="PASS" if not leakage_reasons else "FAIL",
        reasons=tuple(sorted(reasons)),
        limitations=(
            "Arbitrary paraphrased semantic leakage is not detected.",
            "Validation establishes local request provenance, not independent actor blindness.",
        ),
    )


def case_specific_leakage_reasons(
    request: dict[str, Any],
    expectation: dict[str, Any],
    other_case_situations: list[str],
) -> set[str]:
    reasons: set[str] = set()
    visible = provider_visible_without_schema(request)
    keys = _collect_normalized_keys(visible)
    leaked_keys = keys & FORBIDDEN_STRUCTURED_KEYS
    if leaked_keys:
        reasons.add("FORBIDDEN_CASE_SPECIFIC_FIELD")

    normalized_visible = _normalize(json.dumps(visible, ensure_ascii=False, sort_keys=True))
    constraints = expectation.get("constraints", {})
    if isinstance(constraints, dict):
        for values in constraints.values():
            if not isinstance(values, list):
                continue
            for clause in values:
                if not isinstance(clause, str):
                    continue
                normalized_clause = _normalize(clause)
                if len(normalized_clause) >= 40 and normalized_clause in normalized_visible:
                    reasons.add("SUBSTANTIAL_EXPECTATION_CLAUSE_COPY")
    for situation in other_case_situations:
        normalized_situation = _normalize(situation)
        if normalized_situation and normalized_situation in normalized_visible:
            reasons.add("OTHER_HOLDOUT_CASE_CONTENT")
    return reasons


def provider_visible_without_schema(request: dict[str, Any]) -> dict[str, Any]:
    visible = {
        "instructions": request.get("instructions"),
        "input": request.get("input"),
        "model": request.get("model"),
        "reasoning": request.get("reasoning"),
        "tools": request.get("tools"),
        "store": request.get("store"),
    }
    unexpected = set(request) - {
        "instructions",
        "input",
        "model",
        "reasoning",
        "tools",
        "store",
        "text",
    }
    if unexpected:
        visible["unexpected_request_fields"] = sorted(unexpected)
    return visible


def legacy_whole_request_hits(request: dict[str, Any]) -> tuple[str, ...]:
    serialized = json.dumps(request, ensure_ascii=False, sort_keys=True)
    tokens = (
        "REQUIRED",
        "FORBIDDEN",
        "ACCEPTABLE_OR_EVIDENCE_DEPENDENT",
        "HUMAN_VALIDATION_REQUIRED",
        "expectation artifact",
        "expected route",
        "expected trigger",
        "evaluator result",
        "desired answer",
    )
    return tuple(token for token in tokens if token in serialized)


def write_provenance_manifest(experiment_root: Path) -> dict[str, Any]:
    request, manifest = build_request_with_provenance(experiment_root)
    result = validate_request_blindness(request, manifest, experiment_root)
    if result.state != "PASS":
        raise HoldoutBlindnessError("locally reconstructed request failed blindness")
    target = (
        experiment_root
        / "evals"
        / "holdout"
        / "cases"
        / CASE_ID
        / "request_provenance_manifest.json"
    )
    target.write_bytes(canonical_json_bytes(manifest))
    return copy.deepcopy(manifest)


def _collect_normalized_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key).strip().lower())
            keys.update(_collect_normalized_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_collect_normalized_keys(child))
    elif isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return keys
        keys.update(_collect_normalized_keys(decoded))
    return keys


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = write_provenance_manifest(root)
    print(result["request_sha256"])
