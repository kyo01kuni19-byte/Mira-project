from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import openai

from holdout_blindness import (
    EXPECTED_ALLOWED_INPUT_HASH,
    EXPECTED_CANONICAL_SCHEMA_HASH,
    EXPECTED_PROVIDER_ARTIFACT_HASH,
    EXPECTED_PROVIDER_SCHEMA_HASH,
    EXPECTED_REGISTRY_HASH,
    build_request_with_provenance,
    file_sha256,
    load_object,
    validate_request_blindness,
)
from holdout_governance import canonical_json_bytes, seal_payload
from openai_semantic_adapter import (
    OpenAIAdapterConfig,
    OpenAIAdapterError,
    OpenAIProviderResult,
    OpenAISDKTransport,
)
from semantic_adapter import registry_sha256
from semantic_judgment import (
    SemanticJudgmentError,
    evaluate_judgment,
    load_json,
    validate_contract,
    validate_registry_binding,
)
from true_holdout_seal import verify_seal


WORK_CONTRACT_ID = "TRUE-HOLDOUT-CASE1-SEMANTIC-002"
CASE_ID = "TH-CASE-001"
EXPECTED_NATURAL_HASH = (
    "230d94bfd32e28019bf04bb1da12ecaece8ec30279359a8381b208d11e2ad70f"
)
EXPECTED_EXPECTATION_HASH = (
    "174ac79fbacea5a9b7b6b3a81ff6a4c7caf8da74d7f58376cb544eaccefd6894"
)
EXPECTED_PROVENANCE_REQUEST_HASH = (
    "f01aca84d3ecf08acd8e975d8a84fe450539ecc6013e444cce66e3fffcf8d85f"
)
EXPECTED_PROVENANCE_MANIFEST_FILE_HASH = (
    "5d7f974413c2418160117520721269dd025bbd296f62b56b1a4b2285e66bea86"
)
EXPECTED_EVALUATION_BASELINE = "cde62fdd47d7a19176d9c0d8907494d5a85787f1"
EXPECTED_GOVERNANCE_BASELINE = "5d5290913b8a80898ef6e1a4e7eec3cc5f534808"
EXPECTED_CASE_SEAL_FILE_HASHES = {
    "TH-CASE-002": "650aa3a06adc9fde8514fc2eff26bc0b864f1538662de72ef79c39aeb88a88b5",
    "TH-CASE-003": "aa8c80cb4e4e52d429ad4cd56baaa7641c1e78a6480ffeada398cd94e7c3bf64",
}


class LiveHoldoutError(Exception):
    """The bounded holdout request or its local processing failed."""


def evidence_path(root: Path) -> Path:
    return (
        root
        / "evals"
        / "holdout"
        / "cases"
        / CASE_ID
        / f"semantic_agent_execution_{WORK_CONTRACT_ID}.json"
    )


def state_path(root: Path) -> Path:
    return (
        root
        / "evals"
        / "holdout"
        / "cases"
        / CASE_ID
        / f"execution_state_{WORK_CONTRACT_ID}.json"
    )


