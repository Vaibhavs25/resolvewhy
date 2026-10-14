# Release checklist

Complete every item before publishing a release. Record command output and
tool versions in the release notes or audit report.

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
