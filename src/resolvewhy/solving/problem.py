from __future__ import annotations

from dataclasses import dataclass

from resolvewhy.model import (
    Artifact,
    Candidate,
    CandidateDomain,
    DependencyEdge,
    EvidenceState,
    Requirement,
    ResolutionPolicy,
    RuntimeContext,
    SemanticConstraint,
    Trace,
    ProofQuantifier,
)


@dataclass(frozen=True)
class SemanticProblem:
    """Immutable finite semantic problem consumed by the production solver.

    This is deliberately a semantic view of a production trace.  It contains
    only the model objects required for satisfiability evaluation and does not
    retain the resolver, trace schema, proof claim, diagnostics, or filesystem
    state.
    """

    requirements: tuple[Requirement, ...]
    candidates: tuple[Candidate, ...]
    artifacts: tuple[Artifact, ...]
    dependencies: tuple[DependencyEdge, ...]
    candidate_domains: tuple[CandidateDomain, ...]
    semantic_constraints: tuple[SemanticConstraint, ...]
    runtime_contexts: tuple[RuntimeContext, ...]
    resolution_policy: ResolutionPolicy
    evidence_state: EvidenceState
    quantifier: ProofQuantifier

    @classmethod
    def from_trace(
        cls,
        trace: Trace,
        constraints: tuple[SemanticConstraint, ...],
        contexts: tuple[RuntimeContext, ...],
        quantifier: ProofQuantifier,
    ) -> "SemanticProblem":
        return cls(
            requirements=trace.requirements,
            candidates=trace.candidates,
            artifacts=trace.artifacts,
            dependencies=trace.dependencies,
            candidate_domains=trace.candidate_domains,
            semantic_constraints=constraints,
            runtime_contexts=contexts,
            resolution_policy=trace.resolution_policy,
            evidence_state=trace.evidence_state,
            quantifier=quantifier,
        )

    def with_constraints(
        self,
        constraints: tuple[SemanticConstraint, ...],
    ) -> "SemanticProblem":
        return SemanticProblem(
            requirements=self.requirements,
            candidates=self.candidates,
            artifacts=self.artifacts,
            dependencies=self.dependencies,
            candidate_domains=self.candidate_domains,
            semantic_constraints=constraints,
            runtime_contexts=self.runtime_contexts,
            resolution_policy=self.resolution_policy,
            evidence_state=self.evidence_state,
            quantifier=self.quantifier,
        )
