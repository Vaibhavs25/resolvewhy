# AI_BUILD_CONTEXT — resolvewhy

> **Read this file before making non-trivial changes to this repository.**
>
> This file is the canonical high-level description of the **full build we intend to create**. It is deliberately future-facing: the current repository is a validated research prototype, while the build described here is the eventual usable open-source system built on top of that research.

**Project:** `resolvewhy`  
**Repository:** `Vaibhavs25/resolvewhy`  
**Document purpose:** give human developers and AI coding agents a shared understanding of the complete product/research-to-production direction.

---

## 1. What resolvewhy is ultimately supposed to become

The long-term goal is a dependency-resolution **explanation and proof engine**.

A package resolver can fail with a message such as “because A requires B<2 and C requires B>=2, resolution is impossible.” The difficult part is that the resolver's internal state, candidate discovery, environment conditions, policies, and conflict derivations are usually not exposed in a stable form that an independent downstream tool can safely verify.

`resolvewhy` is intended to solve that gap.

### Target outcome

Given sufficiently rich structured dependency-resolution evidence, `resolvewhy` should be able to:

1. capture or receive resolver evidence;
2. normalize the evidence into a portable semantic trace;
3. reconstruct the actual satisfiability problem;
4. independently verify whether the represented problem is SAT or UNSAT;
5. identify a subset-minimal conflict explanation when UNSAT;
6. verify the explanation rather than trusting the resolver's diagnosis;
7. produce a machine-readable proof artifact;
8. produce a useful human-readable explanation;
9. fail closed when the evidence is incomplete, ambiguous, malformed, or outside the supported semantics.

The central design principle is:

**Do not merely repeat why the resolver says it failed. Independently prove what the supplied evidence actually entails.**

---

# 2. Current state vs. full build

## Current state — research prototype

The repository has already completed the declared technical validation program for a finite semantic fragment.

Current research conclusions:

- H1: SUPPORTED for the tested finite semantic fragment.
- H2a: SUPPORTED narrowly.
- H2b: PARTIALLY SUPPORTED.
- H2c: SUPPORTED for the tested fragment.
- H2d: PARTIALLY SUPPORTED.
- H2e: NOT TESTED.
- Production implementation: a separate future decision.

The current repository contains research artifacts, a finite trace-only verifier, reproducibility harnesses, adversarial tests, a serialized 18-case corpus, portability analysis, and semantic-boundary documentation.

### Important evidence boundary

The 18-case corpus is a **deterministic serialized fixture replay**. It is not the same thing as freshly executing all historical resolver incidents today.

The existing reproducibility harness is the research baseline and must remain auditable.

## Full build — future system

The full build is a separate engineering phase.

It should turn the validated semantic idea into a real package/tool that can consume resolver evidence in practice, while preserving the same fail-closed and independently verified semantics.

Do not rewrite history in the research documents to make the production system look as though it already exists.

---

# 3. The complete system we are building

At a high level:

```
                PACKAGE MANAGER / RESOLVER
                           |
                           v
                 Evidence capture / adapter
                           |
                           v
                  Resolver-specific evidence
                           |
                           v
                  Semantic normalization
                           |
                           v
                 resolvewhy semantic trace
                           |
                 +---------+---------+
                 |                   |
                 v                   v
          Independent verifier    Proof builder
                 |                   |
                 v                   v
             SAT / UNSAT       Verified explanation
                 |                   |
                 +---------+---------+
                           |
                           v
                 Human + machine output
```

The architecture should intentionally separate:

- **evidence acquisition** from
- **semantic normalization** from
- **independent verification** from
- **explanation rendering**.

A resolver adapter may know a great deal about one ecosystem. The verifier should not need to know that resolver's internal architecture to check the normalized proposition.

---

# 4. Core concepts that must survive the full build

The semantic core is more important than any particular API.

The production system must preserve, at minimum:

- root requirements;
- parent-linked dependency edges;
- activation conditions / markers;
- package identity;
- opaque and source-aware candidate identity;
- artifact identity when artifact feasibility matters;
- runtime context;
- explicit evaluation domains for quantified claims;
- resolution policy where it changes admissibility or proof scope;
- candidate domains;
- candidate-domain coverage and completeness attestation;
- semantic constraints / literals;
- evidence state;
- provenance;
- explicit proof-claim binding.

These concepts must not be collapsed merely for convenience.

### Critical distinctions

