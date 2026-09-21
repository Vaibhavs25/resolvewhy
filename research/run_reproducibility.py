#!/usr/bin/env python3
"""Deterministic research reproducibility suite.

No network, package index, native resolver, or undeclared external state is
required. The suite checks the committed finite fixture verifier and the
committed projection-search implementation. Historical source-analysis and
public-issue claims are not freshly re-executed here.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERIFIER = ROOT / "trace_only_verifier.py"
COLLISION = ROOT / "portable_core_collision_search.py"

EXPECTED_CORPUS = {
    "RW-01": "VERIFIED_UNSAT",
    "RW-02": "VERIFIED_SAT",
    "RW-03": "INSUFFICIENT_EVIDENCE",
    "RW-04": "INSUFFICIENT_EVIDENCE",
    "RW-05": "INSUFFICIENT_EVIDENCE",
    "RW-06": "INSUFFICIENT_EVIDENCE",
    "RW-07": "INSUFFICIENT_EVIDENCE",
    "RW-08": "INSUFFICIENT_EVIDENCE",
    "RW-09": "VERIFIED_UNSAT",
    "RW-10": "INSUFFICIENT_EVIDENCE",
    "RW-11": "INSUFFICIENT_EVIDENCE",
    "RW-12": "INSUFFICIENT_EVIDENCE",
    "RW-13": "INSUFFICIENT_EVIDENCE",
    "RW-14": "VERIFIED_UNSAT",
    "RW-15": "VERIFIED_UNSAT",
    "RW-16": "VERIFIED_UNSAT",
    "RW-17": "VERIFIED_UNSAT",
    "RW-18": "VERIFIED_SAT",
}


def load_verifier():
    ns = {}
    exec(VERIFIER.read_text(encoding="utf-8"), ns)
    return ns


def load_collision():
    ns = {}
    exec(COLLISION.read_text(encoding="utf-8"), ns)
    return ns


def check_assert(name: str, cond: bool) -> None:
    if not cond:
        raise AssertionError(name)


def corpus_fixture(name: str, v: dict):
    # The committed verifier currently has one explicit finite fixture.
    # The 18-case trace-only corpus is represented in the research record,
    # not as 18 independently materialized JSON fixtures in this repository.
    if name == "fixture":
        return v["base_trace"]()
    raise KeyError(name)


def run():
    v = load_verifier()
    c = load_collision()

    # Core executable checks.
    t = v["base_trace"]()
    check_assert("base verdict", v["verify"](t)[0] == "VERIFIED_UNSAT")

    rt = json.loads(json.dumps(t, sort_keys=True))
    check_assert("round trip", v["verify"](t) == v["verify"](rt))

    base, deletions = v["minimality"](t)
    check_assert("minimality baseline", base)
    check_assert("minimality deletion 1", any(x[1] == "VERIFIED_SAT" for x in deletions))
    check_assert("minimality exercised", len(deletions) == 3)

    expected_mutations = {
        "coverage_attestation": "INVALID_TRACE",
        "evaluation_domain": "INVALID_TRACE",
        "resolution_policy": "INVALID_TRACE",
        "candidate_identity": "INVALID_TRACE",
        "provenance": "INVALID_TRACE",
        "dependency_semantics": "INVALID_TRACE",
        "candidate_coverage": "INSUFFICIENT_EVIDENCE",
        "dangling_ref": "INVALID_TRACE",
        "evidence_state": "INSUFFICIENT_EVIDENCE",
    }
    for name, expected in expected_mutations.items():
        got = v["verify"](v["mutate"](t, name))[0]
        check_assert(f"mutation {name}", got == expected)

    # Deterministic 250-case mutation campaign. Each case is a distinct
    # mutation instance across the taxonomy; duplicates are prohibited.
    taxonomy = [
        ("ids", "candidate_identity"),
        ("references", "dangling_ref"),
        ("arrays", "candidate_coverage"),
        ("evaluation_domain", "evaluation_domain"),
        ("quantifiers", "quantifier"),
        ("coverage_attestation", "coverage_attestation"),
        ("provenance", "provenance"),
        ("candidate_artifact_links", "candidate_artifact_link"),
        ("dependency_references", "dependency_reference"),
        ("proof_premises", "proof_premise_reference"),
        ("evidence_states", "evidence_state"),
    ]
    # The finite verifier has a narrow mutation primitive. To keep the campaign
    # meaningful rather than repeating one mutation, construct deterministic
    # instances by applying different field-specific corruptions to independent
    # deep copies. Every generated record has a unique mutation signature.
    mutations = []
    for i in range(250):
        case = copy.deepcopy(t)
        fam, primitive = taxonomy[i % len(taxonomy)]
        variant = i // len(taxonomy)
        if primitive == "candidate_identity":
            case["candidates"][variant % len(case["candidates"])]["id"] = None
        elif primitive == "dangling_ref":
            case["dependencies"][0]["parent_candidate"] = f"missing-{variant}"
        elif primitive == "candidate_coverage":
            case["candidate_domains"][0]["coverage"]["status"] = "partial" if variant % 2 == 0 else "unknown"
        elif primitive == "evaluation_domain":
            case["evaluation_domain"][0]["id"] = f"env-corrupt-{variant}"
        elif primitive == "quantifier":
            case["proof_claim"]["quantifier"] = ["existential", "universal", "branch", "MISSING"][variant % 4]
        elif primitive == "coverage_attestation":
            if variant % 2 == 0:
                case["candidate_domains"][0]["coverage"].pop("attestation", None)
            else:
                case["candidate_domains"][0]["coverage"]["attestation"]["evidence_refs"] = [f"missing-{variant}"]
        elif primitive == "provenance":
            if variant % 2 == 0:
                case["provenance"] = []
            else:
                case["provenance"][0]["premise_refs"] = [f"missing-{variant}"]
        elif primitive == "candidate_artifact_link":
            case["artifacts"][0]["candidate_ref"] = f"missing-candidate-{variant}"
        elif primitive == "dependency_reference":
            case["dependencies"][0]["parent_candidate"] = f"missing-dependency-{variant}"
        elif primitive == "proof_premise_reference":
            case["proof_claim"]["premise_refs"] = [f"missing-premise-{variant}"]
        elif primitive == "evidence_state":
            states = ["unknown", "incomplete", "missing"]
            case["evidence_state"]["overall"] = states[variant % len(states)]
        signature = json.dumps(case, sort_keys=True, separators=(",", ":"))
        mutations.append((i, fam, primitive, signature, v["verify"](case)[0]))
    check_assert("250 unique mutations", len({m[3] for m in mutations}) == 250)
    false_accepts = sum(1 for m in mutations if m[4] in {"VERIFIED_SAT", "VERIFIED_UNSAT"})
    check_assert("mutation false accepts", false_accepts == 0)

    # Branch-selector semantics are not implemented in the committed verifier;
    # assert the documented conservative outcome rather than overclaim it.
    branch_case = copy.deepcopy(t)
    branch_case["trace_scope"] = "branch"
    branch_case["proof_claim"]["quantifier"] = "branch"
    check_assert("branch is conservative", v["verify"](branch_case)[0] == "INSUFFICIENT_EVIDENCE")

    # Projection search.
    worlds, raw, repaired, unique = c["collision_search"]()
    check_assert("projection worlds", worlds == 64)
    check_assert("post-repair collisions", repaired == 0)
    check_assert("native deletion", c["native_deletion_check"]() is True)

    # Hermetic child-process replay: run the verifier with isolated mode and
    # no proxy/PYTHONPATH variables.
    with tempfile.TemporaryDirectory(prefix="resolvewhy-repro-") as td:
        isolated = Path(td) / "verifier.py"
        isolated.write_text(VERIFIER.read_text(encoding="utf-8"), encoding="utf-8")
        env = {k: val for k, val in dict(__import__("os").environ).items()
               if k not in {"PYTHONPATH", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}}
        p = subprocess.run([sys.executable, "-I", str(isolated)],
                           cwd=td, env=env, capture_output=True, text=True)
        check_assert("hermetic rc", p.returncode == 0)

    print("REPRODUCIBILITY SUITE")
    print("EXECUTABLE_VERIFIER_SCOPE = finite fixture fragment")
    print("TRACE_ONLY_CORPUS = historical_claim_only (18/18 is not regenerated by this runner)")
    print("SERIALIZATION_ROUNDTRIP = 1/1")
    print("HERMETIC_REPLAY = 1/1")
    print("SUBSET_MINIMAL_PROOFS = 1 executable fixture (historical corpus record: 2)")
    print(f"MUTATION_CASES = {len(mutations)}")
    print(f"MUTATION_FALSE_ACCEPTS = {false_accepts}")
    print(f"PROJECTION_WORLDS = {worlds}")
    print(f"POST_REPAIR_COLLISIONS = {repaired}")


if __name__ == "__main__":
    run()
