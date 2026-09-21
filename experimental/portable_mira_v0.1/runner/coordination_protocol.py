from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

PROTOCOL_VERSION = "portable_mira.coordination.v0.1"
VALIDATOR_ID = "portable_mira.coordination.validator.v0.1"
CONCURRENCY_MODE = "SINGLE_EXECUTOR_SINGLE_PROCESS"
DESIGN_SHA256 = "6b01c1c0b4614ffed951bf16ed0928419b46af3de90ac35e25b5a34fc399b538"
SELF_HASH_RULE = "NO_SELF_REFERENTIAL_FILE_HASH"
ACTION_CLASSES = {f"CLASS_{i}_{name}" for i, name in enumerate(("READ_ANALYZE", "LOCAL_REVERSIBLE_CHANGE", "EXTERNAL_BOUNDED_ACTION", "PERSISTENT_REPOSITORY_ACTION", "EXTERNAL_PERSISTENT_ACTION"))}
LOCAL_ACTION_CLASSES = {"CLASS_0_READ_ANALYZE", "CLASS_1_LOCAL_REVERSIBLE_CHANGE"}
AUTHORIZATION_REQUIRED_CLASSES = ACTION_CLASSES - LOCAL_ACTION_CLASSES
ACCESS_RANK = {"METADATA_ONLY": 0, "CONTENT_READ": 1, "CONTENT_WRITE": 2}
DECISION_STATES = {"AUTHORIZED", "BLOCKED", "HUMAN_VALIDATION_REQUIRED", "UNKNOWN"}
VALIDATION_STATES = {"PASS", "FAIL", "NOT_REQUIRED", "UNKNOWN", "HUMAN_VALIDATION_REQUIRED"}
CLAIM_STATES = {"CLAIMED", "OBSERVABLY_SUPPORTED", "UNKNOWN", "HUMAN_VALIDATION_REQUIRED"}
OBSERVABLE_PREFIXES = ("local:", "file:", "git:", "test:", "hash:")
ACTION_FIELDS = {"action_id", "action_class", "operation", "provider", "access_mode", "paths", "resources"}
WORK_FIELDS = {"artifact_type", "protocol_version", "work_contract_id", "created_by", "objective", "value_intent", "baseline_refs", "scope", "allowed_actions", "forbidden_actions", "network_budget", "credential_policy", "execution_mode", "concurrency_mode", "expected_evidence", "stop_conditions", "status"}
AUTH_FIELDS = {"artifact_type", "protocol_version", "authorization_id", "work_contract_id", "work_contract_canonical_content_sha256", "authorized_by", "human_confirmation_state", "confirmation_reference", "cryptographic_human_identity_verification", "authorized_actions", "explicitly_not_authorized", "action_budget", "resource_scope", "concurrency_mode", "authorization_state", "supersedes"}
PRE_FIELDS = {"artifact_type", "protocol_version", "decision_id", "work_contract_id", "work_contract_canonical_content_sha256", "authorization_ref", "validator_id", "decision", "action_class", "requested_action", "access_mode", "baseline_validation", "scope_validation", "authorization_validation", "budget_validation", "diagnostics", "decision_timestamp_or_sequence", "action_executed", "self_hash_rule"}
EVIDENCE_FIELDS = {"artifact_type", "protocol_version", "evidence_id", "work_contract_id", "work_contract_canonical_content_sha256", "authorization_ref", "pre_action_decision_ref", "pre_action_decision_canonical_content_sha256", "executor", "concurrency_mode", "attempt_index", "previous_evidence_ref", "expected_baseline", "observed_baseline", "actions_performed", "actions_not_performed", "request_counts", "files_changed", "tests_checks", "observed_results", "failures", "assumptions", "unknowns", "artifact_integrity", "git_state", "self_hash_rule", "execution_state"}
DecisionState = Literal["AUTHORIZED", "BLOCKED", "HUMAN_VALIDATION_REQUIRED", "UNKNOWN"]
EvidenceState = Literal["OBSERVABLY_SUPPORTED", "UNKNOWN", "HUMAN_VALIDATION_REQUIRED"]


class CoordinationProtocolError(Exception):
    pass


