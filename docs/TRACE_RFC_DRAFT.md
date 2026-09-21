# RFC Draft: Structured dependency-resolution evidence for downstream tooling

**Status:** Experimental research draft  
**Schema:** `resolvewhy-trace/v0`  
**Research date:** 2026-09-20

## Problem

Dependency resolvers already compute rich internal facts while resolving a project: requirements, candidate choices and rejections, dependency relationships, incompatibilities, environment branches, and backtracking causes. Downstream tools generally cannot rely on receiving those facts through a stable machine-readable failure interface.

The practical question is not whether every resolver should adopt `resolvewhy`. The question is narrower:

> Could a small, versioned semantic evidence interface expose enough trustworthy information for independent downstream analysis without requiring downstream tools to parse human-readable diagnostics or depend on resolver internals?

## Proposed abstraction

`resolvewhy-trace/v0` is a deliberately small semantic model. It does **not** define a resolver algorithm, package index, lockfile, package-manager protocol, or human-facing error format.

Core concepts:

- package/candidate identity
- requirement and parent candidate
- dependency edge and activation condition
- environment/policy
- candidate observation/rejection
- incompatibility
- provenance linking claims to premises
- explicit completeness declarations

The key semantic rule is:

> A missing event is not evidence that the event did not occur.

A capture must therefore distinguish an authoritative/exhaustive observation from an incomplete event stream.

## Minimal example

The project requires `a==1` and `b==1`.

- `a==1` depends on `x<2`.
- `b==1` depends on `x>=2`.
- The authoritative candidate inventory contains `x==1` and `x==2`.
- The resulting normalized constraint set is unsatisfiable.

```json
{
  "schema": "resolvewhy-trace/v0",
  "requirements": [
    {"id": "root:a", "raw": "a==1", "evidence_type": "known_fact"},
    {"id": "root:b", "raw": "b==1", "evidence_type": "known_fact"}
  ],
  "candidates": [
    {"id": "a==1", "package": "a", "version": "1", "available": true},
    {"id": "b==1", "package": "b", "version": "1", "available": true},
    {"id": "x==1", "package": "x", "version": "1", "available": true},
    {"id": "x==2", "package": "x", "version": "2", "available": true}
  ],
  "dependency_observations": [
    {"id": "edge:a->x", "parent_candidate": "a==1", "requirement": "x<2", "active": true},
    {"id": "edge:b->x", "parent_candidate": "b==1", "requirement": "x>=2", "active": true}
  ],
  "provenance": [
    {"claim": "a==1 requires x<2", "premises": ["a==1", "edge:a->x"]},
    {"claim": "b==1 requires x>=2", "premises": ["b==1", "edge:b->x"]}
  ],
  "completeness": {
    "requirements_complete": true,
    "candidate_inventory_complete": true,
    "dependency_metadata_complete": true,
    "environment_complete": true,
    "provenance_complete": true
  }
}
```

A consuming analyzer can then return a verified core consisting of the two root constraints and the two dependency constraints. Verification means:

1. the final core is UNSAT; and
2. deleting each individual core constraint makes the model SAT.

This is **subset-minimal**, not minimum-cardinality.

## Why completeness is explicit

Consider a trace containing no `x` candidates. That observation is ambiguous unless the trace also says whether the candidate inventory was exhaustive. The two meanings are different:

- `candidate_inventory_complete=true`: the resolver-side evidence establishes that the candidate domain was exhausted.
- `candidate_inventory_complete=false`: the capture does not establish that no other candidates existed.

The second case must remain `insufficient_evidence`, not UNSAT.

## What this draft does not claim

- This is not an ecosystem standard.
- No cross-resolver standard currently exists as a result of this experiment.
- resolvelib is the only resolver layer tested end-to-end so far.
- pip, uv, and Poetry cross-ecosystem portability is unproven.
- The schema does not solve resolver-specific candidate identity, artifact selection, source/index semantics, marker grammar, or prerelease policy.
- A smaller MUS is not automatically a more useful human explanation.

## Technical questions for maintainers

