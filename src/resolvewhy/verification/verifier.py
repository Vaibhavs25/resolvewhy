from __future__ import annotations

from typing import Iterable

from resolvewhy.model import (
    CoverageStatus,
    EvidenceStateKind,
    ProofQuantifier,
    ProofStatus,
    ReferenceKind,
    Trace,
    VerificationStatus,
)
from resolvewhy.trace import SCHEMA, TraceDecodeError, deserialize_trace
from resolvewhy.validation import validate_trace

from .result import VerificationIssue, VerificationResult
from .semantics import (
    BranchOutcome,
    SemanticGap,
    EvaluationLimit,
    _candidate_domain_map,
    _constraint_packages,
    _constraint_source,
    _validate_constraint_shape,
    evaluate_branch,
)


_BLOCKING_EVIDENCE = {
    EvidenceStateKind.INCOMPLETE,
    EvidenceStateKind.MISSING,
    EvidenceStateKind.UNKNOWN,
}


def _issue(
    code: str,
    message: str,
    ref=None,
) -> VerificationIssue:
    return VerificationIssue(code=code, message=message, ref=ref)


def _base_result(
    trace: Trace | None,
    *,
    status: VerificationStatus,
    issues: tuple[VerificationIssue, ...] = (),
    reasons: tuple[str, ...] = (),
    branch_results: tuple[str, ...] = (),
    core_ids: tuple[str, ...] = (),
    core_verified: bool | None = None,
    minimality_verified: bool | None = None,
    independently_verified: bool | None = None,
) -> VerificationResult:
    claim = trace.proof_claim if trace is not None else None
    evaluation_domain = (
        tuple(str(ref) for ref in trace.evaluation_domain.environment_refs)
        if trace is not None
        else ()
    )
    premise_ids = (
        tuple(str(ref) for ref in claim.premise_refs)
        if claim is not None
        else ()
    )
    if independently_verified is None:
        independently_verified = status in {
            VerificationStatus.VERIFIED_SAT,
            VerificationStatus.VERIFIED_UNSAT,
        }
    return VerificationResult(
        status=status,
        independently_verified=independently_verified,
        proof_claim_id=str(claim.id) if claim is not None else None,
        quantifier=claim.quantifier if claim is not None else None,
        evaluation_domain=evaluation_domain,
        premise_ids=premise_ids,
        core_ids=core_ids,
        core_verified=core_verified,
        minimality_verified=minimality_verified,
        reasons=reasons,
        issues=issues,
        branch_results=branch_results,
    )


def _invalid(
    trace: Trace,
    issues: Iterable[VerificationIssue],
) -> VerificationResult:
    values = tuple(issues)
    return _base_result(
        trace,
        status=VerificationStatus.INVALID_TRACE,
        issues=values,
        reasons=tuple(issue.code for issue in values),
        independently_verified=False,
    )


def _insufficient(
    trace: Trace,
    *,
    reason: str,
    message: str,
    ref=None,
) -> VerificationResult:
    return _base_result(
        trace,
        status=VerificationStatus.INSUFFICIENT_EVIDENCE,
        reasons=(reason,),
        issues=(_issue(reason, message, ref),),
        independently_verified=False,
    )


def _blocking_evidence_states(trace: Trace) -> set[str]:
    return {
        str(obs.id)
        for obs in trace.evidence_state.observations
        if obs.state in _BLOCKING_EVIDENCE
    }


def _validate_relevant_evidence(
    trace: Trace,
    constraints,
) -> VerificationResult | None:
    observations = {
        str(obs.id): obs
        for obs in trace.evidence_state.observations
    }
    for constraint in constraints:
        for ref in constraint.source_refs:
            if ref.kind is not ReferenceKind.EVIDENCE:
                continue
            observation = observations.get(str(ref.id))
            if observation is None:
                return _invalid(
                    trace,
                    (
                        _issue(
                            "dangling_reference",
                            f"semantic constraint {constraint.id} references missing evidence {ref.id}",
                            ref,
                        ),
                    ),
                )
            if observation.state in _BLOCKING_EVIDENCE:
                return _insufficient(
                    trace,
                    reason=(
                        "missing_evidence"
                        if observation.state is EvidenceStateKind.MISSING
                        else "incomplete_evidence"
                    ),
                    message=(
                        f"proof-relevant evidence {observation.id} is "
                        f"{observation.state.value}"
                    ),
                    ref=ref,
                )
    return None


