from __future__ import annotations

import copy
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from semantic_judgment import (
    SemanticJudgmentError,
    evaluate_judgment,
    load_json,
    validate_contract,
    validate_registry_binding,
)


class SemanticAdapterError(Exception):
    """Adapter invocation or integration-stage failure."""

    def __init__(self, message: str, diagnostics: dict[str, str]):
        super().__init__(message)
        self.diagnostics = copy.deepcopy(diagnostics)


@dataclass(frozen=True)
class SemanticJudgmentInput:
    input_ref: str
    situation: str
    value_intent: str | None = None
    available_evidence_refs: tuple[str, ...] = ()
    authority_context: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.input_ref, str) or not self.input_ref:
            raise ValueError("input_ref must be a non-empty string")
        if not isinstance(self.situation, str) or not self.situation:
            raise ValueError("situation must be a non-empty string")
        if self.value_intent is not None and not isinstance(self.value_intent, str):
            raise ValueError("value_intent must be a string or null")
        if not isinstance(self.available_evidence_refs, tuple) or not all(
            isinstance(item, str) for item in self.available_evidence_refs
        ):
            raise ValueError("available_evidence_refs must be a tuple of strings")
        if self.authority_context is not None and not isinstance(self.authority_context, str):
            raise ValueError("authority_context must be a string or null")

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_ref": self.input_ref,
            "situation": self.situation,
            "value_intent": self.value_intent,
            "available_evidence_refs": list(self.available_evidence_refs),
            "authority_context": self.authority_context,
        }


@runtime_checkable
class SemanticJudgmentAdapter(Protocol):
    adapter_id: str

    def judge(self, adapter_input: SemanticJudgmentInput) -> dict[str, Any]:
        """Return only a Semantic Judgment Contract v0.1a object."""


@dataclass(frozen=True)
class AdapterIntegrationResult:
    adapter_id: str
    adapter_metadata: dict[str, Any]
    input_ref: str
    semantic_judgment_ref: str
    expected_registry_hash: str | None
    actual_registry_hash: str
    registry_hash_validation_state: str
    adapter_result_received: str
    contract_validation_state: str
    trigger_registry_validation_state: str
    runtime_resolution_state: str
    authority_boundary_state: str
    inter_entity_impact_state: str
    integration_result: str
    adapter_proposed_route: str | None
    runtime_resolved_route: str | None
    trigger_candidates: list[str]
    cross_routes: list[str]
    knowledge_addresses_used: list[str]
    potential_inter_entity_impact: dict[str, Any]
    observable_state: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FixtureSemanticJudgmentAdapter:
    """Development-only adapter backed by predetermined non-holdout fixtures."""

    adapter_id = "fixture.semantic_judgment.development.v0.1"

    def __init__(self, fixture_path: Path):
        fixture_set = load_json(fixture_path)
        if not isinstance(fixture_set, dict):
            raise SemanticAdapterError("fixture set must be an object", _diagnostics())
        if fixture_set.get("classification") != "DEVELOPMENT_REGRESSION_NOT_HOLDOUT":
            raise SemanticAdapterError(
                "fixture adapter accepts only development/regression fixtures",
                _diagnostics(),
            )
        raw_cases = fixture_set.get("cases")
        if not isinstance(raw_cases, list):
            raise SemanticAdapterError("fixture cases must be a list", _diagnostics())

        self._cases: dict[str, dict[str, Any]] = {}
        for index, case in enumerate(raw_cases):
            if not isinstance(case, dict):
                raise SemanticAdapterError(
                    f"fixture case {index} must be an object", _diagnostics()
                )
            case_id = case.get("case_id")
            situation = case.get("situation")
            judgment = case.get("semantic_judgment")
            if not isinstance(case_id, str) or not case_id:
                raise SemanticAdapterError(
                    f"fixture case {index} has invalid case_id", _diagnostics()
                )
            if case_id in self._cases:
                raise SemanticAdapterError(
                    f"duplicate fixture case_id: {case_id}", _diagnostics()
                )
            if not isinstance(situation, str) or not isinstance(judgment, dict):
                raise SemanticAdapterError(
                    f"fixture case {case_id} is incomplete", _diagnostics()
                )
            self._cases[case_id] = {
                "situation": situation,
                "semantic_judgment": copy.deepcopy(judgment),
            }

    def judge(self, adapter_input: SemanticJudgmentInput) -> dict[str, Any]:
        if adapter_input.input_ref not in self._cases:
            raise SemanticAdapterError(
                f"unknown development fixture: {adapter_input.input_ref}",
                _diagnostics(adapter_result_received="FAIL"),
            )
        case = self._cases[adapter_input.input_ref]
        if adapter_input.situation != case["situation"]:
            raise SemanticAdapterError(
                f"fixture situation mismatch: {adapter_input.input_ref}",
                _diagnostics(adapter_result_received="FAIL"),
            )
        return copy.deepcopy(case["semantic_judgment"])


