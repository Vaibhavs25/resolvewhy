from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from resolvewhy.model import (
    CoverageStatus,
    EvidenceStateKind,
    ProofQuantifier,
    ReferenceKind,
    Trace,
    TraceRef,
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    ref: TraceRef | None = None


class TraceValidationError(ValueError):
    def __init__(self, issues: tuple[ValidationIssue, ...]):
        self.issues = issues
        summary = "; ".join(issue.message for issue in issues)
        super().__init__(summary)


def _duplicate_issues(items: Iterable[object], kind: ReferenceKind) -> list[ValidationIssue]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(getattr(item, "id"))
        counts[value] = counts.get(value, 0) + 1

    return [
        ValidationIssue(
            "duplicate_id",
            f"duplicate {kind.value} id: {value}",
            TraceRef(kind, value),
        )
        for value, count in counts.items()
        if count > 1
    ]


def validate_trace(trace: Trace) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []

    collections = {
        ReferenceKind.RUNTIME_CONTEXT: trace.runtime_contexts,
        ReferenceKind.CANDIDATE_DOMAIN: trace.candidate_domains,
        ReferenceKind.REQUIREMENT: trace.requirements,
        ReferenceKind.CANDIDATE: trace.candidates,
        ReferenceKind.ARTIFACT: trace.artifacts,
        ReferenceKind.DEPENDENCY: trace.dependencies,
        ReferenceKind.REJECTION: trace.rejections,
        ReferenceKind.INCOMPATIBILITY: trace.incompatibilities,
        ReferenceKind.CONSTRAINT: trace.semantic_constraints,
        ReferenceKind.EVIDENCE: trace.evidence_state.observations,
        ReferenceKind.PROVENANCE: trace.provenance,
    }

    for kind, items in collections.items():
        issues.extend(_duplicate_issues(items, kind))

    by_id = {
        kind: {str(getattr(item, "id")) for item in items}
        for kind, items in collections.items()
    }
    by_id[ReferenceKind.EVALUATION_DOMAIN] = {str(trace.evaluation_domain.id)}
    by_id[ReferenceKind.POLICY] = {str(trace.resolution_policy.id)}
    by_id[ReferenceKind.PROOF_CLAIM] = {str(trace.proof_claim.id)}

    def exists(ref: TraceRef) -> bool:
        return ref.id in by_id.get(ref.kind, set())

    def require_ref(ref: TraceRef, code: str = "dangling_reference") -> None:
        if not exists(ref):
            issues.append(
                ValidationIssue(
                    code,
                    f"dangling {ref.kind.value} reference: {ref.id}",
                    ref,
                )
            )

    runtime_ids = by_id[ReferenceKind.RUNTIME_CONTEXT]
    candidate_ids = by_id[ReferenceKind.CANDIDATE]
    artifact_ids = by_id[ReferenceKind.ARTIFACT]
    requirement_ids = by_id[ReferenceKind.REQUIREMENT]
    constraint_ids = by_id[ReferenceKind.CONSTRAINT]
    policy_ids = by_id[ReferenceKind.POLICY]

    # Evaluation-domain integrity and explicit proof binding.
    for env_ref in trace.evaluation_domain.environment_refs:
        env_trace_ref = TraceRef(ReferenceKind.RUNTIME_CONTEXT, str(env_ref))
        if str(env_ref) not in runtime_ids:
            issues.append(
                ValidationIssue(
                    "invalid_evaluation_domain",
                    f"evaluation domain references missing runtime context: {env_ref}",
                    env_trace_ref,
                )
            )

    if str(trace.proof_claim.evaluation_domain_ref) != str(trace.evaluation_domain.id):
        issues.append(
            ValidationIssue(
                "invalid_proof_binding",
                "proof claim must bind to the trace evaluation domain",
                TraceRef(
                    ReferenceKind.EVALUATION_DOMAIN,
                    str(trace.proof_claim.evaluation_domain_ref),
                ),
            )
        )

    if trace.proof_claim.quantifier is ProofQuantifier.BRANCH:
        branch_id = str(trace.proof_claim.branch_ref)
        if branch_id not in {str(ref) for ref in trace.evaluation_domain.environment_refs}:
            issues.append(
                ValidationIssue(
                    "invalid_proof_binding",
                    "branch proof must reference an environment inside the evaluation domain",
                    TraceRef(ReferenceKind.RUNTIME_CONTEXT, branch_id),
                )
            )
    elif trace.proof_claim.branch_ref is not None:
        issues.append(
            ValidationIssue(
                "invalid_proof_binding",
                "only branch proofs may declare branch_ref",
                TraceRef(
                    ReferenceKind.RUNTIME_CONTEXT,
                    str(trace.proof_claim.branch_ref),
                ),
            )
        )

    if trace.proof_claim.subset_minimal_claim:
        premise_ids = {str(ref) for ref in trace.proof_claim.premise_refs}
        core_ids = {str(ref) for ref in trace.proof_claim.claimed_core_refs}
        extra = sorted(core_ids - premise_ids)
        if extra:
            issues.append(
                ValidationIssue(
                    "invalid_proof_binding",
                    "claimed subset-minimal core must be drawn from proof premises",
                    TraceRef(ReferenceKind.CONSTRAINT, extra[0]),
                )
            )

    # Requirements and dependency edges.
    for req in trace.requirements:
        if req.parent_candidate_ref is not None and str(req.parent_candidate_ref) not in candidate_ids:
            issues.append(
                ValidationIssue(
                    "dangling_reference",
                    f"requirement {req.id} references missing parent candidate {req.parent_candidate_ref}",
                    TraceRef(ReferenceKind.CANDIDATE, str(req.parent_candidate_ref)),
                )
            )
        for ref in req.evidence_refs:
            require_ref(ref)

    for edge in trace.dependencies:
        if str(edge.parent_candidate_ref) not in candidate_ids:
            issues.append(
                ValidationIssue(
                    "dangling_reference",
                    f"dependency {edge.id} references missing parent candidate {edge.parent_candidate_ref}",
                    TraceRef(ReferenceKind.CANDIDATE, str(edge.parent_candidate_ref)),
                )
            )
        if str(edge.requirement_ref) not in requirement_ids:
            issues.append(
                ValidationIssue(
                    "dangling_reference",
                    f"dependency {edge.id} references missing requirement {edge.requirement_ref}",
                    TraceRef(ReferenceKind.REQUIREMENT, str(edge.requirement_ref)),
                )
            )
        for ref in edge.evidence_refs:
            require_ref(ref)

    # Candidate/artifact identity.
    for candidate in trace.candidates:
        if candidate.metadata_ref is not None:
            require_ref(candidate.metadata_ref)

    for artifact in trace.artifacts:
        if str(artifact.candidate_ref) not in candidate_ids:
            issues.append(
                ValidationIssue(
                    "candidate_artifact_identity",
                    f"artifact {artifact.id} references missing candidate {artifact.candidate_ref}",
                    TraceRef(ReferenceKind.CANDIDATE, str(artifact.candidate_ref)),
                )
            )
        if artifact.metadata_ref is not None:
            require_ref(artifact.metadata_ref)
        for ref in artifact.evidence_refs:
            require_ref(ref)

    # Candidate-domain coverage.
    for domain in trace.candidate_domains:
        if str(domain.runtime_context_ref) not in runtime_ids:
            issues.append(
                ValidationIssue(
                    "invalid_coverage_reference",
                    f"candidate domain {domain.id} references missing runtime context {domain.runtime_context_ref}",
                    TraceRef(ReferenceKind.RUNTIME_CONTEXT, str(domain.runtime_context_ref)),
                )
            )
        if str(domain.resolution_policy_ref) not in policy_ids:
            issues.append(
                ValidationIssue(
                    "invalid_coverage_reference",
                    f"candidate domain {domain.id} references missing resolution policy {domain.resolution_policy_ref}",
                    TraceRef(ReferenceKind.POLICY, str(domain.resolution_policy_ref)),
                )
            )
        for req_ref in domain.requirement_refs:
            if str(req_ref) not in requirement_ids:
                issues.append(
                    ValidationIssue(
                        "invalid_coverage_reference",
                        f"candidate domain {domain.id} references missing requirement {req_ref}",
                        TraceRef(ReferenceKind.REQUIREMENT, str(req_ref)),
                    )
                )
        for candidate_ref in domain.candidate_refs:
            if str(candidate_ref) not in candidate_ids:
                issues.append(
                    ValidationIssue(
                        "invalid_coverage_reference",
                        f"candidate domain {domain.id} references missing candidate {candidate_ref}",
                        TraceRef(ReferenceKind.CANDIDATE, str(candidate_ref)),
                    )
                )

        coverage = domain.coverage
        for ref in coverage.evidence_refs:
            require_ref(ref)

        if coverage.status is CoverageStatus.COMPLETE:
            if coverage.attestation is None:
                issues.append(
                    ValidationIssue(
                        "invalid_coverage_attestation",
                        f"complete candidate domain {domain.id} requires a completeness attestation",
                        TraceRef(ReferenceKind.CANDIDATE_DOMAIN, str(domain.id)),
                    )
                )
            else:
                for ref in coverage.attestation.evidence_refs:
                    require_ref(ref, "invalid_coverage_attestation")
        elif coverage.attestation is not None:
            issues.append(
                ValidationIssue(
                    "invalid_coverage_attestation",
                    f"non-complete candidate domain {domain.id} must not carry a completeness attestation",
                    TraceRef(ReferenceKind.CANDIDATE_DOMAIN, str(domain.id)),
                )
            )

        if domain.scope.artifact_policy_ref is not None and str(domain.scope.artifact_policy_ref) not in policy_ids:
            issues.append(
                ValidationIssue(
                    "invalid_coverage_reference",
                    f"candidate domain {domain.id} references missing artifact policy {domain.scope.artifact_policy_ref}",
                    TraceRef(ReferenceKind.POLICY, str(domain.scope.artifact_policy_ref)),
                )
            )

    # Semantic constraints and literals.
    for constraint in trace.semantic_constraints:
        for ref in constraint.source_refs:
            require_ref(ref)

        for literal in constraint.literals:
            if literal.candidate_ref is not None and str(literal.candidate_ref) not in candidate_ids:
                issues.append(
                    ValidationIssue(
                        "dangling_reference",
                        f"constraint {constraint.id} references missing candidate {literal.candidate_ref}",
                        TraceRef(ReferenceKind.CANDIDATE, str(literal.candidate_ref)),
                    )
                )
            if literal.artifact_ref is not None and str(literal.artifact_ref) not in artifact_ids:
                issues.append(
                    ValidationIssue(
                        "dangling_reference",
                        f"constraint {constraint.id} references missing artifact {literal.artifact_ref}",
                        TraceRef(ReferenceKind.ARTIFACT, str(literal.artifact_ref)),
                    )
                )
            if literal.runtime_context_ref is not None and str(literal.runtime_context_ref) not in runtime_ids:
                issues.append(
                    ValidationIssue(
                        "dangling_reference",
                        f"constraint {constraint.id} references missing runtime context {literal.runtime_context_ref}",
                        TraceRef(ReferenceKind.RUNTIME_CONTEXT, str(literal.runtime_context_ref)),
                    )
                )
            if literal.package is None and literal.candidate_ref is None and literal.artifact_ref is None:
                issues.append(
                    ValidationIssue(
                        "malformed_semantic_literal",
                        f"constraint {constraint.id} contains a literal without a semantic subject",
                        TraceRef(ReferenceKind.CONSTRAINT, str(constraint.id)),
                    )
                )

    # Proof premises must be actual semantic constraints.
    for premise_ref in trace.proof_claim.premise_refs:
        if str(premise_ref) not in constraint_ids:
            issues.append(
                ValidationIssue(
                    "invalid_proof_premise",
                    f"proof claim references missing semantic constraint {premise_ref}",
                    TraceRef(ReferenceKind.CONSTRAINT, str(premise_ref)),
                )
            )
    for core_ref in trace.proof_claim.claimed_core_refs:
        if str(core_ref) not in constraint_ids:
            issues.append(
                ValidationIssue(
                    "invalid_proof_premise",
                    f"claimed core references missing semantic constraint {core_ref}",
                    TraceRef(ReferenceKind.CONSTRAINT, str(core_ref)),
                )
            )

    # Evidence references.
    for observation in trace.evidence_state.observations:
        for ref in observation.supports_refs:
            require_ref(ref)

    for rejection in trace.rejections:
        require_ref(rejection.target_ref)
        for ref in rejection.premise_refs:
            require_ref(ref)

    incompatibility_ids = {str(item.id) for item in trace.incompatibilities}
    for incompatibility in trace.incompatibilities:
        for ref in incompatibility.term_refs:
            require_ref(ref)
        for derivation_ref in incompatibility.derivation_refs:
            if str(derivation_ref) not in incompatibility_ids:
                issues.append(
                    ValidationIssue(
                        "dangling_reference",
                        f"incompatibility {incompatibility.id} references missing derivation {derivation_ref}",
                        TraceRef(ReferenceKind.INCOMPATIBILITY, str(derivation_ref)),
                    )
                )

    # Provenance integrity and a conservative cycle check.
    provenance_subjects: dict[TraceRef, list[object]] = {}
    for record in trace.provenance:
        require_ref(record.subject_ref)
        provenance_subjects.setdefault(record.subject_ref, []).append(record)
        for ref in record.premise_refs:
            require_ref(ref)

    for subject, records in provenance_subjects.items():
        kinds = {record.kind for record in records}
        if len(kinds) > 1:
            issues.append(
                ValidationIssue(
                    "inconsistent_provenance",
                    f"provenance for {subject.kind.value}:{subject.id} mixes direct and derived records",
                    subject,
                )
            )

    visiting: set[TraceRef] = set()
    visited: set[TraceRef] = set()

    def visit(ref: TraceRef) -> None:
        if ref in visited:
            return
        if ref in visiting:
            issues.append(
                ValidationIssue(
                    "inconsistent_provenance",
                    f"provenance cycle detected at {ref.kind.value}:{ref.id}",
                    ref,
                )
            )
            return

        visiting.add(ref)
        for record in provenance_subjects.get(ref, ()):
            for premise in record.premise_refs:
                if premise in provenance_subjects:
                    visit(premise)
        visiting.remove(ref)
        visited.add(ref)

    for subject_ref in provenance_subjects:
        visit(subject_ref)

    # The top-level evidence state is intentionally not interpreted here.
    # Unknown/incomplete evidence is structurally valid; the future verifier
    # will classify proof sufficiency from it.
    _ = EvidenceStateKind

    return tuple(issues)


def assert_valid_trace(trace: Trace) -> None:
    issues = validate_trace(trace)
    if issues:
        raise TraceValidationError(issues)
