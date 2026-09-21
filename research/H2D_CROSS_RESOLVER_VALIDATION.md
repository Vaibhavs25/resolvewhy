# H2d Cross-Resolver Validation

**Date:** 2026-09-21  
**Hypothesis:** Can the revised `resolvewhy-trace` semantic contract provide a resolver-neutral representation of satisfiability-relevant dependency-resolution evidence across different resolver architectures without unsafe normalization?

## Executive decision

**B. H2d PARTIALLY SUPPORTED — PORTABILITY BOUNDARY MUST BE NARROWED**

The tested pip/resolvelib and uv evidence can map into the same small semantic concepts for the tested cases, but the experiment does **not** justify treating every native resolver field as portable.

The common layer is defensible only when it is semantic and proof-oriented:
requirement, dependency edge, activation condition, opaque candidate identity, artifact identity where relevant, runtime context, resolution policy, candidate-domain coverage, semantic constraint/literal, provenance, and evidence state.

Native derivation graphs, provider internals, index behavior, solver decision state, and detailed artifact selection remain resolver/provider-specific and must stay namespaced or optional.

This is a portability result for the tested pair and cases, not ecosystem-wide portability.

## 1. Experimental design

Two adapter views were treated independently:

- **pip/resolvelib adapter:** starts from the public resolvelib provider/reporter concepts and pip's provider/finder architecture.
- **uv adapter:** starts from uv's PubGrub resolver/error architecture, including its structured derivation/error concepts and explicit environment/index/policy behavior.

The adapters are intentionally not designed to emit identical native events. They are judged only on whether the same satisfiability-relevant fact survives normalization.

Poetry/Mixology and pipgrip/PubGrub were included through source/issue-level mappings rather than executable adapters because their executables were not available in the sandbox.

No production adapter framework was built.

## 2. Resolver evidence basis

### pip / resolvelib

The public `AbstractProvider` contract defines `identify`, `find_matches`, dependency access, and preference/selection hooks. `find_matches` receives requirements and known incompatibilities and returns candidates; its contract explicitly covers VCS/local/archive requirements separately from named requirements. `RequirementInformation` preserves the requirement-parent relation. citeturn246071view0turn438838view3

This makes candidate discovery and parent/dependency provenance directly observable at the provider boundary, but does not make the provider's returned candidate set automatically globally exhaustive.

### uv

uv's documented resolver is PubGrub-based. Its internal model tracks incompatibilities and derives error traces; it explicitly models forking across marker/Python domains, URL dependencies, and Python compatibility. citeturn755747search0

Current uv issues also expose real cases where authentication failures, marker activation, yanked artifacts, and source/policy behavior materially affect the resolver outcome. citeturn768883search1turn768883search3turn553358search0

## 3. Shared semantic test suite

The common suite was evaluated against the previous real-world corpus plus the executable reductions.

| Test | pip/resolvelib mapping | uv mapping | Result |
|---|---|---|---|
| Simple satisfiable resolution | selected candidate + dependency facts | selected package/version | SUPPORTED |
| Direct conflict | conflicting requirements/criteria | PubGrub incompatibility | SUPPORTED |
| Transitive UNSAT | parent-linked requirements + candidate facts | derivation chain + incompatibilities | SUPPORTED |
| Incomplete discovery | observed provider candidates | available/incomplete/unavailable distinctions | SUPPORTED |
| Multiple indexes | finder/provider source scope | index/source scope | SUPPORTED |
| Platform filtering | candidate/artifact applicability | wheel/tag applicability | SUPPORTED |
| Requires-Python | candidate metadata + environment | Python incompatibility | SUPPORTED |
| Prerelease policy | pip policy flag | uv prerelease mode | SUPPORTED |
| Environment markers | requirement marker / activation condition | marker-bearing terms/forks | SUPPORTED |
| Direct URL | link/source identity | URL dependency | SUPPORTED |
| VCS candidate | direct/VCS requirement, URL/commit | URL/VCS candidate identity | SUPPORTED |
| Artifact rejection | wheel/source applicability evidence | candidate/artifact filtering | SUPPORTED |
| Same name/version, different source | source-qualified identity | source-qualified candidate state | SUPPORTED |
| Backtracking | reporter/backtrack causes | PubGrub derivation/backtracking | SUPPORTED semantically; native form differs |
| Native incompatibility | resolvelib cause/criterion | PubGrub clause/derivation | NAMESPACED |
| Authentication failure | source/index failure evidence | index query failure | SUPPORTED as incomplete evidence |
| Bounded candidate domain | provider-observed subset | partial/incomplete source evidence | SUPPORTED |
| Universal/forked resolution | requires explicit declared domain; not native in same form | explicit fork domain | SUPPORTED, domain-scoped |

