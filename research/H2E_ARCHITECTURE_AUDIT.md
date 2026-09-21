# H2e Public Architecture Audit

Research date: 2026-09-21
Scope: current upstream source/documentation for resolvelib, pip, Poetry, pipgrip and uv, plus local reproducible CLI sanity checks.
Status: adversarial architecture validation; maintainer feedback remains absent.

## Executive conclusion

The public-source evidence does not justify abandoning the semantic idea behind resolvewhy-trace/v0.

It does justify revising the v0 evidence contract before treating it as a cross-resolver interchange model.

The strongest conclusion is:

> A small resolver-neutral semantic core is technically defensible, but several current v0 fields are too coarse or too universal in their semantics.

The two most important repairs are:

1. Replace the single trace-wide candidate_inventory_complete boolean with per-candidate-query coverage metadata that records completeness status, basis, scope, and supporting evidence.
2. Treat resolver-specific incompatibility, rejection, decision-state, source/index, and artifact facts as namespaced evidence, not as if they had identical semantics across resolvers.

Architecture decision: REVISE resolvewhy-trace/v0.

H2e remains NOT TESTED. No maintainer feedback was used in this decision.

## Evidence discipline

The audit distinguishes:

- Observed: directly visible in current upstream source or in an executed local experiment.
- Documented: explicitly stated in project documentation/source comments.
- Inference: architectural conclusion derived from observed/documented behavior.
- Unknown: not established by the inspected public surfaces.

The existence of an internal type is not treated as proof of a stable external API.

# 1. resolvelib

## Architecture

Observed/documented:

The public AbstractProvider contract owns identify, find_matches, is_satisfied_by, get_dependencies, and selection/preference hooks.

The public BaseReporter exposes lifecycle hooks including adding_requirement(requirement, parent), resolving_conflicts(causes), rejecting_candidate(criterion, candidate), pinning(candidate), and round/finalization hooks.

RequirementInformation explicitly pairs a requirement with its parent candidate, or None for a root requirement.

The resolver result contains a successful mapping, graph, and criteria.

Architectural implication:

resolvelib deliberately separates generic resolution logic from provider knowledge. Candidate discovery and dependency metadata therefore belong partly to the provider boundary.

## Candidate completeness

The provider's find_matches is the source of candidate enumeration. It may return a callable or iterator and its implementation decides what candidate universe is exposed.

Therefore:

> candidates=[] means only that the provider returned no candidates for this query. It does not, by itself, prove that the source universe was exhaustively observed.

Status: provider-specific, semantically important, not self-certifying.

## Rejections and conflicts

The reporter hook rejecting_candidate is public. Its documented meaning is an observed rejection during backtracking, not an exhaustive record of every candidate considered or filtered upstream.

ResolutionImpossible exposes causes as RequirementInformation pairs. This is useful provenance, but it is not equivalent to a PubGrub derivation tree.

Status: directly capturable, but not a universal incompatibility language.

## Public stability

resolvelib is the strongest immediate substrate found in this audit because these provider/reporter contracts are documented public interfaces.

This supports:
resolver-specific instrumentation -> normalized semantic trace

It does not support:
all resolvers expose identical trace semantics.

Source evidence:
- https://github.com/sarugaku/resolvelib/blob/main/src/resolvelib/providers.py
- https://github.com/sarugaku/resolvelib/blob/main/src/resolvelib/reporters.py
- https://github.com/sarugaku/resolvelib/blob/main/src/resolvelib/structs.py
- https://github.com/sarugaku/resolvelib/blob/main/src/resolvelib/resolvers/criterion.py
- https://github.com/sarugaku/resolvelib/blob/main/src/resolvelib/resolvers/exceptions.py

# 2. pip

## Architecture

Current source places pip's resolver around an internal resolvelib provider, factory and reporter stack.

The internal Factory.find_candidates obtains candidates through PackageFinder.find_all_candidates.

The package-finding layer separately performs candidate evaluation/filtering for applicability and selection.

Thus candidate visibility can be affected before the logical resolver reaches its own candidate criteria.

## Candidate completeness

The relevant pipeline is approximately:

index/link discovery -> candidate construction -> applicability filtering -> resolver candidate query -> backtracking

