# Reproducibility Index

**Date:** 2026-09-21  
**Status:** Current executable research-harness boundary

## Reproducibility boundary

Run:

```bash
python research/run_reproducibility.py
```

The runner uses only the Python standard library and committed research code. It does not require network access, package indexes, native resolver packages, or external services for the executable trace-only checks.

The clean suite currently:

- replays all 18 committed serialized semantic fixtures;
- checks JSON round-trips for all 18 fixtures;
- performs isolated/hermetic verification for all 18 fixtures;
- independently checks subset-minimality for RW-09 and RW-14;
- generates exactly 250 distinct deterministic mutation cases;
- runs the extended 256-world projection search;
- checks deletion of hidden native resolver state.

The 18-case result is **serialized fixture replay**, not a fresh execution of the historical public resolver incidents. Public issue reports, resolver/source analysis, and maintainer-response evidence remain separate research records.

## Current executable mapping

| Claim | Primary record | Current executable status |
|---|---|---|
| Finite SAT/UNSAT verification | `research/trace_only_verifier.py` | REGENERATED |
| Serialization round-trip | `research/run_reproducibility.py` | REPLAYED for 18 committed fixtures |
| Hermetic replay | `research/run_reproducibility.py` | REPLAYED for 18 committed fixtures |
| Subset-minimality | `research/trace_only_verifier.py` | REGENERATED for RW-09 and RW-14 |
| 18-case trace-only classification | `research/TRACE_ONLY_FULL_CORPUS.md` | SERIALIZED FIXTURE REPLAY; not fresh incident execution |
| 250 mutation campaign | `research/run_reproducibility.py` | REGENERATED |
| 256 post-repair projection worlds | `research/portable_core_collision_search.py` | REGENERATED |

| Research question | Evidence class |
|---|---|
| H2d portability | Source/fixture research evidence; not an ecosystem-wide live conformance run |
| H2e maintainer validation | Non-executable empirical record; 0 substantive responses |

## Quantitative research record versus executable regeneration

The final research documents record:

- 18/18 trace-only classification agreement;
- 18/18 serialization round-trips;
- 18/18 isolated replays;
- 2 independently verified nontrivial subset-minimal UNSAT proofs;
- 250 deterministic serialization mutations with 0 incorrectly accepted verified proofs;
- 256 post-repair projection worlds with 0 semantic collisions.

The current runner now independently regenerates the 18 serialized fixture classifications, the 18 round-trips, the 18 hermetic replays, the two executable minimality checks, the 250-case mutation campaign, and the 256-world extended projection search.

These are **finite research-harness results**, not universal or exhaustive guarantees.

## Clean environment

- Recorded research environment: Python 3.13.5.
- Current runner dependencies: Python standard library only.
- Network: not required by the runner.
- Package indexes: not required.
- Native resolver packages: not required.
- Historical public resolver incidents: not re-executed by the runner.
- Poetry and pipgrip: source-validated in the recorded architecture study rather than executed by the trace-only runner.

A local `git clone` was not performed in the current execution environment because external DNS/network access to GitHub is unavailable here. This does not alter the repository claim; it only limits this audit to connector inspection plus code-level alignment.

## Exact current executable output contract

A successful run prints only values computed after the corresponding checks pass:

```text
REPRODUCIBILITY SUITE
TRACE_ONLY_CORPUS = 18/18 (serialized fixture replay; not fresh issue execution)
SERIALIZATION_ROUNDTRIP = 18/18
HERMETIC_REPLAY = 18/18
SUBSET_MINIMAL_PROOFS = 2
MUTATION_CASES = 250
MUTATION_FALSE_ACCEPTS = 0
PROJECTION_WORLDS = 256
POST_REPAIR_COLLISIONS = 0
```

For machine-readable output:

```bash
python research/run_reproducibility.py --json
```

To write both human-readable and JSON result files:

```bash
python research/run_reproducibility.py --write-results research/reproducibility_results
```

## Executable semantic boundary

The committed verifier is intentionally a **fixture-level research verifier**, not a general package-manager verifier.

The executable fragment currently evaluates:

1. normalized version constraints and finite candidate choice;
2. dependency-edge activation using the supported marker expression forms;
3. the tested `Requires-Python` semantic form;
4. finite candidate-domain coverage with completeness attestation;
5. explicit proof quantifier/domain binding;
6. proof premises as the constraints reconstructed by the verifier;
7. provenance reachability from proof premises to supporting evidence;
8. candidate/artifact reference integrity and the reduced artifact `compatible` semantics used by the fixtures;
9. the executable prerelease policy and allowed-source policy;
10. explicit branch selection through `proof_claim.branch_ref`;
11. independent recomputation of SAT/UNSAT rather than trusting `status_claim`;
12. subset-minimality by single-premise deletion.

The verifier does **not** implement full PEP 508, complete build-system or wheel/sdist selection, complete hash policy, complete lockfile semantics, symbolic/infinite environment reasoning, generic virtual/provided-package semantics, or arbitrary resolver-native semantics. Those remain outside the executable guarantee.

## Test entry point

Run:

```bash
python -m unittest research.test_reproducibility
```

The explicit tests cover SAT/UNSAT reconstruction, subset-minimality, serialization, invalid references, duplicate IDs, coverage-attestation failures, incomplete coverage, proof-claim errors, provenance failures, activation-marker preservation, reduced artifact feasibility, executable prerelease policy, explicit branch semantics, resolver-label disagreement, the deterministic 250-case mutation campaign, and the 256-world projection search.

## Fixture provenance

The 18-case fixture archive is stored in `research/fixtures/trace_corpus.py` as a deterministic compressed payload protected by SHA-256:

```
88cadf682c2a7c7d3c91c861e8cc673c92f17134f2a4091b46bafda3b733f8bb
```

The fixture cases correspond to classifications documented in `research/REAL_WORLD_TRACE_CORPUS.md`. They are replay evidence, not a substitute for rerunning the historical resolver incidents.

## Interpretation

A passing executable suite establishes that the **committed finite research harnesses** agree with their stated fixtures and adversarial checks.

It does not establish:

- universal semantic completeness across dependency resolvers;
- a stable public cross-resolver trace/API standard;
- complete package metadata/build/lockfile/hash semantics;
- maintainer acceptance, usefulness, or adoption;
- production readiness.

Historical intermediate documents are preserved for auditability. Their current interpretation is defined by `research/FINAL_RESEARCH_SYNTHESIS.md`, `research/FINAL_SEMANTIC_BOUNDARY.md`, and the current README.