## 4. Cross-adapter semantic equivalence

### 4.1 Requirements and dependency edges

Both architectures expose a parent-to-requirement relation, although the native mechanisms differ.

Common normalization:
`parent candidate -> requirement -> activation condition -> provenance`

The semantic meaning survives without carrying the native event type.

### 4.2 Candidate identity

The test cases demonstrated that package + version alone is insufficient. VCS URLs, direct URLs, source/index origin and artifact variants can affect satisfiability.

The common rule that survived:
- opaque trace-local candidate ID;
- package/version as projections;
- source identity preserved when relevant;
- URL/VCS/path identity preserved when relevant;
- artifact identity separate from candidate.

No adapter is permitted to collapse source-distinct candidates merely because their displayed package/version matches.

### 4.3 Candidate-domain coverage

This is the most important portability boundary.

pip/resolvelib can expose a provider-returned candidate set and provider-side query scope. uv can expose available/incomplete/unavailable and index context internally. Neither architecture justifies the universal statement “all candidates everywhere”.

Therefore the common semantic claim is:
`coverage = complete | partial | unknown`
over an explicit declared domain.

A resolver's local statement that it exhausted its current candidate set is not sufficient unless the provider/index domain is also attested as exhaustive.

### 4.4 Runtime context vs policy

The prerelease experiments are a direct portability test.

With the same available candidate:
- pip default rejects the prerelease;
- pip `--pre` accepts it;
- uv 0.10.0 default accepts it;
- uv `--prerelease=disallow` rejects it.

The candidate identity remains unchanged. The policy changes.

Therefore prerelease mode belongs in `resolution_policy`, not candidate identity or runtime facts.

The same separation applies to yanked handling and `exclude-newer`. The uv `exclude-newer` case demonstrates that an upload-time cutoff is independent of a prerelease hint. citeturn768883search0turn768883search4

### 4.5 Activation conditions

The uv `pywin32; sys_platform == "win32"` issue is the critical negative test. The native failure can be misleading for Linux, so an adapter that drops the activation marker would create a false universal clause. citeturn768883search1

The shared layer therefore requires activation conditions to remain explicit. Marker erasure is classified as unsafe normalization.

### 4.6 Artifact vs candidate

Platform wheel and per-file yank cases show that artifact-level state can differ for one package/version.

uv's current issue on a yanked wheel explicitly notes that the wheel URL/hash can remain while yank state is not represented in the persisted lock structure. citeturn246769search10

The common layer therefore keeps:
`candidate -> artifact -> artifact status/compatibility`

rather than folding artifact state into candidate identity.

### 4.7 Provenance

Both families preserve causal structure, but not with identical native types.

pip/resolvelib uses requirement-parent relationships, criteria and rejection/backtrack hooks. uv uses PubGrub incompatibility/derivation structures.

Common normalization:
`claim -> premises -> derivation rule -> source namespace`

Native derivation stays namespaced.

A human-readable message is never sufficient proof provenance.

## 5. Policy-difference experiment

### Same candidate universe, different resolver policy

Candidate universe:
`foo==1.0rc1`

Requirement:
`foo<2`

Observed:
- pip default: failure
- pip `--pre`: success
- uv default: success
- uv `--prerelease=disallow`: failure

The normalized traces can be made equivalent at the candidate/requirement level while differing in `resolution_policy`.

This demonstrates that resolver-neutrality does not require identical resolver outcomes.

### Yank policy

uv can refuse a yanked dependency where pip only warns and installs it. citeturn553358search0

The common representation is therefore:
- artifact/source fact: yanked
- policy fact: yanked artifacts allowed/disallowed
- resolver result: observed outcome

No universal UNSAT clause is created.

### Source selection

Multiple-index cases show that source scope changes candidate visibility. uv's current index documentation also describes explicit behavior around authentication and index searching. citeturn768883search8

The source query and selected source remain provenance-bearing evidence.

### Universal/forked resolution

uv explicitly forks resolution across marker/Python domains, whereas resolvelib's core abstraction is not itself a universal multi-environment fork model. The common layer can still carry a declared resolution domain and activation condition without pretending the native mechanisms are identical. citeturn755747search0

## 6. Candidate coverage conformance

The following mutation tests were applied conceptually to both adapter models:

| Mutation | Required common result |
|---|---|
| Remove one source from a multi-index domain | `insufficient_evidence` |
| Mark observed provider output as complete without authority | proof forbidden |
| Remove completeness attestation | proof forbidden |
| Keep resolver exhaustion but remove provider/domain scope | proof forbidden |
| Replace 401/403 with “no candidate” | proof forbidden |
| Remove artifact applicability data | artifact proof forbidden |

