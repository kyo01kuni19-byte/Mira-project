from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import anthropic

from anthropic_output_annotator import (
    ANTHROPIC_ANNOTATION_KERNEL,
    AnthropicAnnotatorConfig,
    AnthropicAnnotatorError,
    AnthropicOutputAnnotator,
    parse_provider_annotation_text,
)
from holdout_governance import canonical_json_bytes, seal_payload
from output_annotator import (
    OutputAnnotationInput,
    file_sha256,
    payload_sha256,
    validate_blind_input_fields,
)


WORK_CONTRACT_ID = "TRUE-HOLDOUT-CASE1-ANNOTATION-001"
CASE_ID = "TH-CASE-001"
EXPECTED_NATURAL_ARTIFACT_HASH = (
    "230d94bfd32e28019bf04bb1da12ecaece8ec30279359a8381b208d11e2ad70f"
)
EXPECTED_ALLOWED_INPUT_HASH = (
    "6c159acf8a1cae7f03c8d5cdd2eb2abbfc4f4be7d2ec8cde61f71473b3b80659"
)
EXPECTED_RAW_JUDGMENT_HASH = (
    "6d9001deae784d366ec64c1d79ad3dbe103c84a9c20b903a92abe5f0c0b7226f"
)
EXPECTED_SOURCE_EVIDENCE_FILE_HASH = (
    "e12a930b1ecc46f1174c5bcd7e1a48c004492acc93688fda5b1fb6b034922f51"
)
EXPECTED_EXECUTION_STATE_FILE_HASH = (
    "9e7350fa453e8d37db4d7874a3b58142b3c21c4f18bd3e27ba6115cd270aebdb"
)
EXPECTED_CANONICAL_SCHEMA_HASH = (
    "7f5a606cb2f347b854f1f85085427beb0c5e75053b8af6f952bccaf8d8cd7b1d"
)
EXPECTED_PROVIDER_SCHEMA_HASH = (
    "61b7e8258a0e204b467d2ad1bdcca72f77a992d59b2861ab4790828680bf04f0"
)
EXPECTED_PROVIDER_ARTIFACT_HASH = (
    "0c26c4d6ba03d722e2588d46ddfdfe376bc68e2c197b6a60deb13b8b615ea2d7"
)
EXPECTED_EVALUATION_BASELINE = "cde62fdd47d7a19176d9c0d8907494d5a85787f1"
EXPECTED_GOVERNANCE_BASELINE = "5d5290913b8a80898ef6e1a4e7eec3cc5f534808"
EXPECTED_OTHER_CASE_SEALS = {
    "TH-CASE-002": "650aa3a06adc9fde8514fc2eff26bc0b864f1538662de72ef79c39aeb88a88b5",
    "TH-CASE-003": "aa8c80cb4e4e52d429ad4cd56baaa7641c1e78a6480ffeada398cd94e7c3bf64",
}
ALLOWED_SOURCE_CLASSES = (
    "EXACT_NATURAL_SITUATION",
    "FROZEN_ANNOTATION_KERNEL",
    "FROZEN_ANTHROPIC_PROVIDER_SCHEMA",
    "PRESERVED_SEMANTIC_AGENT_OUTPUT",
)


class BlindAnnotationError(Exception):
    """The bounded blind annotation gate or execution failed."""


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BlindAnnotationError(f"unable to load JSON artifact: {path}") from exc
    if not isinstance(value, dict):
        raise BlindAnnotationError(f"JSON artifact must be an object: {path}")
    return value


def evidence_path(root: Path) -> Path:
    return (
        root
        / "evals"
        / "holdout"
        / "cases"
        / CASE_ID
        / f"blind_annotation_{WORK_CONTRACT_ID}.json"
    )


def provenance_path(root: Path) -> Path:
    return (
        root
        / "evals"
        / "holdout"
        / "cases"
        / CASE_ID
        / "annotation_request_provenance_manifest.json"
    )


