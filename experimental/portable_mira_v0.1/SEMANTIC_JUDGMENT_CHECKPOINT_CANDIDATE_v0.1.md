# Portable MIRA v0.1 Semantic Judgment Checkpoint Candidate

Status:
EXPERIMENTAL CHECKPOINT CANDIDATE — NOT APPROVED

## Value Intent

Freeze a coherent, reproducible review candidate for the first model-independent
Semantic Judgment Adapter infrastructure and its tested OpenAI provider boundary,
while preserving the frozen deterministic runtime as the execution authority.

This checkpoint prepares evidence for Human/MIRA review. It does not approve,
promote, deploy, or establish general Semantic Judgment capability.

## Baseline

Frozen dependency:

- Portable MIRA v0.1 Deterministic Semantic Runtime Foundation
- Commit: `32eeebfa558455590b67b22fbbbc296ab0813948`

The baseline commit is the current repository HEAD. Its runtime registries, build
pipeline, Registry Loader, Router, and deterministic tests remain the frozen
foundation on which this checkpoint depends.

## Checkpoint Scope

This candidate adds, after the frozen baseline:

- Semantic Judgment Contract v0.1a and manual canonical validation
- Model-independent Semantic Judgment Adapter interface and integration path
- Registry-bound route ownership and impact diagnostics
- OpenAI Responses API adapter and provider-schema compiler
- Local development/regression fixtures
- Historical Call 1-4 evidence and derived diagnostic records
- Deterministic provider representation used by the adapter

It does not modify frozen Router semantics or source YAML registries.

## Included Components

### Semantic Contract

- `semantic/semantic_judgment_contract.schema.json`

### Semantic Runtime Interface

- `runner/semantic_judgment.py`
- `runner/semantic_adapter.py`
- `runner/route_boundary.py`
- `runner/impact_evaluation.py`

### OpenAI Provider Boundary

- `runner/openai_semantic_adapter.py`
- `runner/openai_provider_schema.py`
- `runner/openai_schema_audit.py`

### Tests

- `runner/test_semantic_judgment.py`
- `runner/test_semantic_adapter.py`
- `runner/test_openai_semantic_adapter.py`
- `runner/test_openai_provider_schema.py`
- `runner/test_openai_error_diagnostics.py`
- `runner/test_route_boundary.py`

### Development And Evaluation

- `evals/semantic_judgment/development_cases.json`
- `evals/semantic_judgment/LIVE-SJ-001-TRANSPORT-400.json`
- `evals/semantic_judgment/LIVE-SJ-001-SECOND-CALL.json`
- `evals/semantic_judgment/LIVE-SJ-001-CALL-3.json`
- `evals/semantic_judgment/LIVE-SJ-001-CALL-3-REGRESSION.json`
- `evals/semantic_judgment/LIVE-SJ-001-CALL-4.json`

### Derived Provider Representation

- `generated/openai_semantic_judgment_provider_schema.json`

The generated provider schema is a deterministic derived artifact, not semantic
authority. The canonical MIRA contract and runtime registry remain its inputs.

### Artifact Hygiene

- `.gitignore` excludes `__pycache__/`, `*.pyc`, and transient generated tests.
- The reproducible provider schema is explicitly retained for review.
- Historical live evidence is immutable evidence and is never regenerated.

## Excluded Capabilities

- Approved MIRA release or baseline promotion
- General Semantic Judgment capability
- Production readiness, deployment, or operational authorization
- Cross-platform or cross-provider verification
- General multi-agent coordination capability
- Autonomous authority or Inter-Entity Impact approval
- Model tools, web search, retrieval, file search, or code execution
- Complete Coordination Trace integration

## Call 1-4 Evidence Chronology

### Call 1

- One request, no retry
- HTTP 400 `BadRequestError`
- No provider semantic output
- Historical exact cause remains `UNKNOWN`

