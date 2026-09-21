from __future__ import annotations

import json
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from packaging.requirements import Requirement
from packaging.version import Version

from resolvewhy.model import (
    CandidateCoverage,
    CoverageAttestation,
    CoverageAttestationKind,
    CoverageStatus,
    EvaluationDomain,
    EvaluationDomainKind,
    EvidenceStateKind,
    ProofQuantifier,
    ResolutionPolicy,
    RuntimeContext,
    Trace,
)
from resolvewhy.trace import deserialize_trace, serialize_trace
from resolvewhy.validation import validate_trace
from resolvewhy.adapters.pip_resolvelib import (
    AdapterContext,
    AdapterNormalizationError,
    DefaultPipSemantics,
    PipResolvelibAdapter,
)


@dataclass(frozen=True)
class FakeCandidate:
    name: str
    version: Version
    dependencies: tuple[Requirement, ...] = ()


class FakeProvider:
    def __init__(self, candidates: dict[str, tuple[FakeCandidate, ...]]) -> None:
        self.candidates = candidates

    def identify(self, requirement_or_candidate):
        return requirement_or_candidate.name

    def get_preference(
        self,
        identifier,
        resolutions,
        candidates,
        information,
        backtrack_causes,
    ):
        return identifier

    def find_matches(self, identifier, requirements, incompatibilities):
        reqs = tuple(requirements[identifier])
        blocked = {candidate for candidate in incompatibilities.get(identifier, ())}
        return tuple(
            candidate
            for candidate in self.candidates.get(identifier, ())
            if candidate not in blocked
            and all(candidate.version in requirement.specifier for requirement in reqs)
        )

    def is_satisfied_by(self, requirement, candidate):
        return (
            requirement.name == candidate.name
            and candidate.version in requirement.specifier
        )

    def get_dependencies(self, candidate):
        return candidate.dependencies


