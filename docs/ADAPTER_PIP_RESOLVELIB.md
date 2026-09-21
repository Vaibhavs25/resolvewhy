# pip / resolvelib Adapter

**Phase:** 3A — first production resolver adapter  
**Status:** implemented capture + normalization foundation; this is not a verifier and does not claim general pip semantic coverage.

## 1. Purpose

The adapter converts structured evidence observed at the resolvelib provider/reporter boundary into the production semantic model and then into `resolvewhy-trace/1.0`.

```
resolvelib provider/reporter
          |
          v
recorded native events
          |
          v
pip/resolvelib semantic normalization
          |
          v
resolvewhy.model.Trace
          |
          v
resolvewhy-trace/1.0
```

The adapter never treats a resolver diagnostic string as proof.

## 2. Integration surface

The capture layer wraps the public resolvelib concepts:

- provider `identify`;
- provider `get_preference`;
- provider `narrow_requirement_selection`, when available;
- provider `find_matches`;
- provider `is_satisfied_by`;
- provider `get_dependencies`;
- reporter `starting`;
- reporter round hooks;
- reporter `adding_requirement(requirement, parent)`;
- reporter `resolving_conflicts(causes)`;
- reporter `rejecting_candidate(criterion, candidate)`;
- reporter `pinning(candidate)`.

These are the primary structured capture points. Resolver/provider implementations can still contain richer internal information, but the adapter does not flatten that internal state into portable semantics automatically.

## 3. pip boundary

pip itself uses a pip-specific provider/factory/reporter stack around a vendored resolvelib implementation. The adapter therefore supports a resolver-module injection boundary:

```python
PipResolvelibAdapter.from_resolvelib_module(
    resolver_module=some_resolvelib_module,
    provider=provider,
    context=context,
)
```

This avoids importing pip's private resolver implementation into the production semantic core.

A caller that intentionally supplies pip's private provider/factory objects may use the same capture layer, but compatibility with those private APIs is explicitly not a promise of this package. The adapter is designed around resolver evidence that can be justified from the structured integration surface.

## 4. Capture architecture

`RecordingProvider` and `RecordingReporter` are transparent wrappers.

They record an ordered in-memory `CaptureBuffer` containing:

- requirement additions and parent relationships;
- candidate matches;
- dependency observations;
- candidate satisfaction checks;
- pins;
- rejected candidates and their requirement information;
- conflict causes;
- resolver round lifecycle events;
- final native outcome.

The buffer retains native objects only inside the adapter boundary. Normalization converts them into production model objects.

## 5. Normalization architecture

Normalization is performed by `normalize_capture()` with a `DefaultPipSemantics` accessor.

The accessor deliberately exposes a limited semantic surface:

- package/name;
- version constraints supported by the validated six comparison operators;
- raw requirement text;
- packaging marker expressions where the supplied object exposes its structured marker AST;
- explicit candidate lookup when exposed;
- candidate source/origin facts where observable;
- artifact origin/hash/yank observations where observable;
- candidate Requires-Python metadata where observable.

Unsupported or unreadable fields are recorded as incomplete evidence rather than silently inferred.

## 6. Requirement handling

Requirements preserve:

- raw representation;
- normalized version constraints;
- parent-candidate relationship;
- activation condition;
- evidence references.

A compound pip specifier such as `>=1,<3` is represented as multiple semantic literals inside one `SemanticConstraint`. The convenience `Requirement.constraint` field is only populated when exactly one normalized comparison is available; the semantic-constraint collection remains the formal normalized representation.

Constraint order is not a semantic commitment: the conjunction `>=1,<3` is equivalent to `<3,>=1`. Phase 3A tests therefore compare the normalized compound constraint set order-independently. The adapter does not claim preservation of declaration order.

Unsupported operators/wildcards do not become false facts. They make the relevant evidence incomplete.

## 7. Activation and markers

Activation is preserved as a structured `MarkerExpression` rather than flattened into a Boolean result during capture.

The adapter currently parses the structured packaging marker representation exposed by the supplied requirement object. If that representation is unavailable or has an unsupported shape, the trace records an incomplete semantic condition.

The adapter does not implement the full PEP 508 language in Phase 3A.

## 8. Candidate identity

The adapter assigns opaque trace-local candidate IDs.

For candidates whose package/version/source identity is sufficiently observable:

- package;
- version;
- candidate kind;
- source reference;
- origin where source-specific identity matters

form the semantic identity key.

Semantically identical native candidate objects can therefore share a production candidate identity even when the resolver created multiple wrapper objects.

When identity is incomplete, distinct native objects are not collapsed. This conservative behavior avoids a false identity equivalence.

Registry candidates do not use artifact URLs as candidate identity. Artifact records remain separate.

## 9. Candidate kind

The adapter recognizes these cases where the supplied pip object exposes enough information:

- registry;
- VCS;
- direct URL;
- local/path;
- editable/path-like candidates;
- other.

Pip's private class hierarchy and link machinery can be richer than the production portable model. Native details remain outside the portable core unless their semantic meaning is explicit.

## 10. Artifact handling

Where a candidate exposes a source link, the adapter records a separate artifact observation containing, where observable:

- origin;
- observed hash information;
- yanked status.

