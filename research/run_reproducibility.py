#!/usr/bin/env python3
"""Deterministic research reproducibility suite.

The suite regenerates the executable finite verifier checks and the current
projection search. The historical 18-case and 256-world figures remain
research-record figures unless corresponding fixtures/harnesses are committed.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERIFIER = ROOT / "trace_only_verifier.py"
COLLISION = ROOT / "portable_core_collision_search.py"


def load_module(path: Path):
    ns = {}
    exec(path.read_text(encoding="utf-8"), ns)
    return ns


def require(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)


def mutation_campaign(v):
    base = v["base_trace"]()
    taxonomy = [
        "ids", "references", "arrays", "evaluation_domain", "quantifiers",
        "coverage_attestation", "provenance", "candidate_artifact_links",
        "dependency_references", "proof_premises", "evidence_states",
    ]
    results = []
    # 11 mutation families x 22 variants = 242, plus 8 targeted cases = 250.
    for i in range(242):
        case = copy.deepcopy(base)
        fam = taxonomy[i % len(taxonomy)]
        variant = i // len(taxonomy)
        if fam == "ids":
            target = case["candidates"][variant % len(case["candidates"])]
            target["id"] = None
            target["package"] = f"corrupt-package-{variant}"
        elif fam in {"references", "dependency_references"}:
            case["dependencies"][0]["parent_candidate"] = f"missing-{variant}"
        elif fam == "arrays":
            case["candidate_domains"][0]["candidate_ids"] = [f"ghost-array-{variant}"]
        elif fam == "evaluation_domain":
            case["evaluation_domain"][0]["id"] = f"env-corrupt-{variant}"
        elif fam == "quantifiers":
            case["proof_claim"]["quantifier"] = ["existential", "universal", "branch", "invalid"][variant % 4]
            case["proof_claim"]["evaluation_domain_ref"] = f"missing-domain-{variant}"
        elif fam == "coverage_attestation":
            if variant % 2 == 0:
                case["candidate_domains"][0]["coverage"].pop("attestation", None)
            else:
                case["candidate_domains"][0]["coverage"]["attestation"]["evidence_refs"] = [f"missing-{variant}"]
        elif fam == "provenance":
            if variant % 2 == 0:
                case["provenance"] = []
            else:
                case["provenance"][0]["premise_refs"] = [f"missing-{variant}"]
        elif fam == "candidate_artifact_links":
            case["artifacts"][0]["candidate_ref"] = f"missing-candidate-{variant}"
        elif fam == "proof_premises":
            case["proof_claim"]["premise_refs"] = [f"missing-premise-{variant}"]
        elif fam == "evidence_states":
            case["evidence_state"]["overall"] = ["unknown", "incomplete", "missing"][variant % 3]
            case["evidence_state"]["mutation_ref"] = f"evidence-{variant}"
        raw = json.dumps(case, sort_keys=True, separators=(",", ":"))
        results.append((i, fam, raw, v["verify"](case)[0]))
    extras = []
    for j in range(8):
        case = copy.deepcopy(base)
        mode = j % 4
        if mode == 0:
            case["proof_claim"]["premise_refs"] = ["c:missing"]
        elif mode == 1:
            case["proof_claim"]["evaluation_domain_ref"] = f"missing-domain-{j}"
        elif mode == 2:
            case["trace_scope"] = "universal"
            case["proof_claim"]["quantifier"] = "existential"
        else:
            case["candidate_domains"][0]["coverage"]["attestation"]["evidence_refs"] = [f"missing-extra-{j}"]
        raw = json.dumps(case, sort_keys=True, separators=(",", ":"))
        extras.append((242+j, "targeted", raw, v["verify"](case)[0]))
    results.extend(extras)
    require("250 distinct mutation instances", len({x[2] for x in results}) == 250)
    false_accepts = sum(r[3] in {"VERIFIED_SAT", "VERIFIED_UNSAT"} for r in results)
    require("zero mutation false accepts", false_accepts == 0)
    require("proof-premise mutation family executed", "proof_premises" in {x[1] for x in results})
    families={x[1] for x in results}
    require("mutation taxonomy coverage", set(taxonomy).issubset(families))
    family_counts={fam:sum(x[1]==fam for x in results) for fam in taxonomy}
    require("22 instances per primary family", all(n==22 for n in family_counts.values()))
    return len(results), false_accepts, family_counts


def run():
    v = load_module(VERIFIER)
    c = load_module(COLLISION)

    base = v["base_trace"]()
    require("base UNSAT", v["verify"](base)[0] == "VERIFIED_UNSAT")

    # SAT negative control: the same fixture with its transitive dependency removed.
    sat = v["sat_fixture"]()
    require("SAT reconstruction", v["verify"](sat)[0] == "VERIFIED_SAT")

    roundtrip = json.loads(json.dumps(base, sort_keys=True))
    require("serialization roundtrip", v["verify"](base) == v["verify"](roundtrip))

    minimal, deletion_results = v["minimality"](base)
    require("subset-minimal baseline", minimal)
    require("declared core size", len(base["claimed_core"]) == 2)
    require("all declared core deletion checks executed", len(deletion_results) == len(base["claimed_core"]))
    require("deletions become SAT", all(x[1] == "VERIFIED_SAT" for x in deletion_results))
    require("reported core size", len(v["base_trace"]().get("claimed_core", [])) == 2)

    # Declared claim status is deliberately non-authoritative: the verifier recomputes truth.
    disagreement = copy.deepcopy(base)
    disagreement["proof_claim"]["status_claim"] = "SAT"
    require("resolver-label disagreement", v["verify"](disagreement)[0] == "VERIFIED_UNSAT")

    omitted = copy.deepcopy(base)
    omitted["proof_claim"]["premise_refs"] = ["c:root"]
    require("omitted semantic premise changes proposition", v["verify"](omitted)[0] == "VERIFIED_SAT")

    unrelated = copy.deepcopy(base)
    unrelated["proof_claim"]["premise_refs"] = ["c:not-real"]
    require("unrelated premise rejected", v["verify"](unrelated)[0] == "INVALID_TRACE")

    expected = {
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
    for name, wanted in expected.items():
        require(f"mutation {name}", v["verify"](v["mutate"](base, name))[0] == wanted)

    mutation_cases, mutation_false_accepts, mutation_family_counts = mutation_campaign(v)

    branch = copy.deepcopy(base)
    branch["trace_scope"] = "branch"
    branch["proof_claim"]["quantifier"] = "branch"
    require("branch conservative", v["verify"](branch)[0] == "INSUFFICIENT_EVIDENCE")

    worlds, raw_collisions, repaired_collisions, _ = c["collision_search"]()
    require("historical raw collision family preserved", raw_collisions >= 1)
    require("projection harness has 64 worlds", worlds == 64)
    require("post-repair collisions zero", repaired_collisions == 0)
    require("native deletion preserves truth", c["native_deletion_check"]() is True)

    with tempfile.TemporaryDirectory(prefix="resolvewhy-repro-") as td:
        td = Path(td)
        isolated = td / "verifier.py"
        isolated.write_text(VERIFIER.read_text(encoding="utf-8"), encoding="utf-8")
        env = {k: val for k, val in os.environ.items()
               if k not in {"PYTHONPATH", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}}
        p = subprocess.run([sys.executable, "-I", str(isolated)],
                           cwd=td, env=env, capture_output=True, text=True)
        require("hermetic child process", p.returncode == 0)

    print("REPRODUCIBILITY SUITE")
    print("EXECUTABLE_VERIFIER_SCOPE = finite fixture fragment")
    print("TRACE_ONLY_CORPUS = historical 18-case record (not regenerated here)")
    print(f"SERIALIZATION_ROUNDTRIP = 1/1")
    print(f"HERMETIC_REPLAY = 1/1")
    print("SUBSET_MINIMAL_PROOFS = 1 executable fixture (historical full-corpus record: 2)")
    print(f"MUTATION_CASES = {mutation_cases}")
    print(f"MUTATION_FALSE_ACCEPTS = {mutation_false_accepts}")
    print(f"MUTATION_FAMILY_COUNTS = {mutation_family_counts}")
    print(f"PROJECTION_WORLDS = {worlds}")
    print(f"POST_REPAIR_COLLISIONS = {repaired_collisions}")
    print(f"RAW_PRE_REPAIR_COLLISIONS = {raw_collisions}")


if __name__ == "__main__":
    run()
