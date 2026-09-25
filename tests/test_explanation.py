from __future__ import annotations

from dataclasses import replace
import unittest

from resolvewhy.explanation import build_explanation, render_explanation
from resolvewhy.model import (
    Artifact, ArtifactSelectionStatus, Candidate, CandidateCoverage, CandidateDomain,
    CandidateDomainScope, CandidateKind, CoverageAttestation, CoverageAttestationKind,
    CoverageStatus, DependencyEdge, EvaluationDomain, EvaluationDomainKind,
    EvidenceObservation, EvidenceState, EvidenceStateKind, MarkerAtom, MarkerExpression,
    ProofClaim, ProofQuantifier, ProofStatus, ProvenanceKind, ProvenanceRecord,
    ReferenceKind, Requirement, ResolutionPolicy, RuntimeContext, SemanticConstraint,
    SemanticConstraintKind, SemanticLiteral, Trace, TraceRef, TraceScope, VerificationStatus,
    VersionConstraint,
)
from resolvewhy.solving import SemanticProblem
from resolvewhy.verification import verify
from resolvewhy.verification.result import VerificationIssue, VerificationResult


def ctx(name="py311", py="3.11", os="linux"):
    return RuntimeContext(f"env:{name}","CPython",py,os,"x86_64",
                          (("python_version",py),("sys_platform",os)))


def cand(pkg, ver, suffix="1"):
    return Candidate(f"cand:{pkg}:{suffix}",pkg,ver,CandidateKind.REGISTRY,"index:test")


def req(pkg, op, ver, suffix="root"):
    return Requirement(f"req:{pkg}:{suffix}",pkg,VersionConstraint(op,ver))


def domain(package, c, candidates, status=CoverageStatus.COMPLETE):
    eid=f"obs:domain:{package}:{c.id}"
    att=CoverageAttestation(CoverageAttestationKind.AUTHORITATIVE_FINITE_DOMAIN,(TraceRef(ReferenceKind.EVIDENCE,eid),)) if status is CoverageStatus.COMPLETE else None
    return CandidateDomain(f"domain:{package}:{c.id}",package,(),tuple(x.id for x in candidates),
                           CandidateDomainScope(sources=("index:test",)),c.id,"policy:test",
                           CandidateCoverage(status,att))


def constraint(cid, package, op, value, req_id, *, candidate_ref=None, kind=SemanticConstraintKind.REQUIREMENT,
               evidence=None, artifact_ref=None, runtime_context_ref=None, activation=None, source_kind=ReferenceKind.REQUIREMENT):
    lit=SemanticLiteral(kind,package,candidate_ref,artifact_ref,runtime_context_ref,op,value,activation)
    refs=[TraceRef(source_kind,req_id)]
    refs.append(TraceRef(ReferenceKind.EVIDENCE,evidence or f"obs:{cid}"))
    return SemanticConstraint(cid,kind,(lit,),tuple(refs))


