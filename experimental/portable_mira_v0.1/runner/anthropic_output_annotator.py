from __future__ import annotations

import copy
import importlib.util
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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
Describe semantic dimensions, impact categories, and whether escalation is present. Do not decide overall quality or PASS/FAIL, create authority, approve or block execution, alter the source output, retrieve facts, use tools, or provide hidden reasoning."""


class AnthropicAnnotatorError(Exception):
    def __init__(self, state: str, message: str, metadata: dict[str, Any] | None = None):
        super().__init__(message)
        self.state = state
        self.metadata = copy.deepcopy(metadata or {})


@dataclass(frozen=True)
class AnthropicAnnotatorConfig:
    model_id: str
    max_tokens: int = 2048
    temperature: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id:
            raise ValueError("model_id must be a non-empty string")
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")
        if not isinstance(self.temperature, (int, float)) or not 0 <= self.temperature <= 1:
            raise ValueError("temperature must be between 0 and 1")

    def observable_identity(self) -> dict[str, Any]:
        return {
            "provider": "anthropic",
            "model_id": self.model_id,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
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

    def __init__(self, config: AnthropicAnnotatorConfig, schema_path: Path):
        self.config = config
        self.schema_path = schema_path

    def observable_metadata(self) -> dict[str, Any]:
        metadata = self.config.observable_identity()
        metadata.update(
            {
                "annotator_id": self.annotator_id,
                "annotation_contract": "portable_mira.output_annotation_contract.v0.1",
                "annotation_schema_sha256": file_sha256(self.schema_path),
                "independence_claim": "DIFFERENT_PROVIDER_NOT_INDEPENDENT_GROUND_TRUTH",
            }
        )
        return metadata

    def build_dry_run(self, annotation_input: OutputAnnotationInput) -> AnthropicDryRunResult:
        validate_annotation_input(annotation_input, self.schema_path)
        schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        provider_payload = annotation_input.to_provider_payload()
        request = {
            "model": self.config.model_id,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "system": ANTHROPIC_ANNOTATION_KERNEL,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "annotation_input": provider_payload,
                            "output_contract_schema": schema,
                            "output_requirement": "Return only canonical Output Annotation Contract JSON.",
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                }
            ],
            "tools": [],
        }
        validate_blind_input_fields(request)
        return AnthropicDryRunResult(
            state="DRY_RUN_ONLY",
            sdk_state=anthropic_sdk_state(),
            network_call_performed=False,
            credential_accessed=False,
            request=request,
            observable_configuration=self.observable_metadata(),
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