def integrate_adapter(
    adapter: SemanticJudgmentAdapter,
    adapter_input: SemanticJudgmentInput,
    registry_path: Path,
    *,
    expected_registry_hash: str | None = None,
    authority_state: str = "CLEAR",
    impact_state: str = "CLEAR",
) -> AdapterIntegrationResult:
    diagnostics = _diagnostics()
    adapter_id = getattr(adapter, "adapter_id", None)
    if not isinstance(adapter_id, str) or not adapter_id:
        raise SemanticAdapterError("adapter_id must be a non-empty string", diagnostics)
    metadata_provider = getattr(adapter, "observable_metadata", None)
    adapter_metadata = metadata_provider() if callable(metadata_provider) else {}
    if not isinstance(adapter_metadata, dict):
        raise SemanticAdapterError("adapter observable metadata must be an object", diagnostics)

    actual_registry_hash = registry_sha256(registry_path)
    _verify_registry_hash(expected_registry_hash, actual_registry_hash, diagnostics)

    try:
        adapter_output = adapter.judge(adapter_input)
    except SemanticAdapterError:
        raise
    except Exception as exc:
        diagnostics["adapter_result_received"] = "FAIL"
        raise SemanticAdapterError("adapter invocation failed", diagnostics) from exc
    diagnostics["adapter_result_received"] = "PASS"

    try:
        validated = validate_contract(adapter_output)
    except SemanticJudgmentError as exc:
        diagnostics["contract_validation_state"] = "FAIL"
        raise SemanticAdapterError(f"contract validation failed: {exc}", diagnostics) from exc
    diagnostics["contract_validation_state"] = "PASS"

    try:
        registry = load_json(registry_path)
        validate_registry_binding(validated, registry)
    except SemanticJudgmentError as exc:
        diagnostics["trigger_registry_validation_state"] = "FAIL"
        raise SemanticAdapterError(
            f"trigger registry validation failed: {exc}", diagnostics
        ) from exc
    diagnostics["trigger_registry_validation_state"] = "PASS"

    runtime_registry_hash = registry_sha256(registry_path)
    _verify_registry_hash(expected_registry_hash, runtime_registry_hash, diagnostics)
    if runtime_registry_hash != actual_registry_hash:
        diagnostics["registry_hash_validation_state"] = "FAIL"
        raise SemanticAdapterError(
            "runtime registry changed during integration", diagnostics
        )

    try:
        runtime_result = evaluate_judgment(
            adapter_input.input_ref,
            validated,
            registry_path,
            authority_state=authority_state,
            impact_state=impact_state,
        )
    except SemanticJudgmentError as exc:
        diagnostics["runtime_resolution_state"] = "FAIL"
        raise SemanticAdapterError(f"runtime resolution failed: {exc}", diagnostics) from exc

    diagnostics["runtime_resolution_state"] = runtime_result.runtime_resolution
    diagnostics["boundary_state"] = runtime_result.boundary_state
    diagnostics["integration_result"] = runtime_result.final_integration_result
    routing = validated["routing_judgment"]
    trigger_candidates = [
        candidate["trigger_id"] for candidate in routing["trigger_candidates"]
    ]
    judgment_ref = f"{adapter_id}:{adapter_input.input_ref}"
    observable = {
        "adapter_id": adapter_id,
        "adapter_metadata": copy.deepcopy(adapter_metadata),
        "input_ref": adapter_input.input_ref,
        "semantic_judgment_ref": judgment_ref,
        "expected_registry_hash": expected_registry_hash,
        "actual_registry_hash": actual_registry_hash,
        "registry_hash_validation_state": diagnostics[
            "registry_hash_validation_state"
        ],
        "adapter_result_received": diagnostics["adapter_result_received"],
        "adapter_proposed_route": routing["proposed_initial_route"],
        "trigger_candidates": trigger_candidates,
        "contract_validation_state": diagnostics["contract_validation_state"],
        "trigger_registry_validation_state": diagnostics[
            "trigger_registry_validation_state"
        ],
        "runtime_resolution_state": diagnostics["runtime_resolution_state"],
        "runtime_resolved_route": runtime_result.runtime_resolved_route,
        "cross_routes": list(runtime_result.cross_routes),
        "knowledge_addresses_used": list(runtime_result.knowledge_addresses),
        "authority_boundary_state": authority_state,
        "inter_entity_impact_state": impact_state,
        "integration_result": runtime_result.final_integration_result,
    }
    return AdapterIntegrationResult(
        adapter_id=adapter_id,
        adapter_metadata=copy.deepcopy(adapter_metadata),
        input_ref=adapter_input.input_ref,
        semantic_judgment_ref=judgment_ref,
        expected_registry_hash=expected_registry_hash,
        actual_registry_hash=actual_registry_hash,
        registry_hash_validation_state=diagnostics[
            "registry_hash_validation_state"
        ],
        adapter_result_received=diagnostics["adapter_result_received"],
        contract_validation_state=diagnostics["contract_validation_state"],
        trigger_registry_validation_state=diagnostics[
            "trigger_registry_validation_state"
        ],
        runtime_resolution_state=diagnostics["runtime_resolution_state"],
        authority_boundary_state=authority_state,
        inter_entity_impact_state=impact_state,
        integration_result=runtime_result.final_integration_result,
        adapter_proposed_route=routing["proposed_initial_route"],
        runtime_resolved_route=runtime_result.runtime_resolved_route,
        trigger_candidates=trigger_candidates,
        cross_routes=list(runtime_result.cross_routes),
        knowledge_addresses_used=list(runtime_result.knowledge_addresses),
        potential_inter_entity_impact=copy.deepcopy(
            validated["semantic_observation"]["potential_inter_entity_impact"]
        ),
        observable_state=observable,
    )


