# Final H2e decision

## Current status

**H2e: NOT TESTED**

No substantive maintainer feedback has been received.

The public architecture experiments performed on 2026-09-21 are independent technical evidence and do not count as maintainer validation.

## Public artifact

Repository:
https://github.com/Vaibhavs25/resolvewhy

RFC:
https://github.com/Vaibhavs25/resolvewhy/issues/2

## Previous H2e state

Four individualized messages were successfully sent through Outlook to:

1. Damian Shaw — resolvelib / pip
2. Pradyun Gedam — pip / PyPA
3. Randy Döring — Poetry
4. ddelange — pipgrip

Charlie Marsh — uv / Astral — was not contacted because the connected Outlook account returned HTTP 403 due to account suspension.

The last mailbox check found **0 substantive responses**.

That status remains unchanged.

## Public-architecture audit

The audit examined current upstream source/documentation for:

- resolvelib 1.2.2.dev0 — commit a0cb7c50b78028f840b238d8e1c391e0546f2325
- pip 26.3.dev0 source tree — commit 892d13b34a20b3244a05d90622bbb5bf8e7ccf46
- Poetry 2.5.1 — commit 94b6e35b9091991887aa54feeb3771a86d3bd692
- pipgrip current repository HEAD — commit 195dfe41f9efa7abe161d6d69368e35939867b33
- uv 0.10.0 source tree — commit a1b84bcbda122236faae8fa5fdcbe16cfb76cde2

Executable local environment:

- Python 3.13.5
- pip 25.1.1
- uv 0.10.0

Poetry and pipgrip were source-validated because their executables were not installed.

## Revised-contract experiment

The revised contract was tested against local real resolver behavior covering:

- multiple index/source scopes
- platform-only artifacts
- Requires-Python
- prerelease policy
- direct URLs
- local VCS identity
- invalid/incomplete package metadata
- subset/bounded discovery
- artifact-level rejection
- same name/version from different sources

A tiny adversarial proof gate passed **8/8** contract checks.

No tested case produced a false proof after applying the revised semantics.

## Important result

The original revision was tightened once more during adversarial review:

> Resolver exhaustion alone is not sufficient to prove that the external candidate universe is exhaustive.

A resolver can exhaust a candidate set returned by a provider while the provider has only observed a subset of a larger source universe.

Therefore candidate completeness must be:

- scoped to an explicit candidate domain;
- tied to source/index/query scope;
- supported by an explicit exhaustion/authority attestation;
- connected to evidence references;
- interpreted only within that declared domain.

## Architecture decision

### KEEP unchanged

Rejected.

The original v0 semantics were too coarse at candidate completeness, identity, rejection, and conflict boundaries.

### ABANDON

Rejected.

The audited resolver families contain recurring semantic concepts sufficient to make a resolver-neutral layer technically plausible.

### NARROW only

Insufficient.

The proof core should be small, but it also needs explicit coverage and provenance semantics.

### REVISE

**Selected.**

The revised contract is defined in:

research/REVISED_TRACE_SCHEMA.md

The adversarial experiment is recorded in:

research/REVISED_TRACE_ADVERSARIAL_AUDIT.md

The field-level audit is in:

research/TRACE_FIELD_AUDIT.md

## H2 decomposition

| Hypothesis | Current state | Evidence |
|---|---|---|
| H2a | SUPPORTED narrowly | Real structured instrumentation exists through resolvelib; other systems expose rich structured internals |
| H2b | PARTIALLY SUPPORTED | Normalization survives the tested cases after explicit coverage/identity/policy revisions |
| H2c | SUPPORTED in controlled traces | Prior 6/6 real UNSAT trace verification and independent core validation |
| H2d | UNPROVEN | Semantic concepts recur, but a stable portable external trace interface has not been established |
| H2e | NOT TESTED | 0 substantive maintainer responses |

## What the experiment supports

The strongest defensible technical statement is:

> A resolver-neutral semantic evidence layer is technically plausible for the tested dependency-resolution evidence classes, provided that candidate-domain coverage, candidate identity, provenance, runtime context, resolution policy, and resolver-specific conflict semantics are represented explicitly.

## What remains unproven