The implementation must continue to distinguish:

**Runtime context vs. evaluation domain**

A runtime describes one environment. An evaluation domain describes the set of environments over which a quantified proposition is being checked.

**Candidate identity vs. artifact identity**

A version/candidate can exist while a particular artifact is infeasible. These are not interchangeable.

**Observed rejection vs. exhaustive absence**

Seeing no usable candidate in an incomplete trace does not prove that no candidate exists.

**Resolver policy vs. mathematical truth**

A resolver may reject something because of policy. The verifier must model policy explicitly instead of silently turning policy behavior into a universal mathematical impossibility.

**Evidence vs. proof**

Evidence can support a proof. A resolver's diagnostic string is not itself a proof.

**Portable semantics vs. resolver-native internals**

Common semantic roles should be normalized. Native decision levels, backjump structures, provider internals, derivation objects, index machinery, and detailed rejection structures should remain namespaced/resolver-specific unless their semantics are demonstrably portable.

---

# 5. Planned repository architecture

The exact directory names may evolve, but the conceptual separation should remain stable.

## A. Semantic core

A reusable, dependency-free or minimally dependent library containing:

- typed trace model;
- identifiers and references;
- requirements and version constraints;
- dependency edges;
- markers / activation conditions;
- candidate and artifact models;
- runtime contexts;
- evaluation domains;
- policies;
- candidate domains and coverage claims;
- semantic constraints;
- provenance;
- evidence states;
- proof claims;
- validation utilities.

This is the foundation. Do not let CLI code or resolver adapters define the semantics.

## B. Resolver adapters

Separate adapters for resolver ecosystems.

Initial targets should be:

1. pip / resolvelib
2. uv
3. Poetry / Mixology
4. pipgrip / PubGrub

Adapters should extract structured evidence and map it into the semantic core.

An adapter must never silently invent missing facts.

When an adapter cannot establish an evidence obligation, the trace should say so explicitly and verification should fail closed.

## C. Normalizer

The normalizer converts resolver-specific observations into the portable semantic trace.

Responsibilities:

- canonicalize identities;
- preserve source distinctions;
- preserve activation conditions;
- preserve runtime context;
- preserve evaluation-domain meaning;
- normalize requirements/constraints;
- attach provenance to derived semantic claims;
- record coverage claims explicitly;
- retain resolver-native evidence in namespaced fields where useful.

The normalizer must be deterministic where the input evidence is deterministic.

## D. Trace format and serialization

Define a real, versioned machine-readable trace format.

The trace should be:

- self-contained enough for independent verification;
- schema-versioned;
- structurally validated;
- reference-safe;
- deterministic where practical;
- explicit about evidence completeness;
- explicit about proof scope;
- extensible without changing the meaning of old fields.

A future wire format must be derived from the **revised semantic schema**, not from the old illustrative `resolvewhy-trace/v0` sketch.

The old v0 documents are research history, not the production contract.

## E. Independent verifier

The verifier is the trust boundary.

It must:

1. validate trace structure;
2. validate references;
3. validate provenance;
4. validate coverage claims;
5. determine whether evidence is sufficient;
6. reconstruct the semantic problem;
7. independently compute SAT/UNSAT for the supported semantics;
8. verify the proof claim;
9. verify the reported explanation;
10. verify subset-minimality when claimed;
11. return a typed result.

Expected result classes should remain conceptually aligned with:

- `VERIFIED_SAT`
- `VERIFIED_UNSAT`
- `INSUFFICIENT_EVIDENCE`
- `INVALID_TRACE`

Do not reduce everything to a Boolean.

## F. Explanation engine

On top of verification, build a user-facing explanation layer.

For UNSAT, the system should be able to explain:

- which requirements conflict;
- which dependency paths connect them;
- which candidates or artifacts create the contradiction;
- which environment/policy condition matters;
- why the explanation is sufficient;
- why each element is necessary for subset-minimality.

The explanation renderer must be generated from verified semantics, not from untrusted resolver prose.

## G. Proof artifacts

A proof result should be serializable independently of a live resolver process.

A proof artifact should contain enough information to let another process answer:

- what proposition was claimed;
- over what evaluation domain;
- under what policy;
- from which semantic premises;
- what result was established;
- what evidence supports those premises;
- whether the explanation is subset-minimal.

The goal is reproducible verification, not merely a pretty error message.

## H. CLI

