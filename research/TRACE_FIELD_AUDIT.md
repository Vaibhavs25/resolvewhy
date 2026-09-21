# Trace Field Audit — resolvewhy-trace/v0

Research date: 2026-09-21

This document audits each current trace field against the public architecture of resolvelib/pip, Poetry, pipgrip/PubGrub and uv.

Status vocabulary:

- SUPPORTED: the semantic concept recurs and can be represented without pretending implementation identity.
- PARTIALLY AVAILABLE: the concept exists, but completeness or public exposure is conditional.
- INTERNAL ONLY: useful information exists but mainly inside implementation structures.
- PROVIDER-SPECIFIC: semantics are owned by candidate/source/provider layers.
- AMBIGUOUS: the field is too broad to make a trustworthy cross-resolver claim without additional typing.
- NOT AVAILABLE: not established in the inspected architecture.
- UNKNOWN: not sufficiently established by the evidence inspected.

## 1. Candidate identity

Current v0:
Candidate records require package + version and may contain an additional identity string.

Audit:
SUPPORTED SEMANTICALLY; representation is PROVIDER-SPECIFIC.

All four architecture families have a notion corresponding to candidate/package/version identity. But package + version is not universally sufficient.

Satisfiability-relevant distinctions can include URL/direct references, VCS references, local paths, alternate source/index, artifact/platform identity, and extras/source-qualified nodes.

Required revision:
Make candidate.id an opaque adapter-defined identity. Keep candidate.package, candidate.version, candidate.identity as semantic projections. The adapter must not collapse two candidate identities merely because their displayed versions match.

## 2. Candidate inventory / candidate completeness

Current v0:
One global boolean: candidate_inventory_complete.

Audit:
PARTIALLY AVAILABLE; current representation is insufficient.

This is the most important schema defect.

Candidate discovery occurs at different layers:
- resolvelib delegates candidate enumeration to the provider
- pip builds/filters candidates through finder/factory/provider layers
- Poetry and pipgrip obtain versions through source/provider abstractions
- uv tracks available/included/incomplete version information internally

Therefore completeness can differ by package/query, source, index, environment, artifact filter, policy and discovery strategy.

Required revision:
Replace the single global boolean with per-query coverage:
status: complete | partial | unknown
basis: authoritative_finite_domain | exhaustive_provider_query | resolver_exhaustion | bounded | observed
scope: sources/indexes/environment/filters
evidence_refs: supporting observations

Proof rule:
Only complete coverage backed by an exhaustive/authoritative basis can support a claim equivalent to “no compatible candidate exists.”
A bounded or observed candidate set must never support that proof.

## 3. Dependency edges

Current v0:
dependency_observations contains parent candidate, requirement and active flag.

Audit:
SUPPORTED SEMANTICALLY.

All four architectures have an equivalent concept:
- resolvelib: provider get_dependencies(candidate)
- Poetry: provider/package dependency metadata
- pipgrip: dependencies_for(package, version)
- uv: dependency-provider/resolver metadata

Required revision:
Preserve parent candidate identity, raw dependency representation, normalized semantic requirement, activation condition, and source/provider namespace when interpretation is resolver-specific.

An inactive edge should remain observable when it matters to proving that the edge was considered.

## 4. Requirement representation

Current v0:
Requirements preserve raw text plus evidence state.

Audit:
SUPPORTED.

All systems have a structured requirement/dependency concept, but their normalized representations differ.

Required revision:
Keep raw, normalized, and activation/context information.
Do not assume every internal requirement language is identical.

## 5. Environment / policy context

Current v0:
A single environment object.

Audit:
SUPPORTED, but current field is too broad.

Runtime facts and resolver policy are different evidence domains.

Examples of policy-sensitive facts include prerelease selection, source/index selection, format/artifact constraints, Python requirement, exclude-newer cutoffs, and universal/forked resolution.

Required revision:
Split runtime_context and resolution_policy.

A proof must identify which policy values influenced candidate visibility.

## 6. Candidate rejection events

Current v0:
rejections contains candidate, requirements and a free-form reason.

Audit:
PARTIALLY AVAILABLE; semantics are AMBIGUOUS across ecosystems.

resolvelib exposes a public rejection hook.
pip has internal rejection/reporting machinery.
Poetry, pipgrip and uv contain rich internal conflict/rejection mechanisms.

But “rejected” can mean resolver backtracking, dependency conflict, no versions, Python mismatch, platform mismatch, source/index exclusion, artifact incompatibility, or policy exclusion.

Required revision:
Require typed reason_kind and source_layer.

Suggested source layers:
resolver
provider
index
source
artifact
policy
environment

A rejection record is not exhaustive unless separately covered by completeness evidence.

## 7. Incompatibility / conflict evidence

Current v0:
incompatibilities contains literals and provenance.

Audit:
SUPPORTED SEMANTICALLY; resolver-specific representation must be preserved.

Poetry, pipgrip and uv expose PubGrub/Mixology-style clause/derivation objects. resolvelib exposes causes/criteria, but not the same derivation-tree object.

Required revision:
Add semantics, resolver_namespace, and derivation.

The normalized core should use semantic literals + provenance, not assume identical native conflict semantics.

