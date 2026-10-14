# Security policy

Resolvewhy processes resolver evidence as untrusted input. The verifier is
designed to fail closed: malformed, incomplete, unsupported, or resource-limit
exceeding input must not become a verified explanation.

## Reporting a vulnerability

Do not disclose a suspected vulnerability in a public issue. Contact the
repository maintainers privately through the GitHub repository's security
contact. Include a minimal reproducer, affected commit/version, Python version,
operating system, and whether the issue affects confidentiality, integrity, or
availability. Do not include private package indexes, credentials, or
proprietary resolver traces.

## Scope and limitations

The current package has no network service, subprocess execution, or dynamic
code evaluation in its production semantic core. Resource limits protect JSON
decoding and finite evaluation, but automated scans do not prove security.
The package does not claim protection against every denial-of-service input,
resolver-specific behavior, dependency supply-chain compromise, or secrets
embedded in caller-provided traces.

Security fixes must preserve fail-closed verification and add a regression test
for the reported behavior.

## Resource envelope

The trace decoder enforces a 2 MiB serialized-input limit, a maximum JSON
depth of 64, and at most 200,000 JSON values.  Byte, nesting, and value-count
checks run before JSON materialization; reconstructed model validation then
rejects invalid references and unsupported semantics.  Finite branch solving
is limited to 100,000 search states.  Claimed subset-minimal UNSAT cores are
limited to 128 solver invocations, enough to derive and independently check a
63-premise core.  Exceeding a decoding limit produces an invalid trace;
exceeding a solver or core-verification limit produces an inconclusive result.

These values bound untrusted-input work rather than promising a performance
service level.  They are selected to avoid decoder recursion and unbounded
materialization while retaining the current finite research corpus.  Larger
inputs require a separately reviewed supported-envelope change.

## Maintainer security checks

The pinned tools in `security-requirements.txt` are Bandit 1.9.4 for static
analysis and pip-audit 2.10.1 for known-vulnerability checks.  Run them from a
clean Python environment:

```powershell
python -m pip install -r security-requirements.txt
python -m bandit -r src
python -m pip_audit --strict --progress-spinner off -r <base-third-party-freeze.txt>
python -m pip_audit --strict --progress-spinner off -r <pip-resolvelib-third-party-freeze.txt>
```

Use separate environments containing editable `.` and `.[pip-resolvelib]`
respectively, then run `python -m pip list --format=freeze`, removing only
`resolvewhy`, `pip`, and `setuptools` from each generated requirements file.
The base environment currently has no third-party runtime dependencies; the
optional environment must remain non-empty and is audited from its exact frozen
versions. This avoids misreporting the unpublished local package as a PyPI
dependency while keeping every installed third-party runtime dependency in
scope. Artifact CI separately installs and tests the non-editable wheel and
source distribution. pip-audit requires live vulnerability service access; an
unavailable service or failed dependency collection is a failed audit, not a
clean result. The CI `security` job performs those exact base and
optional-dependency checks and keeps scanner dependencies out of the audited
environments.
