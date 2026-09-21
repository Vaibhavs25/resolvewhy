# H2d Conformance Matrix

**Date:** 2026-09-21  
**Scope:** semantic portability of dependency-resolution evidence across pip/resolvelib, uv, Poetry/Mixology, and pipgrip/PubGrub.

## Legend

- **SUPPORTED** — the semantic concept can be represented without changing its role.
- **PARTIAL** — concept exists, but coverage/exposure/meaning is conditional.
- **NAMESPACED** — native semantics should remain resolver-specific.
- **UNKNOWN** — not established by the executed/source evidence.
- **NOT REPRESENTABLE** — the tested evidence cannot be represented safely in the current semantic model.

## Field matrix

| Semantic field | pip/resolvelib | uv | Poetry/Mixology | pipgrip/PubGrub | Portable-core decision |
|---|---|---|---|---|---|
| Requirement | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| Parent candidate / dependency edge | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| Activation / environment marker | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| Opaque candidate identity | SUPPORTED | SUPPORTED | PARTIAL | PARTIAL | SUPPORTED |
| Package/version projection | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| Source/index identity | PARTIAL | SUPPORTED | PARTIAL | PARTIAL | SUPPORTED with explicit scope |
| Direct URL identity | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| VCS identity | SUPPORTED | SUPPORTED | SUPPORTED | PARTIAL | SUPPORTED, provenance-bearing |
| Artifact identity | PARTIAL | SUPPORTED | PARTIAL | PARTIAL | SUPPORTED where artifact affects satisfiability |
| Runtime context | SUPPORTED | SUPPORTED | SUPPORTED | PARTIAL | SUPPORTED |
| Resolution policy | PARTIAL | SUPPORTED | PARTIAL | PARTIAL | SUPPORTED |
| Prerelease policy | PARTIAL | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED as policy |
| Requires-Python | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| Platform/artifact compatibility | SUPPORTED | SUPPORTED | SUPPORTED | PARTIAL | SUPPORTED semantically |
| Candidate-domain coverage | PARTIAL | PARTIAL | PARTIAL | PARTIAL | SUPPORTED only with explicit attestation |
| Evaluation domain / proof quantifier | PARTIAL | SUPPORTED | PARTIAL | PARTIAL | REQUIRED FOR MULTI-ENVIRONMENT PROOF SCOPE |
| Empty candidate observation | SUPPORTED as observation | SUPPORTED as observation | SUPPORTED as observation | SUPPORTED as observation | Never equals global absence |
| Rejection reason | PARTIAL | PARTIAL | PARTIAL | PARTIAL | NAMESPACED + typed |
| Native incompatibility object | NAMESPACED | NAMESPACED | NAMESPACED | NAMESPACED | NAMESPACED |
| Semantic constraint/literal | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED |
| Derivation/provenance | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED | SUPPORTED at semantic level |
| Native derivation tree | NAMESPACED | NAMESPACED | NAMESPACED | NAMESPACED | NAMESPACED |
| Backtracking state | PARTIAL | SUPPORTED | SUPPORTED | SUPPORTED | NAMESPACED / optional |
| Decision levels | PARTIAL | SUPPORTED | SUPPORTED | SUPPORTED | NAMESPACED / optional |
| Index authentication/query failure | PARTIAL | SUPPORTED | UNKNOWN | UNKNOWN | SUPPORTED as evidence state, details namespaced |
| Universal/forked resolution domain | PARTIAL | SUPPORTED | SUPPORTED | PARTIAL | PARTIAL until explicit evaluation domain is present |
| Yank state | PARTIAL | SUPPORTED | PARTIAL | PARTIAL | SUPPORTED as artifact/source fact |
| Cutoff/exclusion policy | PARTIAL | SUPPORTED | PARTIAL | PARTIAL | SUPPORTED as policy |
| Human-readable error text | SUPPORTED as observed text | SUPPORTED as observed text | SUPPORTED as observed text | SUPPORTED as observed text | Not proof-bearing |

## Architecture comparison

### pip/resolvelib

The public provider contract defines `identify`, `find_matches`, requirement-parent information, and known incompatibilities. Candidate enumeration is provider-owned, so returned candidates are not automatically a globally exhaustive index universe. 

### uv

uv uses a PubGrub-based resolver and explicitly models incompatibilities, forking across marker/Python domains, URL dependencies, and Python compatibility. 

### Poetry/Mixology

Poetry's solver exposes first-class incompatibility/cause concepts and detailed Python/dependency conflict derivations in failure output. These are suitable inputs to the semantic core but should not become universal native object types. 

### pipgrip/PubGrub

The prior architecture audit established pipgrip's PubGrub/Mixology-family terms, incompatibilities, derivations, and source/provider boundary. These map to the common semantic role while the native object model remains namespaced.

## Portability boundary

The experiment supports a narrow common semantic core:

`requirement` → `dependency edge` → `activation condition` → `opaque candidate` → `artifact` → `runtime context` → `resolution policy` → `candidate-domain coverage` → `semantic constraint` → `provenance` → `evidence state`

The following must remain namespaced or optional:

`native incompatibility`, `native rejection cause`, `decision level`, `backjump state`, `candidate preference heuristic`, `provider implementation object`, `index authentication machinery`, `native derivation tree`, `human-readable diagnostic`.

## Conformance conclusion

No tested field was forced into **NOT REPRESENTABLE**.

The portable-core sufficiency experiment did find one projection collision: a singleton active-environment claim and a universal claim over a larger environment domain could share the same pre-repair projection. The missing distinction is now represented by explicit `evaluation_domain` proof scope.

Several native fields do have non-identical meanings across resolver families. The safe answer is not to flatten those fields; it is to retain them under resolver namespaces and normalize only their semantic consequences.

The matrix therefore supports **partial H2d portability** with an explicit evaluation-domain boundary for multi-environment claims. It does not support universal interchange.

**H2e remains separate and unchanged: NOT TESTED.**