A downstream consumer observing only the resolver-side candidate set cannot safely conclude that the set is the complete source universe.

The evidence may instead need to say:

- which sources and indexes were queried
- which discovery scope was included
- which compatibility filters were applied
- whether the source query was exhaustive
- whether filtering happened before or after resolver visibility

Status: partial availability; internal/provider/finder semantics are essential.

## pip --report

Current pip documentation states that --report is a stable versioned JSON format, but explicitly says it is not a PyPA interoperability standard.

The report describes installation/resolution output such as pip version, environment, selected install items, metadata, artifact download information, and direct/yanked/requested state.

It is not a canonical failed-resolution event stream.

Local experiment with pip 25.1.1:

- successful local dry-run with --report produced JSON with version 1 and one install item
- an intentionally contradictory local resolution failed with exit code 1 and no report file
- the failure was presented as human-readable ResolutionImpossible output

Therefore a successful installation report cannot be treated as a failure trace.

## Rejection evidence

pip has an internal reporter with rejecting_candidate, and the current source shows the resolver invoking that hook when a candidate's dependency criteria conflict.

This is useful instrumentation evidence, but the reporter is under pip internals rather than a documented independent downstream trace protocol.

## Artifact/environment boundary

pip's candidate finder/evaluator owns concerns including requires-Python filtering, wheel/platform applicability, source vs binary selection, release/pre-release policy, and related candidate filters.

These cannot safely be collapsed into a generic candidate-rejected string.

Source evidence:
- https://github.com/pypa/pip/tree/main/src/pip/_internal/resolution/resolvelib
- https://github.com/pypa/pip/blob/main/src/pip/_internal/resolution/resolvelib/provider.py
- https://github.com/pypa/pip/blob/main/src/pip/_internal/resolution/resolvelib/factory.py
- https://github.com/pypa/pip/blob/main/src/pip/_internal/resolution/resolvelib/reporter.py
- https://github.com/pypa/pip/blob/main/src/pip/_internal/index/package_finder.py
- https://pip.pypa.io/en/stable/reference/installation-report/

# 3. Poetry

## Architecture

Poetry uses a Mixology-style solver.

Current source shows VersionSolver, Incompatibility, Assignment, PartialSolution, explicit incompatibility causes, and conflict resolution that constructs new incompatibilities from earlier causes.

Incompatibility has cause classes including dependency, Python, platform, no versions, root, and derived conflict.

This is substantially richer than a simple rejection-event stream.

## Conflict semantics

Poetry's conflict model is already clause/derivation-oriented.

A derived conflict can be constructed from two prior incompatibilities, and the failure object can walk the external incompatibility derivation.

A normalized trace can represent these facts, but it must not pretend Poetry's Incompatibility has identical semantics to resolvelib's Criterion or reporter causes.

Status: strong semantic availability, internal API.

## Candidate source boundary

Poetry's provider and repository machinery determine which package versions and dependency metadata enter Mixology.

Therefore solver-visible versions are not automatically proof that the external repository universe was completely enumerated.

## Public interface

The inspected solver structures live under Poetry's implementation tree and the failure writer renders them into human-readable diagnostics.

No stable third-party machine-readable failure-trace contract was established by this audit.

Source evidence:
- https://github.com/python-poetry/poetry/blob/main/src/poetry/mixology/incompatibility.py
- https://github.com/python-poetry/poetry/blob/main/src/poetry/mixology/incompatibility_cause.py
- https://github.com/python-poetry/poetry/blob/main/src/poetry/mixology/version_solver.py
- https://github.com/python-poetry/poetry/blob/main/src/poetry/mixology/failure.py
- https://github.com/python-poetry/poetry/blob/main/src/poetry/puzzle/provider.py

# 4. pipgrip / PubGrub

## Architecture

pipgrip uses a PubGrub-based Mixology implementation.

Its PackageSource abstraction supplies versions, dependency metadata, requirement conversion, and package-specific incompatibilities.

The implementation lazily discovers versions and metadata and stores discovered package state.

Its solver constructs Incompatibility objects with causes such as root, no versions, dependency, conflict, and package-not-found.

Its failure object wraps the final incompatibility and renders a human-readable derivation.

## Candidate completeness

