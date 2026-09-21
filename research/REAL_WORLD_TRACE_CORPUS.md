# Real-World Trace Corpus

**Date:** 2026-09-21  
**Purpose:** adversarial validation of the revised `resolvewhy-trace` semantic contract against publicly reproducible dependency-resolution failures and failure-adjacent resolver behavior.

## Scope and evidence discipline

This is a research corpus, not an adoption study. Public issue reports are treated as reproducibility sources and architecture evidence; they are not treated as authoritative resolver traces.

Evidence is separated into:
- **A — authoritative resolver evidence:** structured data emitted by the resolver/provider itself, when actually exposed.
- **B — authoritative provider/index evidence:** source/index/metadata facts established by the provider or index.
- **C — observed evidence:** command output, logs, issue reproduction behavior, or local execution.
- **D — derived evidence:** conclusions computed from A/B/C.
- **E — missing evidence:** facts required for a proof but unavailable from the observed boundary.

The local executable environment available for reductions was Linux x86_64, Python 3.13.5, pip 25.1.1, and uv 0.10.0. Poetry and pipgrip were source-validated rather than executed.

## Case matrix

| ID | Ecosystem / resolver | Version in public case | Environment | Failure / behavior | Expected result | Contract classification |
|---|---|---|---|---|---|---|
| RW-01 | pip | 20.3.3 | Python 3.7, Linux | Transitive `fastapi` ranges are disjoint; pip backtracks through unrelated dependencies before exposing the conflict | UNSAT | A — VERIFIED EXPLANATION |
| RW-02 | pip | 23.3 | Python 3.11 | Extras optimization caused pip to reject a satisfiable `kedro[test]` + `dask[complete]` combination | SAT despite resolver failure | B — CORRECT INSUFFICIENT EVIDENCE / negative control |
| RW-03 | pip | 24.3.1 | Python 3.11, Ubuntu 22.04 | Direct VCS requirement combined with a constraints-file VCS reference produces `ResolutionImpossible`; provider semantics differ from ordinary registry requirements | Resolver failure; formal UNSAT not established from text alone | C — LOSSY BUT SAFE REPRESENTATION |
| RW-04 | pip | 25.3 | Python 3.12/3.13/3.14, Alpine | `kokoro>=0.9.4` fails with a long version list but little causal detail | UNSAT may be true, but available evidence does not identify a verified contradiction | B — CORRECT INSUFFICIENT EVIDENCE |
| RW-05 | pip | 25.0.1 | Python 3.10, Linux | `ipython>9` omits Requires-Python rejection unless verbose logging is enabled | UNSAT for that environment, but evidence can be incomplete | B — CORRECT INSUFFICIENT EVIDENCE |
| RW-06 | pip | 2021-era resolver | Python 3.7, Linux | Multiple `extra-index-url` values and source-specific 404 behavior affect candidate visibility | Result depends on source scope | C — LOSSY BUT SAFE REPRESENTATION |
| RW-07 | uv | 0.8.22 | Python 3.13.7, Linux, private Nexus | Conditional `pywin32; sys_platform == "win32"` was reported as a conflict on Linux although the dependency is inactive; adding any package to the private index made the failure disappear | SAT under the stated Linux marker semantics | D — UNSAFE NORMALIZATION ATTACK REJECTED |
| RW-08 | uv | 0.6.9 | Python 3.12.9, Linux, private index | Private index returns 401/403; uv may say package is not found while authentication failed, and may fall back to PyPI | No-candidate proof is forbidden without source-query success/coverage evidence | B — CORRECT INSUFFICIENT EVIDENCE |
| RW-09 | uv | 0.7.18 | Python 3.12, Linux | Universal resolution split for Python 3.9 creates a real incompatibility even while active Python is 3.12 | UNSAT over declared supported-Python domain | C — LOSSY BUT SAFE REPRESENTATION |
| RW-10 | uv | 0.11.8 | Python 3.14.4, macOS x86_64 | `exclude-newer` removes a version by upload-time cutoff while a pre-release hint is also shown | Failure is policy/cutoff-sensitive, not simply prerelease-disabled | C — LOSSY BUT SAFE REPRESENTATION |
| RW-11 | uv | 0.7.6 | Python 3.7.9, Windows/MSYS | A dependency is yanked; uv refuses it while pip installs with a warning | Resolver-policy difference; no universal UNSAT meaning | C — LOSSY BUT SAFE REPRESENTATION |
| RW-12 | uv | 0.12.4 | Python 3.12.13, x86_64 Linux | Partial per-file yank: one wheel is yanked while another wheel of the same version is not; lockfile retains the yanked wheel | Artifact-level yank status must remain distinct from candidate/version identity | C — LOSSY BUT SAFE REPRESENTATION |
| RW-13 | uv | 0.6.14 | Python 3.11/3.12, Linux | Same package is sourced from remote/local indexes under platform markers | Source scope and active marker determine candidate domain | C — LOSSY BUT SAFE REPRESENTATION |
| RW-14 | uv 0.10.0 reduction + public pattern | 0.10.0 | Linux x86_64, Python 3.13.5 | Minimal transitive conflict: `appa -> depA<2`, `depA==1 -> leaf==1`, `depB==1 -> leaf==2`, roots select `appa==1`, `depB==1` | UNSAT | A — VERIFIED EXPLANATION |
| RW-15 | local pip + uv reduction | 25.1.1 / 0.10.0 | Linux x86_64, Python 3.13.5 | Only Windows wheel available for candidate | No usable artifact in current runtime; candidate itself exists | C — LOSSY BUT SAFE REPRESENTATION |
| RW-16 | local pip + uv reduction | 25.1.1 / 0.10.0 | Linux x86_64, Python 3.13.5 | Candidate has `Requires-Python >=4` | Candidate exists but is unusable in runtime context | C — LOSSY BUT SAFE REPRESENTATION |
| RW-17 | local pip + uv reduction | 25.1.1 / 0.10.0 | Linux x86_64, Python 3.13.5 | Only `1.0rc1` exists for <2; pip default rejects, pip `--pre` accepts; uv default accepts and `--prerelease=disallow` rejects | Policy-sensitive result | C — LOSSY BUT SAFE REPRESENTATION |
| RW-18 | local pip + uv reduction | 25.1.1 / 0.10.0 | Linux x86_64 | Same name/version is exposed from two HTTP indexes; selected artifact carries source URL | Source-qualified candidate identity | C — LOSSY BUT SAFE REPRESENTATION |

