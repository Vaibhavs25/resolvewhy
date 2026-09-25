# Production Independent Verifier

## 1. Purpose

Phase 4A adds the production trust boundary for resolvewhy-trace/1.0.

The verifier reconstructs the semantic proposition represented by a production Trace and independently determines whether that proposition is satisfiable over its explicitly declared proof scope.

It does not reuse the research verifier and does not invoke a resolver.

Public entry points:

~~~python
from resolvewhy.verification import verify, verify_serialized

result = verify(trace)
result = verify_serialized(serialized_trace)
~~~

The result is a typed VerificationResult with one of:

- VERIFIED_SAT
- VERIFIED_UNSAT
- INSUFFICIENT_EVIDENCE
- INVALID_TRACE

A verified result is independent of the producer's status_claim.

## 2. Trust boundary

The verifier treats every trace as untrusted input.

The following are non-authoritative:

- resolver status claims;
- human-readable resolver diagnostics;
- ResolutionImpossible observations;
- resolver-native incompatibility labels;
- search and backtracking state;
- provider exhaustion without completeness evidence;
- resolver decision levels and derivation trees.

Resolver-native observations may remain in the trace as evidence, but they do not determine the mathematical result.

## 3. Verification sequence

Verification proceeds in this order:

1. Check that the input is a production Trace or safely decode resolvewhy-trace/1.0.
2. Run the existing structural validator.
3. Resolve proof-premise bindings.
4. Check proof-relevant evidence states.
5. Check candidate-domain completeness and attestation support.
6. Check evaluation-domain and branch binding.
7. Validate supported semantic constraint shapes.
8. Validate provenance and detect cycles.
9. Reconstruct the finite semantic proposition for each applicable runtime context.
10. Independently evaluate SAT/UNSAT.
11. Compare the independent result with status_claim without trusting the claim.
12. Independently verify a claimed core, when present.
13. Independently verify subset-minimality when subset_minimal_claim is set.
14. Return a structured VerificationResult.

Malformed references and inconsistent proof bindings are INVALID_TRACE.

Semantically relevant but incomplete or unsupported information is INSUFFICIENT_EVIDENCE.

## 4. Supported semantic fragment

Phase 4A intentionally implements only the already established finite semantic boundary.

### Version constraints

The evaluator supports normalized constraints with:

- ==
- !=
- <
- <=
- >
- >=

The implemented version representation is deliberately narrow: numeric two- or three-component releases and the tested a, b, and rc prerelease forms.

Versions outside that representation are not approximated; verification becomes insufficient.

Multiple literals in one semantic constraint are interpreted conjunctively.

### Dependency edges

Dependency constraints preserve:

- parent candidate identity;
- target package identity;
- normalized version predicates;
- activation conditions.

A dependency is checked only when its parent candidate is selected and its activation condition evaluates true in the current runtime context.

### Activation and markers

The evaluator supports the tested boolean marker forms:

- atoms;
- and;
- or;
- not.

The supported runtime variables are those established by the validated fragment, including Python-version and platform values and explicitly supplied marker values.

Unsupported marker variables or operators and unavailable marker values fail closed as INSUFFICIENT_EVIDENCE.

### Finite candidate domains

Candidate enumeration is treated as a proof obligation.

For every proof-relevant package and applicable runtime context, the verifier requires a candidate domain with:

- complete coverage status;
- an explicit coverage attestation;
- attestation evidence that supports that candidate-domain reference;
- candidates whose package identity matches the declared domain;
- candidate source identities consistent with a non-empty declared source scope.

Observed candidates without complete coverage cannot establish UNSAT.

An explicitly complete empty domain is meaningful and may establish UNSAT when the proposition requires a candidate from that empty domain.

### Runtime context and evaluation domain

A RuntimeContext describes one environment.

An EvaluationDomain explicitly identifies the finite environments over which the proof is quantified.

The verifier never derives proof quantification from trace_scope, resolver policy, filenames, or diagnostic text.

Supported proof quantifiers are:

- existential: at least one applicable branch is SAT;
- universal: every applicable branch must be SAT;
- branch: the explicitly referenced runtime environment is evaluated.

The evaluation domain therefore remains part of the mathematical proposition rather than resolver metadata.

### Requires-Python

requires_python literals are evaluated against the explicitly bound python_full_version of the applicable runtime context.

Unsupported version semantics remain insufficient rather than being approximated.

### Candidate and artifact semantics

Candidates and artifacts remain distinct.

For artifact_compatibility constraints:

- explicitly incompatible artifacts make the selected candidate path unsatisfiable;
- explicitly compatible, available artifacts are accepted;
- unknown compatibility is insufficient;
- yanked, filtered, or otherwise unknown selection status is insufficient unless supported policy semantics establish admissibility;
- contradictory artifact status and compatibility facts are invalid semantic data.

