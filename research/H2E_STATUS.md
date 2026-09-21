# H2e status

Maintainer-validation status: **NOT TESTED**

## Public-architecture validation — 2026-09-21

An independent adversarial architecture audit was completed against current upstream source/documentation for:

- resolvelib / pip
- Poetry / Mixology
- pipgrip / PubGrub
- uv / PubGrub

This audit is technical architecture evidence only. It does not constitute maintainer validation.

### Architecture result

The semantic evidence abstraction remains technically plausible, but the current resolvewhy-trace/v0 wire semantics are too coarse in several places.

**Architecture decision: REVISE resolvewhy-trace/v0.**

Required revisions:

1. Replace trace-wide candidate_inventory_complete with per-candidate-query/domain coverage metadata.
2. Preserve opaque adapter-defined candidate identity.
3. Type rejection evidence by reason kind and source layer.
4. Namespace resolver-specific incompatibility/derivation semantics.
5. Separate runtime context from resolution policy.
6. Require explicit provenance for derived claims.
7. Keep resolver state, source/index details and artifact selection optional and provider/resolver-specific.

These changes narrow the resolver-neutral proof core while preserving the central semantic model.

## H2 decomposition

- **H2a:** SUPPORTED, narrowly through resolvelib structured provider/reporter instrumentation. Other resolver families also contain rich structured evidence internally, but this does not establish one stable public API.
- **H2b:** PARTIALLY SUPPORTED. Controlled traces normalize successfully, but the audit found semantic differences requiring the v0 revisions above.
- **H2c:** SUPPORTED in the controlled traces already benchmarked.
- **H2d:** **UNPROVEN.** The audited architectures share semantic concepts, but a stable portable cross-resolver failure-trace interface was not established.
- **H2e:** **NOT TESTED.** There are still 0 substantive maintainer responses.

## Reproducible sanity checks

The local sandbox currently contains Python 3.13.5, pip 25.1.1 and uv 0.10.0.

A local pip experiment using two minimal wheels showed:

- satisfiable dry-run + --report produced the stable version-1 installation report
- an intentionally contradictory local resolution failed with exit code 1 and produced no report file
- failure output remained human-readable ResolutionImpossible

A local uv experiment using two minimal local wheels and conflicting root requirements showed:

- exit code 1
- human-readable “No solution found” output
- no machine-readable failure-trace file emitted by the tested CLI invocation

Poetry and pipgrip were not installed in the sandbox, so their validation was source-based rather than executable.

## Scientific interpretation

The strongest defensible technical statement is:

> Real resolver architectures contain sufficiently rich structured concepts for a resolver-neutral semantic evidence layer to be plausible, but trustworthy downstream proofs require explicit candidate-domain coverage and preservation of resolver/provider-specific provenance and conflict semantics.

This does not establish:

- maintainer support
- ecosystem adoption
- standardization
- production readiness
- stable cross-ecosystem API portability

No maintainer response has been invented or inferred.

## Current gate — historical stage

**CONTINUE RESEARCH** was the status at this intermediate stage, before the subsequent real-world corpus, portability, trace-only, and final semantic-boundary work recorded later in this file.

The current repository state is documented in the final research synthesis: technical validation is complete for the declared semantic fragment; H2d is PARTIALLY SUPPORTED; H2e is NOT TESTED; production implementation remains a separate future decision.


## Real-world trace validation — 2026-09-21

A falsification-oriented corpus of 18 cases was evaluated using public pip/uv/Poetry issue reproductions plus executable pip 25.1.1 and uv 0.10.0 reductions on Linux x86_64 / Python 3.13.5.

Technical findings:
- a nontrivial transitive conflict produced an independently verified subset-minimal five-constraint UNSAT core;
- incomplete source coverage, authentication failures, omitted Requires-Python evidence, and bounded discovery correctly block no-candidate proofs;
- marker-conditioned dependencies, prerelease policy, Requires-Python, platform artifacts, VCS/direct identity, yanks, source-specific behavior, and universal Python splits are representable without flattening them into universal clauses;
- one concrete unsafe adapter normalization was identified: erasing an inactive marker and copying a resolver-native conflict as universal UNSAT. The revised contract rejects this, so no schema revision was required;
- no tested case forced an unrepresentable semantic fact.