The eventual public tool should have a small, obvious CLI.

Conceptually:

```bash
resolvewhy capture ...
resolvewhy normalize ...
resolvewhy verify trace.json
resolvewhy explain trace.json
resolvewhy proof trace.json
```

The exact commands may change, but the separation of capture, normalization, verification, and explanation should remain.

A single high-level command can combine these stages for convenience.

Example user-facing intent:

```bash
resolvewhy explain <resolver evidence>
```

which produces a verified explanation when possible.

## I. Library / API

Expose a Python API so other tools can call `resolvewhy` without invoking the CLI.

Conceptually:

```text
resolver evidence
        -> trace
        -> validation
        -> verification
        -> explanation / proof
```

Potential interfaces:

- `normalize(...)`
- `verify(...)`
- `explain(...)`
- `minimal_core(...)`
- `serialize_trace(...)`
- `load_trace(...)`

Names are not fixed yet. Semantics are.

---

# 6. End-to-end product workflow

The final system should support this complete path.

## Step 1 — Run or observe a resolver

A supported package manager attempts dependency resolution.

## Step 2 — Capture structured evidence

The adapter captures the facts that matter for independent reasoning.

Examples:

- requirements;
- candidate discovery;
- selected candidates;
- dependency edges;
- markers;
- environment information;
- policy decisions;
- candidate/artifact feasibility;
- rejection/incompatibility observations;
- coverage/exhaustion evidence.

## Step 3 — Build a semantic trace

The normalizer produces a resolver-neutral trace.

Resolver-specific details are retained separately.

## Step 4 — Validate the trace

The trace validator checks:

- schema;
- types;
- references;
- completeness;
- evidence states;
- candidate domains;
- provenance;
- proof binding.

Malformed traces become `INVALID_TRACE`.

Incomplete but structurally valid evidence becomes `INSUFFICIENT_EVIDENCE`.

## Step 5 — Reconstruct the proposition

The verifier reconstructs the mathematical problem represented by the evidence.

This is where the system must respect:

- activation;
- runtime context;
- evaluation domain;
- policy;
- candidate admissibility;
- artifact feasibility;
- finite candidate coverage;
- semantic constraints.

## Step 6 — Independently solve

The verifier determines SAT/UNSAT without trusting the resolver's textual conclusion.

## Step 7 — Compute / verify an explanation

For UNSAT:

- derive a conflict set;
- reduce it to a subset-minimal core;
- independently check the core;
- independently check each single-deletion variant.

Do not claim minimum-cardinality unless a separate algorithm and proof justify that stronger claim.

## Step 8 — Render results

Provide both:

### Human output
A concise dependency graph / contradiction explanation.

### Machine output
Structured status, core, proof metadata, provenance, and trace references.

## Step 9 — Preserve reproducibility

The trace and proof artifact should be saveable and replayable independently.

A user should be able to send a trace to another machine without requiring the original resolver or package indexes.

---

# 7. What “independent verification” means

This is one of the most important ideas in the entire project.

The system should not do:

```
resolver says UNSAT
        -> copy resolver message
        -> call that a proof
```

Instead:

```
resolver evidence
        -> semantic trace
        -> independent reconstruction
        -> independent SAT/UNSAT result
        -> independently checked explanation
```

The verifier must not trust:

- human-readable error text;
- an asserted `status_claim`;
- a native resolver's “no candidate” message;
- an unqualified exhaustion statement;
- hidden resolver state;
- unexplained derived incompatibilities.

Where a native resolver provides useful derivations, they may be used as evidence with provenance, but the mathematical conclusion should still be independently checked.

---

# 8. Candidate-domain completeness is a first-class feature

This is a core lesson from the research and must remain central in the full build.

A resolver often explores a restricted set of candidates.

For example:

- only one index was searched;
- authentication blocked another source;
- prereleases were filtered;
- yanked versions were excluded;
- a source query was incomplete;
- candidate discovery was bounded.

Therefore:

```
observed candidates = 0
```

does **not** automatically imply:

```
candidate universe = empty
```

The final product must explicitly represent:

- what candidate domain was considered;
- which sources were included;
- what query/filter/policy applied;
- whether enumeration was complete;
- what evidence supports the completeness claim.

When completeness cannot be demonstrated, the result must be `INSUFFICIENT_EVIDENCE`, not a fabricated UNSAT proof.

---

# 9. Multi-environment reasoning

