# Trace-Only Verification

**Date:** 2026-09-21  
**Decision:** **B. TRACE-ONLY VERIFICATION REQUIRES ANOTHER SEMANTIC FIELD**

## 1. Research hypothesis

The experiment asks whether a serialized portable semantic trace can support independent SAT/UNSAT verification after all original resolver/provider/index/native-state access is removed.

## 2. Critical result

The first hermetic replay exposed a real semantic issue at the proof-artifact boundary: provenance cannot be treated as a single non-empty top-level object, and proof-supporting claims need explicit provenance links to every fact that strengthens the proof.

In particular, deleting one provenance entry from an otherwise identical trace did not change the mathematical result in the minimal fixture, but it destroyed auditability. A trace-only artifact therefore needs a distinction between:

- mathematical semantic sufficiency;
- proof-audit sufficiency.

The artifact specification already requires provenance references, but the verifier harness initially did not enforce reachability from every proof premise. This is an implementation-level defect, not a new schema concept.

A stronger semantic test also revealed a second issue that is schema-level: the current trace does not explicitly carry the quantifier semantics of a claimed result beyond the evaluation domain. A universal domain is not enough unless the result declaration says whether the claim is universal, existential, or branch-specific and ties that quantifier to the evaluation domain.

The smallest repair is therefore to treat proof_scope/claim_quantifier as proof-bearing semantic data rather than incidental metadata.

## 3. Hermetic replay

The committed verifier uses only serialized trace data and Python standard-library code. The intended replay removes network proxies and PYTHONPATH; no resolver package, provider, index, native error tree, or original diagnostics participate in the proof calculation.

The core serialized contradiction is reconstructed without native resolver state.

## 4. Result classes

- VERIFIED_SAT: the trace contains a complete, self-consistent semantic model supporting the stated SAT claim.
- VERIFIED_UNSAT: the trace contains a complete, self-consistent semantic model supporting the stated UNSAT claim.
- INSUFFICIENT_EVIDENCE: structure is valid, but one or more proof premises are incomplete/unknown/non-exhaustive.
- INVALID_TRACE: the artifact is structurally inconsistent or contains an invalid proof-scope/coverage/reference claim.

INSUFFICIENT_EVIDENCE must never be silently promoted to VERIFIED_SAT.

INVALID_TRACE is distinct from insufficiency because malformed references or unsupported completeness claims make the artifact itself untrustworthy.

## 5. Required trace-only checks

The verifier checks, before proof:

1. required field presence;
2. unique candidate/artifact/dependency/constraint IDs;
3. all internal references resolve;
4. complete coverage has an attestation;
5. evidence state is not incomplete/unknown for proof-bearing claims;
6. evaluation domain is explicit;
7. proof scope is explicit;
8. semantic constraints can be reconstructed;
9. provenance reaches each proof-bearing semantic claim;
10. SAT/UNSAT is recomputed independently;
11. any claimed subset-minimal core is rechecked by independent deletion.

## 6. Corpus for trace-only replay

The existing 18-case corpus was reduced to the following trace-only targets:

| Case | Purpose | Trace-only expectation |
|---|---|---|
| RW-01 / RW-14 | nontrivial transitive UNSAT | VERIFIED_UNSAT on a complete reduced trace |
| RW-02 | resolver-failure-but-SAT negative control | VERIFIED_SAT or INSUFFICIENT_EVIDENCE depending on completeness |
| RW-06 | multiple-index scope | INSUFFICIENT_EVIDENCE unless all source domains are complete |
| RW-07 | inactive marker false-conflict | no UNSAT without active marker semantics |
| RW-08 | 401/403 source failure | INSUFFICIENT_EVIDENCE |
| RW-09 | universal Python split | requires explicit evaluation domain + universal proof scope |
| RW-11/RW-12 | yanked/artifact semantics | safe only with artifact/policy evidence |
| RW-17 | prerelease policy | result depends on serialized policy, not native resolver |
| RW-18 | source-distinct identity | candidate origins must remain distinguishable |

## 7. False-proof mutations

The mutation family includes:

- remove coverage attestation;
- remove evaluation domain;
- remove resolution policy;
- remove candidate identity;
- remove provenance;
- remove dependency semantics;
- remove activation condition;
- create dangling references;
- mark evidence unknown/incomplete.

Expected outcome is INVALID_TRACE for structural corruption, or INSUFFICIENT_EVIDENCE when the artifact remains structurally valid but loses proof-relevant evidence.

One mutation class must be handled carefully: removing a provenance record can leave the mathematical constraint set unchanged. The correct result depends on the artifact's declared proof standard. For a proof-supporting artifact, missing provenance should block a formally auditable proof even when the bare mathematics remain unchanged.

## 8. Serialization invariant

serialize -> deserialize -> verify must return the same semantic result.

Cross-reference corruption must not be silently ignored.

The minimal harness successfully round-trips the serialized object before verification.

## 9. Native-state deletion

Removing native derivation trees, decision levels, candidate ordering, and human-readable diagnostics does not alter the semantic truth of the tested finite contradiction.

This supports retaining those objects only as optional namespaced audit/explanation data.

## 10. Minimality

A trace-only UNSAT proof is not complete merely because a contradiction is found.

The claimed core must be independently tested:

1. full core => UNSAT;
2. remove each core element;
3. each single deletion => SAT;
4. only then classify the core as subset-minimal.

Minimum-cardinality is not claimed.

## 11. Remaining semantic boundary

The trace is self-contained only for a declared finite semantic fragment.

Outside the proven boundary are arbitrary dynamic build semantics, unbounded environment quantification, undocumented resolver-specific virtual packages, and semantics that were never serialized as normalized evidence.

## 12. Final decision

**B. TRACE-ONLY VERIFICATION REQUIRES ANOTHER SEMANTIC FIELD**

The trace-only experiment exposed the need to make the proof claim's quantifier/scope explicit and proof-bearing, not merely implied by a policy flag plus evaluation domain.

The smallest schema-level repair is to make the proof scope explicit as semantic claim metadata linked to the evaluation domain.

After this repair is enforced, the hermetic verifier can operate without the original resolver, provider, network, indexes, native derivations, or diagnostics for the tested finite fragment.

H2e remains NOT TESTED and is unaffected.