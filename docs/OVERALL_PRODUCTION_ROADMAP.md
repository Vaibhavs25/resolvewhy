# Overall production roadmap

## Current boundary

Resolvewhy is a bounded, independently checked semantic verifier. It is not a
general package resolver and does not claim universal compatibility with pip,
uv, Poetry, or the full PEP 508 grammar.

The current trace write contract is `resolvewhy-trace/1.1`. It adds explicit
requested extras, candidate declared-extra metadata, and optional-edge extra
context. The decoder still reads strict fieldless `resolvewhy-trace/1.0`
traces, where absent extras fields mean no requested extras and *missing*
candidate declaration metadata; they do not mean authoritative empty
declarations. Historical `1.0` traces remain `1.0` when reserialized. New
extras-aware data must identify itself as `1.1`.

## Completed in this increment

- Validate every active requested extra against the selected candidate outside
  optional-edge enumeration, so an omitted optional edge cannot make an
  undeclared extra appear verified.
- Keep complete-empty, unknown, and missing declared-extra evidence distinct.
  An undeclared extra and absent/unreadable metadata all lead to typed
  non-verified results, not a fabricated contradiction proof.
- Support finite fixed-point activation for the implemented simple optional
  extra contexts, including multi-request, transitive, and cyclic tests.
- Preserve the tested compatible-release normalizations and make unsupported
  compatible forms with extras explicitly incomplete.

## Remaining work

- Broaden only after a semantic model and adversarial corpus establish the
  intended PEP 508 extra-marker combinations, dynamic metadata behavior, and
  resolver-specific semantics.
- Obtain fresh commit-specific CI, packaging, security-audit, and cross-version
  evidence before any release decision.
- Do not describe these bounded results as full PEP 508 support or as proof of
  arbitrary resolver outcomes.