Artifact compatibility is not invented. When the supplied evidence cannot establish compatibility, the field remains unknown.

This is intentional. Phase 3A does not claim complete wheel/sdist selection, build, or hash semantics.

For multiple observed artifact hashes, the current reduced model cannot faithfully encode every hash variant in one artifact object, so the adapter marks the semantic evidence incomplete rather than choosing a stronger interpretation.

## 11. Requires-Python

Where candidate or distribution metadata exposes `Requires-Python`, the adapter converts supported comparison constraints into explicit `SemanticConstraintKind.REQUIRES_PYTHON` records bound to the captured runtime context.

A missing Requires-Python value does not mean “no restriction.”

Malformed or unsupported metadata is marked incomplete.

## 12. Runtime context

The caller supplies the actual runtime context through `AdapterContext`.

The adapter does not invent multi-environment semantics from a single resolver invocation.

Phase 3A supports a singleton evaluation domain tied to that captured runtime context. Universal/forked proof claims must be introduced by a later layer with an explicit declared evaluation domain.

This prevents:

```
one failed environment
    =>
universal UNSAT
```

## 13. Resolution policy

The caller supplies the policy that is actually relevant to the invocation.

The adapter keeps policy separate from semantic constraints.

Examples include:

- prerelease behavior;
- source selection;
- format policy;
- hash policy;
- version strategy;
- cutoff/exclusion information;
- lock preferences.

The adapter does not infer universal mathematical meaning from these policy values.

## 14. Candidate-domain coverage

This is deliberately conservative.

A candidate match event means:

```
the provider exposed this candidate to the resolver
```

It does **not** automatically mean:

```
this is the complete external candidate universe
```

By default, generated candidate domains therefore have:

```
coverage.status = unknown
```

To establish `complete`, the caller must explicitly supply a typed `CoverageAttestation` and supporting evidence references.

The adapter never fabricates a completeness attestation from the fact that `find_matches()` returned an empty or finite sequence.

## 15. Evidence and provenance

The adapter distinguishes:

- known resolver observations;
- derived normalized semantic objects;
- rejected-candidate observations;
- incomplete normalization;
- unknown coverage.

Normalized constraints receive provenance back to their evidence observations.

Resolver-native rejection/conflict records remain namespaced:

```
resolver_namespace = "resolvelib"
```

Their existence does not make them universal proof clauses.

## 16. Native resolver outcomes

A successful resolver run is recorded as a native SAT **status claim**.

A caught `ResolutionImpossible` is recorded as a native UNSAT **status claim**.

These are not verified results.

The adapter does not independently solve the semantic problem. A typical trace will remain `INCOMPLETE` when candidate-domain completeness or other proof-bearing evidence is missing.

The later independent verifier is responsible for deciding whether the reconstructed semantic proposition is actually SAT/UNSAT.

## 17. Negative-control behavior

The adapter intentionally rejects unsafe shortcuts such as:

- no candidates observed => globally no candidates exist;
- `ResolutionImpossible` => verified UNSAT;
- a rejection event => exhaustive rejection;
- missing metadata => benign default;
- one environment => universal result.

Those facts remain observations or incomplete evidence until a later verifier has enough semantic evidence to justify a proof.

## 18. Offline testing strategy

The production adapter tests use an in-memory dependency graph and a locally installed resolvelib-compatible module where available.

The preferred integration path is:

```
pip._vendor.resolvelib
        +
controlled in-memory provider
        +
RecordingProvider / RecordingReporter
        +
DefaultPipSemantics
        +
production Trace
```

No package-index access is required.

Where an external `resolvelib` installation is unavailable, the test suite can use pip's vendored compatible module. This exercises the real resolver protocol without pretending to execute an external package index.

## 19. Known limitations

The current adapter does not claim complete support for:

- full PEP 508 grammar and all marker interactions;
- complete extras propagation;
- dynamic build-backend metadata generation;
- build-environment side effects;
- full wheel/sdist selection semantics;
- complete artifact/build failure semantics;
- complete hash policy semantics;
- complete lockfile semantics;
- authoritative global source/index exhaustion from resolver-side observation alone;
- universal/forked environment proof domains;
- every pip private resolver/provider behavior;
- every future resolvelib API change.

Unsupported semantics are represented conservatively.

## 20. Security/trust assumptions

Resolver objects are treated as untrusted application data at the normalization boundary.

The adapter:

- does not deserialize Python object code;
- does not use pickle;
- does not use eval/exec;
- does not execute build scripts;
- does not make package-index requests itself;
- does not trust human-readable diagnostics as proof.

The caller remains responsible for controlling the resolver process and the objects supplied to the adapter.

## 21. Files

Implementation:

```
src/resolvewhy/adapters/pip_resolvelib/
    adapter.py
    capture.py
    normalize.py
    __init__.py
```

Tests:

```
tests/test_pip_resolvelib_adapter.py
```

The production trace is serialized through the existing Phase 2 codec. No adapter-specific wire format is introduced.

## 22. Research boundary

Phase 3A does not modify the research conclusion, the 18-case historical fixture corpus, or the final semantic boundary.

The adapter is an engineering implementation of the already validated finite semantic concepts. Where pip/resolvelib exposes less evidence than the semantic contract requires, the adapter reports that limitation instead of weakening the contract.
