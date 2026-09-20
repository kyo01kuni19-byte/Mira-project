from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import httpx2
from openai import BadRequestError
from openai.lib._pydantic import _ensure_strict_json_schema

from openai_schema_audit import (
    LOCALLY_UNKNOWN,
    LOCALLY_VERIFIED,
    PROVIDER_COMPATIBLE,
    PROVIDER_INCOMPATIBLE,
    SUSPECT,
    UNKNOWN_SERVER_SIDE,
    audit_request_configuration,
    audit_schema_constructs,
    collect_schema_constructs,
)
from openai_semantic_adapter import (
    OpenAIAdapterConfig,
    OpenAIAdapterError,
    OpenAISDKTransport,
    sanitize_provider_error,
)
from semantic_judgment import load_json, validate_contract


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = EXPERIMENT_ROOT / "semantic" / "semantic_judgment_contract.schema.json"
REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "registry_runtime.json"
FAILURE_PATH = (
    EXPERIMENT_ROOT
    / "evals"
    / "semantic_judgment"
    / "LIVE-SJ-001-TRANSPORT-400.json"
)
CANONICAL_SCHEMA_SHA256 = "dc117d93a9d8040760228d0ce1c40c19e5578963b4961ce50050b269a44272e6"
REGISTRY_SHA256 = "05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a"


def official_bad_request() -> BadRequestError:
    request = httpx2.Request(
        "POST",
        "https://api.openai.com/v1/responses",
        headers={"authorization": "Bearer forbidden-test-secret"},
        content=b'{"situation":"sensitive-input-content"}',
    )
    response = httpx2.Response(
        400,
        request=request,
        headers={
            "x-request-id": "req_sanitized_test",
            "authorization": "Bearer forbidden-response-secret",
        },
    )
    return BadRequestError(
        "raw message with forbidden-test-secret and sensitive-input-content",
        response=response,
        body={
            "type": "invalid_request_error",
            "code": "invalid_json_schema",
            "param": "text.format.schema",
            "message": "raw body with forbidden-response-secret",
        },
    )


def test_er1_sanitized_bad_request_fields_are_retained():
    result = sanitize_provider_error(official_bad_request())
    assert result == {
        "http_status": 400,
        "error_type": "invalid_request_error",
        "error_code": "invalid_json_schema",
        "error_param": "text.format.schema",
        "sanitized_error_message": "OpenAI request failed with BadRequestError (HTTP 400).",
        "request_id": "req_sanitized_test",
    }


def test_er1_transport_preserves_only_sanitized_bad_request_fields():
    provider_error = official_bad_request()

    class Responses:
        @staticmethod
        def create(**request):
            raise provider_error

    class Client:
        responses = Responses()

    transport = OpenAISDKTransport()
    config = OpenAIAdapterConfig(model_id="gpt-5.6-sol")
    with patch("openai.OpenAI", return_value=Client()):
        try:
            transport.send({}, "non-secret-test-placeholder", config)
        except OpenAIAdapterError as exc:
            assert exc.state == "TRANSPORT_ERROR"
            assert exc.__cause__ is None
            assert exc.__context__ is None
            assert exc.metadata["request_count"] == 1
            assert exc.metadata["retry_count"] == 0
            assert exc.metadata["http_status"] == 400
            assert exc.metadata["error_param"] == "text.format.schema"
            assert "body" not in exc.metadata
            assert "headers" not in exc.metadata
            return
    raise AssertionError("official BadRequestError must be converted to sanitized metadata")


def test_er2_sensitive_transport_material_is_not_retained():
    result = sanitize_provider_error(official_bad_request())
    serialized = json.dumps(result, sort_keys=True)
    for forbidden in (
        "forbidden-test-secret",
        "forbidden-response-secret",
        "authorization",
        "sensitive-input-content",
        "headers",
        "body",
    ):
        assert forbidden not in serialized
    assert set(result) == {
        "http_status",
        "error_type",
        "error_code",
        "error_param",
        "sanitized_error_message",
        "request_id",
    }


def test_er3_canonical_schema_is_byte_identical():
    assert hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest() == CANONICAL_SCHEMA_SHA256