def _validate_candidate_coverage(
    trace: Trace,
    constraints,
    contexts,
) -> VerificationResult | None:
    candidate_by_id = {
        str(candidate.id): candidate
        for candidate in trace.candidates
    }

    try:
        packages = _constraint_packages(trace, constraints)
    except SemanticGap as exc:
        if exc.code.startswith("invalid_"):
            return _invalid(
                trace,
                (_issue(exc.code, str(exc)),),
            )
        return _insufficient(
            trace,
            reason=exc.code,
            message=str(exc),
        )

    observations = {
        str(obs.id): obs
        for obs in trace.evidence_state.observations
    }

    for context in contexts:
        for package in sorted(packages):
            domains = [
                domain
                for domain in trace.candidate_domains
                if domain.identifier == package
                and str(domain.runtime_context_ref) == str(context.id)
            ]
            if not domains:
                return _insufficient(
                    trace,
                    reason="incomplete_candidate_coverage",
                    message=(
                        f"no candidate domain covers package {package!r} "
                        f"in runtime context {context.id}"
                    ),
                )

            for domain in domains:
                if str(domain.resolution_policy_ref) != str(trace.resolution_policy.id):
                    return _invalid(
                        trace,
                        (
                            _issue(
                                "invalid_coverage_reference",
                                (
                                    f"candidate domain {domain.id} uses policy "
                                    f"{domain.resolution_policy_ref}, not the trace policy "
                                    f"{trace.resolution_policy.id}"
                                ),
                            ),
                        ),
                    )
                if domain.coverage.status is not CoverageStatus.COMPLETE:
                    return _insufficient(
                        trace,
                        reason="incomplete_candidate_coverage",
                        message=(
                            f"candidate domain {domain.id} has "
                            f"{domain.coverage.status.value} coverage"
                        ),
                    )

                attestation = domain.coverage.attestation
                if attestation is None:
                    return _invalid(
                        trace,
                        (
                            _issue(
                                "invalid_coverage_attestation",
                                f"complete candidate domain {domain.id} lacks attestation",
                            ),
                        ),
                    )
                for evidence_ref in attestation.evidence_refs:
                    observation = observations.get(str(evidence_ref.id))
                    if observation is None:
                        return _invalid(
                            trace,
                            (
                                _issue(
                                    "invalid_coverage_attestation",
                                    (
                                        f"candidate domain {domain.id} references "
                                        f"missing coverage evidence {evidence_ref.id}"
                                    ),
                                    evidence_ref,
                                ),
                            ),
                        )
                    if observation.state in _BLOCKING_EVIDENCE:
                        return _insufficient(
                            trace,
                            reason="incomplete_candidate_coverage",
                            message=(
                                f"candidate domain {domain.id} has non-authoritative "
                                f"coverage evidence {observation.id}"
                            ),
                            ref=evidence_ref,
                        )
                    if not any(
                        supported.kind is ReferenceKind.CANDIDATE_DOMAIN
                        and str(supported.id) == str(domain.id)
                        for supported in observation.supports_refs
                    ):
                        return _invalid(
                            trace,
                            (
                                _issue(
                                    "invalid_coverage_attestation",
                                    (
                                        f"coverage evidence {observation.id} does not "
                                        f"support candidate domain {domain.id}"
                                    ),
                                    evidence_ref,
                                ),
                            ),
                        )

                for candidate_ref in domain.candidate_refs:
                    candidate = candidate_by_id.get(str(candidate_ref))
                    if candidate is None:
                        return _invalid(
                            trace,
                            (
                                _issue(
                                    "dangling_reference",
                                    f"candidate domain {domain.id} references {candidate_ref}",
                                ),
                            ),
                        )
                    if candidate.package != domain.identifier:
                        return _invalid(
                            trace,
                            (
                                _issue(
                                    "invalid_coverage_reference",
                                    (
                                        f"candidate {candidate.id} belongs to "
                                        f"{candidate.package!r}, not {domain.identifier!r}"
                                    ),
                                ),
                            ),
                        )
                    if (
                        domain.scope.sources
                        and candidate.source_ref is not None
                        and candidate.source_ref not in domain.scope.sources
                    ):
                        return _invalid(
                            trace,
                            (
                                _issue(
                                    "invalid_coverage_scope",
                                    (
                                        f"candidate {candidate.id} is outside the "
                                        f"declared source scope of domain {domain.id}"
                                    ),
                                ),
                            ),
                        )
    return None


