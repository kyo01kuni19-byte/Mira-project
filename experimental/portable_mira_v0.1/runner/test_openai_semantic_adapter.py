from __future__ import annotations

import copy
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from openai._utils._transform import maybe_transform
from openai.resources.responses.responses import Responses
from openai.types.responses import response_create_params
from openai.types.responses.response_format_text_json_schema_config_param import (
    ResponseFormatTextJSONSchemaConfigParam,
)
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from openai.types.shared_params.reasoning import Reasoning
from pydantic import TypeAdapter

from openai_semantic_adapter import (
    OpenAIAdapterConfig,
    OpenAIAdapterError,
    OpenAISDKTransport,
    OpenAISemanticJudgmentAdapter,
)
from semantic_adapter import (
    SemanticAdapterError,
    SemanticJudgmentAdapter,
    SemanticJudgmentInput,
    integrate_adapter,
)
from semantic_judgment import load_json


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = EXPERIMENT_ROOT / "generated" / "registry_runtime.json"
SCHEMA_PATH = EXPERIMENT_ROOT / "semantic" / "semantic_judgment_contract.schema.json"
FIXTURE_PATH = EXPERIMENT_ROOT / "evals" / "semantic_judgment" / "development_cases.json"
REGISTRY_HASH = "05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a"
TEST_API_KEY_ENV = "PORTABLE_MIRA_TEST_OPENAI_KEY"


class NoNetworkTransport:
    requires_credential = False

    def __init__(self, output: dict):
        self.output = copy.deepcopy(output)
        self.calls = 0

    def send(self, request: dict, api_key: str | None, config: OpenAIAdapterConfig) -> dict:
        self.calls += 1
        assert api_key is None
        return copy.deepcopy(self.output)


def cases() -> dict[str, dict]:
    fixture_set = load_json(FIXTURE_PATH)
    return {case["case_id"]: case for case in fixture_set["cases"]}


def adapter_input(case_id: str) -> SemanticJudgmentInput:
    case = cases()[case_id]
    observation = case["semantic_judgment"]["semantic_observation"]
    return SemanticJudgmentInput(
        input_ref=case_id,
        situation=case["situation"],
        value_intent=observation["value_intent"]["description"],
        available_evidence_refs=tuple(observation["evidence_basis"]),
        authority_context="synthetic authority context",
    )


def make_adapter(
    *,
    model_id: str = "model-identifier-under-review",
    reasoning_effort: str = "medium",
    expected_hash: str = REGISTRY_HASH,
    transport=None,
) -> OpenAISemanticJudgmentAdapter:
    return OpenAISemanticJudgmentAdapter(
        OpenAIAdapterConfig(
            model_id=model_id,
            reasoning_effort=reasoning_effort,
            api_key_env=TEST_API_KEY_ENV,
        ),
        REGISTRY_PATH,
        SCHEMA_PATH,
        expected_hash,
        transport=transport,
    )


def test_oa1_openai_adapter_satisfies_protocol():
    assert isinstance(make_adapter(), SemanticJudgmentAdapter)


def test_oa2_dry_run_requires_no_api_key():
    os.environ.pop(TEST_API_KEY_ENV, None)
    result = make_adapter().dry_run(adapter_input("R1"))
    assert result.state == "DRY_RUN_READY"
    assert result.network_call_performed is False
    assert result.credential_state == "NOT_REQUIRED_FOR_DRY_RUN"
    assert result.registry_hash_validation_state == "PASS"


def test_oa3_missing_api_key_is_not_configured_without_network():
    adapter = make_adapter()
    with patch.object(OpenAISDKTransport, "send") as send:
        os.environ.pop(TEST_API_KEY_ENV, None)
        try:
            adapter.judge(adapter_input("R1"))
        except OpenAIAdapterError as exc:
            assert exc.state == "NOT_CONFIGURED"
            assert TEST_API_KEY_ENV in str(exc)
        else:
            raise AssertionError("live mode without API key must be NOT_CONFIGURED")
        send.assert_not_called()