def test_er4_every_canonical_construct_is_classified():
    schema = load_json(SCHEMA_PATH)
    constructs = collect_schema_constructs(schema)
    audit = audit_schema_constructs(schema)
    assert set(audit) == constructs
    assert set(audit.values()) <= {
        PROVIDER_COMPATIBLE,
        PROVIDER_INCOMPATIBLE,
        LOCALLY_UNKNOWN,
    }
    assert LOCALLY_UNKNOWN in audit.values()
    assert audit["if"] == PROVIDER_INCOMPATIBLE
    assert audit["then"] == PROVIDER_INCOMPATIBLE
    strict_candidate = _ensure_strict_json_schema(
        copy.deepcopy(schema), path=(), root=copy.deepcopy(schema)
    )
    assert strict_candidate == schema


def test_er5_compiler_is_required_by_incompatible_conditionals():
    audit = audit_schema_constructs(load_json(SCHEMA_PATH))
    assert audit["if"] == PROVIDER_INCOMPATIBLE
    assert audit["then"] == PROVIDER_INCOMPATIBLE


def test_er6_provider_shape_cannot_bypass_canonical_validator():
    malformed = {
        "semantic_observation": {},
        "routing_judgment": {"execution_authorization": True},
    }
    try:
        validate_contract(malformed)
    except Exception:
        return
    raise AssertionError("provider output must still fail the canonical MIRA validator")


def test_er7_unreviewed_canonical_mapping_fails_closed():
    from openai_provider_schema import ProviderSchemaCompilationError, compile_provider_schema

    unreviewed = EXPERIMENT_ROOT / "generated" / "test_unreviewed_contract.schema.json"
    unreviewed.write_text('{"type":"object"}\n', encoding="utf-8")
    try:
        compile_provider_schema(unreviewed, REGISTRY_PATH)
    except ProviderSchemaCompilationError as exc:
        assert "MISSING DESIGN DECISION" in str(exc)
        return
    raise AssertionError("unreviewed provider mapping must fail closed")


def test_er8_er9_request_boundary_and_registry_hash_regressions():
    script = EXPERIMENT_ROOT / "runner" / "test_openai_semantic_adapter.py"
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PASS: OpenAI Semantic Judgment Adapter v0.1 dry-run tests" in completed.stdout
    assert hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest() == REGISTRY_SHA256


def test_er8_request_audit_keeps_server_acceptance_separate():
    request = {
        "model": "gpt-5.6-sol",
        "instructions": "minimal kernel",
        "input": "{}",
        "reasoning": {"effort": "medium"},
        "text": {"format": {"type": "json_schema", "strict": True}},
        "tools": [],
        "store": False,
    }
    audit = audit_request_configuration(request, max_retries=0)
    assert audit["model_identifier"] == UNKNOWN_SERVER_SIDE
    assert audit["strict_schema_subset"] == SUSPECT
    assert audit["unsupported_conditionals_removed"] == LOCALLY_VERIFIED
    assert audit["sdk_local_acceptance_is_server_acceptance"] == UNKNOWN_SERVER_SIDE
    for key in (
        "responses_api_path",
        "reasoning_parameter",
        "text_format_structure",
        "strict_setting",
        "tools_empty",
        "store_false",
        "max_retries_zero",
        "input_shape",
        "instructions_shape",
        "json_schema_format",
    ):
        assert audit[key] == LOCALLY_VERIFIED


def test_er10_first_failure_preserves_unknown_cause():
    record = load_json(FAILURE_PATH)
    assert record["known"]["request_count"] == 1
    assert record["known"]["retry_count"] == 0
    assert record["known"]["error_category"] == "BadRequestError"
    assert record["known"]["provider_semantic_output_received"] is False
    assert record["unknown"]["rejected_server_parameter"] == "UNKNOWN"
    assert record["unknown"]["provider_error_param"] == "UNKNOWN"


if __name__ == "__main__":
    tests = [
        test_er1_sanitized_bad_request_fields_are_retained,
        test_er1_transport_preserves_only_sanitized_bad_request_fields,
        test_er2_sensitive_transport_material_is_not_retained,
        test_er3_canonical_schema_is_byte_identical,
        test_er4_every_canonical_construct_is_classified,
        test_er5_compiler_is_required_by_incompatible_conditionals,
        test_er6_provider_shape_cannot_bypass_canonical_validator,
        test_er7_unreviewed_canonical_mapping_fails_closed,
        test_er8_er9_request_boundary_and_registry_hash_regressions,
        test_er8_request_audit_keeps_server_acceptance_separate,
        test_er10_first_failure_preserves_unknown_cause,
    ]
    for test in tests:
        test()
    print("PASS: OpenAI first-error diagnostics tests (ER1-ER10)")