@dataclass(frozen=True)
class PreActionDecision:
    state: DecisionState
    diagnostics: tuple[str, ...]
    work_contract_canonical_content_sha256: str | None
    remaining_budget_after_action: int | None
    baseline_validation: str = "UNKNOWN"
    scope_validation: str = "UNKNOWN"
    authorization_validation: str = "UNKNOWN"
    budget_validation: str = "UNKNOWN"
    validation_only: bool = True
    action_executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceAssessment:
    state: EvidenceState
    diagnostics: tuple[str, ...]
    work_contract_canonical_content_sha256: str
    evidence_authorizes_new_work: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def canonical_content_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_bytes_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return _obj(json.loads(path.read_text(encoding="utf-8")), str(path))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CoordinationProtocolError(f"unable to load JSON: {path}") from exc


def verify_design_baseline(root: Path) -> None:
    path = root / "coordination/protocol/coordination_protocol_v0.1.design.json"
    if file_bytes_sha256(path) != DESIGN_SHA256:
        raise CoordinationProtocolError("coordination design baseline mismatch")
    if set(_obj(load_json(path).get("artifact_models"), "artifact_models")) != {"WORK_CONTRACT", "HUMAN_AUTHORIZATION", "EXECUTION_EVIDENCE"}:
        raise CoordinationProtocolError("coordination design history changed")


def validate_schema_artifacts(schema_dir: Path) -> None:
    expected = {"work_contract.schema.json": "portable_mira.coordination.work_contract.v0.1", "human_authorization.schema.json": "portable_mira.coordination.human_authorization.v0.1", "pre_action_decision.schema.json": "portable_mira.coordination.pre_action_decision.v0.1", "execution_evidence.schema.json": "portable_mira.coordination.execution_evidence.v0.1"}
    for name, schema_id in expected.items():
        schema = load_json(schema_dir / name)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema" or schema.get("$id") != schema_id or schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            raise CoordinationProtocolError(f"invalid closed schema: {name}")


def validate_work_contract(value: Any) -> dict[str, Any]:
    root = _obj(value, "work_contract"); _fields(root, WORK_FIELDS, "work_contract")
    _eq(root["artifact_type"], "WORK_CONTRACT", "artifact_type"); _eq(root["protocol_version"], PROTOCOL_VERSION, "protocol_version")
    _text(root["work_contract_id"], "work_contract_id"); _one(root["created_by"], {"HUMAN", "MIRA", "CODEX"}, "created_by")
    _text(root["objective"], "objective"); _text(root["value_intent"], "value_intent")
    base = _obj(root["baseline_refs"], "baseline_refs"); _fields(base, {"expected_baseline", "immutable_artifacts", "baseline_mismatch_policy"}, "baseline_refs")
    _text(base["expected_baseline"], "expected_baseline"); _one(base["baseline_mismatch_policy"], {"BLOCKED", "HUMAN_VALIDATION_REQUIRED"}, "baseline_mismatch_policy")
    for i, item in enumerate(_list(base["immutable_artifacts"], "immutable_artifacts")): _integrity(item, f"immutable_artifacts[{i}]")
    _contract_scope(root["scope"]); _actions(root["allowed_actions"], "allowed_actions", required=True); _actions(root["forbidden_actions"], "forbidden_actions")
    _int(root["network_budget"], "network_budget", 0); _one(root["credential_policy"], {"FORBIDDEN", "PRESENCE_ONLY", "BOUNDED_USE"}, "credential_policy")
    _text(root["execution_mode"], "execution_mode"); _eq(root["concurrency_mode"], CONCURRENCY_MODE, "concurrency_mode")
    _strings(root["expected_evidence"], "expected_evidence"); _strings(root["stop_conditions"], "stop_conditions")
    _one(root["status"], {"DRAFT", "READY_FOR_HUMAN_REVIEW", "AUTHORIZED", "EXECUTING", "EXECUTION_COMPLETE", "BLOCKED", "FAILED", "HUMAN_VALIDATION_REQUIRED", "SUPERSEDED"}, "status")
    return copy.deepcopy(root)