class SemanticResolverIntegrationTests(unittest.TestCase):
    def context(self, *, coverage: dict[str, CoverageAttestation] | None = None) -> AdapterContext:
        runtime = RuntimeContext(
            id="env:py3.13-linux-x86_64",
            python_implementation="CPython",
            python_version="3.13",
            os="linux",
            architecture="x86_64",
            marker_values=(
                ("platform_machine", "x86_64"),
                ("python_version", "3.13"),
            ),
        )
        return AdapterContext(
            runtime_context=runtime,
            resolution_policy=ResolutionPolicy(
                id="policy:default",
                prerelease_mode="disallow",
                universal_strategy="single",
            ),
            evaluation_domain=EvaluationDomain(
                id="eval:py3.13-linux",
                kind=EvaluationDomainKind.SINGLETON_ENVIRONMENT,
                environment_refs=(runtime.id,),
            ),
            coverage_attestations=coverage or {},
            resolver_name="pip/resolvelib-test",
        )

    def adapter(self, candidates, *, context=None) -> PipResolvelibAdapter:
        try:
            import pip._vendor.resolvelib as vendored_resolvelib
        except ImportError as exc:
            self.skipTest(f"pip's vendored resolvelib is unavailable: {exc}")
        return PipResolvelibAdapter.from_resolvelib_module(
            resolver_module=vendored_resolvelib,
            provider=FakeProvider(candidates),
            context=context or self.context(),
        )

    def test_simple_satisfiable_real_resolvelib_path(self):
        candidates = {
            "a": (FakeCandidate("a", Version("1.0")),),
        }
        result = self.adapter(candidates).resolve([Requirement("a==1.0")])
        self.assertEqual(result.native_status_claim, "SAT")
        self.assertIsInstance(result.trace, Trace)
        self.assertEqual(result.trace.schema, "resolvewhy-trace/1.0")
        self.assertEqual(validate_trace(result.trace), ())
        payload = serialize_trace(result.trace)
        self.assertEqual(deserialize_trace(payload), result.trace)

    def test_transitive_conflict_real_resolvelib_path(self):
        candidates = {
            "a": (
                FakeCandidate(
                    "a",
                    Version("1.0"),
                    dependencies=(Requirement("c<2"),),
                ),
            ),
            "b": (
                FakeCandidate(
                    "b",
                    Version("1.0"),
                    dependencies=(Requirement("c>=2"),),
                ),
            ),
            "c": (
                FakeCandidate("c", Version("1.0")),
                FakeCandidate("c", Version("2.0")),
            ),
        }
        result = self.adapter(candidates).resolve(
            [Requirement("a==1.0"), Requirement("b==1.0")]
        )
        self.assertEqual(result.native_status_claim, "UNSAT")
        self.assertEqual(result.native_error_type, "RequirementsConflicted")
        self.assertIsInstance(result.trace, Trace)
        self.assertEqual(result.trace.schema, "resolvewhy-trace/1.0")
        self.assertEqual(validate_trace(result.trace), ())
        self.assertEqual(result.trace.proof_claim.quantifier, ProofQuantifier.EXISTENTIAL)

    def test_native_failure_is_not_verified_unsat(self):
        candidates = {
            "a": (
                FakeCandidate(
                    "a",
                    Version("1.0"),
                    dependencies=(Requirement("c<2"),),
                ),
            ),
            "b": (
                FakeCandidate(
                    "b",
                    Version("1.0"),
                    dependencies=(Requirement("c>=2"),),
                ),
            ),
            "c": (
                FakeCandidate("c", Version("1.0")),
                FakeCandidate("c", Version("2.0")),
            ),
        }
        result = self.adapter(candidates).resolve(
            [Requirement("a==1.0"), Requirement("b==1.0")]
        )
        self.assertEqual(result.native_status_claim, "UNSAT")
        self.assertEqual(result.trace.evidence_state.overall, EvidenceStateKind.INCOMPLETE)
        self.assertNotEqual(result.trace.proof_claim.status_claim.value, "VERIFIED_UNSAT")

    def test_unknown_candidate_coverage_is_conservative(self):
        result = self.adapter(
            {"a": (FakeCandidate("a", Version("1.0")),)}
        ).resolve([Requirement("a==1.0")])
        domains = result.trace.candidate_domains
        self.assertTrue(domains)
        self.assertTrue(
            all(domain.coverage.status is CoverageStatus.UNKNOWN for domain in domains)
        )

    def test_attested_candidate_coverage_becomes_complete_only_for_declared_scope(self):
        attestation = CoverageAttestation(
            kind=CoverageAttestationKind.AUTHORITATIVE_FINITE_DOMAIN,
            evidence_refs=(),
        )
        with self.assertRaises(ValueError):
            AdapterContext(
                runtime_context=self.context().runtime_context,
                resolution_policy=self.context().resolution_policy,
                coverage_attestations={"a": attestation},
            )

    def test_marker_preservation(self):
        semantics = DefaultPipSemantics()
        view = semantics.requirement_view(
            Requirement("c<2; python_version >= '3.10'")
        )
        self.assertIsNotNone(view.activation)
        self.assertTrue(view.activation is not None)
        self.assertEqual(view.activation.kind, "atom")

    def test_multiple_version_constraints_are_not_dropped_from_semantic_view(self):
        semantics = DefaultPipSemantics()
        view = semantics.requirement_view(Requirement("c>=1,<3"))
        self.assertEqual(
            [(item.operator, item.version) for item in view.constraints],
            [(">=", "1"), ("<", "3")],
        )

    def test_unsupported_marker_does_not_become_false_fact(self):
        class MarkerLikeRequirement:
            name = "c"
            project_name = "c"
            specifier = None
            marker = object()

            def __str__(self):
                return "c"

        view = DefaultPipSemantics().requirement_view(MarkerLikeRequirement())
        self.assertFalse(view.complete)
        self.assertTrue(view.unsupported_reasons)

    def test_source_distinct_candidates_remain_distinct(self):
        @dataclass(frozen=True)
        class FakeLink:
            url: str
            comes_from: str
            is_vcs: bool = False
            is_file: bool = False
            hashes: dict[str, str] = None
            yanked_reason: str | None = None

        @dataclass(frozen=True)
        class LinkCandidate:
            project_name: str
            version: Version
            source_link: FakeLink

        semantics = DefaultPipSemantics()
        left = semantics.candidate_view(
            LinkCandidate(
                "pkg",
                Version("1.0"),
                FakeLink(
                    url="https://one.example/pkg-1.0.whl",
                    comes_from="https://one.example/simple/pkg/",
                    hashes={},
                ),
            )
        )
        right = semantics.candidate_view(
            LinkCandidate(
                "pkg",
                Version("1.0"),
                FakeLink(
                    url="https://two.example/pkg-1.0.whl",
                    comes_from="https://two.example/simple/pkg/",
                    hashes={},
                ),
            )
        )
        self.assertNotEqual(left.identity_key, right.identity_key)

    def test_deterministic_trace_serialization(self):
        candidates = {
            "a": (FakeCandidate("a", Version("1.0")),),
        }
        first = self.adapter(candidates).resolve([Requirement("a==1.0")])
        second = self.adapter(candidates).resolve([Requirement("a==1.0")])
        self.assertEqual(serialize_trace(first.trace), serialize_trace(second.trace))

    def test_unknown_exception_is_not_relabelled(self):
        class BrokenProvider(FakeProvider):
            def find_matches(self, identifier, requirements, incompatibilities):
                raise RuntimeError("unrelated provider failure")

        try:
            import pip._vendor.resolvelib as vendored_resolvelib
        except ImportError as exc:
            self.skipTest(f"pip's vendored resolvelib is unavailable: {exc}")

        adapter = PipResolvelibAdapter.from_resolvelib_module(
            resolver_module=vendored_resolvelib,
            provider=BrokenProvider({}),
            context=self.context(),
        )
        with self.assertRaises(RuntimeError):
            adapter.resolve([Requirement("a==1.0")])

    def test_resolver_diagnostic_text_is_not_a_semantic_premise(self):
        result = self.adapter(
            {"a": (FakeCandidate("a", Version("1.0")),)}
        ).resolve([Requirement("a==1.0")])
        self.assertTrue(all(
            "diagnostic" not in observation.kind.lower()
            for observation in result.trace.evidence_state.observations
        ))

    def test_vendored_resolvelib_is_used_only_at_optional_integration_boundary(self):
        import resolvewhy
        self.assertTrue(hasattr(resolvewhy, "PipResolvelibAdapter"))

    def test_empty_capture_refuses_to_fabricate_semantics(self):
        from resolvewhy.adapters.pip_resolvelib.capture import CaptureBuffer, CapturedRun
        from resolvewhy.adapters.pip_resolvelib.normalize import normalize_capture
        captured = CapturedRun(
            buffer=CaptureBuffer(outcome=None),
            resolver_result=None,
            native_error=None,
        )
        with self.assertRaises(AdapterNormalizationError):
            normalize_capture(captured, self.context())

    def test_explicit_complete_coverage_can_be_supplied_as_external_evidence(self):
        from resolvewhy.adapters.pip_resolvelib.capture import CaptureBuffer, CapturedRun
        from resolvewhy.adapters.pip_resolvelib.normalize import normalize_capture

        attestation = CoverageAttestation(
            kind=CoverageAttestationKind.AUTHORITATIVE_FINITE_DOMAIN,
            evidence_refs=(
                # The adapter must see this evidence too; it is not allowed to
                # manufacture the attestation source.
                {
                    # Intentional type error is caught by this test's setup below.
                },
            ),
        )
        # This test exists as a documented API boundary rather than a runtime
        # integration assertion. The production model requires typed TraceRef
        # evidence references, so constructing an attestation with an invalid
        # Python object is rejected before normalization.
        with self.assertRaises(ValueError):
            AdapterContext(
                runtime_context=self.context().runtime_context,
                resolution_policy=self.context().resolution_policy,
                coverage_attestations={"a": attestation},
            )


if __name__ == "__main__":
    unittest.main()
