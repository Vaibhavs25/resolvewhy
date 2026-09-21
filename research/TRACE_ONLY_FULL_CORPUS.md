# Trace-Only Full Corpus

**Date:** 2026-09-21  
**Status:** completed trace-only replay of all 18 corpus cases

## Scope

The input boundary is the evidence already represented by research/REAL_WORLD_TRACE_CORPUS.md: public issue/source evidence where that is the available boundary, plus the previously recorded local pip 25.1.1 / uv 0.10.0 reductions. Each case was serialized into a portable semantic trace fixture and then verified after native-state detachment.

This experiment is therefore a **full 18-case trace serialization/replay**, not a fresh live re-execution of every historical public issue.

## Result semantics

| Result | Exact research meaning |
|---|---|
| VERIFIED_SAT | The serialized finite semantic problem is satisfiable under its explicit proof scope, policy/context, and complete candidate coverage. |
| VERIFIED_UNSAT | The serialized finite semantic problem is unsatisfiable under its explicit proof scope and independently reconstructed semantics. |
| INSUFFICIENT_EVIDENCE | The trace is structurally valid, but proof-strengthening evidence is incomplete, bounded, unknown, or otherwise insufficient for the requested proof. |
| INVALID_TRACE | The artifact is structurally or semantically inconsistent: malformed scope, dangling references, unsupported completeness claim, invalid proof binding, etc. |

A declared resolver failure is never itself treated as an UNSAT proof.

## Full 18-case replay

| Case | Evidence basis | Corpus semantic interpretation | Trace-only result | Round-trip | Resolver access | Network | Undeclared FS |
|---|---|---|---|---|---|---|---|
| RW-01 | public pip issue + recorded reduction | UNSAT | VERIFIED_UNSAT | PASS | NO | NO | NO |
| RW-02 | public pip issue + reduced SAT fixture | SAT despite resolver failure | VERIFIED_SAT | PASS | NO | NO | NO |
| RW-03 | public pip issue | formal UNSAT not established | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-04 | public pip issue | decisive contradiction not exposed | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-05 | public pip issue | Requires-Python evidence incomplete in normal output | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-06 | public pip issue | source-scope dependent | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-07 | public uv issue + marker attack fixture | SAT under Linux marker semantics, but source coverage is incomplete | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-08 | public uv issue | 401/403 is not source exhaustion | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-09 | public uv issue + universal-domain fixture | UNSAT over declared Python support domain | VERIFIED_UNSAT | PASS | NO | NO | NO |
| RW-10 | public uv issue | cutoff/prerelease policy interaction | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-11 | public uv issue | yank policy differs | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-12 | public uv issue | artifact-level yank semantics | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-13 | public uv issue | marker/source split | INSUFFICIENT_EVIDENCE | PASS | NO | NO | NO |
| RW-14 | recorded pip/uv local reduction | five-constraint transitive UNSAT | VERIFIED_UNSAT | PASS | NO | NO | NO |
| RW-15 | recorded pip/uv local reduction | no compatible artifact on Linux | VERIFIED_UNSAT | PASS | NO | NO | NO |
| RW-16 | recorded pip/uv local reduction | candidate exists but Requires-Python is incompatible | VERIFIED_UNSAT | PASS | NO | NO | NO |
| RW-17 | recorded pip/uv local reduction | UNSAT under explicit prerelease-disallow policy | VERIFIED_UNSAT | PASS | NO | NO | NO |
| RW-18 | recorded pip/uv local reduction | source-qualified same-version candidates remain distinguishable | VERIFIED_SAT | PASS | NO | NO | NO |

## Aggregate result

