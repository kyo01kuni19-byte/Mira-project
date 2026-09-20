from __future__ import annotations

import copy
import importlib.util
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from semantic_adapter import SemanticJudgmentInput, registry_sha256
from semantic_judgment import load_json
from openai_provider_schema import load_provider_schema_artifact


OPENAI_INSTRUCTION_KERNEL = """You are a Semantic Judgment Adapter. Produce only the supplied Semantic Judgment Contract JSON.
Observe material semantic factors. Distinguish observable evidence references, inferences, assumptions, and uncertainty.
Choose ROUTE, NO_ROUTE, or HUMAN_VALIDATION_REQUIRED. Use only the registered route and trigger semantics in the request.
proposed_initial_route must be one registered initial route token, never an edge ID or compound route path.
possible_secondary_dimensions are observational dimension candidates only; they do not select edges or direct traversal.
Potential Inter-Entity Impact is observational only. Do not create authority, approve impact, execute actions, use tools,
retrieve external information, browse, or provide hidden reasoning."""


class OpenAIAdapterError(Exception):
    def __init__(self, state: str, message: str, metadata: dict[str, Any] | None = None):
        super().__init__(message)
        self.state = state
        self.metadata = copy.deepcopy(metadata or {})


def sanitize_provider_error(exc: Exception) -> dict[str, Any]:
    """Return a deliberately narrow, non-payload-bearing provider error record."""

    def scalar(value: Any) -> str | int | None:
        if value is None or isinstance(value, (str, int)):
            return value
        return None

    http_status = scalar(getattr(exc, "status_code", None))
    exception_type = type(exc).__name__
    provider_type = scalar(getattr(exc, "type", None))
    error_type = provider_type or exception_type
    if http_status is None:
        message = f"OpenAI request failed with {exception_type}."
    else:
        message = f"OpenAI request failed with {exception_type} (HTTP {http_status})."
    return {
        "http_status": http_status,
        "error_type": error_type,
        "error_code": scalar(getattr(exc, "code", None)),
        "error_param": scalar(getattr(exc, "param", None)),
        "sanitized_error_message": message,
        "request_id": scalar(getattr(exc, "request_id", None)),
    }


@dataclass(frozen=True)
class OpenAIAdapterConfig:
    model_id: str
    reasoning_effort: str = "medium"
    api_key_env: str = "OPENAI_API_KEY"
    timeout_seconds: float = 30.0
    transport_max_retries: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id:
            raise ValueError("model_id must be a non-empty string")
        if not isinstance(self.api_key_env, str) or not self.api_key_env:
            raise ValueError("api_key_env must be a non-empty string")
        if self.reasoning_effort not in {
            "none",
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "max",
        }:
            raise ValueError("reasoning_effort is not supported by the installed SDK type")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not isinstance(self.transport_max_retries, int) or not 0 <= self.transport_max_retries <= 2:
            raise ValueError("transport_max_retries must be an integer from 0 to 2")

    def observable_identity(self) -> dict[str, Any]:
        return {
            "provider": "openai",
            "model_id": self.model_id,
            "reasoning_effort": self.reasoning_effort,
            "api_key_env": self.api_key_env,
            "timeout_seconds": self.timeout_seconds,
            "transport_max_retries": self.transport_max_retries,
            "retryable_failure_categories": ["transport_transient"],
            "non_retryable_failure_categories": [
                "semantic_disagreement",
                "wrong_route",
                "unsupported_trigger",
                "contract_schema_failure",
                "silent_assumption",
            ],
        }


@dataclass(frozen=True)
class OpenAIDryRunResult:
    state: str
    network_call_performed: bool
    credential_state: str
    sdk_state: str
    expected_registry_hash: str
    actual_registry_hash: str
    registry_hash_validation_state: str
    sanitized_request_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpenAIProviderResult:
    output: dict[str, Any]
    metadata: dict[str, Any]


class OpenAITransport(Protocol):
    requires_credential: bool

    def send(
        self,
        request: dict[str, Any],
        api_key: str | None,
        config: OpenAIAdapterConfig,
    ) -> dict[str, Any] | OpenAIProviderResult:
        ...


