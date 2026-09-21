# Portable Core Sufficiency

**Date:** 2026-09-21

## 1. Hypothesis

Let `N` be a native resolver evidence state and `P(N)` its projection onto the portable semantic proof core.

The target property is:

> For the tested semantic fragment, if `P(N1) == P(N2)`, then the truth of the stated proof question and its proof-eligibility status must be the same for `N1` and `N2`.

A violation is a projection collision.

## 2. Tested fragment

The search covered:
- version constraints and dependency conjunctions;
- parent-linked dependency edges;
- activation conditions / environment markers;
- opaque candidate identity;
- candidate/artifact separation;
- source-aware candidates;
- runtime-sensitive `Requires-Python`;
- prerelease and yank policy;
- direct URL and VCS identity;
- bounded and partial candidate domains;
- authentication/source-query failure;
- resolver-native derivation and backtracking state;
- universal/forked resolution over a finite environment set.

The last item was deliberately treated as a quantified proof problem rather than merely another runtime marker.

## 3. Portable projection definition

The current projection retained:
- requirements;
- dependency edges and activation conditions;
- candidate and artifact semantics;
- runtime context;
- resolution policy;
- candidate-domain coverage and attestation;
- semantic constraints/literals;
- provenance and evidence state.

Native resolver objects were discarded from the proof layer.

The initial projection did **not** contain a distinct evaluation/proof domain.

## 4. Independent adapter fixtures

Two minimal adapter views were implemented independently for the search:

### pip/resolvelib-shaped adapter

Native fixture concepts used:
- root requirements;
- `RequirementInformation`-style parent/requirement relations;
- provider-returned candidates;
- runtime and policy;
- candidate query coverage;
- provenance.

resolvelib's public provider contract explicitly separates candidate identification, candidate enumeration through `find_matches`, satisfaction checks, and dependency retrieval; parent-linked requirement information is part of the resolver's public structured model. 

### uv-shaped adapter

Native fixture concepts used:
- root terms;
- fork terms;
- included versions;
- environment;
- resolver policy;
- available-version scope;
- derivation references.

uv's resolver documentation describes PubGrub-style incompatibility derivation and explicit forking over Python/marker domains. 

The adapters were judged on semantic role, not native object equality.

## 5. Automated projection-collision search

A finite search generated **64 native fixture worlds** spanning the pip-style and uv-style evidence shapes while varying native derivation shape, decision state, provider observations, and the declared environment domain.

### Before repair

The search found **2 raw collisions**, representing one unique semantic collision family:

- World A: declared evaluation domain = `{Python 3.13/Linux}`.
- World B: declared evaluation domain = `{Python 3.13/Linux, Python 3.9/Linux}`.
- Both worlds had identical current portable projections.
- Both had the same active runtime context: Python 3.13/Linux.
- Both used the same candidate `numba==0.61` with `Requires-Python >=3.10`.
- Both carried the same dependency and coverage facts.
- World A was SAT over its declared domain.
- World B was UNSAT over its declared domain because the candidate cannot satisfy the Python 3.9 branch.

Therefore:

`portable(N_A) == portable(N_B)`

but

`proof(N_A) = SAT`
`proof(N_B) = UNSAT`.

This is a genuine projection collision.

## 6. Why the collision occurred

`runtime_context` answers which environment produced a particular observation.

`resolution_policy` can say that the resolver is operating in a universal/forked mode.

Neither field, by itself, identifies the set of environments over which the proof claim is quantified.

That missing semantic fact can change the truth of the proof query while every other current portable field remains identical.

This is not merely explanation-quality information. It changes the mathematical problem being proved.

## 7. Smallest repair

Introduce one additional portable semantic concept:

`evaluation_domain`

It records the environment set or explicit partition over which the satisfiability claim is asserted.

The repaired contract distinguishes:

- `runtime_context`: local observation environment;
- `resolution_policy`: solver behavior/policy;
- `evaluation_domain`: proof quantification scope;
- `candidate-domain coverage`: exhaustiveness of candidate discovery inside the relevant query/domain.

The schema now requires the evaluation domain for universal/forked claims and permits a singleton domain for single-environment claims.

## 8. Re-run after repair

The repaired projection includes the explicit evaluation domain.

Results:
- current-core collision family is separated;
- repaired projection: **0 projection collisions** in the finite search;
- native derivation/decision-state deletion still leaves semantic truth unchanged in the tested fragment.

This is evidence that the repair removes the discovered collision; it is not proof of universal completeness.

## 9. Information-deletion experiment

For the tested UNSAT world, the following native fields were removed one at a time:

