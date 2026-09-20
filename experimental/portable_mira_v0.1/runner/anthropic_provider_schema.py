from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anthropic


COMPILER_ID = "portable_mira.anthropic_annotation_provider_schema_compiler.v0.1"
CANONICAL_SCHEMA_SHA256 = "7f5a606cb2f347b854f1f85085427beb0c5e75053b8af6f952bccaf8d8cd7b1d"
SDK_LOCAL_ACCEPTANCE_PRINCIPLE = (
    "SDK_LOCAL_ACCEPTANCE != PROVIDER_SERVER_ACCEPTANCE"
)
PROVIDER_COMPATIBLE = "PROVIDER_COMPATIBLE"
PROVIDER_TRANSFORMABLE = "PROVIDER_TRANSFORMABLE"
PROVIDER_INCOMPATIBLE = "PROVIDER_INCOMPATIBLE"
LOCALLY_UNKNOWN = "LOCALLY_UNKNOWN"

SCHEMA_KEYWORDS = frozenset(
    {
        "$defs",
        "$id",
        "$ref",
        "$schema",
        "additionalProperties",
        "const",
        "description",
        "items",
        "minLength",
        "pattern",
        "properties",
        "required",
        "title",
        "type",
    }
)
SDK_RETAINED_KEYWORDS = frozenset(
    {
        "$defs",
        "$ref",
        "additionalProperties",
        "description",
        "items",
        "properties",
        "required",
        "title",
        "type",
    }
)
SDK_TRANSFORMABLE_KEYWORDS = frozenset({"$id", "$schema", "const"})
SDK_NON_ENFORCED_KEYWORDS = frozenset({"minLength", "pattern"})


class AnthropicProviderSchemaError(Exception):
    pass