def test_oa4_request_contains_only_allowed_input_and_registry_context():
    request, metadata = make_adapter().build_request(adapter_input("R1"))
    payload = json.loads(request["input"])
    assert set(payload) == {
        "semantic_judgment_input",
        "registered_semantics",
        "output_requirement",
    }
    assert set(payload["semantic_judgment_input"]) == {
        "input_ref",
        "situation",
        "value_intent",
        "available_evidence_refs",
        "authority_context",
    }
    assert "api_key" not in json.dumps(request).lower()
    assert metadata["credential_in_request"] is False
    assert metadata["network_call_performed"] is False


def test_oa5_structured_output_maps_to_contract_schema():
    request, metadata = make_adapter().build_request(adapter_input("C1"))
    output_format = request["text"]["format"]
    canonical_schema = load_json(SCHEMA_PATH)
    artifact = load_json(
        EXPERIMENT_ROOT
        / "generated"
        / "openai_semantic_judgment_provider_schema.json"
    )
    assert output_format["type"] == "json_schema"
    assert output_format["strict"] is True
    assert output_format["schema"] == artifact["provider_schema"]
    assert output_format["schema"] != canonical_schema
    assert output_format["schema"]["$id"] == "portable_mira.semantic_judgment_contract.v0.1a"
    serialized = json.dumps(output_format["schema"], sort_keys=True)
    assert '"if"' not in serialized
    assert '"then"' not in serialized
    assert metadata["provider_schema_sha256"] == artifact["provider_schema_sha256"]
    assert metadata["provider_schema_compiler_id"].endswith("v0.2")
    assert metadata["structured_output_contract"].endswith("v0.1a")


def test_installed_sdk_accepts_request_types_locally():
    request, _ = make_adapter(
        model_id="gpt-5.6-sol", reasoning_effort="medium"
    ).build_request(adapter_input("C1"))
    validated = TypeAdapter(
        response_create_params.ResponseCreateParamsNonStreaming
    ).validate_python(request)
    transformed = maybe_transform(
        validated, response_create_params.ResponseCreateParamsNonStreaming
    )
    assert transformed["model"] == "gpt-5.6-sol"
    assert transformed["reasoning"] == {"effort": "medium"}
    assert transformed["text"]["format"]["type"] == "json_schema"
    assert transformed["text"]["format"]["strict"] is True
    assert transformed["tools"] == []
    assert transformed["store"] is False
    assert ResponseTextConfigParam.__annotations__["format"]
    assert ResponseFormatTextJSONSchemaConfigParam.__annotations__["schema"]
    assert Reasoning.__annotations__["effort"]
    create_parameters = inspect.signature(Responses.create).parameters
    for parameter in ("model", "instructions", "input", "reasoning", "text", "tools", "store"):
        assert parameter in create_parameters
    assert '"/responses"' in inspect.getsource(Responses.create)


def test_oa6_provider_output_still_passes_mira_validator():
    malformed = copy.deepcopy(cases()["H1"]["semantic_judgment"])
    malformed["routing_judgment"]["execution_authorization"] = True
    transport = NoNetworkTransport(malformed)
    adapter = make_adapter(transport=transport)
    try:
        integrate_adapter(
            adapter,
            adapter_input("H1"),
            REGISTRY_PATH,
            expected_registry_hash=REGISTRY_HASH,
        )
    except SemanticAdapterError as exc:
        assert exc.diagnostics["contract_validation_state"] == "FAIL"
        assert exc.diagnostics["runtime_resolution_state"] == "NOT_RUN"
        assert transport.calls == 1
        return
    raise AssertionError("provider structured output must not bypass MIRA validation")


def test_oa7_matching_registry_hash_permits_integration():
    transport = NoNetworkTransport(cases()["R1"]["semantic_judgment"])
    adapter = make_adapter(transport=transport)
    result = integrate_adapter(
        adapter,
        adapter_input("R1"),
        REGISTRY_PATH,
        expected_registry_hash=REGISTRY_HASH,
    )
    assert result.registry_hash_validation_state == "PASS"
    assert result.actual_registry_hash == REGISTRY_HASH
    assert result.cross_routes == ["E03_FAILURE_FRAMING", "E04_FRAMING_ENVIRONMENT"]
    assert transport.calls == 1


