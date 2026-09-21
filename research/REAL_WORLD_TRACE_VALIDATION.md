# Real-World Trace Validation

**Date:** 2026-09-21  
**Decision:** **A. REAL-WORLD VALIDATION PASSES**

## 1. Research question

Does the revised `resolvewhy-trace` contract remain semantically correct when realistic resolver evidence contains interacting sources, environments, policies, candidate identities, artifacts, metadata, resolver decisions, and incomplete observations?

The experiment was explicitly falsification-oriented. Resolver failure text was never treated as a proof by itself.

No maintainer outreach was performed. No production adapter or production trace framework was built.

## 2. Method

The experiment combined:
1. public reproducible issue reports from pip, uv, and Poetry;
2. current resolver/source architecture observations already established in the project;
3. executable pip 25.1.1 and uv 0.10.0 local reductions on Linux x86_64 / Python 3.13.5;
4. an independent proof gate enforcing revised candidate-domain coverage rules;
5. independent subset-minimality checks over one fully normalized UNSAT reduction.

The public issue corpus was used as the source of realistic semantic patterns. Local reductions were deliberately minimal so the proof engine could be tested without pretending the local fixture is the original upstream environment.

## 3. Evidence model

Every case is partitioned into:

### A. Authoritative resolver evidence
Examples:
- structured uv contradiction/error information when available;
- resolvelib provider/reporter facts from the previously validated architecture boundary.

### B. Authoritative provider/index evidence
Examples:
- package metadata;
- source/index scope;
- artifact tags;
- VCS commit IDs;
- yank state;
- upload cutoff;
- candidate query scope.

### C. Observed evidence
Examples:
- CLI output;
- exit code;
- public issue reproduction;
- selected URL;
- build/log behavior.

### D. Derived evidence
Examples:
- normalized semantic literals;
- candidate-domain intersections;
- proof cores;
- conclusions obtained by the independent proof engine.

### E. Missing evidence
Examples:
- source query failed with 401/403;
- resolver output omits Requires-Python details;
- a provider exposes only a bounded candidate subset;
- a failed `--report` invocation emits no failure trace.

Derived evidence never upgrades into A or B.

## 4. Revised trace generation

The semantic trace for each case contains, as applicable:
- requirement
- opaque candidate identity
- artifact identity
- dependency edge
- activation condition
- runtime context
- resolution policy
- candidate-domain coverage
- semantic constraint/literal
- provenance
- evidence state
- optional resolver-specific derivation namespace

The wire encoding is deliberately secondary. The validation target is semantic preservation.

## 5. Core safety checks

The proof gate enforced:
- a no-candidate conclusion requires an explicit candidate domain;
- source/index scope must be present;
- runtime context and resolution policy must be explicit;
- coverage must be `complete`;
- completeness must have an explicit attestation;
- relevant filtering/artifact constraints must be represented;
- partial, bounded, observed, or unknown coverage forbids no-candidate proof;
- resolver rejection does not imply exhaustion;
- same package/version from distinct sources remains distinct;
- marker activation cannot be dropped;
- resolver-specific incompatibility semantics remain namespaced.

### Gate result

**All 8 previously defined adversarial contract checks passed.**

A second, stronger attack was also applied: removing one necessary coverage component from a complete-domain proof obligation. Each mutation correctly disabled the proof obligation rather than silently assuming the missing fact.

| Removed evidence | Result |
|---|---|
| source scope | proof forbidden |
| completeness status | proof forbidden |
| completeness attestation | proof forbidden |
| artifact/filter evidence | proof forbidden |
| resolution policy | proof forbidden |

No mutation produced an unjustified `UNSAT`.

## 6. Case-by-case findings

### RW-01: transitive conflict
The public pip reproduction and the local reduction are compatible with the semantic model. The conflict can be represented as requirement and dependency literals with provenance. The local reduction generated a verified subset-minimal core.

**Classification: A — VERIFIED EXPLANATION** for the reduced semantic case; the full historical pip trace remains richer and partially implementation-specific.

### RW-02: resolver fails but requirements are satisfiable
The public pip issue is a decisive negative control. A resolver's `ResolutionImpossible` cannot be promoted to mathematical UNSAT without independently checking the normalized constraints.

**Classification: B — CORRECT INSUFFICIENT EVIDENCE / SAT negative control.**

