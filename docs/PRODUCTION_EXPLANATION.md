# Production Human Explanation Layer

**Phase:** 5 — Human Explanation Layer  
**Status:** implemented for already independently verified semantic results

## 1. Purpose
Phase 5 converts an existing production SemanticProblem and an existing VerificationResult into a deterministic, auditable human-readable explanation.
The layer explains verified facts. It does not establish SAT/UNSAT truth.

The builder does not invoke the resolver or solver and does not consume resolver diagnostics, native incompatibility derivations, backtracking state, or search history.

## 2. Inputs
build_explanation(problem, verification_result) accepts the immutable production SemanticProblem and the production VerificationResult returned by the independent verifier.
For authoritative VERIFIED_SAT and VERIFIED_UNSAT, independently_verified must be true. Otherwise construction fails closed.

## 3. Output model
Explanation is an immutable typed model containing result kind, proof quantifier/scope, verified evaluation-domain identifier, runtime-context references, verified semantic constraints, dependency paths, relevant candidates, relevant artifacts, policy facts, evidence facts, a verified subset-minimal core when established, and verification issues/warnings.
Convenience reference properties expose deterministic constraint, dependency-path, and candidate IDs for audit tooling.

## 4. Supported result states
### VERIFIED_UNSAT
The explanation exposes verified proof scope, evaluation domain, relevant semantic premises, dependency relationships, candidates, artifacts, policy/evidence facts, and a Verified subset-minimal core only when both core verification and subset-minimality verification succeeded.
It does not claim minimum-cardinality, globally smallest, or optimal.

### VERIFIED_SAT
The explanation identifies independently verified SAT and exposes the verified scope, evaluation domain, semantic premises, and supporting facts.
The current SolveResult does not expose a complete satisfying assignment, so the explanation does not invent one.

### INSUFFICIENT_EVIDENCE
The explanation preserves the conservative result and states that available evidence is insufficient for an independent SAT/UNSAT conclusion.

### INVALID_TRACE
The explanation states that structural or semantic trace validation failed. Resolver outcome fields are not presented as proof.

## 5. Dependency-path derivation
Dependency paths are reconstructed only from production semantic objects: SemanticConstraint -> Requirement or DependencyEdge -> Requirement -> parent Candidate.
The layer never reconstructs resolver backtracking, resolver decision order, native conflict messages, heuristic search history, or native incompatibility derivations.

## 6. Auditable references
Every explained semantic constraint retains its production constraint ID. Dependency paths have stable derived IDs. Candidate, artifact, and evidence records retain their production IDs.
The evaluation-domain ID is copied from the already verified trace result. It is presentation of an existing verified fact, not a new semantic interpretation.

## 7. Determinism
Rendering uses stable ordering for semantic constraints, dependency paths, candidates, artifacts, policy facts, evidence facts, verification issues, and warnings.
No timestamps, random IDs, resolver search order, filesystem enumeration, network state, or native diagnostics enter rendered output.

## 8. Relationship to verifier and solver
The production verifier remains responsible for trace/schema validation, proof binding, evidence sufficiency, candidate-domain coverage, provenance, independent SAT/UNSAT evaluation, and claimed-core verification.
The production solver remains responsible for finite semantic SAT/UNSAT evaluation, conservative handling of unsupported semantics, subset-minimal core extraction, and core verification.
The explanation layer is downstream of those components. It must not become a second verifier or solver.

## 9. Fail-closed behavior
Authoritative SAT/UNSAT explanations require an independently verified result.
INSUFFICIENT_EVIDENCE and INVALID_TRACE are never rewritten as SAT or UNSAT.
A supplied core is described as a verified subset-minimal core only when both core verification and minimality verification succeeded.

## 10. Limitations
The explanation layer does not add dependency-resolution semantics, expand PEP 508 support, inspect package indexes, execute package code, infer facts from resolver diagnostics, compute a new SAT/UNSAT result, compute minimum-cardinality or globally optimal explanations, or expose a complete SAT assignment unless the solver API is extended.

## 11. Non-goals
Phase 5 does not add a CLI, HTTP/API service, additional resolver adapters, a new semantic fragment, research verifier changes, performance optimization, UI state, or external side effects.