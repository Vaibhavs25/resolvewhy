# Trace-Only Verification

**Date:** 2026-09-21  
**Decision:** **A. TRACE-ONLY PROOF ARTIFACT VALIDATED — within the tested finite semantic fragment**

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

## Final boundary clarification — proof claim binding

The trace-only experiment identified that proof scope must be an explicit proof-bearing semantic claim, not an inference from resolution policy plus evaluation domain. The revised schema now includes a `proof claim` concept binding the result quantifier to `evaluation_domain` and to the semantic premises being verified.

The hermetic proof artifact boundary is therefore:

`serialized trace -> structural validation -> proof claim binding -> semantic reconstruction -> independent SAT/UNSAT verification -> core validation`

No native resolver state is consulted during these steps.

## Final repaired experiment — 2026-09-21

The explicit proof-claim repair was implemented and the trace-only experiment was rerun against the full 18-case corpus.

### Full-corpus result

18/18 serialized traces matched their intended trace-only classifications:

- **VERIFIED_UNSAT:** RW-01, RW-09, RW-14, RW-15, RW-16, RW-17
- **VERIFIED_SAT:** RW-02, RW-18
- **INSUFFICIENT_EVIDENCE:** RW-03, RW-04, RW-05, RW-06, RW-07, RW-08, RW-10, RW-11, RW-12, RW-13
- **INVALID_TRACE:** 0 base corpus traces

All 18 traces survived JSON serialization/deserialization with the same semantic result, and all 18 isolated replay processes completed without resolver/network/external-state access.

### Proof-claim falsification

The repaired verifier distinguishes quantifier and domain binding:

- RW-09 universal claim -> VERIFIED_UNSAT
- the same branch represented existentially -> VERIFIED_SAT
- missing quantifier/domain reference -> INVALID_TRACE
- unrelated premise references -> independently recomputed result, not trusted claim text
- declared UNSAT on a SAT trace -> VERIFIED_SAT
- declared SAT on an UNSAT trace -> VERIFIED_UNSAT

Coverage and proof scope interact fail-closed: partial candidate coverage or incomplete evaluation-domain evidence cannot authorize a universal UNSAT proof.

### Provenance

For proof-supporting artifacts, provenance is reachability-checked from:

proof claim -> semantic premise -> provenance -> evidence observation

Removing provenance, changing it to unrelated scoped evidence, creating cycles, or creating dangling references produces INVALID_TRACE. Incomplete proof evidence produces INSUFFICIENT_EVIDENCE.

This intentionally distinguishes bare mathematical satisfiability from auditability of a proof-supporting artifact.

### Nontrivial UNSAT verification

Two independent subset-minimal proofs were verified from serialized traces alone:

- **RW-14:** five-constraint transitive UNSAT core. Full core is UNSAT; deleting each of the five core constraints individually yields SAT.
- **RW-09:** three-constraint universal Python-domain core. Python 3.12 branch is SAT; Python 3.9 branch is UNSAT because Requires-Python >=3.10; under the explicit universal quantifier the claim is UNSAT. Deleting each core element individually yields SAT.

These are subset-minimal cores, not minimum-cardinality cores.

### Marker and negative-control tests

The RW-07 attack demonstrates that activation conditions remain proof-relevant:

- complete attack fixture with sys_platform == win32 preserved on Linux -> VERIFIED_SAT;
- erasing the activation condition -> VERIFIED_UNSAT, demonstrating a deliberate semantic corruption that the conformance rules forbid adapters from introducing.

RW-02 remains the resolver-failure-but-SAT negative control. Resolver labels such as ResolutionImpossible or No solution found are not proof premises.

### Reproducibility status

The historical full-corpus results in this document are retained as research evidence. The current clean executable runner does not recreate all 18 serialized fixtures; it therefore treats the 18/18 result as historical rather than as freshly regenerated output.

The current runner independently regenerates:
- the finite committed verifier fixture;
- serialization round-trip for that fixture;
- hermetic replay for that fixture;
- subset-minimality for that fixture;
- 250 deterministic mutation cases;
- the current 64-world projection harness.

The broader 18-case corpus and 256-world extended search remain documented research records and are linked through `research/REPRODUCIBILITY_INDEX.md`.

## Serialization fuzzing and projection collision

A deterministic structural campaign executed 250 serialized mutations with **0 incorrectly accepted verified proofs**.

The extended projection search covered 256 native fixture worlds. After retaining explicit proof scope, there were **0 semantic projection collisions** and **0 cases where identical portable data plus different hidden native resolver state changed the correct proof result** in the tested fragment.

### Final decision

**A. TRACE-ONLY PROOF ARTIFACT VALIDATED — within the tested finite semantic fragment.**

The strongest supported statement is:

> After explicit proof-claim binding, a serialized resolvewhy-trace can serve as a self-contained proof-supporting evidence artifact for the tested finite semantic fragment: the verifier can reconstruct the proposition, respect quantified environment scope, independently establish SAT/UNSAT, validate subset-minimality, and fail closed on malformed, incomplete, or unsupported proof evidence without consulting native resolver or external state.

This does not establish arbitrary resolver semantics, ecosystem-wide interchange, maintainer acceptance, or production readiness.

H2d remains PARTIALLY SUPPORTED. H2e remains NOT TESTED.


## Executable implementation boundary — 2026-09-21

The committed `research/trace_only_verifier.py` is a research fixture verifier, not a general dependency resolver or universal proof engine.

It directly evaluates only:
- normalized version constraints supported by the fixture operators;
- explicit boolean dependency-edge activation;
- the recorded `Requires-Python >=3.10` compatibility rule;
- finite evaluation-domain quantification for existential/universal claims;
- explicit branch selection through `proof_claim.branch_ref`;
- complete candidate-domain coverage with attestation;
- proof-premise selection from declared semantic constraints;
- provenance reachability from proof premises to in-scope requirement/dependency/evidence references;
- artifact-reference integrity and the tested artifact `compatible` flag;
- the fixed executable policy contract used by the fixture.

It does not evaluate arbitrary PEP 508 markers, general prerelease/source policies, full artifact selection/build semantics, complete lockfile semantics, generic virtual/provided packages, or arbitrary resolver-specific metadata.

These omissions are deliberate. Unsupported semantics must not be inferred; the executable verifier therefore returns `INSUFFICIENT_EVIDENCE` or `INVALID_TRACE` rather than silently broadening its proof domain.