## Detailed case records

### RW-01 — pip transitive backtracking conflict

Public reproduction: pip issue #9455. A package `package1==0.0.1` requires `fastapi>=0.61.0,<0.62.0`, while `package2==0.0.2` requires both `package1` and `fastapi>=0.60.0,<0.61.0`. pip reports the disjoint `fastapi` ranges after exploring multiple versions. The issue explicitly describes a self-contained local reproduction.

Trace semantics:
- root requirements are authoritative known facts.
- dependency edges are authoritative metadata facts.
- candidate-domain coverage is proof-strengthening only once the relevant source scope is explicitly covered.
- resolver backtracking is observed resolver evidence, not itself the proof.
- the normalized contradiction is the intersection of the two version constraints.

Outcome:
The contradiction is representable and independently verifiable as UNSAT in the semantic core.

### RW-02 — pip extras optimization failure on a satisfiable problem

Public reproduction: pip issue #12376. The issue reports that pip 23.3's extras optimization can cause a valid combination involving `kedro[test]==0.18.14` and `dask[complete]==2021.12.0` to fail with `ResolutionImpossible`.

This is a critical negative control: a resolver failure is not equivalent to a mathematically UNSAT dependency set.

Trace semantics:
- resolver failure is C evidence.
- the optimization behavior is resolver-specific A/C evidence.
- unless the normalized active dependency constraints themselves contradict, the downstream proof engine must not emit UNSAT.
- the correct semantic status for the observed failure is either SAT (when the full package semantics are independently established) or insufficient_evidence, never UNSAT merely because pip failed.

### RW-03 — pip VCS constraint interaction

