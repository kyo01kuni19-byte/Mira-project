from __future__ import annotations

import copy
import inspect
from pathlib import Path

from coordination_protocol import (
    CONCURRENCY_MODE,
    SELF_HASH_RULE,
    CoordinationProtocolError,
    assess_execution_evidence,
    build_pre_action_decision_artifact,
    canonical_content_sha256,
    file_bytes_sha256,
    validate_human_authorization,
    validate_pre_action,
    validate_pre_action_decision_artifact,
    validate_pre_action_decision_binding,
    validate_schema_artifacts,
    validate_work_contract,
    verify_design_baseline,
)


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "baseline-001"
HUMAN_REQUEST = {
    "state": "HUMAN_REQUEST_CONFIRMED",
    "reference_id": "current-user-request",
}


def action(
    action_id: str,
    action_class: str,
    operation: str,
    *,
    provider: str | None = None,
    paths: tuple[str, ...] = (),
    resources: tuple[str, ...] = (),
    access_mode: str = "METADATA_ONLY",
) -> dict:
    return {
        "action_id": action_id,
        "action_class": action_class,
        "operation": operation,
        "provider": provider,
        "access_mode": access_mode,
        "paths": list(paths),
        "resources": list(resources),
    }


def contract(
    allowed: list[dict],
    *,
    contract_id: str = "WC-001",
    created_by: str = "HUMAN",
    forbidden: list[dict] | None = None,
    mismatch_policy: str = "BLOCKED",
    network_budget: int = 1,
) -> dict:
    path_modes = {path: item["access_mode"] for item in allowed for path in item["paths"]}
    resources = sorted({resource for item in allowed for resource in item["resources"]})
    providers = sorted(
        {item["provider"] for item in allowed if item["provider"] is not None}
    )
    return {
        "artifact_type": "WORK_CONTRACT",
        "protocol_version": "portable_mira.coordination.v0.1",
        "work_contract_id": contract_id,
        "created_by": created_by,
        "objective": "Validate one bounded action without executing it.",
        "value_intent": "Preserve Human authority and observable evidence.",
        "baseline_refs": {
            "expected_baseline": BASELINE,
            "immutable_artifacts": [],
            "baseline_mismatch_policy": mismatch_policy,
        },
        "scope": {
            "path_permissions": [
                {"path": path, "access_mode": path_modes[path]}
                for path in sorted(path_modes)
            ],
            "forbidden_paths": ["forbidden/path"],
            "permitted_resources": resources,
            "forbidden_resources": ["forbidden-resource"],
            "permitted_providers": providers,
            "forbidden_providers": ["forbidden-provider"],
        },
        "allowed_actions": copy.deepcopy(allowed),
        "forbidden_actions": copy.deepcopy(forbidden or []),
        "network_budget": network_budget,
        "credential_policy": "FORBIDDEN",
        "execution_mode": "LOCAL_VALIDATION_ONLY",
        "concurrency_mode": CONCURRENCY_MODE,
        "expected_evidence": ["pre-action decision"],
        "stop_conditions": ["any scope or authorization mismatch"],
        "status": "AUTHORIZED",
    }