def validate_human_authorization(value: Any) -> dict[str, Any]:
    root = _obj(value, "authorization"); _fields(root, AUTH_FIELDS, "authorization")
    _eq(root["artifact_type"], "HUMAN_AUTHORIZATION", "artifact_type"); _eq(root["protocol_version"], PROTOCOL_VERSION, "protocol_version")
    _text(root["authorization_id"], "authorization_id"); _text(root["work_contract_id"], "work_contract_id"); _sha(root["work_contract_canonical_content_sha256"], "contract hash")
    _eq(root["authorized_by"], "HUMAN", "authorized_by"); _eq(root["human_confirmation_state"], "HUMAN_CONFIRMATION_RECORDED", "human_confirmation_state")
    conf = _obj(root["confirmation_reference"], "confirmation_reference"); _fields(conf, {"method", "reference_id"}, "confirmation_reference"); _eq(conf["method"], "OUT_OF_BAND_EXPLICIT_CONFIRMATION", "method"); _text(conf["reference_id"], "reference_id")
    _eq(root["cryptographic_human_identity_verification"], "NOT_IMPLEMENTED", "identity verification")
    authorized = _actions(root["authorized_actions"], "authorized_actions", required=True); _actions(root["explicitly_not_authorized"], "explicitly_not_authorized")
    seen = set()
    for i, item in enumerate(_list(root["action_budget"], "action_budget")):
        item = _obj(item, f"budget[{i}]"); _fields(item, {"action_id", "limit"}, f"budget[{i}]"); aid = _text(item["action_id"], "action_id"); _int(item["limit"], "limit", 0)
        if aid in seen: raise CoordinationProtocolError("duplicate authorization budget")
        seen.add(aid)
    ids = {a["action_id"] for a in authorized}
    if not seen <= ids or not {a["action_id"] for a in authorized if a["action_class"] in AUTHORIZATION_REQUIRED_CLASSES} <= seen: raise CoordinationProtocolError("invalid authorization budget")
    scope = _obj(root["resource_scope"], "resource_scope"); _fields(scope, {"path_permissions", "resources", "providers"}, "resource_scope"); _permissions(scope["path_permissions"], "path_permissions"); _strings(scope["resources"], "resources"); _strings(scope["providers"], "providers")
    _eq(root["concurrency_mode"], CONCURRENCY_MODE, "concurrency_mode"); _one(root["authorization_state"], {"ACTIVE", "CONSUMED", "REVOKED", "SUPERSEDED", "INVALIDATED"}, "authorization_state")
    if root["supersedes"] is not None: _text(root["supersedes"], "supersedes")
    return copy.deepcopy(root)


def validate_pre_action_decision_artifact(value: Any) -> dict[str, Any]:
    root = _obj(value, "pre_action_decision"); _fields(root, PRE_FIELDS, "pre_action_decision")
    _eq(root["artifact_type"], "PRE_ACTION_DECISION", "artifact_type"); _eq(root["protocol_version"], PROTOCOL_VERSION, "protocol_version"); _text(root["decision_id"], "decision_id"); _text(root["work_contract_id"], "work_contract_id"); _sha(root["work_contract_canonical_content_sha256"], "contract hash")
    if root["authorization_ref"] is not None: _text(root["authorization_ref"], "authorization_ref")
    _eq(root["validator_id"], VALIDATOR_ID, "validator_id"); _one(root["decision"], DECISION_STATES, "decision")
    action = _action(root["requested_action"], "requested_action"); _eq(root["action_class"], action["action_class"], "action_class"); _eq(root["access_mode"], action["access_mode"], "access_mode")
    for name in ("baseline_validation", "scope_validation", "authorization_validation", "budget_validation"): _one(root[name], VALIDATION_STATES, name)
    _strings(root["diagnostics"], "diagnostics")
    if isinstance(root["decision_timestamp_or_sequence"], bool) or not isinstance(root["decision_timestamp_or_sequence"], (str, int)): raise CoordinationProtocolError("invalid decision sequence")
    _eq(root["action_executed"], False, "action_executed"); _eq(root["self_hash_rule"], SELF_HASH_RULE, "self_hash_rule")
    return copy.deepcopy(root)


