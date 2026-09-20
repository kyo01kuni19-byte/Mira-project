from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


COMPILER_ID = "portable_mira.openai_provider_schema_compiler.v0.2"
CANONICAL_SCHEMA_SHA256 = "dc117d93a9d8040760228d0ce1c40c19e5578963b4961ce50050b269a44272e6"
UNSUPPORTED_CONDITIONAL_KEYWORDS = frozenset({"if", "then", "else"})


class ProviderSchemaCompilationError(Exception):
    pass


@dataclass(frozen=True)
class ProviderSchemaCompilation:
    compiler_id: str
    canonical_schema_sha256: str
    registry_sha256: str
    provider_schema_sha256: str
    removed_keywords: tuple[str, ...]
    initial_route_vocabulary: tuple[str, ...]
    semantic_dimension_vocabulary: tuple[str, ...]
    provider_schema: dict[str, Any]

    def artifact(self) -> dict[str, Any]:
        return {
            "artifact_type": "OPENAI_PROVIDER_SCHEMA_DERIVED_NOT_AUTHORITY",
            "compiler_id": self.compiler_id,
            "canonical_schema_sha256": self.canonical_schema_sha256,
            "registry_sha256": self.registry_sha256,
            "provider_schema_sha256": self.provider_schema_sha256,
            "removed_keywords": list(self.removed_keywords),
            "initial_route_vocabulary": list(self.initial_route_vocabulary),
            "semantic_dimension_vocabulary": list(
                self.semantic_dimension_vocabulary
            ),
            "provider_schema": copy.deepcopy(self.provider_schema),
        }


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def derive_route_vocabularies(
    registry_path: Path,
) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    registry_bytes = registry_path.read_bytes()
    registry_hash = hashlib.sha256(registry_bytes).hexdigest()
    try:
        registry = json.loads(registry_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProviderSchemaCompilationError("runtime registry is not valid JSON") from exc
    if not isinstance(registry, dict) or registry.get("artifact_type") != (
        "portable_mira.registry_runtime"
    ):
        raise ProviderSchemaCompilationError("runtime registry has unexpected authority type")
    routing = registry.get("routing")
    if not isinstance(routing, dict):
        raise ProviderSchemaCompilationError("runtime registry routing must be an object")
    edges = routing.get("normal_edges")
    if not isinstance(edges, list) or not edges:
        raise ProviderSchemaCompilationError("normal routing edges must be a non-empty list")

    initial_routes: set[str] = set()
    dimensions: set[str] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ProviderSchemaCompilationError(f"normal edge {index} must be an object")
        for field in ("id", "from", "trigger", "to"):
            if not isinstance(edge.get(field), str) or not edge[field]:
                raise ProviderSchemaCompilationError(
                    f"normal edge {index} has invalid field: {field}"
                )
        initial_routes.add(edge["from"])
        dimensions.update((edge["from"], edge["to"]))

    value_fit = routing.get("value_fit_reentry")
    if value_fit is not None:
        if not isinstance(value_fit, dict):
            raise ProviderSchemaCompilationError("value_fit_reentry must be an object")
        destination = value_fit.get("to")
        if not isinstance(destination, str) or not destination:
            raise ProviderSchemaCompilationError(
                "value_fit_reentry has invalid destination"
            )
        dimensions.add(destination)

    if any("->" in token for token in initial_routes | dimensions):
        raise ProviderSchemaCompilationError(
            "registered semantic token contains route-path syntax; MISSING DESIGN DECISION"
        )
    return tuple(sorted(initial_routes)), tuple(sorted(dimensions)), registry_hash


def compile_provider_schema(
    canonical_schema_path: Path, registry_path: Path
) -> ProviderSchemaCompilation:
    canonical_bytes = canonical_schema_path.read_bytes()
    canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()
    if canonical_hash != CANONICAL_SCHEMA_SHA256:
        raise ProviderSchemaCompilationError(
            "canonical schema is not the reviewed v0.1a input; MISSING DESIGN DECISION"
        )
    canonical = json.loads(canonical_bytes.decode("utf-8"))
    if not isinstance(canonical, dict):
        raise ProviderSchemaCompilationError("canonical schema must be an object")

    initial_routes, dimensions, registry_hash = derive_route_vocabularies(
        registry_path
    )

    removed: set[str] = set()
    provider_schema = _remove_deferred_conditionals(canonical, removed)
    if removed != {"if", "then"}:
        raise ProviderSchemaCompilationError(
            "conditional transformation set changed; MISSING DESIGN DECISION"
        )
    if _find_keywords(provider_schema, UNSUPPORTED_CONDITIONAL_KEYWORDS):
        raise ProviderSchemaCompilationError(
            "provider schema retains unsupported conditional keywords"
        )
    try:
        routing_properties = provider_schema["properties"]["routing_judgment"][
            "properties"
        ]
        routing_properties["proposed_initial_route"] = {
            "enum": [None, *initial_routes]
        }
        routing_properties["possible_secondary_dimensions"] = {
            "type": "array",
            "items": {"enum": list(dimensions)},
        }
    except (KeyError, TypeError) as exc:
        raise ProviderSchemaCompilationError(
            "canonical routing structure changed; MISSING DESIGN DECISION"
        ) from exc
    provider_hash = hashlib.sha256(canonical_json_bytes(provider_schema)).hexdigest()
    return ProviderSchemaCompilation(
        compiler_id=COMPILER_ID,
        canonical_schema_sha256=canonical_hash,
        registry_sha256=registry_hash,
        provider_schema_sha256=provider_hash,
        removed_keywords=tuple(sorted(removed)),
        initial_route_vocabulary=initial_routes,
        semantic_dimension_vocabulary=dimensions,
        provider_schema=provider_schema,
    )


def write_provider_schema_artifact(
    canonical_schema_path: Path, registry_path: Path, artifact_path: Path
) -> ProviderSchemaCompilation:
    compilation = compile_provider_schema(canonical_schema_path, registry_path)
    artifact_bytes = canonical_json_bytes(compilation.artifact())
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(artifact_bytes)
    if artifact_path.read_bytes() != artifact_bytes:
        raise ProviderSchemaCompilationError("provider schema artifact read-back mismatch")
    loaded = load_provider_schema_artifact(
        artifact_path, canonical_schema_path, registry_path
    )
    if loaded.provider_schema_sha256 != compilation.provider_schema_sha256:
        raise ProviderSchemaCompilationError("provider schema artifact hash mismatch")
    return compilation


def load_provider_schema_artifact(
    artifact_path: Path, canonical_schema_path: Path, registry_path: Path
) -> ProviderSchemaCompilation:
    expected = compile_provider_schema(canonical_schema_path, registry_path)
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProviderSchemaCompilationError("unable to load provider schema artifact") from exc
    if artifact != expected.artifact():
        raise ProviderSchemaCompilationError(
            "provider schema artifact is stale or non-canonical; rebuild required"
        )
    return expected


def _remove_deferred_conditionals(value: Any, removed: set[str]) -> Any:
    if isinstance(value, list):
        return [_remove_deferred_conditionals(item, removed) for item in value]
    if not isinstance(value, dict):
        return copy.deepcopy(value)

    result: dict[str, Any] = {}
    for key, child in value.items():
        if key in UNSUPPORTED_CONDITIONAL_KEYWORDS:
            removed.add(key)
            continue
        transformed = _remove_deferred_conditionals(child, removed)
        if key == "allOf" and isinstance(transformed, list):
            transformed = [entry for entry in transformed if entry != {}]
            if not transformed:
                continue
        result[key] = transformed
    return result


def _find_keywords(value: Any, keywords: frozenset[str]) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keywords:
                found.add(key)
            found.update(_find_keywords(child, keywords))
    elif isinstance(value, list):
        for child in value:
            found.update(_find_keywords(child, keywords))
    return found


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = write_provider_schema_artifact(
        root / "semantic" / "semantic_judgment_contract.schema.json",
        root / "generated" / "registry_runtime.json",
        root / "generated" / "openai_semantic_judgment_provider_schema.json",
    )
    print(result.provider_schema_sha256)