def authorization(work_contract: dict, authorized: list[dict], *, limit: int = 1) -> dict:
    path_modes = {path: item["access_mode"] for item in authorized for path in item["paths"]}
    resources = sorted({resource for item in authorized for resource in item["resources"]})
    providers = sorted(
        {item["provider"] for item in authorized if item["provider"] is not None}
    )
    return {
        "artifact_type": "HUMAN_AUTHORIZATION",
        "protocol_version": "portable_mira.coordination.v0.1",
        "authorization_id": "AUTH-001",
        "work_contract_id": work_contract["work_contract_id"],
        "work_contract_canonical_content_sha256": canonical_content_sha256(work_contract),
        "authorized_by": "HUMAN",
        "human_confirmation_state": "HUMAN_CONFIRMATION_RECORDED",
        "confirmation_reference": {
            "method": "OUT_OF_BAND_EXPLICIT_CONFIRMATION",
            "reference_id": "human-confirmation-001",
        },
        "cryptographic_human_identity_verification": "NOT_IMPLEMENTED",
        "authorized_actions": copy.deepcopy(authorized),
        "explicitly_not_authorized": [],
        "action_budget": [
            {"action_id": item["action_id"], "limit": limit} for item in authorized
        ],
        "resource_scope": {
            "path_permissions": [
                {"path": path, "access_mode": path_modes[path]}
                for path in sorted(path_modes)
            ],
            "resources": resources,
            "providers": providers,
        },
        "concurrency_mode": CONCURRENCY_MODE,
        "authorization_state": "ACTIVE",
        "supersedes": None,
    }


def authorization_confirmation(work_contract: dict, auth: dict) -> dict:
    return {
        "state": "HUMAN_CONFIRMATION_RECORDED",
        "method": "OUT_OF_BAND_EXPLICIT_CONFIRMATION",
        "reference_id": auth["confirmation_reference"]["reference_id"],
        "work_contract_canonical_content_sha256": canonical_content_sha256(work_contract),
    }


def pre_action(work_contract: dict, requested_action: dict) -> dict:
    decision = validate_pre_action(
        work_contract,
        requested_action,
        BASELINE,
        human_request_confirmation=HUMAN_REQUEST,
    )
    return build_pre_action_decision_artifact(
        "PRE-001", work_contract, requested_action, decision
    )


def evidence(work_contract: dict, performed: list[dict], pre: dict | None = None) -> dict:
    pre = pre or pre_action(work_contract, performed[0] if performed else work_contract["allowed_actions"][0])
    return {
        "artifact_type": "EXECUTION_EVIDENCE",
        "protocol_version": "portable_mira.coordination.v0.1",
        "evidence_id": "EVIDENCE-001",
        "work_contract_id": work_contract["work_contract_id"],
        "work_contract_canonical_content_sha256": canonical_content_sha256(work_contract),
        "authorization_ref": None,
        "pre_action_decision_ref": pre["decision_id"],
        "pre_action_decision_canonical_content_sha256": canonical_content_sha256(pre),
        "executor": "CODEX",
        "concurrency_mode": CONCURRENCY_MODE,
        "attempt_index": 1,
        "previous_evidence_ref": None,
        "expected_baseline": BASELINE,
        "observed_baseline": BASELINE,
        "actions_performed": copy.deepcopy(performed),
        "actions_not_performed": [],
        "request_counts": [],
        "files_changed": [],
        "tests_checks": [],
        "observed_results": [],
        "failures": [],
        "assumptions": [],
        "unknowns": [],
        "artifact_integrity": [],
        "git_state": {
            "head": "local-head",
            "branch": "local-branch",
            "staged_paths": [],
            "unstaged_paths": [],
            "untracked_paths": [],
        },
        "self_hash_rule": SELF_HASH_RULE,
        "execution_state": "EXECUTION_COMPLETE",
    }


OPENAI = action(
    "openai-request",
    "CLASS_2_EXTERNAL_BOUNDED_ACTION",
    "responses.create",
    provider="openai",
    resources=("case-001",),
)
ANTHROPIC = action(
    "anthropic-request",
    "CLASS_2_EXTERNAL_BOUNDED_ACTION",
    "messages.create",
    provider="anthropic",
    resources=("case-001",),
)
READ = action(
    "read-repository",
    "CLASS_0_READ_ANALYZE",
    "read",
    paths=("experimental/portable_mira_v0.1",),
    access_mode="CONTENT_READ",
)
EDIT = action(
    "edit-experiment",
    "CLASS_1_LOCAL_REVERSIBLE_CHANGE",
    "modify",
    paths=("experimental/portable_mira_v0.1/coordination",),
    access_mode="CONTENT_WRITE",
)
STAGE_COMMIT = action(
    "stage-commit",
    "CLASS_3_PERSISTENT_REPOSITORY_ACTION",
    "stage_and_commit",
    paths=("experimental/portable_mira_v0.1/coordination",),
    access_mode="CONTENT_WRITE",
)
PUSH = action(
    "push-origin",
    "CLASS_4_EXTERNAL_PERSISTENT_ACTION",
    "git_push",
    provider="git",
    resources=("origin/current-branch",),
)