- whether maintainers consider the abstraction useful
- whether maintainers would expose the required evidence
- whether a stable public trace API is acceptable
- whether the revised semantics remain practical across more ecosystems
- whether difficult real-world build/artifact cases can be represented without excessive adapter complexity
- whether downstream tooling would adopt the model

## Final research decision

**CONTINUE RESEARCH**

More specifically:

**The revised contract survives the current adversarial experiment, but production infrastructure remains unjustified.**

The next high-value work is to expand adversarial real-world coverage or obtain substantive maintainer feedback. H2e remains a separate empirical gate.

No maintainer support, ecosystem adoption, standardization, or production readiness is claimed.


## Real-world validation update — 2026-09-21

The latest falsification experiment expanded the evidence base from controlled traces to a corpus of 18 substantially more realistic dependency-resolution cases drawn from public pip, uv, and Poetry issue reports, together with executable pip 25.1.1 and uv 0.10.0 reductions.

### Technical result

**A. REAL-WORLD VALIDATION PASSES**

The revised contract survived the corpus without a new semantic defect requiring schema revision.

The strongest evidence is not the number of passing cases but the boundary behavior:
- a nontrivial transitive conflict yielded an independently verified subset-minimal UNSAT core;
- source-local emptiness and authentication failures did not authorize global no-candidate proofs;
- marker activation, artifact identity, prerelease policy, Requires-Python, source identity, yanking, and universal-resolution splits remained semantically distinguishable;
- a real resolver-failure-but-satisfiable pattern was retained as a negative control;
- an unsafe adapter normalization was explicitly demonstrated and rejected: flattening an inactive platform marker into an unconditional dependency and promoting the native resolver failure to universal UNSAT.

No change was made to research/REVISED_TRACE_SCHEMA.md.

### Interpretation

This strengthens:
- H2a: real structured evidence exists in resolver/provider layers;
- H2b: the revised semantic contract survives substantially more realistic cases;
- H2c: independent verification remains possible for a nontrivial reduced case.

It does not establish H2d. Stable portable cross-resolver interchange remains unproven.

### H2e separation

**H2e remains NOT TESTED.**

There are still **0 substantive maintainer responses**. The real-world corpus is technical evidence, not maintainer validation, ecosystem acceptance, adoption, or endorsement.

Production architecture remains NOT APPROVED.

## Updated research conclusion

The current strongest defensible statement is:

> The revised resolvewhy-trace semantic contract survives the tested real-world adversarial corpus and can carry enough trustworthy evidence for independent verification in selected nontrivial cases, while correctly refusing proofs when critical evidence is incomplete. Cross-resolver interchange stability and maintainer validation remain open empirical questions.

The project remains in research/falsification mode; this result does not justify production adapters or a production trace framework.


## H2d update — cross-resolver portability experiment — 2026-09-21

A direct portability experiment was completed using independent semantic mappings for pip/resolvelib and uv, with source-level mappings for Poetry/Mixology and pipgrip/PubGrub.

**H2d result: B. H2d PARTIALLY SUPPORTED — PORTABILITY BOUNDARY MUST BE NARROWED.**

The tested pair can preserve the same satisfiability-relevant semantics for:
- requirements and dependency edges;
- activation conditions;
- opaque candidate identity;
- artifact identity where relevant;
- runtime context;
- resolution policy;
- candidate-domain coverage;
- semantic constraints/literals;
- provenance;
- evidence state.

The experiment also showed that native incompatibility/rejection objects, derivation trees, decision levels, backjump state, provider internals, index machinery, and human-readable diagnostics do not have one safely universal meaning. These must remain namespaced/optional.

The known uv conditional-marker case was used as a critical unsafe-normalization attack: removing the activation marker and promoting the native conflict to a universal incompatibility is unsound, and the semantic proof boundary rejects it.

No tested semantic field was forced into NOT REPRESENTABLE.

This establishes technical portability only for the tested resolver pair and cases. It does not establish ecosystem-wide interchange, API stability, adoption, or maintainer acceptance.

**H2e remains NOT TESTED.** This experiment supplied no maintainer feedback and does not change the 0 substantive-response status.


## Portable-core sufficiency update — 2026-09-21

The latest falsification experiment tested the portable semantic proof core itself for projection collisions.

