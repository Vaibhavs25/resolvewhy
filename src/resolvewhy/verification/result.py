from __future__ import annotations

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
    CLAIM_MISMATCH = "claim_mismatch"


@dataclass(frozen=True)
class VerificationIssue:
    code: str
    message: str
    ref: TraceRef | None = None

    @classmethod
    def from_validation(cls, issue: ValidationIssue) -> "VerificationIssue":
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

    @property
    def is_verified(self) -> bool:
        return self.independently_verified

    @property
    def status_value(self) -> str:
        return self.status.value
