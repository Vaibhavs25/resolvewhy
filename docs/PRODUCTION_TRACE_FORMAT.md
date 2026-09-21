# Production Trace Format

**Schema:** `resolvewhy-trace/1.0`  
**Status:** production-format foundation; the format is versioned and implemented, but it is not an ecosystem standard.

## 1. Purpose

The production trace is the transport boundary between the typed semantic model and later resolver adapters/verifiers:

```
resolvewhy.model.Trace
        |
        v
serialize_trace()
        |
        v
resolvewhy-trace/1.0 JSON
        |
        v
deserialize_trace()
        |
        v
resolvewhy.model.Trace
```

A trace is pure data. Loading it does not execute a resolver, import a resolver plugin, contact a package index, access the network, or execute embedded code.

The format is designed to carry the validated semantic fragment from the research program without relying on the research fixture schema as the production wire contract.

## 2. Versioning policy

The current identifier is exactly:

```
resolvewhy-trace/1.0
```

The loader accepts that identifier only.

A breaking change to required fields, field meaning, reference semantics, enum semantics, or proof-scope semantics requires a new schema version. An unknown schema identifier is rejected; it is never silently interpreted as `1.0`.

Version `1.0` intentionally has no generic extension bag. Unknown fields are rejected. Resolver-native information belongs in the typed namespaced evidence records already represented by the semantic model. A future version may introduce an explicit namespaced extension mechanism without changing the meaning of existing `1.0` traces.

## 3. Top-level structure

The canonical trace contains these sections:

| Section | Purpose |
|---|---|
| `schema` | Exact production schema identifier |
| `resolver` | Producer name/version/commit |
| `trace_scope` | Declared single-, multi-environment, or forked scope |
| `runtime_contexts` | Environment facts attached to observations/proof |
| `evaluation_domain` | Environments over which a quantified claim is made |
| `resolution_policy` | Proof-relevant admissibility/selection policy |
| `candidate_domains` | Explicit candidate universe scopes and completeness state |
| `requirements` | Root/parent-linked package requirements |
| `candidates` | Opaque/source-aware candidate identity |
| `artifacts` | Candidate-associated artifact identity and feasibility |
| `dependencies` | Parent candidate -> requirement edges and activation |
| `rejections` | Resolver/provider/source observations, not automatic proof |
| `incompatibilities` | Resolver-native conflict structures with namespace |
| `semantic_constraints` | Portable constraints used by later independent verification |
| `evidence_state` | Known/derived/incomplete/missing/unknown evidence |
| `provenance` | Direct/derived support for proof-bearing facts |
| `proof_claim` | Explicit proposition, quantifier, domain, status, and premises |

No top-level field is derived from or substituted by human-readable resolver diagnostics.

## 4. Identifier and reference encoding

Semantic identifiers are encoded as JSON strings.

Typed `TraceRef` values are encoded explicitly as:

```json
{"kind":"constraint","id":"c:req"}
```

This prevents a bare string reference from losing its semantic namespace.

The loader rejects:

- empty identifiers;
- invalid reference kinds;
- duplicate IDs where uniqueness is required;
- dangling references;
- cross-section references to objects that do not exist.

## 5. Requirements and dependencies

Requirements preserve:

- stable ID;
- package name;
- normalized version constraint;
- optional raw representation;
- optional parent candidate;
- activation/marker expression;
- evidence references.

Dependency edges preserve:

- edge ID;
- parent candidate identity;
- requirement identity;
- activation/marker expression;
- raw dependency representation;
- evidence references;
- optional resolver/provider namespace.

The activation condition is not flattened away.

## 6. Candidate and artifact identity

Candidates use an opaque ID and retain source/origin information.

Package + version is not treated as globally unique.

Artifacts are a separate object with their own ID and a candidate reference. This matters because a candidate may exist while a particular artifact is incompatible, filtered, yanked, or otherwise unavailable.

Boolean artifact feasibility is serialized as a JSON boolean or explicit `null`; it is never encoded as a string.

## 7. Runtime context vs. evaluation domain

A runtime context describes the environment represented by an observation.

An evaluation domain describes the environment set over which the proof claim is quantified.

They are intentionally different objects.

A universal or multi-environment proof must bind its claim to an explicit evaluation-domain ID. A loader therefore does not infer universal scope from a policy string or filename.

## 8. Resolution policy

Policy is serialized separately from mathematical constraints.

The current model represents:

- prerelease mode;
- source-selection preferences;
- format policy;
- hash policy;
- version-selection strategy;
- universal/fork strategy;
- cutoff/exclusion inputs;
- lockfile preferences.

Policy fields describe admissibility/search semantics; they are not themselves proof results.

## 9. Candidate-domain coverage

Every candidate domain declares:

- candidate domain ID;
- identifier;
- relevant requirement refs;
- candidate refs;
- source/query scope;
- runtime-context ref;
- policy ref;
- coverage status.

Coverage is one of:

- `complete`
- `partial`
- `unknown`

A `complete` status requires a completeness attestation with evidence references.