def preflight(root: Path) -> dict[str, Any]:
    case_dir = root / "evals" / "holdout" / "cases" / CASE_ID
    protocol_path = root / "evals" / "holdout" / "annotation_governance_protocol.json"
    seal = verify_seal(case_dir, protocol_path)
    expected_hashes = {
        "natural_situation": EXPECTED_NATURAL_HASH,
        "expectation_artifact": EXPECTED_EXPECTATION_HASH,
        "allowed_model_input": EXPECTED_ALLOWED_INPUT_HASH,
    }
    for name, expected in expected_hashes.items():
        if seal["hashes"].get(name) != expected:
            raise LiveHoldoutError(f"sealed hash mismatch: {name}")
    if seal["baseline_bindings"]["evaluation_baseline"] != EXPECTED_EVALUATION_BASELINE:
        raise LiveHoldoutError("evaluation baseline mismatch")
    if seal["baseline_bindings"]["governance_baseline"] != EXPECTED_GOVERNANCE_BASELINE:
        raise LiveHoldoutError("governance baseline mismatch")
    if seal["sealed_before_model_execution"] is not True:
        raise LiveHoldoutError("case was not sealed before model execution")
    if seal["model_execution_count"] != 0:
        raise LiveHoldoutError("case already has a model execution")
    if seal["governance_assessment"]["eligibility"] != "ELIGIBILITY_UNKNOWN":
        raise LiveHoldoutError("holdout eligibility state changed")
    if seal["available_evidence_contamination_check"] != "NO_KNOWN_CONTAMINATION":
        raise LiveHoldoutError("known contamination is present")

    provenance_path = case_dir / "request_provenance_manifest.json"
    if file_sha256(provenance_path) != EXPECTED_PROVENANCE_MANIFEST_FILE_HASH:
        raise LiveHoldoutError("provenance manifest file hash mismatch")
    recorded_manifest = load_object(provenance_path)
    request, reconstructed_manifest = build_request_with_provenance(root)
    if canonical_json_bytes(recorded_manifest) != canonical_json_bytes(
        reconstructed_manifest
    ):
        raise LiveHoldoutError("provenance manifest does not match reconstruction")
    if seal_payload(request) != EXPECTED_PROVENANCE_REQUEST_HASH:
        raise LiveHoldoutError("deterministic request hash mismatch")
    blindness = validate_request_blindness(request, reconstructed_manifest, root)
    if blindness.state != "PASS":
        raise LiveHoldoutError("provenance-aware blindness validation failed")

    if openai.__version__ != "3.16.2":
        raise LiveHoldoutError("OpenAI SDK version mismatch")
    if request.get("model") != "gpt-5.6-sol":
        raise LiveHoldoutError("model identifier mismatch")
    if request.get("reasoning") != {"effort": "medium"}:
        raise LiveHoldoutError("reasoning configuration mismatch")
    if request.get("tools") != [] or request.get("store") is not False:
        raise LiveHoldoutError("prohibited provider capability configured")
    text = request.get("text")
    if not isinstance(text, dict) or text.get("format", {}).get("strict") is not True:
        raise LiveHoldoutError("strict structured output is not enabled")
    if set(request) != {
        "model", "instructions", "input", "reasoning", "text", "tools", "store"
    }:
        raise LiveHoldoutError("provider request contains an unexpected field")

    for case_id, expected_hash in EXPECTED_CASE_SEAL_FILE_HASHES.items():
        path = root / "evals" / "holdout" / "cases" / case_id / "seal.json"
        if file_sha256(path) != expected_hash:
            raise LiveHoldoutError(f"unexecuted case seal changed: {case_id}")
    return {
        "request": request,
        "manifest": reconstructed_manifest,
        "blindness": blindness.to_dict(),
        "seal": seal,
        "case2_case3_seal_hashes": copy.deepcopy(EXPECTED_CASE_SEAL_FILE_HASHES),
    }


