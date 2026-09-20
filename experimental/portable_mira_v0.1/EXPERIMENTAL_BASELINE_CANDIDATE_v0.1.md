# Portable MIRA v0.1 Deterministic Semantic Runtime Foundation

**Status:** EXPERIMENTAL BASELINE CANDIDATE — NOT APPROVED

## Purpose

Freeze the first validated deterministic foundation before Semantic Judgment / LLM integration. This candidate is prepared for Human/MIRA review only. It is not an Approved MIRA baseline, release, deployment authorization, or production capability claim.

## Value Intent

Test whether human/MIRA-editable YAML semantic registries can be deterministically validated and compiled into a canonical machine runtime representation, then used for deterministic routing without silently changing semantic meaning. Preserve explicit Authority and Inter-Entity blocking boundaries and fail closed when required knowledge references cannot be resolved.

## Evidence Boundary

The evidence levels remain distinct:

`Artifact exists` != `Test passed` != `Control operational in tested scope` != `General capability verified` != `Approved capability`

The recorded PASS results establish only the behavior exercised by the listed tests in the recorded environment.

## Included Components

Human/MIRA-editable experimental sources and schemas:

- `runtime/routing_edges.yaml`
- `runtime/knowledge_registry.yaml`
- `runtime/impact_boundary.yaml`
- `runtime/coordination_trace.schema.yaml`
- `build/build_manifest.schema.yaml`

Deterministic implementation and tests:

- `runner/registry_loader.py`
- `runner/router.py`
- `runner/test_registry_loader.py`
- `runner/test_router.py`
- `build/build.py`
- `build/test_build.py`

Reviewable derived artifact:

- `generated/registry_runtime.json`
  - SHA-256: `05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a`
  - Derived from the YAML registry sources; never an independent authority.

Candidate metadata and hygiene:

- `.gitignore`
- `EXPERIMENTAL_BASELINE_CANDIDATE_v0.1.md`

`SEMANTIC_CORE_01.md` remains contextual experimental material and is not included as an implementation component of this foundation candidate.

## Validation Evidence

Executed from the repository root on 2026-09-20:

```text
./.venv/bin/python experimental/portable_mira_v0.1/runner/registry_loader.py
PASS: registry loader v0.1 05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a

shasum -a 256 experimental/portable_mira_v0.1/generated/registry_runtime.json
05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a  experimental/portable_mira_v0.1/generated/registry_runtime.json

./.venv/bin/python -m py_compile experimental/portable_mira_v0.1/runner/registry_loader.py experimental/portable_mira_v0.1/runner/router.py experimental/portable_mira_v0.1/runner/test_registry_loader.py experimental/portable_mira_v0.1/runner/test_router.py experimental/portable_mira_v0.1/build/build.py experimental/portable_mira_v0.1/build/test_build.py
PASS (exit 0; no output)

./.venv/bin/python experimental/portable_mira_v0.1/runner/test_registry_loader.py
PASS: registry loader v0.1 deterministic tests 05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a

./.venv/bin/python experimental/portable_mira_v0.1/runner/test_router.py
PASS: registry-backed router v0.1 tests

./.venv/bin/python experimental/portable_mira_v0.1/build/test_build.py
PASS: build pipeline v0.1 deterministic tests
```

Registry-loader tests verify repeated build byte identity, SHA-256 identity, read-back equality, duplicate Edge ID rejection, unresolved knowledge rejection, separation of `value_fit_reentry`, and unchanged YAML source bytes.

Router tests verify NO_ROUTE behavior, the `FAILURE -> FRAMING -> ENVIRONMENT` path, Authority and Inter-Entity global blocking, fail-closed unresolved knowledge behavior, and generated-registry execution using an artifact-only sentinel Edge ID.

## Evidence Environment

- Operating system: `macOS-26.6.2-arm64-arm-64bit-Mach-O`
- Python: `3.14.5` from the repository `.venv`
- Python implementation build: `Clang 21.0.0 (clang-2100.0.123.102)`
- PyYAML: `6.0.3`
- Canonical JSON policy: UTF-8, sorted keys, compact stable separators, one trailing newline
- External network access or package installation: not used

## Excluded or Unverified Capabilities

- Semantic Judgment, trigger discovery, materiality judgment, or LLM integration
- General MIRA capability or semantic preservation beyond the tested registries and paths
- Execution of `value_fit_reentry` by the Router
- Exhaustive execution testing of every routing edge and trigger combination
- Runtime derivation of Authority or Inter-Entity impact state
- Full schema validation of emitted Coordination Trace objects
- Runtime validation of `impact_boundary.yaml` as an executable policy
- Cross-platform, cross-version, concurrency, performance, security, deployment, and production verification
- Approved MIRA status, release status, or promotion authority

## Known Limitations

- The Router accepts already-established trigger and boundary states; it does not decide whether they are true.
- The canonical registry is validated against YAML during its build, but the Router does not independently rebuild from YAML or compare hashes when loading it.
- Knowledge resolution proves address presence in the compiled registry; physical source retrieval remains adapter-resolved and unverified.
- Coordination Trace output is observable state only and has not been validated by a machine-enforced schema validator.
- PASS evidence is local to the recorded environment and test inputs.

## Next Material Gap

Define and review the Semantic Judgment boundary: how trigger and materiality assertions are established, evidenced, represented in Coordination Trace, and kept separate from deterministic routing. Human/MIRA validation is required before introducing an LLM or promoting this candidate.