@dataclass(frozen=True)
class AnthropicProviderSchemaCompilation:
    compiler_id: str
    sdk_version: str
    canonical_schema_sha256: str
    provider_schema_sha256: str
    construct_audit: dict[str, str]
    provider_schema: dict[str, Any]

    def artifact(self) -> dict[str, Any]:
        return {
            "artifact_type": "ANTHROPIC_PROVIDER_SCHEMA_DERIVED_NOT_AUTHORITY",
            "compiler_id": self.compiler_id,
            "sdk_version": self.sdk_version,
            "canonical_schema_sha256": self.canonical_schema_sha256,
            "provider_schema_sha256": self.provider_schema_sha256,
            "construct_audit": copy.deepcopy(self.construct_audit),
            "canonical_post_validation_required": True,
            "provider_server_compatibility": "UNKNOWN",
            "provider_schema": copy.deepcopy(self.provider_schema),
        }


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def collect_schema_constructs(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in SCHEMA_KEYWORDS:
                found.add(key)
            found.update(collect_schema_constructs(child))
    elif isinstance(value, list):
        for child in value:
            found.update(collect_schema_constructs(child))
    return found


def audit_schema_constructs(schema: dict[str, Any]) -> dict[str, str]:
    audit: dict[str, str] = {}
    for keyword in sorted(collect_schema_constructs(schema)):
        if keyword in SDK_RETAINED_KEYWORDS:
            audit[keyword] = PROVIDER_COMPATIBLE
        elif keyword in SDK_TRANSFORMABLE_KEYWORDS:
            audit[keyword] = PROVIDER_TRANSFORMABLE
        elif keyword in SDK_NON_ENFORCED_KEYWORDS:
            audit[keyword] = PROVIDER_INCOMPATIBLE
        else:
            audit[keyword] = LOCALLY_UNKNOWN
    return audit


def compile_provider_schema(
    canonical_schema_path: Path,
) -> AnthropicProviderSchemaCompilation:
    canonical_bytes = canonical_schema_path.read_bytes()
    canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()
    if canonical_hash != CANONICAL_SCHEMA_SHA256:
        raise AnthropicProviderSchemaError(
            "canonical annotation schema is not the reviewed v0.1 input; "
            "MISSING DESIGN DECISION"
        )
    try:
        canonical = json.loads(canonical_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise AnthropicProviderSchemaError(
            "canonical annotation schema is not valid UTF-8 JSON"
        ) from exc
    if not isinstance(canonical, dict):
        raise AnthropicProviderSchemaError("canonical annotation schema must be an object")

    prepared = _replace_const_with_single_value_enum(canonical)
    try:
        provider_schema = anthropic.transform_schema(prepared)
    except (TypeError, ValueError) as exc:
        raise AnthropicProviderSchemaError(
            "official Anthropic SDK could not transform the canonical schema"
        ) from exc

    audit = audit_schema_constructs(canonical)
    if set(audit) != collect_schema_constructs(canonical):
        raise AnthropicProviderSchemaError("canonical schema audit is incomplete")
    provider_hash = hashlib.sha256(canonical_json_bytes(provider_schema)).hexdigest()
    return AnthropicProviderSchemaCompilation(
        compiler_id=COMPILER_ID,
        sdk_version=anthropic.__version__,
        canonical_schema_sha256=canonical_hash,
        provider_schema_sha256=provider_hash,
        construct_audit=audit,
        provider_schema=provider_schema,
    )


def write_provider_schema_artifact(
    canonical_schema_path: Path, artifact_path: Path
) -> AnthropicProviderSchemaCompilation:
    compilation = compile_provider_schema(canonical_schema_path)
    artifact_bytes = canonical_json_bytes(compilation.artifact())
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(artifact_bytes)
    if artifact_path.read_bytes() != artifact_bytes:
        raise AnthropicProviderSchemaError("provider artifact read-back mismatch")
    load_provider_schema_artifact(artifact_path, canonical_schema_path)
    return compilation


def load_provider_schema_artifact(
    artifact_path: Path, canonical_schema_path: Path
) -> AnthropicProviderSchemaCompilation:
    expected = compile_provider_schema(canonical_schema_path)
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AnthropicProviderSchemaError("unable to load provider schema artifact") from exc
    if artifact != expected.artifact():
        raise AnthropicProviderSchemaError(
            "provider schema artifact is stale or non-canonical; rebuild required"
        )
    return expected


def bind_provider_schema(
    provider_schema: dict[str, Any],
    *,
    case_id: str,
    annotator_id: str,
    case_sha256: str,
    raw_output_sha256: str,
    annotation_schema_sha256: str,
) -> dict[str, Any]:
    bound = copy.deepcopy(provider_schema)
    try:
        metadata = bound["properties"]["annotation_metadata"]["properties"]
    except (KeyError, TypeError) as exc:
        raise AnthropicProviderSchemaError(
            "provider annotation metadata structure changed; MISSING DESIGN DECISION"
        ) from exc
    bindings = {
        "case_id": case_id,
        "annotator_id": annotator_id,
        "case_sha256": case_sha256,
        "raw_output_sha256": raw_output_sha256,
        "annotation_schema_sha256": annotation_schema_sha256,
    }
    for field, value in bindings.items():
        metadata[field] = {"type": "string", "enum": [value]}
    return bound


def _replace_const_with_single_value_enum(value: Any) -> Any:
    if isinstance(value, list):
        return [_replace_const_with_single_value_enum(item) for item in value]
    if not isinstance(value, dict):
        return copy.deepcopy(value)

    transformed = {
        key: _replace_const_with_single_value_enum(child)
        for key, child in value.items()
        if key != "const"
    }
    if "const" in value:
        if "enum" in value:
            raise AnthropicProviderSchemaError(
                "schema node contains both const and enum; MISSING DESIGN DECISION"
            )
        constant = copy.deepcopy(value["const"])
        transformed["enum"] = [constant]
        transformed.setdefault("type", _json_type(constant))
    return transformed


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    raise AnthropicProviderSchemaError("const value is not a JSON value")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = write_provider_schema_artifact(
        root / "semantic" / "output_annotation_contract.schema.json",
        root / "generated" / "anthropic_output_annotation_provider_schema.json",
    )
    print(result.provider_schema_sha256)