An empty candidate list without authoritative completeness remains representable as non-complete evidence. The format does not turn observed absence into proof of universal absence.

## 10. Semantic constraints and proof claims

Portable proof-bearing constraints are encoded separately from resolver-native incompatibility objects.

A proof claim binds:

- result kind;
- quantifier;
- evaluation-domain reference;
- claimed status;
- semantic premise references;
- optional branch reference;
- optional subset-minimal core;
- whether subset-minimality is claimed.

The claim is a proposition to be independently checked later; the claimed status is not trusted as evidence.

## 11. Evidence and provenance

Evidence states distinguish:

- `known_fact`
- `derived_fact`
- `rejected_candidate`
- `incomplete`
- `missing`
- `unknown`

Provenance distinguishes direct facts from derived claims and records the references used to derive them.

A missing/incomplete observation can therefore remain a valid serialized trace while later verification can classify it as `INSUFFICIENT_EVIDENCE`.

## 12. Resolver-native evidence

Resolver-native rejection and incompatibility structures remain explicitly namespaced.

Examples include namespaces such as:

```
pubgrub/uv
resolvelib
mixology
pipgrip
```

These records are audit/evidence material. They do not become a universal native conflict object merely by passing through the production format.

## 13. Canonical serialization rules

`serialize_trace()` returns UTF-8 JSON bytes with:

- `ensure_ascii=False`;
- `allow_nan=False`;
- lexicographically sorted JSON object keys;
- compact separators (`,` and `:`);
- explicit `null` for optional fields;
- JSON arrays for model tuples/sequences;
- no Python `repr()`;
- no pickle.

The current model does not declare its tuple-valued collections as unordered sets. Therefore their element order is preserved exactly rather than silently sorted. This guarantees lossless model round-tripping. Object-key ordering is the only universal canonical ordering applied by the serializer in version `1.0`.

The resulting UTF-8 byte sequence is stable and suitable as a deterministic hashing input.

## 14. Serialization/deserialization behavior

```python
payload: bytes = serialize_trace(trace)
trace2: Trace = deserialize_trace(payload)
assert trace2 == trace
assert serialize_trace(trace2) == payload
```

The loader performs:

1. UTF-8 decoding;
2. strict JSON parsing with duplicate-key detection;
3. non-standard JSON constant rejection;
4. size/depth/node-count guards;
5. exact schema-version validation;
6. explicit reconstruction of every semantic object;
7. structural validation and reference validation.

The deserializer never uses dynamic imports, `eval`, `exec`, pickle, resolver execution, or external references.

## 15. Structural invalidity vs. incomplete evidence

The loader preserves two distinct conditions.

### `INVALID_TRACE`

Used by the validation layer when the serialized artifact is structurally inconsistent, for example:

- malformed object;
- duplicate identifier;
- dangling reference;
- invalid enum;
- malformed marker;
- invalid proof binding;
- invalid coverage attestation.

### `INSUFFICIENT_EVIDENCE`

A structurally valid artifact can still describe evidence that is:

- partial;
- incomplete;
- missing;
- unknown;
- non-exhaustive.

Phase 2 does not perform SAT/UNSAT verification. It only ensures that these states remain representable and are not collapsed during serialization.

## 16. Security model

Treat traces as untrusted input.

The implementation applies:

- a maximum input size of 2 MiB;
- a maximum decoded JSON depth of 64;
- a maximum decoded node count of 200,000;
- duplicate JSON-key rejection;
- standard-JSON-only constants;
- strict field/type checking;
- no dynamic execution;
- no external I/O during decoding.

The caller controls whether bytes are read from disk or another transport. The codec itself operates only on supplied data.

## 17. Complete example

A complete `resolvewhy-trace/1.0` example is committed at:

```
tests/fixtures/production_trace.json
```

It contains a runtime context, evaluation domain, policy, candidate domain with an authoritative finite-domain attestation, requirement, source-aware candidate, separate artifact, semantic constraint, evidence observations, provenance, and proof claim.

It is an illustrative production-format fixture, not a historical resolver incident.

## 18. Relationship to the research schema

The production format was deliberately derived from the **Phase 1 production semantic model** and the validated research requirements.

It is not a direct serialization of the old illustrative `resolvewhy-trace/v0` material.

Research files under `research/` remain historical/experimental evidence. The production trace format is implemented under `src/resolvewhy/trace/`.

## 19. Compatibility policy

A `1.0` artifact is interpreted only according to the `1.0` rules.

Compatibility guarantees:

- a `1.0` trace must remain readable by future implementations that explicitly support `1.0`;
- breaking semantic changes require a new version;
- unknown schema versions are rejected;
- unknown fields inside `1.0` objects are rejected;
- optional future behavior must not silently change the meaning of existing fields.

The goal is conservative, auditable evolution rather than permissive parsing.

## 20. Phase 2 boundary

This format is the transport foundation only.

It does **not** yet provide:

- resolver adapters;
- pip/uv/Poetry/pipgrip capture;
- package-index access;
- SAT/UNSAT computation;
- subset-minimal core extraction;
- explanation generation;
- CLI;
- network functionality.

Those belong to later phases.
