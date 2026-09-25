from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .problem import SemanticProblem
from resolvewhy.model import EvidenceStateKind, ProofQuantifier
from .semantics import (
    BranchOutcome,
    EvaluationLimit,
    SemanticGap,
    evaluate_branch,
    _constraint_packages,
)


class SolveStatus(str, Enum):
    SAT = "SAT"
    UNSAT = "UNSAT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVALID_PROBLEM = "INVALID_PROBLEM"


@dataclass(frozen=True)
class SolveResult:
    status: SolveStatus
    branch_results: tuple[BranchOutcome, ...] = ()
    reason: str | None = None
    message: str | None = None

    @property
    def is_decided(self) -> bool:
        return self.status in {SolveStatus.SAT, SolveStatus.UNSAT}


def _combine(quantifier: ProofQuantifier, results: tuple[BranchOutcome, ...]) -> BranchOutcome:
    if quantifier is ProofQuantifier.EXISTENTIAL:
        if any(result is BranchOutcome.SAT for result in results):
            return BranchOutcome.SAT
        if any(result is BranchOutcome.UNKNOWN for result in results):
            return BranchOutcome.UNKNOWN
        return BranchOutcome.UNSAT
    if quantifier is ProofQuantifier.UNIVERSAL:
        if any(result is BranchOutcome.UNSAT for result in results):
            return BranchOutcome.UNSAT
        if any(result is BranchOutcome.UNKNOWN for result in results):
            return BranchOutcome.UNKNOWN
        return BranchOutcome.SAT
    if quantifier is ProofQuantifier.BRANCH:
        if len(results) != 1:
            raise ValueError("branch quantifier requires exactly one runtime context")
        return results[0]
    raise ValueError(f"unsupported quantifier {quantifier!r}")



def _validate_problem(problem: SemanticProblem) -> tuple[SolveStatus, str, str] | None:
    ids = {
        "requirements": [str(item.id) for item in problem.requirements],
        "candidates": [str(item.id) for item in problem.candidates],
        "artifacts": [str(item.id) for item in problem.artifacts],
        "dependencies": [str(item.id) for item in problem.dependencies],
        "candidate_domains": [str(item.id) for item in problem.candidate_domains],
        "constraints": [str(item.id) for item in problem.semantic_constraints],
        "contexts": [str(item.id) for item in problem.runtime_contexts],
    }
    for kind, values in ids.items():
        if len(values) != len(set(values)):
            return SolveStatus.INVALID_PROBLEM, "duplicate_identifier", f"duplicate {kind} identifier"
    if problem.evidence_state.overall in {
        EvidenceStateKind.INCOMPLETE,
        EvidenceStateKind.MISSING,
        EvidenceStateKind.UNKNOWN,
    }:
        return SolveStatus.INSUFFICIENT_EVIDENCE, "incomplete_evidence", f"problem evidence state is {problem.evidence_state.overall.value}"

    candidate_by_id = {str(item.id): item for item in problem.candidates}
    evidence_by_id = {str(item.id): item for item in problem.evidence_state.observations}
    for domain in problem.candidate_domains:
        if str(domain.resolution_policy_ref) != str(problem.resolution_policy.id):
            return SolveStatus.INVALID_PROBLEM, "invalid_coverage_reference", f"candidate domain {domain.id} uses a different resolution policy"
        for ref in domain.candidate_refs:
            candidate = candidate_by_id.get(str(ref))
            if candidate is None:
                return SolveStatus.INVALID_PROBLEM, "invalid_candidate_domain", f"candidate domain {domain.id} references missing candidate {ref}"
            if candidate.package != domain.identifier:
                return SolveStatus.INVALID_PROBLEM, "invalid_candidate_domain", f"candidate {ref} does not belong to domain {domain.identifier!r}"
        if domain.coverage.status.value != "complete":
            continue
        if domain.coverage.attestation is None:
            return SolveStatus.INVALID_PROBLEM, "invalid_coverage_attestation", f"complete candidate domain {domain.id} lacks attestation"
        for ref in domain.coverage.attestation.evidence_refs:
            observation = evidence_by_id.get(str(ref.id))
            if observation is None:
                return SolveStatus.INVALID_PROBLEM, "invalid_coverage_attestation", f"candidate domain {domain.id} references missing evidence {ref.id}"
            if observation.state in {EvidenceStateKind.INCOMPLETE, EvidenceStateKind.MISSING, EvidenceStateKind.UNKNOWN}:
                return SolveStatus.INSUFFICIENT_EVIDENCE, "incomplete_candidate_coverage", f"coverage evidence {observation.id} is {observation.state.value}"
            if not any(
                supported.kind.value == "candidate_domain"
                and str(supported.id) == str(domain.id)
                for supported in observation.supports_refs
            ):
                return SolveStatus.INVALID_PROBLEM, "invalid_coverage_attestation", f"coverage evidence {observation.id} does not support candidate domain {domain.id}"

    try:
        packages = _constraint_packages(problem, problem.semantic_constraints)
    except SemanticGap as exc:
        if exc.code.startswith("unsupported_") or exc.code.startswith("incomplete_"):
            return SolveStatus.INSUFFICIENT_EVIDENCE, exc.code, str(exc)
        return SolveStatus.INVALID_PROBLEM, exc.code, str(exc)

    for constraint in problem.semantic_constraints:
        for ref in constraint.source_refs:
            if ref.kind.value == "evidence":
                observation = evidence_by_id.get(str(ref.id))
                if observation is None:
                    return SolveStatus.INVALID_PROBLEM, "dangling_evidence_reference", f"constraint {constraint.id} references missing evidence {ref.id}"
                if observation.state in {EvidenceStateKind.INCOMPLETE, EvidenceStateKind.MISSING, EvidenceStateKind.UNKNOWN}:
                    return SolveStatus.INSUFFICIENT_EVIDENCE, "incomplete_evidence", f"constraint evidence {observation.id} is {observation.state.value}"

    for context in problem.runtime_contexts:
        for package in sorted(packages):
            domains = [
                domain for domain in problem.candidate_domains
                if domain.identifier == package and str(domain.runtime_context_ref) == str(context.id)
            ]
            if not domains:
                return SolveStatus.INSUFFICIENT_EVIDENCE, "incomplete_candidate_coverage", f"no candidate domain covers package {package!r} in {context.id}"
            if any(domain.coverage.status.value != "complete" for domain in domains):
                return SolveStatus.INSUFFICIENT_EVIDENCE, "incomplete_candidate_coverage", f"candidate domain for {package!r} is not complete"
    return None