1. **Evidence utility:** Would a structured resolver evidence stream be useful to downstream tools that need to independently analyze resolution failures?
2. **Trust boundary:** Which fields would you consider authoritative enough for a third party to reason from? In particular, what should prove that candidate discovery was exhaustive?
3. **Interface:** If exposed, would a callback/event API, trace file, debug API, or another mechanism fit the resolver architecture better than a public general-purpose object model?
4. **Provider boundary:** Which facts belong to the provider/finder rather than the resolver, and which should therefore be considered resolver-specific in a common schema?
5. **Derived conflicts:** Is it reasonable to expose derived incompatibilities/backtracking causes as structured evidence, provided they carry provenance and are versioned separately from raw observations?
6. **Portability:** Which semantic concepts genuinely recur across your resolver and other resolvers, and which look deceptively similar but have different meanings?
7. **Rejection:** What would make an external evidence abstraction misleading or too expensive to maintain?

Negative feedback is explicitly valuable. The goal is to find the abstraction's technical boundary, not to obtain adoption commitments.

## Current evidence before maintainer feedback

A controlled resolvelib capture can already be collected through public provider/reporter contracts without stderr scraping, normalized, and consumed by the repaired `resolvewhy` core. That is evidence for feasibility in one resolver architecture only. It is not evidence of maintainer willingness, portability, or ecosystem standardization.

## Source references

- resolvelib provider interface: https://github.com/sarugaku/resolvelib/blob/main/src/resolvelib/providers.py
- resolvelib reporter interface: https://github.com/sarugaku/resolvelib/blob/main/src/resolvelib/reporters.py
- pip installation report: https://pip.pypa.io/en/stable/reference/installation-report/
- pip resolver internals: https://github.com/pypa/pip/tree/main/src/pip/_internal/resolution/resolvelib
- uv resolver internals: https://docs.astral.sh/uv/reference/internals/resolver/
- Poetry Mixology source: https://github.com/python-poetry/poetry/tree/main/src/poetry/mixology
- pipgrip: https://github.com/ddelange/pipgrip

**Public RFC status:** publication candidate for the experimental research repository.

## Final research-state addendum — 2026-09-21

The research conducted after the initial draft narrowed the semantic contract substantially. The later validated model is described in `research/REVISED_TRACE_SCHEMA.md` and the final proof-supporting artifact requirements in `research/TRACE_PROOF_ARTIFACT_SPEC.md`.

The current research understanding adds the following distinctions to the experimental model:

- candidate identity is opaque and may be source/VCS/path-qualified;
- candidate/artifact identity are separate when artifact feasibility matters;
- runtime context is distinct from resolution policy;
- candidate completeness is scoped to an explicit candidate domain and requires attestation for exhaustive claims;
- evaluation domain is explicit for quantified multi-environment claims;
- proof claims explicitly bind result kind, quantifier, evaluation domain and semantic premises;
- derived proof premises require provenance/evidence reachability;
- resolver-native conflict/derivation structures remain namespaced rather than universalized.

## Final evidence position

The technical validation program now reports a bounded positive result: the trace-only proof-artifact boundary has been validated for the tested finite semantic fragment, including independent SAT/UNSAT reconstruction and subset-minimality checks from serialized traces. This does not establish an ecosystem-wide standard or stable public interchange API.

H2d is **PARTIALLY SUPPORTED**. H2e remains **NOT TESTED**; there is no substantive maintainer feedback to incorporate.

The RFC remains an experimental research artifact. Its original illustrative model is retained as historical context; the later research documents are authoritative for the current semantic boundary and validation status.

## Current-status marker — 2026-09-21

The original H2 table above is historical draft state. The current research status is defined by the later research records:

- H2a: SUPPORTED narrowly
- H2b: PARTIALLY SUPPORTED
- H2c: SUPPORTED for the tested fragment
- H2d: PARTIALLY SUPPORTED
- H2e: NOT TESTED

The revised schema and proof-artifact requirements are documented in `research/REVISED_TRACE_SCHEMA.md` and `research/TRACE_PROOF_ARTIFACT_SPEC.md`. The clean executable reproducibility boundary is documented in `research/REPRODUCIBILITY_INDEX.md`.