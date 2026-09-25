from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import unittest

from resolvewhy.model import (
    Artifact,
    ArtifactSelectionStatus,
    Candidate,
    CandidateCoverage,
    CandidateDomain,
    CandidateDomainScope,
    CandidateKind,
    CoverageAttestation,
    CoverageAttestationKind,
    CoverageStatus,
    DependencyEdge,
    EvaluationDomain,
    EvaluationDomainKind,
    EvidenceObservation,
    EvidenceState,
    EvidenceStateKind,
    IncompatibilityObservation,
    MarkerAtom,
    MarkerExpression,
    ProofClaim,
    ProofQuantifier,
    ProofStatus,
    ProvenanceKind,
    ProvenanceRecord,
    ReferenceKind,
    RejectionObservation,
    Requirement,
    ResolutionPolicy,
    RuntimeContext,
    SemanticConstraint,
    SemanticConstraintKind,
    SemanticLiteral,
    Trace,
    TraceRef,
    TraceScope,
    VerificationStatus,
    VersionConstraint,
)
from resolvewhy.trace import deserialize_trace, serialize_trace
from resolvewhy.verification import verify, verify_serialized


def _ctx(
    name: str = "py311-linux",
    *,
    python_version: str = "3.11",
    python_full_version: str = "3.11.9",
    os: str = "linux",
    architecture: str = "x86_64",
) -> RuntimeContext:
    return RuntimeContext(
        id=f"env:{name}",
        python_implementation="CPython",
        python_version=python_version,
        os=os,
        architecture=architecture,
        marker_values=(
            ("platform_machine", architecture),
            ("python_full_version", python_full_version),
            ("python_version", python_version),
            ("sys_platform", os),
        ),
    )


def _policy(mode: str = "disallow") -> ResolutionPolicy:
    return ResolutionPolicy(
        id="policy:test",
        prerelease_mode=mode,
        universal_strategy="single",
    )


def _candidate(
    package: str,
    version: str | None,
    suffix: str = "1",
    *,
    source: str = "index:test",
) -> Candidate:
    return Candidate(
        id=f"cand:{package}:{suffix}",
        package=package,
        version=version,
        kind=CandidateKind.REGISTRY,
        source_ref=source,
    )


def _req(
    package: str,
    operator: str,
    version: str,
    suffix: str = "root",
) -> Requirement:
    return Requirement(
        id=f"req:{package}:{suffix}",
        package=package,
        constraint=VersionConstraint(operator, version),
    )


def _domain(
    package: str,
    environment: RuntimeContext,
    candidates: tuple[Candidate, ...],
    *,
    status: CoverageStatus = CoverageStatus.COMPLETE,
    evidence_id: str | None = None,
) -> CandidateDomain:
    evidence_id = evidence_id or f"obs:domain:{package}:{environment.id}"
    attestation = (
        CoverageAttestation(
            CoverageAttestationKind.AUTHORITATIVE_FINITE_DOMAIN,
            (TraceRef(ReferenceKind.EVIDENCE, evidence_id),),
        )
        if status is CoverageStatus.COMPLETE
        else None
    )
    return CandidateDomain(
        id=f"domain:{package}:{environment.id}",
        identifier=package,
        requirement_refs=(),
        candidate_refs=tuple(candidate.id for candidate in candidates),
        scope=CandidateDomainScope(sources=("index:test",)),
        runtime_context_ref=environment.id,
        resolution_policy_ref="policy:test",
        coverage=CandidateCoverage(status=status, attestation=attestation),
    )


def _constraint(
    cid: str,
    kind: SemanticConstraintKind,
    literals: tuple[SemanticLiteral, ...],
    source: TraceRef,
    evidence_id: str,
) -> SemanticConstraint:
    return SemanticConstraint(
        id=cid,
        kind=kind,
        literals=literals,
        source_refs=(source, TraceRef(ReferenceKind.EVIDENCE, evidence_id)),
    )


