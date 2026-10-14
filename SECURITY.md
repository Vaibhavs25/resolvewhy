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