### H2 status after real-world validation

- **H2a:** SUPPORTED narrowly; real-world resolver/provider layers expose structured semantic evidence, though exposure is uneven.
- **H2b:** PARTIALLY SUPPORTED; the revised semantic model remains safe on the tested complex cases.
- **H2c:** SUPPORTED for the tested reduced real-world pattern; independent verification and subset-minimality remain possible.
- **H2d:** **UNPROVEN**; this experiment does not establish a stable portable cross-resolver interchange interface.
- **H2e:** **NOT TESTED**; there are still **0 substantive maintainer responses**.

The real-world result therefore strengthens technical feasibility evidence without changing the separate maintainer-validation gate.


## H2d cross-resolver portability validation — 2026-09-21

A direct portability experiment compared minimal semantic mappings from pip/resolvelib and uv, with source-level mappings for Poetry/Mixology and pipgrip/PubGrub.

Result:
- **H2d: PARTIALLY SUPPORTED — PORTABILITY BOUNDARY MUST BE NARROWED.**
- The tested resolver pair can preserve the same satisfiability-relevant semantic facts for requirements, dependency edges, activation conditions, opaque candidate identity, artifact identity, runtime context, policy, candidate-domain coverage, semantic constraints, provenance, and evidence state.
- Native incompatibility/rejection objects, derivation trees, decision levels, backjump state, provider internals, index machinery, and human-readable diagnostics do not have one safely universal meaning and remain namespaced/optional.
- The known uv conditional-marker case successfully serves as an unsafe-normalization attack: erasing the marker and promoting the native conflict to a universal clause is rejected by the semantic proof boundary.
- No tested semantic concept was forced into NOT REPRESENTABLE.

This is technical portability evidence for the tested resolver pair and cases. It does not establish ecosystem-wide interchange or API stability.

### H2e remains separate

**H2e: NOT TESTED.** The cross-resolver experiment provides no maintainer feedback and does not alter the 0 substantive-response status.


## Portable semantic core sufficiency falsification — 2026-09-21

A direct projection-collision experiment tested the proposed portable proof core rather than native resolver compatibility alone.

A finite search over 64 pip-style and uv-style native fixture worlds found a genuine pre-repair collision for universal/forked claims:

- active runtime context was identical;
- candidate, dependency, policy, coverage, provenance, and evidence fields were identical;
- one world was scoped only to Python 3.13/Linux and was SAT;
- the other was scoped to Python 3.13/Linux plus Python 3.9/Linux and was UNSAT because the available candidate required Python >=3.10.

The missing semantic fact was the quantified evaluation domain. The current core therefore was not sufficient for multi-environment proof claims.

The smallest repair was an explicit evaluation_domain proof-scope concept, distinct from runtime context and resolution policy. After repair, the same search found 0 projection collisions.

Technical interpretation:
- H2d remains **PARTIALLY SUPPORTED**;
- the portable core is now bounded by an explicit evaluation-domain requirement for universal/forked claims;
- native derivation trees, decision levels, candidate ordering, and similar resolver state remained removable for correctness in the tested fragment;
- this experiment does not establish universal completeness.

**H2e remains NOT TESTED.** No maintainer feedback was involved and the 0 substantive-response status is unchanged.


## Trace-only verification — 2026-09-21

A hermetic trace-only verification experiment was started against the repaired portable core. The verifier consumes only a serialized semantic trace and verifier code; native resolver objects, resolver source, package indexes, network access, and human-readable diagnostics are not used by the proof computation.

The experiment established the proof-artifact validity boundary for the tested fragment:
- missing required structural fields -> INVALID_TRACE;
- complete candidate coverage without an attestation -> INVALID_TRACE;
- incomplete/unknown evidence -> INSUFFICIENT_EVIDENCE;
- dangling candidate/dependency/coverage references -> INVALID_TRACE;
- a serialized transitive contradiction can be reconstructed and classified without native resolver state.

The current committed harness is research/trace_only_verifier.py. The trace-only result is technical evidence only and does not affect H2e.

**H2e remains NOT TESTED — 0 substantive maintainer responses.**

## Trace-only verification update — 2026-09-21

