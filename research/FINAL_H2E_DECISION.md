# Final H2e decision

## Current status

**H2e: NOT TESTED**

No substantive maintainer feedback has been received.

The public-architecture audit performed on 2026-09-21 is independent source/experiment evidence and does not count as maintainer validation.

## Public artifact

Repository:
https://github.com/Vaibhavs25/resolvewhy

RFC:
https://github.com/Vaibhavs25/resolvewhy/issues/2

## Architecture audit result

Current upstream source/documentation was examined for:

- resolvelib
- pip
- Poetry
- pipgrip
- uv

The audit found strong recurring semantic concepts:

- requirements
- candidate identity
- dependency edges
- environment/policy
- candidate availability
- conflict/incompatibility
- provenance
- source/index information

It also found significant differences in ownership and semantics across resolver/provider/source layers.

### Major falsification finding 1: candidate completeness

A global candidate_inventory_complete boolean is insufficient.

Candidate discovery and filtering may involve:

- provider/source queries
- index scope
- environment filters
- artifact compatibility
- prerelease and other policy decisions
- bounded discovery
- incomplete metadata

A correct proof boundary therefore needs coverage metadata attached to candidate domains/queries.

### Major falsification finding 2: incompatibility/rejection semantics

“Rejected candidate” and “incompatibility” are not universal primitives.

- resolvelib exposes provider/reporter causes and criteria
- Poetry and pipgrip use Mixology-style incompatibilities
- uv uses PubGrub derivation structures

These can be normalized semantically, but their native meanings should remain explicitly namespaced.

### Major falsification finding 3: candidate identity

package + version is not universally enough.

URL, VCS, local path, source/index, or artifact identity can affect satisfiability.

The adapter must therefore preserve opaque candidate identity.

### Major falsification finding 4: environment vs policy

A machine-environment snapshot alone does not capture all resolver semantics.

The trace should separate runtime context from resolution policy.

## Decision on resolvewhy-trace/v0

### KEEP unchanged

Rejected.

The audit found concrete semantic ambiguity that could allow an external consumer to overclaim completeness or flatten resolver-specific causes.

### ABANDON

Rejected.

The same semantic structure recurs across all four architecture families, and the tested resolvelib evidence path plus structured uv/Poetry/pipgrip internals show that the underlying abstraction has technical substance.

### NARROW only

Insufficient by itself.

The semantic core should be narrower, but explicit coverage and namespacing are also required.

### REVISE

**Selected.**

The revised architecture is:

resolver/provider-specific evidence
-> typed + namespaced observations
-> explicit per-domain coverage
-> small resolver-neutral semantic core
-> independent consistency/MUS verification

The proposed revised resolver-neutral core is:

- requirement
- opaque candidate identity
- dependency edge
- runtime context
- resolution policy
- candidate-domain coverage
- semantic constraint/literal
- provenance
- explicit evidence state

Everything else may remain optional resolver-specific evidence.

## H2 decomposition

| Hypothesis | Current state | Reason |
|---|---|---|
| H2a | SUPPORTED narrowly | resolvelib exposes provider/reporter contracts that can carry structured evidence |
| H2b | PARTIALLY SUPPORTED | controlled normalization works, but portability requires revised coverage/identity/policy semantics |
| H2c | SUPPORTED in controlled traces | 6/6 UNSAT traces already passed independent minimality verification |
| H2d | UNPROVEN | a common semantic layer is plausible; a stable portable external trace interface is not established |
| H2e | NOT TESTED | 0 substantive maintainer responses |

## Maintainer validation

Current substantive response count:

**0**

No A-D classification exists.

Silence, delivery status, and blocked communication attempts are not treated as technical evidence.

## Final research decision

**CONTINUE RESEARCH**

More specifically:

> REVISE resolvewhy-trace/v0, then test the revised coverage/provenance contract against adversarial real-world traces. Do not build production infrastructure yet.

## What is now defensible to claim

> Public architecture evidence across resolvelib/pip, Poetry, pipgrip and uv supports the plausibility of a resolver-neutral semantic evidence layer, provided that candidate completeness, provenance, identity, policy and resolver-specific conflict semantics are represented explicitly.

## What remains unproven

- whether maintainers consider the interface useful
- whether maintainers would expose the required evidence
- whether a stable public trace API is acceptable
- whether downstream tooling would adopt the model
- whether the revised schema is portable without excessive adapter-specific complexity
- whether difficult real-world source/artifact cases can be handled without misleading proofs

## Next technical gate

Test the revised candidate coverage model with adversarial cases involving:

- multiple indexes
- source-specific candidates
- platform/wheel filtering
- requires-Python filtering
- prerelease policy
- VCS/direct URL identity
- incomplete metadata
- bounded candidate discovery

The output of that experiment should be used to decide whether the semantic contract is sufficiently trustworthy to justify production architecture.

No maintainer support is claimed.
