# Boundary Cases

**Date:** 2026-09-21  
**Purpose:** identify the nearest semantic cases relative to the currently validated resolvewhy-trace fragment.

## Inside the proven fragment

| Case | Status | Why |
|---|---|---|
| Disjoint version ranges through multiple dependency edges | INSIDE | Independently reconstructed and used for subset-minimal UNSAT cores |
| Marker-activated dependency | INSIDE | Activation condition is explicit and environment-sensitive |
| Requires-Python incompatibility | INSIDE | Candidate metadata + runtime context are serialized |
| Platform-incompatible artifact | INSIDE | Candidate/artifact separation is explicit |
| Source-qualified same-version candidates | INSIDE | Candidate identity is opaque/source-aware |
| Prerelease policy difference | INSIDE in tested reductions | Policy is serialized separately from identity |
| Yank/artifact distinction | INSIDE in tested reductions | Artifact status remains distinct from candidate/version |
| Finite universal Python domain | INSIDE | Explicit evaluation domain + proof quantifier binding |
| Partial source/query coverage | INSIDE as insufficiency | Coverage/evidence state prevents false no-candidate proofs |
| Resolver-failure-but-SAT negative control | INSIDE | Resolver failure is not trusted as mathematical UNSAT |
| Proof-core subset minimality | INSIDE | Each reported element is deleted independently and SAT is rechecked |

## Near the boundary

### Nested PEP 508 markers

A dependency can use a nested marker expression combining and/or with environment and extra variables. The current semantic slot is activation condition, so such expressions are representable when faithfully normalized. Exhaustive equivalence across every legal marker form and field combination has not been established. 

### Multiple extras

A dependency may request multiple extras. The current model can represent the resulting additional dependency set, but full arbitrary transitive extra propagation has not been exhaustively verified.

### Multi-dimensional environments

Example domain:

Python version × operating system × architecture × implementation.

Finite explicit partitions are conceptually supported because evaluation_domain and proof claims are explicit. Symbolic or infinite domain reasoning is not established.

### Artifact mixtures

Example:
- compatible wheel;
- incompatible wheel;
- buildable sdist;
- build-failing sdist;
- hash-disallowed archive.

The candidate/artifact distinction is sufficient to keep these facts separate, but complete artifact-selection/build-failure semantics are not established.

### Lock-constrained satisfiability

The proposition "satisfiable under dependency semantics" must remain distinct from "satisfiable under dependency semantics plus lockfile restrictions." The current model can encode extra semantic constraints, but the full lockfile execution semantics have not been independently validated. 

## Outside the current guarantee

### Dynamic metadata generation

Build backends can generate metadata during build hooks in an isolated build environment. 

The current verifier can consume the resulting metadata if serialized, but does not independently reconstruct arbitrary backend computation.

### Build-environment side effects

Environment state can influence build-time computation. Those hidden inputs are outside the current portable proof fragment unless the resulting semantic facts and their provenance are serialized.

### Hash/reproducibility semantics

Hash restrictions can affect artifact admissibility, including pip's hash-checking mode. 

The present evidence is insufficient to claim complete cross-resolver hash semantics.

### Virtual/provided/system packages

A synthetic package node can be represented, but the relation defining which installed component provides it was not part of the validated fragment.

### Arbitrary lockfile execution semantics

The current pylock specification includes environment selectors, extras, dependency groups, package markers, Requires-Python, archives, hashes and sources.  Their complete interaction semantics remain outside the established guarantee.

## Boundary rule

A semantic feature enters the proven boundary only when its satisfiability meaning can be reconstructed from serialized evidence and the relevant completeness/provenance obligations are independently established.

A feature does not enter merely because a resolver supports it, its syntax can be serialized, or a native diagnostic mentions it.
