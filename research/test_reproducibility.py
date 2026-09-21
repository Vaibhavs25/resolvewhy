from __future__ import annotations

import copy
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent

def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

verifier = load("resolvewhy_trace_only_verifier", "trace_only_verifier.py")
collision = load("resolvewhy_collision_search", "portable_core_collision_search.py")
runner = load("resolvewhy_repro_runner", "run_reproducibility.py")


class TestTraceOnlyVerifier(unittest.TestCase):
    def setUp(self):
        self.base = verifier.base_trace()

    def test_sat_reconstruction(self):
        self.assertEqual(verifier.verify(verifier.sat_fixture())[0], "VERIFIED_SAT")

    def test_unsat_reconstruction(self):
        self.assertEqual(verifier.verify(self.base)[0], "VERIFIED_UNSAT")

    def test_subset_minimality(self):
        ok, deletions = verifier.minimality(self.base)
        self.assertTrue(ok)
        self.assertEqual([x[1] for x in deletions], ["VERIFIED_SAT"] * len(deletions))

    def test_serialization_roundtrip(self):
        import json
        rt = json.loads(json.dumps(self.base, sort_keys=True))
        self.assertEqual(verifier.verify(self.base), verifier.verify(rt))

    def test_dangling_references(self):
        self.assertEqual(verifier.verify(verifier.mutate(self.base, "dangling_ref"))[0], "INVALID_TRACE")

    def test_duplicate_ids(self):
        t = copy.deepcopy(self.base)
        t["candidates"].append(copy.deepcopy(t["candidates"][0]))
        self.assertEqual(verifier.verify(t)[0], "INVALID_TRACE")

    def test_missing_coverage_attestation(self):
        self.assertEqual(verifier.verify(verifier.mutate(self.base, "coverage_attestation"))[0], "INVALID_TRACE")

    def test_incomplete_candidate_coverage(self):
        self.assertEqual(verifier.verify(verifier.mutate(self.base, "candidate_coverage"))[0], "INSUFFICIENT_EVIDENCE")

    def test_malformed_proof_claim(self):
        t = copy.deepcopy(self.base)
        t["proof_claim"] = "not-an-object"
        self.assertEqual(verifier.verify(t)[0], "INVALID_TRACE")

    def test_missing_quantifier(self):
        t = copy.deepcopy(self.base)
        t["proof_claim"]["quantifier"] = None
        self.assertEqual(verifier.verify(t)[0], "INVALID_TRACE")

    def test_missing_evaluation_domain(self):
        self.assertEqual(verifier.verify(verifier.mutate(self.base, "evaluation_domain"))[0], "INVALID_TRACE")

    def test_invalid_proof_premise_reference(self):
        t = copy.deepcopy(self.base)
        t["proof_claim"]["premise_refs"] = ["missing-premise"]
        self.assertEqual(verifier.verify(t)[0], "INVALID_TRACE")

    def test_provenance_failures(self):
        self.assertEqual(verifier.verify(verifier.mutate(self.base, "provenance"))[0], "INVALID_TRACE")
        t = copy.deepcopy(self.base)
        t["provenance"][0]["evidence_refs"] = ["unrelated"]
        self.assertEqual(verifier.verify(t)[0], "INVALID_TRACE")

    def test_provenance_cycle(self):
        t = copy.deepcopy(self.base)
        t["provenance"] = [
            {"id": "p1", "premise_refs": ["c:root"], "evidence_refs": []},
            {"id": "p2", "premise_refs": ["p1"], "evidence_refs": []},
            {"id": "p3", "premise_refs": ["p2"], "evidence_refs": []},
            {"id": "p4", "premise_refs": ["p3"], "evidence_refs": []},
        ]
        self.assertEqual(verifier.verify(t)[0], "INVALID_TRACE")

    def test_activation_preserved(self):
        self.assertEqual(verifier.verify(self.base)[0], "VERIFIED_UNSAT")
        t = copy.deepcopy(self.base)
        t["dependencies"][0]["active"] = False
        t["proof_claim"]["status_claim"] = "SAT"
        self.assertEqual(verifier.verify(t)[0], "VERIFIED_SAT")

    def test_resolver_label_disagreement(self):
        t = copy.deepcopy(self.base)
        t["proof_claim"]["status_claim"] = "SAT"
        self.assertEqual(verifier.verify(t)[0], "VERIFIED_UNSAT")

    def test_candidate_artifact_distinction(self):
        t = copy.deepcopy(self.base)
        t["artifacts"][0]["compatible"] = False
        self.assertEqual(verifier.verify(t)[0], "VERIFIED_UNSAT")

    def test_branch_semantics(self):
        t = copy.deepcopy(self.base)
        t["trace_scope"] = "branch"
        t["proof_claim"]["quantifier"] = "branch"
        t["proof_claim"]["branch_ref"] = "py3.13-linux"
        self.assertIn(verifier.verify(t)[0], {"VERIFIED_SAT", "VERIFIED_UNSAT"})

    def test_projection_search(self):
        worlds, raw, repaired, _ = collision.collision_search()
        self.assertEqual(worlds, 256)
        self.assertEqual(repaired, 0)
        self.assertGreaterEqual(raw, 1)

    def test_campaign(self):
        count, false_accepts, counts = runner.mutate_campaign(verifier)
        self.assertEqual(count, 250)
        self.assertEqual(false_accepts, 0)
        self.assertEqual(sum(counts.values()), 250)


if __name__ == "__main__":
    unittest.main()
