from __future__ import annotations

import copy
import json
import sys
from dataclasses import replace
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from resolvewhy.model import (
    Candidate,
    CandidateKind,
    IncompatibilityObservation,
    RejectionObservation,
    TraceRef,
    ReferenceKind,
    EvidenceStateKind,
    ProofQuantifier,
)
from resolvewhy.trace import (
    SCHEMA,
    TraceDecodeError,
    TraceSerializationError,
    deserialize_trace,
    serialize_trace,
)
from test_semantic_core import valid_trace


FIXTURE = ROOT / "tests" / "fixtures" / "production_trace.json"


class TraceFormatTests(unittest.TestCase):
    def test_complete_valid_trace_serialization(self):
        trace = valid_trace()
        payload = serialize_trace(trace)
        self.assertTrue(payload.startswith(b"{"))
        self.assertIn(b'"schema":"resolvewhy-trace/1.0"', payload)

    def test_deserialization(self):
        trace = deserialize_trace(FIXTURE.read_bytes())
        self.assertEqual(trace.schema, SCHEMA)
        self.assertEqual(trace.candidates[0].package, "a")

    def test_semantic_round_trip_equality(self):
        trace = valid_trace()
        self.assertEqual(deserialize_trace(serialize_trace(trace)), trace)

    def test_canonical_serialization_stability(self):
        trace = valid_trace()
        first = serialize_trace(trace)
        second = serialize_trace(trace)
        self.assertEqual(first, second)

    def test_fixture_is_canonical(self):
        raw = FIXTURE.read_bytes()
        trace = deserialize_trace(raw)
        self.assertEqual(serialize_trace(trace), raw)

    def test_enum_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertEqual(loaded.candidates[0].kind, CandidateKind.REGISTRY)
        self.assertEqual(
            loaded.proof_claim.quantifier,
            ProofQuantifier.EXISTENTIAL,
        )

    def test_nested_marker_preservation(self):
        trace = valid_trace()
        marker = copy.deepcopy(trace.requirements[0].activation)
        if marker is not None:
            marker = None
        from resolvewhy.model import MarkerAtom, MarkerExpression
        activation = MarkerExpression(
            kind="and",
            children=(
                MarkerExpression(
                    kind="atom",
                    atom=MarkerAtom("python_version", ">=", "3.10"),
                ),
                MarkerExpression(
                    kind="not",
                    children=(
                        MarkerExpression(
                            kind="atom",
                            atom=MarkerAtom("sys_platform", "==", "win32"),
                        ),
                    ),
                ),
            ),
        )
        req = replace(trace.requirements[0], activation=activation)
        trace = replace(trace, requirements=(req,))
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertEqual(loaded.requirements[0].activation, activation)

    def test_candidate_source_identity_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertEqual(loaded.candidates[0].id, "cand:a:1")
        self.assertEqual(loaded.candidates[0].source_ref, "index:main")

    def test_candidate_artifact_identity_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertNotEqual(loaded.candidates[0].id, loaded.artifacts[0].id)
        self.assertEqual(loaded.artifacts[0].candidate_ref, loaded.candidates[0].id)

    def test_runtime_context_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertEqual(loaded.runtime_contexts, trace.runtime_contexts)

    def test_evaluation_domain_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertEqual(loaded.evaluation_domain, trace.evaluation_domain)
        self.assertEqual(
            loaded.proof_claim.evaluation_domain_ref,
            loaded.evaluation_domain.id,
        )

    def test_quantifier_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertEqual(loaded.proof_claim.quantifier, ProofQuantifier.EXISTENTIAL)

    def test_proof_premise_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertEqual(loaded.proof_claim.premise_refs, ("c:req",))

    def test_branch_binding_preservation(self):
        trace = valid_trace()
        claim = replace(
            trace.proof_claim,
            quantifier=ProofQuantifier.BRANCH,
            branch_ref=trace.runtime_contexts[0].id,
        )
        branched = replace(trace, proof_claim=claim)
        loaded = deserialize_trace(serialize_trace(branched))
        self.assertEqual(loaded.proof_claim.branch_ref, "env:py3.11-linux")

    def test_candidate_coverage_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        coverage = loaded.candidate_domains[0].coverage
        self.assertEqual(coverage.status.value, "complete")

    def test_completeness_attestation_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        attestation = loaded.candidate_domains[0].coverage.attestation
        self.assertIsNotNone(attestation)
        self.assertEqual(attestation.kind.value, "authoritative_finite_domain")
        self.assertEqual(
            attestation.evidence_refs[0].id,
            "obs:coverage",
        )

    def test_provenance_preservation(self):
        trace = valid_trace()
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertEqual(loaded.provenance, trace.provenance)

    def test_resolver_native_namespace_preservation(self):
        trace = valid_trace()
        rejection = RejectionObservation(
            id="reject:a:1",
            target_ref=TraceRef(ReferenceKind.CANDIDATE, "cand:a:1"),
            reason_kind="platform_incompatible",
            source_layer="artifact",
            evidence_status=EvidenceStateKind.KNOWN_FACT,
        )
        incompatibility = IncompatibilityObservation(
            id="inc:uv:1",
            semantics="resolver_clause",
            resolver_namespace="pubgrub/uv",
        )
        augmented = replace(
            trace,
            rejections=(rejection,),
            incompatibilities=(incompatibility,),
        )
        loaded = deserialize_trace(serialize_trace(augmented))
        self.assertEqual(loaded.rejections[0].reason_kind, "platform_incompatible")
        self.assertEqual(
            loaded.incompatibilities[0].resolver_namespace,
            "pubgrub/uv",
        )

    def test_missing_required_field_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload.pop("proof_claim")
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_wrong_field_type_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["artifacts"][0]["compatible"] = "true"
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_invalid_enum_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["candidates"][0]["kind"] = "made-up"
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_dangling_reference_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["artifacts"][0]["candidate_ref"] = "cand:missing"
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_duplicate_id_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["candidates"].append(copy.deepcopy(payload["candidates"][0]))
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_invalid_evaluation_domain_reference_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["evaluation_domain"]["environment_refs"] = ["env:missing"]
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_invalid_coverage_reference_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["candidate_domains"][0]["coverage"]["attestation"]["evidence_refs"][0]["id"] = "obs:missing"
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_invalid_proof_premise_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["proof_claim"]["premise_refs"] = ["c:missing"]
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_invalid_branch_binding_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["proof_claim"]["quantifier"] = "branch"
        payload["proof_claim"]["branch_ref"] = "env:missing"
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_malformed_marker_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["requirements"][0]["activation"] = {
            "kind": "and",
            "atom": None,
            "children": [],
        }
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_unsupported_schema_version_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["schema"] = "resolvewhy-trace/2.0"
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_unknown_extension_field_rejected_in_v1(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["extensions"] = {"example.namespace": {"x": 1}}
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_malformed_provenance_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["provenance"][0]["kind"] = "direct"
        payload["provenance"][0]["premise_refs"] = [{"kind": "constraint", "id": "c:req"}]
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_incomplete_evidence_remains_structurally_valid(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["evidence_state"]["overall"] = "incomplete"
        trace = deserialize_trace(json.dumps(payload))
        self.assertEqual(trace.evidence_state.overall, EvidenceStateKind.INCOMPLETE)

    def test_null_fields_round_trip(self):
        trace = valid_trace()
        trace = replace(
            trace,
            candidates=(replace(trace.candidates[0], origin=None, metadata_ref=None),),
            artifacts=(replace(trace.artifacts[0], hash=None, compatible=None, metadata_ref=None),),
        )
        loaded = deserialize_trace(serialize_trace(trace))
        self.assertEqual(loaded, trace)

    def test_canonical_utf8_bytes(self):
        trace = valid_trace()
        encoded = serialize_trace(trace)
        self.assertIsInstance(encoded, bytes)
        encoded.decode("utf-8")

    def test_serializer_rejects_invalid_model_graph(self):
        trace = valid_trace()
        broken_artifact = replace(
            trace.artifacts[0],
            candidate_ref="cand:missing",
        )
        broken = replace(trace, artifacts=(broken_artifact,))
        with self.assertRaises(TraceSerializationError):
            serialize_trace(broken)


if __name__ == "__main__":
    unittest.main()