def test_oa8_registry_hash_mismatch_fails_before_adapter_and_runtime():
    wrong_hash = "0" * 64
    transport = NoNetworkTransport(cases()["R1"]["semantic_judgment"])
    adapter = make_adapter(expected_hash=wrong_hash, transport=transport)
    try:
        integrate_adapter(
            adapter,
            adapter_input("R1"),
            REGISTRY_PATH,
            expected_registry_hash=wrong_hash,
        )
    except SemanticAdapterError as exc:
        assert exc.diagnostics["registry_hash_validation_state"] == "FAIL"
        assert exc.diagnostics["adapter_result_received"] == "NOT_RUN"
        assert exc.diagnostics["runtime_resolution_state"] == "NOT_RUN"
        assert transport.calls == 0
        return
    raise AssertionError("registry hash mismatch must fail closed")


def test_oa9_request_exposes_no_tools_web_or_retrieval():
    request, metadata = make_adapter().build_request(adapter_input("R3"))
    assert request["tools"] == []
    assert metadata["tools_enabled"] is False
    assert metadata["external_retrieval_enabled"] is False
    assert metadata["hidden_reasoning_requested"] is False
    assert request["store"] is False


def test_oa10_no_credential_is_written_or_logged():
    result = make_adapter().dry_run(adapter_input("C1"))
    serialized = json.dumps(result.to_dict(), sort_keys=True)
    assert TEST_API_KEY_ENV in serialized
    assert "credential_in_request\": true" not in serialized.lower()
    assert "api_key" not in result.sanitized_request_metadata


def test_oa11_model_configuration_is_injectable_and_observable():
    first = make_adapter(model_id="model-identifier-a")
    second = make_adapter(model_id="model-identifier-b")
    first_result = first.dry_run(adapter_input("C1"))
    second_result = second.dry_run(adapter_input("C1"))
    assert first_result.sanitized_request_metadata["model_id"] == "model-identifier-a"
    assert second_result.sanitized_request_metadata["model_id"] == "model-identifier-b"
    assert first_result.sanitized_request_metadata["reasoning_effort"] == "medium"
    assert first_result.sanitized_request_metadata["transport_max_retries"] == 0


def run_regression(script: Path, expected_output: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=EXPERIMENT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert expected_output in completed.stdout


def test_oa12_existing_regressions_remain_pass():
    checks = (
        ("runner/test_semantic_adapter.py", "PASS: First Semantic Judgment Adapter Infrastructure v0.1 tests"),
        ("runner/test_semantic_judgment.py", "PASS: Semantic Judgment Contract v0.1a tests"),
        ("runner/test_router.py", "PASS: registry-backed router v0.1 tests"),
        ("runner/test_registry_loader.py", "PASS: registry loader v0.1 deterministic tests"),
        ("build/test_build.py", "PASS: build pipeline v0.1 deterministic tests"),
    )
    for relative_path, expected in checks:
        run_regression(EXPERIMENT_ROOT / relative_path, expected)


if __name__ == "__main__":
    tests = [
        test_oa1_openai_adapter_satisfies_protocol,
        test_oa2_dry_run_requires_no_api_key,
        test_oa3_missing_api_key_is_not_configured_without_network,
        test_oa4_request_contains_only_allowed_input_and_registry_context,
        test_oa5_structured_output_maps_to_contract_schema,
        test_installed_sdk_accepts_request_types_locally,
        test_oa6_provider_output_still_passes_mira_validator,
        test_oa7_matching_registry_hash_permits_integration,
        test_oa8_registry_hash_mismatch_fails_before_adapter_and_runtime,
        test_oa9_request_exposes_no_tools_web_or_retrieval,
        test_oa10_no_credential_is_written_or_logged,
        test_oa11_model_configuration_is_injectable_and_observable,
        test_oa12_existing_regressions_remain_pass,
    ]
    for test in tests:
        test()
    print("PASS: OpenAI Semantic Judgment Adapter v0.1 dry-run tests (OA1-OA12)")