def build_pre_action_decision_artifact(decision_id: str, work_contract: Any, requested_action: Any, decision: PreActionDecision, *, authorization_ref: str | None = None, decision_timestamp_or_sequence: str | int = 1) -> dict[str, Any]:
    contract = validate_work_contract(work_contract); action = _action(requested_action, "requested_action")
    return validate_pre_action_decision_artifact({"artifact_type": "PRE_ACTION_DECISION", "protocol_version": PROTOCOL_VERSION, "decision_id": decision_id, "work_contract_id": contract["work_contract_id"], "work_contract_canonical_content_sha256": canonical_content_sha256(contract), "authorization_ref": authorization_ref, "validator_id": VALIDATOR_ID, "decision": decision.state, "action_class": action["action_class"], "requested_action": action, "access_mode": action["access_mode"], "baseline_validation": decision.baseline_validation, "scope_validation": decision.scope_validation, "authorization_validation": decision.authorization_validation, "budget_validation": decision.budget_validation, "diagnostics": list(decision.diagnostics), "decision_timestamp_or_sequence": decision_timestamp_or_sequence, "action_executed": False, "self_hash_rule": SELF_HASH_RULE})


def validate_execution_evidence_shape(value: Any) -> dict[str, Any]:
    root = _obj(value, "evidence"); _fields(root, EVIDENCE_FIELDS, "evidence")
    _eq(root["artifact_type"], "EXECUTION_EVIDENCE", "artifact_type"); _eq(root["protocol_version"], PROTOCOL_VERSION, "protocol_version"); _text(root["evidence_id"], "evidence_id"); _text(root["work_contract_id"], "work_contract_id"); _sha(root["work_contract_canonical_content_sha256"], "contract hash")
    if root["authorization_ref"] is not None: _text(root["authorization_ref"], "authorization_ref")
    _text(root["pre_action_decision_ref"], "pre_action_decision_ref"); _sha(root["pre_action_decision_canonical_content_sha256"], "pre_action hash"); _text(root["executor"], "executor"); _eq(root["concurrency_mode"], CONCURRENCY_MODE, "concurrency_mode")
    _int(root["attempt_index"], "attempt_index", 1)
    if root["previous_evidence_ref"] is not None: _text(root["previous_evidence_ref"], "previous_evidence_ref")
    if root["attempt_index"] > 1 and root["previous_evidence_ref"] is None: raise CoordinationProtocolError("later attempt requires previous evidence")
    _text(root["expected_baseline"], "expected_baseline"); _text(root["observed_baseline"], "observed_baseline")
    for i, item in enumerate(_list(root["actions_performed"], "actions_performed")):
        item = _obj(item, f"performed[{i}]"); _fields(item, ACTION_FIELDS | {"claim_state", "evidence_refs"}, f"performed[{i}]"); _action({k: item[k] for k in ACTION_FIELDS}, f"performed[{i}]"); _one(item["claim_state"], CLAIM_STATES, "claim_state"); _strings(item["evidence_refs"], "evidence_refs")
    _strings(root["actions_not_performed"], "actions_not_performed")
    for item in _list(root["request_counts"], "request_counts"): _fields(_obj(item, "request_count"), {"action_id", "completed", "unknown_dispatch"}, "request_count"); _text(item["action_id"], "action_id"); _int(item["completed"], "completed", 0); _int(item["unknown_dispatch"], "unknown_dispatch", 0)
    for item in _list(root["files_changed"], "files_changed"):
        _fields(_obj(item, "file_change"), {"path", "file_bytes_sha256_before", "file_bytes_sha256_after"}, "file_change"); _text(item["path"], "path")
        for name in ("file_bytes_sha256_before", "file_bytes_sha256_after"):
            if item[name] is not None: _sha(item[name], name)
    for item in _list(root["tests_checks"], "tests_checks"): _fields(_obj(item, "check"), {"name", "state", "evidence_refs"}, "check"); _text(item["name"], "name"); _one(item["state"], {"PASS", "FAIL", "UNKNOWN"}, "state"); _strings(item["evidence_refs"], "refs")
    for name in ("observed_results", "failures"):
        for item in _list(root[name], name): _claim(item)
    _strings(root["assumptions"], "assumptions"); _strings(root["unknowns"], "unknowns")
    for i, item in enumerate(_list(root["artifact_integrity"], "artifact_integrity")): _integrity(item, f"artifact_integrity[{i}]")
    git = _obj(root["git_state"], "git_state"); _fields(git, {"head", "branch", "staged_paths", "unstaged_paths", "untracked_paths"}, "git_state"); _text(git["head"], "head"); _text(git["branch"], "branch")
    for name in ("staged_paths", "unstaged_paths", "untracked_paths"): _strings(git[name], name)
    _eq(root["self_hash_rule"], SELF_HASH_RULE, "self_hash_rule"); _one(root["execution_state"], {"PRE_ACTION_GATE_FAILED", "EXECUTING", "PARTIAL", "EXECUTION_COMPLETE", "BLOCKED", "FAILED", "HUMAN_VALIDATION_REQUIRED"}, "execution_state")
    return copy.deepcopy(root)


