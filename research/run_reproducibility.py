from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
VERIFIER_PATH = HERE / "trace_only_verifier.py"
COLLISION_PATH = HERE / "portable_core_collision_search.py"

def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def require(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)


def load_corpus(verifier) -> list[dict]:
    data = verifier.corpus_cases()
    require("18 corpus fixtures", isinstance(data, list) and len(data) == 18)
    case_ids = [entry.get("case_id") for entry in data]
    require("unique corpus IDs", len(case_ids) == len(set(case_ids)))
    return data


def mutation_campaign(verifier):
    base = verifier.base_trace()
    families = [
        "ids", "references", "arrays", "evaluation_domain", "quantifiers",
        "coverage_attestation", "provenance", "candidate_artifact_links",
        "dependency_references", "proof_premises", "evidence_states",
    ]
    results = []

    # 11 families x 22 deterministic variants = 242.
    for i in range(242):
        trace = copy.deepcopy(base)
        family = families[i % len(families)]
        variant = i // len(families)

        if family == "ids":
            idx = variant % len(trace["candidates"])
            trace["candidates"][idx]["id"] = f"mutated-candidate-{variant}-{idx}"
        elif family == "references":
            trace["semantic_constraints"][0]["source_ref"] = f"missing-requirement-{variant}"
        elif family == "arrays":
            trace["candidate_domains"][2]["candidate_ids"] = [
                "cand:x1", f"ghost-candidate-{variant}",
            ]
        elif family == "evaluation_domain":
            trace["evaluation_domain"][0]["runtime_context_ref"] = f"missing-context-{variant}"
        elif family == "quantifiers":
            trace["proof_claim"]["quantifier"] = (
                ["existential", "universal", "branch", "invalid"][variant % 4]
            )
            trace["proof_claim"]["evaluation_domain_ref"] = f"missing-domain-{variant}"
            trace["proof_claim"]["branch_ref"] = f"missing-branch-{variant}"
        elif family == "coverage_attestation":
            if variant % 2 == 0:
                trace["candidate_domains"][2]["coverage"].pop("attestation", None)
                trace["candidate_domains"][2]["scope"]["query_id"] = f"query-{variant}"
            else:
                trace["candidate_domains"][2]["coverage"]["attestation"]["evidence_refs"] = [
                    f"missing-evidence-{variant}"
                ]
        elif family == "provenance":
            if variant % 2 == 0:
                trace["provenance"] = [
                    p for p in trace["provenance"] if p["id"] != "prov:root:a"
                ]
                trace["provenance"][0]["evidence_refs"] = [f"missing-evidence-{variant}"]
            else:
                trace["provenance"][0]["evidence_refs"] = [f"missing-evidence-{variant}"]
        elif family == "candidate_artifact_links":
            trace["artifacts"][0]["candidate_ref"] = f"missing-candidate-{variant}"
        elif family == "dependency_references":
            trace["dependencies"][0]["parent_candidate"] = f"missing-parent-{variant}"
        elif family == "proof_premises":
            trace["proof_claim"]["premise_refs"] = [f"missing-premise-{variant}"]
            trace["claimed_core"] = [f"missing-premise-{variant}"]
        elif family == "evidence_states":
            trace["evidence_state"]["overall"] = (
                ["unknown", "incomplete", "missing"][variant % 3]
            )
            trace["evidence_state"]["observations"].append(
                {"id": f"obs:mutation:{variant}", "kind": "mutation", "supports_refs": []}
            )

        results.append({
            "index": i,
            "family": family,
            "serialized": json.dumps(trace, sort_keys=True, separators=(",", ":")),
            "result": verifier.verify(trace)[0],
        })

    targeted_names = [
        "targeted_dangling_premise", "targeted_domain_binding",
        "targeted_scope_mismatch", "targeted_coverage_evidence",
        "targeted_unrelated_provenance", "targeted_wrong_evidence",
        "targeted_malformed_dependency", "targeted_marker_semantics",
    ]
    for j, family in enumerate(targeted_names):
        trace = copy.deepcopy(base)
        if j == 0:
            trace["proof_claim"]["premise_refs"] = ["c:missing"]
            trace["claimed_core"] = ["c:missing"]
        elif j == 1:
            trace["proof_claim"]["evaluation_domain_ref"] = "missing-domain"
        elif j == 2:
            trace["trace_scope"] = "universal"
            trace["proof_claim"]["quantifier"] = "existential"
        elif j == 3:
            trace["candidate_domains"][0]["coverage"]["attestation"]["evidence_refs"] = [
                "missing-attestation-evidence"
            ]
        elif j == 4:
            trace["provenance"][0]["premise_refs"] = ["c:root:b"]
        elif j == 5:
            trace["provenance"][0]["evidence_refs"] = ["obs:domain:x"]
        elif j == 6:
            trace["dependencies"][0]["requirement"]["version"] = None
        elif j == 7:
            trace["dependencies"][0]["activation_condition"] = {
                "variable": "sys_platform", "op": "???", "value": "linux"
            }
        results.append({
            "index": 242 + j,
            "family": family,
            "serialized": json.dumps(trace, sort_keys=True, separators=(",", ":")),
            "result": verifier.verify(trace)[0],
        })

    require("exactly 250 mutation cases", len(results) == 250)
    require("250 distinct serialized mutations", len({r["serialized"] for r in results}) == 250)
    false_accepts = sum(r["result"] in {"VERIFIED_SAT", "VERIFIED_UNSAT"} for r in results)
    require("zero mutation false accepts", false_accepts == 0)
    families_seen = {r["family"] for r in results}
    require("all mutation families exercised", set(families).issubset(families_seen))

    counts: dict[str, int] = {}
    taxonomy: dict[str, int] = {}
    for row in results:
        counts[row["result"]] = counts.get(row["result"], 0) + 1
        taxonomy[row["family"]] = taxonomy.get(row["family"], 0) + 1

    return results, false_accepts, counts, taxonomy


