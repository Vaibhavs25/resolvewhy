"""Artifact-only smoke test invoked from the packaging CI job."""

from __future__ import annotations

import importlib.metadata
import json
import os
import sys
from pathlib import Path

import resolvewhy
from resolvewhy.explanation import build_explanation, render_explanation
from resolvewhy.solving import SemanticProblem
from resolvewhy.trace import TraceDecodeError, deserialize_trace
from resolvewhy.verification import verify


def main() -> None:
    fixture = Path(os.environ["RESOLVEWHY_SMOKE_FIXTURE"])
    installed_root = Path(sys.prefix).resolve()
    package_path = Path(resolvewhy.__file__).resolve()
    assert package_path.is_relative_to(installed_root), package_path
    assert importlib.metadata.version("resolvewhy") == os.environ["RESOLVEWHY_EXPECTED_VERSION"]

    trace = deserialize_trace(fixture.read_bytes())
    assert verify(trace).status.value == "VERIFIED_SAT"

    conflict_payload = json.loads(fixture.read_text(encoding="utf-8"))
    conflict_payload["requirements"][0]["constraint"]["version"] = "2.0"
    conflict_payload["semantic_constraints"][0]["literals"][0]["value"] = "2.0"
    conflict_payload["proof_claim"]["status_claim"] = "UNSAT"
    conflict_trace = deserialize_trace(json.dumps(conflict_payload))
    conflict = verify(conflict_trace)
    assert conflict.status.value == "VERIFIED_UNSAT"

    problem = SemanticProblem.from_trace(
        conflict_trace,
        conflict_trace.semantic_constraints,
        conflict_trace.runtime_contexts,
        conflict_trace.proof_claim.quantifier,
    )
    assert render_explanation(build_explanation(problem, conflict))

    try:
        deserialize_trace(b'{"schema":"resolvewhy-trace/invalid"}')
    except TraceDecodeError:
        pass
    else:
        raise AssertionError("malformed serialized input was accepted")

    incomplete_payload = json.loads(fixture.read_text(encoding="utf-8"))
    incomplete_payload["evidence_state"]["overall"] = "incomplete"
    incomplete = verify(deserialize_trace(json.dumps(incomplete_payload)))
    assert incomplete.status.value == "INSUFFICIENT_EVIDENCE"


if __name__ == "__main__":
    main()