def validate_pre_action(work_contract: Any, requested_action: Any, observed_baseline: str, *, authorization: Any | None = None, human_authorization_confirmation: Any | None = None, human_request_confirmation: Any | None = None, consumed_count: int = 0, unknown_dispatch_count: int = 0, executor_count: int = 1, process_count: int = 1) -> PreActionDecision:
    try:
        contract = validate_work_contract(work_contract); action = _action(requested_action, "requested_action"); _text(observed_baseline, "observed_baseline"); _int(consumed_count, "consumed_count", 0); _int(unknown_dispatch_count, "unknown_dispatch_count", 0)
    except CoordinationProtocolError as exc: return _decision("BLOCKED", (f"SCHEMA_OR_REQUEST_INVALID:{exc}",), None, None)
    chash = canonical_content_sha256(contract)
    if executor_count != 1 or process_count != 1: return _decision("BLOCKED", ("SINGLE_EXECUTOR_SINGLE_PROCESS_REQUIRED",), chash, None)
    if contract["status"] not in {"AUTHORIZED", "EXECUTING"}: return _decision("BLOCKED", ("WORK_CONTRACT_NOT_AUTHORIZED",), chash, None)
    if action not in contract["allowed_actions"]: return _decision("BLOCKED", ("ACTION_NOT_ALLOWED_BY_WORK_CONTRACT",), chash, None)
    if action in contract["forbidden_actions"]: return _decision("BLOCKED", ("ACTION_EXPLICITLY_FORBIDDEN",), chash, None, scope="FAIL")
    error = _scope_error(action, contract["scope"], True)
    if error: return _decision("BLOCKED", (error,), chash, None, scope="FAIL")
    if action["action_class"] == "CLASS_0_READ_ANALYZE" and action["access_mode"] == "CONTENT_WRITE": return _decision("BLOCKED", ("CLASS_0_CONTENT_WRITE_FORBIDDEN",), chash, None, scope="FAIL")
    if observed_baseline != contract["baseline_refs"]["expected_baseline"]:
        state = contract["baseline_refs"]["baseline_mismatch_policy"]; return _decision(state, ("BASELINE_MISMATCH",), chash, None, baseline="HUMAN_VALIDATION_REQUIRED" if state == "HUMAN_VALIDATION_REQUIRED" else "FAIL", scope="PASS")
    if action["action_class"] in LOCAL_ACTION_CLASSES:
        if not _valid_request(human_request_confirmation): return _decision("BLOCKED", ("VALID_HUMAN_REQUEST_CONTEXT_REQUIRED",), chash, None, baseline="PASS", scope="PASS", authorization="FAIL", budget="NOT_REQUIRED")
        return _decision("AUTHORIZED", ("LOCAL_PRE_ACTION_GATE_PASS", "VALIDATION_ONLY_NO_ACTION_EXECUTED"), chash, None, baseline="PASS", scope="PASS", authorization="NOT_REQUIRED", budget="NOT_REQUIRED")
    if authorization is None: return _decision("BLOCKED", ("HUMAN_AUTHORIZATION_REQUIRED",), chash, None, baseline="PASS", scope="PASS", authorization="FAIL")
    try: auth = validate_human_authorization(authorization)
    except CoordinationProtocolError as exc: return _decision("BLOCKED", (f"AUTHORIZATION_INVALID:{exc}",), chash, None, baseline="PASS", scope="PASS", authorization="FAIL")
    if auth["work_contract_id"] != contract["work_contract_id"]: return _decision("BLOCKED", ("AUTHORIZATION_CONTRACT_ID_MISMATCH",), chash, None, baseline="PASS", scope="PASS", authorization="FAIL")
    if auth["work_contract_canonical_content_sha256"] != chash: return _decision("BLOCKED", ("AUTHORIZATION_CONTRACT_HASH_MISMATCH",), chash, None, baseline="PASS", scope="PASS", authorization="FAIL")
    if not _valid_confirmation(human_authorization_confirmation, auth, chash): return _decision("BLOCKED", ("OUT_OF_BAND_HUMAN_CONFIRMATION_REQUIRED",), chash, None, baseline="PASS", scope="PASS", authorization="FAIL")
    if auth["authorization_state"] != "ACTIVE" or action not in auth["authorized_actions"]: return _decision("BLOCKED", ("ACTION_NOT_AUTHORIZED",), chash, None, baseline="PASS", scope="PASS", authorization="FAIL")
    error = _scope_error(action, auth["resource_scope"], False)
    if error: return _decision("BLOCKED", (f"AUTHORIZATION_{error}",), chash, None, baseline="PASS", scope="PASS", authorization="FAIL")
    limit = next((x["limit"] for x in auth["action_budget"] if x["action_id"] == action["action_id"]), None)
    if limit is None: return _decision("BLOCKED", ("ACTION_BUDGET_MISSING",), chash, None, baseline="PASS", scope="PASS", authorization="PASS", budget="FAIL")
    remaining = limit - consumed_count - unknown_dispatch_count
    if action["action_class"] == "CLASS_2_EXTERNAL_BOUNDED_ACTION": remaining = min(remaining, contract["network_budget"] - consumed_count - unknown_dispatch_count)
    if remaining <= 0: return _decision("BLOCKED", ("ACTION_BUDGET_EXHAUSTED",), chash, 0, baseline="PASS", scope="PASS", authorization="PASS", budget="FAIL")
    return _decision("AUTHORIZED", ("PRE_ACTION_GATE_PASS", "VALIDATION_ONLY_NO_ACTION_EXECUTED"), chash, remaining - 1, baseline="PASS", scope="PASS", authorization="PASS", budget="PASS")


