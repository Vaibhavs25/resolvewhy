# Current limitations

Resolvewhy is a bounded verification library, not a general package resolver.

- The independently verified semantic fragment is finite and explicitly
  scoped. Unsupported semantics return an inconclusive or invalid result.
- Full PEP 508 interactions, build-backend behavior, lockfiles, hash policy,
  system/provided packages, and arbitrary resolver-specific semantics are not
  established.
- The pip/resolvelib adapter records observable evidence; it does not claim
  that a resolver failure or a pip report enumerates every candidate.
- CLI, HTTP API, hosted service, and additional resolver adapters are not
  implemented.
- H2e maintainer validation is **NOT TESTED**. No generic acknowledgement or
  lack of response is treated as technical validation.
- The package is not production-ready until the acceptance contract in
  `docs/PRODUCTION_READINESS.md` has no mandatory FAIL, BLOCKED, or NOT TESTED
  entries.
- The documented security envelope is bounded: traces are limited to 2 MiB,
  JSON depth 64, and 200,000 values; branch solving is capped at 100,000
  states; subset-minimal core checking is capped at 128 solver calls.  These
  limits produce invalid or inconclusive outcomes rather than a verified
  result, but they are not a throughput guarantee for arbitrary large graphs.