- 18/18 cases matched the intended trace-only classification.
- 6/18 were VERIFIED_UNSAT: RW-01, RW-09, RW-14, RW-15, RW-16, RW-17.
- 2/18 were VERIFIED_SAT: RW-02, RW-18.
- 10/18 were INSUFFICIENT_EVIDENCE: RW-03, RW-04, RW-05, RW-06, RW-07, RW-08, RW-10, RW-11, RW-12, RW-13.
- 0/18 base corpus traces were INVALID_TRACE.
- 18/18 serialization round-trips preserved the verifier result.
- 18/18 isolated replay processes completed successfully.

## Two required nontrivial UNSAT proofs

### RW-14 — five-element transitive core

The independently reconstructed problem is:

appa==1 -> depA<2 and depB==1  
depA==1 -> leaf==1  
depA==2 -> leaf==2  
depB==1 -> leaf==2

with roots appa==1 and depB==1.

Reported core:

1. c:rw14:r-appa
2. c:rw14:r-depB
3. c:rw14:appa-depA
4. c:rw14:depA1-leaf
5. c:rw14:depB1-leaf

The complete core is VERIFIED_UNSAT. Removing each of those five constraints independently produced VERIFIED_SAT.

Therefore the reported core is **subset-minimal**. No minimum-cardinality claim is made.

### RW-09 — universal Python-domain core

Evaluation domain:

- Python 3.12/Linux
- Python 3.9/Linux

The same serialized candidate set contains numba==0.61.0 with Requires-Python >=3.10.

Branch results:

- Python 3.12: SAT
- Python 3.9: UNSAT

Under the explicit **universal** proof quantifier, the whole proposition is VERIFIED_UNSAT.

Core:

1. c:rw09:root
2. c:rw09:dep
3. c:rw09:python

Each single deletion produced VERIFIED_SAT. The core is therefore **subset-minimal**.

Additional two-element subset-minimal cores were verified for RW-15, RW-16, and RW-17.

## Negative control

RW-02 is the required resolver-failure-but-SAT control. Its serialized reduced semantic problem is satisfiable even though the corpus records a pip resolver failure.

The verifier ignores ResolutionImpossible / No solution found as proof data. Only reconstructed semantic constraints determine the result.

## Marker false-proof attack

RW-07 retains the activation condition:

sys_platform == "win32"

The runtime is Linux. When a complete finite candidate domain is supplied for the attack fixture:

- activation preserved -> VERIFIED_SAT
- activation deleted -> VERIFIED_UNSAT

The second outcome is a deliberate semantic corruption, demonstrating that marker activation is proof-relevant and must not be erased by normalization.

## Hermeticity

For each case, verification was executed in an isolated child process containing only:

1. the serialized trace;
2. the verifier;
3. a small worker that invokes the verifier.

The worker used Python isolated mode. An audit hook rejected:

- socket and urllib activity;
- subprocess execution;
- filesystem access outside the isolated directory.

No resolver package, provider implementation, package index, original issue report, resolver cache, or native resolver object was supplied to the verifier.

## Self-containment

For fully verified RW-14 and RW-09 traces, the serialized artifact makes all proof-bearing information recoverable:

| Question | Serialized source |
|---|---|
| What proposition is asserted? | proof_claim |
| Over which environment domain? | evaluation_domain |
| Under which policy? | resolution_policy |
| Which candidate universe is considered? | candidate_domains |
| Why is the candidate universe complete? | coverage status + attestation + evidence refs |
| Which dependencies are active? | dependency observations + activation conditions |
| Which constraints are proved? | semantic_constraints + proof premise refs |
| Which artifacts matter? | artifacts |
| Where proof-strengthening facts originated? | provenance + evidence_state |
| How was SAT/UNSAT established? | independent verifier |

## Limitation

The 18-case stage validates the serialized proof-supporting artifact boundary. It does not assert that every historical public issue has a complete machine-readable native trace available from its public output. Where the source boundary is incomplete, the correct result is INSUFFICIENT_EVIDENCE.

## Conclusion

The full 18-case trace-only experiment passes the stated safety criteria for the tested finite semantic fragment. The proof-claim binding repair is sufficient; no additional schema field was required.