def test_mc1_external_request_without_human_authorization_is_blocked() -> None:
    result = validate_pre_action(contract([OPENAI]), OPENAI, BASELINE)
    assert result.state == "BLOCKED"
    assert "HUMAN_AUTHORIZATION_REQUIRED" in result.diagnostics


def test_mc2_capability_or_credential_does_not_replace_authorization() -> None:
    work = contract([OPENAI], created_by="CODEX")
    result = validate_pre_action(work, OPENAI, BASELINE)
    assert result.state == "BLOCKED"
    assert result.action_executed is False


def test_mc3_second_request_exceeds_single_request_budget() -> None:
    work = contract([OPENAI])
    auth = authorization(work, [OPENAI], limit=1)
    confirmation = authorization_confirmation(work, auth)
    first = validate_pre_action(
        work,
        OPENAI,
        BASELINE,
        authorization=auth,
        human_authorization_confirmation=confirmation,
    )
    second = validate_pre_action(
        work,
        OPENAI,
        BASELINE,
        authorization=auth,
        human_authorization_confirmation=confirmation,
        consumed_count=1,
    )
    assert first.state == "AUTHORIZED"
    assert first.remaining_budget_after_action == 0
    assert second.state == "BLOCKED"
    assert "ACTION_BUDGET_EXHAUSTED" in second.diagnostics


def test_mc4_provider_scope_mismatch_is_blocked() -> None:
    work = contract([OPENAI, ANTHROPIC], network_budget=2)
    auth = authorization(work, [OPENAI])
    result = validate_pre_action(
        work,
        ANTHROPIC,
        BASELINE,
        authorization=auth,
        human_authorization_confirmation=authorization_confirmation(work, auth),
    )
    assert result.state == "BLOCKED"
    assert "ACTION_NOT_AUTHORIZED" in result.diagnostics


def test_mc5_local_change_authorization_cannot_authorize_push() -> None:
    work = contract([EDIT, PUSH])
    auth = authorization(work, [EDIT])
    result = validate_pre_action(
        work,
        PUSH,
        BASELINE,
        authorization=auth,
        human_authorization_confirmation=authorization_confirmation(work, auth),
    )
    assert result.state == "BLOCKED"
    assert "ACTION_NOT_AUTHORIZED" in result.diagnostics


def test_mc6_contract_mutation_invalidates_authorization() -> None:
    work = contract([OPENAI])
    auth = authorization(work, [OPENAI])
    mutated = copy.deepcopy(work)
    mutated["objective"] = "Materially changed objective."
    result = validate_pre_action(
        mutated,
        OPENAI,
        BASELINE,
        authorization=auth,
        human_authorization_confirmation=authorization_confirmation(work, auth),
    )
    assert result.state == "BLOCKED"
    assert "AUTHORIZATION_CONTRACT_HASH_MISMATCH" in result.diagnostics


def test_mc7_baseline_mismatch_is_blocked() -> None:
    result = validate_pre_action(
        contract([READ]),
        READ,
        "different-baseline",
        human_request_confirmation=HUMAN_REQUEST,
    )
    assert result.state == "BLOCKED"
    assert "BASELINE_MISMATCH" in result.diagnostics


