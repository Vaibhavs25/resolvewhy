# Final Semantic Boundary

**Date:** 2026-09-21  
**Decision:** **A. BOUNDARY SURVIVES — NO NEW SEMANTIC DEFECT**

## 1. Purpose

This document defines the largest semantic fragment justified by the experiments completed so far. It is a research boundary, not a claim of universal resolver compatibility.

The tested question is whether the current semantic trace and independent verifier preserve enough satisfiability-relevant information to distinguish SAT, UNSAT, insufficient evidence, and invalid artifacts without consulting native resolver state.

## 2. Validated fragment

### Dependency semantics

Validated for:
- conjunctions of normalized version constraints;
- parent-linked dependency edges;
- candidate-specific dependency metadata;
- active/inactive dependency edges;
- environment-marker activation for the tested marker forms;
- multiple simultaneously active dependency edges;
- source-aware/direct/VCS candidate identity in the tested reduced cases;
- prerelease and yank policy distinctions where represented as policy/artifact evidence;
- Requires-Python compatibility;
- finite candidate domains with explicit completeness scope and attestation.

Rich PEP 508 expressions are structurally representable through activation conditions, but exhaustive semantic preservation for every legal marker expression and every marker-variable interaction has not been established. The current packaging specification includes nested and/or markers and fields including python_version, python_full_version, sys_platform, platform_machine, implementation fields, extra, extras, and dependency_groups. citeturn936757search1

### Environment semantics

Validated for:
- explicit runtime context;
- Python-version compatibility;
- platform-sensitive activation;
- finite evaluation domains;
- singleton, existential, universal, and branch proof claims;
- multi-environment claims when the domain is explicitly serialized and bound to the proof claim.

Not established for arbitrary symbolic/infinite environment domains or every possible future marker interpretation.

### Candidate and artifact semantics

Validated for:
- opaque candidate identity;
- source-qualified identity;
- candidate/artifact separation;
- platform-compatible versus incompatible artifacts;
- per-artifact status in reduced cases;
- Requires-Python restrictions;
- prerelease/yank policy distinctions.

Not established for every build and artifact-selection rule used by every package manager.

### Proof semantics

Validated for:
- explicit proof claim;
- quantifier binding;
- explicit evaluation-domain reference;
- semantic premise references;
- independent SAT/UNSAT recomputation;
- subset-minimality by single-element deletion;
- fail-closed result classes.

Minimum-cardinality explanations are not established.

### Evidence and coverage

Validated for:
- complete versus partial/unknown candidate coverage;
- source/query scope;
- completeness attestation;
- evidence states;
- provenance reachability;
- refusal to infer global absence from bounded or failed source queries;
- serialization round-trip integrity;
- structural mutation fail-closed behavior.

## 3. Boundary families

| Family | Result | Boundary |
|---|---|---|
| Nested PEP 508 markers | Semantically representable at the activation-condition level | Exhaustive grammar/variable interaction validation is not established |
| Multiple extras | Representable in the dependency model | Full arbitrary transitive extras propagation is not exhaustively validated |
| Dynamic build metadata | Outside current proof guarantee | Generated metadata can be consumed once captured, but backend computation is not reconstructed |
| Wheel/sdist mixtures | Partially supported | Candidate/artifact separation survives tested reductions; full build-selection semantics are not established |
| Hash-allowlist rejection | Representable in principle | Complete cross-resolver hash-selection semantics are not independently demonstrated |
| Local/editable/workspace | Representable by opaque identity/provenance in reduced cases | Dynamic filesystem/build semantics remain outside guarantee |
| Lockfile constraints | Representable as extra constraints/policy in principle | Full lockfile execution/selection semantics are not end-to-end validated |
| Virtual/provided packages | Outside current guarantee when provider semantics are implicit | A synthetic node does not specify what satisfies/provides it |
| Finite multi-dimensional domains | Supported conceptually | Symbolic/infinite domain reasoning is not established |
| Dynamic source availability | Safe when serialized as scoped coverage/evidence | Hidden external availability cannot be inferred |

## 4. Nearest realistic cases outside the boundary

### Dynamic metadata generation

PEP 517 permits build backends to provide additional build requirements and metadata-generation hooks, executed in a build environment. citeturn639779search1turn936757search0

Therefore:

source tree -> backend execution -> generated dependency metadata

is not equivalent to a static dependency edge unless the generated metadata itself is captured. This is outside the current proof guarantee, not a demonstrated schema defect.

### Artifact and hash policy

The current Python lock-file specification distinguishes package identity, archive identity, hashes, environment markers and dependency records. citeturn639779search0 pip hash-checking mode likewise makes allowed hashes part of installation admissibility. citeturn639779search2

The existing artifact + policy concepts can represent reduced cases, but complete hash-policy semantics have not been independently demonstrated.

