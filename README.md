# resolvewhy

Research prototype for formally verified explanations of dependency-resolution failures from structured evidence.

## Research question

Can a resolver expose a small, versioned, machine-readable evidence surface that an independent downstream analyzer can consume to compute a formally justified dependency-conflict explanation without parsing human-readable diagnostics?

The work separates two hypotheses:

- **H1:** Given sufficiently rich structured evidence, resolvewhy can compute a verified subset-minimal explanation.
- **H2:** Real resolver/tooling ecosystems can expose that evidence in a sufficiently stable and portable form for an independent library to consume.

## Current evidence

A real resolvelib implementation has been instrumented through structured provider/reporter contracts without stderr scraping. In controlled round-trip experiments, resolver outcomes matched resolvewhy, and captured UNSAT traces produced independently verified subset-minimal cores. Explicitly removing candidate-inventory evidence correctly resulted in `insufficient_evidence`.

The current evidence-interface work therefore establishes feasibility in one resolver architecture. It does not establish cross-ecosystem portability or maintainer support.

## Current H2 status

- H2a — real resolver can expose sufficiently rich evidence: **SUPPORTED, narrowly**
- H2b — evidence can be normalized: **PARTIALLY SUPPORTED**
- H2c — normalized evidence is sufficient for verified MUS extraction: **SUPPORTED in controlled traces**
- H2d — stable/portable across ecosystems: **UNPROVEN**
- H2e — maintainer validation: **NOT TESTED / currently being tested**

See [docs/TRACE_RFC_DRAFT.md](docs/TRACE_RFC_DRAFT.md) for the experimental trace abstraction and research questions.

> **Research-only status:** This repository is a research prototype. It does not claim to provide a production resolver, a package-manager standard, or an established cross-ecosystem trace format.

No adoption, maintainer endorsement, ecosystem standardization, production readiness, or superiority over pip, uv, Poetry, or other tools is claimed.