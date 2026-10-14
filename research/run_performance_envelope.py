"""Bounded, reproducible local measurements for the documented envelope.

This is not a benchmark suite or service-level objective. It records the local
runtime and Python allocator peak for representative supported operations and
asserts that a deliberately exhausted evaluation budget fails closed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from resolvewhy.model import (
    Candidate,
    CandidateCoverage,
    CandidateDomain,
    CandidateDomainScope,
    CandidateKind,
    CoverageAttestation,
    CoverageAttestationKind,
    CoverageStatus,
    DependencyEdge,
    EvidenceObservation,
    EvidenceState,
    EvidenceStateKind,
    ProofQuantifier,
    ReferenceKind,
    Requirement,
    ResolutionPolicy,
    RuntimeContext,
    SemanticConstraint,
    SemanticConstraintKind,
    SemanticLiteral,
    TraceRef,
    VersionConstraint,
)
from resolvewhy.solving.problem import SemanticProblem
from resolvewhy.solving.semantics import EvaluationLimit, evaluate_branch
from resolvewhy.solving.solver import SolveStatus, solve
from resolvewhy.trace import (
    MAX_JSON_DEPTH,
    MAX_JSON_NODES,
    MAX_TRACE_BYTES,
    deserialize_trace,
)
from resolvewhy.verification import verify

FIXTURE = ROOT / "tests" / "fixtures" / "production_trace.json"
GRAPH_PACKAGES = 32


def measure(operation):
    tracemalloc.start()
    start = time.perf_counter()
    value = operation()
    elapsed_ms = round((time.perf_counter() - start) * 1_000, 3)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return value, {"elapsed_ms": elapsed_ms, "python_peak_bytes": peak}


def dependency_problem() -> SemanticProblem:
    context = RuntimeContext(
        id="env:performance",
        python_implementation="CPython",
        python_version="3.12",
        os="linux",
        architecture="x86_64",
    )
    policy = ResolutionPolicy(
        id="policy:performance",
        prerelease_mode="disallow",
        universal_strategy="single",
    )
    requirements = []
    candidates = []
    domains = []
    dependencies = []
    constraints = []
    observations = []
    for index in range(GRAPH_PACKAGES):
        package = f"pkg{index}"
        requirement = Requirement(
            id=f"req:{package}",
            package=package,
            constraint=VersionConstraint("==", "1.0"),
            parent_candidate_ref=(f"cand:pkg{index - 1}" if index else None),
            evidence_refs=(TraceRef(ReferenceKind.EVIDENCE, f"obs:{package}"),),
        )
        candidate = Candidate(
            id=f"cand:{package}",
            package=package,
            version="1.0",
            kind=CandidateKind.REGISTRY,
            source_ref="index:performance",
        )
        requirements.append(requirement)
        candidates.append(candidate)
        domains.append(
            CandidateDomain(
                id=f"domain:{package}",
                identifier=package,
                requirement_refs=(requirement.id,),
                candidate_refs=(candidate.id,),
                scope=CandidateDomainScope(sources=("index:performance",)),
                runtime_context_ref=context.id,
                resolution_policy_ref=policy.id,
                coverage=CandidateCoverage(
                    CoverageStatus.COMPLETE,
                    attestation=CoverageAttestation(
                        CoverageAttestationKind.AUTHORITATIVE_FINITE_DOMAIN,
                        (TraceRef(ReferenceKind.EVIDENCE, f"obs:coverage:{package}"),),
                    ),
                ),
            )
        )
        observations.append(
            EvidenceObservation(
                id=f"obs:{package}",
                kind="performance-fixture",
                state=EvidenceStateKind.KNOWN_FACT,
                supports_refs=(),
                source_namespace="performance",
            )
        )
        observations.append(
            EvidenceObservation(
                id=f"obs:coverage:{package}",
                kind="authoritative-finite-domain",
                state=EvidenceStateKind.KNOWN_FACT,
                supports_refs=(
                    TraceRef(ReferenceKind.CANDIDATE_DOMAIN, f"domain:{package}"),
                ),
                source_namespace="performance",
            )
        )
        if index:
            dependencies.append(
                DependencyEdge(
                    id=f"dep:pkg{index - 1}:pkg{index}",
                    parent_candidate_ref=f"cand:pkg{index - 1}",
                    requirement_ref=requirement.id,
                    evidence_refs=(TraceRef(ReferenceKind.EVIDENCE, f"obs:{package}"),),
                    source_namespace="performance",
                )
            )
        constraints.append(
            SemanticConstraint(
                id=f"constraint:{package}",
                kind=(
                    SemanticConstraintKind.REQUIREMENT
                    if index == 0
                    else SemanticConstraintKind.DEPENDENCY
                ),
                literals=(
                    SemanticLiteral(
                        kind=(
                            SemanticConstraintKind.REQUIREMENT
                            if index == 0
                            else SemanticConstraintKind.DEPENDENCY
                        ),
                        package=package,
                        candidate_ref=(f"cand:pkg{index - 1}" if index else None),
                        operator="==",
                        value="1.0",
                    ),
                ),
                source_refs=(TraceRef(ReferenceKind.EVIDENCE, f"obs:{package}"),),
            )
        )
    return SemanticProblem(
        requirements=tuple(requirements),
        candidates=tuple(candidates),
        artifacts=(),
        dependencies=tuple(dependencies),
        candidate_domains=tuple(domains),
        semantic_constraints=tuple(constraints),
        runtime_contexts=(context,),
        resolution_policy=policy,
        evidence_state=EvidenceState(
            EvidenceStateKind.KNOWN_FACT,
            tuple(observations),
        ),
        quantifier=ProofQuantifier.EXISTENTIAL,
    )


def run() -> dict[str, object]:
    fixture = FIXTURE.read_bytes()
    trace, fixture_measurement = measure(lambda: deserialize_trace(fixture))
    result, verification_measurement = measure(lambda: verify(trace))
    if not result.is_verified:
        raise AssertionError(
            f"fixture verification unexpectedly returned {result.status.value}"
        )

    padded = b" " * (MAX_TRACE_BYTES - len(fixture)) + fixture
    _, near_limit_measurement = measure(lambda: deserialize_trace(padded))

    problem = dependency_problem()
    solve_result, graph_measurement = measure(lambda: solve(problem))
    if solve_result.status is not SolveStatus.SAT:
        raise AssertionError(
            f"performance graph unexpectedly returned {solve_result.status.value}"
        )

    try:
        evaluate_branch(
            problem,
            problem.semantic_constraints,
            problem.runtime_contexts[0],
            max_states=0,
        )
    except EvaluationLimit as exc:
        if exc.code != "evaluation_search_limit":
            raise AssertionError(f"unexpected limit code {exc.code}") from exc
    else:
        raise AssertionError("exhausted evaluation budget was accepted")

    return {
        "fixture_bytes": len(fixture),
        "near_limit_payload_bytes": len(padded),
        "dependency_graph": {
            "packages": GRAPH_PACKAGES,
            "dependency_edges": GRAPH_PACKAGES - 1,
            "candidates": GRAPH_PACKAGES,
            "status": solve_result.status.value,
        },
        "configured_limits": {
            "max_trace_bytes": MAX_TRACE_BYTES,
            "max_json_depth": MAX_JSON_DEPTH,
            "max_json_nodes": MAX_JSON_NODES,
            "branch_search_states": 100_000,
            "limit_exhaustion_result": "evaluation_search_limit",
        },
        "measurements": {
            "fixture_decode": fixture_measurement,
            "fixture_verify": verification_measurement,
            "near_limit_decode": near_limit_measurement,
            "dependency_graph_solve": graph_measurement,
        },
        "resource_limit_behavior": "PASS: zero-state evaluation budget raised evaluation_search_limit",
        "scope": "local sample only; not a throughput or latency guarantee",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json", action="store_true", help="print machine-readable output"
    )
    args = parser.parse_args()
    summary = run()
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