All preserve the same rule:
**absence of evidence is not evidence of absence.**

uv's real 401/403 case is particularly useful because the issue shows a concrete distinction between index-query failure and package absence. citeturn768883search3

## 7. Unsafe normalization attack

The naive uv adapter was defined as:

1. drop `sys_platform == "win32"`;
2. copy the native `pywin32` conflict;
3. emit a universal incompatibility;
4. pass it to the proof layer.

That normalization is unsound on Linux.

The correct adapter retains:
- the dependency requirement;
- activation marker;
- Linux runtime context;
- source/index evidence;
- resolver-native incompatibility under the uv namespace.

The common proof layer therefore refuses to infer UNSAT from the native message alone.

**Result: unsafe normalization detected and rejected.**

This is an important portability result: a common schema by itself does not guarantee semantic portability; the adapter boundary remains part of the trust model.

## 8. Poetry / Mixology source mapping

Poetry's public issue corpus demonstrates first-class incompatibility derivations and Python constraints. Its Mixology failure messages distinguish causes such as package dependencies and Python incompatibilities. citeturn703071search2turn703071search5

The safe mapping is:
- requirement/term -> portable semantic constraint;
- incompatibility cause -> namespaced resolver evidence;
- derived incompatibility -> provenance-bearing claim;
- Python constraint -> runtime-context/policy semantic constraint.

The native `Incompatibility` object itself should not be promoted to a universal interchange type.

## 9. pipgrip / PubGrub source mapping

The prior architecture audit established pipgrip's PubGrub/Mixology family semantics. These map naturally to:
- package/term;
- candidate/version;
- incompatibility;
- cause/derivation;
- source/query scope.

Again, the derivation graph is semantically portable only at the level of logical premises and provenance; its object model remains namespaced.

## 10. Falsification criteria assessment

| Criterion | Finding |
|---|---|
| Required semantic concept not representable | Not found in tested set |
| Supposedly common field has incompatible meanings | Yes, for native incompatibility/rejection objects; solved by namespacing |
| Common proof layer requires resolver-specific assumptions | No, provided proof uses normalized literals + provenance only |
| Candidate identity cannot be normalized safely | No; opaque IDs + source/artifact separation suffice |
| Candidate completeness ambiguous | Yes if adapter omits domain authority; revised coverage model prevents this |
| Provenance lost during normalization | Not in tested mappings |
| Policy differences cannot be preserved | Not found |
| Namespaced conflict semantics misleading | Avoided by not treating namespaces as universal semantics |
| Adapter must lie about evidence | No; partial/unknown evidence is representable |
| Fundamentally different universal-field meaning | Native rejection/incompatibility only; kept outside portable proof core |

## 11. What is actually portable

The tested pair supports the following as the portable semantic core:

1. requirement
2. dependency edge
3. activation condition
4. opaque candidate identity
5. artifact identity where needed
6. runtime context
7. resolution policy
8. candidate-domain coverage
9. semantic constraint/literal
10. provenance
11. evidence state

These are statements about semantic role, not a claim that every resolver exposes them through a stable API.

## 12. What is not portable and should remain namespaced

- native incompatibility/derivation object shapes
- resolver decision levels
- backjump implementation state
- candidate preference heuristics
- provider internals
- index authentication/search machinery
- detailed artifact-selection pipelines
- cache state
- resolver-specific virtual-package representations
- exact human-readable error wording

## 13. Limitations

The most important limitations are:

- Only pip 25.1.1 and uv 0.10.0 were executable in the sandbox.
- Poetry and pipgrip were source/issue validated rather than executed.
- The adapters were minimal semantic mappings, not production integrations.
- Public issue reports establish realistic semantic patterns but are not equivalent to complete native traces.
- Universal multi-environment resolution is richer in uv than in the resolvelib core abstraction.
- The experiment validates semantic portability for tested cases, not API stability over future versions.

## 14. Final decision

**B. H2d PARTIALLY SUPPORTED — PORTABILITY BOUNDARY MUST BE NARROWED**

The experiment falsified the stronger interpretation of resolver-neutrality: it is not safe to make native rejection, incompatibility, or decision-state structures universal.

The narrower interpretation survives:

> Different resolver architectures can map tested satisfiability-relevant facts into a common semantic proof layer, provided that candidate coverage, activation conditions, identity, artifact state, runtime context, policy, evidence state, and provenance are explicit, while native resolver semantics remain namespaced.

This supports H2d for the tested pip/resolvelib–uv pair and cases, but it does not establish general cross-ecosystem portability.

H2e is unchanged and remains NOT TESTED.
