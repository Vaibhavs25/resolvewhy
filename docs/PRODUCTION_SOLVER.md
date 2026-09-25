# Production Solver and Minimal-Core Engine

**Phase:** 4B — Independent Solver + Minimal-Core Engine  
**Status:** implemented for the established finite semantic fragment

## 1. Purpose

Phase 4B separates reusable semantic solving from the higher-level production verifier.

The pipeline is:

```text
production Trace
      |
      v
verifier: validation, evidence, proof binding, provenance
      |
      v
SemanticProblem
      |
      v
production solver
      |
      +--> SAT / UNSAT
      +--> conflict core
      +--> independently verified subset-minimal core
```

The solver is declarative. It does not execute a resolver, inspect package indexes, access the network, execute package code, or trust resolver status claims.

## 2. Finite semantic problem representation

`resolvewhy.solving.problem.SemanticProblem` is an immutable semantic view containing only the model data required by the evaluator:

- requirements;
- candidates and source-aware candidate identities;
- artifacts;
- parent-linked dependency edges;
- candidate domains and coverage information;
- normalized semantic constraints/literals;
- runtime contexts;
- resolution policy;
- proof-relevant evidence state;
- the explicit proof quantifier.

A `Trace` is converted to this representation by `SemanticProblem.from_trace(...)`. The solver never consumes the `Trace` object, resolver metadata, diagnostics, incompatibility labels, or native search state.

The verifier remains responsible for selecting the proof premises and applicable evaluation environments before reconstruction.

## 3. Supported semantics

The solver deliberately preserves the established finite fragment only:

- normalized version constraints;
- finite candidate choices;
- parent-linked dependency implications;
- tested activation/marker semantics;
- runtime contexts;
- explicit finite evaluation domains;
- existential and universal quantification plus explicit branch scope;
- candidate and source-aware candidate identity;
- candidate/artifact distinction;
- the supported artifact-feasibility rules;
- supported Requires-Python semantics;
- supported prerelease policy;
- complete candidate-domain coverage;
- semantic constraints/literals.

Unsupported or ambiguous proof-relevant semantics fail closed.

## 4. SAT evaluation

The exact evaluator uses deterministic finite-domain backtracking over candidate choices.

For each runtime context it:

1. constructs the candidate domain for every proof-relevant package;
2. filters candidates according to the supported prerelease policy;
3. explores candidate assignments in deterministic package order;
4. checks activated requirements and dependency implications;
5. checks Requires-Python constraints;
6. checks artifact feasibility;
7. propagates unknown/incomplete semantic facts as an undecidable outcome rather than inventing a Boolean value.

The search is finite and bounded. A configured search-state limit returns `INSUFFICIENT_EVIDENCE` rather than an approximate SAT/UNSAT result.

## 5. UNSAT and quantification

A branch is UNSAT only when every finite candidate assignment violates at least one supported semantic constraint.

For an `EXISTENTIAL` proposition, at least one SAT branch makes the proposition SAT. If no branch is SAT and no branch is unknown, it is UNSAT.

For a `UNIVERSAL` proposition, any UNSAT branch makes the proposition UNSAT. All branches must be SAT for the universal proposition to be SAT. An unknown branch makes the result conservative.

For a `BRANCH` proposition, exactly the explicitly bound runtime context is evaluated.

The solver does not infer scope from filenames, `trace_scope`, resolver status, or policy labels.

## 6. Evidence obligations

The solver validates the semantic problem before evaluation. In particular:

- proof-relevant evidence cannot be missing, incomplete, or unknown;
- every proof-relevant package/context needs a candidate domain;
- candidate-domain coverage must be explicitly complete;
- complete coverage needs an attestation with existing, non-blocking evidence;
- the attestation evidence must explicitly support the candidate-domain object;
- candidate-domain policy references must match the problem policy;
- dangling candidate/domain/evidence references are invalid.

Therefore an empty or partial observed candidate list cannot by itself prove UNSAT.

The verifier performs the fuller trace-level evidence/provenance checks before constructing the problem; the solver repeats the obligations needed to prevent direct callers from accidentally turning incomplete candidate evidence into a proof.

## 7. Evaluation-domain handling

The semantic problem contains the concrete runtime contexts selected by the verifier for the declared quantifier. This is the evaluated finite domain, not merely the context of one observation.

The solver preserves the distinction between:

- one runtime environment;
- the finite set of environments being quantified;
- an explicitly selected branch.

The evaluation-domain identifier and proof binding remain trace/verifier concerns; the solver receives the already bound finite environments and quantifier as semantic inputs.

## 8. Core extraction

`minimal_unsat_core(problem, premises)` uses deterministic deletion-based reduction.

The algorithm first establishes that the supplied premise set is UNSAT. It then visits premise IDs in lexicographic order and removes a premise whenever the remaining set is still UNSAT.

The resulting core is therefore guaranteed to satisfy:

```text
core is UNSAT
and
for every c in core:
    core \ {c} is SAT
```

This is **subset-minimality**.

It is not minimum-cardinality optimization. Different semantic problems can have multiple valid subset-minimal cores; the implementation uses the documented lexicographic deletion policy to choose deterministically among them.

## 9. Core verification

`verify_unsat_core(problem, claimed_core)` independently checks:

1. every claimed ID is a declared semantic constraint;
2. the claimed set is UNSAT;
3. every single-deletion subset is SAT.

Any invalid, non-UNSAT, undecidable, or non-minimal claim is rejected as unverified.

The verifier uses this reusable checker for `claimed_core_refs` and `subset_minimal_claim` rather than maintaining a second deletion algorithm.

## 10. Determinism

Determinism is explicit:

- package evaluation order is lexicographic;
- premise/core IDs are canonicalized lexicographically;
- candidate order follows the declared candidate-domain sequence after deterministic package selection;
- core extraction removes candidates using the same lexicographic premise order;
- no resolver search order, timestamps, filesystem enumeration, network state, or hash-randomized ordering is consulted.

The chosen core is not claimed to be unique.

## 11. Result model

`SolveResult` distinguishes:

- `SAT`;
- `UNSAT`;
- `INSUFFICIENT_EVIDENCE`;
- `INVALID_PROBLEM`.

Core operations return typed `CoreResult` and `CoreVerificationResult` objects containing semantic constraint IDs and verification metadata rather than exposing raw strings as the only interface.

The verifier maps the solver result into the public production result classes:

- `VERIFIED_SAT`;
- `VERIFIED_UNSAT`;
- `INSUFFICIENT_EVIDENCE`;
- `INVALID_TRACE`.

## 12. Trust boundary

Resolver-native status, error strings, incompatibility labels, and diagnostic prose are absent from `SemanticProblem` and therefore cannot become mathematical premises accidentally.

The solver computes only from normalized semantic data supplied to it.

Consequently, a trace may claim UNSAT while the solver establishes SAT, or claim SAT while the solver establishes UNSAT. The resolver claim has no authority over the result.

## 13. Limitations

This phase does not establish:

- arbitrary PEP 508 semantics;
- dynamic build metadata or build failures;
- complete wheel/sdist selection;
- complete hash or lockfile semantics;
- implicit virtual/provided packages;
- symbolic or infinite environment domains;
- universal package-ecosystem semantics;
- minimum-cardinality cores;
- performance characteristics for large dependency graphs.

These remain outside the validated fragment.

## 14. Future optimization points

The solver API deliberately isolates satisfiability calls so future implementations can add, without changing the semantic contract:

- incremental solving;
- memoization;
- graph decomposition;
- clause caching;
- parallel deletion checks;
- other exact finite-domain search improvements.

No such optimization is required for Phase 4B correctness.
