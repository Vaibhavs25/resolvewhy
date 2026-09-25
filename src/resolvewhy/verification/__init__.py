"""Independent verification for production resolvewhy traces."""

from .result import VerificationIssue, VerificationReason, VerificationResult
from .semantics import BranchOutcome, evaluate_branch, eval_marker, parse_version, version_satisfies
from .verifier import verify, verify_serialized

__all__ = [
    "BranchOutcome",
    "VerificationIssue",
    "VerificationReason",
    "VerificationResult",
    "eval_marker",
    "evaluate_branch",
    "parse_version",
    "verify",
    "verify_serialized",
    "version_satisfies",
]