### Lockfile semantics

Lock files can constrain environments, extras, dependency groups, package markers, Requires-Python, dependency relations, archives, hashes and sources. citeturn639779search0 The current core can encode many of these as semantic constraints/policy inputs, but their complete interactions are not established.

### Virtual/provided packages

Opaque identity can represent a synthetic node, but satisfiability requires a semantic rule identifying what provides or satisfies that node. That provider relation is outside the validated finite fragment.

## 5. Automated boundary-search interpretation

The previous projection-collision methodology was extended conceptually to marker complexity, artifact relations, source scope, proof quantifiers, finite evaluation domains, policy combinations, metadata availability, local/VCS identity, lock constraints, and virtual-package-like nodes.

No new collision was identified inside the already declared finite fragment. The nearest unresolved cases are associated with semantics deliberately outside that fragment, especially build-time generation and implicit provider/provided-package relations.

This is a boundary result, not evidence of universal completeness.

## 6. No-silent-fallback rule

For outside-fragment cases:
- missing or incomplete evidence -> INSUFFICIENT_EVIDENCE;
- malformed or inconsistent trace -> INVALID_TRACE;
- resolver diagnostics are never mathematical proof;
- build logs are never mathematical proof;
- missing metadata is never inferred as absence;
- failed source access is never inferred as exhaustive candidate absence;
- the declared SAT/UNSAT label is never trusted over independent recomputation.

## 7. Field necessity recheck

| Field | Classification | Basis |
|---|---|---|
| Requirement | REQUIRED FOR CORRECTNESS | Defines root constraints |
| Dependency edge | REQUIRED FOR CORRECTNESS | Carries transitive requirements |
| Activation condition | REQUIRED FOR CORRECTNESS | Changes the active constraint set |
| Opaque candidate identity | REQUIRED FOR CORRECTNESS | Source/VCS/path distinctions can matter |
| Artifact identity | REQUIRED FOR CORRECTNESS when artifact choice matters | Platform/yank cases require candidate/artifact separation |
| Runtime context | REQUIRED FOR PROOF SCOPE | Environment-sensitive semantics |
| Evaluation domain | REQUIRED FOR PROOF SCOPE for multi-environment claims | Previous collision |
| Resolution policy | REQUIRED FOR PROOF SCOPE | Prerelease/yank/source/cutoff behavior |
| Candidate-domain coverage | REQUIRED FOR COVERAGE | Prevents false no-candidate proofs |
| Semantic constraint/literal | REQUIRED FOR CORRECTNESS | Independent proof engine consumes it |
| Provenance | REQUIRED FOR AUDITABILITY | Proof-premise reachability |
| Evidence state | REQUIRED FOR PROOF SCOPE/COVERAGE | Distinguishes absence from unknown |
| Proof claim | REQUIRED FOR PROOF SCOPE | Quantifier/domain binding |
| Native derivation tree | EXPLANATION/AUDIT ONLY in tested fragment | Native deletion preserved truth |
| Decision/backjump state | SAFE TO DISCARD for correctness in tested fragment | Search state is not needed for recomputation |
| Human-readable diagnostics | EXPLANATION ONLY | Not proof premises |
| Resolver-specific rejection/incompatibility structure | NAMESPACED | No universal native meaning established |

No existing field changed classification.

## 8. Exact supported claim

> Within the tested finite semantic fragment—normalized dependency/version constraints, parent-linked dependency edges, activation conditions, opaque/source-aware candidate identity, artifact identity where feasibility is artifact-dependent, explicit runtime context and finite evaluation domains, resolution policy, scoped candidate-domain coverage with completeness attestation, semantic literals, provenance/evidence state, and explicitly bound proof claims—resolvewhy-trace preserves sufficient satisfiability-relevant evidence for independent SAT/UNSAT verification and subset-minimal explanation, while incomplete evidence and unsupported semantics fail closed.

## 9. Deliberate exclusions

Not established for:
- arbitrary dynamic build backend semantics;
- source-tree state that changes generated metadata;
- hidden environment-variable effects during metadata generation;
- complete build-failure semantics;
- all wheel/sdist selection algorithms;
- complete hash-selection and reproducibility semantics;
- arbitrary editable/workspace filesystem semantics;
- full lockfile semantics across all tools and modes;
- arbitrary virtual/provided/system-package semantics;
- infinite or symbolic environment quantification;
- exhaustive preservation of every PEP 508 marker interaction;
- future resolver-native semantics not represented by the portable model.

These are evidence boundaries, not claims that such semantics are impossible to represent.

## 10. Final decision

**A. BOUNDARY SURVIVES — NO NEW SEMANTIC DEFECT.**

The current schema is unchanged. The technical-validation phase is sufficiently bounded for final synthesis and reproducibility packaging. H2e remains a separate empirical gate.