Later evidence that provider strict schemas do not support `if/then` made schema
incompatibility a supported candidate cause. It does not prove that conditionals
were the sole historical cause.

### Call 2

- One request, no retry
- HTTP 429
- `insufficient_quota` / `credit_balance_exhausted`
- No provider semantic output

### Call 3

- Provider transport and structured output: PASS
- Canonical MIRA validation: PASS
- Materiality, environment difference, causal restraint, and registered triggers:
  positive evidence
- Proposed initial route: `FAILURE->FRAMING`
- Trigger registry handoff: FAIL
- Deterministic routing: NOT RUN
- AI-agent impact classification: `IMPACT_INFLATION_CANDIDATE`

The Call-3 record remains unchanged. Its regression record decomposes partial
positive evidence from the initial-route and runtime-handoff failure.

### Call 4

- Provider transport and structured output: PASS
- Canonical and trigger registry validation: PASS
- Proposed initial route: `FAILURE`
- Deterministic Runtime selected `E03_FAILURE_FRAMING` and
  `E04_FRAMING_ENVIRONMENT`
- Runtime resolved route: `ENVIRONMENT`
- Boundary enforcement and full integration: PASS
- AI-agent impact classification remained an `IMPACT_INFLATION_CANDIDATE`

Call 4 is positive single-case evidence for the route-ownership control. It is not
general capability proof and does not retroactively rewrite Calls 1-3.

## Failure -> Learning -> Control -> Evaluation

### Chain A: Deterministic Transport

- Failure: LLM-authored Base64/transport corruption.
- Learning: deterministic operations should not be delegated to probabilistic
  language generation where avoidable.
- Control: local deterministic build and transport path.
- Evaluation: Build Pipeline operational PASS in the tested environment.

### Chain B: Provider Schema Boundary

- Failure: the canonical MIRA schema was sent directly to the provider and Call 1
  returned HTTP 400; the exact historical cause is unknown.
- Later evidence: provider strict structured output does not support `if/then`.
- Learning: provider structural guarantees and canonical MIRA semantics require a
  deliberate boundary.
- Control: Canonical MIRA Contract -> Provider Schema Compiler -> Provider output
  -> unchanged canonical MIRA validation.
- Evaluation: Calls 3 and 4 passed provider structured output and canonical
  validation. This is consistent with the control; it does not prove the sole cause
  of Call 1.

### Chain C: Route Ownership

- Failure: Call 3 authored compound route `FAILURE->FRAMING`.
- Learning: Semantic Agent and deterministic Runtime ownership was insufficiently
  enforced.
- Control: registry-derived initial-route vocabulary, provider structural enum,
  observational secondary dimensions, and Runtime-only graph traversal.
- Evaluation: Call 4 used `FAILURE`; Runtime alone resolved E03/E04 to
  `ENVIRONMENT`; full integration PASS for LIVE-SJ-001.

### Counter-Failure Candidate: Impact Inflation

- Candidate: operational impact on an AI agent was represented as potential
  Inter-Entity Impact.
- Control status: diagnostic/evaluation only.
- Evaluation: operationally affected, potential material impact, impact miss, and
  impact inflation remain distinct diagnostics.
- Normative status: no Entity rule was adopted; the diagnostic neither authorizes
  nor blocks execution.

## Semantic Judgment Evidence Claim

LIVE-SJ-001 provides one-case positive operational evidence that a real Semantic
Agent can identify material causal uncertainty and hand off registered semantics
through the MIRA Contract into deterministic Runtime.

This claim is limited to this case and tested configuration. It does not establish
general Semantic Judgment capability.

## Semantic Coordination Architecture Evidence Claim

Observed development coordination path:

Human -> MIRA semantic/design coordination -> Codex local execution -> OpenAI
Semantic Agent -> deterministic MIRA Runtime -> Codex evidence collection -> MIRA
evaluation -> Human decision

