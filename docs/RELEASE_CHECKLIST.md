# Release checklist

Complete every item before publishing a release. Record command output and
tool versions in the release notes or audit report.

## CI-enforced gates

For a proposed commit, GitHub Actions runs on every push and pull request:

- pinned Ruff and mypy checks on Linux Python 3.12;
- production/adapter tests, research tests, the network-free reproducibility
  harness, and bounded-performance regression coverage on Linux and Windows
  Python 3.10, 3.11, and 3.12;
- Bandit and strict dependency audits, including base and optional adapter
  environments; and
- wheel/sdist builds, metadata validation, isolated external artifact smoke
  tests, and `pip check` on Python 3.10, 3.11, and 3.12.

CI success is evidence only for the commit tested. It does not create a tag,
publish a package, establish an SLO, add a wall-clock timeout or telemetry
guarantee, establish universal resolver compatibility, or change H2e from
**NOT TESTED**.

## Release-candidate decision

Before proposing a release candidate, require a successful CI run for the
candidate commit, every mandatory production-readiness row to be `PASS`, this
checklist to remain accurate, a clean reviewed tree, and explicit approval.
Release tags and package publication require separate authorization.

- [ ] Review the production-readiness contract; every mandatory row is PASS.
- [ ] Run production unit and adapter tests on Linux and Windows for Python
      3.10, 3.11, and 3.12.
- [ ] Run research tests and the network-free reproducibility harness.
- [ ] Run configured linting, type checking, Bandit static analysis, and
      pip-audit dependency scans for both base and optional adapter environments.
- [ ] Build both wheel and source distribution from a clean checkout.
- [ ] Install the wheel in an isolated environment outside the repository and
      run the documented public-API smoke test.
- [ ] Verify optional adapter dependencies and unsupported-semantics failures.
- [ ] Review trace size/depth/node and solver evaluation limits.
- [ ] Review README, limitations, SECURITY.md, and H2e wording for claims.
- [ ] Inspect the final diff for unrelated changes and confirm the working tree
      is clean.
- [ ] Obtain explicit approval before pushing release commits or tags.
