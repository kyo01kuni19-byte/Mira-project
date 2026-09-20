from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class BuildError(Exception):
    """Deterministic build validation failure."""


@dataclass(frozen=True)
class BuildResult:
    source_id: str
    source_hash_sha256: str
    artifact_hash_sha256: str
    source_bytes: int
    artifact_bytes: int
    base64_characters: int
    round_trip_match: bool
    exact_content_match: bool
    build_status: str


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_utf8_source(data: bytes) -> str:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise BuildError("Source is not valid UTF-8") from exc
    if "\x00" in text:
        raise BuildError("Source contains a NUL character")
    return text


def deterministic_build(source_id: str, source_bytes: bytes) -> tuple[BuildResult, bytes, str]:
    """Build a byte-exact artifact and validate transport encoding round-trip.
    The artifact is intentionally identical to the source in v0.1.
    Future compilers may transform it, but must preserve this validation boundary.
    """
    validate_utf8_source(source_bytes)

    source_hash = sha256(source_bytes)
    artifact = bytes(source_bytes)
    artifact_hash = sha256(artifact)

    transport_b64 = base64.b64encode(artifact).decode("ascii")
    try:
        decoded = base64.b64decode(transport_b64, validate=True)
    except Exception as exc:
        raise BuildError("Deterministic Base64 round-trip failed") from exc

    round_trip_match = decoded == artifact
    exact_content_match = source_bytes == artifact

    if not round_trip_match:
        raise BuildError("Base64 round-trip changed artifact bytes")
    if not exact_content_match:
        raise BuildError("Artifact does not match source bytes")

    result = BuildResult(
        source_id=source_id,
        source_hash_sha256=source_hash,
        artifact_hash_sha256=artifact_hash,
        source_bytes=len(source_bytes),
        artifact_bytes=len(artifact),
        base64_characters=len(transport_b64),
        round_trip_match=round_trip_match,
        exact_content_match=exact_content_match,
        build_status="PASS",
    )
    return result, artifact, transport_b64


def build_file(source_path: Path, artifact_path: Path) -> BuildResult:
    source_bytes = source_path.read_bytes()
    result, artifact, _ = deterministic_build(str(source_path), source_bytes)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(artifact)
    readback = artifact_path.read_bytes()
    if sha256(readback) != result.artifact_hash_sha256:
        raise BuildError("Local artifact read-back hash mismatch")
    return result


def manifest_fields(result: BuildResult) -> dict[str, Any]:
    return {
        "source_id": result.source_id,
        "source_hash_sha256": result.source_hash_sha256,
        "artifact_hash_sha256": result.artifact_hash_sha256,
        "build_status": result.build_status,
        "exact_content_match": result.exact_content_match,
        "base64_round_trip_match": result.round_trip_match,
    }