Public reproduction: pip issue #13120. A normal requirement `faster_whisper` leads to a transitive `whisper-timestamped` requirement while the constraints file supplies a VCS URL for the same package. pip 24.3.1 reports a conflict. A pip maintainer explains in the issue that constraints are not intended to cause packages to be downloaded/built and that VCS links require source-tree metadata extraction.

Trace semantics:
- direct/VCS identity must remain opaque and source-qualified.
- the fact that a constraint contains a VCS reference is not equivalent to an ordinary version constraint.
- resolver/provider design semantics are namespaced.
- without structured metadata proving the exact candidate relation, no independent UNSAT proof is claimed.

### RW-04 — pip `kokoro>=0.9.4` with poor conflict evidence

Public reproduction: pip issue #13760. On Python 3.12/3.13/3.14 Alpine environments, pip 25.3 reports many old `kokoro` versions as conflicting but does not explain the decisive conflict for the requested range. The issue reports a long build process before failure.

Trace semantics:
- the emitted version list is observed candidate evidence.
- no complete semantic contradiction is recovered from the issue output alone.
- a downstream engine must return `insufficient_evidence` unless additional authoritative metadata establishes the contradiction.

### RW-05 — pip Requires-Python evidence omitted from normal error output

Public reproduction: pip issue #13260. With Python 3.10, `pip install "ipython>9"` can fail without stating the Requires-Python incompatibility unless verbose logging is enabled.

This demonstrates that human-readable failure output can omit semantically decisive metadata even when the resolver internally knows it.

Trace semantics:
- runtime context is authoritative only when actually captured.
- Requires-Python is candidate metadata, not candidate absence.
- absence of the skipped-link explanation must be treated as missing evidence, not as proof that the candidate did not exist.

### RW-06 — pip multiple extra-index source scope

Public reproduction: pip issue #11628. Multiple `--extra-index-url` values and source-specific 404 behavior affect candidate discovery.

Trace semantics:
- source/index scope is part of the candidate domain.
- an empty result from one source is not global source exhaustion.
- source query failure/404 semantics remain namespaced provider/index evidence.

### RW-07 — uv conditional dependency false-conflict pattern

Public reproduction: uv issue #16613, uv 0.8.22, Python 3.13.7, Linux. The project depends on `docker`, whose dependency on `pywin32` is marked `sys_platform == "win32"`. The issue reports uv constructing a conflict on Linux against a private Nexus mirror that lacks `pywin32`; uploading any `pywin32` package to the private index removes the failure.

This is the strongest false-proof attack in the corpus.

Naive normalization:
`docker -> pywin32>=304` + `only pywin32<304 available` -> UNSAT.

Correct semantic normalization:
the dependency edge has an activation condition; for Linux, `sys_platform == "win32"` is false, so the edge is inactive. The native uv failure therefore cannot be copied into a formal UNSAT claim.

Outcome:
**The revised contract rejects the unsafe normalization.**

### RW-08 — private-index authentication failure masquerading as absence

Public reproduction: uv issue #12362, uv 0.6.9, Python 3.12.9, Linux. A private index returning 401/403 can cause uv to report that a package was not found; the same issue states that uv may fall back to PyPI when the package is available there.

Required trace state:
- source query attempted
- source/index identity
- authentication failure
- query coverage = unknown/partial
- candidate coverage attestation absent

Outcome:
`insufficient_evidence` for any claim of source-global candidate absence.

### RW-09 — universal Python split

Public reproduction: uv issue #14484, uv 0.7.18, Python 3.12, Linux. Project `requires-python >=3.9` depends on `numba>=0.61`; uv reports a failing split for `python_full_version == '3.9.*'` because the relevant numba versions require >=3.10.

Trace semantics:
- the supported-Python domain contains more than the active interpreter.
- a single runtime snapshot is insufficient to represent universal resolution.
- the candidate domain/query scope must include the split condition.
- if the split domain is authoritative and exhaustively covered, UNSAT over that declared project support domain is independently verifiable.

### RW-10 — `exclude-newer` policy interaction

Public reproduction: uv issue #19266, uv 0.11.8, Python 3.14.4, macOS x86_64. `aiobotocore~=3.6` is filtered by `exclude-newer` to uploads before a cutoff; uv additionally emits a prerelease hint.

