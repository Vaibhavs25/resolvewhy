from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from resolvewhy.model import ProofQuantifier, TraceRef, VerificationStatus
from resolvewhy.validation import ValidationIssue


class VerificationReason(str, Enum):
    UNSUPPORTED_SEMANTICS = "unsupported_semantics"
    UNSUPPORTED_VERSION = "unsupported_version_semantics"
    UNSUPPORTED_MARKER = "unsupported_marker_semantics"
    UNSUPPORTED_POLICY = "unsupported_policy_semantics"
    INCOMPLETE_EVIDENCE = "incomplete_evidence"
    MISSING_EVIDENCE = "missing_evidence"
    INCOMPLETE_CANDIDATE_COVERAGE = "incomplete_candidate_coverage"
    INVALID_COVERAGE_ATTESTATION = "invalid_coverage_attestation"
    INVALID_PROOF_BINDING = "invalid_proof_binding"
    INVALID_PROVENANCE = "invalid_provenance"
    INCOMPLETE_CANDIDATE_METADATA = "incomplete_candidate_metadata"
    UNKNOWN_ARTIFACT_COMPATIBILITY = "unknown_artifact_compatibility"
    SEARCH_LIMIT = "evaluation_search_limit"
    CORE_EVALUATION_LIMIT = "core_evaluation_limit"
    CLAIM_MISMATCH = "claim_mismatch"
    INTERNAL_ERROR = "internal_error"


class VerificationCategory(str, Enum):
    """Stable caller-facing classification of a verification outcome."""

    VERIFIED_SAT = "verified_sat"
    VERIFIED_UNSAT = "verified_unsat"
    INVALID_EVIDENCE = "invalid_evidence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNSUPPORTED_SEMANTICS = "unsupported_semantics"
    RESOURCE_LIMIT = "resource_limit"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class VerificationIssue:
    code: str
    message: str
    ref: TraceRef | None = None

    @classmethod
    def from_validation(cls, issue: ValidationIssue) -> VerificationIssue:
        return cls(issue.code, issue.message, issue.ref)


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    independently_verified: bool
    proof_claim_id: str | None
    quantifier: ProofQuantifier | None
    evaluation_domain: tuple[str, ...]
    premise_ids: tuple[str, ...]
    core_ids: tuple[str, ...]
    core_verified: bool | None
    minimality_verified: bool | None
    reasons: tuple[str, ...] = ()
    issues: tuple[VerificationIssue, ...] = ()
    branch_results: tuple[str, ...] = ()
    evaluation_domain_id: str | None = None

    @property
    def is_verified(self) -> bool:
        return self.independently_verified

    @property
    def status_value(self) -> str:
        return self.status.value

    @property
    def category(self) -> VerificationCategory:
        """Return the stable, machine-readable outcome category.

        This property is the supported way for callers to distinguish a
        resource limit or unsupported semantic fragment from other
        insufficient-evidence outcomes.  Do not parse ``message`` values.
        """
        if self.status is VerificationStatus.VERIFIED_SAT:
            return VerificationCategory.VERIFIED_SAT
        if self.status is VerificationStatus.VERIFIED_UNSAT:
            return VerificationCategory.VERIFIED_UNSAT
        if self.status is VerificationStatus.INVALID_TRACE:
            return VerificationCategory.INVALID_EVIDENCE
        if self.status is VerificationStatus.INTERNAL_ERROR:
            return VerificationCategory.INTERNAL_ERROR
        if any(
            reason
            in {
                VerificationReason.SEARCH_LIMIT.value,
                VerificationReason.CORE_EVALUATION_LIMIT.value,
            }
            for reason in self.reasons
        ):
            return VerificationCategory.RESOURCE_LIMIT
        if any(reason.startswith("unsupported_") for reason in self.reasons):
            return VerificationCategory.UNSUPPORTED_SEMANTICS
        return VerificationCategory.INSUFFICIENT_EVIDENCE

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic, JSON-compatible public result shape."""
        return {
            "status": self.status.value,
            "category": self.category.value,
            "independently_verified": self.independently_verified,
            "proof_claim_id": self.proof_claim_id,
            "quantifier": self.quantifier.value
            if self.quantifier is not None
            else None,
            "evaluation_domain": list(self.evaluation_domain),
            "evaluation_domain_id": self.evaluation_domain_id,
            "premise_ids": list(self.premise_ids),
            "core_ids": list(self.core_ids),
            "core_verified": self.core_verified,
            "minimality_verified": self.minimality_verified,
            "reasons": list(self.reasons),
            "issues": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "ref": str(issue.ref) if issue.ref is not None else None,
                }
                for issue in self.issues
            ],
            "branch_results": list(self.branch_results),
        }

    def to_json(self) -> str:
        """Serialize :meth:`to_dict` deterministically for diagnostics."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