Full wheel or sdist selection and build-system semantics are intentionally outside this implementation.

### Resolution policy

Only policy semantics already sufficiently established for the implementation are evaluated.

Prerelease policy supports the explicit modes represented by the production model.

Other populated policy fields such as source-selection, hash, format, cutoff, lockfile, or version-selection settings are currently treated as unsupported rather than silently interpreted.

## 5. Evidence sufficiency

Evidence is classified separately from structural validity.

The verifier returns INSUFFICIENT_EVIDENCE when a proof-relevant fact is:

- incomplete;
- missing;
- unknown;
- outside the supported semantic fragment;
- not accompanied by complete candidate-domain coverage;
- dependent on artifact semantics that are not established.

The verifier does not convert absence of evidence into evidence of absence.

## 6. Provenance

Every proof premise must have supporting provenance.

The verifier:

- resolves provenance subjects;
- validates provenance premise references;
- checks referenced evidence states;
- builds the provenance dependency graph;
- detects provenance cycles;
- distinguishes direct and derived provenance records.

Provenance establishes auditability. It does not replace independent semantic evaluation.

## 7. Proof claims and cores

proof_claim.status_claim is advisory.

The verifier independently computes the result and reports claim_mismatch when the producer's status claim disagrees.

Proof premises must refer to actual semantic constraints.

When claimed_core_refs are present, the verifier checks that they are within the proof premises and independently checks whether the claimed core is UNSAT under the same proof scope.

When subset_minimal_claim is true, the verifier additionally:

1. verifies that the claimed core is UNSAT;
2. removes each core constraint individually;
3. reevaluates the remaining proposition;
4. requires every single-deletion result to be SAT.

This establishes subset-minimality by individual deletion.

It does not establish minimum cardinality.

## 8. Result model

VerificationResult contains structured metadata including:

- final VerificationStatus;
- independently_verified;
- proof-claim identifier;
- quantifier;
- evaluation-domain runtime references;
- checked premise IDs;
- checked core IDs;
- core_verified;
- minimality_verified;
- structured reason codes;
- structural and verification issues;
- per-branch SAT/UNSAT outcomes.

A VERIFIED_* status means the semantic proposition was independently decided within the supported fragment.

INSUFFICIENT_EVIDENCE and INVALID_TRACE are never treated as successful verification.

## 9. Security

The verifier is declarative.

Verification code does not:

- execute trace content;
- use eval or exec;
- import modules named by trace data;
- invoke package managers;
- execute package code;
- access the network;
- execute build backends;
- follow arbitrary URLs or filesystem paths as proof dependencies.

The verifier depends only on the production model, trace codec, structural validator, and standard-library evaluator code.

## 10. Determinism

For a fixed production trace, verification is deterministic.

The evaluator does not consult:

- package indexes;
- resolver search order;
- network state;
- filesystem ordering;
- timestamps;
- external resolver state.

Finite search has an explicit state limit. Exceeding that limit produces INSUFFICIENT_EVIDENCE rather than an unverified result.

## 11. Test coverage

The dedicated Phase 4A suite contains 46 tests covering:

- SAT reconstruction;
- transitive dependency graphs;
- conditional activation;
- source-distinct candidates;
- compatible artifacts;
- direct and transitive UNSAT;
- Requires-Python;
- artifact incompatibility;
- finite universal and branch scopes;
- incomplete candidate coverage;
- unsupported markers and versions;
- unsupported policy;
- unknown and yanked artifact states;
- malformed references;
- duplicate identities;
- invalid proof bindings;
- provenance cycles;
- non-authoritative resolver claims;
- fabricated completeness;
- altered evaluation domains and quantifiers;
- altered proof premises;
- candidate and artifact mutations;
- activation and policy mutations;
- serialized verification;
- deterministic repeatability;
- independently checked subset-minimality.

The existing production suite remains part of the validation set.

## 12. Known limitations

Phase 4A does not establish complete support for:

- arbitrary PEP 508;
- complete extras semantics;
- dynamic build metadata;
- full wheel or sdist selection;
- complete hash semantics;
- complete lockfile semantics;
- implicit virtual or provided packages;
- symbolic or infinite environment domains;
- undocumented resolver-specific semantics.

Those cases must remain incomplete rather than being silently generalized.

## 13. Phase boundary

Phase 4A is the independent verification boundary.

The following are intentionally not included:

- optimization or Phase 4B solver work;
- global minimum-cardinality search;
- explanation rendering;
- CLI;
- API layer;
- additional resolver adapters.

Production readiness has not been claimed merely because Phase 4A verification tests pass.
