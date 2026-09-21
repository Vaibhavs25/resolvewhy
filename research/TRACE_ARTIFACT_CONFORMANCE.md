## Executable alignment note

The conformance evidence below records the historical 18-case and extended 256-world experiments. The current clean reproducibility runner does not regenerate those historical fixture sets; it regenerates the finite executable verifier fixture, one proof-minimality check, the 250 mutation campaign, and the current 64-world projection harness. See `research/REPRODUCIBILITY_INDEX.md`.

The 18/18, 2-proof, and 256-world figures in this section are retained as historical research evidence. The current clean executable runner does not regenerate the full 18-case fixture set or the 256-world extended search; see research/REPRODUCIBILITY_INDEX.md for the exact executable boundary.

## Reproducibility boundary note

The current committed runner regenerates one finite verifier fixture, its round-trip and hermetic replay, its subset-minimality checks, a deterministic 250-case mutation campaign, and the current 64-world projection harness. It must not be read as a fresh regeneration of the historical 18-case or 256-world figures.

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