Environment-sensitive dependency resolution is not necessarily a single Boolean problem.

The system needs explicit support for propositions such as:

- this environment is satisfiable;
- at least one environment is satisfiable;
- every environment in a declared finite domain is satisfiable;
- a specific branch is satisfiable/unsatisfiable.

Therefore the proof artifact must explicitly bind:

- quantifier;
- evaluation domain;
- relevant runtime context;
- semantic premises.

Do not infer the quantifier from a filename, CLI mode, or informal wording.

---

# 10. Failure-safe behavior

The production system should be conservative.

### It should return `VERIFIED_UNSAT` only when:

- the trace is structurally valid;
- all required references resolve;
- evidence is sufficient for the supported semantics;
- candidate-domain obligations are satisfied;
- the proof proposition is explicit;
- the reconstructed problem is actually UNSAT;
- the claimed explanation passes the appropriate verification checks.

### It should return `VERIFIED_SAT` only when:

- the represented proposition is independently shown satisfiable.

### It should return `INSUFFICIENT_EVIDENCE` when:

- necessary candidate coverage is incomplete;
- source access was partial;
- required metadata is missing;
- the semantic meaning is unknown or unsupported;
- a conclusion would otherwise rely on an unjustified assumption.

### It should return `INVALID_TRACE` when:

- structure is malformed;
- IDs or references are invalid;
- provenance is broken;
- proof claims are inconsistent;
- schema invariants are violated.

The system must **fail closed**, especially around UNSAT claims.

---

# 11. Research-to-production rules

The research code has a different purpose from the final library.

### Keep the research record intact

Do not:

- delete historical audit documents;
- rewrite old conclusions so they look current;
- erase discovered bugs;
- remove falsification history;
- turn historical fixtures into claims of fresh incident execution.

### Build production code separately

When implementation begins, create a clean package architecture that reuses validated semantics rather than turning research scripts into a production package by accretion.

The research files are evidence and experiments.

The production package should be maintainable independently.

---

# 12. Planned build phases

## Phase 0 — Research baseline
**Status: complete for the declared finite fragment.**

Preserve:

- semantic model;
- verifier behavior;
- adversarial tests;
- corpus fixtures;
- reproducibility runner;
- semantic boundary;
- portability findings.

Do not destabilize this baseline casually.

## Phase 1 — Production semantic core

Build a tested package containing:

- typed semantic objects;
- validators;
- canonical identifiers;
- constraints;
- environment/evaluation-domain model;
- policy model;
- evidence-state model;
- provenance;
- proof claims.

### Exit condition

The production semantic core can represent every concept already required by the validated research fragment without semantic loss.

## Phase 2 — Trace format

Create the first real versioned production trace format.

Goals:

- stable serialization;
- schema validation;
- deterministic loading;
- forward-compatible extension strategy;
- explicit coverage;
- explicit proof claim;
- explicit evidence status.

### Exit condition

A trace generated by one process can be independently validated and verified by another process with no resolver state.

## Phase 3 — Resolver adapters

Implement adapters one at a time.

Suggested order:

1. pip / resolvelib
2. uv
3. Poetry / Mixology
4. pipgrip / PubGrub

For every adapter:

- capture evidence;
- preserve native provenance;
- normalize what is truly portable;
- explicitly mark unavailable semantics;
- create ecosystem-specific conformance tests.

### Exit condition

Each supported resolver has real structured evidence capture plus tests showing that unsupported/incomplete evidence fails closed.

## Phase 4 — Independent solver and minimal-core engine

Generalize the current finite verifier into a reusable engine.

Goals:

- efficient satisfiability checks;
- subset-minimal core extraction;
- proof checking;
- bounded behavior on large inputs;
- deterministic results where practical.

Potential future optimization techniques include:

- incremental SAT solving;
- clause caching;
- graph-based preprocessing;
- hitting-set approaches;
- memoization;
- parallel deletion checks.

Optimization must never weaken semantic verification.

## Phase 5 — Human explanation layer

Build readable explanations from verified proof data.

Examples of desired output:

```text
Resolution is unsatisfiable under Python 3.11.

A 2.4 depends on B < 2
C 4.1 depends on B >= 2

No candidate for B satisfies both constraints.

Verified UNSAT.
Subset-minimal core: {A 2.4, C 4.1}
```

The wording should be generated from the semantic proof, not copied from resolver error strings.

## Phase 6 — CLI + Python API

