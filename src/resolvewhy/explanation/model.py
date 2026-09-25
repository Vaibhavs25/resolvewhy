from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from resolvewhy.model import ProofQuantifier, VerificationStatus
class ExplanationKind(str, Enum):
    VERIFIED_UNSAT=VerificationStatus.VERIFIED_UNSAT.value
    VERIFIED_SAT=VerificationStatus.VERIFIED_SAT.value
    INSUFFICIENT_EVIDENCE=VerificationStatus.INSUFFICIENT_EVIDENCE.value
    INVALID_TRACE=VerificationStatus.INVALID_TRACE.value
@dataclass(frozen=True)
class ExplanationScope:
    quantifier: ProofQuantifier|None
    evaluation_domain_id: str|None
    runtime_context_refs: tuple[str,...]
@dataclass(frozen=True)
class ExplanationConstraint:
    id:str
    kind:str
    description:str
    source_refs:tuple[str,...]=()
@dataclass(frozen=True)
class ExplanationDependencyPath:
    id:str
    constraint_ref:str
    requirement_ref:str|None
    dependency_ref:str|None
    parent_candidate_ref:str|None
@dataclass(frozen=True)
class ExplanationCandidate:
    id:str
    package:str
    version:str|None
    source_ref:str|None
@dataclass(frozen=True)
class ExplanationArtifact:
    id:str
    candidate_ref:str
    compatible:bool|None
    selection_status:str
@dataclass(frozen=True)
class ExplanationPolicyFact:
    key:str
    value:str
@dataclass(frozen=True)
class ExplanationEvidenceFact:
    ref:str
    state:str
    kind:str
@dataclass(frozen=True)
class ExplanationCore:
    constraint_refs:tuple[str,...]
    subset_minimal:bool
@dataclass(frozen=True)
class ExplanationIssue:
    code:str
    message:str
    ref:str|None=None
@dataclass(frozen=True)
class Explanation:
    kind:ExplanationKind
    scope:ExplanationScope
    constraints:tuple[ExplanationConstraint,...]=()
    dependency_paths:tuple[ExplanationDependencyPath,...]=()
    candidates:tuple[ExplanationCandidate,...]=()
    artifacts:tuple[ExplanationArtifact,...]=()
    policy_facts:tuple[ExplanationPolicyFact,...]=()
    evidence_facts:tuple[ExplanationEvidenceFact,...]=()
    core:ExplanationCore|None=None
    issues:tuple[ExplanationIssue,...]=()
    warnings:tuple[str,...]=()
    @property
    def constraint_refs(self): return tuple(x.id for x in self.constraints)
    @property
    def dependency_path_refs(self): return tuple(x.id for x in self.dependency_paths)
    @property
    def candidate_refs(self): return tuple(x.id for x in self.candidates)