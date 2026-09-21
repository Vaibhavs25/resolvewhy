# resolvewhy

Research prototype for formally verified explanations of dependency-resolution failures from structured evidence.

## Research status

**Technical validation:** complete for the declared finite semantic fragment.
**H2d:** PARTIALLY SUPPORTED — bounded semantic portability.
**H2e:** NOT TESTED — no substantive maintainer feedback was obtained.
**Production implementation:** not established or approved by this research.

## Research question

The project asks whether sufficiently rich structured dependency-resolution evidence can be normalized into a small semantic trace from which an independent verifier can derive a formally checked explanation without parsing human-readable diagnostics or depending on native resolver state.

The research separates:

- **H1:** Given sufficiently rich structured evidence, can a downstream engine compute a verified subset-minimal explanation?
- **H2:** Can resolver/tooling ecosystems expose sufficiently rich evidence in a stable and portable form for independent downstream use?

## Strongest technical result

Within the tested finite semantic fragment, a serialized trace can act as a self-contained proof-supporting evidence artifact. The independent verifier can reconstruct the semantic problem, respect runtime context, finite evaluation domains, policy, activation conditions, candidate/artifact distinctions, coverage attestations, provenance, and explicit proof claims, then independently classify SAT/UNSAT and verify subset-minimality without consulting the original resolver or external state.

The research record reports **18/18 trace-only classification agreement**, **18/18 serialization round-trip agreement**, **18/18 isolated replays**, **2** independently rechecked nontrivial subset-minimal UNSAT proofs, **250** serialization mutations with zero incorrectly accepted verified proofs, and an extended **256-world** post-repair projection search with zero semantic collisions.

The clean executable reproducibility runner currently regenerates the finite verifier fixture, its SAT/UNSAT and minimality checks, exactly 250 deterministic mutation cases, and the committed 64-world projection harness. The 18-case and 256-world results remain historical research-record evidence rather than fresh output of the clean runner.

These results are bounded experimental evidence, not universal correctness claims.

## Reproducibility

Run `python research/run_reproducibility.py` for the clean, network-free research-harness checks. See `research/REPRODUCIBILITY_INDEX.md` for the exact executable versus historical evidence boundary.

## Proven semantic boundary

### Inside the established guarantee

- normalized version constraints and dependency conjunctions;
- parent-linked dependency edges;
- tested activation-marker semantics;
- opaque/source-aware candidate identity;
- candidate/artifact separation when artifact feasibility matters;
- runtime context;
- finite explicit evaluation domains;
- singleton, existential, universal, and branch proof scopes within that finite domain model;
- resolution policy where it changes admissibility;
- scoped candidate-domain coverage and completeness attestation;
- semantic constraints/literals;
- evidence states and provenance;
- explicit proof-claim binding;
- independent SAT/UNSAT recomputation;
- subset-minimality by individual deletion.

### Supported only in reduced/tested form

Nested and/or PEP 508 markers, extras, wheel/sdist mixtures, local/editable/workspace candidates, hash constraints, lockfile restrictions, richer artifact-selection rules, and multi-dimensional environment partitions are semantically representable in the model, but their full interactions have not been independently established.

### Outside the current guarantee

- arbitrary dynamic build-backend metadata generation;
- hidden build-environment effects;
- complete wheel/sdist build-selection and build-failure semantics;
- complete cross-resolver hash/reproducibility semantics;
- complete lockfile semantics;
- implicit virtual/provided/system-package satisfaction relations;
- symbolic or infinite environment-domain reasoning;
- exhaustive arbitrary PEP 508 semantics;
- future resolver-specific semantics not represented by the normalized model.

"Outside the current guarantee" means **not established by the present evidence**, not impossible.

## What H2d establishes

The portability experiments support a bounded common semantic layer across the tested pip/resolvelib and uv evidence shapes, with source-level mappings for Poetry/Mixology and pipgrip/PubGrub.

The evidence does **not** establish a stable public interchange API, ecosystem-wide wire compatibility, or identical native resolver semantics. Resolver-native derivation trees, decision levels, backjump state, provider internals, index machinery, and detailed rejection structures remain resolver-specific/namespaced.

The projection-collision experiment also showed why explicit evaluation-domain semantics are necessary for multi-environment proof claims.

## What H2e says

H2e remains **NOT TESTED**. The project has no substantive maintainer response to incorporate into the technical conclusion. Four individualized outreach attempts were successfully sent; a fifth named maintainer was not contacted because the connected Outlook account was suspended. No silence, delivery state, generic acknowledgement, or failed contact is treated as evidence.

The RFC therefore records technical questions for maintainer feedback, not endorsement claims.

## Research artifacts

Key research records are under research/, including:

- FINAL_SEMANTIC_BOUNDARY.md
- BOUNDARY_CASES.md
- REAL_WORLD_TRACE_CORPUS.md
- REAL_WORLD_TRACE_VALIDATION.md
- H2D_CROSS_RESOLVER_VALIDATION.md
- H2D_CONFORMANCE_MATRIX.md
- PORTABLE_CORE_SUFFICIENCY.md
- PORTABLE_CORE_MINIMALITY.md
- TRACE_ONLY_FULL_CORPUS.md
- TRACE_PROOF_CLAIM_FALSIFICATION.md
- TRACE_PROOF_ARTIFACT_SPEC.md
- TRACE_ARTIFACT_CONFORMANCE.md
- REVISED_TRACE_SCHEMA.md

The repository preserves earlier research documents so that discovered defects and their repairs remain auditable.

## Status statement

This repository is a research record. It does not claim a production resolver, ecosystem standard, maintainer endorsement, or production readiness.