def test_mc8_unsupported_execution_claim_is_unknown() -> None:
    work = contract([PUSH])
    claimed = copy.deepcopy(PUSH)
    claimed.update({"claim_state": "CLAIMED", "evidence_refs": []})
    pre = pre_action(work, PUSH)
    result = assess_execution_evidence(evidence(work, [claimed], pre), work, pre)
    assert result.state == "UNKNOWN"
    assert result.evidence_authorizes_new_work is False


def test_mc9_mira_recommendation_is_not_human_authorization() -> None:
    work = contract([OPENAI], created_by="MIRA")
    result = validate_pre_action(work, OPENAI, BASELINE)
    assert result.state == "BLOCKED"
    assert "HUMAN_AUTHORIZATION_REQUIRED" in result.diagnostics


def test_mc10_authorization_cannot_be_reused_for_different_contract() -> None:
    first = contract([OPENAI], contract_id="WC-FIRST")
    auth = authorization(first, [OPENAI])
    second = contract([OPENAI], contract_id="WC-SECOND")
    result = validate_pre_action(
        second,
        OPENAI,
        BASELINE,
        authorization=auth,
        human_authorization_confirmation=authorization_confirmation(first, auth),
    )
    assert result.state == "BLOCKED"
    assert "AUTHORIZATION_CONTRACT_ID_MISMATCH" in result.diagnostics


def test_pc1_class0_analysis_is_authorized_without_separate_authorization() -> None:
    result = validate_pre_action(
        contract([READ]),
        READ,
        BASELINE,
        human_request_confirmation=HUMAN_REQUEST,
    )
    assert result.state == "AUTHORIZED"
    assert result.action_executed is False


def test_pc2_class1_change_is_authorized_without_separate_authorization() -> None:
    result = validate_pre_action(
        contract([EDIT]),
        EDIT,
        BASELINE,
        human_request_confirmation=HUMAN_REQUEST,
    )
    assert result.state == "AUTHORIZED"
    assert result.action_executed is False


def test_pc3_exact_openai_request_passes_pre_action_validation() -> None:
    work = contract([OPENAI])
    auth = authorization(work, [OPENAI])
    result = validate_pre_action(
        work,
        OPENAI,
        BASELINE,
        authorization=auth,
        human_authorization_confirmation=authorization_confirmation(work, auth),
    )
    assert result.state == "AUTHORIZED"
    assert result.remaining_budget_after_action == 0
    assert result.action_executed is False


def test_pc4_exact_stage_commit_passes_pre_action_validation_only() -> None:
    work = contract([STAGE_COMMIT])
    auth = authorization(work, [STAGE_COMMIT])
    result = validate_pre_action(
        work,
        STAGE_COMMIT,
        BASELINE,
        authorization=auth,
        human_authorization_confirmation=authorization_confirmation(work, auth),
    )
    assert result.state == "AUTHORIZED"
    assert result.validation_only is True
    assert result.action_executed is False


def test_cprot1_schemas_are_closed_and_well_formed() -> None:
    validate_schema_artifacts(ROOT / "coordination" / "schemas")
    work = contract([READ])
    auth = authorization(contract([OPENAI]), [OPENAI])
    pre = pre_action(work, READ)
    record = evidence(work, [], pre)
    validators = (
        (validate_work_contract, work),
        (validate_human_authorization, auth),
        (lambda value: assess_execution_evidence(value, work, pre), record),
        (validate_pre_action_decision_artifact, pre),
    )
    for validator, artifact in validators:
        invalid = copy.deepcopy(artifact)
        invalid["unexpected"] = True
        try:
            validator(invalid)
        except CoordinationProtocolError as exc:
            assert "additional=['unexpected']" in str(exc)
        else:
            raise AssertionError("unknown coordination artifact field was accepted")


def test_cprot2_canonical_hash_is_deterministic() -> None:
    work = contract([READ])
    reordered = dict(reversed(list(work.items())))
    assert canonical_content_sha256(work) == canonical_content_sha256(reordered)