## 8. Provenance

Current v0:
Claims link to premise identifiers.

Audit:
SUPPORTED SEMANTICALLY; derivation semantics differ.

All four systems have some causal relation:
- resolvelib requirement-parent/cause relationships
- Poetry incompatibility causes and conflict derivations
- pipgrip ConflictCause derivations
- uv ErrorTree derivations

Required revision:
Keep claim-to-premise links, but derived claims should include derivation_rule and source_namespace.

A free-form explanation string must never substitute for proof provenance.

## 9. Resolver state / decision context

Current v0:
Mostly represented through events.

Audit:
INTERNAL ONLY / OPTIONAL.

Selection order, decision levels, backjump targets and partial solver state exist in these resolver families but are not semantically interchangeable.

Required revision:
Do not make detailed solver state part of the minimal proof core.
Represent it as optional, namespaced evidence.
The verified MUS must remain independently recomputable from the normalized constraint domain.

## 10. Source / index information

Current v0:
source/index facts are represented as generic provenance information.

Audit:
PROVIDER-SPECIFIC.

All four systems can carry source/index information, but they differ in repository models, index selection, direct origins, local paths, source priorities and source capabilities.

Required revision:
Expose generic source identity and query scope, but preserve detailed source behavior in provider-specific evidence.

This field must contribute to coverage when candidate enumeration depends on it.

## 11. Artifact selection

Current v0:
Artifact compatibility is represented generically.

Audit:
PARTIALLY AVAILABLE; PROVIDER-SPECIFIC.

pip and uv have substantial artifact machinery involving Python compatibility, platform tags, wheels/source distributions, hashes and format policies. Poetry and pipgrip expose less uniform artifact-level semantics.

Required revision:
Do not turn artifact selection into a universal resolver primitive.
Represent artifact identity, compatibility facts, selection/filter reason, and source layer when available.

A proof involving artifact availability must not rely on version-only candidate identity.

## Cross-field dependency

The fields are not independent.

The more accurate dependency structure is:

runtime_context + resolution_policy
                 |
                 v
       source/index scope
                 |
                 v
         candidate_query
            /                  v         v
candidate coverage  candidate facts
                    /
             v     v
        dependency edges
                 |
                 v
       semantic constraints
             /                   v         v
     resolver events  provenance
                    /
               v   v
           explanation/MUS

This is why a trace-wide boolean completeness flag is insufficient.

## Revised minimal semantic core

The smallest defensible resolver-neutral core is:

1. requirement
2. opaque candidate identity
3. dependency edge
4. runtime context
5. resolution policy
6. candidate-domain coverage
7. semantic constraint/literal
8. provenance
9. explicit evidence state

Everything else should be optional or namespaced resolver evidence.

## Final field decision

| Field | Current v0 | Decision |
|---|---|---|
| Candidate identity | package + version + optional identity | REVISE |
| Candidate inventory completeness | global boolean | REVISE STRONGLY |
| Dependency edges | parent + requirement + active | KEEP WITH TYPING |
| Requirements | raw requirement | KEEP |
| Environment | single object | SPLIT |
| Rejections | candidate + free-form reason | REVISE |
| Incompatibilities | generic literals | REVISE / NAMESPACE |
| Provenance | claim -> premises | KEEP + derivation metadata |
| Resolver state | events | KEEP OPTIONAL / NAMESPACE |
| Source/index | generic | KEEP OPTIONAL / PROVIDER-SPECIFIC |
| Artifact selection | generic | KEEP OPTIONAL / PROVIDER-SPECIFIC |
| Evidence states | known/derived/rejected/incomplete/missing | KEEP |
| Completeness model | global booleans | REVISE TO PER-DOMAIN COVERAGE |

## Final verdict

The abstraction survives.

The current wire semantics do not fully survive.

Decision: REVISE resolvewhy-trace/v0.

The revision is required to prevent false proofs when candidate discovery, filtering, provenance or conflict semantics are owned by different layers of a resolver architecture.

H2e remains NOT TESTED because this audit contains no maintainer feedback.


## Revised-contract adversarial results — 2026-09-21

The revised field semantics were tested against local pip 25.1.1 and uv 0.10.0 cases and current source for Poetry 2.5.1 and pipgrip.

Key refinements from the experiment:

1. Candidate completeness is per candidate-domain/query, not trace-global.
2. Complete coverage must be tied to an explicit source/index/query scope and an exhaustion attestation.
3. A generic resolver-exhaustion assertion cannot independently prove external source exhaustion.
4. Candidate identity is opaque and source-aware; package/version is not always unique.
5. Artifact is a distinct entity from candidate where wheel/source artifact selection affects installability.
6. Runtime context is separate from resolution policy, especially for prerelease and universal/forked resolution.
7. Rejection records require reason kind and source layer and do not imply exhaustive rejection.
8. Native incompatibility/derivation structures remain namespaced; only semantic literals and provenance are normalized.
9. Missing metadata from the capture remains insufficient_evidence; an actually observed invalid artifact can be a known rejection.

Targeted contract test result: **8/8 checks passed**.

The revised schema is defined in research/REVISED_TRACE_SCHEMA.md.
