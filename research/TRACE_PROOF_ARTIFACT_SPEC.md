# Trace-Only Proof Artifact Specification

**Date:** 2026-09-21
**Status:** research specification, not an ecosystem standard

## Purpose

A trace is a **proof-supporting evidence artifact** when an independent verifier can determine the exact semantic problem and independently validate the claimed satisfiability result using only the serialized trace and verifier code, with no access to the original resolver, provider, index, network, diagnostics, or unrecorded filesystem state.

## Required artifact contents

1. `schema` and version.
2. Requirements with raw and normalized semantics.
3. Dependency edges with parent candidate, normalized requirement, and activation condition.
4. Opaque candidate identities and satisfiability-relevant origin information.
5. Artifact identities whenever artifact selection affects feasibility.
6. Runtime contexts used by the proof.
7. `evaluation_domain` describing the environments over which the proof claim is quantified.
8. `resolution_policy` relevant to candidate admissibility.
9. Candidate domains with explicit source/query scope and coverage status.
10. Coverage attestation for every completeness claim used by proof.
11. Semantic constraints/literals consumed by the independent proof engine.
12. Evidence state distinguishing known, derived, incomplete, missing, and related states.
13. Provenance references for every proof-strengthening derived claim.

## Proof scope

The trace must explicitly distinguish:

- single-environment proof;
- existential multi-environment claim;
- universal multi-environment claim;
- branch/fork-specific claim.

`evaluation_domain` is mandatory whenever the claim ranges over multiple environments.

## Candidate completeness

A verifier may use a no-candidate conclusion only when:

- the candidate domain is explicitly identified;
- source/index/query scope is explicit;
- the domain is declared complete;
- an attestation explains why it is complete;
- all satisfiability-relevant filters are represented;
- the independent verifier can check the contradiction.

Resolver exhaustion without provider/domain authority is insufficient.

## Evidence states

Recommended proof-facing states:

- `known_fact`: directly recorded fact with authoritative source/evidence;
- `derived_fact`: computed from recorded premises;
- `incomplete`: observation exists but is known incomplete;
- `missing`: required observation is absent;
- `unknown`: status cannot be established.

Missing or incomplete proof premises produce `INSUFFICIENT_EVIDENCE`, not `VERIFIED_SAT`.

## Trace validity

A trace is `INVALID_TRACE` when its structure makes its claims non-auditable or internally inconsistent, including:

- missing required structural fields;
- malformed evaluation domain;
- dangling candidate/dependency/artifact/domain/provenance references;
- duplicate IDs where uniqueness is required;
- complete coverage without valid attestation;
- a proof claim referring to an undeclared environment domain;
- invalid proof scope value;
- malformed semantic literals that the verifier cannot interpret.

Invalidity is distinct from insufficiency: an invalid trace cannot be safely interpreted as a weaker proof.

## Verifier obligations

An independent verifier must:

1. validate structural integrity before semantic reasoning;
2. reconstruct the semantic constraint problem from the trace;
3. honor activation conditions and runtime context;
4. honor evaluation-domain quantification;
5. honor resolution policy where it changes admissibility;
6. enforce candidate coverage requirements before absence proofs;
7. verify provenance for proof-strengthening claims;
8. independently establish SAT/UNSAT rather than trusting a resolver conclusion;
9. validate any claimed subset-minimal core by removing each core element and re-checking satisfiability;
10. never consult native resolver structures as an implicit fallback.

## Serialization invariant

`deserialize(serialize(trace))` must preserve semantic result and all cross-references.

Malformed or dangling references after deserialization must produce `INVALID_TRACE`.

## Hermeticity

A conforming trace-only verification process has no dependency on:

- original resolver executable or source;
- provider implementation;
- package index or network;
- original stdout/stderr;
- resolver caches/search state;
- filesystem metadata not serialized in the trace.

Only the serialized trace and verifier implementation may affect the proof result.

## Proof-supporting vs explanatory artifacts

A trace may be proof-supporting but lossy about explanation quality. Native derivation trees and decision state may be retained as namespaced audit material without being proof premises.

Conversely, a trace that preserves a rich native error message but omits proof scope, candidate coverage, activation conditions, or provenance is not proof-supporting.

## Research boundary

This specification supports the tested finite semantic fragment only. It does not establish universal completeness for arbitrary dependency resolvers, dynamic build systems, or future resolver semantics.

## Proof claim binding

A proof-supporting artifact MUST contain an explicit proof claim object binding:
- result kind;
- quantifier (existential, universal, or branch);
- evaluation_domain_ref;
- semantic premises asserted for verification.

The result claim is a proposition to be independently verified, not authoritative resolver evidence.

For a multi-environment result, quantifier plus evaluation_domain_ref together define the mathematical scope. A resolver policy flag such as universal or fork does not substitute for either.

A verifier MUST return INVALID_TRACE when a multi-environment claim lacks an explicit quantifier/domain binding or contains inconsistent references.
