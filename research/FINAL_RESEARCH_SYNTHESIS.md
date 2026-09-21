# FINAL RESEARCH SYNTHESIS — resolvewhy

**Date:** 2026-09-21
**Status:** Technical validation complete for the declared semantic fragment; maintainer validation remains open.

## 1. Executive summary

`resolvewhy` investigated whether structured dependency-resolution evidence can be transformed into a small semantic representation from which an independent engine can compute and verify a subset-minimal explanation without relying on human-readable resolver diagnostics or native resolver state.

The research produced a bounded positive result, not a universal one. The mathematical explanation engine survived repeated adversarial testing after several genuine defects were exposed and repaired. The revised semantic trace also survived a real-world corpus, a cross-resolver portability study, a projection-collision search after repair, hermetic trace-only verification, proof-claim falsification, serialization mutation testing, and a final semantic-boundary audit.

The central technical result is therefore conditional: for a finite, explicitly serialized semantic fragment with explicit scope, candidate coverage, policy, provenance, and proof-claim binding, an independent verifier can reconstruct the semantic problem and independently establish SAT/UNSAT and subset-minimality without the original resolver.

The same body of evidence does **not** establish universal resolver coverage, a stable cross-ecosystem interchange format, complete build or lockfile semantics, or maintainer acceptance.

## 2. Research question

> Can sufficiently rich structured dependency-resolution evidence be represented in a portable semantic trace from which an independent verifier can compute and check a formally justified conflict explanation without parsing human-readable diagnostics or consulting native resolver state?

The project separates the mathematical question from the ecosystem/interface question.

## 3. Research hypotheses

| Hypothesis | Exact statement | Status | Strongest evidence | Strongest limitation | Upgrade requirement |
|---|---|---|---|---|---|
| H1 | Given sufficiently rich structured evidence, a downstream engine can compute a verified subset-minimal explanation. | SUPPORTED | Independent SAT/UNSAT reconstruction, subset-minimal cores, hermetic trace-only verification, negative controls, mutation testing. | Validated only for the declared finite semantic fragment and executed/reduced cases. | Broaden the independently verified semantic domain and preserve the same proof obligations. |
| H2a | Real resolver architectures can expose sufficiently rich structured evidence for downstream semantic analysis. | SUPPORTED | resolvelib provider/reporter instrumentation; rich structured concepts observed in pip, uv, Poetry and pipgrip. | Exposure is uneven and often implementation-specific. | Stable evidence exposure through real resolver APIs or equivalent sustained interfaces. |
| H2b | Resolver evidence can be normalized into a sufficiently faithful semantic model. | PARTIALLY SUPPORTED | Revised contract survived realistic adversarial cases after explicit coverage, identity, policy, provenance and scope repairs. | Some resolver/provider meanings remain different and require namespacing or lossiness. | Demonstrate faithful normalization over broader resolver and semantic coverage. |
| H2c | Normalized evidence is sufficient for independently verified UNSAT explanations and subset-minimal cores. | SUPPORTED | Controlled trace tests; real reduced transitive conflict; two trace-only subset-minimal proofs. | Proof depends on the declared finite fragment and complete evidence obligations. | Additional independently verified semantic classes would broaden the claim. |
| H2d | The semantic evidence abstraction is stable/portable across resolver ecosystems. | PARTIALLY SUPPORTED | pip/resolvelib ↔ uv semantic mapping; source-level Poetry/pipgrip mapping; zero post-repair projection collisions in tested worlds. | No stable public cross-resolver wire/API contract was established; native semantics differ. | Evidence of durable common semantics and actual stable interfaces across more ecosystems. |
| H2e | Resolver/package-manager maintainers validate the practical usefulness and feasibility of the abstraction. | NOT TESTED | Four successful individualized outreach attempts; no substantive response; one named contact not attempted because the connected account was suspended. | No maintainer technical feedback exists, so no conclusion about usefulness, maintenance cost, or adoption can be drawn. | Actual substantive maintainer analysis or other direct ecosystem validation. |

## 4. Methodological progression

The research did not proceed as a straight confirmation path. Each major expansion was used to search for a semantic failure mode.