def validate_pre_action_decision_binding(pre_action: Any, work_contract: Any, requested_action: Any) -> PreActionDecision:
    try: artifact = validate_pre_action_decision_artifact(pre_action); contract = validate_work_contract(work_contract); action = _action(requested_action, "requested_action")
    except CoordinationProtocolError as exc: return _decision("BLOCKED", (f"PRE_ACTION_BINDING_INVALID:{exc}",), None, None)
    chash = canonical_content_sha256(contract); diagnostics = []
    if artifact["work_contract_id"] != contract["work_contract_id"]: diagnostics.append("PRE_ACTION_CONTRACT_ID_MISMATCH")
    if artifact["work_contract_canonical_content_sha256"] != chash: diagnostics.append("PRE_ACTION_CONTRACT_HASH_MISMATCH")
    if artifact["requested_action"] != action: diagnostics.append("PRE_ACTION_ACTION_MISMATCH")
    if artifact["decision"] != "AUTHORIZED": diagnostics.append("PRE_ACTION_NOT_AUTHORIZED")
    return _decision("BLOCKED" if diagnostics else "AUTHORIZED", tuple(diagnostics or ["PRE_ACTION_BINDING_PASS"]), chash, None, baseline=artifact["baseline_validation"], scope=artifact["scope_validation"], authorization=artifact["authorization_validation"], budget=artifact["budget_validation"])