It found one genuine semantic collision family: a single-environment satisfiable trace and a universal multi-environment trace can have identical pre-repair portable projections when both use the same active runtime context and the same universal/fork policy but differ in the declared environment domain. The universal case became UNSAT because the additional Python 3.9 branch violated the candidate's Requires-Python constraint.

The smallest repair was to add explicit evaluation_domain proof scope to the semantic core. After the repair, the finite search over 64 pip-style and uv-style native fixture worlds produced 0 projection collisions. Native derivation and decision-state deletion still preserved semantic truth in the tested fragment.

### Updated technical conclusion

H2d remains **PARTIALLY SUPPORTED**. The portable proof core is sufficient only within a stated semantic fragment and requires explicit evaluation-domain information for quantified multi-environment claims.

The revised schema was updated accordingly. This is a genuine narrowing of the proven boundary, not a claim of universal cross-resolver completeness.

### H2e separation

**H2e remains NOT TESTED.** The experiment used no maintainer feedback, sent no outreach, and does not alter the 0 substantive-response status.

Production architecture remains NOT APPROVED.


## Trace-only verification update — 2026-09-21

The trace-only experiment tested the stronger proposition that a serialized portable trace can be used as a self-contained proof-supporting artifact after detaching from the original resolver, provider, indexes, network, diagnostics, and native derivation state.

A trace-only hermetic verifier was added. Structural corruption such as missing required fields, dangling references, and complete candidate coverage without an attestation is rejected as INVALID_TRACE; incomplete proof evidence is classified as INSUFFICIENT_EVIDENCE. A serialized finite contradiction can be reconstructed without native resolver access.

The experiment also exposed one semantic proof-artifact requirement: multi-environment proof claims must explicitly bind a result quantifier to the declared evaluation domain. This is now represented by an explicit proof-claim concept in the revised schema. The repair was required by the proof-artifact falsification test.

Accordingly, the trace-only stage is currently **B. TRACE-ONLY VERIFICATION REQUIRES ANOTHER SEMANTIC FIELD**, with the smallest repair being explicit proof-claim scope binding. After that repair, the hermetic verifier boundary is sufficient for the tested finite fragment, but full corpus-scale replay is not yet established by the committed harness.

H2d therefore remains PARTIALLY SUPPORTED, not upgraded. H2e remains NOT TESTED with 0 substantive maintainer responses. Production architecture remains NOT APPROVED.

## Final trace-only proof-artifact result — 2026-09-21

The trace-only experiment was completed after the explicit proof-claim binding repair.

### Result

**A. TRACE-ONLY PROOF ARTIFACT VALIDATED — within the tested finite semantic fragment.**

Full-corpus evidence:
- 18/18 serialized corpus cases matched the intended trace-only classification.
- 6 VERIFIED_UNSAT, 2 VERIFIED_SAT, 10 INSUFFICIENT_EVIDENCE, 0 INVALID_TRACE in the base corpus.
- 18/18 serialization round-trips preserved semantic results.
- 18/18 isolated replays completed without resolver/provider/index/network/external-state access.

Proof-strength evidence:
- RW-14: five-constraint transitive UNSAT core independently rechecked; every single core-element deletion produced SAT.
- RW-09: universal Python-domain proof independently rechecked; Python 3.12 is SAT, Python 3.9 is UNSAT under Requires-Python >=3.10; every single core-element deletion produced SAT.
- RW-02 remained a resolver-failure-but-SAT negative control; resolver failure labels were not trusted as mathematical proof.
- RW-07 demonstrated that deleting an activation marker can create a false UNSAT, confirming that activation semantics remain proof-bearing.

Falsification evidence:
- 250 deterministic serialization mutations: 0 incorrectly accepted verified proofs.
- 256-world post-repair projection search: 0 semantic collisions.
- identical portable data plus different hidden native state: 0 differing proof results in the tested fragment.

This completes the requested trace-only boundary test for the declared finite semantic fragment. It does not prove arbitrary resolver completeness, ecosystem-wide wire compatibility, maintainer acceptance, or production readiness.

### H2 decomposition after this experiment

- H2d remains **PARTIALLY SUPPORTED**: the semantic portability boundary is demonstrated only for the tested fragment and resolver-shaped evidence families.
- H2e remains **NOT TESTED**: there are still 0 substantive maintainer responses.
- Production architecture remains **NOT APPROVED**.

No new schema field was required after proof-claim binding was repaired.