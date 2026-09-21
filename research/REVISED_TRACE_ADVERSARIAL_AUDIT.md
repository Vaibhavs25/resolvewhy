# Revised Trace Adversarial Audit

**Date:** 2026-09-21

## Research question

Can the revised resolvewhy-trace contract distinguish a genuinely unsatisfiable dependency problem from a problem caused by incomplete, filtered, bounded, or otherwise non-exhaustive evidence?

The experiment focused on actual pip/resolvelib execution, actual uv execution, current upstream source inspection for Poetry/pipgrip, and a tiny contract-level proof gate.

No production adapters or generalized framework were built.

## Resolver/source versions

### Executable environment

- Python: 3.13.5
- pip runtime: 25.1.1
- uv runtime: 0.10.0
- Poetry executable: not installed
- pipgrip executable: not installed

### Current upstream source snapshots inspected

| System | Version / source state | Commit |
|---|---|---|
| resolvelib | 1.2.2.dev0 | a0cb7c50b78028f840b238d8e1c391e0546f2325 |
| pip | 26.3.dev0 source tree | 892d13b34a20b3244a05d90622bbb5bf8e7ccf46 |
| Poetry | 2.5.1 | 94b6e35b9091991887aa54feeb3771a86d3bd692 |
| pipgrip | current repository HEAD | 195dfe41f9efa7abe161d6d69368e35939867b33 |
| uv | 0.10.0 source tree | a1b84bcbda122236faae8fa5fdcbe16cfb76cde2 |

The executable pip runtime is older than the inspected pip source tree. Executable evidence therefore specifically describes pip 25.1.1; source-level architecture evidence uses the later pip commit above.

## Test matrix

### A. Multiple indexes

A package existed only on local index B.

Observed:
- pip with index A only: resolution failed with no matching distribution.
- pip with A+B: package resolved and the selected artifact URL pointed to B.
- uv with index A only: resolution failed.
- uv with A+B: package resolved.

Interpretation:
Candidate absence is meaningful only relative to the declared source scope.

Classification: **CORRECTLY REPRESENTED**, provided coverage scope includes the source set.

### B. Platform filtering

A package existed as a Windows-only wheel while the execution environment was Linux.

Observed:
- pip failed with no matching distribution.
- uv explained that the only available version had no wheel with a matching platform tag and named the Windows tag.

Interpretation:
The package/version existed, but a usable artifact did not exist for the current artifact-selection context.

Classification: **CORRECTLY REPRESENTED** after separating candidate identity from artifact identity.

### C. Requires-Python

A package candidate declared Requires-Python >=4 while the execution environment was Python 3.13.5.

Observed:
- pip rejected the package because 3.13.5 did not satisfy >=4.
- uv produced an incompatibility explanation tying the available version to its Python requirement.

Interpretation:
The candidate exists. Usability is constrained by runtime/policy context.

Classification: **CORRECTLY REPRESENTED**.

### D. Prereleases

Only foo==1.0rc1 was available, with requirement foo<2.

Observed:
- pip default rejected the prerelease.
- pip with --pre selected 1.0rc1.
- uv 0.10.0 default behavior selected the prerelease.
- uv with --prerelease=disallow rejected it.
- uv with --prerelease=if-necessary-or-explicit selected it.

Interpretation:
Prerelease eligibility is a resolver-policy interaction.

Classification: **CORRECTLY REPRESENTED** only when resolution policy is explicit.

This directly falsifies any normalization that omits prerelease policy.

### E. Direct URL and VCS identity

A local wheel was supplied through a direct file URL. A local git repository was resolved through a VCS URL.

Observed:
- pip successfully resolved the direct wheel URL.
- pip --report recorded the direct URL.
- pip --report recorded VCS kind and commit_id for the local git dependency.
- uv successfully resolved the direct local wheel.
- pip and uv resolved the local git dependency when build isolation was disabled.

Interpretation:
package + version is insufficient as complete identity of a satisfiability-relevant candidate.

Classification: **CORRECTLY REPRESENTED** by opaque candidate identity plus source/provenance.

### F. Incomplete or invalid metadata

A local wheel was deliberately constructed without a valid .dist-info/METADATA structure.

Observed:
- pip raised BadMetadata for an invalid metadata entry.
- uv warned that the package had an invalid package format and produced an unsatisfiable-resolution explanation.

Interpretation:
Two cases must be separated:
1. the resolver has authoritative evidence that the artifact is invalid;
2. the trace capture simply failed to obtain metadata.