A versions_for(package, constraint) result is what the source supplies to the solver. There is no universal completeness declaration telling an external consumer whether those versions represent every version in the configured index, every currently discoverable version, or a bounded/filter-dependent set.

Status: semantically possible; completeness must be stated explicitly by the adapter.

## JSON output

pipgrip provides JSON output for resolved pins and dependency trees.

That is useful graph evidence but is not the same thing as a machine-readable failure derivation trace.

## Conflict semantics

PubGrub/Mixology gives pipgrip a natural derivation graph. A common trace should therefore preserve:

- terms
- derivation links
- cause kind
- resolver namespace

rather than flattening all incompatibilities into one universal meaning.

Source evidence:
- https://github.com/ddelange/pipgrip/blob/master/src/pipgrip/package_source.py
- https://github.com/ddelange/pipgrip/blob/master/src/pipgrip/libs/mixology/incompatibility.py
- https://github.com/ddelange/pipgrip/blob/master/src/pipgrip/libs/mixology/incompatibility_cause.py
- https://github.com/ddelange/pipgrip/blob/master/src/pipgrip/libs/mixology/version_solver.py
- https://github.com/ddelange/pipgrip/blob/master/src/pipgrip/libs/mixology/failure.py

# 5. uv

## Architecture

uv uses PubGrub and maintains a structured derivation/error model internally.

Current source shows ErrorTree, NoSolutionError, tracked incompatibilities, candidate-selection machinery, resolver/provider traits, and explicit environment/index structures.

Current uv resolver documentation describes deriving incompatibilities and constructing an understandable error trace from them.

## Important evidence

Current source re-exports ErrorTree and NoSolutionError.

NoSolutionError stores structured information including:

- the derivation tree
- included versions
- available versions
- available indexes
- incomplete package information
- unavailable package information
- environment
- Python requirement
- tags
- resolver/index state

However, most of these rich fields remain private inside NoSolutionError.

This is materially stronger structured exposure than a pure text-only CLI interface, but it is still not a generic cross-resolver trace protocol.

## Candidate completeness

uv makes the case for structured coverage metadata especially clear.

The current error model distinguishes at least available versions, included versions, incomplete package metadata, unavailable packages and index information.

These distinctions show that:
some versions existed
and
the evidence establishes the complete usable candidate domain
are different claims.

The trace should preserve that distinction.

## Resolver policy

uv resolution depends on policy and environment concepts including Python requirement, platform tags, prerelease policy, index behavior, newer-version cutoffs, and universal/forked resolution context.

These are resolution-policy facts, not merely machine environment facts.

## Public vs internal boundary

The existence of public ErrorTree and NoSolutionError is important evidence for feasibility.

The rich construction, candidate selector state, derivation processing, and much of the evidence payload remain implementation-specific.

Status: rich structured internal evidence with some public access; still not a portable external trace contract.

Source evidence:
- https://docs.astral.sh/uv/reference/internals/resolver/
- https://github.com/astral-sh/uv/blob/main/crates/uv-resolver/src/error.rs
- https://github.com/astral-sh/uv/blob/main/crates/uv-resolver/src/lib.rs
- https://github.com/astral-sh/uv/blob/main/crates/uv-resolver/src/candidate_selector.rs
- https://github.com/astral-sh/uv/blob/main/crates/uv-resolver/src/resolver/mod.rs
- https://github.com/astral-sh/uv/blob/main/crates/uv-resolver/src/resolver/derivation.rs
- https://github.com/astral-sh/uv/blob/main/crates/uv-resolver/src/pubgrub/report.rs

# 6. Field-by-field architectural comparison