def _diagnostics(**updates: str) -> dict[str, str]:
    states = {
        "adapter_result_received": "NOT_RUN",
        "registry_hash_validation_state": "NOT_RUN",
        "contract_validation_state": "NOT_RUN",
        "trigger_registry_validation_state": "NOT_RUN",
        "runtime_resolution_state": "NOT_RUN",
        "boundary_state": "NOT_RUN",
        "integration_result": "NOT_RUN",
    }
    states.update(updates)
    return states


def registry_sha256(registry_path: Path) -> str:
    try:
        return hashlib.sha256(registry_path.read_bytes()).hexdigest()
    except OSError as exc:
        raise SemanticAdapterError(
            f"unable to read runtime registry: {registry_path}", _diagnostics()
        ) from exc


def _verify_registry_hash(
    expected_hash: str | None,
    actual_hash: str,
    diagnostics: dict[str, str],
) -> None:
    if expected_hash is None:
        diagnostics["registry_hash_validation_state"] = "NOT_REQUIRED"
        return
    if (
        not isinstance(expected_hash, str)
        or len(expected_hash) != 64
        or any(character not in "0123456789abcdef" for character in expected_hash)
    ):
        diagnostics["registry_hash_validation_state"] = "FAIL"
        raise SemanticAdapterError("expected_registry_hash must be lowercase SHA-256", diagnostics)
    if actual_hash != expected_hash:
        diagnostics["registry_hash_validation_state"] = "FAIL"
        raise SemanticAdapterError(
            f"runtime registry SHA-256 mismatch: expected {expected_hash}, got {actual_hash}",
            diagnostics,
        )
    diagnostics["registry_hash_validation_state"] = "PASS"
