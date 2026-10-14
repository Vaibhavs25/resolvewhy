from __future__ import annotations

from dataclasses import dataclass

from .problem import SemanticProblem
from .solver import SolveStatus, solve

# A subset-minimality check needs one solve for the claimed core and one solve
# for every deletion.  The bounded budget therefore permits independently
# checking a 127-premise core while preventing an untrusted claim from turning
# a verified result into an unbounded sequence of 100,000-state searches.
MAX_CORE_SOLVE_ATTEMPTS = 128


@dataclass(frozen=True)
class CoreResult:
    status: SolveStatus
    premise_ids: tuple[str, ...]
    core_ids: tuple[str, ...] = ()
    minimal: bool = False
    reason: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class CoreVerificationResult:
    verified: bool
    core_ids: tuple[str, ...]
    unsat_verified: bool
    deletion_results: tuple[tuple[str, SolveStatus], ...] = ()
    reason: str | None = None


def _ordered_premises(problem: SemanticProblem, premise_ids: tuple[str, ...]):
    wanted = set(premise_ids)
    if len(wanted) != len(premise_ids):
        return None
    by_id = {str(item.id): item for item in problem.semantic_constraints}
    if not wanted.issubset(by_id):
        return None
    # Deterministic policy: lexicographic constraint-ID order.  When several
    # subset-minimal cores exist, greedy deletion retains earlier IDs first.
    return tuple(by_id[item] for item in sorted(wanted))


@dataclass
class _CoreSolveBudget:
    maximum: int
    attempts: int = 0

    def solve(self, problem: SemanticProblem, constraints) -> SolveStatus | None:
        if self.attempts >= self.maximum:
            return None
        self.attempts += 1
        return solve(problem.with_constraints(tuple(constraints))).status


def _limit_result(
    premise_ids: tuple[str, ...],
    core_ids: tuple[str, ...] = (),
    *,
    maximum: int,
) -> CoreResult:
    return CoreResult(
        SolveStatus.INSUFFICIENT_EVIDENCE,
        premise_ids,
        core_ids=core_ids,
        reason="core_evaluation_limit",
        message=(
            f"minimal-core evaluation exceeded {maximum} "
            "solver invocations"
        ),
    )


def minimal_unsat_core(
    problem: SemanticProblem,
    premises: tuple[str, ...] | list[str],
    *,
    max_solve_attempts: int = MAX_CORE_SOLVE_ATTEMPTS,
) -> CoreResult:
    premise_ids = tuple(sorted({str(item) for item in premises}))
    ordered = _ordered_premises(problem, premise_ids)
    if ordered is None:
        return CoreResult(
            SolveStatus.INVALID_PROBLEM,
            premise_ids,
            reason="invalid_premises",
            message="premises must be unique semantic constraint IDs in the problem",
        )

    budget = _CoreSolveBudget(max_solve_attempts)
    initial = budget.solve(problem, ordered)
    if initial is None:
        return _limit_result(premise_ids, maximum=max_solve_attempts)
    if initial is not SolveStatus.UNSAT:
        return CoreResult(
            initial,
            tuple(str(item.id) for item in ordered),
            reason="premises_not_unsat",
        )

    core = list(ordered)
    for candidate in tuple(ordered):
        reduced = tuple(item for item in core if item is not candidate)
        reduced_status = budget.solve(problem, reduced)
        if reduced_status is None:
            return _limit_result(
                premise_ids,
                tuple(str(item.id) for item in core),
                maximum=max_solve_attempts,
            )
        if reduced_status is SolveStatus.UNSAT:
            core.remove(candidate)
        elif reduced_status is not SolveStatus.SAT:
            return CoreResult(
                reduced_status,
                premise_ids,
                core_ids=tuple(str(item.id) for item in core),
                reason="core_reduction_not_decidable",
            )

    core_ids = tuple(str(item.id) for item in core)
    verification = _verify_unsat_core(problem, core_ids, budget)
    if verification.reason == "core_evaluation_limit":
        return _limit_result(premise_ids, core_ids, maximum=max_solve_attempts)
    return CoreResult(
        SolveStatus.UNSAT,
        premise_ids,
        core_ids=core_ids,
        minimal=verification.verified,
        reason=None if verification.verified else "minimality_not_verified",
    )


def verify_unsat_core(
    problem: SemanticProblem,
    claimed_core: tuple[str, ...] | list[str],
    *,
    max_solve_attempts: int = MAX_CORE_SOLVE_ATTEMPTS,
) -> CoreVerificationResult:
    return _verify_unsat_core(
        problem,
        claimed_core,
        _CoreSolveBudget(max_solve_attempts),
    )


def _verify_unsat_core(
    problem: SemanticProblem,
    claimed_core: tuple[str, ...] | list[str],
    budget: _CoreSolveBudget,
) -> CoreVerificationResult:
    core_ids = tuple(str(item) for item in claimed_core)
    ordered = _ordered_premises(problem, core_ids)
    if ordered is None or not ordered:
        return CoreVerificationResult(
            verified=False,
            core_ids=core_ids,
            unsat_verified=False,
            reason="invalid_core",
        )

    status = budget.solve(problem, ordered)
    if status is None:
        return CoreVerificationResult(
            verified=False,
            core_ids=tuple(str(item.id) for item in ordered),
            unsat_verified=False,
            reason="core_evaluation_limit",
        )
    if status is not SolveStatus.UNSAT:
        return CoreVerificationResult(
            verified=False,
            core_ids=tuple(str(item.id) for item in ordered),
            unsat_verified=False,
            reason="core_not_unsat",
        )

    deletions: list[tuple[str, SolveStatus]] = []
    for removed in tuple(ordered):
        reduced = tuple(item for item in ordered if item is not removed)
        reduced_status: SolveStatus | None
        if not reduced:
            reduced_status = SolveStatus.SAT
        else:
            reduced_status = budget.solve(problem, reduced)
            if reduced_status is None:
                return CoreVerificationResult(
                    verified=False,
                    core_ids=tuple(str(item.id) for item in ordered),
                    unsat_verified=True,
                    deletion_results=tuple(deletions),
                    reason="core_evaluation_limit",
                )
        deletions.append((str(removed.id), reduced_status))
        if reduced_status is not SolveStatus.SAT:
            return CoreVerificationResult(
                verified=False,
                core_ids=tuple(str(item.id) for item in ordered),
                unsat_verified=True,
                deletion_results=tuple(deletions),
                reason="deletion_not_sat",
            )

    return CoreVerificationResult(
        verified=True,
        core_ids=tuple(str(item.id) for item in ordered),
        unsat_verified=True,
        deletion_results=tuple(deletions),
    )