def test_cprot3_human_field_alone_is_not_authorization() -> None:
    work = contract([OPENAI])
    auth = authorization(work, [OPENAI])
    auth["human_confirmation_state"] = "MISSING"
    try:
        validate_human_authorization(auth)
    except CoordinationProtocolError as exc:
        assert "human_confirmation_state" in str(exc)
    else:
        raise AssertionError("authorized_by=HUMAN was accepted without confirmation")


def test_cprot4_single_executor_single_process_is_enforced() -> None:
    result = validate_pre_action(
        contract([READ]),
        READ,
        BASELINE,
        human_request_confirmation=HUMAN_REQUEST,
        executor_count=2,
    )
    assert result.state == "BLOCKED"
    assert "SINGLE_EXECUTOR_SINGLE_PROCESS_REQUIRED" in result.diagnostics


def test_cprot5_unknown_dispatch_consumes_budget() -> None:
    work = contract([OPENAI])
    auth = authorization(work, [OPENAI], limit=1)
    result = validate_pre_action(
        work,
        OPENAI,
        BASELINE,
        authorization=auth,
        human_authorization_confirmation=authorization_confirmation(work, auth),
        unknown_dispatch_count=1,
    )
    assert result.state == "BLOCKED"
    assert "ACTION_BUDGET_EXHAUSTED" in result.diagnostics


def test_cprot6_validator_has_no_executor_network_or_credential_capability() -> None:
    import coordination_protocol

    source = inspect.getsource(coordination_protocol)
    prohibited = (
        "os" + "." + "environ",
        "OPENAI_" + "API" + "_KEY",
        "ANTHROPIC_" + "API" + "_KEY",
        "import socket",
        "import requests",
        "import urllib",
        "import openai",
        "import anthropic",
        "subprocess",
    )
    assert not any(item in source for item in prohibited)
    assert not any(name.startswith("execute_") for name in dir(coordination_protocol))


def test_cprot7_observable_evidence_is_supported_without_granting_authority() -> None:
    work = contract([READ])
    supported = copy.deepcopy(READ)
    supported.update(
        {"claim_state": "OBSERVABLY_SUPPORTED", "evidence_refs": ["local:test-log"]}
    )
    pre = pre_action(work, READ)
    result = assess_execution_evidence(evidence(work, [supported], pre), work, pre)
    assert result.state == "OBSERVABLY_SUPPORTED"
    assert result.evidence_authorizes_new_work is False


def test_cprot8_human_validation_baseline_policy_is_preserved() -> None:
    work = contract([READ], mismatch_policy="HUMAN_VALIDATION_REQUIRED")
    result = validate_pre_action(
        work,
        READ,
        "different-baseline",
        human_request_confirmation=HUMAN_REQUEST,
    )
    assert result.state == "HUMAN_VALIDATION_REQUIRED"


def test_cprot9_local_action_still_requires_valid_human_request_context() -> None:
    result = validate_pre_action(contract([READ], created_by="MIRA"), READ, BASELINE)
    assert result.state == "BLOCKED"
    assert "VALID_HUMAN_REQUEST_CONTEXT_REQUIRED" in result.diagnostics


def test_cprot10_explicit_forbidden_action_is_blocked() -> None:
    result = validate_pre_action(
        contract([READ], forbidden=[READ]),
        READ,
        BASELINE,
        human_request_confirmation=HUMAN_REQUEST,
    )
    assert result.state == "BLOCKED"
    assert "ACTION_EXPLICITLY_FORBIDDEN" in result.diagnostics


def test_cprot11_reviewed_design_baseline_is_unchanged() -> None:
    verify_design_baseline(ROOT)


def test_cprot12_git_success_requires_git_observable_evidence() -> None:
    work = contract([PUSH])
    unsupported = copy.deepcopy(PUSH)
    unsupported.update(
        {
            "claim_state": "OBSERVABLY_SUPPORTED",
            "evidence_refs": ["local:unverified-claim"],
        }
    )
    pre = pre_action(work, PUSH)
    result = assess_execution_evidence(evidence(work, [unsupported], pre), work, pre)
    assert result.state == "UNKNOWN"
    assert "GIT_OBSERVABLE_SUPPORT_MISSING" in result.diagnostics