def make_trace(*, unsat=False, incomplete=False, dependency=False, artifact=False, quantifier=ProofQuantifier.EXISTENTIAL):
    c=ctx()
    a=cand("pkg","1.0")
    b=cand("pkg","2.0","2")
    requirements=[req("pkg",">=","2.0","ge"),req("pkg","<","2.0","lt")] if unsat else [req("pkg","==","1.0")]
    constraints=[
        constraint("c:ge","pkg",">=","2.0",requirements[0].id),
        constraint("c:lt","pkg","<","2.0",requirements[1].id),
    ] if unsat else [constraint("c:pkg","pkg","==","1.0",requirements[0].id,candidate_ref=a.id)]
    deps=()
    if dependency:
        dep_req=req("child","==","1.0","dep")
        edge=DependencyEdge("dep:pkg-child",a.id,dep_req.id)
        requirements.append(dep_req)
        constraints.append(constraint("c:dep","child","==","1.0",edge.id,candidate_ref=a.id,
                                       kind=SemanticConstraintKind.DEPENDENCY,source_kind=ReferenceKind.DEPENDENCY))
        deps=(edge,)
    arts=()
    if artifact:
        art=Artifact("art:pkg",a.id,compatible=False,selection_status=ArtifactSelectionStatus.INCOMPATIBLE)
        constraints.append(constraint("c:artifact","pkg","", "",art.id,candidate_ref=a.id,
                                       kind=SemanticConstraintKind.ARTIFACT_COMPATIBILITY,
                                       source_kind=ReferenceKind.ARTIFACT,artifact_ref=art.id))
        arts=(art,)
    domains=[domain("pkg",c,((a,b) if unsat else (a,)),CoverageStatus.UNKNOWN if incomplete else CoverageStatus.COMPLETE)]
    if dependency: domains.append(domain("child",c,()))
    observations={}
    for d in domains:
        if d.coverage.attestation:
            eid=str(d.coverage.attestation.evidence_refs[0].id)
            observations[eid]=EvidenceObservation(eid,"candidate-domain",EvidenceStateKind.KNOWN_FACT,
                (TraceRef(ReferenceKind.CANDIDATE_DOMAIN,str(d.id)),))
    for q in constraints:
        for r in q.source_refs:
            if r.kind is ReferenceKind.EVIDENCE:
                observations[str(r.id)]=EvidenceObservation(str(r.id),"constraint-evidence",
                    EvidenceStateKind.INCOMPLETE if incomplete else EvidenceStateKind.KNOWN_FACT,
                    (TraceRef(ReferenceKind.CONSTRAINT,str(q.id)),))
    constraints=tuple(constraints)
    ev=EvidenceState(EvidenceStateKind.KNOWN_FACT,tuple(observations.values()))
    ed=EvaluationDomain("eval:test",EvaluationDomainKind.SINGLETON_ENVIRONMENT,(c.id,))
    claim=ProofClaim("claim:test","satisfiability",quantifier,ed.id,
        ProofStatus.UNSAT if unsat else ProofStatus.SAT,tuple(x.id for x in constraints),
        claimed_core_refs=tuple(x.id for x in constraints) if unsat else (),
        subset_minimal_claim=unsat)
    prov=tuple(ProvenanceRecord(f"prov:{x.id}",TraceRef(ReferenceKind.CONSTRAINT,str(x.id)),ProvenanceKind.DIRECT) for x in constraints)
    return Trace("resolvewhy-trace/1.0","test-resolver","1.0",None,TraceScope.SINGLE_ENVIRONMENT,
        (c,),ed,ResolutionPolicy("policy:test",prerelease_mode="disallow",universal_strategy="single"),
        tuple(domains),tuple(requirements),(a,),arts,deps,(),(),constraints,ev,prov,claim)


def problem_for(trace):
    return SemanticProblem.from_trace(trace,trace.semantic_constraints,trace.runtime_contexts,trace.proof_claim.quantifier)


