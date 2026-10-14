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
| Public API | Typed result categories and stable error classes are documented and tested | `docs/PUBLIC_API.md`, package exports, verification and adapter contract tests | PASS for the documented 0.1 public boundary; no pre-1.0 cross-release Python API guarantee |
| Error handling | Timeout, unsupported semantics, invalid evidence, and internal failures remain distinguishable | typed verification categories, safe verifier entry points, adapter failure codes, and regression tests | PASS for documented resource-limit and failure categories; no wall-clock timeout API exists |
| Security limits | Input size, JSON depth/node count, and evaluation search limits are enforced | codec/solver limits and adversarial tests | PASS for implemented limits; broader threat review remains required |
| Packaging | Wheel and source distribution build; clean installs work outside the checkout | [CI run 38548052099](https://github.com/Vaibhavs25/resolvewhy/actions/runs/38548052099): wheel and sdist validation, external clean installs, smoke tests, and `pip check` on Python 3.10–3.12 | PASS |
| Cross-platform | Linux and Windows Python 3.10–3.12 run the required suites | GitHub Actions CI `test` and `windows` matrices run production/adapter tests, research tests, and the reproducibility harness | PASS on the cited published run; the matrices are enforced on every push and pull request |
| Performance | Bounded execution under documented limits and representative stress cases | `research/run_performance_envelope.py` regression test is included in the production test suite; local Python 3.14.6 sample: a 2 MiB valid decode measured 360.834 ms / 2,111,820 Python-allocator bytes and a deterministic 32-package/31-edge graph solve measured 163.466 ms / 19,269 bytes; zero-state budget exhaustion produced `evaluation_search_limit` | PASS for the automated bounded-regression behavior and these documented local samples only; not a throughput, memory, or latency guarantee |
| Documentation | Installation, API, limitations, research boundary, and support policy match implementation | README, `docs/PUBLIC_API.md`, docs, SECURITY.md | PASS for the documented current scope; historical audit documents intentionally preserve prior evidence |
| CI/release reproducibility | Quality, package, security, and test gates run on every proposed change | `.github/workflows/ci.yml` runs on every push and pull request: pinned Ruff and mypy on Linux Python 3.12; production/adapter, research, reproducibility, and bounded-performance regression tests on Linux and Windows Python 3.10–3.12; security scans/audits and dependency integrity; and wheel/sdist build, validation, clean external smoke tests, and `pip check` on Python 3.10–3.12. [CI run 38592205107](https://github.com/Vaibhavs25/resolvewhy/actions/runs/38592205107) passed the pre-Phase-6 configured jobs for commit `662789a`; the new quality job needs a subsequent published run before it is CI evidence. | PASS for the pre-Phase-6 configured gates on `662789a`; static-analysis enforcement is pending CI evidence for this change |
| Observability/support | Failures expose actionable typed diagnostics without leaking sensitive input | typed verification categories, deterministic result serialization, safe diagnostics, adapter failure codes, and regression tests | PASS for local-library diagnostics; no telemetry, service monitoring, or operational SLO is implemented |

## Release rule

Resolvewhy may be called production-ready only when every mandatory row is
`PASS`. A passing research harness or unit-test suite alone is insufficient.
H2e remains **NOT TESTED** unless substantive maintainer feedback is obtained
and evaluated. No release may claim universal resolver compatibility.

## Gate classification

The CI workflow is triggered for every push and pull request, without path
filters: a source, test, dependency-manifest, packaging, security-configuration,
or workflow change receives the same gates. The CI-enforced gates are Ruff,
mypy, Linux and Windows production/adapter tests, research tests, the
network-free reproducibility harness, bounded-performance regression coverage,
Bandit, strict dependency audits, artifact builds and metadata validation,
external wheel/sdist smoke tests, and `pip check`. The numerical measurements
printed by the performance harness are local evidence, not a CI performance
threshold or an SLO.

Release-candidate publication is a later, manual decision: it requires a
successful CI run for the candidate commit, every mandatory readiness row to be
`PASS`, an accurate release checklist, explicit approval, and no claim beyond
the documented finite fragment. It does not authorize package publication or a
release tag by itself.