def solve(problem: SemanticProblem) -> SolveResult:
    """Solve the finite semantic proposition represented by ``problem``."""
    if not isinstance(problem, SemanticProblem):
        raise TypeError("solve expects a SemanticProblem")
    validation = _validate_problem(problem)
    if validation is not None:
        status, reason, message = validation
        return SolveResult(status, reason=reason, message=message)
    if not problem.runtime_contexts:
        return SolveResult(
            SolveStatus.INVALID_PROBLEM,
            reason="no_runtime_context",
            message="semantic problem has no active runtime context",
        )
    if problem.quantifier is ProofQuantifier.BRANCH and len(problem.runtime_contexts) != 1:
        return SolveResult(
            SolveStatus.INVALID_PROBLEM,
            reason="branch_context_count",
            message="branch propositions require exactly one runtime context",
        )

    results: list[BranchOutcome] = []
    for context in problem.runtime_contexts:
        branch_problem = problem.with_constraints(problem.semantic_constraints)
        try:
            outcome = evaluate_branch(branch_problem, branch_problem.semantic_constraints, context)
        except EvaluationLimit as exc:
            return SolveResult(SolveStatus.INSUFFICIENT_EVIDENCE, tuple(results), exc.code, str(exc))
        except SemanticGap as exc:
            if (
                exc.code.startswith("unsupported_")
                or exc.code.startswith("incomplete_")
                or exc.code.startswith("unknown_")
                or exc.code.startswith("evaluation_")
            ):
                return SolveResult(SolveStatus.INSUFFICIENT_EVIDENCE, tuple(results), exc.code, str(exc))
            return SolveResult(SolveStatus.INVALID_PROBLEM, tuple(results), exc.code, str(exc))
        results.append(outcome)

    combined = _combine(problem.quantifier, tuple(results))
    if combined is BranchOutcome.UNKNOWN:
        return SolveResult(
            SolveStatus.INSUFFICIENT_EVIDENCE,
            tuple(results),
            "insufficient_semantic_evidence",
            "the represented proposition cannot be decided from the supported fragment",
        )
    return SolveResult(
        SolveStatus.SAT if combined is BranchOutcome.SAT else SolveStatus.UNSAT,
        tuple(results),
    )