def build_preflight(root: Path) -> dict[str, Any]:
    case_dir = root / "evals" / "holdout" / "cases" / CASE_ID
    natural_path = case_dir / "natural_situation.json"
    allowed_path = case_dir / "allowed_model_input.json"
    source_path = (
        case_dir
        / "semantic_agent_execution_TRUE-HOLDOUT-CASE1-SEMANTIC-002.json"
    )
    execution_state_path = (
        case_dir / "execution_state_TRUE-HOLDOUT-CASE1-SEMANTIC-002.json"
    )
    schema_path = root / "semantic" / "output_annotation_contract.schema.json"
    provider_path = (
        root / "generated" / "anthropic_output_annotation_provider_schema.json"
    )

    natural_artifact = load_object(natural_path)
    allowed_artifact = load_object(allowed_path)
    source_evidence = load_object(source_path)
    execution_state = load_object(execution_state_path)
    if seal_payload(natural_artifact) != EXPECTED_NATURAL_ARTIFACT_HASH:
        raise BlindAnnotationError("Natural Situation artifact hash mismatch")
    if seal_payload(allowed_artifact) != EXPECTED_ALLOWED_INPUT_HASH:
        raise BlindAnnotationError("allowed model input hash mismatch")
    if file_sha256(source_path) != EXPECTED_SOURCE_EVIDENCE_FILE_HASH:
        raise BlindAnnotationError("source semantic evidence file hash mismatch")
    if file_sha256(execution_state_path) != EXPECTED_EXECUTION_STATE_FILE_HASH:
        raise BlindAnnotationError("source execution-state file hash mismatch")
    if source_evidence.get("eligibility") != "ELIGIBILITY_UNKNOWN":
        raise BlindAnnotationError("source eligibility state changed")
    if source_evidence.get("contamination") != "NO_KNOWN_CONTAMINATION":
        raise BlindAnnotationError("source contamination state changed")
    if execution_state.get("model_execution_count_after") != 1:
        raise BlindAnnotationError("source execution count is not one")

    natural_situation = natural_artifact.get("natural_situation")
    allowed_input = allowed_artifact.get("semantic_judgment_input")
    if not isinstance(allowed_input, dict) or allowed_input.get("situation") != natural_situation:
        raise BlindAnnotationError("Natural Situation differs from sealed allowed input")
    raw_judgment = source_evidence.get("raw_observable_semantic_judgment")
    if not isinstance(raw_judgment, dict):
        raise BlindAnnotationError("source Semantic Judgment is missing")
    if payload_sha256(raw_judgment) != EXPECTED_RAW_JUDGMENT_HASH:
        raise BlindAnnotationError("source Semantic Judgment hash mismatch")
    if source_evidence.get("raw_semantic_judgment_sha256") != EXPECTED_RAW_JUDGMENT_HASH:
        raise BlindAnnotationError("recorded source Semantic Judgment hash mismatch")
    if file_sha256(schema_path) != EXPECTED_CANONICAL_SCHEMA_HASH:
        raise BlindAnnotationError("canonical annotation schema hash mismatch")
    if file_sha256(provider_path) != EXPECTED_PROVIDER_ARTIFACT_HASH:
        raise BlindAnnotationError("Anthropic provider artifact hash mismatch")

    annotation_input = OutputAnnotationInput(
        case_id=CASE_ID,
        natural_situation=natural_situation,
        preserved_semantic_agent_output=raw_judgment,
        case_sha256=payload_sha256(
            {"case_id": CASE_ID, "natural_situation": natural_situation}
        ),
        raw_output_sha256=EXPECTED_RAW_JUDGMENT_HASH,
        annotation_schema_sha256=EXPECTED_CANONICAL_SCHEMA_HASH,
        governance_baseline_commit=EXPECTED_GOVERNANCE_BASELINE,
        evaluation_baseline_commit=EXPECTED_EVALUATION_BASELINE,
    )
    annotator = AnthropicOutputAnnotator(
        AnthropicAnnotatorConfig(model_id="claude-sonnet-5", max_tokens=3072),
        schema_path,
        provider_path,
    )
    dry = annotator.build_dry_run(annotation_input)
    request = dry.request
    metadata = dry.observable_configuration
    if anthropic.__version__ != "1.7.0":
        raise BlindAnnotationError("Anthropic SDK version mismatch")
    if metadata.get("provider_schema_sha256") != EXPECTED_PROVIDER_SCHEMA_HASH:
        raise BlindAnnotationError("Anthropic provider schema hash mismatch")
    if request.get("model") != "claude-sonnet-5" or request.get("max_tokens") != 3072:
        raise BlindAnnotationError("Anthropic request configuration mismatch")
    if request.get("system") != ANTHROPIC_ANNOTATION_KERNEL:
        raise BlindAnnotationError("compact annotation kernel mismatch")
    if set(request) != {"model", "max_tokens", "system", "messages", "output_config"}:
        raise BlindAnnotationError("Anthropic request contains a prohibited field")
    if len(request["messages"]) != 1 or request["messages"][0].get("role") != "user":
        raise BlindAnnotationError("assistant prefill or unexpected message configured")
    provider_input = json.loads(request["messages"][0]["content"])
    if set(provider_input) != {
        "natural_situation",
        "preserved_semantic_agent_output",
    }:
        raise BlindAnnotationError("provider input contains an unauthorized field")
    validate_blind_input_fields(provider_input)
    if provider_input["natural_situation"] != natural_situation:
        raise BlindAnnotationError("provider Natural Situation changed")
    if provider_input["preserved_semantic_agent_output"] != raw_judgment:
        raise BlindAnnotationError("provider Semantic Judgment changed")
    provider_visible = json.dumps(
        {"system": request["system"], "messages": request["messages"]},
        ensure_ascii=False,
        sort_keys=True,
    )
    forbidden_literals = (
        "174ac79fbacea5a9b7b6b3a81ff6a4c7caf8da74d7f58376cb544eaccefd6894",
        "TH-CASE-002",
        "TH-CASE-003",
        "expectation_artifact",
        "expected_route",
        "expected_trigger",
        "expected_diagnostic",
        "evaluator_result",
        "desired_answer",
    )
    if any(value in provider_visible for value in forbidden_literals):
        raise BlindAnnotationError("case-specific forbidden content entered request")

    for case_id, expected_hash in EXPECTED_OTHER_CASE_SEALS.items():
        path = root / "evals" / "holdout" / "cases" / case_id / "seal.json"
        if file_sha256(path) != expected_hash:
            raise BlindAnnotationError(f"other-case seal changed: {case_id}")

    sources = [
        {
            "source_class": "EXACT_NATURAL_SITUATION",
            "reference": f"evals/holdout/cases/{CASE_ID}/natural_situation.json",
            "sha256": EXPECTED_NATURAL_ARTIFACT_HASH,
        },
        {
            "source_class": "FROZEN_ANNOTATION_KERNEL",
            "reference": "runner/anthropic_output_annotator.py:ANTHROPIC_ANNOTATION_KERNEL",
            "sha256": hashlib.sha256(ANTHROPIC_ANNOTATION_KERNEL.encode("utf-8")).hexdigest(),
        },
        {
            "source_class": "FROZEN_ANTHROPIC_PROVIDER_SCHEMA",
            "reference": "generated/anthropic_output_annotation_provider_schema.json",
            "sha256": EXPECTED_PROVIDER_ARTIFACT_HASH,
            "provider_schema_sha256": EXPECTED_PROVIDER_SCHEMA_HASH,
        },
        {
            "source_class": "PRESERVED_SEMANTIC_AGENT_OUTPUT",
            "reference": (
                f"evals/holdout/cases/{CASE_ID}/"
                "semantic_agent_execution_TRUE-HOLDOUT-CASE1-SEMANTIC-002.json"
            ),
            "sha256": EXPECTED_RAW_JUDGMENT_HASH,
            "source_artifact_sha256": EXPECTED_SOURCE_EVIDENCE_FILE_HASH,
        },
    ]
    if tuple(sorted(item["source_class"] for item in sources)) != tuple(
        sorted(ALLOWED_SOURCE_CLASSES)
    ):
        raise BlindAnnotationError("annotation provenance source classes changed")
    manifest = {
        "artifact_type": "BLIND_ANNOTATION_REQUEST_PROVENANCE_MANIFEST",
        "work_contract_id": WORK_CONTRACT_ID,
        "case_id": CASE_ID,
        "request_sha256": payload_sha256(request),
        "allowed_source_classes": list(ALLOWED_SOURCE_CLASSES),
        "sources": sources,
        "expectation_visible": False,
        "expectation_source_present": False,
        "evaluator_source_present": False,
        "other_holdout_case_source_present": False,
        "sent_to_model": False,
        "limitations": [
            "Structural provenance does not prove arbitrary semantic paraphrase absence.",
            "Different-provider annotation is not independent ground truth.",
        ],
    }
    return {
        "annotation_input": annotation_input,
        "annotator": annotator,
        "request": request,
        "metadata": metadata,
        "manifest": manifest,
        "source_evidence": source_evidence,
        "other_case_seals": copy.deepcopy(EXPECTED_OTHER_CASE_SEALS),
    }