class ExplanationTests(unittest.TestCase):
    def verified(self, trace):
        result=verify(trace)
        self.assertTrue(result.independently_verified or result.status in {
            VerificationStatus.INSUFFICIENT_EVIDENCE,VerificationStatus.INVALID_TRACE})
        return problem_for(trace),result

    def test_model_construction(self):
        p,r=self.verified(make_trace())
        e=build_explanation(p,r)
        self.assertEqual(e.kind.value,"VERIFIED_SAT")
        self.assertTrue(e.scope.evaluation_domain_id)

    def test_deterministic_rendering(self):
        p,r=self.verified(make_trace())
        self.assertEqual(render_explanation(build_explanation(p,r)),render_explanation(build_explanation(p,r)))

    def test_verified_sat(self):
        p,r=self.verified(make_trace())
        e=build_explanation(p,r)
        self.assertEqual(e.kind.value,"VERIFIED_SAT")
        self.assertIn("Verified SAT.",render_explanation(e))

    def test_verified_unsat(self):
        p,r=self.verified(make_trace(unsat=True))
        e=build_explanation(p,r)
        self.assertEqual(e.kind.value,"VERIFIED_UNSAT")
        self.assertIn("Verified UNSAT.",render_explanation(e))

    def test_insufficient_evidence(self):
        p,r=self.verified(make_trace(incomplete=True))
        self.assertEqual(r.status,VerificationStatus.INSUFFICIENT_EVIDENCE)
        e=build_explanation(p,r)
        text=render_explanation(e)
        self.assertIn("insufficient",text.lower())
        self.assertNotIn("Verified UNSAT.",text)
        self.assertNotIn("Verified SAT.",text)

    def test_invalid_trace(self):
        trace=make_trace()
        bad=replace(trace,candidates=(trace.candidates[0],trace.candidates[0]))
        p=problem_for(bad)
        r=verify(bad)
        self.assertEqual(r.status,VerificationStatus.INVALID_TRACE)
        self.assertIn("failed structural or semantic validation",render_explanation(build_explanation(p,r)))

    def test_subset_minimal_wording(self):
        p,r=self.verified(make_trace(unsat=True))
        text=render_explanation(build_explanation(p,r))
        self.assertIn("Verified subset-minimal core",text)
        self.assertNotIn("minimum-cardinality",text)
        self.assertNotIn("smallest",text)

    def test_dependency_path_derivation(self):
        p,r=self.verified(make_trace(dependency=True))
        e=build_explanation(p,r)
        self.assertTrue(e.dependency_paths)
        self.assertTrue(all(x.dependency_ref or x.requirement_ref for x in e.dependency_paths))

    def test_candidate_references(self):
        p,r=self.verified(make_trace())
        e=build_explanation(p,r)
        self.assertIn("cand:pkg:1",e.candidate_refs)

    def test_artifact_references(self):
        p,r=self.verified(make_trace(artifact=True))
        e=build_explanation(p,r)
        self.assertIn("art:pkg",tuple(x.id for x in e.artifacts))

    def test_evaluation_domain_exposure(self):
        p,r=self.verified(make_trace())
        self.assertEqual(r.evaluation_domain_id,"eval:test")
        self.assertEqual(build_explanation(p,r).scope.evaluation_domain_id,"eval:test")

    def test_proof_scope_exposure(self):
        p,r=self.verified(make_trace())
        self.assertEqual(build_explanation(p,r).scope.quantifier,ProofQuantifier.EXISTENTIAL)

    def test_runtime_context_exposure(self):
        p,r=self.verified(make_trace())
        self.assertEqual(build_explanation(p,r).scope.runtime_context_refs,("env:py311",))

    def test_unverified_authoritative_rejected(self):
        p,r=self.verified(make_trace())
        bad=replace(r,status=VerificationStatus.VERIFIED_UNSAT,independently_verified=False)
        with self.assertRaises(ValueError): build_explanation(p,bad)

    def test_nondecision_marked_verified_rejected(self):
        p,r=self.verified(make_trace(incomplete=True))
        bad=replace(r,independently_verified=True)
        with self.assertRaises(ValueError): build_explanation(p,bad)

    def test_native_diagnostics_not_rendered(self):
        p,r=self.verified(make_trace())
        text=render_explanation(build_explanation(p,r))
        self.assertNotIn("test-resolver",text)

    def test_native_incompatibility_not_rendered(self):
        p,r=self.verified(make_trace(artifact=True))
        text=render_explanation(build_explanation(p,r))
        self.assertNotIn("resolver_namespace",text)

    def test_stable_constraint_order(self):
        p,r=self.verified(make_trace(unsat=True))
        e=build_explanation(p,r)
        self.assertEqual(e.constraint_refs,tuple(sorted(e.constraint_refs)))

    def test_stable_candidate_order(self):
        p,r=self.verified(make_trace())
        e=build_explanation(p,r)
        self.assertEqual(e.candidate_refs,tuple(sorted(e.candidate_refs)))

    def test_stable_policy_order(self):
        p,r=self.verified(make_trace())
        e=build_explanation(p,r)
        keys=tuple(x.key for x in e.policy_facts)
        self.assertEqual(keys,tuple(sorted(keys)))

    def test_stable_evidence_order(self):
        p,r=self.verified(make_trace(unsat=True))
        e=build_explanation(p,r)
        refs=tuple(x.ref for x in e.evidence_facts)
        self.assertEqual(refs,tuple(sorted(refs)))

    def test_auditable_constraint_refs(self):
        p,r=self.verified(make_trace(unsat=True))
        e=build_explanation(p,r)
        self.assertEqual(set(e.constraint_refs),set(r.premise_ids))

    def test_auditable_dependency_refs(self):
        p,r=self.verified(make_trace(dependency=True))
        e=build_explanation(p,r)
        self.assertEqual(tuple(sorted(e.dependency_path_refs)),e.dependency_path_refs)

    def test_auditable_candidate_refs(self):
        p,r=self.verified(make_trace())
        e=build_explanation(p,r)
        self.assertEqual(e.candidate_refs,tuple(sorted(e.candidate_refs)))

    def test_policy_facts_present(self):
        p,r=self.verified(make_trace())
        e=build_explanation(p,r)
        self.assertTrue(any(x.key=="prerelease_mode" for x in e.policy_facts))

    def test_evidence_facts_present(self):
        p,r=self.verified(make_trace())
        e=build_explanation(p,r)
        self.assertTrue(e.evidence_facts)

    def test_sat_assignment_not_invented(self):
        p,r=self.verified(make_trace())
        text=render_explanation(build_explanation(p,r))
        self.assertIn("No satisfying assignment is shown",text)

    def test_fail_closed_invalid_status(self):
        p,r=self.verified(make_trace())
        bad=replace(r,status=VerificationStatus.INVALID_TRACE,independently_verified=False,
                    issues=(VerificationIssue("invalid_schema","bad"),))
        text=render_explanation(build_explanation(p,bad))
        self.assertNotIn("Verified SAT.",text)
        self.assertNotIn("Verified UNSAT.",text)

    def test_issue_refs_are_auditable(self):
        p,r=self.verified(make_trace(incomplete=True))
        e=build_explanation(p,r)
        self.assertTrue(all(x.code for x in e.issues))

    def test_core_is_only_exposed_when_verified_minimal(self):
        p,r=self.verified(make_trace(unsat=True))
        e=build_explanation(p,r)
        self.assertIsNotNone(e.core)
        unverified=replace(r,minimality_verified=False)
        self.assertIsNone(build_explanation(p,unverified).core)

    def test_no_solver_invocation_contract(self):
        # The builder only receives SemanticProblem + VerificationResult; a valid
        # precomputed result is sufficient and no solver dependency is required.
        p,r=self.verified(make_trace())
        e=build_explanation(p,r)
        self.assertEqual(e.kind.value,"VERIFIED_SAT")

    def test_empty_core_not_claimed(self):
        p,r=self.verified(make_trace())
        bad=replace(r,status=VerificationStatus.VERIFIED_UNSAT,independently_verified=True,
                    core_ids=(),core_verified=None,minimality_verified=None)
        e=build_explanation(p,bad)
        self.assertIsNone(e.core)

    def test_invalid_trace_has_no_verified_outcome_claim(self):
        trace=make_trace()
        bad=replace(trace,candidates=(trace.candidates[0],trace.candidates[0]))
        e=build_explanation(problem_for(bad),verify(bad))
        text=render_explanation(e)
        self.assertNotIn("Verified SAT.",text)
        self.assertNotIn("Verified UNSAT.",text)

    def test_scope_is_independent_of_trace_scope_label(self):
        p,r=self.verified(make_trace())
        changed=replace(r,quantifier=ProofQuantifier.BRANCH,evaluation_domain=("env:py311",))
        e=build_explanation(p,changed)
        self.assertEqual(e.scope.quantifier,ProofQuantifier.BRANCH)

    def test_renderer_has_no_nondeterministic_fields(self):
        p,r=self.verified(make_trace())
        text=render_explanation(build_explanation(p,r))
        self.assertNotIn("timestamp",text.lower())
        self.assertNotIn("datetime",text.lower())


if __name__=="__main__":
    unittest.main()
