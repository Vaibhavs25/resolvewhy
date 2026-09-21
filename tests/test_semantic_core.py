from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from resolvewhy.model import (
    Artifact,
    Candidate,
    CandidateCoverage,
    CandidateDomain,
    CandidateDomainScope,
    CandidateKind,
    CoverageAttestation,
    CoverageAttestationKind,
    CoverageStatus,
    EvaluationDomain,
    EvaluationDomainKind,
    EvidenceObservation,
    EvidenceState,
    EvidenceStateKind,
    MarkerAtom,
    MarkerExpression,
    ProofClaim,
    ProofQuantifier,
    ProofStatus,
    ProvenanceKind,
    ProvenanceRecord,
    ReferenceKind,
    Requirement,
    ResolutionPolicy,
    RuntimeContext,
    SemanticConstraint,
    SemanticConstraintKind,
    SemanticLiteral,
    Trace,
    TraceRef,
    TraceScope,
    VersionConstraint,
)
from resolvewhy.validation import validate_trace


def valid_trace() -> Trace:
    env = RuntimeContext(
        id="env:py3.11-linux",
        python_implementation="CPython",
        python_version="3.11",
        os="linux",
        architecture="x86_64",
        marker_values=(
            ("platform_machine", "x86_64"),
            ("python_full_version", "3.11.9"),
            ("python_version", "3.11"),
        ),
    )
    policy = ResolutionPolicy(
        id="policy:default",
        prerelease_mode="disallow",
        universal_strategy="single",
    )
    req = Requirement(
        id="req:a",
        package="a",
        constraint=VersionConstraint("==", "1.0"),
    )
    candidate = Candidate(
        id="cand:a:1",
        package="a",
        version="1.0",
        kind=CandidateKind.REGISTRY,
        source_ref="index:main",
    )
    artifact = Artifact(
        id="artifact:a:1:wheel",
        candidate_ref="cand:a:1",
        origin="https://example.invalid/a-1.0-py3-none-any.whl",
        compatible=True,
    )
    evaluation_domain = EvaluationDomain(
        id="eval:singleton",
        kind=EvaluationDomainKind.SINGLETON_ENVIRONMENT,
        environment_refs=("env:py3.11-linux",),
    )
    evidence = EvidenceState(
        overall=EvidenceStateKind.KNOWN_FACT,
        observations=(
            EvidenceObservation(
                id="obs:req",
                kind="requirement",
                state=EvidenceStateKind.KNOWN_FACT,
                supports_refs=(TraceRef(ReferenceKind.CONSTRAINT, "c:req"),),
            ),
            EvidenceObservation(
                id="obs:coverage",
                kind="coverage",
                state=EvidenceStateKind.KNOWN_FACT,
                supports_refs=(TraceRef(ReferenceKind.CANDIDATE_DOMAIN, "domain:a"),),
            ),
        ),
    )
    domain = CandidateDomain(
        id="domain:a",
        identifier="a",
        requirement_refs=("req:a",),
        candidate_refs=("cand:a:1",),
        scope=CandidateDomainScope(sources=("index:main",)),
        runtime_context_ref="env:py3.11-linux",
        resolution_policy_ref=policy.id,
        coverage=CandidateCoverage(
            status=CoverageStatus.COMPLETE,
            attestation=CoverageAttestation(
                CoverageAttestationKind.AUTHORITATIVE_FINITE_DOMAIN,
                evidence_refs=(TraceRef(ReferenceKind.EVIDENCE, "obs:coverage"),),
            ),
        ),
    )
    constraint = SemanticConstraint(
        id="c:req",
        kind=SemanticConstraintKind.REQUIREMENT,
        literals=(
            SemanticLiteral(
                kind=SemanticConstraintKind.REQUIREMENT,
                package="a",
                candidate_ref="cand:a:1",
                operator="==",
                value="1.0",
            ),
        ),
        source_refs=(TraceRef(ReferenceKind.EVIDENCE, "obs:req"),),
    )
    provenance = (
        ProvenanceRecord(
            id="prov:c:req",
            subject_ref=TraceRef(ReferenceKind.CONSTRAINT, "c:req"),
            kind=ProvenanceKind.DIRECT,
        ),
    )
    claim = ProofClaim(
        id="claim:1",
        kind="satisfiability",
        quantifier=ProofQuantifier.EXISTENTIAL,
        evaluation_domain_ref=evaluation_domain.id,
        status_claim=ProofStatus.SAT,
        premise_refs=("c:req",),
    )
    return Trace(
        schema="resolvewhy-trace/1.0",
        resolver_name="test-resolver",
        resolver_version="1",
        resolver_commit=None,
        trace_scope=TraceScope.SINGLE_ENVIRONMENT,
        runtime_contexts=(env,),
        evaluation_domain=evaluation_domain,
        resolution_policy=policy,
        candidate_domains=(domain,),
        requirements=(req,),
        candidates=(candidate,),
        artifacts=(artifact,),
        dependencies=(),
        rejections=(),
        incompatibilities=(),
        semantic_constraints=(constraint,),
        evidence_state=evidence,
        provenance=provenance,
        proof_claim=claim,
    )