def _trace(
    *,
    contexts: tuple[RuntimeContext, ...] = (),
    requirements: tuple[Requirement, ...] = (),
    candidates: tuple[Candidate, ...] = (),
    domains: tuple[CandidateDomain, ...] = (),
    constraints: tuple[SemanticConstraint, ...] = (),
    artifacts: tuple[Artifact, ...] = (),
    dependencies: tuple[DependencyEdge, ...] = (),
    claim: ProofClaim | None = None,
    policy: ResolutionPolicy | None = None,
    evidence_overall: EvidenceStateKind = EvidenceStateKind.KNOWN_FACT,
    evidence_states: dict[str, EvidenceStateKind] | None = None,
    provenances: tuple[ProvenanceRecord, ...] | None = None,
    trace_scope: TraceScope = TraceScope.SINGLE_ENVIRONMENT,
    evaluation_domain: EvaluationDomain | None = None,
    rejections: tuple[RejectionObservation, ...] = (),
    incompatibilities: tuple[IncompatibilityObservation, ...] = (),
) -> Trace:
    contexts = contexts or (_ctx(),)
    policy = policy or _policy()
    evaluation_domain = evaluation_domain or EvaluationDomain(
        id="eval:test",
        kind=(
            EvaluationDomainKind.SINGLETON_ENVIRONMENT
            if len(contexts) == 1
            else EvaluationDomainKind.FINITE_ENVIRONMENT_SET
        ),
        environment_refs=tuple(context.id for context in contexts),
    )
    evidence_states = evidence_states or {}
    observations: list[EvidenceObservation] = []
    for domain in domains:
        evidence_id = f"obs:domain:{domain.identifier}:{domain.runtime_context_ref}"
        if domain.coverage.attestation is not None:
            evidence_id = str(domain.coverage.attestation.evidence_refs[0].id)
            observations.append(
                EvidenceObservation(
                    id=evidence_id,
                    kind="candidate-domain",
                    state=evidence_states.get(evidence_id, EvidenceStateKind.KNOWN_FACT),
                    supports_refs=(TraceRef(ReferenceKind.CANDIDATE_DOMAIN, str(domain.id)),),
                )
            )
    for constraint in constraints:
        evidence_refs = [
            ref for ref in constraint.source_refs
            if ref.kind is ReferenceKind.EVIDENCE
        ]
        for ref in evidence_refs:
            observations.append(
                EvidenceObservation(
                    id=str(ref.id),
                    kind="constraint-evidence",
                    state=evidence_states.get(str(ref.id), EvidenceStateKind.KNOWN_FACT),
                    supports_refs=(TraceRef(ReferenceKind.CONSTRAINT, str(constraint.id)),),
                )
            )
    observations_by_id = {}
    for item in observations:
        observations_by_id[str(item.id)] = item
    observations = list(observations_by_id.values())

    if provenances is None:
        provenances = tuple(
            ProvenanceRecord(
                id=f"prov:{constraint.id}",
                subject_ref=TraceRef(ReferenceKind.CONSTRAINT, str(constraint.id)),
                kind=ProvenanceKind.DIRECT,
            )
            for constraint in constraints
        )

    if claim is None:
        premise_refs = tuple(str(constraint.id) for constraint in constraints)
        claim = ProofClaim(
            id="claim:test",
            kind="satisfiability",
            quantifier=(
                ProofQuantifier.EXISTENTIAL
                if len(contexts) == 1
                else ProofQuantifier.UNIVERSAL
            ),
            evaluation_domain_ref=evaluation_domain.id,
            status_claim=ProofStatus.SAT,
            premise_refs=premise_refs,
        )

    return Trace(
        schema="resolvewhy-trace/1.0",
        resolver_name="test-resolver",
        resolver_version="1.0",
        resolver_commit=None,
        trace_scope=trace_scope,
        runtime_contexts=contexts,
        evaluation_domain=evaluation_domain,
        resolution_policy=policy,
        candidate_domains=domains,
        requirements=requirements,
        candidates=candidates,
        artifacts=artifacts,
        dependencies=dependencies,
        rejections=rejections,
        incompatibilities=incompatibilities,
        semantic_constraints=constraints,
        evidence_state=EvidenceState(
            overall=evidence_overall,
            observations=tuple(observations),
        ),
        provenance=provenances,
        proof_claim=claim,
    )