def test_cprot13_authorization_artifact_alone_cannot_synthesize_authority() -> None:
    work = contract([OPENAI])
    auth = authorization(work, [OPENAI])
    result = validate_pre_action(work, OPENAI, BASELINE, authorization=auth)
    assert result.state == "BLOCKED"
    assert "OUT_OF_BAND_HUMAN_CONFIRMATION_REQUIRED" in result.diagnostics


def test_cr1_metadata_permission_does_not_permit_content_read() -> None:
    work = contract([READ])
    work["scope"]["path_permissions"][0]["access_mode"] = "METADATA_ONLY"
    result = validate_pre_action(work, READ, BASELINE, human_request_confirmation=HUMAN_REQUEST)
    assert result.state == "BLOCKED"
    assert "PATH_ACCESS_MODE_EXCEEDED" in result.diagnostics


def test_cr2_content_read_permission_does_not_permit_write() -> None:
    work = contract([EDIT])
    work["scope"]["path_permissions"][0]["access_mode"] = "CONTENT_READ"
    result = validate_pre_action(work, EDIT, BASELINE, human_request_confirmation=HUMAN_REQUEST)
    assert result.state == "BLOCKED"
    assert "PATH_ACCESS_MODE_EXCEEDED" in result.diagnostics


def test_cr3_class1_content_write_is_authorized_in_scope() -> None:
    result = validate_pre_action(contract([EDIT]), EDIT, BASELINE, human_request_confirmation=HUMAN_REQUEST)
    assert result.state == "AUTHORIZED"
    assert result.action_executed is False


def test_cr4_pre_action_cannot_claim_action_executed() -> None:
    work = contract([READ]); artifact = pre_action(work, READ); artifact["action_executed"] = True
    try:
        validate_pre_action_decision_artifact(artifact)
    except CoordinationProtocolError as exc:
        assert "action_executed" in str(exc)
    else:
        raise AssertionError("PRE_ACTION action_executed=true was accepted")


def test_cr5_wrong_pre_action_hash_makes_evidence_unknown() -> None:
    work = contract([READ]); pre = pre_action(work, READ); record = evidence(work, [], pre)
    record["pre_action_decision_canonical_content_sha256"] = "0" * 64
    result = assess_execution_evidence(record, work, pre)
    assert result.state == "UNKNOWN"
    assert "EVIDENCE_PRE_ACTION_HASH_MISMATCH" in result.diagnostics


def test_cr6_file_bytes_hash_cannot_replace_canonical_contract_hash() -> None:
    work = contract([OPENAI]); auth = authorization(work, [OPENAI])
    auth["work_contract_canonical_content_sha256"] = file_bytes_sha256(Path(__file__))
    result = validate_pre_action(work, OPENAI, BASELINE, authorization=auth, human_authorization_confirmation=authorization_confirmation(work, auth))
    assert result.state == "BLOCKED"
    assert "AUTHORIZATION_CONTRACT_HASH_MISMATCH" in result.diagnostics


def test_cr7_canonical_mutation_invalidates_authorization() -> None:
    work = contract([OPENAI]); auth = authorization(work, [OPENAI]); mutated = copy.deepcopy(work)
    mutated["value_intent"] = "Changed semantic content in otherwise valid JSON."
    result = validate_pre_action(mutated, OPENAI, BASELINE, authorization=auth, human_authorization_confirmation=authorization_confirmation(mutated, auth))
    assert result.state == "BLOCKED"
    assert "AUTHORIZATION_CONTRACT_HASH_MISMATCH" in result.diagnostics


