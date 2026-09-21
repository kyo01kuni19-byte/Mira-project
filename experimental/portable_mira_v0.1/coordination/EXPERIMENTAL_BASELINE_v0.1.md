# MIRA-Codex Coordination Protocol v0.1

Status: EXPERIMENTAL BASELINE - NOT APPROVED MIRA

This checkpoint freezes the reviewed provider-independent coordination protocol in its tested single-executor, single-process scope. It preserves separation among Work Contract, Human Authorization, PRE_ACTION Decision, and Execution Evidence.

## Version Freeze Rule

After this v0.1 freeze, a change that materially breaks artifact semantic compatibility must not silently reuse the same frozen schema or protocol version. This includes authority-semantic changes, required-field incompatibility, hash-binding semantic changes, access-mode semantic changes, and action-class semantic changes.

This rule does not establish a version-management subsystem.

## Bounded Evidence Claim

Local deterministic tests support contract separation, exact canonical contract hash binding, action-class and access-mode enforcement, budget and baseline enforcement, fail-closed unknown dispatch, and the first Class-0 dogfood replay.

This checkpoint does not establish automated MIRA-to-Codex execution, cryptographically verified Human identity, concurrent or multi-process safety, general workflow-engine capability, production readiness, or Approved MIRA status.