class OpenAISDKTransport:
    requires_credential = True

    def __init__(self) -> None:
        self.request_count = 0

    def send(
        self,
        request: dict[str, Any],
        api_key: str | None,
        config: OpenAIAdapterConfig,
    ) -> OpenAIProviderResult:
        if not sdk_available():
            raise OpenAIAdapterError(
                "NOT_CONFIGURED", "official OpenAI Python SDK is not installed"
            )
        if not api_key:
            raise OpenAIAdapterError("NOT_CONFIGURED", "OpenAI API key is not configured")

        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            timeout=config.timeout_seconds,
            max_retries=config.transport_max_retries,
        )
        if self.request_count != 0:
            raise OpenAIAdapterError(
                "REQUEST_LIMIT_REACHED", "the one-request transport boundary is exhausted"
            )
        self.request_count += 1
        transport_error: OpenAIAdapterError | None = None
        try:
            response = client.responses.create(**request)
        except Exception as exc:
            sanitized_error = sanitize_provider_error(exc)
            transport_error = OpenAIAdapterError(
                "TRANSPORT_ERROR",
                f"OpenAI request failed: {type(exc).__name__}",
                {
                    "request_count": self.request_count,
                    "retry_count": 0,
                    "error_category": type(exc).__name__,
                    **sanitized_error,
                },
            )
        if transport_error is not None:
            # Raise outside the provider exception scope so raw SDK response data is
            # not retained through Python exception chaining.
            raise transport_error
        output_text = response.output_text
        usage = getattr(response, "usage", None)
        metadata = {
            "request_count": self.request_count,
            "retry_count": 0,
            "response_id": getattr(response, "id", None),
            "token_usage": {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
        }
        try:
            output = json.loads(output_text)
        except (TypeError, json.JSONDecodeError) as exc:
            raise OpenAIAdapterError(
                "PROVIDER_OUTPUT_INVALID",
                "OpenAI structured output was not valid JSON",
                metadata,
            ) from exc
        if not isinstance(output, dict):
            raise OpenAIAdapterError(
                "PROVIDER_OUTPUT_INVALID",
                "OpenAI structured output must be an object",
                metadata,
            )
        return OpenAIProviderResult(output=output, metadata=metadata)


class OpenAISemanticJudgmentAdapter:
    adapter_id = "openai.semantic_judgment.v0.1"

    def __init__(
        self,
        config: OpenAIAdapterConfig,
        registry_path: Path,
        contract_schema_path: Path,
        expected_registry_hash: str,
        *,
        transport: OpenAITransport | None = None,
        provider_schema_path: Path | None = None,
    ):
        self.config = config
        self.registry_path = registry_path
        self.contract_schema_path = contract_schema_path
        self.expected_registry_hash = expected_registry_hash
        self.transport = transport or OpenAISDKTransport()
        self.provider_schema_path = provider_schema_path or (
            contract_schema_path.parents[1]
            / "generated"
            / "openai_semantic_judgment_provider_schema.json"
        )
        self.last_call_metadata: dict[str, Any] = {
            "request_count": 0,
            "retry_count": 0,
        }
        self.last_provider_output: dict[str, Any] | None = None

    def observable_metadata(self) -> dict[str, Any]:
        metadata = self.config.observable_identity()
        metadata.update(
            {
                "expected_registry_hash": self.expected_registry_hash,
                "structured_output_contract": "portable_mira.semantic_judgment_contract.v0.1a",
                "tools_enabled": False,
                "external_retrieval_enabled": False,
            }
        )
        return metadata

    def judge(self, adapter_input: SemanticJudgmentInput) -> dict[str, Any]:
        request, _ = self.build_request(adapter_input)
        api_key: str | None = None
        if self.transport.requires_credential:
            api_key = os.environ.get(self.config.api_key_env)
            if not api_key:
                raise OpenAIAdapterError(
                    "NOT_CONFIGURED",
                    f"required environment variable is absent: {self.config.api_key_env}",
                    self.observable_metadata(),
                )
            if not sdk_available():
                raise OpenAIAdapterError(
                    "NOT_CONFIGURED",
                    "official OpenAI Python SDK is not installed",
                    self.observable_metadata(),
                )

        try:
            transport_result = self.transport.send(request, api_key, self.config)
        except OpenAIAdapterError as exc:
            self.last_call_metadata = copy.deepcopy(exc.metadata)
            raise
        if isinstance(transport_result, OpenAIProviderResult):
            output = transport_result.output
            self.last_call_metadata = copy.deepcopy(transport_result.metadata)
        else:
            output = transport_result
            self.last_call_metadata = {
                "request_count": getattr(self.transport, "calls", 1),
                "retry_count": 0,
            }
        if not isinstance(output, dict):
            raise OpenAIAdapterError(
                "PROVIDER_OUTPUT_INVALID", "provider output must be a contract object"
            )
        self.last_provider_output = copy.deepcopy(output)
        return copy.deepcopy(output)

    def build_request(
        self, adapter_input: SemanticJudgmentInput
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        actual_hash = registry_sha256(self.registry_path)
        if actual_hash != self.expected_registry_hash:
            raise OpenAIAdapterError(
                "REGISTRY_HASH_MISMATCH",
                "runtime registry does not match expected SHA-256",
                {
                    "expected_registry_hash": self.expected_registry_hash,
                    "actual_registry_hash": actual_hash,
                },
            )
        registry = load_json(self.registry_path)
        provider_compilation = load_provider_schema_artifact(
            self.provider_schema_path, self.contract_schema_path, self.registry_path
        )
        schema = provider_compilation.provider_schema
        registered_semantics = _registered_semantics(registry)
        input_payload = {
            "semantic_judgment_input": adapter_input.to_dict(),
            "registered_semantics": registered_semantics,
            "output_requirement": "Return only Semantic Judgment Contract v0.1a JSON.",
        }
        request = {
            "model": self.config.model_id,
            "instructions": OPENAI_INSTRUCTION_KERNEL,
            "input": json.dumps(input_payload, ensure_ascii=False, sort_keys=True),
            "reasoning": {"effort": self.config.reasoning_effort},
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "portable_mira_semantic_judgment_v0_1a",
                    "schema": schema,
                    "strict": True,
                }
            },
            "tools": [],
            "store": False,
        }
        metadata = {
            **self.observable_metadata(),
            "actual_registry_hash": actual_hash,
            "registry_hash_validation_state": "PASS",
            "canonical_schema_sha256": provider_compilation.canonical_schema_sha256,
            "provider_schema_sha256": provider_compilation.provider_schema_sha256,
            "provider_schema_compiler_id": provider_compilation.compiler_id,
            "provider_schema_artifact": str(self.provider_schema_path),
            "provider_schema_registry_sha256": provider_compilation.registry_sha256,
            "initial_route_vocabulary": list(
                provider_compilation.initial_route_vocabulary
            ),
            "semantic_dimension_vocabulary": list(
                provider_compilation.semantic_dimension_vocabulary
            ),
            "input_ref": adapter_input.input_ref,
            "input_fields": sorted(adapter_input.to_dict()),
            "normal_route_count": len(registered_semantics["normal_routes"]),
            "request_count": 1,
            "network_call_performed": False,
            "credential_in_request": False,
            "hidden_reasoning_requested": False,
        }
        return request, metadata

    def dry_run(self, adapter_input: SemanticJudgmentInput) -> OpenAIDryRunResult:
        _, metadata = self.build_request(adapter_input)
        return OpenAIDryRunResult(
            state="DRY_RUN_READY",
            network_call_performed=False,
            credential_state="NOT_REQUIRED_FOR_DRY_RUN",
            sdk_state="AVAILABLE" if sdk_available() else "NOT_INSTALLED",
            expected_registry_hash=self.expected_registry_hash,
            actual_registry_hash=metadata["actual_registry_hash"],
            registry_hash_validation_state=metadata[
                "registry_hash_validation_state"
            ],
            sanitized_request_metadata=metadata,
        )


def sdk_available() -> bool:
    return importlib.util.find_spec("openai") is not None


def _registered_semantics(registry: Any) -> dict[str, Any]:
    if not isinstance(registry, dict):
        raise OpenAIAdapterError("REGISTRY_INVALID", "runtime registry must be an object")
    routing = registry.get("routing")
    if not isinstance(routing, dict) or not isinstance(routing.get("normal_edges"), list):
        raise OpenAIAdapterError("REGISTRY_INVALID", "runtime routing registry is invalid")
    normal_routes = []
    for edge in routing["normal_edges"]:
        if not isinstance(edge, dict):
            raise OpenAIAdapterError("REGISTRY_INVALID", "runtime edge must be an object")
        normal_routes.append(
            {"from": edge.get("from"), "trigger": edge.get("trigger"), "to": edge.get("to")}
        )
    value_fit = routing.get("value_fit_reentry")
    value_fit_context = None
    if isinstance(value_fit, dict):
        value_fit_context = {
            "trigger": value_fit.get("trigger"),
            "to": value_fit.get("to"),
            "normal_router_executable": False,
        }
    return {
        "normal_routes": normal_routes,
        "value_fit_reentry": value_fit_context,
    }