class ProductionVerifierTests(unittest.TestCase):
    def test_simple_sat_trace(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg",
            SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(
                kind=SemanticConstraintKind.REQUIREMENT,
                package="pkg",
                candidate_ref=cand.id,
                operator="==",
                value="1.0",
            ),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id),
            "obs:c:pkg",
        )
        trace = _trace(
            contexts=(ctx,),
            requirements=(req,),
            candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),),
            constraints=(c,),
        )
        result = verify(trace)
        self.assertEqual(result.status, VerificationStatus.VERIFIED_SAT)
        self.assertTrue(result.independently_verified)

    def test_sat_transitive_graph(self):
        ctx = _ctx()
        a = _candidate("a", "1.0")
        b = _candidate("b", "2.0")
        req = _req("a", "==", "1.0")
        dep_req = _req("b", "==", "2.0", "dep")
        edge = DependencyEdge(
            id="dep:a-b",
            parent_candidate_ref=a.id,
            requirement_ref=dep_req.id,
        )
        c_root = _constraint(
            "c:a",
            SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(
                kind=SemanticConstraintKind.REQUIREMENT,
                package="a",
                candidate_ref=a.id,
                operator="==",
                value="1.0",
            ),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id),
            "obs:c:a",
        )
        c_dep = _constraint(
            "c:a-b",
            SemanticConstraintKind.DEPENDENCY,
            (SemanticLiteral(
                kind=SemanticConstraintKind.DEPENDENCY,
                package="b",
                candidate_ref=a.id,
                operator="==",
                value="2.0",
            ),),
            TraceRef(ReferenceKind.DEPENDENCY, edge.id),
            "obs:c:a-b",
        )
        trace = _trace(
            contexts=(ctx,),
            requirements=(req, dep_req),
            candidates=(a, b),
            domains=(
                _domain("a", ctx, (a,)),
                _domain("b", ctx, (b,)),
            ),
            dependencies=(edge,),
            constraints=(c_root, c_dep),
        )
        result = verify(trace)
        self.assertEqual(result.status, VerificationStatus.VERIFIED_SAT)

    def test_sat_conditional_dependency(self):
        ctx = _ctx(os="linux")
        a = _candidate("a", "1.0")
        req = _req("a", "==", "1.0")
        edge = DependencyEdge(
            id="dep:a-b",
            parent_candidate_ref=a.id,
            requirement_ref="req:b:dep",
            activation=MarkerExpression(
                kind="atom",
                atom=MarkerAtom("sys_platform", "==", "win32"),
            ),
        )
        dep_req = _req("b", "==", "1.0", "dep")
        c_root = _constraint(
            "c:a",
            SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(
                kind=SemanticConstraintKind.REQUIREMENT,
                package="a",
                candidate_ref=a.id,
                operator="==",
                value="1.0",
            ),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id),
            "obs:c:a",
        )
        c_dep = _constraint(
            "c:a-b",
            SemanticConstraintKind.DEPENDENCY,
            (SemanticLiteral(
                kind=SemanticConstraintKind.DEPENDENCY,
                package="b",
                candidate_ref=a.id,
                operator="==",
                value="1.0",
                activation=edge.activation,
            ),),
            TraceRef(ReferenceKind.DEPENDENCY, edge.id),
            "obs:c:a-b",
        )
        trace = _trace(
            contexts=(ctx,),
            requirements=(req, dep_req),
            candidates=(a,),
            domains=(
                _domain("a", ctx, (a,)),
                _domain("b", ctx, ()),
            ),
            dependencies=(edge,),
            constraints=(c_root, c_dep),
        )
        self.assertEqual(verify(trace).status, VerificationStatus.VERIFIED_SAT)

    def test_sat_source_distinct_candidates(self):
        ctx = _ctx()
        a = _candidate("pkg", "1.0", "A", source="index:A")
        b = _candidate("pkg", "1.0", "B", source="index:B")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg",
            SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(
                kind=SemanticConstraintKind.REQUIREMENT,
                package="pkg",
                operator="==",
                value="1.0",
            ),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id),
            "obs:c:pkg",
        )
        domain = replace(
            _domain("pkg", ctx, (a, b)),
            scope=CandidateDomainScope(sources=("index:A", "index:B")),
        )
        self.assertEqual(
            verify(_trace(
                contexts=(ctx,),
                requirements=(req,),
                candidates=(a, b),
                domains=(domain,),
                constraints=(c,),
            )).status,
            VerificationStatus.VERIFIED_SAT,
        )

    def test_sat_compatible_artifact(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        art = Artifact(
            id="art:pkg",
            candidate_ref=cand.id,
            compatible=True,
            selection_status=ArtifactSelectionStatus.AVAILABLE,
        )
        c_root = _constraint(
            "c:root",
            SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(
                kind=SemanticConstraintKind.REQUIREMENT,
                package="pkg",
                operator="==",
                value="1.0",
            ),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id),
            "obs:c:root",
        )
        c_art = _constraint(
            "c:artifact",
            SemanticConstraintKind.ARTIFACT_COMPATIBILITY,
            (SemanticLiteral(
                kind=SemanticConstraintKind.ARTIFACT_COMPATIBILITY,
                candidate_ref=cand.id,
                artifact_ref=art.id,
            ),),
            TraceRef(ReferenceKind.ARTIFACT, art.id),
            "obs:c:artifact",
        )
        self.assertEqual(
            verify(_trace(
                contexts=(ctx,),
                requirements=(req,),
                candidates=(cand,),
                domains=(_domain("pkg", ctx, (cand,)),),
                artifacts=(art,),
                constraints=(c_root, c_art),
            )).status,
            VerificationStatus.VERIFIED_SAT,
        )

    def test_unsat_direct_version_contradiction(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        r1 = _req("pkg", ">=", "2.0", "ge")
        r2 = _req("pkg", "<", "2.0", "lt")
        c1 = _constraint(
            "c:ge", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator=">=", value="2.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, r1.id), "obs:c:ge",
        )
        c2 = _constraint(
            "c:lt", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="<", value="2.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, r2.id), "obs:c:lt",
        )
        result = verify(_trace(
            contexts=(ctx,), requirements=(r1, r2), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c1, c2),
        ))
        self.assertEqual(result.status, VerificationStatus.VERIFIED_UNSAT)

    def test_unsat_transitive_contradiction(self):
        ctx = _ctx()
        a = _candidate("a", "1.0")
        b = _candidate("b", "1.0")
        c1 = _candidate("c", "1.0", "one")
        c2 = _candidate("c", "2.0", "two")
        ra = _req("a", "==", "1.0")
        rb = _req("b", "==", "1.0")
        rca = _req("c", "<", "2.0", "a")
        rcb = _req("c", ">=", "2.0", "b")
        da = DependencyEdge(id="dep:a-c", parent_candidate_ref=a.id, requirement_ref=rca.id)
        db = DependencyEdge(id="dep:b-c", parent_candidate_ref=b.id, requirement_ref=rcb.id)
        root_a = _constraint(
            "c:a", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="a", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, ra.id), "obs:c:a",
        )
        root_b = _constraint(
            "c:b", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="b", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, rb.id), "obs:c:b",
        )
        dep_a = _constraint(
            "c:a-c", SemanticConstraintKind.DEPENDENCY,
            (SemanticLiteral(kind=SemanticConstraintKind.DEPENDENCY, package="c", candidate_ref=a.id, operator="<", value="2.0"),),
            TraceRef(ReferenceKind.DEPENDENCY, da.id), "obs:c:a-c",
        )
        dep_b = _constraint(
            "c:b-c", SemanticConstraintKind.DEPENDENCY,
            (SemanticLiteral(kind=SemanticConstraintKind.DEPENDENCY, package="c", candidate_ref=b.id, operator=">=", value="2.0"),),
            TraceRef(ReferenceKind.DEPENDENCY, db.id), "obs:c:b-c",
        )
        result = verify(_trace(
            contexts=(ctx,),
            requirements=(ra, rb, rca, rcb),
            candidates=(a, b, c1, c2),
            domains=(
                _domain("a", ctx, (a,)),
                _domain("b", ctx, (b,)),
                _domain("c", ctx, (c1, c2)),
            ),
            dependencies=(da, db),
            constraints=(root_a, root_b, dep_a, dep_b),
        ))
        self.assertEqual(result.status, VerificationStatus.VERIFIED_UNSAT)

    def test_unsat_requires_python(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c_req = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        c_py = _constraint(
            "c:python", SemanticConstraintKind.REQUIRES_PYTHON,
            (SemanticLiteral(
                kind=SemanticConstraintKind.REQUIRES_PYTHON,
                package="<Python>", candidate_ref=cand.id, runtime_context_ref=ctx.id,
                operator=">=", value="4.0",
            ),),
            TraceRef(ReferenceKind.CANDIDATE, cand.id), "obs:c:python",
        )
        self.assertEqual(
            verify(_trace(
                contexts=(ctx,), requirements=(req,), candidates=(cand,),
                domains=(_domain("pkg", ctx, (cand,)),),
                constraints=(c_req, c_py),
            )).status,
            VerificationStatus.VERIFIED_UNSAT,
        )

    def test_unsat_incompatible_artifact(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        art = Artifact(
            id="art:pkg",
            candidate_ref=cand.id,
            compatible=False,
            selection_status=ArtifactSelectionStatus.INCOMPATIBLE,
        )
        c_req = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        c_art = _constraint(
            "c:artifact", SemanticConstraintKind.ARTIFACT_COMPATIBILITY,
            (SemanticLiteral(kind=SemanticConstraintKind.ARTIFACT_COMPATIBILITY, artifact_ref=art.id, candidate_ref=cand.id),),
            TraceRef(ReferenceKind.ARTIFACT, art.id), "obs:c:artifact",
        )
        self.assertEqual(
            verify(_trace(
                contexts=(ctx,), requirements=(req,), candidates=(cand,),
                domains=(_domain("pkg", ctx, (cand,)),),
                artifacts=(art,), constraints=(c_req, c_art),
            )).status,
            VerificationStatus.VERIFIED_UNSAT,
        )

    def _multi_env_fixture(self, quantifier: ProofQuantifier) -> Trace:
        linux = _ctx("py312", python_version="3.12", python_full_version="3.12.0")
        old = _ctx("py39", python_version="3.9", python_full_version="3.9.18")
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c_req = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        c_py = _constraint(
            "c:python", SemanticConstraintKind.REQUIRES_PYTHON,
            (SemanticLiteral(
                kind=SemanticConstraintKind.REQUIRES_PYTHON,
                package="<Python>", candidate_ref=cand.id, runtime_context_ref=old.id,
                operator=">=", value="3.10",
            ),),
            TraceRef(ReferenceKind.CANDIDATE, cand.id), "obs:c:python",
        )
        domain = EvaluationDomain(
            id="eval:two",
            kind=EvaluationDomainKind.FINITE_ENVIRONMENT_SET,
            environment_refs=(linux.id, old.id),
        )
        claim = ProofClaim(
            id="claim:multi",
            kind="satisfiability",
            quantifier=quantifier,
            evaluation_domain_ref=domain.id,
            status_claim=ProofStatus.UNSAT,
            premise_refs=(c_req.id, c_py.id),
            branch_ref=old.id if quantifier is ProofQuantifier.BRANCH else None,
        )
        return _trace(
            contexts=(linux, old),
            requirements=(req,),
            candidates=(cand,),
            domains=(
                _domain("pkg", linux, (cand,)),
                _domain("pkg", old, (cand,)),
            ),
            constraints=(c_req, c_py),
            claim=claim,
            trace_scope=TraceScope.MULTI_ENVIRONMENT,
            evaluation_domain=domain,
        )

    def test_unsat_universal_finite_domain(self):
        result = verify(self._multi_env_fixture(ProofQuantifier.UNIVERSAL))
        self.assertEqual(result.status, VerificationStatus.VERIFIED_UNSAT)
        self.assertEqual(result.branch_results, ("SAT", "UNSAT"))

    def test_unsat_branch_contradiction(self):
        trace = self._multi_env_fixture(ProofQuantifier.BRANCH)
        trace = replace(
            trace,
            proof_claim=replace(trace.proof_claim, branch_ref="env:py39"),
        )
        self.assertEqual(verify(trace).status, VerificationStatus.VERIFIED_UNSAT)

    def test_insufficient_unknown_candidate_coverage(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        result = verify(_trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,), status=CoverageStatus.UNKNOWN),),
            constraints=(c,),
        ))
        self.assertEqual(result.status, VerificationStatus.INSUFFICIENT_EVIDENCE)

    def test_insufficient_partial_source_discovery(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        domain = _domain("pkg", ctx, (cand,), status=CoverageStatus.PARTIAL)
        domain = replace(domain, scope=CandidateDomainScope(
            sources=("index:test",), queries=("partial-query",)
        ))
        result = verify(_trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(domain,), constraints=(c,),
        ))
        self.assertEqual(result.status, VerificationStatus.INSUFFICIENT_EVIDENCE)

    def test_insufficient_missing_candidate_domain(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        trace = _trace(contexts=(ctx,), requirements=(req,), candidates=(cand,), constraints=(c,))
        self.assertEqual(verify(trace).status, VerificationStatus.INSUFFICIENT_EVIDENCE)

    def test_insufficient_unsupported_marker(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        marker = MarkerExpression(
            kind="atom",
            atom=MarkerAtom("dependency_groups", "==", "dev"),
        )
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(
                kind=SemanticConstraintKind.REQUIREMENT, package="pkg",
                operator="==", value="1.0", activation=marker,
            ),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        trace = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,),
        )
        self.assertEqual(verify(trace).status, VerificationStatus.INSUFFICIENT_EVIDENCE)

    def test_insufficient_unknown_artifact_compatibility(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        art = Artifact(
            id="art:pkg",
            candidate_ref=cand.id,
            compatible=None,
            selection_status=ArtifactSelectionStatus.UNKNOWN,
        )
        c_req = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        c_art = _constraint(
            "c:artifact", SemanticConstraintKind.ARTIFACT_COMPATIBILITY,
            (SemanticLiteral(kind=SemanticConstraintKind.ARTIFACT_COMPATIBILITY, artifact_ref=art.id, candidate_ref=cand.id),),
            TraceRef(ReferenceKind.ARTIFACT, art.id), "obs:c:artifact",
        )
        self.assertEqual(
            verify(_trace(
                contexts=(ctx,), requirements=(req,), candidates=(cand,),
                domains=(_domain("pkg", ctx, (cand,)),), artifacts=(art,),
                constraints=(c_req, c_art),
            )).status,
            VerificationStatus.INSUFFICIENT_EVIDENCE,
        )

    def test_insufficient_unsupported_candidate_admissibility(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:admission", SemanticConstraintKind.CANDIDATE_ADMISSIBILITY,
            (SemanticLiteral(kind=SemanticConstraintKind.CANDIDATE_ADMISSIBILITY, candidate_ref=cand.id),),
            TraceRef(ReferenceKind.CANDIDATE, cand.id), "obs:c:admission",
        )
        trace = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,),
        )
        self.assertEqual(verify(trace).status, VerificationStatus.INSUFFICIENT_EVIDENCE)

    def test_insufficient_missing_proof_evidence(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        trace = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,),
            evidence_states={"obs:c:pkg": EvidenceStateKind.INCOMPLETE},
        )
        self.assertEqual(verify(trace).status, VerificationStatus.INSUFFICIENT_EVIDENCE)

    def test_insufficient_unsupported_policy(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        policy = replace(_policy(), source_selection=("index:test",))
        self.assertEqual(
            verify(_trace(
                contexts=(ctx,), requirements=(req,), candidates=(cand,),
                domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,), policy=policy,
            )).status,
            VerificationStatus.INSUFFICIENT_EVIDENCE,
        )

    def test_invalid_malformed_reference(self):
        trace = deserialize_trace(Path("tests/fixtures/production_trace.json").read_bytes())
        artifact = Artifact(id="art:broken", candidate_ref="missing")
        broken = replace(trace, artifacts=(artifact,))
        self.assertEqual(verify(broken).status, VerificationStatus.INVALID_TRACE)

    def test_invalid_duplicate_ids(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        base = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,),
        )
        self.assertEqual(
            verify(replace(base, candidates=(cand, cand))).status,
            VerificationStatus.INVALID_TRACE,
        )

    def test_invalid_proof_premise(self):
        trace = deserialize_trace(Path("tests/fixtures/production_trace.json").read_bytes())
        claim = replace(trace.proof_claim, premise_refs=("missing-constraint",))
        self.assertEqual(
            verify(replace(trace, proof_claim=claim)).status,
            VerificationStatus.INVALID_TRACE,
        )

    def test_invalid_proof_domain_binding(self):
        trace = deserialize_trace(Path("tests/fixtures/production_trace.json").read_bytes())
        claim = replace(trace.proof_claim, evaluation_domain_ref="missing-domain")
        self.assertEqual(
            verify(replace(trace, proof_claim=claim)).status,
            VerificationStatus.INVALID_TRACE,
        )

    def test_invalid_branch_binding(self):
        trace = self._multi_env_fixture(ProofQuantifier.BRANCH)
        claim = replace(trace.proof_claim, branch_ref="env:missing")
        self.assertEqual(verify(replace(trace, proof_claim=claim)).status, VerificationStatus.INVALID_TRACE)

    def test_invalid_provenance_cycle(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        p1 = ProvenanceRecord(
            id="prov:p1",
            subject_ref=TraceRef(ReferenceKind.PROVENANCE, "prov:p1"),
            kind=ProvenanceKind.DERIVED,
            premise_refs=(TraceRef(ReferenceKind.PROVENANCE, "prov:p2"),),
            derivation_rule="test",
        )
        p2 = ProvenanceRecord(
            id="prov:p2",
            subject_ref=TraceRef(ReferenceKind.PROVENANCE, "prov:p2"),
            kind=ProvenanceKind.DERIVED,
            premise_refs=(TraceRef(ReferenceKind.PROVENANCE, "prov:p1"),),
            derivation_rule="test",
        )
        trace = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,),
            provenances=(
                ProvenanceRecord(
                    id="prov:c:pkg",
                    subject_ref=TraceRef(ReferenceKind.CONSTRAINT, c.id),
                    kind=ProvenanceKind.DIRECT,
                ),
                p1, p2,
            ),
        )
        self.assertEqual(verify(trace).status, VerificationStatus.INVALID_TRACE)

    def test_native_unsat_claim_is_non_authoritative(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        trace = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,),
            claim=ProofClaim(
                id="claim:native-unsat",
                kind="satisfiability",
                quantifier=ProofQuantifier.EXISTENTIAL,
                evaluation_domain_ref="eval:test",
                status_claim=ProofStatus.UNSAT,
                premise_refs=(c.id,),
            ),
            incompatibilities=(IncompatibilityObservation(
                id="inc:resolvelib:1",
                semantics="ResolutionImpossible",
                resolver_namespace="resolvelib",
            ),),
        )
        result = verify(trace)
        self.assertEqual(result.status, VerificationStatus.VERIFIED_SAT)
        self.assertIn("claim_mismatch", result.reasons)

    def test_native_sat_claim_is_non_authoritative(self):
        trace = self._unsat_three_constraints_fixture()
        trace = replace(
            trace,
            proof_claim=replace(trace.proof_claim, status_claim=ProofStatus.SAT),
        )
        result = verify(trace)
        self.assertEqual(result.status, VerificationStatus.VERIFIED_UNSAT)
        self.assertIn("claim_mismatch", result.reasons)

    def test_resolver_error_text_is_not_proof(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        rejection = RejectionObservation(
            id="reject:1",
            target_ref=TraceRef(ReferenceKind.CANDIDATE, cand.id),
            reason_kind="ResolutionImpossible",
            source_layer="resolver",
            evidence_status=EvidenceStateKind.REJECTED_CANDIDATE,
        )
        trace = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,),
            rejections=(rejection,),
        )
        self.assertEqual(verify(trace).status, VerificationStatus.VERIFIED_SAT)

    def test_empty_candidate_domain_without_completeness_is_insufficient(self):
        ctx = _ctx()
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        domain = _domain("pkg", ctx, (), status=CoverageStatus.UNKNOWN)
        result = verify(_trace(
            contexts=(ctx,), requirements=(req,), domains=(domain,), constraints=(c,),
        ))
        self.assertEqual(result.status, VerificationStatus.INSUFFICIENT_EVIDENCE)

    def test_fabricated_completeness_is_invalid(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        domain = _domain("pkg", ctx, (cand,))
        bad_evidence = EvidenceObservation(
            id="obs:domain:pkg:env:py311-linux",
            kind="candidate-domain",
            state=EvidenceStateKind.KNOWN_FACT,
            supports_refs=(TraceRef(ReferenceKind.CANDIDATE, cand.id),),
        )
        trace = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(domain,), constraints=(c,),
        )
        trace = replace(
            trace,
            evidence_state=replace(
                trace.evidence_state,
                observations=tuple(
                    bad_evidence if obs.id == bad_evidence.id else obs
                    for obs in trace.evidence_state.observations
                ),
            ),
        )
        self.assertEqual(verify(trace).status, VerificationStatus.INVALID_TRACE)

    def test_altered_evaluation_domain_changes_result(self):
        trace = self._multi_env_fixture(ProofQuantifier.UNIVERSAL)
        single = EvaluationDomain(
            id="eval:single",
            kind=EvaluationDomainKind.SINGLETON_ENVIRONMENT,
            environment_refs=("env:py312",),
        )
        claim = replace(trace.proof_claim, evaluation_domain_ref=single.id)
        single_trace = replace(trace, evaluation_domain=single, proof_claim=claim)
        result = verify(single_trace)
        self.assertEqual(result.status, VerificationStatus.VERIFIED_SAT)

    def test_altered_quantifier_changes_result(self):
        universal = verify(self._multi_env_fixture(ProofQuantifier.UNIVERSAL))
        existential = verify(self._multi_env_fixture(ProofQuantifier.EXISTENTIAL))
        self.assertEqual(universal.status, VerificationStatus.VERIFIED_UNSAT)
        self.assertEqual(existential.status, VerificationStatus.VERIFIED_SAT)

    def test_altered_proof_premises_changes_result(self):
        trace = self._multi_env_fixture(ProofQuantifier.UNIVERSAL)
        reduced = replace(
            trace,
            proof_claim=replace(
                trace.proof_claim,
                premise_refs=("c:pkg",),
                status_claim=ProofStatus.SAT,
            ),
        )
        self.assertEqual(verify(reduced).status, VerificationStatus.VERIFIED_SAT)

    def test_altered_candidate_identity_is_invalid(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(
                kind=SemanticConstraintKind.REQUIREMENT, package="pkg",
                candidate_ref="missing", operator="==", value="1.0",
            ),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        trace = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,),
        )
        self.assertEqual(verify(trace).status, VerificationStatus.INVALID_TRACE)

    def test_altered_artifact_feasibility_changes_result(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        art = Artifact(
            id="art:pkg",
            candidate_ref=cand.id,
            compatible=True,
            selection_status=ArtifactSelectionStatus.AVAILABLE,
        )
        c_req = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        c_art = _constraint(
            "c:artifact", SemanticConstraintKind.ARTIFACT_COMPATIBILITY,
            (SemanticLiteral(kind=SemanticConstraintKind.ARTIFACT_COMPATIBILITY, artifact_ref=art.id, candidate_ref=cand.id),),
            TraceRef(ReferenceKind.ARTIFACT, art.id), "obs:c:artifact",
        )
        sat = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), artifacts=(art,),
            constraints=(c_req, c_art),
        )
        unsat = replace(sat, artifacts=(replace(art, compatible=False, selection_status=ArtifactSelectionStatus.INCOMPATIBLE),))
        self.assertEqual(verify(sat).status, VerificationStatus.VERIFIED_SAT)
        self.assertEqual(verify(unsat).status, VerificationStatus.VERIFIED_UNSAT)

    def test_erased_activation_changes_result(self):
        ctx = _ctx(os="linux")
        a = _candidate("a", "1.0")
        req = _req("a", "==", "1.0")
        dep_req = _req("b", "==", "1.0", "dep")
        edge = DependencyEdge(
            id="dep:a-b", parent_candidate_ref=a.id, requirement_ref=dep_req.id,
            activation=MarkerExpression(kind="atom", atom=MarkerAtom("sys_platform", "==", "win32")),
        )
        c_root = _constraint(
            "c:a", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="a", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:a",
        )
        c_dep = _constraint(
            "c:a-b", SemanticConstraintKind.DEPENDENCY,
            (SemanticLiteral(kind=SemanticConstraintKind.DEPENDENCY, package="b", candidate_ref=a.id, operator="==", value="1.0", activation=edge.activation),),
            TraceRef(ReferenceKind.DEPENDENCY, edge.id), "obs:c:a-b",
        )
        sat = _trace(
            contexts=(ctx,), requirements=(req, dep_req), candidates=(a,),
            domains=(_domain("a", ctx, (a,)), _domain("b", ctx, ())),
            dependencies=(edge,), constraints=(c_root, c_dep),
        )
        erased = replace(
            sat,
            dependencies=(replace(edge, activation=None),),
            semantic_constraints=(
                c_root,
                replace(c_dep, literals=(replace(c_dep.literals[0], activation=None),)),
            ),
        )
        self.assertEqual(verify(sat).status, VerificationStatus.VERIFIED_SAT)
        self.assertEqual(verify(erased).status, VerificationStatus.VERIFIED_UNSAT)

    def test_altered_prerelease_policy_changes_result(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0rc1")
        req = _req("pkg", "<", "2.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="<", value="2.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        disallow = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,), policy=_policy("disallow"),
        )
        allow = replace(disallow, resolution_policy=_policy("allow"))
        self.assertEqual(verify(disallow).status, VerificationStatus.VERIFIED_UNSAT)
        self.assertEqual(verify(allow).status, VerificationStatus.VERIFIED_SAT)

    def test_compound_constraints_are_conjunctive(self):
        ctx = _ctx()
        c1 = _candidate("pkg", "2.0")
        c2 = _candidate("pkg", "4.0", "2")
        req = _req("pkg", ">=", "1.0")
        c = _constraint(
            "c:compound", SemanticConstraintKind.REQUIREMENT,
            (
                SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator=">=", value="1.0"),
                SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="<", value="3.0"),
            ),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:compound",
        )
        result = verify(_trace(
            contexts=(ctx,), requirements=(req,), candidates=(c1, c2),
            domains=(_domain("pkg", ctx, (c1, c2)),), constraints=(c,),
        ))
        self.assertEqual(result.status, VerificationStatus.VERIFIED_SAT)

    def test_subset_minimality_is_independently_verified(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        r1 = _req("pkg", ">=", "2.0", "ge")
        r2 = _req("pkg", "<", "2.0", "lt")
        c1 = _constraint(
            "c:ge", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator=">=", value="2.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, r1.id), "obs:c:ge",
        )
        c2 = _constraint(
            "c:lt", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="<", value="2.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, r2.id), "obs:c:lt",
        )
        claim = ProofClaim(
            id="claim:min",
            kind="satisfiability",
            quantifier=ProofQuantifier.EXISTENTIAL,
            evaluation_domain_ref="eval:test",
            status_claim=ProofStatus.UNSAT,
            premise_refs=(c1.id, c2.id),
            claimed_core_refs=(c1.id, c2.id),
            subset_minimal_claim=True,
        )
        result = verify(_trace(
            contexts=(ctx,), requirements=(r1, r2), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),),
            constraints=(c1, c2), claim=claim,
        ))
        self.assertEqual(result.status, VerificationStatus.VERIFIED_UNSAT)
        self.assertTrue(result.minimality_verified)

    def _unsat_three_constraints_fixture(self) -> Trace:
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        r1 = _req("pkg", ">=", "1.0", "ge")
        r2 = _req("pkg", "<", "3.0", "lt")
        r3 = _req("pkg", "<", "0.0", "bad")
        c1 = _constraint(
            "c:ge", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator=">=", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, r1.id), "obs:c:ge",
        )
        c2 = _constraint(
            "c:lt", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="<", value="3.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, r2.id), "obs:c:lt",
        )
        c3 = _constraint(
            "c:bad", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="<", value="0.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, r3.id), "obs:c:bad",
        )
        claim = ProofClaim(
            id="claim:three",
            kind="satisfiability",
            quantifier=ProofQuantifier.EXISTENTIAL,
            evaluation_domain_ref="eval:test",
            status_claim=ProofStatus.UNSAT,
            premise_refs=(c1.id, c2.id, c3.id),
        )
        return _trace(
            contexts=(ctx,), requirements=(r1, r2, r3), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c1, c2, c3), claim=claim,
        )

    def test_false_subset_minimality_claim_is_not_reported_as_verified(self):
        trace = self._unsat_three_constraints_fixture()
        bad_claim = replace(
            trace.proof_claim,
            claimed_core_refs=("c:ge", "c:lt"),
            subset_minimal_claim=True,
        )
        result = verify(replace(trace, proof_claim=bad_claim))
        self.assertEqual(result.status, VerificationStatus.VERIFIED_UNSAT)
        self.assertFalse(result.minimality_verified)
        self.assertIn("minimality_not_verified", result.reasons)

    def test_serialized_production_entrypoint(self):
        fixture = Path("tests/fixtures/production_trace.json").read_bytes()
        result = verify_serialized(fixture)
        self.assertEqual(result.status, VerificationStatus.VERIFIED_SAT)

    def test_invalid_serialized_trace(self):
        result = verify_serialized(b'{"schema":"resolvewhy-trace/research-2026"}')
        self.assertEqual(result.status, VerificationStatus.INVALID_TRACE)

    def test_deterministic_result(self):
        ctx = _ctx()
        cand = _candidate("pkg", "1.0")
        req = _req("pkg", "==", "1.0")
        c = _constraint(
            "c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg",
        )
        trace = _trace(
            contexts=(ctx,), requirements=(req,), candidates=(cand,),
            domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,),
        )
        self.assertEqual(verify(trace), verify(trace))


if __name__ == "__main__":
    unittest.main()