1. **Original H1 hypothesis:** sufficiently rich structured evidence might permit a verified subset-minimal dependency-conflict explanation.
2. **Initial mathematical core:** normalized dependency constraints were used to compute candidate explanations.
3. **Initial defects:** forced explicit incompatibilities could yield false SAT; stale top-level reasons could disagree with the verified MUS; identity recursion and several evidence-completeness ambiguities were also exposed.
4. **Mathematical repair:** the core was repaired and checked against the prior regression suite and restricted oracle-generated instances.
5. **Controlled structured traces:** resolvelib provider/reporter instrumentation demonstrated that structured resolver evidence could be captured without scraping stderr and checked independently.
6. **Architecture audit:** public and source-level examination of resolvelib/pip, Poetry, pipgrip and uv showed that semantic concepts recur, but candidate discovery, rejection, conflict derivation, source/index behavior and artifact handling are split across different layers.
7. **Coverage repair:** the global candidate-completeness idea was replaced by scoped candidate-domain coverage with explicit attestation; resolver exhaustion was separated from external-source exhaustion.
8. **Real-world corpus:** 18 cases stressed transitive conflicts, resolver-failure-but-SAT behavior, source scope, authentication failures, markers, universal resolution, prerelease policy, Requires-Python, artifacts, VCS identity and yanks.
9. **Portability boundary:** the common semantic layer was narrowed so native incompatibility/derivation structures remain namespaced rather than being flattened into a universal object model.
10. **Projection collision:** a single-environment SAT world and a universal multi-environment UNSAT world had identical pre-repair portable projections.
11. **Evaluation-domain repair:** explicit quantified evaluation domains were added to the semantic proof model.
12. **Trace-only proof-artifact test:** verification was detached from native resolver state and run on serialized evidence.
13. **Proof-claim collision:** policy plus evaluation domain alone did not fully identify the proposition being proved.
14. **Proof-claim repair:** an explicit claim binds result kind, quantifier, evaluation domain and semantic premises.
15. **Full serialized replay:** all 18 corpus fixtures were replayed through the trace-only boundary.
16. **Final semantic-boundary audit:** nearest realistic cases outside the established fragment were catalogued; no new semantic defect was identified.
17. **Maintainer-validation experiment:** H2e remained NOT TESTED because no substantive maintainer response was obtained.

This history is itself part of the result: the abstraction was retained only after several stronger versions were falsified and narrowed.

## 5. Methodology

The research combined mathematical consistency checking, controlled resolver instrumentation, public architecture/source analysis, real-world issue-pattern synthesis, local pip/uv reductions, semantic projection collision searches, trace-only hermetic verification, fail-closed mutation campaigns, and proof-core deletion checks.

Public issue reports were treated as realistic semantic patterns and reproducibility sources, not automatically as authoritative native resolver traces. Poetry and pipgrip were source-validated in the local environment rather than executed.

The executable environment recorded in the repository is Python 3.13.5, pip 25.1.1 and uv 0.10.0.

## 6. Mathematical validation

The explanation problem is reduced to a semantic constraint system. A reported core is accepted only when the core itself is independently unsatisfiable and each individual core element, when deleted, yields a satisfiable system. This establishes subset-minimality, not minimum cardinality.

The repaired core also distinguishes mathematical satisfiability from evidence sufficiency. Resolver failure is observational data, not mathematical proof.

## 7. Structured evidence validation

The controlled and real-world evidence show that the common semantic layer must preserve the distinction among:

- root requirements and parent-linked dependency edges;
- active and inactive dependency edges;
- runtime context and resolver policy;
- candidate identity and artifact identity;
- candidate enumeration and candidate-domain completeness;
- observed rejection and exhaustive absence;
- semantic premises and resolver-native derivation objects;
- mathematical truth and provenance/auditability.

The resulting contract is intentionally small and semantically typed rather than a universal serialization of resolver internals.

## 8. Cross-resolver portability

H2d is **PARTIALLY SUPPORTED**.

The tested pip/resolvelib and uv mappings preserve common satisfiability-relevant roles for requirements, dependency edges, activation conditions, opaque candidate identity, artifact identity where needed, runtime context, policy, candidate-domain coverage, semantic literals, provenance and evidence state. Poetry/Mixology and pipgrip/PubGrub source structures provide additional evidence that several of these semantic roles recur.