This is L1 Case evidence that the Human-Centered Semantic Coordination Layer
architecture coordinated differentiated roles in this experiment. It is not a
claim of general multi-agent capability.

## Relevant Hashes

- Baseline commit: `32eeebfa558455590b67b22fbbbc296ab0813948`
- Registry runtime: `05b3b77e6172e2c0011bd17e3b846b0220500f914d011226cd804c94b83e313a`
- Canonical Semantic Judgment schema:
  `dc117d93a9d8040760228d0ce1c40c19e5578963b4961ce50050b269a44272e6`
- Compiled provider schema:
  `17084f729a834710c95972a49d7be8a68e70e00a279dd40b9645f8b008beec4f`
- Provider artifact file:
  `ee6c14a5ef934a6bc1167a99f46580b0513a06b7d01f12a6fdfe4b0f38ef5980`
- Call 1: `2f8124fa11c6df8730f3a8413a16987603061241cdca17f02befadbb6e999132`
- Call 2: `208a51391bafe7995c53ebb6311def4ebff2ece03a5fbaadc9ef33c537fa1154`
- Call 3: `7f6cdacda1f2701bb6a02e4e7781f365d643f972a25fb9c34dc725307ee75dc4`
- Call-3 regression:
  `6dbca80cec9730839c468a78b578148bd281278d1a64a7ce7f09b55664b56319`
- Call 4: `63789644d8d06e00ea7a7d2b89631b4d86e79fe41df68f74e296a5c45d26a0c3`

## Validation Evidence

Local validation on 2026-09-20:

- Python syntax/compile: PASS
- Semantic route vocabulary boundary RB1-RB12: PASS
- OpenAI Provider Schema Compiler PS1-PS12: PASS
- OpenAI error diagnostics ER1-ER10: PASS
- OpenAI Adapter OA1-OA12: PASS
- Semantic Adapter FA1-FA12: PASS
- Semantic Judgment SJ1-SJ12: PASS
- Registry-backed Router: PASS
- Registry Loader deterministic tests: PASS
- Build Pipeline deterministic tests: PASS
- `git diff --check`: PASS
- Provider schema repeated rebuild: byte-identical and hash-identical PASS
- Historical evidence hash verification: PASS

No network request or credential access was used for checkpoint validation.

## Environment Facts

- Python: 3.14.5
- PyYAML: 6.0.3
- OpenAI Python SDK: 3.16.2
- Host used for evidence: macOS 26.6.2, arm64
- Git baseline/HEAD during validation:
  `32eeebfa558455590b67b22fbbbc296ab0813948`

These are environment facts for the recorded evidence, not cross-platform proof.

## Known Limitations And Unknowns

- One successful semantic live case only
- No true holdout evidence
- No cross-provider evidence
- No cross-platform evidence
- Evidence-reference discipline remains incomplete
- Secondary-dimension sparsity and relevance remain incomplete
- AI-agent impact inflation remains a candidate issue
- Evidence provenance and truth are not yet verified
- `value_fit_reentry` remains non-executable by the normal Router
- Coordination Trace integration remains incomplete
- JSON Schema/manual validator drift risk remains
- Security, performance, reliability, and production behavior are unverified

## Remaining Material Gaps

- True holdout evaluation without development-answer leakage
- Evidence-reference discipline and provenance validation
- Secondary-dimension relevance evaluation
- Impact-inflation evaluation without adopting premature normative Entity rules
- Contract/schema/manual-validator drift controls
- Complete trace-compatible adapter observability

## Next Proposed Evaluation Stage

Prepare Human/MIRA-reviewed holdout cases covering route selection, evidence
discipline, secondary-dimension relevance, authority restraint, and impact
inflation. Run them locally first, then separately authorize only the minimum live
evidence needed. Do not replay LIVE-SJ-001 merely to accumulate repetitions.

## Evidence Semantics Boundary

Artifact exists
!=
Test passed
!=
Control operational in tested scope
!=
General capability verified
!=
Approved capability
