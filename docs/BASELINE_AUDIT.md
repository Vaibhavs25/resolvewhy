# Production-readiness baseline

Baseline captured from commit `aeced1a1f8a3270b3f6261d3dc780c66407a27f1`
(`main`, `origin/main`) on Windows with Python 3.12.14.

## Confirmed results

- `python -m unittest discover -s tests -v`: **178 tests passed**.
- `python -m unittest research.test_reproducibility -v`: **29 tests passed**.
- `python research/run_reproducibility.py --json`: **passed** when run with
  permission to create isolated temporary subprocess directories. It reported
  18/18 trace-only classifications, 18/18 serialization round trips, 18/18
  hermetic replays, 2 subset-minimal proofs, 250 mutation cases with zero
  false verified-proof accepts, and 256 projection worlds with zero
  post-repair collisions.
- `python -m pip check`: passed.
- A wheel can be built with `pip wheel . --no-deps --no-build-isolation`.
- GitHub CI for the same commit passed Linux and Windows Python 3.10–3.12.

## Confirmed defects and gaps

- Ruff 0.17.0 reports **136 findings** across source and tests. Findings
  include import ordering, unused exports, formatting, and broad exception
  handling. No lint gate is currently configured.
- mypy 2.4.0 reports **131 errors in 7 source files** under the current
  permissive baseline invocation. No type-check gate is currently configured.
- Source-distribution build and isolated wheel/sdist smoke testing were not
  yet recorded in this baseline.
- No maintained vulnerability/dependency audit gate is configured.
- Public API stability and support/observability contracts are not fully
  documented.
- Performance and adversarial resource-exhaustion behavior beyond existing
  parser/search limits are not established.

## Harness/environment distinction

The first local harness attempt failed because the sandbox denied writes to its
temporary directory. This was an environment permission failure, not a test
failure. The same command passed when executed with the required permission.

## Correctly unsupported behavior

The adapter and verifier intentionally fail closed for unsupported markers,
policies, candidate coverage, artifact compatibility, and version semantics.
The repository does not claim full PEP 508, universal resolver compatibility,
or a CLI/API.

## Documentation discrepancies

The README correctly preserves the bounded research status and H2e
**NOT TESTED** boundary, but it previously lacked a measurable engineering
readiness contract and security/release policy. Those documents are added by
this audit; their PASS statuses depend on later evidence.
