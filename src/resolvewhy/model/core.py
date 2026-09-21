from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, NewType


RequirementId = NewType("RequirementId", str)
DependencyEdgeId = NewType("DependencyEdgeId", str)
CandidateId = NewType("CandidateId", str)
ArtifactId = NewType("ArtifactId", str)
RuntimeContextId = NewType("RuntimeContextId", str)
EvaluationDomainId = NewType("EvaluationDomainId", str)
PolicyId = NewType("PolicyId", str)
CandidateDomainId = NewType("CandidateDomainId", str)
ConstraintId = NewType("ConstraintId", str)
EvidenceId = NewType("EvidenceId", str)
ProvenanceId = NewType("ProvenanceId", str)
ProofClaimId = NewType("ProofClaimId", str)
RejectionId = NewType("RejectionId", str)
IncompatibilityId = NewType("IncompatibilityId", str)


def _required(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


class CandidateKind(str, Enum):
    REGISTRY = "registry"
    VCS = "vcs"
    DIRECT_URL = "direct_url"
    PATH = "path"
    WORKSPACE = "workspace"
    OTHER = "other"


class ArtifactSelectionStatus(str, Enum):
    AVAILABLE = "available"
    INCOMPATIBLE = "incompatible"
    YANKED = "yanked"
    FILTERED = "filtered"
    UNKNOWN = "unknown"


class CoverageStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class CoverageAttestationKind(str, Enum):
    AUTHORITATIVE_FINITE_DOMAIN = "authoritative_finite_domain"
    EXHAUSTIVE_PROVIDER_SOURCE_QUERY = "exhaustive_provider_source_query"
    AUTHORITATIVE_SOURCE_EXHAUSTION = "authoritative_source_exhaustion"


class EvidenceStateKind(str, Enum):
    KNOWN_FACT = "known_fact"
    DERIVED_FACT = "derived_fact"
    REJECTED_CANDIDATE = "rejected_candidate"
    INCOMPLETE = "incomplete"
    MISSING = "missing"
    UNKNOWN = "unknown"


class ProofQuantifier(str, Enum):
    EXISTENTIAL = "existential"
    UNIVERSAL = "universal"
    BRANCH = "branch"


class ProofStatus(str, Enum):
    SAT = "SAT"
    UNSAT = "UNSAT"


class VerificationStatus(str, Enum):
    VERIFIED_SAT = "VERIFIED_SAT"
    VERIFIED_UNSAT = "VERIFIED_UNSAT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVALID_TRACE = "INVALID_TRACE"


class EvaluationDomainKind(str, Enum):
    SINGLETON_ENVIRONMENT = "singleton_environment"
    FINITE_ENVIRONMENT_SET = "finite_environment_set"
    FINITE_ENVIRONMENT_PARTITION = "finite_environment_partition"


class TraceScope(str, Enum):
    SINGLE_ENVIRONMENT = "single_environment"
    MULTI_ENVIRONMENT = "multi_environment"
    FORKED = "forked"


class SemanticConstraintKind(str, Enum):
    REQUIREMENT = "requirement"
    DEPENDENCY = "dependency"
    REQUIRES_PYTHON = "requires_python"
    CANDIDATE_ADMISSIBILITY = "candidate_admissibility"
    ARTIFACT_COMPATIBILITY = "artifact_compatibility"
    OTHER = "other"


class ProvenanceKind(str, Enum):
    DIRECT = "direct"
    DERIVED = "derived"


class ReferenceKind(str, Enum):
    REQUIREMENT = "requirement"
    DEPENDENCY = "dependency"
    CANDIDATE = "candidate"
    ARTIFACT = "artifact"
    RUNTIME_CONTEXT = "runtime_context"
    EVALUATION_DOMAIN = "evaluation_domain"
    POLICY = "policy"
    CANDIDATE_DOMAIN = "candidate_domain"
    CONSTRAINT = "constraint"
    EVIDENCE = "evidence"
    PROVENANCE = "provenance"
    PROOF_CLAIM = "proof_claim"
    REJECTION = "rejection"
    INCOMPATIBILITY = "incompatibility"


VersionOperator = Literal["==", "!=", "<", "<=", ">", ">="]


@dataclass(frozen=True)
class TraceRef:
    kind: ReferenceKind
    id: str

    def __post_init__(self) -> None:
        _required(self.id, "TraceRef.id")


@dataclass(frozen=True)
class VersionConstraint:
    operator: VersionOperator
    version: str

    def __post_init__(self) -> None:
        _required(self.version, "VersionConstraint.version")


@dataclass(frozen=True)
class MarkerAtom:
    variable: str
    operator: str
    value: str

    def __post_init__(self) -> None:
        _required(self.variable, "MarkerAtom.variable")
        _required(self.operator, "MarkerAtom.operator")


@dataclass(frozen=True)
class MarkerExpression:
    kind: Literal["atom", "and", "or", "not"]
    atom: MarkerAtom | None = None
    children: tuple["MarkerExpression", ...] = ()

    def __post_init__(self) -> None:
        if self.kind == "atom":
            if self.atom is None or self.children:
                raise ValueError("atom marker expressions require exactly one atom")
        elif self.kind == "not":
            if self.atom is not None or len(self.children) != 1:
                raise ValueError("not marker expressions require exactly one child")
        elif self.kind in {"and", "or"}:
            if self.atom is not None or len(self.children) < 1:
                raise ValueError("and/or marker expressions require child expressions")
        else:
            raise ValueError(f"unsupported marker expression kind: {self.kind!r}")


@dataclass(frozen=True)
class Requirement:
    id: RequirementId
    package: str
    constraint: VersionConstraint | None
    raw: str | None = None
    parent_candidate_ref: CandidateId | None = None
    activation: MarkerExpression | None = None
    evidence_refs: tuple[TraceRef, ...] = ()

    def __post_init__(self) -> None:
        _required(str(self.id), "Requirement.id")
        _required(self.package, "Requirement.package")


@dataclass(frozen=True)
class DependencyEdge:
    id: DependencyEdgeId
    parent_candidate_ref: CandidateId
    requirement_ref: RequirementId
    activation: MarkerExpression | None = None
    raw_dependency: str | None = None
    evidence_refs: tuple[TraceRef, ...] = ()
    source_namespace: str | None = None

    def __post_init__(self) -> None:
        _required(str(self.id), "DependencyEdge.id")
        _required(str(self.parent_candidate_ref), "DependencyEdge.parent_candidate_ref")
        _required(str(self.requirement_ref), "DependencyEdge.requirement_ref")


@dataclass(frozen=True)
class Candidate:
    id: CandidateId
    package: str
    version: str | None
    kind: CandidateKind
    source_ref: str | None = None
    origin: str | None = None
    metadata_ref: TraceRef | None = None

    def __post_init__(self) -> None:
        _required(str(self.id), "Candidate.id")
        _required(self.package, "Candidate.package")
        if self.source_ref is not None:
            _required(self.source_ref, "Candidate.source_ref")


@dataclass(frozen=True)
class Artifact:
    id: ArtifactId
    candidate_ref: CandidateId
    origin: str | None = None
    tags: tuple[str, ...] = ()
    hash: str | None = None
    metadata_ref: TraceRef | None = None
    compatible: bool | None = None
    selection_status: ArtifactSelectionStatus = ArtifactSelectionStatus.UNKNOWN
    evidence_refs: tuple[TraceRef, ...] = ()

    def __post_init__(self) -> None:
        _required(str(self.id), "Artifact.id")
        _required(str(self.candidate_ref), "Artifact.candidate_ref")


@dataclass(frozen=True)
class RuntimeContext:
    id: RuntimeContextId
    python_implementation: str
    python_version: str
    os: str
    architecture: str
    marker_values: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _required(str(self.id), "RuntimeContext.id")
        _required(self.python_implementation, "RuntimeContext.python_implementation")
        _required(self.python_version, "RuntimeContext.python_version")
        _required(self.os, "RuntimeContext.os")
        _required(self.architecture, "RuntimeContext.architecture")
        if tuple(sorted(self.marker_values)) != self.marker_values:
            raise ValueError("RuntimeContext.marker_values must be sorted by key")


@dataclass(frozen=True)
class EvaluationDomain:
    id: EvaluationDomainId
    kind: EvaluationDomainKind
    environment_refs: tuple[RuntimeContextId, ...]
    evidence_refs: tuple[TraceRef, ...] = ()

    def __post_init__(self) -> None:
        _required(str(self.id), "EvaluationDomain.id")
        if not self.environment_refs:
            raise ValueError("EvaluationDomain.environment_refs must not be empty")
        if len(set(self.environment_refs)) != len(self.environment_refs):
            raise ValueError("EvaluationDomain.environment_refs must be unique")
        if self.kind is EvaluationDomainKind.SINGLETON_ENVIRONMENT and len(self.environment_refs) != 1:
            raise ValueError("singleton evaluation domains require exactly one environment")


@dataclass(frozen=True)
class ResolutionPolicy:
    id: PolicyId
    prerelease_mode: Literal["allow", "disallow", "only", "unspecified"] = "unspecified"
    source_selection: tuple[str, ...] = ()
    format_policy: tuple[str, ...] = ()
    hash_policy: tuple[str, ...] = ()
    version_selection: str | None = None
    universal_strategy: Literal["single", "universal", "fork", "unspecified"] = "unspecified"
    cutoff_exclusions: tuple[str, ...] = ()
    lockfile_preferences: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _required(str(self.id), "ResolutionPolicy.id")
        if self.prerelease_mode not in {"allow", "disallow", "only", "unspecified"}:
            raise ValueError("ResolutionPolicy.prerelease_mode is invalid")
        if self.universal_strategy not in {"single", "universal", "fork", "unspecified"}:
            raise ValueError("ResolutionPolicy.universal_strategy is invalid")


@dataclass(frozen=True)
class CandidateDomainScope:
    sources: tuple[str, ...] = ()
    queries: tuple[str, ...] = ()
    artifact_policy_ref: PolicyId | None = None

    def __post_init__(self) -> None:
        if any(not isinstance(value, str) or not value.strip() for value in self.sources):
            raise ValueError("CandidateDomainScope.sources cannot contain empty values")
        if any(not isinstance(value, str) or not value.strip() for value in self.queries):
            raise ValueError("CandidateDomainScope.queries cannot contain empty values")


@dataclass(frozen=True)
class CoverageAttestation:
    kind: CoverageAttestationKind
    evidence_refs: tuple[TraceRef, ...]

    def __post_init__(self) -> None:
        if not self.evidence_refs:
            raise ValueError("CoverageAttestation.evidence_refs must not be empty")


@dataclass(frozen=True)
class CandidateCoverage:
    status: CoverageStatus
    attestation: CoverageAttestation | None = None
    evidence_refs: tuple[TraceRef, ...] = ()


@dataclass(frozen=True)
class CandidateDomain:
    id: CandidateDomainId
    identifier: str
    requirement_refs: tuple[RequirementId, ...]
    candidate_refs: tuple[CandidateId, ...]
    scope: CandidateDomainScope
    runtime_context_ref: RuntimeContextId
    resolution_policy_ref: PolicyId
    coverage: CandidateCoverage

    def __post_init__(self) -> None:
        _required(str(self.id), "CandidateDomain.id")
        _required(self.identifier, "CandidateDomain.identifier")
        _required(str(self.runtime_context_ref), "CandidateDomain.runtime_context_ref")
        _required(str(self.resolution_policy_ref), "CandidateDomain.resolution_policy_ref")
        if len(set(self.requirement_refs)) != len(self.requirement_refs):
            raise ValueError("CandidateDomain.requirement_refs must be unique")
        if len(set(self.candidate_refs)) != len(self.candidate_refs):
            raise ValueError("CandidateDomain.candidate_refs must be unique")


@dataclass(frozen=True)
class SemanticLiteral:
    kind: SemanticConstraintKind
    package: str | None = None
    candidate_ref: CandidateId | None = None
    artifact_ref: ArtifactId | None = None
    runtime_context_ref: RuntimeContextId | None = None
    operator: str | None = None
    value: str | bool | None = None
    activation: MarkerExpression | None = None

    def __post_init__(self) -> None:
        if (self.operator is None) != (self.value is None):
            raise ValueError("SemanticLiteral.operator and value must be provided together")


@dataclass(frozen=True)
class SemanticConstraint:
    id: ConstraintId
    kind: SemanticConstraintKind
    literals: tuple[SemanticLiteral, ...]
    source_refs: tuple[TraceRef, ...] = ()

    def __post_init__(self) -> None:
        _required(str(self.id), "SemanticConstraint.id")
        if not self.literals:
            raise ValueError("SemanticConstraint.literals must not be empty")


@dataclass(frozen=True)
class RejectionObservation:
    id: RejectionId
    target_ref: TraceRef
    reason_kind: str
    source_layer: str
    evidence_status: EvidenceStateKind
    premise_refs: tuple[TraceRef, ...] = ()

    def __post_init__(self) -> None:
        _required(str(self.id), "RejectionObservation.id")
        _required(self.reason_kind, "RejectionObservation.reason_kind")
        _required(self.source_layer, "RejectionObservation.source_layer")


@dataclass(frozen=True)
class IncompatibilityObservation:
    id: IncompatibilityId
    semantics: str
    resolver_namespace: str
    term_refs: tuple[TraceRef, ...] = ()
    derivation_refs: tuple[IncompatibilityId, ...] = ()

    def __post_init__(self) -> None:
        _required(str(self.id), "IncompatibilityObservation.id")
        _required(self.semantics, "IncompatibilityObservation.semantics")
        _required(self.resolver_namespace, "IncompatibilityObservation.resolver_namespace")


@dataclass(frozen=True)
class EvidenceObservation:
    id: EvidenceId
    kind: str
    state: EvidenceStateKind
    supports_refs: tuple[TraceRef, ...] = ()
    source_namespace: str | None = None

    def __post_init__(self) -> None:
        _required(str(self.id), "EvidenceObservation.id")
        _required(self.kind, "EvidenceObservation.kind")


@dataclass(frozen=True)
class EvidenceState:
    overall: EvidenceStateKind
    observations: tuple[EvidenceObservation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.overall, EvidenceStateKind):
            raise ValueError("EvidenceState.overall is invalid")


@dataclass(frozen=True)
class ProvenanceRecord:
    id: ProvenanceId
    subject_ref: TraceRef
    kind: ProvenanceKind
    premise_refs: tuple[TraceRef, ...] = ()
    derivation_rule: str | None = None
    source_namespace: str | None = None

    def __post_init__(self) -> None:
        _required(str(self.id), "ProvenanceRecord.id")
        if self.kind is ProvenanceKind.DIRECT and self.premise_refs:
            raise ValueError("direct provenance cannot declare premise_refs")
        if self.kind is ProvenanceKind.DERIVED:
            if not self.premise_refs:
                raise ValueError("derived provenance requires premise_refs")
            if self.derivation_rule is None or not self.derivation_rule.strip():
                raise ValueError("derived provenance requires derivation_rule")


@dataclass(frozen=True)
class ProofClaim:
    id: ProofClaimId
    kind: Literal["satisfiability"]
    quantifier: ProofQuantifier
    evaluation_domain_ref: EvaluationDomainId
    status_claim: ProofStatus
    premise_refs: tuple[ConstraintId, ...]
    branch_ref: RuntimeContextId | None = None
    claimed_core_refs: tuple[ConstraintId, ...] = ()
    subset_minimal_claim: bool = False

    def __post_init__(self) -> None:
        _required(str(self.id), "ProofClaim.id")
        _required(self.kind, "ProofClaim.kind")
        if not self.premise_refs:
            raise ValueError("ProofClaim.premise_refs must not be empty")
        if self.quantifier is ProofQuantifier.BRANCH and self.branch_ref is None:
            raise ValueError("branch proofs require branch_ref")
        if self.quantifier is not ProofQuantifier.BRANCH and self.branch_ref is not None:
            raise ValueError("only branch proofs may set branch_ref")
        if self.subset_minimal_claim and self.status_claim is not ProofStatus.UNSAT:
            raise ValueError("subset_minimal_claim is only valid for an UNSAT claim")
        if self.subset_minimal_claim and not self.claimed_core_refs:
            raise ValueError("subset_minimal_claim requires claimed_core_refs")
        if len(set(self.premise_refs)) != len(self.premise_refs):
            raise ValueError("ProofClaim.premise_refs must be unique")
        if len(set(self.claimed_core_refs)) != len(self.claimed_core_refs):
            raise ValueError("ProofClaim.claimed_core_refs must be unique")


@dataclass(frozen=True)
class Trace:
    schema: str
    resolver_name: str
    resolver_version: str | None
    resolver_commit: str | None
    trace_scope: TraceScope
    runtime_contexts: tuple[RuntimeContext, ...]
    evaluation_domain: EvaluationDomain
    resolution_policy: ResolutionPolicy
    candidate_domains: tuple[CandidateDomain, ...]
    requirements: tuple[Requirement, ...]
    candidates: tuple[Candidate, ...]
    artifacts: tuple[Artifact, ...]
    dependencies: tuple[DependencyEdge, ...]
    rejections: tuple[RejectionObservation, ...]
    incompatibilities: tuple[IncompatibilityObservation, ...]
    semantic_constraints: tuple[SemanticConstraint, ...]
    evidence_state: EvidenceState
    provenance: tuple[ProvenanceRecord, ...]
    proof_claim: ProofClaim

    def __post_init__(self) -> None:
        _required(self.schema, "Trace.schema")
        _required(self.resolver_name, "Trace.resolver_name")
        if not self.runtime_contexts:
            raise ValueError("Trace.runtime_contexts must not be empty")
