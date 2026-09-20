from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


ANNOTATION_KEYS = {
    "annotation_metadata",
    "evidence_discipline",
    "semantic_sparsity",
    "impact_discipline",
    "human_burden",
}
EVIDENCE_KEYS = {
    "evidence_references",
    "presented_or_observed_statements",
    "inferences",
    "assumptions",
    "unknowns",
    "annotator_uncertain",
}
SPARSITY_KEYS = {
    "materially_relevant_dimensions",
    "plausible_but_unnecessary_dimensions",
    "potentially_missing_dimensions",
    "annotator_uncertain",
}
IMPACT_KEYS = {
    "mentioned_entities",
    "operationally_affected",
    "represented_or_delegated_actors",
    "independent_interest_candidates",
    "potential_material_impact_candidates",
    "annotator_uncertain",
}
FORBIDDEN_INPUT_FIELDS = {
    "expectation",
    "expectations",
    "expectation_artifact",
    "sealed_expectations",
    "expected_route",
    "expected_routes",
    "expected_trigger",
    "expected_triggers",
    "expected_diagnostic",
    "expected_diagnostics",
    "evaluator_result",
    "deterministic_evaluator_result",
    "desired_answer",
    "disagreement_review_conclusion",
}


class OutputAnnotationError(Exception):
    """Annotation contract, blindness, or immutable-reference failure."""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def payload_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class OutputAnnotationInput:
    case_id: str
    natural_situation: str
    preserved_semantic_agent_output: dict[str, Any]
    case_sha256: str
    raw_output_sha256: str
    annotation_schema_sha256: str
    governance_baseline_commit: str
    evaluation_baseline_commit: str

    def __post_init__(self) -> None:
        if not isinstance(self.case_id, str) or not self.case_id:
            raise ValueError("case_id must be a non-empty string")
        if not isinstance(self.natural_situation, str) or not self.natural_situation:
            raise ValueError("natural_situation must be a non-empty string")
        if not isinstance(self.preserved_semantic_agent_output, dict):
            raise ValueError("preserved_semantic_agent_output must be an object")
        for field in (
            "case_sha256",
            "raw_output_sha256",
            "annotation_schema_sha256",
            "governance_baseline_commit",
            "evaluation_baseline_commit",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field} must be a non-empty string")

    def case_payload(self) -> dict[str, str]:
        return {"case_id": self.case_id, "natural_situation": self.natural_situation}

    def to_provider_payload(self) -> dict[str, Any]:
        return {
            "case": copy.deepcopy(self.case_payload()),
            "preserved_semantic_agent_output": copy.deepcopy(
                self.preserved_semantic_agent_output
            ),
            "immutable_references": {
                "case_sha256": self.case_sha256,
                "raw_output_sha256": self.raw_output_sha256,
                "annotation_schema_sha256": self.annotation_schema_sha256,
                "governance_baseline_commit": self.governance_baseline_commit,
                "evaluation_baseline_commit": self.evaluation_baseline_commit,
            },
        }


@runtime_checkable
class OutputAnnotator(Protocol):
    annotator_id: str

    def annotate(self, annotation_input: OutputAnnotationInput) -> dict[str, Any]:
        """Return only a canonical Output Annotation Contract object."""


class FixtureOutputAnnotator:
    """Development-only annotator backed by predetermined local fixtures."""

    annotator_id = "fixture.output_annotator.development.v0.1"

    def __init__(self, fixtures: dict[str, dict[str, Any]], schema_path: Path):
        self._fixtures = copy.deepcopy(fixtures)
        self.schema_path = schema_path

    def annotate(self, annotation_input: OutputAnnotationInput) -> dict[str, Any]:
        validate_annotation_input(annotation_input, self.schema_path)
        if annotation_input.case_id not in self._fixtures:
            raise OutputAnnotationError("unknown development annotation fixture")
        annotation = copy.deepcopy(self._fixtures[annotation_input.case_id])
        return validate_annotation(
            annotation,
            expected_case_id=annotation_input.case_id,
            expected_bindings={
                "case_sha256": annotation_input.case_sha256,
                "raw_output_sha256": annotation_input.raw_output_sha256,
                "annotation_schema_sha256": annotation_input.annotation_schema_sha256,
            },
        )


