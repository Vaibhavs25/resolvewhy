from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verifier = load("resolvewhy_test_verifier", "trace_only_verifier.py")
collision = load("resolvewhy_test_collision", "portable_core_collision_search.py")
runner = load("resolvewhy_test_runner", "run_reproducibility.py")


class TraceOnlyTests(unittest.TestCase):
    def setUp(self):
        self.base = verifier.base_trace()

    def test_sat_reconstruction(self):
        self.assertEqual(verifier.verify(verifier.sat_fixture())[0], "VERIFIED_SAT")

    def test_unsat_reconstruction(self):
        self.assertEqual(verifier.verify(self.base)[0], "VERIFIED_UNSAT")

    def test_subset_minimality(self):
        ok, checks = verifier.minimality(self.base)
        self.assertTrue(ok)
        self.assertEqual([result for _, result in checks], ["VERIFIED_SAT"] * 4)

    def test_serialization_roundtrip(self):
        roundtrip = json.loads(json.dumps(self.base, sort_keys=True))
        self.assertEqual(verifier.verify(self.base), verifier.verify(roundtrip))

    def test_dangling_references(self):
        self.assertEqual(verifier.verify(verifier.mutate(self.base, "dangling_ref"))[0], "INVALID_TRACE")

    def test_duplicate_ids(self):
        trace = copy.deepcopy(self.base)
        trace["candidates"].append(copy.deepcopy(trace["candidates"][0]))
        self.assertEqual(verifier.verify(trace)[0], "INVALID_TRACE")

    def test_missing_coverage_attestation(self):
        self.assertEqual(verifier.verify(verifier.mutate(self.base, "coverage_attestation"))[0], "INVALID_TRACE")

    def test_incomplete_candidate_coverage(self):
        self.assertEqual(verifier.verify(verifier.mutate(self.base, "candidate_coverage"))[0], "INSUFFICIENT_EVIDENCE")

    def test_malformed_proof_claim(self):
        trace = copy.deepcopy(self.base)
        trace["proof_claim"] = "invalid"
        self.assertEqual(verifier.verify(trace)[0], "INVALID_TRACE")

    def test_missing_quantifier(self):
        trace = copy.deepcopy(self.base)
        trace["proof_claim"]["quantifier"] = None
        self.assertEqual(verifier.verify(trace)[0], "INVALID_TRACE")

    def test_missing_evaluation_domain(self):
        self.assertEqual(verifier.verify(verifier.mutate(self.base, "evaluation_domain"))[0], "INVALID_TRACE")

    def test_invalid_proof_premise_reference(self):
        trace = copy.deepcopy(self.base)
        trace["proof_claim"]["premise_refs"] = ["missing-premise"]
        trace["claimed_core"] = ["missing-premise"]
        self.assertEqual(verifier.verify(trace)[0], "INVALID_TRACE")

    def test_proof_premise_omission_changes_proposition(self):
        trace = copy.deepcopy(self.base)
        trace["proof_claim"]["premise_refs"] = ["c:root:a"]
        trace["claimed_core"] = ["c:root:a"]
        self.assertEqual(verifier.verify(trace)[0], "VERIFIED_SAT")

    def test_provenance_missing(self):
        trace = copy.deepcopy(self.base)
        trace["provenance"] = []
        self.assertEqual(verifier.verify(trace)[0], "INVALID_TRACE")

    def test_provenance_unrelated_evidence(self):
        trace = copy.deepcopy(self.base)
        trace["provenance"][0]["evidence_refs"] = ["obs:domain:x"]
        self.assertEqual(verifier.verify(trace)[0], "INVALID_TRACE")

    def test_provenance_dangling_reference(self):
        trace = copy.deepcopy(self.base)
        trace["provenance"][0]["evidence_refs"] = ["missing-evidence"]
        self.assertEqual(verifier.verify(trace)[0], "INVALID_TRACE")

    def test_provenance_cycle(self):
        trace = copy.deepcopy(self.base)
        trace["provenance"] = [
            {"id": "p1", "premise_refs": ["p2"], "evidence_refs": ["obs:req:a"]},
            {"id": "p2", "premise_refs": ["p1"], "evidence_refs": ["obs:req:b"]},
            {"id": "p3", "premise_refs": ["c:root:a"], "evidence_refs": ["obs:req:a"]},
            {"id": "p4", "premise_refs": ["c:root:b"], "evidence_refs": ["obs:req:b"]},
            {"id": "p5", "premise_refs": ["c:dep:a-x"], "evidence_refs": ["obs:dep:a"]},
            {"id": "p6", "premise_refs": ["c:dep:b-x"], "evidence_refs": ["obs:dep:b"]},
        ]
        self.assertEqual(verifier.verify(trace)[0], "INVALID_TRACE")

    def test_incomplete_proof_evidence(self):
        trace = copy.deepcopy(self.base)
        trace["evidence_state"]["overall"] = "unknown"
        self.assertEqual(verifier.verify(trace)[0], "INSUFFICIENT_EVIDENCE")

    def test_activation_marker_preserved(self):
        trace = copy.deepcopy(self.base)
        trace["dependencies"][0]["activation_condition"] = False
        trace["dependencies"][1]["activation_condition"] = False
        trace["proof_claim"]["status_claim"] = "SAT"
        self.assertEqual(verifier.verify(trace)[0], "VERIFIED_SAT")

    def test_activation_nested_and_or(self):
        self.assertEqual(verifier.verify(self.base)[0], "VERIFIED_UNSAT")

    def test_resolver_status_label_is_non_authoritative(self):
        trace = copy.deepcopy(self.base)
        trace["proof_claim"]["status_claim"] = "SAT"
        self.assertEqual(verifier.verify(trace)[0], "VERIFIED_UNSAT")

    def test_artifact_feasibility(self):
        self.assertEqual(verifier.verify(verifier.rw15_fixture())[0], "VERIFIED_UNSAT")
        trace = copy.deepcopy(verifier.rw15_fixture())
        trace["artifacts"][0]["compatible"] = True
        trace["proof_claim"]["status_claim"] = "SAT"
        self.assertEqual(verifier.verify(trace)[0], "VERIFIED_SAT")

    def test_policy_prerelease_changes_result(self):
        trace = verifier.prerelease_fixture()
        self.assertEqual(verifier.verify(trace)[0], "VERIFIED_UNSAT")
        trace["resolution_policy"]["prerelease"] = "allow"
        trace["proof_claim"]["status_claim"] = "SAT"
        self.assertEqual(verifier.verify(trace)[0], "VERIFIED_SAT")

    def test_branch_scope(self):
        trace = copy.deepcopy(self.base)
        trace["trace_scope"] = "branch"
        trace["proof_claim"]["quantifier"] = "branch"
        trace["proof_claim"]["branch_ref"] = "env:linux"
        self.assertEqual(verifier.verify(trace)[0], "VERIFIED_UNSAT")

        corpus = verifier.corpus_cases()
        rw09 = next(x["trace"] for x in corpus if x["case_id"] == "RW-09")
        rw09["trace_scope"] = "branch"
        rw09["proof_claim"]["quantifier"] = "branch"
        rw09["proof_claim"]["branch_ref"] = "env:py3.12"
        self.assertEqual(verifier.verify(rw09)[0], "VERIFIED_SAT")
        rw09["proof_claim"]["branch_ref"] = "env:py3.9"
        rw09["proof_claim"]["status_claim"] = "UNSAT"
        self.assertEqual(verifier.verify(rw09)[0], "VERIFIED_UNSAT")

    def test_candidate_artifact_links_and_source_identity(self):
        rw18 = next(x["trace"] for x in verifier.corpus_cases() if x["case_id"] == "RW-18")
        self.assertEqual(verifier.verify(rw18)[0], "VERIFIED_SAT")
        bad = copy.deepcopy(rw18)
        bad["artifacts"][0]["candidate_ref"] = "missing"
        self.assertEqual(verifier.verify(bad)[0], "INVALID_TRACE")

    def test_18_case_classifications(self):
        results = verifier.corpus_cases()
        self.assertEqual(len(results), 18)
        expected = {x["case_id"]: x["expected_result"] for x in results}
        observed = {x["case_id"]: verifier.verify(x["trace"])[0] for x in results}
        self.assertEqual(observed, expected)

    def test_coverage_mutation_campaign(self):
        _, false_accepts, counts, taxonomy = runner.mutation_campaign(verifier)
        self.assertEqual(false_accepts, 0)
        self.assertEqual(sum(counts.values()), 250)
        self.assertEqual(sum(taxonomy.values()), 250)
        self.assertTrue(set([
            "ids", "references", "arrays", "evaluation_domain", "quantifiers",
            "coverage_attestation", "provenance", "candidate_artifact_links",
            "dependency_references", "proof_premises", "evidence_states",
        ]).issubset(taxonomy))

    def test_projection_search_256(self):
        worlds, raw, repaired, _ = collision.collision_search()
        self.assertEqual(worlds, 256)
        self.assertGreater(raw, 0)
        self.assertEqual(repaired, 0)
        self.assertTrue(collision.native_deletion_check())


if __name__ == "__main__":
    unittest.main()