def test_cr8_self_referential_file_hash_is_rejected() -> None:
    work = contract([READ]); artifact = pre_action(work, READ); artifact["file_bytes_sha256"] = "0" * 64
    try:
        validate_pre_action_decision_artifact(artifact)
    except CoordinationProtocolError as exc:
        assert "file_bytes_sha256" in str(exc)
    else:
        raise AssertionError("self-referential file hash field was accepted")


def test_cr9_cursor_metadata_inspection_is_representable_without_content() -> None:
    inspect_cursor = action("inspect-cursor-status", "CLASS_0_READ_ANALYZE", "inspect_path_metadata", paths=(".cursor/mcp.json",), access_mode="METADATA_ONLY")
    result = validate_pre_action(contract([inspect_cursor]), inspect_cursor, BASELINE, human_request_confirmation=HUMAN_REQUEST)
    assert result.state == "AUTHORIZED"
    assert inspect_cursor["access_mode"] == "METADATA_ONLY"


def test_cr10_pre_action_cannot_be_reused_for_different_action() -> None:
    work = contract([READ, EDIT]); artifact = pre_action(work, READ)
    result = validate_pre_action_decision_binding(artifact, work, EDIT)
    assert result.state == "BLOCKED"
    assert "PRE_ACTION_ACTION_MISMATCH" in result.diagnostics


if __name__ == "__main__":
    tests = (
        test_mc1_external_request_without_human_authorization_is_blocked,
        test_mc2_capability_or_credential_does_not_replace_authorization,
        test_mc3_second_request_exceeds_single_request_budget,
        test_mc4_provider_scope_mismatch_is_blocked,
        test_mc5_local_change_authorization_cannot_authorize_push,
        test_mc6_contract_mutation_invalidates_authorization,
        test_mc7_baseline_mismatch_is_blocked,
        test_mc8_unsupported_execution_claim_is_unknown,
        test_mc9_mira_recommendation_is_not_human_authorization,
        test_mc10_authorization_cannot_be_reused_for_different_contract,
        test_pc1_class0_analysis_is_authorized_without_separate_authorization,
        test_pc2_class1_change_is_authorized_without_separate_authorization,
        test_pc3_exact_openai_request_passes_pre_action_validation,
        test_pc4_exact_stage_commit_passes_pre_action_validation_only,
        test_cprot1_schemas_are_closed_and_well_formed,
        test_cprot2_canonical_hash_is_deterministic,
        test_cprot3_human_field_alone_is_not_authorization,
        test_cprot4_single_executor_single_process_is_enforced,
        test_cprot5_unknown_dispatch_consumes_budget,
        test_cprot6_validator_has_no_executor_network_or_credential_capability,
        test_cprot7_observable_evidence_is_supported_without_granting_authority,
        test_cprot8_human_validation_baseline_policy_is_preserved,
        test_cprot9_local_action_still_requires_valid_human_request_context,
        test_cprot10_explicit_forbidden_action_is_blocked,
        test_cprot11_reviewed_design_baseline_is_unchanged,
        test_cprot12_git_success_requires_git_observable_evidence,
        test_cprot13_authorization_artifact_alone_cannot_synthesize_authority,
        test_cr1_metadata_permission_does_not_permit_content_read,
        test_cr2_content_read_permission_does_not_permit_write,
        test_cr3_class1_content_write_is_authorized_in_scope,
        test_cr4_pre_action_cannot_claim_action_executed,
        test_cr5_wrong_pre_action_hash_makes_evidence_unknown,
        test_cr6_file_bytes_hash_cannot_replace_canonical_contract_hash,
        test_cr7_canonical_mutation_invalidates_authorization,
        test_cr8_self_referential_file_hash_is_rejected,
        test_cr9_cursor_metadata_inspection_is_representable_without_content,
        test_cr10_pre_action_cannot_be_reused_for_different_action,
    )
    for test in tests:
        test()
    print("PASS: Coordination Protocol v0.1 tests (MC1-MC10, PC1-PC4, CR1-CR10, CPROT1-CPROT13)")
