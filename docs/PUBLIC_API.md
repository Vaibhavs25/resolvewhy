# Public API and diagnostic contract

This document defines the intended Python API for the proposed `0.1.0rc1`
release candidate. It supports Python 3.10, 3.11, and 3.12. It describes a
bounded verification library, not a package resolver, CLI, HTTP service, or
ecosystem-wide resolver interface.

## Supported modules

The supported import surfaces are:

- `resolvewhy.model` for immutable trace and semantic-model dataclasses;
- `resolvewhy.trace` for the `resolvewhy-trace/1.0` codec and its explicit
  limits;
- `resolvewhy.validation` for structural validation;
- `resolvewhy.verification` for independently recomputed verification;
- `resolvewhy.explanation` for deterministic renderable explanations; and
- `resolvewhy.adapters.pip_resolvelib` when the optional
  `pip-resolvelib` extra is installed.

The root `resolvewhy` package re-exports the trace model, codec, and structural
validation surface for convenience. New integrations should use the named
submodules above so their dependencies are explicit.

## Verification results

`verify(trace)` accepts only a typed `Trace`. It is intentionally strict: a
wrong Python type is a programmer error and raises `TypeError`; unexpected
implementation failures propagate for local debugging.

`verify_serialized(data)` accepts UTF-8 JSON text or bytes. Decode and schema
failures are returned as `VerificationResult(status=INVALID_TRACE)` with stable
issue codes; callers do not need to parse exception text.

Services handling untrusted requests can use `verify_safe` or
`verify_serialized_safe`. They turn unexpected `Exception` failures into
`INTERNAL_ERROR`, never a verified result, and deliberately return the fixed
`internal_error` diagnostic without exception messages, trace contents,
credentials, private-index URLs, or local filesystem paths. The direct APIs do
not log input or emit telemetry.

| `VerificationCategory` | Meaning | Independently verified? |
| --- | --- | --- |
| `verified_sat` | The supported finite proposition is satisfiable. | Yes |
| `verified_unsat` | The supported finite proposition is unsatisfiable. | Yes |
| `invalid_evidence` | The trace is malformed, inconsistent, or invalid. | No |
| `insufficient_evidence` | Required evidence is missing or incomplete. | No |
| `unsupported_semantics` | The trace needs semantics outside the supported fragment. | No |
| `resource_limit` | A configured solver or core-verification limit was exhausted. | No |
| `internal_error` | A safe entry point caught an unexpected failure. | No |

Use `result.category`, `result.status`, `result.reasons`, and
`result.issues[*].code` as machine-readable data. `message` is actionable
human diagnostic text, not an API for branching. `result.is_verified` is true
only for `VERIFIED_SAT` and `VERIFIED_UNSAT`.

`VerificationResult.to_dict()` and `to_json()` expose a deterministic,
JSON-compatible diagnostic representation. The result representation is an
output report, not a separately versioned interchange format; callers should
retain the original trace when durable interchange is needed.

## Errors and adapters

`deserialize_trace` raises `TraceDecodeError` for malformed serialized input;
`serialize_trace` raises `TraceSerializationError` for an invalid typed model;
and `assert_valid_trace` raises `TraceValidationError` containing typed
`ValidationIssue` values. Each is a `ValueError` subtype and should be handled
at the trace boundary.

The optional pip/resolvelib adapter preserves native SAT/UNSAT claims as
unverified capture information. A resolver failure does not establish
`VERIFIED_UNSAT`. Its construction/execution failures raise
`AdapterExecutionError` with an `AdapterFailureCode` of
`optional_dependency_missing`, `unsupported_resolver_interface`, or
`adapter_execution_failed`. The original exception is chained for a direct
caller, while the public message does not repeat arbitrary provider diagnostics.

The adapter supports the public resolvelib provider/reporter protocol and the
documented `AdapterContext` evidence model. pip private internals, arbitrary
resolver event types, index completeness, and future resolver versions are not
compatibility promises; see `docs/ADAPTER_PIP_RESOLVELIB.md`.

## Trace and compatibility policy

`resolvewhy-trace/1.0` has canonical deterministic UTF-8 JSON serialization.
Unknown fields, unknown schema versions, malformed references, and values over
the published size/depth/node limits are rejected. Existing `1.0` documents
remain readable only when they meet the current validation and security limits.
No automatic schema migration is performed.

Before a `1.0` package release, Resolvewhy makes no cross-release compatibility
guarantee beyond the documented `resolvewhy-trace/1.0` schema and Python 3.10,
3.11, and 3.12 for this candidate. Changes to this named Python surface should
be additive where practical. Any removal or material semantic change requires a
documented deprecation notice in a release before it is removed, except where a
security fix must fail closed. New trace schemas require a new schema identifier
and an explicit compatibility statement; they must not silently reinterpret
`1.0` documents.

## Bounded operation

There is no wall-clock timeout API in this release. The decoder and solver use
the resource bounds in `SECURITY.md`; limit exhaustion is an explicit non-
verified outcome. The bounded performance harness,
`python research/run_performance_envelope.py --json`, records a local sample of
near-limit decode/verification, a deterministic semantic dependency graph, and
resource-limit behavior. It is evidence for those inputs only, not a service-
level objective or general performance guarantee.