However, native incompatibility structures, decision levels, backjump state, provider internals, index machinery, detailed artifact-selection pipelines and diagnostics do not have one safely universal interpretation. The research therefore supports semantic normalization with resolver-specific namespaces, not a universal native object model or stable interchange API.

## 9. Trace-only proof artifact

The final trace-only experiment establishes a bounded self-contained proof-artifact result.

Recorded outcomes:

- 18/18 serialized corpus cases matched the intended trace-only classification.
- 18/18 serialization round-trips preserved the semantic result.
- 18/18 isolated replay processes completed without resolver/provider/index/network/external-state access.
- 2 nontrivial subset-minimal UNSAT proofs were independently reconstructed from serialized traces alone in the historical full-corpus record; the current executable runner rechecks one committed finite proof fixture.
- 250 deterministic serialization mutations produced 0 incorrectly accepted verified proofs.
- the historical extended search reported 256 post-repair projection worlds with 0 semantic collisions; the current committed projection harness independently regenerates its 64-world subset and reports 0 post-repair collisions there.
- the declared resolver-result label was not trusted over independently reconstructed semantics.

These counts are deliberately separated into executable and historical evidence in `research/REPRODUCIBILITY_INDEX.md`; none is presented as exhaustive testing of the semantic space.

## 10. Final semantic boundary

### Inside current guarantee

- normalized version constraints and conjunctions;
- parent-linked dependency edges;
- tested activation/marker semantics;
- opaque and source-aware candidate identity;
- candidate/artifact separation where artifact feasibility matters;
- explicit runtime context;
- finite explicit evaluation domains;
- singleton, existential, universal and branch proof scopes within that finite domain model;
- resolution policy where it affects admissibility;
- scoped candidate-domain coverage with completeness attestation;
- normalized semantic constraints/literals;
- evidence state and provenance reachability;
- explicit proof-claim binding;
- independent SAT/UNSAT reconstruction;
- subset-minimality by individual deletion.

### Supported only in reduced/tested form

- richer nested PEP 508 marker combinations and all extras interactions;
- complex multi-dimensional environment partitions;
- wheel/sdist mixtures and detailed artifact selection;
- local/editable/workspace candidates;
- hash constraints and reproducibility policies;
- lockfile restrictions and environment branches;
- richer source/index selection semantics.

### Outside current guarantee

- arbitrary dynamic build-backend metadata generation;
- hidden build-environment effects;
- complete wheel/sdist build-selection and build-failure semantics;
- complete cross-resolver hash/reproducibility semantics;
- complete lockfile semantics;
- implicit virtual/provided/system-package satisfaction relations;
- symbolic or infinite environment-domain reasoning;
- exhaustive arbitrary PEP 508 semantics;
- future resolver-specific semantics not represented by the normalized model.

Outside the current guarantee means **not established by the evidence**, not impossible.

## 11. Important failure history

| Defect | Exposure | Repair | Validation after repair |
|---|---|---|---|
| Forced explicit incompatibility could yield false SAT | Adversarial mathematical-core testing | Strengthened contradiction semantics and regressions | Repaired regression suite and restricted independent oracle validation passed |
| Stale top-level reason could describe a different conflict than the verified MUS | Explanation-integrity adversarial testing | Bind explanation/core computation to the actual verified semantic conflict | Repair regression passed; verified cores matched the intended constraints |
| Global candidate completeness was too strong | Architecture audit of provider/finder/source boundaries | Replace global completeness with per-domain/query coverage | Revised contract adversarial checks passed |
| Resolver exhaustion was confused with external-domain exhaustion | Provider/source architecture analysis | Require explicit candidate-domain scope and completeness attestation | No-candidate proof gate rejected unsupported exhaustion claims |
| `evaluation_domain` was absent from the portable projection | Automated 64-world collision search | Add explicit evaluation domain for quantified claims | Post-repair collision search found 0 collisions |
| Proof-claim quantifier/domain scope was implicit | Trace-only proof-claim falsification | Explicit proof claim binding quantifier + domain + premises | Full repaired replay passed |
| Provenance was treated too coarsely | Trace-only auditability mutation | Enforce proof-premise provenance reachability | Corrupted provenance failed closed |
| Inactive marker could be flattened into a universal conflict | uv real-world false-normalization case | Preserve activation condition and independently recompute semantics | Attack was rejected; preserved-marker case retained correct non-conflict semantics |