def _validate_provenance(
    trace: Trace,
    constraints,
) -> VerificationResult | None:
    records = {str(record.id): record for record in trace.provenance}
    by_subject: dict[tuple[ReferenceKind, str], list[object]] = {}
    for record in trace.provenance:
        by_subject.setdefault(
            (record.subject_ref.kind, str(record.subject_ref.id)),
            [],
        ).append(record)

    for constraint in constraints:
        key = (ReferenceKind.CONSTRAINT, str(constraint.id))
        if key not in by_subject:
            return _invalid(
                trace,
                (
                    _issue(
                        "invalid_provenance",
                        f"proof premise {constraint.id} has no provenance record",
                    ),
                ),
            )

    evidence = {
        str(obs.id): obs
        for obs in trace.evidence_state.observations
    }
    graph: dict[str, set[str]] = {}
    for record in trace.provenance:
        graph[str(record.id)] = set()
        for premise in record.premise_refs:
            if premise.kind is ReferenceKind.EVIDENCE:
                observation = evidence.get(str(premise.id))
                if observation is None:
                    return _invalid(
                        trace,
                        (
                            _issue(
                                "invalid_provenance",
                                (
                                    f"provenance {record.id} references missing "
                                    f"evidence {premise.id}"
                                ),
                                premise,
                            ),
                        ),
                    )
                if observation.state in _BLOCKING_EVIDENCE:
                    return _insufficient(
                        trace,
                        reason="incomplete_evidence",
                        message=(
                            f"provenance evidence {observation.id} is "
                            f"{observation.state.value}"
                        ),
                        ref=premise,
                    )
            nested = by_subject.get((premise.kind, str(premise.id)))
            if nested:
                graph[str(record.id)].update(str(item.id) for item in nested)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(child) for child in graph.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(visit(node) for node in graph):
        return _invalid(
            trace,
            (_issue("invalid_provenance", "provenance cycle detected"),),
        )
    return None


def _validate_semantics(
    trace: Trace,
    constraints,
) -> VerificationResult | None:
    for constraint in constraints:
        try:
            source = _constraint_source(trace, constraint)
            _validate_constraint_shape(trace, constraint, source)
        except SemanticGap as exc:
            if exc.code.startswith("unsupported_") or exc.code.startswith("incomplete_"):
                return _insufficient(
                    trace,
                    reason=exc.code,
                    message=str(exc),
                )
            return _invalid(
                trace,
                (_issue(exc.code, str(exc)),),
            )
    return None


def _evaluate(
    trace: Trace,
    constraints,
    contexts,
) -> tuple[tuple[BranchOutcome, ...], VerificationResult | None]:
    results: list[BranchOutcome] = []
    for context in contexts:
        try:
            outcome = evaluate_branch(trace, constraints, context)
        except EvaluationLimit as exc:
            return (
                tuple(results),
                _insufficient(
                    trace,
                    reason=exc.code,
                    message=str(exc),
                ),
            )
        except SemanticGap as exc:
            if (
                exc.code.startswith("unsupported_")
                or exc.code.startswith("incomplete_")
                or exc.code in {
                    "evaluation_search_limit",
                    "unknown_artifact_compatibility",
                }
            ):
                return (
                    tuple(results),
                    _insufficient(
                        trace,
                        reason=exc.code,
                        message=str(exc),
                    ),
                )
            return (
                tuple(results),
                _invalid(
                    trace,
                    (_issue(exc.code, str(exc)),),
                ),
            )
        results.append(outcome)
    return tuple(results), None


def _combine(
    quantifier: ProofQuantifier,
    results: tuple[BranchOutcome, ...],
) -> BranchOutcome:
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
    if len(results) != 1:
        raise ValueError("branch quantifier must select exactly one environment")
    return results[0]


def _minimality(
    trace: Trace,
    premise_constraints,
    core_ids: tuple[str, ...],
    contexts,
) -> bool:
    if not core_ids:
        return False

    constraint_by_id = {
        str(constraint.id): constraint
        for constraint in premise_constraints
    }
    core = tuple(constraint_by_id[item] for item in core_ids)

    results, error = _evaluate(trace, core, contexts)
    if error is not None or _combine(trace.proof_claim.quantifier, results) is not BranchOutcome.UNSAT:
        return False

    for removed in core_ids:
        reduced = tuple(item for item in core if str(item.id) != removed)
        if not reduced:
            # The empty conjunction is satisfiable over the finite fragment.
            deletion_outcome = BranchOutcome.SAT
        else:
            results, error = _evaluate(trace, reduced, contexts)
            if error is not None:
                return False
            deletion_outcome = _combine(trace.proof_claim.quantifier, results)
        if deletion_outcome is not BranchOutcome.SAT:
            return False
    return True


