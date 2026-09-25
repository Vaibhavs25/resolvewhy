# resolvewhy

Research prototype for formally verified explanations of dependency-resolution failures from structured evidence.

## Research status

**Technical validation:** complete for the declared finite semantic fragment.
**H2d:** PARTIALLY SUPPORTED — bounded semantic portability.
**H2e:** NOT TESTED — no substantive maintainer feedback was obtained.
**Production implementation:** not established or approved by this research.

## Production implementation status

**Phase 1 — Production Semantic Core:** complete.

**Phase 2 — Production Trace Format:** complete as `resolvewhy-trace/1.0`.

**Phase 3A — pip/resolvelib Adapter:** implemented and validated. The production suite and the Windows production CI both pass 75/75, including the controlled pip/resolvelib integration paths.

**Phase 4A — Production Independent Verifier:** implemented for the declared finite semantic fragment. The verifier independently reconstructs and evaluates production `resolvewhy-trace/1.0` traces and returns typed `VERIFIED_SAT`, `VERIFIED_UNSAT`, `INSUFFICIENT_EVIDENCE`, or `INVALID_TRACE` results. It does not import the research verifier or depend on a resolver.

Phase 4B — Independent Solver + Minimal-Core Engine: implemented and tested for the established finite semantic fragment. The reusable solver operates on a typed semantic problem, independently computes SAT/UNSAT, and provides deterministic subset-minimal core extraction and core verification. Phase 4B does not imply general production readiness. Unsupported semantics continue to fail closed, and the explanation layer, CLI/API, and additional resolver adapters remain future work.

See `docs/PRODUCTION_SEMANTIC_CORE.md`, `docs/PRODUCTION_TRACE_FORMAT.md`, `docs/PRODUCTION_VERIFIER.md`, and `AI_BUILD_CONTEXT.md`.

## Production trace format

**Phase 2 — Production Trace Format:** implemented as `resolvewhy-trace/1.0`.

The production trace boundary provides deterministic UTF-8 JSON serialization and safe reconstruction of the typed semantic model. Unknown schema versions, unknown fields, malformed references, invalid enums, malformed markers, and invalid proof/coverage structures are rejected; incomplete evidence remains distinguishable from invalid structure.

See `docs/PRODUCTION_TRACE_FORMAT.md` and the canonical fixture at `tests/fixtures/production_trace.json`.

## Research question

The project asks whether sufficiently rich structured dependency-resolution evidence can be normalized into a small semantic trace from which an independent verifier can derive a formally checked explanation without parsing human-readable diagnostics or depending on native resolver state.

The research separates:

- **H1:** Given sufficiently rich structured evidence, can a downstream engine compute a verified subset-minimal explanation?
- **H2:** Can resolver/tooling ecosystems expose sufficiently rich evidence in a stable and portable form for independent downstream use?

## Strongest technical result

Within the tested finite semantic fragment, a serialized trace can act as a self-contained proof-supporting evidence artifact. The independent verifier can reconstruct the semantic problem, respect runtime context, finite evaluation domains, policy, activation conditions, candidate/artifact distinctions, coverage attestations, provenance, and explicit proof claims, then independently classify SAT/UNSAT and verify subset-minimality without consulting the original resolver or external state.

The research record reports **18/18 trace-only classification agreement**, **18/18 serialization round-trip agreement**, **18/18 isolated replays**, **2** independently rechecked nontrivial subset-minimal UNSAT proofs, **250** serialization mutations with zero incorrectly accepted verified proofs, and an extended **256-world** post-repair projection search with zero semantic collisions.

The clean executable reproducibility runner currently regenerates the finite verifier fixture, its SAT/UNSAT and minimality checks, exactly 250 deterministic mutation cases, and the extended 256-world projection harness. The 18-case result remains historical research-record evidence rather than a fresh execution of every historical resolver incident; the 256-world projection search is part of the clean runner.

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

## Reproducibility

The research harness is runnable without resolver packages, package indexes, or network access:

```bash
python research/run_reproducibility.py
```

The explicit research tests are:

```bash
python -m unittest research.test_reproducibility
```

The current suite computes 18/18 deterministic serialized-fixture replay, 18/18 round trips, 18/18 hermetic replays, 2 executable subset-minimality checks, 250 mutation cases with zero false verified-proof acceptances, and 256 projection worlds with zero post-repair collisions.

The 18-case replay is a deterministic serialized semantic fixture replay of the documented corpus classifications. It is not a fresh execution of all historical public resolver incidents. See `research/REPRODUCIBILITY_README.md` and `research/REPRODUCIBILITY_INDEX.md` for the exact evidence boundary.

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