The sequence demonstrates that the final model is the result of falsification and repair, not only positive examples.

## 12. What the project contributes

### Mathematical contribution

The work demonstrates a concrete independent explanation procedure for a bounded dependency-constraint fragment. The key property is not merely finding a conflict, but rechecking the claimed explanation independently and establishing subset-minimality by deletion.

This is presented as a demonstrated research result rather than a claim of mathematical novelty beyond the repository's evidence.

### Systems/research contribution

The work develops a resolver-neutral semantic evidence boundary that separates portable satisfiability facts from resolver-specific operational structures. In particular, it treats candidate-domain completeness, candidate identity, artifact identity, runtime context, resolution policy, evaluation domain, proof claims and provenance as first-class proof concerns.

### Methodological contribution

The strongest methodological result is the fail-closed proof-artifact discipline: incomplete evidence becomes `INSUFFICIENT_EVIDENCE`; malformed/inconsistent traces become `INVALID_TRACE`; resolver diagnostics do not become proofs; and native solver state is not silently consulted as a fallback.

No novelty claim is made for any individual algorithmic ingredient unless separately established by the mathematical literature; the contribution here is the tested combination and evidence boundary.

## 13. Maintainer-validation gap

H2e remains **NOT TESTED**.

The repository records four successful individualized outreach attempts to maintainers associated with resolvelib/pip, pip/PyPA, Poetry and pipgrip. A fifth named maintainer associated with uv was not contacted because the connected Outlook account was suspended. The mailbox check recorded zero substantive responses. Silence and contact failure were not treated as technical evidence.

Maintainer feedback would add information that technical experiments cannot provide, including practical feasibility of exposing the evidence, maintenance burden, preferred API boundaries, stability concerns, usefulness to downstream tooling, and alternative designs. None of those questions has been answered by the current evidence.

H2e is separate from the mathematical foundation: the absence of feedback does not weaken the verified proof results; it leaves the practical interface/adoption question unresolved.

## 14. Production-readiness audit

### Proven enough for research prototype

- the bounded mathematical explanation engine;
- controlled structured-trace capture in the tested resolver architecture;
- semantic normalization for the tested fragment;
- fail-closed evidence/coverage semantics;
- serialized trace-only verification in the tested fragment;
- subset-minimal explanation verification.

### Not proven enough for production

- stable public adapter APIs for real resolver versions;
- versioned trace-schema compatibility guarantees over time;
- performance and memory overhead under large real-world resolution graphs;
- complete package metadata and build-system semantics;
- complete wheel/sdist and hash-policy semantics;
- complete lockfile semantics;
- security and trust model for completeness attestations and provenance;
- long-term backward/forward compatibility;
- broad multi-ecosystem conformance testing;
- maintainership and operational ownership;
- independently reviewed production conformance suites.

Accordingly, production implementation is a separate future decision and is not justified by the present research evidence alone.

## 15. Repository publication/readiness audit

The research history should remain intact. The repository now has a dedicated final semantic boundary and conformance record, but historical status documents still contain earlier intermediate conclusions. Those historical sections should be preserved rather than rewritten, because they document the falsification path.

The current README has been aligned to the final high-level status, including the bounded technical result, partial H2d, untested H2e, explicit exclusions, and research-only status.

The public RFC remains an **experimental research artifact**. It should be understood as a research question and semantic proposal, not as an endorsed ecosystem specification. It still contains the original illustrative v0 concepts; the research records elsewhere in the repository contain the later semantic repairs. This is a documentation-versioning issue, not evidence of technical invalidity.

## 16. Reproducibility map