class SemanticCoreTests(unittest.TestCase):
    def test_valid_candidate_identity(self):
        trace = valid_trace()
        self.assertEqual(trace.candidates[0].id, "cand:a:1")
        self.assertEqual(trace.candidates[0].kind, CandidateKind.REGISTRY)
        self.assertEqual(validate_trace(trace), ())

    def test_valid_source_aware_candidate(self):
        trace = valid_trace()
        mirror = Candidate(
            id="cand:a:1:mirror",
            package="a",
            version="1.0",
            kind=CandidateKind.REGISTRY,
            source_ref="index:mirror",
        )
        self.assertNotEqual(trace.candidates[0].id, mirror.id)
        self.assertNotEqual(trace.candidates[0].source_ref, mirror.source_ref)

    def test_candidate_artifact_distinction(self):
        trace = valid_trace()
        self.assertNotEqual(trace.candidates[0].id, trace.artifacts[0].id)
        self.assertEqual(trace.artifacts[0].candidate_ref, trace.candidates[0].id)

    def test_runtime_context_vs_evaluation_domain(self):
        trace = valid_trace()
        self.assertEqual(trace.evaluation_domain.environment_refs, (trace.runtime_contexts[0].id,))
        self.assertNotEqual(trace.evaluation_domain.id, trace.runtime_contexts[0].id)

    def test_explicit_quantifier_domain_binding(self):
        trace = valid_trace()
        self.assertEqual(trace.proof_claim.quantifier, ProofQuantifier.EXISTENTIAL)
        self.assertEqual(
            trace.proof_claim.evaluation_domain_ref,
            trace.evaluation_domain.id,
        )

    def test_valid_proof_premises(self):
        self.assertEqual(validate_trace(valid_trace()), ())

    def test_invalid_proof_premise_reference(self):
        trace = valid_trace()
        broken_claim = replace(
            trace.proof_claim,
            premise_refs=("missing-constraint",),
        )
        broken = replace(trace, proof_claim=broken_claim)
        codes = {issue.code for issue in validate_trace(broken)}
        self.assertIn("invalid_proof_premise", codes)

    def test_complete_candidate_coverage_attestation(self):
        coverage = valid_trace().candidate_domains[0].coverage
        self.assertEqual(coverage.status, CoverageStatus.COMPLETE)
        self.assertIsNotNone(coverage.attestation)

    def test_incomplete_coverage_is_representable_without_completeness_claim(self):
        trace = valid_trace()
        domain = trace.candidate_domains[0]
        incomplete = replace(
            domain,
            coverage=CandidateCoverage(status=CoverageStatus.PARTIAL),
        )
        changed = replace(trace, candidate_domains=(incomplete,))
        self.assertEqual(validate_trace(changed), ())

    def test_provenance_reference(self):
        trace = valid_trace()
        self.assertEqual(trace.provenance[0].subject_ref.kind, ReferenceKind.CONSTRAINT)
        self.assertEqual(validate_trace(trace), ())

    def test_dangling_reference_rejected(self):
        trace = valid_trace()
        broken_artifact = replace(
            trace.artifacts[0],
            candidate_ref="missing-candidate",
        )
        broken = replace(trace, artifacts=(broken_artifact,))
        codes = {issue.code for issue in validate_trace(broken)}
        self.assertIn("candidate_artifact_identity", codes)

    def test_duplicate_id_rejected(self):
        trace = valid_trace()
        duplicate = trace.candidates[0]
        broken = replace(trace, candidates=(duplicate, duplicate))
        codes = {issue.code for issue in validate_trace(broken)}
        self.assertIn("duplicate_id", codes)

    def test_activation_condition_preserved(self):
        marker = MarkerExpression(
            kind="atom",
            atom=MarkerAtom("python_version", ">=", "3.10"),
        )
        req = Requirement(
            id="req:b",
            package="b",
            constraint=VersionConstraint(">=", "1.0"),
            activation=marker,
        )
        self.assertEqual(req.activation, marker)

    def test_policy_is_separate_from_constraint(self):
        trace = valid_trace()
        self.assertIsInstance(trace.resolution_policy, ResolutionPolicy)
        self.assertIsInstance(trace.semantic_constraints[0], SemanticConstraint)
        self.assertIsNot(trace.resolution_policy, trace.semantic_constraints[0])

    def test_complete_coverage_without_attestation_is_rejected(self):
        trace = valid_trace()
        domain = trace.candidate_domains[0]
        broken_domain = replace(
            domain,
            coverage=CandidateCoverage(status=CoverageStatus.COMPLETE),
        )
        broken = replace(trace, candidate_domains=(broken_domain,))
        codes = {issue.code for issue in validate_trace(broken)}
        self.assertIn("invalid_coverage_attestation", codes)

    def test_branch_claim_must_bind_to_declared_environment(self):
        trace = valid_trace()
        claim = replace(
            trace.proof_claim,
            quantifier=ProofQuantifier.BRANCH,
            branch_ref="missing-env",
        )
        broken = replace(trace, proof_claim=claim)
        codes = {issue.code for issue in validate_trace(broken)}
        self.assertIn("invalid_proof_binding", codes)


if __name__ == "__main__":
    unittest.main()