def isolated_verify(verifier_source: str, trace: dict) -> str:
    with tempfile.TemporaryDirectory(prefix="resolvewhy-hermetic-") as td:
        temp = Path(td)
        (temp / "verifier.py").write_text(verifier_source, encoding="utf-8")
        (temp / "trace.json").write_text(json.dumps(trace, sort_keys=True), encoding="utf-8")
        worker = temp / "worker.py"
        worker.write_text(
            r'''
import json
import os
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STDLIB = Path(sysconfig.get_paths()["stdlib"]).resolve()

def deny(event, args):
    if event in {"socket.__new__", "socket.connect", "subprocess.Popen", "urllib.Request"}:
        raise RuntimeError(f"forbidden external access: {event}")
    if event == "open":
        target = args[0] if args else None
        if not isinstance(target, (str, bytes, os.PathLike)):
            return
        path = Path(target).resolve()
        allowed = path == ROOT or ROOT in path.parents or path == STDLIB or STDLIB in path.parents
        if not allowed:
            raise RuntimeError(f"filesystem escape: {path}")

sys.addaudithook(deny)
sys.path.insert(0, str(ROOT))
import verifier

trace = json.loads((ROOT / "trace.json").read_text(encoding="utf-8"))
print(verifier.verify(trace)[0])
'''.strip() + "\n",
            encoding="utf-8",
        )
        env = {
            key: value for key, value in os.environ.items()
            if key not in {"PYTHONPATH", "PYTHONHOME", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}
        }
        proc = subprocess.run(
            [sys.executable, "-I", str(worker)],
            cwd=temp, env=env, capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            raise AssertionError("hermetic child failed: " + proc.stderr.strip())
        return proc.stdout.strip()


def run():
    verifier = load_module(VERIFIER_PATH, "resolvewhy_verifier")
    collision = load_module(COLLISION_PATH, "resolvewhy_collision")

    base = verifier.base_trace()
    require("base UNSAT", verifier.verify(base)[0] == "VERIFIED_UNSAT")
    require("SAT fixture", verifier.verify(verifier.sat_fixture())[0] == "VERIFIED_SAT")

    prerelease = verifier.prerelease_fixture()
    require("prerelease disallow", verifier.verify(prerelease)[0] == "VERIFIED_UNSAT")
    prerelease["resolution_policy"]["prerelease"] = "allow"
    require("prerelease allow", verifier.verify(prerelease)[0] == "VERIFIED_SAT")

    branch = copy.deepcopy(base)
    branch["trace_scope"] = "branch"
    branch["proof_claim"]["quantifier"] = "branch"
    branch["proof_claim"]["branch_ref"] = "env:linux"
    require("branch semantics", verifier.verify(branch)[0] == "VERIFIED_UNSAT")

    root_only = copy.deepcopy(base)
    root_only["proof_claim"]["premise_refs"] = ["c:root:a", "c:root:b"]
    root_only["claimed_core"] = root_only["proof_claim"]["premise_refs"]
    require("proof premises affect proposition", verifier.verify(root_only)[0] == "VERIFIED_SAT")

    declared_status = copy.deepcopy(base)
    declared_status["proof_claim"]["status_claim"] = "SAT"
    require("declared status is non-authoritative",
            verifier.verify(declared_status)[0] == "VERIFIED_UNSAT")

    corpus = load_corpus(verifier)
    corpus_results = []
    verifier_source = VERIFIER_PATH.read_text(encoding="utf-8")
    roundtrip_passes = 0
    isolated_passes = 0

    for entry in corpus:
        trace = entry["trace"]
        expected = entry["expected_result"]
        observed = verifier.verify(trace)[0]
        require(f"{entry['case_id']} classification", observed == expected)
        roundtrip = json.loads(json.dumps(trace, sort_keys=True))
        require(f"{entry['case_id']} round-trip", verifier.verify(roundtrip)[0] == observed)
        roundtrip_passes += 1
        require(f"{entry['case_id']} isolated replay", isolated_verify(verifier_source, trace) == observed)
        isolated_passes += 1
        corpus_results.append({"case_id": entry["case_id"], "expected": expected, "observed": observed})

    minimality_results = {}
    for case_id in ("RW-09", "RW-14"):
        trace = next(e["trace"] for e in corpus if e["case_id"] == case_id)
        ok, deletions = verifier.minimality(trace)
        require(f"{case_id} minimality", ok and all(result == "VERIFIED_SAT" for _, result in deletions))
        minimality_results[case_id] = deletions

    mutation_results, mutation_false_accepts, mutation_counts, mutation_taxonomy = mutation_campaign(verifier)

    worlds, raw_collisions, post_repair_collisions, unique_families = collision.collision_search()
    require("projection world count", worlds == 256)
    require("post-repair collision count", post_repair_collisions == 0)
    require("pre-repair collision exists", raw_collisions > 0)
    require("native-state deletion", collision.native_deletion_check())

    summary = {
        "trace_only_corpus": "18/18",
        "serialization_roundtrip": f"{roundtrip_passes}/18",
        "hermetic_replay": f"{isolated_passes}/18",
        "subset_minimal_proofs": 2,
        "subset_minimality_details": minimality_results,
        "mutation_cases": len(mutation_results),
        "mutation_false_accepts": mutation_false_accepts,
        "mutation_verdict_counts": mutation_counts,
        "mutation_taxonomy": mutation_taxonomy,
        "projection_worlds": worlds,
        "raw_pre_repair_collision_groups": raw_collisions,
        "post_repair_collisions": post_repair_collisions,
        "unique_pre_repair_collision_families": unique_families,
        "corpus_results": corpus_results,
    }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="print only JSON")
    parser.add_argument("--write-results", metavar="DIR",
                        help="write reproducibility.json and reproducibility.txt to DIR")
    args = parser.parse_args()
    summary = run()

    human = "\n".join([
        "REPRODUCIBILITY SUITE",
        "TRACE_ONLY_CORPUS = 18/18 (serialized fixture replay; not fresh issue execution)",
        f"SERIALIZATION_ROUNDTRIP = {summary['serialization_roundtrip']}",
        f"HERMETIC_REPLAY = {summary['hermetic_replay']}",
        f"SUBSET_MINIMAL_PROOFS = {summary['subset_minimal_proofs']}",
        f"MUTATION_CASES = {summary['mutation_cases']}",
        f"MUTATION_FALSE_ACCEPTS = {summary['mutation_false_accepts']}",
        f"PROJECTION_WORLDS = {summary['projection_worlds']}",
        f"POST_REPAIR_COLLISIONS = {summary['post_repair_collisions']}",
    ])

    if args.write_results:
        out = Path(args.write_results)
        out.mkdir(parents=True, exist_ok=True)
        (out / "reproducibility.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / "reproducibility.txt").write_text(human + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(human)


if __name__ == "__main__":
    main()
