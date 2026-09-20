from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from anthropic_provider_schema import (
    SDK_LOCAL_ACCEPTANCE_PRINCIPLE,
    bind_provider_schema,
    canonical_json_bytes,
    load_provider_schema_artifact,
)

from output_annotator import (
    OutputAnnotationError,
    OutputAnnotationInput,
    file_sha256,
    validate_annotation,
    validate_annotation_input,
    validate_blind_input_fields,
)


ANTHROPIC_ANNOTATION_KERNEL = """You are an Output Annotator. Describe only the supplied Natural Situation and preserved observable Semantic Agent output using the supplied Annotation Contract.
Keep evidence references, presented statements, inferences, assumptions, and unknowns distinct. Mark uncertainty rather than forcing certainty.
Describe semantic dimensions, impact categories, and whether escalation is present. Return every contract field, but keep values concise: use existing reference identifiers and short labels or clauses, do not restate the full input, and do not duplicate the same explanation across categories. Use empty lists when no supported item exists and uncertainty fields for concise uncertainty.
Do not decide overall quality or PASS/FAIL, create authority, approve or block execution, alter the source output, retrieve facts, use tools, or provide hidden reasoning."""


class AnthropicAnnotatorError(Exception):
    def __init__(self, state: str, message: str, metadata: dict[str, Any] | None = None):
        super().__init__(message)
        self.state = state
        self.metadata = copy.deepcopy(metadata or {})


@dataclass(frozen=True)
class AnthropicAnnotatorConfig:
    model_id: str
    max_tokens: int = 2048

    def __post_init__(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id:
            raise ValueError("model_id must be a non-empty string")
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")

    def observable_identity(self) -> dict[str, Any]:
        return {
            "provider": "anthropic",
            "model_id": self.model_id,
            "max_tokens": self.max_tokens,
            "temperature_supported_by_installed_sdk": False,
            "tools_enabled": False,
            "web_enabled": False,
            "retrieval_enabled": False,
            "external_actions_enabled": False,
            "hidden_reasoning_requested": False,
            "provider_server_compatibility": "UNKNOWN",
        }


@dataclass(frozen=True)
class AnthropicDryRunResult:
    state: str
    sdk_state: str
    network_call_performed: bool
    credential_accessed: bool
    request: dict[str, Any]
    observable_configuration: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AnthropicOutputAnnotator:
    annotator_id = "anthropic.output_annotator.candidate.v0.1"

    def __init__(
        self,
        config: AnthropicAnnotatorConfig,
        schema_path: Path,
        provider_artifact_path: Path | None = None,
    ):
        self.config = config
        self.schema_path = schema_path
        self.provider_artifact_path = provider_artifact_path or (
            schema_path.parents[1]
            / "generated"
            / "anthropic_output_annotation_provider_schema.json"
        )

    def observable_metadata(self) -> dict[str, Any]:
        metadata = self.config.observable_identity()
        metadata.update(
            {
                "annotator_id": self.annotator_id,
                "annotation_contract": "portable_mira.output_annotation_contract.v0.1",
                "annotation_schema_sha256": file_sha256(self.schema_path),
                "independence_claim": "DIFFERENT_PROVIDER_NOT_INDEPENDENT_GROUND_TRUTH",
                "sdk_acceptance_principle": SDK_LOCAL_ACCEPTANCE_PRINCIPLE,
                "canonical_post_validation_required": True,
            }
        )
        return metadata

    def build_dry_run(self, annotation_input: OutputAnnotationInput) -> AnthropicDryRunResult:
        validate_annotation_input(annotation_input, self.schema_path)
        compilation = load_provider_schema_artifact(
            self.provider_artifact_path, self.schema_path
        )
        provider_schema = bind_provider_schema(
            compilation.provider_schema,
            case_id=annotation_input.case_id,
            annotator_id=self.annotator_id,
            case_sha256=annotation_input.case_sha256,
            raw_output_sha256=annotation_input.raw_output_sha256,
            annotation_schema_sha256=annotation_input.annotation_schema_sha256,
        )
        request = {
            "model": self.config.model_id,
            "max_tokens": self.config.max_tokens,
            "system": ANTHROPIC_ANNOTATION_KERNEL,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "natural_situation": annotation_input.natural_situation,
                            "preserved_semantic_agent_output": (
                                annotation_input.preserved_semantic_agent_output
                            ),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                }
            ],
            "output_config": {
                "format": {
                    "type": "json_schema",
                    "schema": provider_schema,
                }
            },
        }
        validate_blind_input_fields(request)
        return AnthropicDryRunResult(
            state="DRY_RUN_ONLY",
            sdk_state=anthropic_sdk_state(),
            network_call_performed=False,
            credential_accessed=False,
            request=request,
            observable_configuration={
                **self.observable_metadata(),
                "anthropic_sdk_version": compilation.sdk_version,
                "provider_schema_sha256": compilation.provider_schema_sha256,
                "bound_provider_schema_sha256": hashlib.sha256(
                    canonical_json_bytes(provider_schema)
                ).hexdigest(),
            },
        )

    def annotate(self, annotation_input: OutputAnnotationInput) -> dict[str, Any]:
        self.build_dry_run(annotation_input)
        if anthropic_sdk_state() == "NOT_CONFIGURED":
            raise AnthropicAnnotatorError(
                "DEPENDENCY_REQUIRED",
                "official Anthropic Python SDK is not installed; raw HTTP fallback is forbidden",
                self.observable_metadata(),
            )
        raise AnthropicAnnotatorError(
            "LIVE_EXECUTION_NOT_AUTHORIZED",
            "Anthropic live annotation is not authorized by this adapter candidate",
            self.observable_metadata(),
        )

    def validate_provider_output(
        self, output: Any, *, annotation_input: OutputAnnotationInput
    ) -> dict[str, Any]:
        try:
            validate_annotation_input(annotation_input, self.schema_path)
            return validate_annotation(
                output,
                expected_case_id=annotation_input.case_id,
                expected_bindings={
                    "case_sha256": annotation_input.case_sha256,
                    "raw_output_sha256": annotation_input.raw_output_sha256,
                    "annotation_schema_sha256": annotation_input.annotation_schema_sha256,
                },
            )
        except OutputAnnotationError as exc:
            raise AnthropicAnnotatorError(
                "CANONICAL_VALIDATION_FAILED", str(exc), self.observable_metadata()
            ) from exc


def anthropic_sdk_state() -> str:
    return "CONFIGURED" if importlib.util.find_spec("anthropic") else "NOT_CONFIGURED"


def parse_provider_annotation_text(raw_text: str, *, stop_reason: str) -> dict[str, Any]:
    if stop_reason == "max_tokens":
        raise AnthropicAnnotatorError(
            "TRUNCATED_OUTPUT",
            "provider output reached max_tokens; partial output is rejected",
        )
    if stop_reason != "end_turn":
        raise AnthropicAnnotatorError(
            "INCOMPLETE_OUTPUT",
            f"provider output did not complete normally: {stop_reason}",
        )
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise AnthropicAnnotatorError(
            "STRUCTURED_OUTPUT_INVALID",
            "provider output is not complete JSON; repair is forbidden",
        ) from exc
    if not isinstance(parsed, dict):
        raise AnthropicAnnotatorError(
            "STRUCTURED_OUTPUT_INVALID", "provider output must be a JSON object"
        )
    return parsed