def assess_execution_evidence(evidence: Any, work_contract: Any, pre_action_decision: Any) -> EvidenceAssessment:
    contract = validate_work_contract(work_contract); record = validate_execution_evidence_shape(evidence); pre = validate_pre_action_decision_artifact(pre_action_decision); chash = canonical_content_sha256(contract); diagnostics = set()
    if record["work_contract_id"] != contract["work_contract_id"]: diagnostics.add("EVIDENCE_CONTRACT_ID_MISMATCH")
    if record["work_contract_canonical_content_sha256"] != chash: diagnostics.add("EVIDENCE_CONTRACT_HASH_MISMATCH")
    if record["pre_action_decision_ref"] != pre["decision_id"]: diagnostics.add("EVIDENCE_PRE_ACTION_REF_MISMATCH")
    if record["pre_action_decision_canonical_content_sha256"] != canonical_content_sha256(pre): diagnostics.add("EVIDENCE_PRE_ACTION_HASH_MISMATCH")
    binding = validate_pre_action_decision_binding(pre, contract, pre["requested_action"])
    if binding.state != "AUTHORIZED": diagnostics.update(binding.diagnostics)
    expected = contract["baseline_refs"]["expected_baseline"]
    if record["expected_baseline"] != expected or record["observed_baseline"] != expected: diagnostics.add("EVIDENCE_BASELINE_MISMATCH")
    for item in record["actions_performed"]:
        if {k: item[k] for k in ACTION_FIELDS} != pre["requested_action"]: diagnostics.add("EVIDENCE_ACTION_PRE_ACTION_MISMATCH")
    human = False; unknown = bool(diagnostics)
    for item in list(record["actions_performed"]) + list(record["observed_results"]) + list(record["failures"]):
        if item["claim_state"] == "HUMAN_VALIDATION_REQUIRED": human = True
        elif item["claim_state"] in {"CLAIMED", "UNKNOWN"}: unknown = True
        elif not item["evidence_refs"] or not all(any(ref.startswith(p) and len(ref) > len(p) for p in OBSERVABLE_PREFIXES) for ref in item["evidence_refs"]): diagnostics.add("OBSERVABLE_SUPPORT_MISSING"); unknown = True
        if item.get("operation") in {"git_push", "stage_and_commit", "commit"} and item["claim_state"] == "OBSERVABLY_SUPPORTED" and not any(ref.startswith("git:") for ref in item["evidence_refs"]): diagnostics.add("GIT_OBSERVABLE_SUPPORT_MISSING"); unknown = True
    for check in record["tests_checks"]:
        if check["state"] == "PASS" and not check["evidence_refs"]: diagnostics.add("TEST_SUPPORT_MISSING"); unknown = True
    state: EvidenceState = "HUMAN_VALIDATION_REQUIRED" if human else "UNKNOWN" if unknown else "OBSERVABLY_SUPPORTED"
    if state == "OBSERVABLY_SUPPORTED": diagnostics.add("OBSERVABLE_EVIDENCE_PRESENT")
    return EvidenceAssessment(state, tuple(sorted(diagnostics)), chash)


def _decision(state, diagnostics, chash, remaining, *, baseline="UNKNOWN", scope="UNKNOWN", authorization="UNKNOWN", budget="UNKNOWN"):
    return PreActionDecision(state, diagnostics, chash, remaining, baseline, scope, authorization, budget)


def _valid_request(value): return isinstance(value, dict) and value.get("state") == "HUMAN_REQUEST_CONFIRMED" and bool(value.get("reference_id")) and set(value) == {"state", "reference_id"}
def _valid_confirmation(value, auth, chash): return isinstance(value, dict) and set(value) == {"state", "method", "reference_id", "work_contract_canonical_content_sha256"} and value["state"] == "HUMAN_CONFIRMATION_RECORDED" and value["method"] == "OUT_OF_BAND_EXPLICIT_CONFIRMATION" and value["reference_id"] == auth["confirmation_reference"]["reference_id"] and value["work_contract_canonical_content_sha256"] == chash


def _actions(value, path, required=False):
    items = _list(value, path)
    if required and not items: raise CoordinationProtocolError(f"{path} must not be empty")
    result = [_action(item, f"{path}[{i}]") for i, item in enumerate(items)]
    ids = [x["action_id"] for x in result]
    if len(ids) != len(set(ids)): raise CoordinationProtocolError("duplicate action_id")
    return result


def _action(value, path):
    item = _obj(value, path); _fields(item, ACTION_FIELDS, path); _text(item["action_id"], "action_id"); _one(item["action_class"], ACTION_CLASSES, "action_class"); _text(item["operation"], "operation")
    if item["provider"] is not None: _text(item["provider"], "provider")
    _one(item["access_mode"], set(ACCESS_RANK), "access_mode"); _strings(item["paths"], "paths"); _strings(item["resources"], "resources")
    return copy.deepcopy(item)


