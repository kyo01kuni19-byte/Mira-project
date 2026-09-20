import tempfile
from pathlib import Path

from build import BuildError, build_file, deterministic_build


def test_reproducible_hash():
    source = "Portable MIRA - UTF8 test".encode("utf-8")
    a, _, _ = deterministic_build("t1", source)
    b, _, _ = deterministic_build("t1", source)
    assert a.source_hash_sha256 == b.source_hash_sha256
    assert a.artifact_hash_sha256 == b.artifact_hash_sha256


def test_base64_round_trip():
    source = bytes([0, 1, 2, 3, 10, 13, 31, 32, 65, 127]) + b"byte-exact"
    result, artifact, _ = deterministic_build("t2", source)
    assert artifact == source
    assert result.round_trip_match is True
    assert result.exact_content_match is True


def test_invalid_utf8_fails_closed():
    invalid = bytes([0xFF, 0xFE])
    try:
        deterministic_build("t3", invalid)
    except BuildError:
        return
    raise AssertionError("invalid UTF-8 must fail closed")


def test_local_readback():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "source.md"
        artifact = root / "artifact" / "source.md"
        source.write_bytes(bytes("North Star\nValue -> Reality\n", "utf-8"))
        result = build_file(source, artifact)
        assert result.build_status == "PASS"
        assert source.read_bytes() == artifact.read_bytes()


def test_source_unchanged_after_build():
    source = b"authoritative-source"
    before = bytes(source)
    deterministic_build("t5", source)
    assert source == before


if __name__ == "__main__":
    test_reproducible_hash()
    test_base64_round_trip()
    test_invalid_utf8_fails_closed()
    test_local_readback()
    test_source_unchanged_after_build()
    print("PASS: build pipeline v0.1 deterministic tests")
