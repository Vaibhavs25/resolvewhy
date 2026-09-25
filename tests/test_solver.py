from __future__ import annotations

from dataclasses import replace
import unittest

from resolvewhy.model import (
    Artifact,
    ArtifactSelectionStatus,
    Candidate,
    CandidateKind,
    CoverageStatus,
    DependencyEdge,
    EvaluationDomain,
    EvaluationDomainKind,
    EvidenceStateKind,
    MarkerAtom,
    MarkerExpression,
    ProofClaim,
    ProofQuantifier,
    ProofStatus,
    ReferenceKind,
    Requirement,
    ResolutionPolicy,
    SemanticConstraint,
    SemanticConstraintKind,
    SemanticLiteral,
    TraceRef,
    TraceScope,
    VersionConstraint,
)
from resolvewhy.solving import (
    SemanticProblem,
    SolveStatus,
    minimal_unsat_core,
    solve,
    verify_unsat_core,
)
from resolvewhy.verification import verify
from resolvewhy.verification.result import VerificationStatus

import tests.test_verification as verification_fixtures

from tests.test_verification import (
    _candidate,
    _constraint,
    _ctx,
    _domain,
    _policy,
    _req,
    _trace,
)


class SolverTests(unittest.TestCase):
    def _problem(self, trace, constraints=None, contexts=None, quantifier=None):
        constraints = tuple(constraints or trace.semantic_constraints)
        contexts = tuple(contexts or trace.runtime_contexts)
        quantifier = quantifier or trace.proof_claim.quantifier
        return SemanticProblem.from_trace(trace, constraints, contexts, quantifier)

    def test_direct_two_constraint_unsat(self):
        ctx = _ctx(); c1 = _candidate("pkg", "1.0", "one"); c2 = _candidate("pkg", "2.0", "two")
        r1 = _req("pkg", ">=", "2.0", "ge"); r2 = _req("pkg", "<", "2.0", "lt")
        q1 = _constraint("c:ge", SemanticConstraintKind.REQUIREMENT, (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", candidate_ref=None, operator=">=", value="2.0"),), TraceRef(ReferenceKind.REQUIREMENT, r1.id), "obs:c:ge")
        q2 = _constraint("c:lt", SemanticConstraintKind.REQUIREMENT, (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", candidate_ref=None, operator="<", value="2.0"),), TraceRef(ReferenceKind.REQUIREMENT, r2.id), "obs:c:lt")
        trace = _trace(contexts=(ctx,), requirements=(r1, r2), candidates=(c1, c2), domains=(_domain("pkg", ctx, (c1, c2)),), constraints=(q1, q2))
        self.assertEqual(solve(self._problem(trace)).status, SolveStatus.UNSAT)

    def test_transitive_unsat(self):
        ctx = _ctx()
        a = _candidate("a", "1.0")
        b = _candidate("b", "1.0")
        c1 = _candidate("c", "1.0", "one")
        c2 = _candidate("c", "2.0", "two")
        ra = _req("a", "==", "1.0")
        rb = _req("b", "==", "1.0")
        rca = _req("c", "<", "2.0", "a")
        rcb = _req("c", ">=", "2.0", "b")
        da = DependencyEdge("dep:a-c", a.id, rca.id)
        db = DependencyEdge("dep:b-c", b.id, rcb.id)
        constraints = (
            _constraint("c:a", SemanticConstraintKind.REQUIREMENT,
                (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="a", candidate_ref=a.id, operator="==", value="1.0"),),
                TraceRef(ReferenceKind.REQUIREMENT, ra.id), "obs:c:a"),
            _constraint("c:b", SemanticConstraintKind.REQUIREMENT,
                (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="b", candidate_ref=b.id, operator="==", value="1.0"),),
                TraceRef(ReferenceKind.REQUIREMENT, rb.id), "obs:c:b"),
            _constraint("c:a-c", SemanticConstraintKind.DEPENDENCY,
                (SemanticLiteral(kind=SemanticConstraintKind.DEPENDENCY, package="c", candidate_ref=a.id, operator="<", value="2.0"),),
                TraceRef(ReferenceKind.DEPENDENCY, da.id), "obs:c:a-c"),
            _constraint("c:b-c", SemanticConstraintKind.DEPENDENCY,
                (SemanticLiteral(kind=SemanticConstraintKind.DEPENDENCY, package="c", candidate_ref=b.id, operator=">=", value="2.0"),),
                TraceRef(ReferenceKind.DEPENDENCY, db.id), "obs:c:b-c"),
        )
        trace = _trace(
            contexts=(ctx,), requirements=(ra, rb, rca, rcb), candidates=(a, b, c1, c2),
            domains=(_domain("a", ctx, (a,)), _domain("b", ctx, (b,)), _domain("c", ctx, (c1, c2))),
            dependencies=(da, db), constraints=constraints,
        )
        self.assertEqual(solve(self._problem(trace)).status, SolveStatus.UNSAT)

    def test_sat_after_one_constraint_removed(self):
        trace = verification_fixtures.ProductionVerifierTests()._unsat_three_constraints_fixture()
        problem = self._problem(trace, (trace.semantic_constraints[0], trace.semantic_constraints[1]))
        self.assertEqual(solve(problem).status, SolveStatus.SAT)

    def test_subset_minimal_core(self):
        trace = verification_fixtures.ProductionVerifierTests()._unsat_three_constraints_fixture()
        result = minimal_unsat_core(self._problem(trace), tuple(c.id for c in trace.semantic_constraints))
        self.assertEqual(result.status, SolveStatus.UNSAT)
        self.assertTrue(result.minimal)
        self.assertEqual(result.core_ids, ("c:bad",))

    def test_non_minimal_supplied_core_rejected(self):
        trace = verification_fixtures.ProductionVerifierTests()._unsat_three_constraints_fixture()
        problem = self._problem(trace)
        result = verify_unsat_core(problem, tuple(c.id for c in trace.semantic_constraints))
        self.assertFalse(result.verified)
        self.assertTrue(result.unsat_verified)
        self.assertEqual(result.reason, "deletion_not_sat")

    def test_incorrect_supplied_core_rejected(self):
        trace = verification_fixtures.ProductionVerifierTests()._unsat_three_constraints_fixture()
        problem = self._problem(trace)
        result = verify_unsat_core(problem, ("c:ge", "c:lt"))
        self.assertFalse(result.verified)
        self.assertFalse(result.unsat_verified)

    def test_sat_problem_has_no_unsat_core(self):
        # Build one consistent context/candidate set.
        ctx = _ctx(); cand = _candidate("pkg", "1.0"); req = _req("pkg", "==", "1.0")
        c = _constraint("c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", candidate_ref=None, operator="==", value="1.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg")
        trace = _trace(contexts=(ctx,), requirements=(req,), candidates=(cand,), domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,))
        problem = self._problem(trace)
        self.assertEqual(solve(problem).status, SolveStatus.SAT)
        self.assertEqual(minimal_unsat_core(problem, (c.id,)).status, SolveStatus.SAT)

    def test_incomplete_candidate_coverage_blocks_unsat(self):
        ctx = _ctx(); req = _req("pkg", "==", "9.0")
        c = _constraint("c:pkg", SemanticConstraintKind.REQUIREMENT,
            (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", candidate_ref=None, operator="==", value="9.0"),),
            TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg")
        trace = _trace(contexts=(ctx,), requirements=(req,), domains=(_domain("pkg", ctx, (), status=CoverageStatus.UNKNOWN),), constraints=(c,))
        result = solve(self._problem(trace))
        self.assertEqual(result.status, SolveStatus.INSUFFICIENT_EVIDENCE)

    def test_universal_environment_contradiction(self):
        trace = verification_fixtures.ProductionVerifierTests()._multi_env_fixture(ProofQuantifier.UNIVERSAL)
        problem = self._problem(trace, quantifier=ProofQuantifier.UNIVERSAL)
        result = solve(problem)
        self.assertEqual(result.status, SolveStatus.UNSAT)
        self.assertEqual(tuple(x.value for x in result.branch_results), ("SAT", "UNSAT"))

    def test_branch_contradiction(self):
        trace = verification_fixtures.ProductionVerifierTests()._multi_env_fixture(ProofQuantifier.BRANCH)
        problem = self._problem(trace, quantifier=ProofQuantifier.BRANCH, contexts=(trace.runtime_contexts[1],))
        self.assertEqual(solve(problem).status, SolveStatus.UNSAT)

    def test_conditional_dependency(self):
        ctx = _ctx(os="linux"); a = _candidate("a", "1.0"); req = _req("a", "==", "1.0"); dep_req = _req("b", "==", "1.0", "dep")
        edge = DependencyEdge("dep:a-b", a.id, dep_req.id, MarkerExpression("atom", MarkerAtom("sys_platform", "==", "win32")))
        c1 = _constraint("c:a", SemanticConstraintKind.REQUIREMENT, (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="a", candidate_ref=a.id, operator="==", value="1.0"),), TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:a")
        c2 = _constraint("c:a-b", SemanticConstraintKind.DEPENDENCY, (SemanticLiteral(kind=SemanticConstraintKind.DEPENDENCY, package="b", candidate_ref=a.id, operator="==", value="1.0", activation=edge.activation),), TraceRef(ReferenceKind.DEPENDENCY, edge.id), "obs:c:a-b")
        trace = _trace(contexts=(ctx,), requirements=(req, dep_req), candidates=(a,), domains=(_domain("a", ctx, (a,)), _domain("b", ctx, ())), dependencies=(edge,), constraints=(c1, c2))
        self.assertEqual(solve(self._problem(trace)).status, SolveStatus.SAT)

    def test_artifact_feasibility(self):
        ctx = _ctx(); cand = _candidate("pkg", "1.0"); req = _req("pkg", "==", "1.0")
        art = Artifact(id="art:pkg", candidate_ref=cand.id, compatible=False, selection_status=ArtifactSelectionStatus.INCOMPATIBLE)
        c1 = _constraint("c:pkg", SemanticConstraintKind.REQUIREMENT, (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", candidate_ref=None, operator="==", value="1.0"),), TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg")
        c2 = _constraint("c:artifact", SemanticConstraintKind.ARTIFACT_COMPATIBILITY, (SemanticLiteral(SemanticConstraintKind.ARTIFACT_COMPATIBILITY, "pkg", cand.id, artifact_ref=art.id),), TraceRef(ReferenceKind.ARTIFACT, art.id), "obs:c:artifact")
        trace = _trace(contexts=(ctx,), requirements=(req,), candidates=(cand,), domains=(_domain("pkg", ctx, (cand,)),), artifacts=(art,), constraints=(c1, c2))
        self.assertEqual(solve(self._problem(trace)).status, SolveStatus.UNSAT)

    def test_requires_python(self):
        ctx = _ctx(); cand = _candidate("pkg", "1.0"); req = _req("pkg", "==", "1.0")
        c1 = _constraint("c:pkg", SemanticConstraintKind.REQUIREMENT, (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", candidate_ref=None, operator="==", value="1.0"),), TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg")
        c2 = _constraint("c:python", SemanticConstraintKind.REQUIRES_PYTHON, (SemanticLiteral(kind=SemanticConstraintKind.REQUIRES_PYTHON, package="<Python>", candidate_ref=cand.id, runtime_context_ref=ctx.id, operator=">=", value="4.0"),), TraceRef(ReferenceKind.CANDIDATE, cand.id), "obs:c:python")
        trace = _trace(contexts=(ctx,), requirements=(req,), candidates=(cand,), domains=(_domain("pkg", ctx, (cand,)),), constraints=(c1, c2))
        self.assertEqual(solve(self._problem(trace)).status, SolveStatus.UNSAT)

    def test_prerelease_policy(self):
        ctx = _ctx(); cand = _candidate("pkg", "1.0rc1"); req = _req("pkg", "<", "2.0")
        c = _constraint("c:pkg", SemanticConstraintKind.REQUIREMENT, (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", candidate_ref=None, operator="<", value="2.0"),), TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:pkg")
        disallow = _trace(contexts=(ctx,), requirements=(req,), candidates=(cand,), domains=(_domain("pkg", ctx, (cand,)),), constraints=(c,), policy=_policy("disallow"))
        allow = replace(disallow, resolution_policy=_policy("allow"))
        self.assertEqual(solve(self._problem(disallow)).status, SolveStatus.UNSAT)
        self.assertEqual(solve(self._problem(allow)).status, SolveStatus.SAT)

    def test_altered_candidate_identity_changes_result(self):
        ctx = _ctx(); a = _candidate("pkg", "1.0", "a"); b = _candidate("pkg", "1.0", "b"); req = _req("pkg", "==", "1.0")
        c_a = _constraint("c:a", SemanticConstraintKind.REQUIREMENT, (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="pkg", candidate_ref=a.id, operator="==", value="1.0"),), TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:a")
        trace = _trace(contexts=(ctx,), requirements=(req,), candidates=(a, b), domains=(_domain("pkg", ctx, (a,)),), constraints=(c_a,))
        sat = solve(self._problem(trace)).status
        c_b = replace(c_a, literals=(replace(c_a.literals[0], candidate_ref=b.id),))
        unsat = solve(self._problem(replace(trace, semantic_constraints=(c_b,)))).status
        self.assertEqual((sat, unsat), (SolveStatus.SAT, SolveStatus.UNSAT))

    def test_altered_evaluation_domain_changes_universal_result(self):
        trace = verification_fixtures.ProductionVerifierTests()._multi_env_fixture(ProofQuantifier.UNIVERSAL)
        all_envs = self._problem(trace, quantifier=ProofQuantifier.UNIVERSAL)
        one_env = self._problem(trace, contexts=(trace.runtime_contexts[0],), quantifier=ProofQuantifier.UNIVERSAL)
        self.assertEqual(solve(all_envs).status, SolveStatus.UNSAT)
        self.assertEqual(solve(one_env).status, SolveStatus.SAT)

    def test_altered_quantifier_changes_result(self):
        trace = verification_fixtures.ProductionVerifierTests()._multi_env_fixture(ProofQuantifier.UNIVERSAL)
        universal = solve(self._problem(trace, quantifier=ProofQuantifier.UNIVERSAL)).status
        existential = solve(self._problem(trace, quantifier=ProofQuantifier.EXISTENTIAL)).status
        self.assertEqual((universal, existential), (SolveStatus.UNSAT, SolveStatus.SAT))

    def test_altered_activation_changes_result(self):
        ctx = _ctx(os="linux"); a = _candidate("a", "1.0"); req = _req("a", "==", "1.0"); dep_req = _req("b", "==", "1.0", "dep")
        active = MarkerExpression("atom", MarkerAtom("sys_platform", "==", "linux"))
        edge = DependencyEdge("dep:a-b", a.id, dep_req.id, active)
        c1 = _constraint("c:a", SemanticConstraintKind.REQUIREMENT, (SemanticLiteral(kind=SemanticConstraintKind.REQUIREMENT, package="a", candidate_ref=a.id, operator="==", value="1.0"),), TraceRef(ReferenceKind.REQUIREMENT, req.id), "obs:c:a")
        c2 = _constraint("c:a-b", SemanticConstraintKind.DEPENDENCY, (SemanticLiteral(kind=SemanticConstraintKind.DEPENDENCY, package="b", candidate_ref=a.id, operator="==", value="1.0", activation=active),), TraceRef(ReferenceKind.DEPENDENCY, edge.id), "obs:c:a-b")
        trace = _trace(contexts=(ctx,), requirements=(req, dep_req), candidates=(a,), domains=(_domain("a", ctx, (a,)), _domain("b", ctx, ())), dependencies=(edge,), constraints=(c1, c2))
        self.assertEqual(solve(self._problem(trace)).status, SolveStatus.UNSAT)
        inactive = replace(edge, activation=MarkerExpression("atom", MarkerAtom("sys_platform", "==", "win32")))
        inactive_c = replace(c2, literals=(replace(c2.literals[0], activation=inactive.activation),))
        changed = replace(trace, dependencies=(inactive,), semantic_constraints=(c1, inactive_c))
        self.assertEqual(solve(self._problem(changed)).status, SolveStatus.SAT)

    def test_malformed_semantic_problem_rejected(self):
        trace = verification_fixtures.ProductionVerifierTests()._unsat_three_constraints_fixture()
        bad = replace(trace, candidates=(trace.candidates[0], trace.candidates[0]))
        problem = self._problem(bad)
        result = solve(problem)
        self.assertEqual(result.status, SolveStatus.INVALID_PROBLEM)

    def test_deterministic_repeated_solving(self):
        trace = verification_fixtures.ProductionVerifierTests()._unsat_three_constraints_fixture()
        problem = self._problem(trace)
        first = solve(problem)
        self.assertEqual(first, solve(problem))
        left = minimal_unsat_core(problem, tuple(c.id for c in trace.semantic_constraints))
        right = minimal_unsat_core(problem, tuple(c.id for c in reversed(trace.semantic_constraints)))
        self.assertEqual(left.core_ids, right.core_ids)
        self.assertEqual(left.minimal, right.minimal)

    def test_resolver_unsat_claim_is_ignored(self):
        trace = verification_fixtures.ProductionVerifierTests()._unsat_three_constraints_fixture()
        trace = replace(trace, proof_claim=replace(trace.proof_claim, status_claim=ProofStatus.SAT))
        problem = self._problem(trace)
        self.assertEqual(solve(problem).status, SolveStatus.UNSAT)
        self.assertEqual(verify(trace).status, VerificationStatus.VERIFIED_UNSAT)

    def test_resolver_sat_claim_is_ignored(self):
        trace = verification_fixtures.ProductionVerifierTests()._unsat_three_constraints_fixture()
        trace = replace(trace, proof_claim=replace(trace.proof_claim, status_claim=ProofStatus.SAT))
        self.assertEqual(solve(self._problem(trace)).status, SolveStatus.UNSAT)


if __name__ == "__main__":
    unittest.main()
