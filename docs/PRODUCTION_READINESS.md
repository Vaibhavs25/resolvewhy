# Production-readiness contract

This document is the acceptance contract for Resolvewhy engineering work. It
does not convert research evidence into a production guarantee. Every item is
evaluated using only recorded evidence from the current repository and CI.

Status values are deliberately limited to `PASS`, `FAIL`, `BLOCKED`, and
`NOT TESTED`.

| Area | Acceptance criterion | Implementation/evidence | Status |
| --- | --- | --- | --- |
| Correctness | Supported SAT/UNSAT results are independently recomputed | `verification/`, production tests, research harness | PASS for the declared finite fragment |
| Soundness | Incomplete or unsupported evidence cannot produce a verified result | fail-closed verifier and adversarial tests | PASS for tested cases |
| Trace validation | Malformed schemas, references, enums, duplicate keys, and resource-limit violations are rejected | `trace/codec.py`, validation and mutation tests | PASS for tested limits and cases |
| Explanation consistency | Every displayed verified claim is bound to the verified result and references | explanation tests and provenance checks | PASS for tested cases |
| Dependency semantics | Supported version, marker, candidate, artifact, policy, and finite-domain semantics are explicit | semantic solver and boundary documentation | PASS only within documented subset |
| Public API | Typed result categories and stable error classes are documented and tested | package exports, verification result tests | FAIL: API stability policy and type-clean surface remain incomplete |
| Error handling | Timeout, unsupported semantics, invalid evidence, and internal failures remain distinguishable | verifier result model and adapter tests | PASS for tested categories |
| Security limits | Input size, JSON depth/node count, and evaluation search limits are enforced | codec/solver limits and adversarial tests | PASS for implemented limits; broader threat review remains required |
| Packaging | Wheel and source distribution build; clean installs work outside the checkout | [CI run 38548052099](https://github.com/Vaibhavs25/resolvewhy/actions/runs/38548052099): wheel and sdist validation, external clean installs, smoke tests, and `pip check` on Python 3.10–3.12 | PASS |
| Cross-platform | Linux and Windows Python 3.10–3.12 run the required suites | GitHub Actions CI | PASS for current commit |
| Performance | Bounded execution under documented limits and representative stress cases | solver search limit; stress evidence | NOT TESTED |
| Documentation | Installation, API, limitations, research boundary, and support policy match implementation | README, docs, SECURITY.md | FAIL until this contract is fully synchronized |
| CI/release reproducibility | Quality, package, security, and test gates run on every supported platform | `.github/workflows/ci.yml`; Linux/Windows test matrices and artifact validation passed in CI run 38548052099; security gate is defined but requires CI execution on its publishing commit | BLOCKED: pending security-job CI evidence |
| Observability/support | Failures expose actionable typed diagnostics without leaking sensitive input | result/issue models and security policy | NOT TESTED |

## Release rule

Resolvewhy may be called production-ready only when every mandatory row is
`PASS`. A passing research harness or unit-test suite alone is insufficient.
H2e remains **NOT TESTED** unless substantive maintainer feedback is obtained
and evaluated. No release may claim universal resolver compatibility.