Trace semantics:
- upload-time cutoff belongs to `resolution_policy`.
- prerelease state is separately represented.
- the hint is human-readable resolver output and is not a universal semantic clause.

A normalizer that collapses both facts into `prerelease disabled` would be unsafe. The revised contract avoids this by separating policy facts and provenance.

### RW-11 — yanked dependency policy difference

Public reproduction: uv issue #13569, uv 0.7.6. A package depends on yanked `futures==3.1.1`; uv refuses the dependency while pip installs it with a warning.

Trace semantics:
- yank state belongs to source/artifact metadata.
- whether yanked artifacts are allowed is resolution policy.
- resolver outcome must not be normalized into universal UNSAT.

### RW-12 — per-file yank vs version identity

Public reproduction: uv issue #21430, uv 0.12.4, Python 3.12.13, x86_64 Linux. Two wheels for `numpy==2.1.3` share a version but one file is yanked and the other is not. uv avoids selecting the yanked wheel but retains its URL/hash in `uv.lock`.

Trace semantics:
- candidate identity cannot be only package+version.
- artifact identity and artifact status are distinct.
- the issue shows why artifact-level provenance must survive serialization.

### RW-13 — source split by marker

Public reproduction: uv issue #13448, uv 0.6.14, Python 3.11/3.12, Linux. The package `abc` is sourced from one index under `sys_platform == "linux"` and another local index under the opposite marker.

Trace semantics:
- source/index scope is conditional.
- runtime context activates one source branch.
- the normalized query domain must preserve both the source set and activation condition.

### RW-14 — executed cross-resolver minimal transitive reduction

Local executable reduction built specifically from the structure of real transitive conflict reports:
- `appa==1.0 -> depA<2, depB==1.0`
- `depA==1.0 -> leaf==1.0`
- `depA==2.0 -> leaf==2.0`
- `depB==1.0 -> leaf==2.0`
- roots require `appa==1.0` and `depB==1.0`

pip 25.1.1 and uv 0.10.0 both fail.

The semantic core independently produced a verified subset-minimal UNSAT core:
`root:appa`, `root:depB`, `appa->depA`, `depA1->leaf`, `depB1->leaf`.

Removing any one of those five constraints made the normalized problem satisfiable.

This is subset-minimal, not minimum-cardinality.

### RW-15 — executed platform artifact reduction

A local wheel exists only with a Windows platform tag while the runtime is Linux x86_64.

pip 25.1.1 reports no matching distribution. uv 0.10.0 explicitly distinguishes the existing version from the absence of a matching wheel.

Semantic interpretation:
candidate exists; artifact is incompatible with the runtime context.

### RW-16 — executed Requires-Python reduction

A local candidate declares `Requires-Python >=4`; runtime is Python 3.13.5.

pip 25.1.1 rejects it; uv 0.10.0 provides a structured explanation connecting the candidate to the Python requirement.

Semantic interpretation:
candidate exists; runtime context makes it unusable.

### RW-17 — executed prerelease-policy reduction

Only `prepkg==1.0rc1` exists for `prepkg<2`.

pip default rejects; pip `--pre` accepts.
uv 0.10.0 default accepts; uv `--prerelease=disallow` rejects.

This is a direct cross-resolver policy difference. Identical candidate evidence produces different resolver outcomes under different policies.

### RW-18 — executed source-distinct same-version reduction

Two local HTTP indexes each expose `indexpkg==1.0`, with distinct artifacts. pip and uv both resolve with the combined source configuration; pip's successful report points to the selected source URL.

Semantic interpretation:
same package/version is not sufficient identity for all source-sensitive cases.

## Case selection conclusion

The corpus intentionally contains:
- true transitive UNSAT
- resolver-failure-but-SAT behavior
- source/index scope failures
- authentication/access failures
- marker-conditioned false conflicts
- universal-resolution splits
- prerelease policy differences
- Requires-Python
- platform artifacts
- VCS/direct source identity
- extras
- yanking
- artifact-level provenance
- bounded/subset candidate discovery
- resolver backtracking

The cases were selected to stress semantic boundaries rather than maximize the number of successful proofs.
