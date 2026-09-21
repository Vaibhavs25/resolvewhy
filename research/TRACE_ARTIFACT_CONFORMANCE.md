## Executable alignment note

The current reproducibility runner regenerates the finite research harnesses used for this conformance record. It replays the 18 serialized semantic fixtures, checks serialization and isolated replay, runs the two executable subset-minimality checks, executes the deterministic 250-case mutation campaign, and regenerates the 256-world projection search.

The 18-case result is a serialized fixture replay, not a fresh execution of every historical public resolver incident. The historical corpus and resolver/source analyses remain separate evidence records.

## Reproducibility boundary note

For the clone-and-run path, use:

```bash
python research/run_reproducibility.py
```

The current committed runner regenerates one finite verifier fixture, its round-trip and hermetic replay, its subset-minimality checks, a deterministic 250-case mutation campaign, and the 256-world extended projection harness.

# Trace Artifact Conformance

**Date:** 2026-09-21  
**Status:** research conformance contract; not an ecosystem standard

## Purpose

A trace is conformant for trace-only proof support when an independent verifier can reconstruct the asserted semantic problem and validate SAT/UNSAT using only the serialized artifact and verifier implementation.

## Required semantic contents

| Area | Requirement |
|---|---|
| Envelope | schema/version, resolver identity, trace scope |
| Requirements | normalized root requirements |
| Dependencies | parent candidate, requirement, activation semantics |
| Candidate identity | opaque unique candidate identity; package/version is not assumed sufficient |
| Artifact identity | separate artifact facts when feasibility depends on artifacts |
| Runtime context | Python/platform/marker environment facts |
| Evaluation domain | explicit quantified environment set/partition when proof scope is multi-environment |
| Resolution policy | prerelease/source/cutoff/yank/format policy when proof-relevant |
| Candidate-domain coverage | explicit candidate domain, scope, coverage state, completeness attestation |
| Semantic constraints | normalized constraints consumed by the independent proof engine |
| Evidence state | known/derived/incomplete/missing/unknown distinctions |
| Provenance | proof-bearing claims trace back to in-scope evidence observations |
| Proof claim | explicit result kind, quantifier, evaluation_domain_ref, premise_refs |

## Exact result classes

VERIFIED_SAT means the reconstructed finite semantic problem has a satisfying model.

VERIFIED_UNSAT means the reconstructed finite semantic problem has no satisfying model.

INSUFFICIENT_EVIDENCE means the artifact is structurally valid but the proof obligation depends on missing, incomplete, partial, unknown, or non-exhaustive evidence.

INVALID_TRACE means the artifact itself cannot be safely interpreted as a proof-supporting artifact because of structural or semantic inconsistency.

## Mandatory fail-closed rules

A verifier must reject or downgrade, rather than infer proof, when:

- a reference is dangling;
- unique IDs collide;
- complete candidate coverage lacks attestation;
- source/query scope is missing for a no-candidate claim;
- evaluation-domain scope is missing or incomplete for a universal/multi-environment proof;
- proof quantifier is absent or inconsistent;
- semantic premises are not provenance-connected;
- evidence used by a proof is incomplete/unknown;
- activation conditions have been erased;
- artifact-level facts are collapsed into candidate/version identity where artifacts affect feasibility;
- the declared SAT/UNSAT label conflicts with independently recomputed semantics.

## Hermeticity

Verification must not consult:

- the original resolver or provider;
- package indexes or network;
- resolver caches;
- original stdout/stderr or issue-report text;
- unrecorded filesystem state.

The proof result must come from the serialized trace and verifier only.

## Minimality

For a declared subset-minimal UNSAT core:

1. verify the full core as UNSAT;
2. delete each core element individually;
3. verify SAT after each deletion.

This establishes subset-minimality, not minimum cardinality.

## Native data that may remain outside the proof core

Resolver-native error trees, decision levels, backjump state, candidate ordering, heuristics, index internals, and human-readable diagnostics may be retained as namespaced explanation/audit material. They are not required for correctness once their satisfiability-relevant semantic consequences are normalized.

## Conformance evidence from this experiment

- 18/18 corpus traces matched expected trace-only results.
- 18/18 serialization round-trips preserved results.
- 18/18 hermetic replays succeeded.
- 2 nontrivial subset-minimal UNSAT cores were independently rechecked.
- 250 structural mutation cases produced 0 unsafe verified proofs.
- 256-world post-repair projection search produced 0 semantic collisions.

## Boundary

This is a bounded research result for the tested finite semantic fragment. It does not establish ecosystem-wide wire compatibility, universal resolver semantics, or maintainer approval.