def validate_annotation_input(
    annotation_input: OutputAnnotationInput, schema_path: Path
) -> None:
    validate_blind_input_fields(annotation_input.to_provider_payload())
    if payload_sha256(annotation_input.case_payload()) != annotation_input.case_sha256:
        raise OutputAnnotationError("case SHA-256 mismatch")
    if (
        payload_sha256(annotation_input.preserved_semantic_agent_output)
        != annotation_input.raw_output_sha256
    ):
        raise OutputAnnotationError("raw Semantic Agent output SHA-256 mismatch")
    if file_sha256(schema_path) != annotation_input.annotation_schema_sha256:
        raise OutputAnnotationError("annotation schema SHA-256 mismatch")


def validate_blind_input_fields(value: Any, path: str = "input") -> None:
    if isinstance(value, dict):
        forbidden = sorted(set(value) & FORBIDDEN_INPUT_FIELDS)
        if forbidden:
            raise OutputAnnotationError(
                f"forbidden annotator input field(s) at {path}: {', '.join(forbidden)}"
            )
        for key, child in value.items():
            validate_blind_input_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_blind_input_fields(child, f"{path}[{index}]")


def validate_annotation(
    annotation: Any,
    *,
    expected_case_id: str | None = None,
    expected_bindings: dict[str, str] | None = None,
) -> dict[str, Any]:
    root = _object(annotation, "annotation")
    _exact_keys(root, ANNOTATION_KEYS, "annotation")
    metadata = _object(root["annotation_metadata"], "annotation_metadata")
    _exact_keys(
        metadata,
        {
            "case_id",
            "annotator_id",
            "expectation_visible",
            "case_sha256",
            "raw_output_sha256",
            "annotation_schema_sha256",
        },
        "annotation_metadata",
    )
    _non_empty_string(metadata["case_id"], "annotation_metadata.case_id")
    _non_empty_string(metadata["annotator_id"], "annotation_metadata.annotator_id")
    if metadata["expectation_visible"] is not False:
        raise OutputAnnotationError("annotation_metadata.expectation_visible must be false")
    if expected_case_id is not None and metadata["case_id"] != expected_case_id:
        raise OutputAnnotationError("annotation case_id does not match input case_id")
    for field in ("case_sha256", "raw_output_sha256", "annotation_schema_sha256"):
        _sha256(metadata[field], f"annotation_metadata.{field}")
    if expected_bindings is not None:
        for field, expected in expected_bindings.items():
            if metadata.get(field) != expected:
                raise OutputAnnotationError(f"annotation {field} does not match input binding")

    evidence = _object(root["evidence_discipline"], "evidence_discipline")
    _exact_keys(evidence, EVIDENCE_KEYS, "evidence_discipline")
    sparsity = _object(root["semantic_sparsity"], "semantic_sparsity")
    _exact_keys(sparsity, SPARSITY_KEYS, "semantic_sparsity")
    impact = _object(root["impact_discipline"], "impact_discipline")
    _exact_keys(impact, IMPACT_KEYS, "impact_discipline")
    for section_name, section in (
        ("evidence_discipline", evidence),
        ("semantic_sparsity", sparsity),
        ("impact_discipline", impact),
    ):
        for key, value in section.items():
            _string_list(value, f"{section_name}.{key}")

    burden = _object(root["human_burden"], "human_burden")
    _exact_keys(
        burden,
        {"escalation_present", "escalation_basis", "escalation_uncertain"},
        "human_burden",
    )
    if not isinstance(burden["escalation_present"], bool):
        raise OutputAnnotationError("human_burden.escalation_present must be boolean")
    _string_list(burden["escalation_basis"], "human_burden.escalation_basis")
    if not isinstance(burden["escalation_uncertain"], bool):
        raise OutputAnnotationError("human_burden.escalation_uncertain must be boolean")
    return copy.deepcopy(root)


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise OutputAnnotationError(f"{path} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], path: str) -> None:
    missing = sorted(expected - value.keys())
    unexpected = sorted(value.keys() - expected)
    if missing:
        raise OutputAnnotationError(f"{path} missing required field(s): {', '.join(missing)}")
    if unexpected:
        raise OutputAnnotationError(f"{path} has forbidden field(s): {', '.join(unexpected)}")


def _non_empty_string(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value:
        raise OutputAnnotationError(f"{path} must be a non-empty string")


def _string_list(value: Any, path: str) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise OutputAnnotationError(f"{path} must be a list of strings")


def _sha256(value: Any, path: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise OutputAnnotationError(f"{path} must be a lowercase SHA-256 hex digest")