def _contract_scope(value):
    scope = _obj(value, "scope"); fields = {"path_permissions", "forbidden_paths", "permitted_resources", "forbidden_resources", "permitted_providers", "forbidden_providers"}; _fields(scope, fields, "scope"); _permissions(scope["path_permissions"], "path_permissions")
    for name in fields - {"path_permissions"}: _strings(scope[name], name)


def _permissions(value, path):
    seen = set()
    for item in _list(value, path):
        item = _obj(item, path); _fields(item, {"path", "access_mode"}, path); name = _text(item["path"], "path"); _one(item["access_mode"], set(ACCESS_RANK), "access_mode")
        if name in seen: raise CoordinationProtocolError("duplicate path permission")
        seen.add(name)


def _scope_error(action, scope, contract_scope):
    permissions = {x["path"]: x["access_mode"] for x in scope["path_permissions"]}
    forbidden_paths = set(scope["forbidden_paths"]) if contract_scope else set(); resources = set(scope["permitted_resources"] if contract_scope else scope["resources"]); forbidden_resources = set(scope["forbidden_resources"]) if contract_scope else set(); providers = set(scope["permitted_providers"] if contract_scope else scope["providers"]); forbidden_providers = set(scope["forbidden_providers"]) if contract_scope else set()
    if set(action["paths"]) & forbidden_paths: return "FORBIDDEN_PATH"
    for path in action["paths"]:
        if path not in permissions: return "PATH_OUT_OF_SCOPE"
        if ACCESS_RANK[action["access_mode"]] > ACCESS_RANK[permissions[path]]: return "PATH_ACCESS_MODE_EXCEEDED"
    if set(action["resources"]) & forbidden_resources: return "FORBIDDEN_RESOURCE"
    if not set(action["resources"]) <= resources: return "RESOURCE_OUT_OF_SCOPE"
    if action["provider"] in forbidden_providers: return "FORBIDDEN_PROVIDER"
    if action["provider"] is not None and action["provider"] not in providers: return "PROVIDER_OUT_OF_SCOPE"
    return None


def _integrity(value, path):
    item = _obj(value, path); _fields(item, {"path", "canonical_content_sha256", "file_bytes_sha256"}, path); _text(item["path"], "path")
    if item["canonical_content_sha256"] is None and item["file_bytes_sha256"] is None: raise CoordinationProtocolError("integrity hash required")
    for name in ("canonical_content_sha256", "file_bytes_sha256"):
        if item[name] is not None: _sha(item[name], name)


def _claim(value):
    item = _obj(value, "claim"); _fields(item, {"claim", "claim_state", "evidence_refs"}, "claim"); _text(item["claim"], "claim"); _one(item["claim_state"], CLAIM_STATES, "claim_state"); _strings(item["evidence_refs"], "evidence_refs")


def _obj(value, path):
    if not isinstance(value, dict): raise CoordinationProtocolError(f"{path} must be an object")
    return value
def _list(value, path):
    if not isinstance(value, list): raise CoordinationProtocolError(f"{path} must be an array")
    return value
def _fields(value, expected, path):
    missing, extra = sorted(expected - set(value)), sorted(set(value) - expected)
    if missing or extra: raise CoordinationProtocolError(f"{path} fields mismatch; missing={missing}, additional={extra}")
def _text(value, path):
    if not isinstance(value, str) or not value: raise CoordinationProtocolError(f"{path} must be a non-empty string")
    return value
def _strings(value, path):
    items = _list(value, path)
    if any(not isinstance(x, str) or not x for x in items) or len(items) != len(set(items)): raise CoordinationProtocolError(f"{path} must contain unique non-empty strings")
    return items
def _int(value, path, minimum):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum: raise CoordinationProtocolError(f"{path} must be integer >= {minimum}")
def _sha(value, path):
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value): raise CoordinationProtocolError(f"{path} must be lowercase SHA-256")
def _eq(value, expected, path):
    if value != expected: raise CoordinationProtocolError(f"{path} must equal {expected!r}")
def _one(value, options, path):
    if value not in options: raise CoordinationProtocolError(f"{path} is not an allowed value")
