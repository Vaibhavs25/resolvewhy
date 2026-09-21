# Reproducibility Index

**Date:** 2026-09-21

This index maps the final research claims to the primary experiment, source document, harness, corpus/result record, and the relevant Git history where a commit is explicitly recorded.

| Claim | Experiment / evidence | Primary source file | Harness / code | Result reference / commit |
|---|---|---|---|---|
| Verified subset-minimal explanation is possible in the mathematical fragment | Mathematical core + adversarial repair history | research/REVISED_TRACE_ADVERSARIAL_AUDIT.md; research/REAL_WORLD_TRACE_VALIDATION.md | Core research harnesses in repository history | Five-element RW-14 core; related repair history |
| Real resolver structured evidence can be captured | Public architecture audit + controlled resolvelib instrumentation | research/H2E_ARCHITECTURE_AUDIT.md | resolvelib provider/reporter instrumentation described there | Architecture evidence; no ecosystem standard claimed |
| Revised evidence contract survives realistic adversarial cases | Revised-trace adversarial testing | research/REVISED_TRACE_ADVERSARIAL_AUDIT.md | Contract-level proof gate and local reductions | 8/8 adversarial contract checks |
| 18 realistic cases are represented safely or downgraded | Real-world corpus | research/REAL_WORLD_TRACE_CORPUS.md | Local pip 25.1.1 / uv 0.10.0 reductions | 18-case corpus; research/REAL_WORLD_TRACE_VALIDATION.md |
| Cross-resolver portability is partial | Portability experiment | research/H2D_CROSS_RESOLVER_VALIDATION.md; research/H2D_CONFORMANCE_MATRIX.md | research/portable_core_collision_search.py | Post-repair bounded portability result |
| Evaluation domain is semantically necessary for multi-environment claims | Projection collision search | research/PORTABLE_CORE_SUFFICIENCY.md | research/portable_core_collision_search.py | Commit associated with repair: evaluation-domain revision recorded in research history |
| Trace-only proof artifact works in tested fragment | Full trace-only replay | research/TRACE_ONLY_FULL_CORPUS.md | research/trace_only_verifier.py | 18/18 replay; 18/18 round-trips; 18/18 isolated replays |
| Explicit proof-claim binding is semantically necessary and then sufficient in the tested fragment | Proof-claim falsification | research/TRACE_PROOF_CLAIM_FALSIFICATION.md | research/trace_only_verifier.py | 250 mutation cases; 0 unsafe verified proofs |
| Post-repair portable projection is collision-free in tested worlds | Extended collision search | research/TRACE_PROOF_CLAIM_FALSIFICATION.md; research/FINAL_SEMANTIC_BOUNDARY.md | portable_core_collision_search.py / extended fixture methodology | 256 tested worlds; 0 post-repair collisions |
| Candidate coverage must be scoped and attested | Coverage adversarial audit | research/REVISED_TRACE_SCHEMA.md; research/TRACE_ARTIFACT_CONFORMANCE.md | Contract-level proof gate | Unsupported exhaustion rejected; incomplete evidence downgraded |
| Provenance is proof-bearing for an auditable artifact | Trace proof-claim falsification | research/TRACE_PROOF_CLAIM_FALSIFICATION.md | Trace-only verifier mutation checks | Provenance corruption fails closed |
| Final semantic boundary has no new defect | Final boundary/generalization audit | research/FINAL_SEMANTIC_BOUNDARY.md; research/BOUNDARY_CASES.md | Prior falsification/collision harnesses | Decision A; schema unchanged |
| H2e remains untested | Maintainer-validation record | research/H2E_RESPONSE_LOG.md; research/H2E_STATUS.md | Mailbox check record | 0 substantive responses |

## Key file map

| File | Role |
|---|---|
| research/REVISED_TRACE_SCHEMA.md | Current semantic trace contract |
| research/TRACE_PROOF_ARTIFACT_SPEC.md | Proof-supporting artifact requirements |
| research/TRACE_ARTIFACT_CONFORMANCE.md | Conformance/fail-closed requirements |
| research/REAL_WORLD_TRACE_CORPUS.md | 18-case semantic corpus |
| research/REAL_WORLD_TRACE_VALIDATION.md | Real-world validation results |
| research/H2D_CROSS_RESOLVER_VALIDATION.md | Cross-resolver portability analysis |
| research/H2D_CONFORMANCE_MATRIX.md | Portability field matrix |
| research/PORTABLE_CORE_SUFFICIENCY.md | Projection-collision evidence and repair |
| research/PORTABLE_CORE_MINIMALITY.md | Field necessity classification |
| research/TRACE_ONLY_FULL_CORPUS.md | 18-case serialized trace-only replay |
| research/TRACE_PROOF_CLAIM_FALSIFICATION.md | Proof-claim and mutation falsification |
| research/FINAL_SEMANTIC_BOUNDARY.md | Final semantic boundary |
| research/BOUNDARY_CASES.md | Near-boundary case catalogue |
| research/H2E_RESPONSE_LOG.md | Maintainer-response evidence |
| research/H2E_STATUS.md | Consolidated H2e status |
| research/FINAL_H2E_DECISION.md | H2e/final technical decision history |
| research/trace_only_verifier.py | Research trace-only verifier |
| research/portable_core_collision_search.py | Projection-collision harness |

## Explicit commit references

- `16c99428db037f5051155887c0f887be3fc9ca5e` — explicit evaluation-domain repair in the revised trace schema.
- `f01900a18e90240e4bbc9e9592a571fb7628b508e` — proof-artifact specification with proof-claim binding.
- `61d16be5e897bedfb5230fccad9ee36c07b922fe` — final trace-only verification update.
- `46a6ecb37073efd05ebdad9419508bf00772d655` — trace-only verifier aligned with explicit proof-claim structure.
- `c410cc403640e8ba1cace3905d94f01ffa674ff1` — README aligned with final research status.
- `df81cf6b3e59d8bb67ad8f3c0a6a400e484ced68` — final semantic-boundary/H2e status update commit.

These commit references identify repository states where those specific research updates were recorded; they are not claims that the commit contains every preceding experiment.