# Revised Trace Schema — resolvewhy-trace

**Status:** research specification; not an ecosystem standard

## Objective

Represent dependency-resolution evidence without allowing incomplete or resolver-specific observations to become false proofs.

The contract is semantic. Adapters may use callbacks, reporters, error trees, provider hooks, internal objects, or future public trace formats.

## 1. Trace envelope

Conceptual fields:

- schema identifier/version
- resolver identity
- resolver version/commit
- declared trace scope
- runtime_context
- resolution_policy
- candidate domains
- requirements
- candidates
- artifacts
- dependency observations
- rejection observations
- incompatibility observations
- provenance/evidence references

## 2. Candidate identity

A candidate MUST have an opaque identifier unique within the trace.

Semantic projections include:
- package
- version, when applicable
- candidate kind
- source reference
- other satisfiability-relevant identity

Rules:
1. candidate.id is the primary identity used by provenance and dependency edges.
2. package + version is not assumed to be unique.
3. URL, VCS, path, workspace, source/index, or other origin must remain distinguishable when relevant to satisfiability.
4. Equality across traces requires an adapter-defined identity relation.

## 3. Artifact identity

Artifacts are separate from candidates.

An artifact MAY contain:
- id
- candidate_ref
- origin URL/path
- tags
- hash
- metadata_ref
- artifact-selection status

Reason: a package/version can exist while no artifact is usable in the current environment.

## 4. Candidate-domain coverage

Every candidate enumeration belongs to a declared domain.

Conceptual shape:

~~~json
{
  "id": "domain:x:1",
  "identifier": "x",
  "requirements": ["req:7", "req:9"],
  "scope": {
    "sources": ["index:A", "index:B"],
    "index_queries": ["query:11"],
    "artifact_policy_ref": "policy:2"
  },
  "runtime_context_ref": "env:1",
  "resolution_policy_ref": "policy:1",
  "coverage": {
    "status": "complete",
    "attestation": {
      "kind": "authoritative_finite_domain",
      "evidence_refs": ["obs:55"]
    }
  }
}
~~~

### Coverage status

Allowed:
- complete
- partial
- unknown

### Attestation rule

A complete claim MUST state why the declared candidate domain is exhaustive.

Suitable examples:
- authoritative finite test domain
- exhaustive provider/source query whose scope is explicit
- authoritative source exhaustion over a declared finite domain

The statement “the resolver exhausted its candidates” is not enough unless the evidence also establishes that the provider/source domain is complete.

### Scope rule

Completeness is relative to the declared candidate domain.

It never means “all candidates everywhere.”

## 5. Requirements

Preserve:
- raw representation
- normalized semantic representation
- parent candidate, when applicable
- activation condition
- evidence status

## 6. Dependency observations

Represent:
parent candidate -> requirement

Preserve:
- parent candidate
- raw dependency
- normalized requirement
- activation/marker condition
- evidence references
- resolver/provider namespace if necessary

## 7. Runtime context

Runtime context contains facts such as:
- Python implementation/version
- OS/platform
- architecture
- wheel compatibility tags
- relevant marker values

Do not put resolver policy in this field.

## 8. Resolution policy

Separate policy such as:
- prerelease mode
- source/index selection
- format policy
- hash policy
- version selection strategy
- universal/fork strategy
- cutoff/exclusion policy
- lockfile/preferences inputs

## 9. Rejection observations

A rejection is an observation, not automatically a proof.

Conceptual shape:

~~~json
{
  "id": "reject:12",
  "target_ref": "artifact:31",
  "reason_kind": "platform_incompatible",
  "source_layer": "artifact",
  "evidence_status": "known_fact",
  "premise_refs": ["meta:9", "env:1"]
}
~~~

Recommended source layers:
- resolver
- provider
- source
- index
- metadata
- artifact
- policy
- environment

Keep the taxonomy small.

A rejection does not imply every other candidate was rejected.

## 10. Incompatibilities

Native resolver conflict objects are not assumed to share one universal mathematical meaning.

Conceptual shape:

~~~json
{
  "id": "inc:44",
  "semantics": "resolver_clause",
  "resolver_namespace": "pubgrub/uv",
  "terms": [],
  "derivation_refs": ["inc:42", "inc:43"]
}
~~~

The normalized proof core uses semantic constraints/literals and provenance.

Native derivation objects remain namespaced evidence.

## 11. Provenance

Derived claims MUST carry provenance.

Conceptual shape:

~~~json
{
  "id": "claim:51",
  "claim_type": "derived_incompatibility",
  "premise_refs": ["inc:44", "req:9"],
  "derivation_rule": "intersection",
  "source_namespace": "resolvewhy-normalizer"
}
~~~

A human-readable explanation string never substitutes for proof provenance.

## 12. Evidence states

Observations should distinguish at least:
- known_fact
- derived_fact
- rejected_candidate
- incomplete
- missing

The vocabulary may grow, but evidence absence must remain distinguishable from evidence of absence.

## 13. Insufficient evidence

The downstream engine MUST return:

insufficient_evidence

when a proof obligation depends on evidence that is:
- partial
- unknown
- missing
- redacted
- outside declared scope
- unavailable from the resolver/provider boundary

It MUST NOT silently convert those states into UNSAT.

## 14. No-candidate proof rule

A claim equivalent to:

> no candidate satisfying requirement R exists

is permitted only when:

1. the candidate domain is explicitly identified;
2. source/index scope is explicit;
3. runtime context and relevant resolution policy are explicit;
4. coverage is complete for that exact domain;
5. completeness has an explicit attestation/evidence reference;
6. relevant candidate/artifact filtering is represented;
7. the independent proof engine verifies the resulting contradiction.

An empty candidate list alone is never sufficient.
A rejection event alone is never sufficient.
Resolver exhaustion alone is never sufficient without domain attestation.

## 15. Normalization boundary

Normalize:
- requirement
- opaque candidate identity
- dependency edge
- runtime context
- resolution policy
- candidate-domain coverage
- semantic constraint/literal
- provenance
- evidence state

Keep optional/namespaced:
- native derivation trees
- decision levels
- backjump state
- resolver heuristics
- index internals
- artifact-selection internals
- provider-specific rejection structures

## 16. Core safety invariant

Every proof-strengthening statement must carry the evidence that justifies its scope.

Invalid:

observed candidate set is empty
=> no candidate exists

Valid:

authoritatively exhaustive candidate domain
+
no candidate satisfies constraints
=> no candidate exists in that declared domain

Only then may the proof engine derive UNSAT.

## 17. Research status

The revised contract survived the targeted adversarial experiment documented in:

research/REVISED_TRACE_ADVERSARIAL_AUDIT.md

It is not an ecosystem standard and has not received maintainer endorsement.