def verify(trace: Trace) -> VerificationResult:
    if not isinstance(trace, Trace):
        raise TypeError("verify expects a resolvewhy.model.Trace")

    if trace.schema != SCHEMA:
        return _invalid(
            trace,
            (
                _issue(
                    "invalid_schema",
                    f"unsupported production schema {trace.schema!r}; expected {SCHEMA!r}",
                ),
            ),
        )

    structural_issues = validate_trace(trace)
    if structural_issues:
        return _invalid(
            trace,
            tuple(VerificationIssue.from_validation(issue) for issue in structural_issues),
        )

    claim = trace.proof_claim
    premises = tuple(
        constraint
        for constraint in trace.semantic_constraints
        if str(constraint.id) in {str(ref) for ref in claim.premise_refs}
    )
    if len(premises) != len(claim.premise_refs):
        return _invalid(
            trace,
            (
                _issue(
                    "invalid_proof_premise",
                    "proof premises do not resolve to the declared semantic constraints",
                ),
            ),
        )

    premise_ids = {str(item.id) for item in premises}
    claimed_core = tuple(str(item) for item in claim.claimed_core_refs)
    if not set(claimed_core).issubset(premise_ids):
        return _invalid(
            trace,
            (
                _issue(
                    "invalid_proof_binding",
                    "claimed core contains constraints outside the proof premises",
                ),
            ),
        )

    if claim.quantifier is ProofQuantifier.BRANCH:
        active_contexts = tuple(
            context
            for context in trace.runtime_contexts
            if str(context.id) == str(claim.branch_ref)
        )
    else:
        active_contexts = tuple(
            context
            for context in trace.runtime_contexts
            if str(context.id) in {str(ref) for ref in trace.evaluation_domain.environment_refs}
        )
    if not active_contexts:
        return _invalid(
            trace,
            (_issue("invalid_proof_binding", "proof claim has no applicable runtime context"),),
        )

    evidence_error = _validate_relevant_evidence(trace, premises)
    if evidence_error is not None:
        return evidence_error

    semantic_error = _validate_semantics(trace, premises)
    if semantic_error is not None:
        return semantic_error

    coverage_error = _validate_candidate_coverage(trace, premises, active_contexts)
    if coverage_error is not None:
        return coverage_error

    provenance_error = _validate_provenance(trace, premises)
    if provenance_error is not None:
        return provenance_error

    if trace.evidence_state.overall in _BLOCKING_EVIDENCE:
        return _insufficient(
            trace,
            reason="incomplete_evidence",
            message=(
                f"trace evidence state is {trace.evidence_state.overall.value}"
            ),
        )

    branch_outcomes, evaluation_error = _evaluate(trace, premises, active_contexts)
    if evaluation_error is not None:
        return evaluation_error

    combined = _combine(claim.quantifier, branch_outcomes)
    if combined is BranchOutcome.UNKNOWN:
        return _insufficient(
            trace,
            reason="insufficient_semantic_evidence",
            message="the represented proposition cannot be decided from the supported fragment",
        )

    status = (
        VerificationStatus.VERIFIED_SAT
        if combined is BranchOutcome.SAT
        else VerificationStatus.VERIFIED_UNSAT
    )
    reasons: list[str] = []
    if (
        (claim.status_claim is ProofStatus.SAT and status is VerificationStatus.VERIFIED_UNSAT)
        or (claim.status_claim is ProofStatus.UNSAT and status is VerificationStatus.VERIFIED_SAT)
    ):
        reasons.append("claim_mismatch")

    minimality_verified: bool | None = None
    if claim.subset_minimal_claim:
        minimality_verified = _minimality(
            trace,
            premises,
            tuple(claim.claimed_core_refs),
            active_contexts,
        )
        if not minimality_verified:
            reasons.append("minimality_not_verified")
    elif claim.claimed_core_refs:
        minimality_verified = None

    core_ids = tuple(str(item) for item in claim.claimed_core_refs)
    return _base_result(
        trace,
        status=status,
        reasons=tuple(reasons),
        core_ids=core_ids,
        minimality_verified=minimality_verified,
        branch_results=tuple(result.value for result in branch_outcomes),
        independently_verified=True,
    )


def verify_serialized(data: str | bytes | bytearray) -> VerificationResult:
    try:
        trace = deserialize_trace(data)
    except TraceDecodeError as exc:
        return VerificationResult(
            status=VerificationStatus.INVALID_TRACE,
            independently_verified=False,
            proof_claim_id=None,
            quantifier=None,
            evaluation_domain=(),
            premise_ids=(),
            core_ids=(),
            core_verified=None,
            minimality_verified=None,
            reasons=("invalid_trace",),
            issues=(_issue("invalid_trace", str(exc)),),
            branch_results=(),
        )
    return verify(trace)
