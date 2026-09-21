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

## Current gate

**CONTINUE RESEARCH**

The next technical target is to test the revised candidate-coverage/provenance contract against adversarial real-world cases before building production infrastructure.


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