### RW-03: VCS constraint interaction
The VCS and constraint semantics are source/provider-specific. Candidate identity and build/source behavior can be carried, but the issue text alone is not enough for a resolver-independent proof.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

### RW-04: poor `ResolutionImpossible` explanation
The failure is observable, but the decisive contradiction is not exposed.

**Classification: B — CORRECT INSUFFICIENT EVIDENCE.**

### RW-05: omitted Requires-Python diagnostics
The candidate may exist even when normal output omits the reason it was filtered.

**Classification: B — CORRECT INSUFFICIENT EVIDENCE.**

### RW-06: multiple extra indexes
A source-local negative result is not global source exhaustion.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

### RW-07: uv false conflict under inactive marker
This is the principal unsafe-normalization attack.

A naive adapter could flatten the conditional edge and reproduce uv's `No solution found` as an UNSAT clause. That would be unsound on Linux.

The revised contract retains the activation condition and requires independent semantic verification. Therefore the unsafe normalization is rejected.

**Classification: D — UNSAFE NORMALIZATION ATTACK REJECTED BY CONTRACT.**

This is a property of the contract, not a defect requiring schema revision.

### RW-08: index authentication failure
A 401/403 is not source exhaustion.

The trace must record source-query failure and mark coverage unknown/partial.

**Classification: B — CORRECT INSUFFICIENT EVIDENCE.**

### RW-09: universal Python split
The semantic model can represent a separate candidate domain/scope for `python_full_version == '3.9.*'`.

**Classification: C — LOSSY BUT SAFE REPRESENTATION**, with independent proof possible when the split domain is authoritative and complete.

### RW-10: `exclude-newer`
The cutoff is a policy fact and must not be collapsed into prerelease policy.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

### RW-11: yanked dependency
Yank state and yanked-acceptance policy differ across resolvers.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

### RW-12: partial per-file yank
Artifact identity is distinct from candidate/version identity.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

### RW-13: marker-dependent source split
Source/index identity and marker activation can both be preserved.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

### RW-14: executed cross-resolver reduction
pip 25.1.1 and uv 0.10.0 both reported failure. The normalized proof engine independently verified the five-element core and verified necessity by deleting each element individually.

**Classification: A — VERIFIED EXPLANATION.**

### RW-15: platform-only wheel
The candidate/version exists but no artifact is compatible with the runtime.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

### RW-16: Requires-Python
The candidate exists, but runtime context makes it unusable.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

### RW-17: prerelease policy
pip and uv legitimately produce different outcomes from the same candidate set because prerelease policy differs.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

### RW-18: source-distinct same version
Candidate identity remains source-aware and artifacts remain separate.

**Classification: C — LOSSY BUT SAFE REPRESENTATION.**

## 7. False-proof attacks

The most important attacks were:

### Attack 1 — empty candidate list
Remove one source from a multi-index domain.

Expected:
`insufficient_evidence`, not `no candidate exists`.

Observed:
proof gate forbids the proof.

### Attack 2 — drop source authentication/query status
Use uv's 401/403 case but retain only the human-readable “not found” clause.

Expected:
`insufficient_evidence`.

Observed:
the completeness obligation is not satisfied.

### Attack 3 — drop activation marker
Take RW-07 and erase `sys_platform == "win32"`.

Expected:
unsafe normalization.

Observed:
the contract identifies the lost semantic condition; an UNSAT proof cannot be accepted without it.

### Attack 4 — drop artifact identity
Take platform/yank cases and keep only package/version.

Expected:
proof obligation fails for artifact-level claims.

Observed:
candidate/artifact separation prevents silent collapse.

### Attack 5 — drop prerelease policy
Use RW-17 with the same candidate set under pip default, pip `--pre`, uv default, and uv disallow.

Expected:
outcome cannot be normalized without policy.

Observed:
runtime context and policy are separate; the trace remains safe.

### Attack 6 — drop Requires-Python evidence
Use RW-05/RW-16 but remove the candidate's Python requirement.

Expected:
no-candidate or UNSAT conclusion is forbidden.

Observed:
missing evidence remains missing.

### Attack 7 — resolver rejection interpreted as exhaustive domain
Use a backtracking/rejection event as though it established source exhaustion.

Expected:
proof forbidden unless domain completeness is attested.

Observed:
proof gate rejects the inference.

## 8. Minimality verification

The independently normalized RW-14 problem produced:

`root:appa`  
`root:depB`  
`appa->depA`  
`depA1->leaf`  
`depB1->leaf`

The full five-constraint set was verified UNSAT.

For each element, the element was deleted and the reduced problem was verified SAT.

Therefore the reported explanation is:

**subset-minimal**

It is not claimed to be:
- minimum-cardinality;
- globally smallest;
- optimal under any resolver-specific cost metric.

## 9. Cross-resolver comparison

### pip vs uv: transitive conflict
Both fail the RW-14 reduction. uv provides a more explicit structured derivation chain; pip exposes a more human-oriented `ResolutionImpossible` explanation.

The semantic core does not require identical derivation objects.

### pip vs uv: prerelease
The same candidate set can resolve differently:
- pip default: prerelease excluded;
- pip `--pre`: accepted;
- uv 0.10.0 default: accepted;
- uv `--prerelease=disallow`: excluded.

A common trace must preserve policy rather than force identical outcomes.

### pip vs uv: artifact/platform
Both distinguish usable artifacts from package/version existence, although the diagnostics differ.

### pip vs uv: direct/VCS
Both can preserve a URL/source identity; pip's successful `--report` in the local reduction recorded the direct URL and VCS commit provenance. uv's resolver also pins URL/VCS identity, but its CLI exposure is structurally different.

### uv vs Poetry/pipgrip
uv, Poetry, and pipgrip use derivation-rich PubGrub/Mixology-family concepts. resolvelib/pip exposes provider criteria/cause relations rather than the same clause graph. The common semantic layer therefore normalizes literals/provenance while retaining resolver-specific derivations under namespace.

No identical trace is expected or required.

## 10. Failed cases and limitations

The following were not promoted to verified UNSAT proofs:
- pip #13760: decisive conflict evidence missing;
- pip #13260: normal output omits Requires-Python filtering details;
- uv #12362: source query can fail with authentication and masquerade as absence;
- VCS/constraint cases where source/build semantics are implementation-specific;
- yanked/artifact cases where resolver policy differs.

These are not failures of the contract. They are intended `insufficient_evidence` or namespaced-lossy outcomes.

## 11. D/E assessment

### D — unsafe normalization
One concrete unsafe normalization exists at the adapter level: flattening an inactive marker into an unconditional dependency and copying uv's native failure as a universal incompatibility. The revised contract prevents this by requiring activation conditions and independent semantic verification.

No contract-level unsafe normalization survived the proof gate.

### E — unrepresentable
No tested case forced a necessary semantic fact outside the revised model.

The hardest cases—source authentication failure, universal Python splits, partial per-file yanks, VCS identity, and marker-conditioned source selection—can all be represented as scoped evidence, policy/context, artifact identity, or namespaced resolver-specific data.

## 12. Schema revision decision

**No update to `research/REVISED_TRACE_SCHEMA.md` is required.**

The experiment found no new semantic defect in the revised contract.

The major lesson is operational rather than structural:
an adapter must not manufacture completeness, drop activation markers, or flatten resolver-specific derivations into universal clauses.

## 13. H2 interpretation

This experiment establishes additional technical evidence for:
- **H2a:** richer real-world structured evidence exists in resolver/provider layers;
- **H2b:** revised semantics remain safe across substantially more realistic cases;
- **H2c:** independent verification remains possible for a nontrivial transitive conflict;
- **H2d:** remains **UNPROVEN** because this experiment does not establish a stable public cross-resolver interchange API;
- **H2e:** remains **NOT TESTED** because there are **0 substantive maintainer responses**.

Technical feasibility, practical exposure, and maintainer validation remain separate gates.

## 14. Final technical judgment

**A. REAL-WORLD VALIDATION PASSES**

The revised contract survived the real-world corpus.

The important qualification is that “passes” means:
- no tested semantic defect forced another schema revision;
- independently verified UNSAT was possible on a nontrivial reduced case;
- incomplete evidence was correctly refused as proof;
- resolver-specific behavior was retained as namespaced/lossy rather than flattened unsafely;
- at least one real resolver failure that is satisfiable under the stated semantics was treated as a negative control rather than as UNSAT.

It does **not** mean:
- cross-ecosystem interchange is proven;
- all resolver evidence is publicly exposed;
- maintainer acceptance exists;
- production adapters are justified;
- ecosystem adoption exists.
