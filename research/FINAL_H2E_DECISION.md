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
