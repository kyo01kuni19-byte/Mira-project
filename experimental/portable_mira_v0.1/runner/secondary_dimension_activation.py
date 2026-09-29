"""Experimental secondary-dimension activation discipline.

The three-case true-holdout synthesis classifies this control as a next
experiment, not as a baseline or production change. The frozen Semantic
Judgment Contract, provider schema, and OpenAI instruction kernel stay in
place. This module only evaluates a separate necessity record and can build
a candidate instruction that is not installed into the adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CANDIDATE_ID = "portable_mira.secondary_dimension_activation.v0.1"
EPISTEMIC_STATUS = "EXPERIMENTAL_CONTROL_CANDIDATE_NOT_BASELINE"
NECESSITY = Literal["MATERIAL", "OBSERVATIONAL"]

ACTIVATION_INSTRUCTION_DELTA = (
    "List a possible_secondary_dimension only when it is materially necessary "
    "for the case. Do not list a dimension only because it is semantically "
    "plausible. Omitting a materially necessary dimension is a failure. "
    "possible_secondary_dimensions still do not select edges or direct traversal."
)


class ActivationDisciplineError(Exception):
    """Structural failure of an activation-discipline record."""


@dataclass(frozen=True)
class DimensionBasis:
    dimension: str
    necessity: NECESSITY
    basis_ref: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.dimension, str) or not self.dimension:
            raise ActivationDisciplineError("dimension must be a non-empty string")
        if self.necessity not in {"MATERIAL", "OBSERVATIONAL"}:
            raise ActivationDisciplineError("necessity must be MATERIAL or OBSERVATIONAL")
        if not isinstance(self.basis_ref, str):
            raise ActivationDisciplineError("basis_ref must be a string")
        if self.necessity == "MATERIAL" and not self.basis_ref:
            raise ActivationDisciplineError("MATERIAL necessity requires a basis_ref")
        if self.necessity == "OBSERVATIONAL" and self.basis_ref:
            raise ActivationDisciplineError("OBSERVATIONAL necessity cannot carry a basis_ref")


@dataclass(frozen=True)
class ActivationDecision:
    candidate_id: str
    listed_dimensions: tuple[str, ...]
    materially_supported_dimensions: tuple[str, ...]
    diagnostics: tuple[str, ...]
    result: str
    route_selection_modified: bool
    baseline_instruction_modified: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "listed_dimensions": list(self.listed_dimensions),
            "materially_supported_dimensions": list(self.materially_supported_dimensions),
            "diagnostics": list(self.diagnostics),
            "result": self.result,
            "route_selection_modified": self.route_selection_modified,
            "baseline_instruction_modified": self.baseline_instruction_modified,
            "epistemic_status": EPISTEMIC_STATUS,
        }


def candidate_instruction(frozen_kernel: str) -> str:
    """Return an uninstalled instruction candidate derived from the frozen kernel."""

    if not isinstance(frozen_kernel, str) or not frozen_kernel.strip():
        raise ActivationDisciplineError("frozen instruction kernel is empty")
    if ACTIVATION_INSTRUCTION_DELTA in frozen_kernel:
        raise ActivationDisciplineError("frozen kernel already contains the candidate delta")
    return f"{frozen_kernel.rstrip()}\n{ACTIVATION_INSTRUCTION_DELTA}"


def evaluate_activation(
    listed_dimensions: list[str] | tuple[str, ...],
    bases: list[DimensionBasis] | tuple[DimensionBasis, ...],
    required_dimensions: list[str] | tuple[str, ...],
    registered_dimensions: set[str] | frozenset[str],
) -> ActivationDecision:
    """Evaluate listing discipline without rewriting a Semantic Judgment."""

    listed = _dimension_tuple(listed_dimensions, "listed_dimensions")
    required = _dimension_tuple(required_dimensions, "required_dimensions")
    vocabulary = _vocabulary(registered_dimensions)
    unknown = sorted((set(listed) | set(required)) - vocabulary)
    if unknown:
        raise ActivationDisciplineError(
            f"unregistered secondary dimension: {', '.join(unknown)}"
        )
    by_dimension = _bases_by_dimension(bases)
    extra_bases = sorted(set(by_dimension) - set(listed) - set(required))
    if extra_bases:
        raise ActivationDisciplineError(
            f"necessity basis is not listed or required: {', '.join(extra_bases)}"
        )

    supported: list[str] = []
    unsupported: list[str] = []
    for dimension in listed:
        basis = by_dimension.get(dimension)
        if basis is not None and basis.necessity == "MATERIAL":
            supported.append(dimension)
        else:
            unsupported.append(dimension)
    omitted = [dimension for dimension in required if dimension not in supported]

    diagnostics: list[str] = []
    if unsupported:
        diagnostics.append("SECONDARY_DIMENSION_ACTIVATION_WITHOUT_NECESSITY")
    if omitted:
        diagnostics.append("SECONDARY_DIMENSION_OMISSION")
    if not diagnostics:
        diagnostics.append("ACTIVATION_DISCIPLINE_PRESERVED")
    return ActivationDecision(
        candidate_id=CANDIDATE_ID,
        listed_dimensions=listed,
        materially_supported_dimensions=tuple(supported),
        diagnostics=tuple(diagnostics),
        result="PASS" if diagnostics == ["ACTIVATION_DISCIPLINE_PRESERVED"] else "FAIL",
        route_selection_modified=False,
        baseline_instruction_modified=False,
    )


def _dimension_tuple(values: list[str] | tuple[str, ...], label: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise ActivationDisciplineError(f"{label} must be a list")
    if any(not isinstance(item, str) or not item for item in values):
        raise ActivationDisciplineError(f"{label} must contain non-empty strings")
    if len(set(values)) != len(values):
        raise ActivationDisciplineError(f"{label} contains a duplicate dimension")
    return tuple(values)


def _vocabulary(values: set[str] | frozenset[str]) -> frozenset[str]:
    if not isinstance(values, (set, frozenset)) or not values:
        raise ActivationDisciplineError("registered_dimensions must be a non-empty set")
    if any(not isinstance(item, str) or not item for item in values):
        raise ActivationDisciplineError("registered_dimensions must contain non-empty strings")
    return frozenset(values)


def _bases_by_dimension(
    bases: list[DimensionBasis] | tuple[DimensionBasis, ...],
) -> dict[str, DimensionBasis]:
    if not isinstance(bases, (list, tuple)):
        raise ActivationDisciplineError("bases must be a list")
    by_dimension: dict[str, DimensionBasis] = {}
    for basis in bases:
        if not isinstance(basis, DimensionBasis):
            raise ActivationDisciplineError("bases must contain DimensionBasis values")
        if basis.dimension in by_dimension:
            raise ActivationDisciplineError(
                f"duplicate necessity basis: {basis.dimension}"
            )
        by_dimension[basis.dimension] = basis
    return by_dimension
