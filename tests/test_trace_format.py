from __future__ import annotations

import copy
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from test_semantic_core import valid_trace

from resolvewhy.model import (
    CandidateKind,
    DeclaredExtrasStatus,
    DependencyEdge,
    EvidenceStateKind,
    IncompatibilityObservation,
    ProofQuantifier,
    ReferenceKind,
    RejectionObservation,
    TraceRef,
)
from resolvewhy.trace import (
    LEGACY_SCHEMA,
    MAX_JSON_DEPTH,
    MAX_JSON_NODES,
    MAX_TRACE_BYTES,
    SCHEMA,
    TraceDecodeError,
    TraceSerializationError,
    deserialize_trace,
    serialize_trace,
)

FIXTURE = ROOT / "tests" / "fixtures" / "production_trace.json"


class TraceFormatTests(unittest.TestCase):
    def test_complete_valid_trace_serialization(self):
        trace = valid_trace()
        payload = serialize_trace(trace)
        self.assertTrue(payload.startswith(b"{"))
        self.assertIn(b'"schema":"resolvewhy-trace/1.0"', payload)

    def test_deserialization(self):
        trace = deserialize_trace(FIXTURE.read_bytes())
        self.assertEqual(trace.schema, LEGACY_SCHEMA)
        self.assertEqual(
            trace.candidates[0].declared_extras_status,
            DeclaredExtrasStatus.MISSING,
        )
        self.assertEqual(trace.candidates[0].package, "a")

    def test_v1_1_extras_round_trip(self):
        trace = valid_trace()
        requirement = replace(trace.requirements[0], requested_extras=("feature",))
        candidate = replace(
            trace.candidates[0],
            declared_extras=("feature",),
            declared_extras_status=DeclaredExtrasStatus.COMPLETE,
        )
        edge = DependencyEdge(
            id="dep:a-feature",
            parent_candidate_ref=candidate.id,
            requirement_ref=requirement.id,
            extra_context=("feature",),
        )
        trace = replace(
            trace,
            schema=SCHEMA,
            requirements=(requirement,),
            candidates=(candidate,),
            dependencies=(edge,),
        )
        payload = serialize_trace(trace)
        self.assertIn(b'"schema":"resolvewhy-trace/1.1"', payload)
        self.assertIn(b'"requested_extras":["feature"]', payload)
        self.assertIn(b'"extra_context":["feature"]', payload)
        self.assertEqual(deserialize_trace(payload), trace)

    def test_legacy_v1_0_rejects_v1_1_extras_fields(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["requirements"][0]["requested_extras"] = []
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_noncanonical_extra_name_rejected_at_decoder_boundary(self):
        trace = replace(valid_trace(), schema=SCHEMA)
        payload = json.loads(serialize_trace(trace))
        payload["requirements"][0]["requested_extras"] = ["Feature_Name"]
        with self.assertRaisesRegex(TraceDecodeError, "canonical extra spelling"):
            deserialize_trace(json.dumps(payload))

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

    def test_null_marker_child_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["requirements"][0]["activation"] = {
            "kind": "not",
            "atom": None,
            "children": [None],
        }
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(json.dumps(payload))

    def test_blank_typed_identifier_rejected(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["candidate_domains"][0]["candidate_refs"] = [" "]
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

    def test_serializer_rejects_unsupported_model_schema(self):
        trace = replace(valid_trace(), schema="resolvewhy-trace/2.0")
        with self.assertRaises(TraceSerializationError):
            serialize_trace(trace)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(b'{"schema":"resolvewhy-trace/1.0","schema":"resolvewhy-trace/1.0"}')

    def test_nonstandard_json_constant_rejected(self):
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(b'{"schema":NaN}')

    def test_invalid_utf8_rejected(self):
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(b"\xff\xfe")

    def test_oversized_input_rejected(self):
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(b" " * (MAX_TRACE_BYTES + 1))

    def test_pathological_depth_rejected(self):
        nested = "[" * (MAX_JSON_DEPTH + 1) + "]" * (MAX_JSON_DEPTH + 1)
        with self.assertRaises(TraceDecodeError):
            deserialize_trace(nested)

    def test_excessive_depth_is_rejected_before_json_decoding(self):
        from resolvewhy.trace import codec

        nested = b"[" * (MAX_JSON_DEPTH + 1) + b"]" * (MAX_JSON_DEPTH + 1)
        with (
            patch.object(codec.json, "loads", side_effect=AssertionError("decoder reached")),
            self.assertRaisesRegex(TraceDecodeError, "nesting depth"),
        ):
            deserialize_trace(nested)

    def test_json_node_limit_has_exact_boundary(self):
        # The root list contributes one node, so this has exactly MAX_JSON_NODES.
        at_limit = b"[" + b"0," * (MAX_JSON_NODES - 2) + b"0]"
        with self.assertRaisesRegex(TraceDecodeError, "top-level trace"):
            deserialize_trace(at_limit)

        one_over = b"[" + b"0," * (MAX_JSON_NODES - 1) + b"0]"
        with self.assertRaisesRegex(TraceDecodeError, "node count"):
            deserialize_trace(one_over)

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
