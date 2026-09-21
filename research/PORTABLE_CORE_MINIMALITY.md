# Portable Core Minimality

**Date:** 2026-09-21

## Scope

This document asks which information is necessary for correctness, proof scope, provenance, or explanation quality in the tested semantic fragment.

## Classification

| Field | Classification | Evidence / rationale |
|---|---|---|
| Requirement | REQUIRED FOR CORRECTNESS | Defines the root constraint being satisfied or contradicted. |
| Dependency edge | REQUIRED FOR CORRECTNESS | Carries transitive constraints from a selected candidate to its dependencies. |
| Activation condition | REQUIRED FOR CORRECTNESS | Marker/extras activation changes whether an edge exists in the evaluated branch. |
| Opaque candidate identity | REQUIRED FOR CORRECTNESS | Prevents source/VCS/path/artifact-relevant candidates from being silently identified by package/version alone. |
| Artifact identity | REQUIRED FOR CORRECTNESS when artifact selection affects satisfiability | A candidate can exist while every usable artifact is incompatible, yanked, or filtered. |
| Runtime context | REQUIRED FOR PROOF SCOPE | `Requires-Python`, platform and marker semantics depend on the evaluated environment. |
| Evaluation domain | REQUIRED FOR PROOF SCOPE for multi-environment claims | The collision search showed that a universal claim can differ in truth solely because the quantified environment set differs. |
| Resolution policy | REQUIRED FOR PROOF SCOPE | Prerelease, yank, source selection, cutoff, and format behavior can change candidate usability without changing candidate identity. |
| Candidate-domain coverage | REQUIRED FOR PROOF SCOPE | Prevents observed/bounded candidate sets from being treated as exhaustive. |
| Semantic constraint/literal | REQUIRED FOR CORRECTNESS | This is the normalized object actually checked by the independent proof engine. |
| Provenance | REQUIRED FOR PROVENANCE | Makes derived facts auditable and prevents unsupported claims from entering the proof. |
| Evidence state | REQUIRED FOR PROOF SCOPE | Distinguishes known facts from missing/partial observations and forces `insufficient_evidence` when necessary. |
| Native derivation tree | REQUIRED ONLY FOR EXPLANATION QUALITY / audit detail | The tested proof engine remained correct after deletion; the native tree remains valuable as namespaced evidence. |
| Decision level | SAFE TO DISCARD for correctness | Deletion did not change the semantic truth of the tested problem. |
| Backjump state | SAFE TO DISCARD for correctness | Solver search state is not part of the independently recomputed satisfiability relation. |
| Candidate ordering / preference | SAFE TO DISCARD for correctness | Ordering can affect search path but not the truth of the normalized complete problem. |
| Human-readable diagnostics | SAFE TO DISCARD for proof | They are observational output, not proof premises. |
| Provider implementation metadata | RESOLVER-SPECIFIC; SAFE TO DISCARD after semantic extraction | Implementation detail is not itself a portable semantic primitive. |
| Resolver-specific rejection structure | RESOLVER-SPECIFIC | Meaning varies; only extracted semantic consequences belong in the common core. |
| Resolver-specific incompatibility structure | RESOLVER-SPECIFIC | PubGrub/Mixology derivations and resolvelib causes are not one universal object type. |
| Index authentication/search machinery | RESOLVER-SPECIFIC | Required evidence may be represented as source-query outcome, coverage, provenance, and evidence state. |

## Necessary-information principle

A field is necessary for correctness when deleting it permits a satisfiability-relevant projection collision or invalid proof.

A field is necessary for proof scope when deleting it changes what domain is actually being claimed or what evidence is exhaustive.

A field is necessary for provenance when deleting it makes a derived claim unauditable.

A field is explanation-only when deletion leaves the truth of the independent proof query unchanged but reduces diagnostic detail.

## Critical result

The portable core was close to minimal but not complete.

The one field discovered to be missing was **evaluation domain**. The current runtime context identifies the environment of an observation, but not the set of environments over which a universal/forked claim is quantified.

Once `evaluation_domain` is added, the finite projection search separates the previous SAT/UNSAT collision.

## Resolver-neutrality boundary

The experiment supports a small semantic core, not a universal common representation of resolver implementations.

Native objects can be discarded from the proof calculation when their satisfiability-relevant semantic consequences have already been extracted. They should remain available as namespaced provenance/audit material where useful.

## Final classification

The smallest defensible proof core for the tested fragment is:

`requirement`
`dependency edge`
`activation condition`
`opaque candidate identity`
`artifact identity where relevant`
`runtime context`
`evaluation domain when claims are multi-environment`
`resolution policy`
`candidate-domain coverage`
`semantic constraint/literal`
`provenance`
`evidence state`

This is the current research boundary. It is not claimed to be complete for all resolver ecosystems.