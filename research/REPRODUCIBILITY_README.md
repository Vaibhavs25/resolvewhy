# Reproducibility boundary

**Status:** current executable research-harness path.

## What the clean suite regenerates

The repository contains a standard-library-only reproducibility entry point:

```bash
python research/run_reproducibility.py
```

It deterministically regenerates:

- the 18-case serialized semantic fixture replay;
- JSON serialization round-trip checks for all 18 fixtures;
- isolated/hermetic verification for all 18 fixtures;
- two executable subset-minimality checks, for RW-09 and RW-14;
- exactly 250 distinct structural/semantic mutations;
- the extended 256-world projection-collision search;
- native-state deletion checks.

The historical public resolver incidents are **not** freshly re-executed by this command. The 18-case result is a replay of the serialized semantic fixtures recorded for the research corpus. The public issue reports and resolver/source analyses remain historical/source-analysis evidence.

## Environment

Tested environment:

- Python 3.13.5
- external Python packages: none
- network: not required
- package indexes: not required
- native resolver packages: not required

The trace-only suite is designed to be hermetic. Its child processes contain only the serialized trace, the verifier, a small worker and Python's standard library. The audit hook rejects socket/subprocess activity and filesystem access outside the temporary execution area and standard library.

## Expected executable output

A successful run prints:

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

The numbers above are printed by the runner only after the corresponding assertions pass.

For machine-readable details:

```bash
python research/run_reproducibility.py --json
```

To write both human-readable and JSON result files:

```bash
python research/run_reproducibility.py --write-results research/reproducibility_results
```

## Test entry point

The executable research tests are:

```bash
python -m unittest research.test_reproducibility
```

They cover SAT/UNSAT reconstruction, subset-minimality, serialization, structural integrity, candidate coverage, proof-claim validity, provenance failures, activation markers, artifact feasibility in the tested reduced fragment, prerelease policy, branch/evaluation-domain semantics, the 250-case mutation campaign, and the 256-world projection search.

## Interpretation

A passing executable suite reproduces the **implemented finite research harnesses**.

It does not freshly reproduce:

- historical public issue executions;
- current upstream resolver behavior at arbitrary versions;
- Poetry/pipgrip runtime executions in the local test environment;
- ecosystem-wide portability;
- maintainer validation.

Those remain separate research evidence classes.

## Fixture provenance

The 18-case fixture archive is stored in `research/fixtures/trace_corpus.py` as a deterministic compressed payload with an SHA-256 checksum. The fixture cases correspond to the classifications documented in `research/REAL_WORLD_TRACE_CORPUS.md`.

The fixture is deliberately treated as evidence to replay, not as a substitute for re-running the historical resolver incidents.

## Scope discipline

The committed verifier implements a deliberately bounded finite semantic fragment. It does not attempt full PEP 508, full wheel/build selection, full lockfile semantics, full hash policy, symbolic/infinite domains, or arbitrary resolver-native behavior. Unsupported semantics must be represented as insufficient evidence or invalid trace rather than silently inferred.