def execute_once(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    output_path = evidence_path(root)
    execution_state_path = state_path(root)
    if output_path.exists() or execution_state_path.exists():
        raise LiveHoldoutError("append-only execution evidence already exists")

    gate = preflight(root)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise LiveHoldoutError("OPENAI_API_KEY presence is NOT_CONFIGURED")

    config = OpenAIAdapterConfig(
        model_id="gpt-5.6-sol",
        reasoning_effort="medium",
        transport_max_retries=0,
    )
    transport = OpenAISDKTransport()
    if transport.request_count != 0:
        raise LiveHoldoutError("network request count was not zero before execution")

    registry_path = root / "generated" / "registry_runtime.json"
    provider_output: dict[str, Any] | None = None
    provider_metadata: dict[str, Any] = {}
    sanitized_error: dict[str, Any] | None = None
    stage_states = {
        "transport": "UNKNOWN",
        "structured_output": "UNKNOWN",
        "canonical_validation": "UNKNOWN",
        "trigger_registry_validation": "UNKNOWN",
        "deterministic_routing": "UNKNOWN",
        "boundary_enforcement": "UNKNOWN",
        "raw_semantic_integration": "UNKNOWN",
    }
    runtime_evidence: dict[str, Any] | None = None
    impact_diagnostic: dict[str, Any] | None = None

    try:
        transport_result = transport.send(gate["request"], api_key, config)
    except OpenAIAdapterError as exc:
        provider_metadata = copy.deepcopy(exc.metadata)
        sanitized_error = {
            "state": exc.state,
            "message": str(exc),
            "metadata": copy.deepcopy(exc.metadata),
        }
        if exc.state == "PROVIDER_OUTPUT_INVALID":
            stage_states["transport"] = "PASS"
            stage_states["structured_output"] = "FAIL"
        else:
            stage_states["transport"] = "FAIL"
    else:
        if not isinstance(transport_result, OpenAIProviderResult):
            raise LiveHoldoutError("official transport returned an unexpected result")
        stage_states["transport"] = "PASS"
        stage_states["structured_output"] = "PASS"
        provider_output = copy.deepcopy(transport_result.output)
        provider_metadata = copy.deepcopy(transport_result.metadata)

        try:
            validated = validate_contract(provider_output)
        except SemanticJudgmentError as exc:
            stage_states["canonical_validation"] = "FAIL"
            sanitized_error = {
                "state": "CANONICAL_VALIDATION_FAILED",
                "message": str(exc),
            }
        else:
            stage_states["canonical_validation"] = "PASS"
            registry = load_json(registry_path)
            try:
                validate_registry_binding(validated, registry)
            except SemanticJudgmentError as exc:
                stage_states["trigger_registry_validation"] = "FAIL"
                sanitized_error = {
                    "state": "TRIGGER_REGISTRY_VALIDATION_FAILED",
                    "message": str(exc),
                }
            else:
                stage_states["trigger_registry_validation"] = "PASS"
                if registry_sha256(registry_path) != EXPECTED_REGISTRY_HASH:
                    sanitized_error = {
                        "state": "REGISTRY_HASH_VALIDATION_FAILED",
                        "message": "runtime registry hash changed during processing",
                    }
                else:
                    try:
                        runtime = evaluate_judgment(
                            CASE_ID,
                            validated,
                            registry_path,
                            authority_state="CLEAR",
                            impact_state="CLEAR",
                        )
                    except SemanticJudgmentError as exc:
                        stage_states["deterministic_routing"] = "FAIL"
                        sanitized_error = {
                            "state": "DETERMINISTIC_ROUTING_FAILED",
                            "message": str(exc),
                        }
                    else:
                        stage_states["deterministic_routing"] = "PASS"
                        stage_states["boundary_enforcement"] = "PASS"
                        stage_states["raw_semantic_integration"] = "PASS"
                        runtime_evidence = {
                            "result": runtime.to_dict(),
                            "cross_routes": list(runtime.cross_routes),
                            "resolved_route": runtime.runtime_resolved_route,
                            "knowledge_addresses_used": list(runtime.knowledge_addresses),
                            "authority_boundary_state": "CLEAR",
                            "inter_entity_impact_boundary_state": "CLEAR",
                            "integration_state": runtime.final_integration_result,
                        }
                        impact = validated["semantic_observation"][
                            "potential_inter_entity_impact"
                        ]
                        impact_diagnostic = {
                            "provider_observation_detected": impact["detected"],
                            "provider_observed_affected_entities": copy.deepcopy(
                                impact["affected_entities"]
                            ),
                            "provider_observed_basis": copy.deepcopy(impact["basis"]),
                            "independent_interest_assessment": "NOT_EVALUATED",
                            "impact_inflation_assessment": "NOT_EVALUATED",
                            "diagnostic_only": True,
                            "changes_authority": False,
                            "changes_boundary_state": False,
                        }

    request_count = transport.request_count
    if request_count != 1:
        raise LiveHoldoutError(
            f"exactly one network request was required, observed {request_count}"
        )
    retry_count = provider_metadata.get("retry_count", 0)
    raw_output_hash = seal_payload(provider_output) if provider_output is not None else None
    evidence = {
        "artifact_type": "TRUE_HOLDOUT_RAW_SEMANTIC_AGENT_EVIDENCE",
        "work_contract_id": WORK_CONTRACT_ID,
        "case_id": CASE_ID,
        "eligibility": "ELIGIBILITY_UNKNOWN",
        "contamination": "NO_KNOWN_CONTAMINATION",
        "hashes": {
            "natural_situation": EXPECTED_NATURAL_HASH,
            "expectation_artifact": EXPECTED_EXPECTATION_HASH,
            "allowed_model_input": EXPECTED_ALLOWED_INPUT_HASH,
            "request": EXPECTED_PROVENANCE_REQUEST_HASH,
            "provenance_manifest_file": EXPECTED_PROVENANCE_MANIFEST_FILE_HASH,
            "registry": EXPECTED_REGISTRY_HASH,
            "canonical_schema": EXPECTED_CANONICAL_SCHEMA_HASH,
            "provider_schema": EXPECTED_PROVIDER_SCHEMA_HASH,
            "provider_artifact_file": EXPECTED_PROVIDER_ARTIFACT_HASH,
        },
        "configuration": {
            "provider": "openai",
            "sdk_version": openai.__version__,
            "model": config.model_id,
            "reasoning_effort": config.reasoning_effort,
            "strict_structured_output": True,
            "tools": [],
            "store": False,
            "max_retries": config.transport_max_retries,
            "web_retrieval": False,
            "external_actions": False,
        },
        "request_count": request_count,
        "retry_count": retry_count,
        "token_usage": copy.deepcopy(provider_metadata.get("token_usage")),
        "provider_response_id": provider_metadata.get("response_id"),
        "raw_observable_semantic_judgment": provider_output,
        "raw_semantic_judgment_sha256": raw_output_hash,
        "stage_states": stage_states,
        "runtime_evidence": runtime_evidence,
        "impact_diagnostic": impact_diagnostic,
        "sanitized_error": sanitized_error,
        "hidden_reasoning_stored": False,
        "expectation_based_evaluation": "NOT_RUN",
        "anthropic_annotation": "NOT_RUN",
    }
    state = {
        "artifact_type": "TRUE_HOLDOUT_APPEND_ONLY_EXECUTION_STATE",
        "work_contract_id": WORK_CONTRACT_ID,
        "case_id": CASE_ID,
        "pre_execution_seal_file_sha256": file_sha256(
            root / "evals" / "holdout" / "cases" / CASE_ID / "seal.json"
        ),
        "model_execution_count_before": 0,
        "model_execution_count_after": 1,
        "network_request_count": request_count,
        "retry_count": retry_count,
        "further_execution_authorized": False,
        "pre_execution_seal_mutated": False,
        "case2_case3_seal_hashes": copy.deepcopy(
            gate["case2_case3_seal_hashes"]
        ),
    }
    output_path.write_bytes(canonical_json_bytes(evidence))
    execution_state_path.write_bytes(canonical_json_bytes(state))
    return evidence, state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "execute"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.mode == "preflight":
        result = preflight(root)
        print(
            json.dumps(
                {
                    "state": "PASS",
                    "request_sha256": seal_payload(result["request"]),
                    "blindness": result["blindness"],
                    "credential_accessed": False,
                    "network_request_count": 0,
                },
                sort_keys=True,
            )
        )
        return
    evidence, state = execute_once(root)
    print(
        json.dumps(
            {
                "request_count": evidence["request_count"],
                "retry_count": evidence["retry_count"],
                "stage_states": evidence["stage_states"],
                "evidence_sha256": file_sha256(evidence_path(root)),
                "state_sha256": file_sha256(state_path(root)),
                "model_execution_count_after": state["model_execution_count_after"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