| Field | resolvelib / pip | Poetry | pipgrip / PubGrub | uv | Architecture status |
|---|---|---|---|---|---|
| Candidate identity | Provider-defined | Package/Dependency objects | Package + version/source | PubGrub package/candidate | SUPPORTED SEMANTICALLY; representation provider-specific |
| Candidate inventory / completeness | Provider-owned | Provider/repository-owned | PackageSource-owned | Rich internal available/included/incomplete distinction | PARTIALLY AVAILABLE; explicit coverage required |
| Dependency edges | Public provider hook | Provider/package metadata | dependencies_for | Resolver dependency provider | SUPPORTED SEMANTICALLY |
| Requirement representation | Generic requirement type + parent info | Dependency/term | Dependency/constraint | Requirement/term | SUPPORTED; preserve raw + normalized forms |
| Environment / policy | Provider/application-specific | Provider/solver/environment | Source + package metadata | Rich resolver environment/policy | SUPPORTED; split runtime context from policy |
| Candidate rejection | Public resolvelib hook; pip internal | Internal causes | Internal causes | Internal candidate/incompatibility machinery | PARTIALLY AVAILABLE; reason kind + source layer required |
| Incompatibility/conflict | Causes/criteria | First-class incompatibility | First-class incompatibility | PubGrub derivation tree | SUPPORTED SEMANTICALLY; namespace required |
| Provenance | Requirement-parent/cause relations | Cause graph | ConflictCause graph | ErrorTree | SUPPORTED SEMANTICALLY; derivation differs |
| Resolver state / decision context | Partially available | Internal partial solution/decision level | Internal partial solution | Internal resolver state | INTERNAL / OPTIONAL |
| Source/index information | Finder/provider | Repository pool/provider | PackageSource | In-memory index/index locations | PROVIDER-SPECIFIC |
| Artifact selection | Important | Source/direct-origin related | Source-driven | Rich distribution/candidate selection | OPTIONAL PROVIDER-SPECIFIC |

# 7. Adversarial findings

## Finding A — trace-wide candidate completeness is too coarse

A single boolean cannot encode different candidate queries having different source scope, index scope, filters, environments, discovery guarantees or boundedness.

Impact: high.

Repair: make coverage a per-query/per-domain object.

## Finding B — rejected candidate is not a universal semantic

A rejection can mean resolver backtracking, dependency conflict, no versions, Python mismatch, platform mismatch, source/index exclusion, artifact incompatibility or policy exclusion.

Impact: high.

Repair: add reason_kind and source_layer; do not infer universal semantics.

## Finding C — incompatibility is resolver-family-specific

Poetry, pipgrip and uv expose clause/derivation-oriented structures. resolvelib exposes causes/criteria rather than the same derivation object.

Impact: high for portability.

Repair: keep normalized literals and provenance generic, but preserve raw incompatibility evidence under a resolver namespace.

## Finding D — candidate identity cannot be only package/version

URL, VCS, local path, alternate source/index and artifact identity can affect satisfiability.

Impact: high.

Repair: opaque adapter-defined candidate identity is primary; package/version is a semantic projection.

## Finding E — runtime environment and resolver policy are different evidence domains

A machine environment snapshot does not capture all resolution semantics.

Impact: medium/high.

Repair: split runtime_context and resolution_policy.

## Finding F — rejection events are causal evidence, not proof of exhaustion

A backtracking event shows what the resolver rejected at that point. It does not prove that the source/index universe was exhausted.

Impact: high.

Repair: keep rejection evidence non-exhaustive unless a separate coverage declaration establishes exhaustiveness.

## Finding G — uv shows structured errors can exist without being portable traces

Public ErrorTree/NoSolutionError materially strengthens the feasibility case, but much of the evidence remains uv/PubGrub-specific.

Impact: medium.

Repair: normalize semantics, not implementation objects.

# 8. Reproducible local sanity checks

Sandbox runtime:

- Python 3.13.5
- pip 25.1.1
- uv 0.10.0
- Poetry not installed
- pipgrip not installed

## pip experiment

Two minimal local wheels, foo==1.0 and foo==2.0, were supplied through a local find-links directory.

Requirements requested both exact versions.

Observed:

- exit code 1
- human-readable ResolutionImpossible
- no report file generated by the failed --report invocation

A separate satisfiable local foo==1.0 dry-run produced a report with version 1, pip_version, environment, and one install item.

This reinforces that the stable report format is not itself a failed-resolution trace.

## uv experiment

A local project with foo==1.0 and foo==2.0 was resolved using:

uv lock --offline --find-links <local-directory>

Observed:

- exit code 1
- human-readable No solution found diagnostic
- diagnostic identified the contradictory root requirements
- no machine-readable failure trace was emitted by the tested CLI invocation