Case 1 is an observed candidate/artifact rejection.
Case 2 is incomplete evidence and must not be converted into UNSAT.

Classification: **CORRECTLY REPRESENTED** after distinguishing observed invalidity from capture incompleteness.

### G. Bounded / subset discovery

The same package was made available on two independent local index scopes.

Observed:
- querying only index A omitted a package present on B;
- querying A+B exposed the additional candidate;
- the contract-level proof gate rejected bounded or observed coverage as proof of no-candidate.

This demonstrates the essential subset-of-domain failure without altering pip internals.

Classification: **INSUFFICIENT EVIDENCE CORRECTLY DETECTED**.

### H. Artifact-level rejection

The Windows-only wheel case produced a package/version candidate but no compatible artifact for Linux.

Classification: **CORRECTLY REPRESENTED** with a distinct artifact entity.

## Contract-level adversarial checks

A tiny proof gate tested:
1. complete + authoritative finite domain -> no-candidate proof permitted
2. observed subset -> proof forbidden
3. bounded provider -> proof forbidden
4. unknown coverage -> proof forbidden
5. same package/version from different sources -> identities remain distinct
6. rejection without exhaustive coverage -> no-candidate proof forbidden
7. resolver-specific namespaces remain distinct
8. runtime context and resolution policy remain separate

Result:

**8/8 contract checks passed.**

## Hostile cases and repairs

### Looks complete but is actually incomplete

A trace can appear complete if it marks an observed candidate list complete without declaring the source/domain covered.

**Repair:** completeness is relative to an explicit candidate domain and requires an exhaustion attestation for that domain.

### Real UNSAT looks satisfiable

Prior repaired-core tests and 3,000/3,000 restricted random oracle validation cover this risk. The revised contract does not bypass independent verification.

### SAT looks UNSAT

Partial, unknown, or bounded evidence must produce insufficient_evidence rather than a no-candidate proof.

### Semantically different candidates share identity

Same name/version packages served from different local indexes were used as the concrete case.

**Repair:** opaque adapter-defined candidate IDs plus source identity.

### Provider rejection treated as proof

A rejection/backtracking event is not an exhaustive source-domain attestation.

**Repair:** rejection is a typed observation; it cannot independently authorize a no-candidate proof.

### Source/index distinction lost

Multiple-index and same-version/different-source cases show source scope is semantically relevant.

**Repair:** source scope participates in candidate-domain definition and provenance.

### Environment/policy lost

Requires-Python and prerelease cases show the same candidate set can produce different outcomes under different context/policy.

**Repair:** split runtime_context and resolution_policy.

### Resolver-specific derivation flattened

Poetry, pipgrip and uv expose Mixology/PubGrub-style derivations; resolvelib exposes causes/criteria and reporter hooks.

**Repair:** normalize semantic literals/provenance and retain native derivation under a resolver namespace.

## Additional semantic tightening discovered

A generic resolver_exhaustion basis is too strong if interpreted without a domain attestation.

A resolver may exhaust the candidate set returned by a provider while that provider itself observed only a subset of the external source universe.

Therefore:

> Resolver exhaustion is not sufficient by itself to prove external source exhaustion.

The revised contract requires completeness to be tied to an explicitly declared candidate domain and an attestation explaining why that domain is exhaustive.

## Final classification

| Case | Result |
|---|---|
| Multiple indexes | CORRECTLY REPRESENTED |
| Platform filtering | CORRECTLY REPRESENTED |
| Requires-Python | CORRECTLY REPRESENTED |
| Prerelease policy | CORRECTLY REPRESENTED |
| Direct URL identity | CORRECTLY REPRESENTED |
| VCS identity/provenance | CORRECTLY REPRESENTED |
| Invalid artifact metadata | CORRECTLY REPRESENTED |
| Missing capture metadata | INSUFFICIENT EVIDENCE CORRECTLY DETECTED |
| Bounded discovery | INSUFFICIENT EVIDENCE CORRECTLY DETECTED |
| Artifact-level rejection | CORRECTLY REPRESENTED |
| Source-distinct same-version candidates | CORRECTLY REPRESENTED |
| Resolver-specific derivation | REPRESENTABLE BUT LOSSY unless namespaced |

No tested case produced a false proof after the revised rules were applied.

## Final judgment

**A. REVISED CONTRACT SURVIVES**

The revised contract survives the targeted adversarial experiment.

This means the semantics are sufficiently precise for the tested evidence classes. It does not establish:
- cross-ecosystem portability
- a stable public interchange API
- maintainer adoption
- production readiness

**H2e remains NOT TESTED.**
