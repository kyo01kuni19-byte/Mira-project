from __future__ import annotations

from typing import Any


PROVIDER_COMPATIBLE = "PROVIDER_COMPATIBLE"
PROVIDER_INCOMPATIBLE = "PROVIDER_INCOMPATIBLE"
LOCALLY_UNKNOWN = "LOCALLY_UNKNOWN"
LOCALLY_VERIFIED = "LOCALLY_VERIFIED"
SUSPECT = "SUSPECT"
UNKNOWN_SERVER_SIDE = "UNKNOWN_SERVER_SIDE"
SDK_LOCAL_ACCEPTANCE_PRINCIPLE = (
    "SDK_LOCAL_ACCEPTANCE != PROVIDER_SERVER_ACCEPTANCE"
)

# The compatible set is limited to constructs explicitly traversed or normalized by
# openai.lib._pydantic._ensure_strict_json_schema in SDK 3.16.2. The SDK accepts an
# arbitrary schema dictionary, so mere request-type acceptance is not provider proof.
SCHEMA_CONSTRUCT_CLASSIFICATION = {
    "$defs": PROVIDER_COMPATIBLE,
    "$id": LOCALLY_UNKNOWN,
    "$ref": PROVIDER_COMPATIBLE,
    "$schema": LOCALLY_UNKNOWN,
    "additionalProperties": PROVIDER_COMPATIBLE,
    "allOf": PROVIDER_COMPATIBLE,
    "const": LOCALLY_UNKNOWN,
    "description": LOCALLY_UNKNOWN,
    "enum": LOCALLY_UNKNOWN,
    "if": PROVIDER_INCOMPATIBLE,
    "items": PROVIDER_COMPATIBLE,
    "maxItems": LOCALLY_UNKNOWN,
    "minItems": LOCALLY_UNKNOWN,
    "minLength": LOCALLY_UNKNOWN,
    "properties": PROVIDER_COMPATIBLE,
    "required": PROVIDER_COMPATIBLE,
    "then": PROVIDER_INCOMPATIBLE,
    "title": LOCALLY_UNKNOWN,
    "type": PROVIDER_COMPATIBLE,
    "else": PROVIDER_INCOMPATIBLE,
}


def collect_schema_constructs(schema: Any) -> set[str]:
    constructs: set[str] = set()

    def visit(node: Any) -> None:
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            constructs.add(key)
            if key in {"properties", "$defs", "definitions"} and isinstance(value, dict):
                for child in value.values():
                    visit(child)
            elif isinstance(value, dict):
                visit(value)
            elif key in {"allOf", "anyOf", "oneOf", "prefixItems"} and isinstance(value, list):
                for child in value:
                    visit(child)

    visit(schema)
    return constructs


def audit_schema_constructs(schema: Any) -> dict[str, str]:
    constructs = collect_schema_constructs(schema)
    return {
        construct: SCHEMA_CONSTRUCT_CLASSIFICATION.get(construct, LOCALLY_UNKNOWN)
        for construct in sorted(constructs)
    }


def audit_request_configuration(request: dict[str, Any], max_retries: int) -> dict[str, str]:
    format_config = request.get("text", {}).get("format", {})
    return {
        "model_identifier": UNKNOWN_SERVER_SIDE,
        "responses_api_path": LOCALLY_VERIFIED,
        "reasoning_parameter": LOCALLY_VERIFIED,
        "text_format_structure": LOCALLY_VERIFIED,
        "strict_setting": LOCALLY_VERIFIED,
        "strict_schema_subset": SUSPECT,
        "unsupported_conditionals_removed": LOCALLY_VERIFIED,
        "sdk_local_acceptance_is_server_acceptance": UNKNOWN_SERVER_SIDE,
        "tools_empty": LOCALLY_VERIFIED if request.get("tools") == [] else SUSPECT,
        "store_false": LOCALLY_VERIFIED if request.get("store") is False else SUSPECT,
        "max_retries_zero": LOCALLY_VERIFIED if max_retries == 0 else SUSPECT,
        "input_shape": LOCALLY_VERIFIED if isinstance(request.get("input"), str) else SUSPECT,
        "instructions_shape": (
            LOCALLY_VERIFIED if isinstance(request.get("instructions"), str) else SUSPECT
        ),
        "json_schema_format": (
            LOCALLY_VERIFIED
            if format_config.get("type") == "json_schema"
            and format_config.get("strict") is True
            else SUSPECT
        ),
    }
