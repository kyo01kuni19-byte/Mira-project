from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict

class RequestState(str, Enum):
    DRAFT = "DRAFT"
    FORMAL_REQUEST = "FORMAL_REQUEST"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"

@dataclass
class ChangeRequest:
    request_id: str
    matrix_id: str
    parameter_id: str
    change_target: str
    current_value: object
    proposed_value: object
    rationale: str
    qa_coordinator: str
    state: RequestState = RequestState.DRAFT

@dataclass(frozen=True)
class FrozenSnapshot:
    request_id: str
    request_fingerprint: str
    artifact_sha256: Optional[str]
    core_reference: str
    matrix_reference: str

@dataclass
class AssessmentRecord:
    purpose: str
    method_status: str
    agent_finding: Optional[str] = None
    agent_ccs: Optional[int] = None
    human_finding: Optional[str] = None
    human_ccs: Optional[int] = None
    difference_reason: Optional[str] = None

    def validate_ccs(self) -> None:
        for v in (self.agent_ccs, self.human_ccs):
            if v is not None and v not in range(5):
                raise ValueError("CCS must be 0..4")