def write_provenance(root: Path, gate: dict[str, Any]) -> str:
    path = provenance_path(root)
    content = canonical_json_bytes(gate["manifest"])
    if path.exists() and path.read_bytes() != content:
        raise BlindAnnotationError("existing annotation provenance manifest differs")
    path.write_bytes(content)
    return file_sha256(path)


def execute_once(root: Path) -> dict[str, Any]:
    output_path = evidence_path(root)
    if output_path.exists():
        raise BlindAnnotationError("append-only annotation evidence already exists")
    gate = build_preflight(root)
    provenance_file_hash = write_provenance(root, gate)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise BlindAnnotationError("ANTHROPIC_API_KEY presence is NOT_CONFIGURED")

    request_count = 0
    retry_count = 0
    raw_text: str | None = None
    raw_annotation: dict[str, Any] | None = None
    validated_annotation: dict[str, Any] | None = None
    provider_result: dict[str, Any] = {
        "state": "NOT_RUN",
        "stop_reason": None,
        "request_id": None,
        "usage": None,
    }
    states = {
        "transport": "UNKNOWN",
        "anthropic_server_acceptance": "UNKNOWN",
        "structured_output": "UNKNOWN",
        "canonical_annotation_validation": "UNKNOWN",
        "hash_binding": "UNKNOWN",
        "blind_annotation_integration": "UNKNOWN",
    }
    sanitized_error: dict[str, Any] | None = None

    client = anthropic.Anthropic(api_key=api_key, max_retries=0, timeout=60.0)
    request_count += 1
    try:
        response = client.messages.create(**gate["request"])
    except Exception as exc:
        states["transport"] = "FAIL"
        sanitized_error = {
            "error_type": type(exc).__name__,
            "http_status": getattr(exc, "status_code", None),
            "request_id": getattr(exc, "request_id", None),
            "message": f"Anthropic request failed with {type(exc).__name__}.",
        }
        provider_result["state"] = "ERROR"
    else:
        states["transport"] = "PASS"
        states["anthropic_server_acceptance"] = "PASS"
        raw_text = "".join(
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text"
        )
        provider_result = {
            "state": "RESPONSE_RECEIVED",
            "stop_reason": response.stop_reason,
            "request_id": getattr(response, "id", None),
            "usage": {
                "input_tokens": getattr(response.usage, "input_tokens", None),
                "output_tokens": getattr(response.usage, "output_tokens", None),
            },
        }
        try:
            raw_annotation = parse_provider_annotation_text(
                raw_text, stop_reason=response.stop_reason
            )
        except AnthropicAnnotatorError as exc:
            states["structured_output"] = "FAIL"
            sanitized_error = {"state": exc.state, "message": str(exc)}
        else:
            states["structured_output"] = "PASS"
            try:
                validated_annotation = gate["annotator"].validate_provider_output(
                    raw_annotation,
                    annotation_input=gate["annotation_input"],
                )
            except AnthropicAnnotatorError as exc:
                states["canonical_annotation_validation"] = "FAIL"
                sanitized_error = {"state": exc.state, "message": str(exc)}
            else:
                states["canonical_annotation_validation"] = "PASS"
                metadata = validated_annotation["annotation_metadata"]
                expected_bindings = {
                    "case_sha256": gate["annotation_input"].case_sha256,
                    "raw_output_sha256": EXPECTED_RAW_JUDGMENT_HASH,
                    "annotation_schema_sha256": EXPECTED_CANONICAL_SCHEMA_HASH,
                }
                if any(metadata.get(key) != value for key, value in expected_bindings.items()):
                    states["hash_binding"] = "FAIL"
                    sanitized_error = {
                        "state": "HASH_BINDING_FAILED",
                        "message": "validated annotation binding mismatch",
                    }
                else:
                    states["hash_binding"] = "PASS"
                    states["blind_annotation_integration"] = "PASS"

    evidence = {
        "artifact_type": "TRUE_HOLDOUT_BLIND_ANNOTATION_EVIDENCE",
        "work_contract_id": WORK_CONTRACT_ID,
        "case_id": CASE_ID,
        "eligibility": "ELIGIBILITY_UNKNOWN",
        "contamination": "NO_KNOWN_CONTAMINATION",
        "bindings": {
            "natural_situation_sha256": EXPECTED_NATURAL_ARTIFACT_HASH,
            "source_semantic_judgment_sha256": EXPECTED_RAW_JUDGMENT_HASH,
            "source_semantic_execution_artifact_sha256": (
                EXPECTED_SOURCE_EVIDENCE_FILE_HASH
            ),
            "source_execution_state_artifact_sha256": (
                EXPECTED_EXECUTION_STATE_FILE_HASH
            ),
            "canonical_annotation_schema_sha256": EXPECTED_CANONICAL_SCHEMA_HASH,
            "provider_schema_sha256": EXPECTED_PROVIDER_SCHEMA_HASH,
            "provider_artifact_sha256": EXPECTED_PROVIDER_ARTIFACT_HASH,
            "annotation_request_sha256": gate["manifest"]["request_sha256"],
            "annotation_provenance_manifest_file_sha256": provenance_file_hash,
        },
        "configuration": {
            "provider": "anthropic",
            "sdk_version": anthropic.__version__,
            "model": "claude-sonnet-5",
            "max_tokens": 3072,
            "max_retries": 0,
            "compact_annotation_kernel": True,
            "tools": None,
            "web_retrieval": None,
            "citations": None,
            "assistant_prefill": None,
            "explicit_thinking": None,
            "external_actions": None,
        },
        "request_count": request_count,
        "retry_count": retry_count,
        "provider_result": provider_result,
        "raw_observable_annotation": raw_annotation,
        "validated_annotation": validated_annotation,
        "annotation_sha256": (
            payload_sha256(raw_annotation) if raw_annotation is not None else None
        ),
        "raw_text_sha256": (
            hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
            if raw_text is not None
            else None
        ),
        "completion_gate": (
            "PASS"
            if all(value == "PASS" for value in states.values())
            else "FAIL"
        ),
        "states": states,
        "hash_binding_state": states["hash_binding"],
        "expectation_visible": False,
        "expectation_based_evaluation": "NOT_RUN",
        "disagreement_review": "NOT_RUN",
        "sanitized_error": sanitized_error,
        "hidden_reasoning_stored": False,
    }
    output_path.write_bytes(canonical_json_bytes(evidence))
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "execute"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    gate = build_preflight(root)
    manifest_hash = write_provenance(root, gate)
    if args.mode == "preflight":
        print(
            json.dumps(
                {
                    "state": "PASS",
                    "request_sha256": gate["manifest"]["request_sha256"],
                    "provenance_manifest_sha256": manifest_hash,
                    "credential_accessed": False,
                    "network_request_count": 0,
                },
                sort_keys=True,
            )
        )
        return
    evidence = execute_once(root)
    print(
        json.dumps(
            {
                "request_count": evidence["request_count"],
                "retry_count": evidence["retry_count"],
                "completion_gate": evidence["completion_gate"],
                "states": evidence["states"],
                "artifact_sha256": file_sha256(evidence_path(root)),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
