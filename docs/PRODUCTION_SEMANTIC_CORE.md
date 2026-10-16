# Production Semantic Core

**Phase:** 1 — Production Semantic Core  
**Status:** initial foundation

## Purpose

The production package under `src/resolvewhy` is a reusable semantic model for the concepts validated by the research program. It is deliberately separate from `research/` and does not execute resolvers, access package indexes, or perform SAT/UNSAT reasoning.

The package is the foundation for later phases: trace serialization, resolver adapters, independent verification, and explanation rendering.

## Semantic model

The model provides typed, immutable representations for:

- requirements and normalized version constraints;
- canonical requested extras on requirements;
- parent-linked dependency edges;
- optional-edge extra context;
- activation/marker expressions;
- opaque and source-aware candidate identity;
- declared-extra metadata with explicit `complete`, `unknown`, and `missing` states;
- separate artifact identity and artifact compatibility/selection status;
- runtime contexts;
- explicit finite evaluation domains;
- quantifier/proof scope and explicit proof-premise binding;
- resolution policy;
- candidate domains and scoped coverage;
- completeness attestations;
- semantic constraints and literals;
- evidence states and evidence observations;
- provenance;
- proof claims;
- resolver-native rejection/incompatibility observations as namespaced evidence;
- the research result classes as `VerificationStatus`.

## Safety invariants

The model and structural validator preserve these research distinctions:

1. runtime context is not the evaluation domain;
2. candidate identity is not artifact identity;
3. observed rejection is not exhaustive candidate absence;
4. resolution policy is separate from mathematical constraints;
5. evidence is separate from proof claims;
6. portable semantic objects are separate from resolver-native evidence.
7. an empty complete declared-extra set means “declares no extras”; missing or
   unknown metadata never means that.

Complete candidate coverage requires an explicit attestation and evidence references. Partial/unknown coverage remains representable without being mislabeled as complete.

The structural validator distinguishes malformed structure/reference failures from evidence insufficiency. It does not decide SAT/UNSAT.

## Extras semantics

Requested and declared extras use canonical PEP 685 spellings. An active
requirement contributes its requested extras to its selected candidate. An
optional dependency edge may name the extra context that activates it; active
requests are propagated to a finite fixed point, including transitive and
cyclic optional edges.

Before either SAT or UNSAT is reported as verified, every active requested
extra must be checked against the selected candidate's declaration metadata.
Complete metadata that omits an extra produces the typed non-verified
`undeclared_extra` result. `unknown` and `missing` declaration states produce
their own non-verified diagnostics instead; neither is treated as proof that
the extra is absent. Candidate-domain coverage and normal provenance checks
remain independent requirements for any verified claim.

## Relationship to research code

`research/trace_only_verifier.py` remains the fixture-level research verifier. The production model does not copy that implementation into `src/`.

The research harness and fixtures remain authoritative research records. Production code reuses the validated semantic concepts while remaining independently maintainable.

## Phase 1 non-goals

This phase does not include:

- pip/uv/Poetry/pipgrip adapters;
- resolver execution;
- package-index access;
- a general PEP 508 parser;
- production SAT/UNSAT verification;
- minimal-core search;
- CLI/UI;
- lockfile/build/hash semantics;
- symbolic or infinite evaluation domains;
- performance optimization;
- ecosystem integrations.

Later work must not silently broaden the research guarantee. Unsupported semantics should be represented explicitly and handled conservatively by later verifier layers.

## Research regression rule

Changes to the production core must not modify the research fixtures or research conclusion merely to make the production package easier to implement. A semantic mismatch with the validated research fragment should be documented and resolved deliberately.