Make the tool usable by developers and CI systems.

Possible entry points:

- command line;
- Python library;
- JSON trace interface;
- machine-readable exit/result codes.

## Phase 7 — Ecosystem integrations

Potential integrations:

- pip tooling;
- uv tooling;
- Poetry tooling;
- CI diagnostics;
- IDE/editor tooling;
- dependency bots;
- build/debug pipelines;
- reproducibility/debugging workflows.

Integrations should consume the semantic API rather than bypassing the verifier.

## Phase 8 — Scale and robustness

Stress the system on:

- large dependency graphs;
- many candidate versions;
- multiple sources;
- environment matrices;
- artifact constraints;
- prerelease policies;
- source-specific behavior;
- long transitive conflicts.

Measure:

- trace size;
- normalization time;
- verification time;
- explanation time;
- memory usage;
- false-positive/false-proof rate;
- coverage loss by adapter.

## Phase 9 — Public release

Only after the semantics, adapters, verification, and tests are mature:

- package the library;
- publish documentation;
- publish examples;
- publish benchmark suite;
- publish trace fixtures;
- publish reproducible releases;
- define compatibility/versioning policy;
- build contributor workflows.

Adoption and maintainer acceptance are separate ecosystem outcomes, not assumptions.

---

# 13. Test strategy for the full build

Testing must remain adversarial.

## A. Unit tests

Every semantic concept needs positive and negative tests.

## B. Property tests

Generate dependency graphs and candidate domains to test invariants.

## C. Differential tests

Compare supported adapters against the native resolver's actual behavior where a faithful oracle is available.

Do not equate textual error messages.

Compare semantic decisions and evidence interpretation.

## D. Mutation tests

Mutate traces intentionally:

- delete references;
- alter package IDs;
- alter candidate IDs;
- alter policy;
- alter evaluation domain;
- alter coverage;
- alter provenance;
- alter proof premises;
- flip activation;
- corrupt artifact feasibility.

The verifier should reject mutations that invalidate the proof.

## E. Negative controls

Keep known SAT cases alongside UNSAT cases.

A good verifier must distinguish:

- UNSAT;
- SAT;
- insufficient evidence;
- malformed evidence.

## F. Reproducibility tests

Every published research fixture should remain replayable.

## G. Cross-resolver conformance

The same semantic scenario should be represented consistently across adapters where the underlying meaning is actually shared.

When it is not shared, the adapter should preserve resolver-specific semantics instead of forcing a false normalization.

---

# 14. Performance goals

The explanation problem may be expensive.

Do not promise constant-time or globally optimal explanations.

The practical target is:

- exact verification for supported inputs;
- subset-minimal explanations;
- bounded/explicit behavior on hard instances;
- useful performance on real dependency graphs.

The implementation may use heuristics to **find** candidate cores, but any final “verified” result must pass the independent checker.

Possible future performance layers:

- incremental solving;
- memoized satisfiability calls;
- graph decomposition;
- conflict-directed search;
- parallel core minimization;
- compact trace encoding.

These are engineering optimizations, not semantic shortcuts.

---

# 15. What is deliberately NOT part of the first production release

The first production release should not pretend to solve every package-management semantic problem.

Unless independently implemented and tested, do not claim complete support for:

- arbitrary PEP 508 grammar;
- dynamic build-backend metadata generation;
- hidden build environments;
- complete wheel/sdist build selection;
- complete hash semantics;
- complete lockfile semantics;
- implicit virtual/provided/system packages;
- arbitrary symbolic or infinite environment domains;
- every resolver-specific native semantic;
- undocumented future resolver behavior.

Unsupported semantics should be represented explicitly and should cause a conservative result when they matter to the proof.

---

# 16. Security and trust model

The verifier should be designed as though traces are untrusted input.

Threats include:

- maliciously altered traces;
- forged proof premises;
- dangling references;
- false coverage claims;
- identity collisions;
- provenance spoofing;
- policy confusion;
- environment-domain confusion;
- artifact/candidate confusion.

Therefore:

- validate before reasoning;
- use strong reference integrity;
- avoid implicit defaults that change proof meaning;
- distinguish absence of evidence from evidence of absence;
- never trust a claimed result without recomputation;
- keep proof claims explicit.

A proof artifact should be independently checkable even if the producer is buggy or dishonest.

---

# 17. What AI coding agents must do

Before coding:

1. Read this file.
2. Read the current README.
3. Read the relevant research specification before modifying semantics.
4. Locate the existing executable test covering the behavior being changed.
5. Determine whether the change is research-only or part of the future production architecture.

During coding:

- prefer small, reviewable changes;
- add tests with semantic changes;
- preserve existing research fixtures;
- keep resolver-specific behavior isolated;
- fail closed on ambiguity;
- document new semantics;
- do not silently broaden guarantees.

After coding:

- run the narrowest relevant tests first;
- run the full relevant test suite;
- update documentation when a semantic contract changes;
- record any change that affects the research/product boundary.

---

# 18. Things an AI agent must NOT do

Do not:

- assume a resolver failure message proves UNSAT;
- assume an empty candidate list means the universe is empty;
- invent candidate-domain completeness;
- collapse runtime context and evaluation domain;
- collapse candidate identity and artifact identity;
- silently erase marker/activation conditions;
- turn resolver policy into universal mathematical truth;
- flatten resolver-native internals into fake portable semantics;
- claim support for semantics that are only “representable” but not independently tested;
- call historical fixture replay “fresh incident reproduction”;
- delete the falsification history because it looks messy;
- change the research conclusion merely to make a release look stronger;
- claim maintainer validation without substantive external validation;
- claim production readiness before the production architecture actually exists.

---

# 19. Definition of done for the full build

The project should eventually be considered production-ready only when all of the following are true:

### Semantics
The public semantic model is explicit, versioned, typed, and documented.

### Evidence
Supported adapters produce structured evidence without relying on fragile text scraping as the semantic source of truth.

### Completeness
Candidate-domain and evidence-completeness semantics are explicit and conservative.

### Verification
The verifier independently recomputes the represented SAT/UNSAT proposition.

### Explanations
UNSAT explanations are generated from verified semantics and can be checked.

### Minimality
Subset-minimal claims are independently validated rather than merely asserted.

### Portability
Common semantic roles are shared across supported resolver ecosystems, while resolver-specific semantics remain safely namespaced.

### Reproducibility
Traces and proof artifacts can be serialized, replayed, and independently checked.

### Testing
Adversarial, mutation, differential, regression, and cross-resolver conformance tests cover the supported surface.

### Performance
The tool is usable on realistic dependency graphs with documented limits.

### UX
A developer can go from “my dependency resolution failed” to a machine-checkable explanation with a small number of commands.

---

# 20. North-star example

The final experience we are aiming for is approximately:

```text
$ resolvewhy explain resolution-trace.json

RESOLUTION: UNSAT
SCOPE: Python 3.11
POLICY: stable releases, configured indexes

Verified conflicting requirements:

  application
    -> package-a == 2.4
       -> package-b < 2

  application
    -> package-c == 4.1
       -> package-b >= 2

Candidate-domain coverage:
  package-b: complete for the declared sources and policy

Independent result:
  UNSAT

Subset-minimal core:
  1. package-a == 2.4
  2. package-c == 4.1

Verification:
  core UNSAT: PASS
  delete #1 -> SAT: PASS
  delete #2 -> SAT: PASS

Proof artifact:
  resolvewhy-proof.json
```

The important part is not the formatting.

The important part is that the explanation is **derived from evidence and independently verified**.

---

# 21. Strategic direction

The project should evolve in this order:

```
research validity
      ↓
semantic core
      ↓
trace format
      ↓
real resolver evidence adapters
      ↓
independent verifier
      ↓
minimal explanation engine
      ↓
CLI / API
      ↓
ecosystem integrations
      ↓
scale / performance
      ↓
public release
```

Do not reverse this order by building a flashy UI first, then trying to retrofit the semantics.

The hard part of `resolvewhy` is the correctness boundary.

The user experience should be built on top of that boundary.

---

# 22. Final instruction to future AI agents

When making a decision about what to implement next, ask:

> **Does this change make `resolvewhy` better at producing independently verified, reproducible, machine-readable explanations of dependency-resolution outcomes from trustworthy structured evidence?**

If yes, implement it with tests and preserve the semantic boundaries.

If it changes a research conclusion, semantic guarantee, or proof obligation, stop treating it as ordinary refactoring: update the relevant research specification and validation evidence first.

If evidence is insufficient, **do not guess**.

The long-term product is not “a better dependency error message.”

It is:

> **an independently verifiable explanation layer for dependency resolution.**

That is the full build.
