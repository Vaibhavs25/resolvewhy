# Trace Proof-Claim Falsification

**Date:** 2026-09-21

## 1. Proof-claim semantics

A proof-supporting artifact carries an explicit claim containing:

- result kind;
- quantifier;
- evaluation_domain_ref;
- semantic premise_refs.

The claim is a proposition to be independently checked. It is never treated as authoritative evidence.

For the bounded finite-domain verifier:

- universal: SAT iff every declared environment branch is SAT; UNSAT if any branch is UNSAT;
- existential: SAT iff at least one branch is SAT; UNSAT iff none are SAT;
- branch: evaluate only the explicitly named environment.

## 2. Minimal-pair and mutation results

| Mutation / comparison | Trace-only result |
|---|---|
| RW-09 universal -> existential | VERIFIED_SAT |
| remove quantifier | INVALID_TRACE |
| remove evaluation_domain_ref | INVALID_TRACE |
| wrong evaluation_domain_ref | INVALID_TRACE |
| remove premise_refs | INVALID_TRACE |
| unrelated premise refs | VERIFIED_SAT |
| claim UNSAT on the RW-02 SAT fixture | VERIFIED_SAT |
| claim SAT on the RW-14 UNSAT fixture | VERIFIED_UNSAT |
| valid branch claim on RW-09 Python 3.12 | VERIFIED_SAT |
| promote that branch claim to universal | VERIFIED_UNSAT |

The RW-09 universal/existential pair is the key semantic test: the proposition itself changes, and the verifier follows the changed scope rather than a resolver policy flag.

Claim/result disagreement tests also show that status_claim is not trusted.

## 3. Coverage × proof-claim interaction

| Attack | Result |
|---|---|
| partial candidate coverage + universal UNSAT | INSUFFICIENT_EVIDENCE |
| incomplete evaluation domain | INSUFFICIENT_EVIDENCE |
| missing proof quantifier | INVALID_TRACE |
| complete coverage with no attestation | INVALID_TRACE |

A candidate list observed from a bounded or failed source query cannot become an exhaustive no-candidate proof.

## 4. Provenance reachability

The proof graph enforced by the verifier is:

proof claim -> semantic premise -> provenance record -> evidence observation.

The following mutations were tested:

| Mutation | Result |
|---|---|
| remove provenance records | INVALID_TRACE |
| remove provenance links | INVALID_TRACE |
| replace provenance evidence with unrelated scoped evidence | INVALID_TRACE |
| create provenance cycle | INVALID_TRACE |
| create dangling provenance ref | INVALID_TRACE |
| mark proof evidence incomplete | INSUFFICIENT_EVIDENCE |

This preserves the distinction between mathematical constraint content and proof auditability. An artifact outside the proof-supporting contract cannot silently be treated as a verified proof.

## 5. Serialization fuzzing

A deterministic 250-case structural campaign mutated:

- IDs;
- references;
- arrays;
- evaluation-domain objects;
- quantifiers;
- coverage attestations;
- provenance references;
- candidate/artifact links;
- requirement references;
- proof premise references.

Results:

- mutations: 250
- incorrectly accepted as a verified proof: 0
- all mutation attacks failed closed: YES

## 6. Projection-collision search

The extended search generated 256 semantic worlds across two resolver-shaped native evidence families. It varied:

- evaluation domain;
- proof quantifier;
- candidate coverage;
- prerelease policy;
- activation state;
- artifact compatibility;
- provenance state;
- hidden native decision state.

Before proof scope was retained in the projection, the search exposed 2 collision groups representing one semantic collision family.

After proof scope was retained:

- post-repair semantic collisions: 0
- same portable trace + different hidden native state + different proof result: 0

This is evidence that proof scope is semantic while native decision/derivation state is removable for correctness in the tested fragment.

## 7. Result of the falsification stage

No second semantic defect was found after the explicit proof-claim repair.

The combined evidence is:

- full 18-case replay passed;
- 2 nontrivial subset-minimal UNSAT proofs passed;
- 2 SAT cases passed;
- incomplete cases downgraded to INSUFFICIENT_EVIDENCE;
- 250/250 structural mutation attacks failed closed;
- 256-world post-repair collision search found 0 semantic collisions;
- hermetic replay succeeded without native resolver or external state.

The appropriate scientific result is therefore:

**A. TRACE-ONLY PROOF ARTIFACT VALIDATED — within the tested finite semantic fragment.**

This is not an ecosystem standard and does not establish resolver-wide completeness or maintainer acceptance.