| Deleted native information | Correctness preserved? | Classification |
|---|---|---|
| Native derivation tree | Yes | SAFE TO DISCARD for correctness; useful for explanation provenance/detail |
| Decision level | Yes | SAFE TO DISCARD |
| Candidate ordering | Yes | SAFE TO DISCARD |
| Provider implementation note | Yes | SAFE TO DISCARD once required semantic facts are retained |
| Human-readable diagnostic | Yes | SAFE TO DISCARD for proof |
| Resolver-specific rejection shape | Yes | SAFE TO DISCARD when its semantic premise is already normalized |
| Resolver-specific incompatibility object | Yes | SAFE TO DISCARD from proof computation; retain as namespaced audit evidence |

The qualification is important: a native field is safe to discard only when its satisfiability-relevant semantic consequences have already been represented or the trace is explicitly downgraded to `insufficient_evidence`.

## 10. Targeted collision families

| Family | Current projection collision? | Reason |
|---|---|---|
| Candidate completeness | No | Coverage status/attestation is portable |
| Source/index scope | No | Source scope is portable proof-scope evidence |
| Authentication failure | No | Evidence state and source-query provenance remain distinct |
| `Requires-Python` | No | Candidate metadata + runtime context survive |
| Activation markers | No | Activation condition is explicit |
| Prerelease policy | No | Policy survives separately from candidate identity |
| Yank policy | No | Artifact/source fact and policy survive |
| Artifact identity | No | Artifact remains distinct from candidate |
| Candidate identity | No | Opaque/source-aware identity survives |
| Direct URL/VCS identity | No | Source identity and provenance survive |
| Universal/forked resolution | **Yes** | Evaluation domain was absent |
| Resolver-native incompatibility | No truth collision in tested fragment | Native shape changes, but semantic contradiction does not |

## 11. What this falsifies

The experiment falsifies the stronger claim:

> The current eleven-field portable core is sufficient for every tested proof question, including quantified universal resolution.

That claim is false because the universal-resolution domain can be semantically decisive while hidden outside the projection.

It does **not** falsify the narrower claim that a small semantic core can support independent reasoning after the missing proof-scope concept is added.

## 12. Proven fragment after repair

The defensible fragment is:

`version constraints + dependency conjunctions + markers + finite candidate domains + candidate/artifact separation + source-aware identity + Requires-Python + prerelease/yank policy + direct/VCS identity + bounded/partial evidence + finite multi-environment evaluation domains`.

For this fragment, the repaired projection search found no projection collision.

## 13. Outside the proven fragment

Not established by this experiment:
- arbitrary marker-language completeness;
- all package-manager-specific virtual packages;
- arbitrary dynamic metadata generation semantics;
- all artifact/build-system semantics;
- infinite or symbolic environment domains without an explicit semantic encoding;
- future resolver versions or unseen resolver architectures;
- ecosystem-wide wire compatibility.

## 14. Final decision

**B. PARTIALLY SUFFICIENT — NARROW OR REVISE**

The current portable core was found to be incomplete for quantified universal/forked proof claims.

The smallest repair is explicit `evaluation_domain` proof scope.

The repaired core survives the finite projection-collision search and the native-information deletion tests.

Therefore the research claim should be narrowed to:

> The portable semantic core is sufficient for the tested finite semantic fragment when proof scope is explicit, including an explicit evaluation domain for multi-environment claims; native resolver derivations and decision state are not required for correctness in that fragment.

H2d remains partial rather than fully supported. H2e is unaffected and remains NOT TESTED.
## Final semantic-boundary update — 2026-09-21

The portable-core sufficiency result is now explicitly bounded by the final semantic-boundary audit.

### Bounded sufficiency statement

Within the tested finite semantic fragment, the portable core preserves enough satisfiability-relevant information for independent verification when the trace explicitly records requirements, parent-linked dependency edges, activation conditions, opaque/source-aware candidate identity, artifact identity when feasibility is artifact-dependent, runtime context, finite evaluation domains, resolution policy, scoped candidate-domain coverage with completeness attestation, semantic literals, provenance/evidence state, and proof-claim quantifier/domain binding.

The experiments establish this only for the finite and explicitly serialized fragment exercised so far. They do not establish complete semantics for dynamic build backends, arbitrary source-tree metadata generation, full hash/reproducibility behavior, complete lockfile semantics, implicit virtual/provided packages, symbolic or infinite environment domains, every PEP 508 interaction, or future resolver-specific semantics.

### Boundary-collision interpretation

The prior genuine projection collision was repaired by explicit evaluation_domain. After that repair and the subsequent trace-only/projection tests, no additional collision was identified inside the declared finite fragment. The remaining near-boundary cases are treated as outside the current evidence boundary rather than silently generalized into the core.

### Decision

**BOUNDARY SURVIVES — NO NEW SEMANTIC DEFECT.**

H2d remains PARTIALLY SUPPORTED and bounded to the tested semantic portability fragment.