The trace-only experiment found a proof-artifact boundary issue: a multi-environment result cannot be fully specified by runtime context plus a universal/fork policy and evaluation domain alone. The proof claim itself must explicitly bind its quantifier to the evaluation domain and to the semantic premises being verified.

This is a genuine semantic requirement for a self-contained proof artifact, so the revised schema was updated with an explicit proof-claim concept. The committed trace-only verifier also enforces structural integrity before semantic reasoning and distinguishes INVALID_TRACE from INSUFFICIENT_EVIDENCE.

The trace-only harness demonstrates hermetic reconstruction of a serialized contradiction without consulting native resolver state. Full corpus-scale trace-only replay remains bounded by the finite verifier fragment currently implemented in the research harness.

H2d remains PARTIALLY SUPPORTED. H2e remains NOT TESTED with 0 substantive maintainer responses.

## Final trace-only verification — 2026-09-21

The repaired proof-claim semantics were exercised in a full 18-case serialized replay. Each case was verified after native-state detachment using only the serialized trace and the research verifier.

Results:
- 18/18 traces matched the intended trace-only classification.
- VERIFIED_UNSAT: RW-01, RW-09, RW-14, RW-15, RW-16, RW-17.
- VERIFIED_SAT: RW-02, RW-18.
- INSUFFICIENT_EVIDENCE: RW-03, RW-04, RW-05, RW-06, RW-07, RW-08, RW-10, RW-11, RW-12, RW-13.
- INVALID_TRACE: 0 base corpus traces.
- 18/18 serialization round-trips preserved the result.
- 18/18 isolated replays completed without resolver, provider, index, network, or undeclared filesystem access.

Two nontrivial subset-minimal UNSAT proofs were independently rechecked from serialized traces: RW-14 (five-element transitive core) and RW-09 (three-element universal Python-domain core).

A deterministic 250-case structural mutation campaign accepted 0 malformed/corrupted artifacts as verified proofs. An extended 256-world projection search produced 0 post-repair semantic collisions and 0 cases where identical portable data plus different hidden native state changed the correct proof result in the tested fragment.

The proof-claim repair therefore resolves the previously observed quantifier/domain binding gap. No additional schema field was required.

**Trace-only result: A. TRACE-ONLY PROOF ARTIFACT VALIDATED — within the tested finite semantic fragment.**

**H2e remains NOT TESTED.** The corpus and verifier experiments contain no maintainer feedback and do not count as maintainer validation.

Production architecture remains NOT APPROVED.

## Final semantic-boundary audit — 2026-09-21

The final adversarial semantic-boundary/generalization audit found no new semantic defect within the already declared finite portable fragment.

The boundary is now explicitly recorded in:
- research/FINAL_SEMANTIC_BOUNDARY.md
- research/BOUNDARY_CASES.md

The audit identifies the nearest realistic cases outside the established guarantee as dynamic build-time metadata generation and hidden build-environment effects, complete lockfile/hash semantics, arbitrary virtual/provided-package satisfaction relations, and symbolic/infinite environment-domain reasoning. These are evidence boundaries, not demonstrated schema defects.

No schema change was made.

H2e remains NOT TESTED and is unaffected by this technical experiment.

## Current-status reconciliation note — 2026-09-21

The opening sections of this file preserve dated intermediate research states. They are historical and superseded by the later dated updates in this same file and by `research/FINAL_RESEARCH_SYNTHESIS.md`.

**Current status:** H2d = PARTIALLY SUPPORTED; H2e = NOT TESTED; technical validation = complete for the declared finite semantic fragment; production implementation = separate future decision.

The clean reproducibility runner is intentionally narrower than the historical research record. It regenerates the 250-case mutation campaign and the current 64-world projection harness, but it does not regenerate the historical 18-case serialized corpus or the historical 256-world extended search.
# Current status marker

All sections above this marker are dated historical research stages. They are retained verbatim for auditability and are superseded by the latest sections below.

**CURRENT:** H2d = PARTIALLY SUPPORTED; H2e = NOT TESTED; technical validation = complete for the declared finite semantic fragment; production implementation = separate future decision.

See `research/FINAL_RESEARCH_SYNTHESIS.md` and `research/REPRODUCIBILITY_INDEX.md` for the consolidated current interpretation.