| Claim | Primary evidence | Code/harness | Result artifact |
|---|---|---|---|
| Mathematical core can produce verified subset-minimal explanations | Revised adversarial/core-validation history | Core research harnesses recorded in the repository history | Real-world validation records and final decision documents |
| Structured resolver evidence can be captured | H2e architecture audit + controlled trace work | resolvelib instrumentation described in repository | H2E_ARCHITECTURE_AUDIT.md |
| Revised coverage/identity/policy contract is safe on tested cases | REVISED_TRACE_ADVERSARIAL_AUDIT.md | Contract-level proof gate and local reductions | Same report |
| 18-case realistic semantic corpus was analyzed | REAL_WORLD_TRACE_CORPUS.md | Local pip/uv reductions for executable cases | REAL_WORLD_TRACE_VALIDATION.md |
| Cross-resolver semantic portability is partial | H2D_CROSS_RESOLVER_VALIDATION.md / H2D_CONFORMANCE_MATRIX.md | portable_core_collision_search.py plus adapter fixture mappings | PORTABLE_CORE_SUFFICIENCY.md |
| Evaluation-domain omission caused a real projection collision | PORTABLE_CORE_SUFFICIENCY.md | portable_core_collision_search.py | Same document |
| Trace-only artifact is self-contained in the tested fragment | TRACE_ONLY_FULL_CORPUS.md | trace_only_verifier.py | TRACE_ONLY_FULL_CORPUS.md + TRACE_PROOF_ARTIFACT_SPEC.md |
| Proof-claim binding survives adversarial mutation | TRACE_PROOF_CLAIM_FALSIFICATION.md | trace-only verifier / mutation harness | Same report |
| Final semantic boundary has no new defect | FINAL_SEMANTIC_BOUNDARY.md / BOUNDARY_CASES.md | Prior collision/mutation harnesses | FINAL_SEMANTIC_BOUNDARY.md |
| Maintainer validation remains open | H2E_RESPONSE_LOG.md | Mailbox execution record | H2E_STATUS.md / FINAL_H2E_DECISION.md |

## 17. What has been demonstrated

1. For the tested bounded semantic fragment, structured evidence can be normalized into a proof-supporting semantic artifact.
2. The semantic artifact can be detached from the original resolver and independently checked.
3. Candidate coverage and proof scope are proof obligations, not cosmetic metadata.
4. Resolver-native derivations can be omitted from correctness computation once their semantic consequences are normalized.
5. Incomplete or malformed evidence can be rejected rather than silently converted into a proof.
6. Subset-minimal explanations can be independently checked for nontrivial reduced dependency conflicts.

## 18. What remains unproven

- universal semantic completeness across dependency resolvers;
- stable public cross-resolver trace interchange;
- complete PEP 508 semantic preservation;
- dynamic build-system reconstruction;
- complete artifact/build/hash/lockfile semantics;
- arbitrary virtual/provided package behavior;
- symbolic or infinite environment quantification;
- practical production cost and performance;
- maintainer acceptance, usefulness or adoption.

## 19. Final research conclusion

### Technical conclusion

> Within the tested finite semantic fragment—normalized dependency/version constraints, parent-linked dependency edges, activation conditions, opaque/source-aware candidate identity, artifact identity where artifact feasibility matters, explicit runtime context and finite evaluation domains, resolution policy, scoped candidate-domain coverage with completeness attestation, semantic literals, provenance/evidence state, and explicitly bound proof claims—`resolvewhy-trace` preserves sufficient satisfiability-relevant evidence for an independent verifier to establish SAT/UNSAT and subset-minimal explanations, while incomplete evidence and unsupported semantics fail closed.

This conclusion is conditional on the declared semantic fragment and on the evidence actually being serialized with the required proof scope, coverage and provenance.

### Portability conclusion

H2d is **PARTIALLY SUPPORTED**. The experiments support a bounded semantic portability layer for the tested resolver-shaped evidence, while native resolver derivations, decision state, provider internals and other implementation structures remain namespaced or optional. A stable ecosystem-wide trace/API standard has not been established.

### External-validation conclusion

H2e is **NOT TESTED**. The repository contains no substantive maintainer feedback. Therefore the project has no empirical basis for claiming maintainer acceptance, practical ecosystem support or adoption.

## 20. Research stopping point

**TECHNICAL VALIDATION COMPLETE FOR THE DECLARED SEMANTIC FRAGMENT.**

**MAINTAINER VALIDATION REMAINS OPEN.**

**PRODUCTION IMPLEMENTATION REMAINS A SEPARATE FUTURE DECISION.**