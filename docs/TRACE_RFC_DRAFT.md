# RFC: Structured dependency-resolution evidence for downstream tooling

**Status:** Experimental research artifact  
**Schema context:** The original `resolvewhy-trace/v0` example below is historical context. The validated semantic boundary is defined by `research/REVISED_TRACE_SCHEMA.md` and `research/TRACE_PROOF_ARTIFACT_SPEC.md`.

This is a technical research record, not an adoption request or ecosystem standard proposal.

## Research problem

Dependency resolvers compute structured facts during resolution: requirements, candidate choices and rejections, dependency relationships, incompatibilities, environment branches, and backtracking causes. Downstream tooling generally cannot rely on a stable machine-readable failure-evidence surface.

The research question is whether a deliberately small semantic trace can preserve enough trustworthy information for independent downstream analysis without parsing human-readable diagnostics or depending on resolver internals.

## Research abstraction

The research models proof-relevant concepts including:

- package and opaque/source-aware candidate identity;
- candidate/artifact identity when artifact feasibility matters;
- requirements and parent-linked dependency edges;
- activation conditions;
- runtime context;
- explicit evaluation domains for quantified claims;
- resolution policy where it changes admissibility or proof scope;
- scoped candidate-domain coverage with completeness attestation;
- semantic constraints/literals;
- evidence state and provenance;
- an explicit proof claim binding result kind, quantifier, evaluation domain and semantic premises.

Resolver-native derivation, decision and rejection structures remain resolver-specific or namespaced; they are not flattened into a universal object model.

## Why completeness matters

An empty observed candidate set is not by itself proof that no candidate exists. A trace must distinguish an exhaustive candidate domain from an incomplete capture. Unsupported or incomplete evidence must therefore fail closed rather than being turned into a proof.

## Current research position

The technical validation program reports a bounded result for the declared finite semantic fragment:

- H1: **SUPPORTED**
- H2a: **SUPPORTED narrowly**
- H2b: **PARTIALLY SUPPORTED**
- H2c: **SUPPORTED for the tested fragment**
- H2d: **PARTIALLY SUPPORTED**
- H2e: **NOT TESTED**

The trace-only proof-artifact boundary was validated in the tested finite fragment. This does not establish universal resolver completeness, a stable ecosystem-wide trace/API standard, maintainer acceptance, ecosystem adoption, or production readiness.

## Technical questions

1. Which structured evidence is sufficiently authoritative for downstream third-party reasoning?
2. How should candidate-domain completeness be attested when candidate discovery is provider-, source-, or policy-dependent?
3. Which exposure mechanism best fits resolver architectures: callback/event API, serialized trace, opt-in debug interface, or another mechanism?
4. Which facts should remain resolver/provider-specific rather than being normalized into a common semantic layer?
5. Which derived incompatibilities or backtracking facts are useful when accompanied by explicit provenance?
6. Which semantic concepts recur across resolvers without implying identical native meanings?
7. What would make an external evidence abstraction misleading, unstable, or too expensive to maintain?

Negative technical feedback is valuable. No endorsement, adoption, promotion, or maintenance commitment is being requested.

## Evidence and limitations

The repository contains controlled resolvelib instrumentation, cross-resolver source/fixture analysis, real-world semantic fixtures, a trace-only verifier, reproducibility harnesses, and explicit semantic-boundary records.

The committed verifier is a deliberately bounded research implementation. It does not implement full PEP 508 semantics, complete build-system or wheel/sdist selection, complete hash or lockfile semantics, symbolic/infinite environment reasoning, generic virtual/provided-package semantics, or arbitrary resolver-native behavior.

See:

- `research/FINAL_RESEARCH_SYNTHESIS.md`
- `research/REPRODUCIBILITY_INDEX.md`
- `research/FINAL_SEMANTIC_BOUNDARY.md`
- `research/REVISED_TRACE_SCHEMA.md`
- `research/TRACE_PROOF_ARTIFACT_SPEC.md`

## Historical note

Earlier versions of this RFC used a coarse `resolvewhy-trace/v0` illustrative model and earlier H2 labels. Those materials are preserved as research history. The later validated documents are authoritative for the current semantic boundary and validation status.