This reinforces the distinction between uv's structured internal ErrorTree and its CLI failure output.

# 9. Exact semantic revision proposed

## 9.1 Candidate coverage

Replace the single global boolean with per-query coverage metadata.

Example shape:

{
  "id": "query:x",
  "identifier": "x",
  "requirements": ["root:a->x<2", "root:b->x>=2"],
  "coverage": {
    "status": "complete",
    "basis": "authoritative_finite_domain",
    "scope": {
      "sources": ["local-fixture"],
      "indexes": [],
      "environment_ref": "env:1",
      "filters": []
    },
    "evidence_refs": ["obs:versions:x"]
  }
}

Recommended status values:
- complete
- partial
- unknown

Recommended basis values:
- authoritative_finite_domain
- exhaustive_provider_query
- resolver_exhaustion
- bounded
- observed

Only the first three can support an exhaustive candidate-domain claim.

## 9.2 Candidate identity

Use:

candidate.id = opaque adapter-defined identity
candidate.package = normalized package identity
candidate.version = semantic version when applicable
candidate.identity = source/VCS/path/artifact discriminator

Do not collapse identities that differ in satisfiability-relevant source semantics.

## 9.3 Rejection evidence

Add:

reason_kind
source_layer

Suggested source layers:
- resolver
- provider
- index
- source
- artifact
- policy
- environment

## 9.4 Incompatibility evidence

Add:

semantics
resolver_namespace
derivation

Examples of semantics:
- raw_resolver_clause
- resolver_cause

The normalized model may store semantic literals and provenance, while raw resolver objects remain namespaced.

## 9.5 Environment

Split:

runtime_context
resolution_policy

This prevents prerelease, source-selection, index and universal-resolution semantics from being mistaken for machine facts.

## 9.6 Provenance

Require:

claim -> premises -> derivation rule/source namespace

A free-form explanation string is never sufficient to establish a proof.

# 10. Decision

KEEP v0 unchanged: rejected. The current completeness and conflict semantics are too coarse.

ABANDON v0: rejected. The same semantic concepts recur across all four architecture families, and real structured resolver evidence clearly exists.

NARROW only: insufficient by itself. The resolver-neutral core should be smaller, but it also needs stronger typing and explicit coverage semantics.

REVISE v0: selected.

The revised architecture should be:

resolver/provider-specific evidence
    ->
typed + namespaced observations
    ->
explicit per-domain coverage
    ->
small resolver-neutral semantic core
    ->
independent consistency / MUS verification

The resolver-neutral core should be limited to:

- requirement
- opaque candidate identity
- dependency edge
- runtime context
- resolution policy
- candidate-domain coverage
- semantic constraint/literal
- provenance
- explicit evidence state

Resolver-specific objects such as derivation trees, backtracking state, rejection causes, index details and artifact-selection diagnostics should remain attached as namespaced evidence.

# 11. H2 status after this audit

This architecture audit does not constitute maintainer validation.

- H2a: supported narrowly through resolvelib structured provider/reporter instrumentation. Other resolvers also contain rich structured evidence internally, but this does not establish a stable common public API.
- H2b: partially supported. Normalization works in controlled traces, but candidate coverage, identity, policy and conflict semantics require the revisions above.
- H2c: supported in the controlled traces already benchmarked.
- H2d: UNPROVEN. Public/stable cross-ecosystem interchange has not been established.
- H2e: NOT TESTED. There are still 0 substantive maintainer responses.

The architecture evidence strengthens the technical plausibility of a resolver-neutral semantic layer while simultaneously weakening the claim that the current v0 schema is ready as a portable wire format.

# 12. Final research conclusion

The strongest defensible claim at this stage is:

> Real dependency resolvers expose enough structured information, either publicly or internally, to make a resolver-neutral semantic evidence layer technically plausible. However, the information is divided across resolver, provider, source/index, artifact and policy layers, so a correct interchange model must encode coverage and provenance explicitly and preserve resolver-specific semantics rather than flatten them.

Final architecture decision: REVISE resolvewhy-trace/v0.

H2e remains NOT TESTED.

No production architecture should begin solely from this audit; the next research gate is still substantive external maintainer feedback or another falsification experiment targeting the revised coverage/provenance contract.
