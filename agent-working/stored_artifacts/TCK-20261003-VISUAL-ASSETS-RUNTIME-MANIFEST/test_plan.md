---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST
artifact_type: test_plan
tags: [architecture, rendering, determinism, testing]
---

# Test Plan — TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST

Contract rejections (unknown fields, non-derived and malformed `file`, duplicate/unsorted keys, oversize dimensions, versions, key count); exact allowed field names and no provenance text; each refusal with a catalog and output-parent snapshot and (for output problems) proof that `verify` did not run first; determinism; failure while writing and an output appearing mid-export; CLI exit codes; committed fixture equals a fresh regeneration and the three alpha masks differ; boundary row and planted server import. Mutants: verify skipped, inside-catalog check removed, symlink-blind exists check, pixel-hash check removed, no cleanup on failure, file derivation unchecked, registry hash unchecked, a changed generator (stale fixture), two identical shapes.

## Proof Plan

- Level: unit, with a committed fixture regeneration check.
- Proof kind: executable tests plus recorded mutants.
- Oracle source: the ticket's acceptance criteria and `docs/assets/store_contract.md`.
- Expected effect: tests pass on the tree and each mutant fails its named test.
- Selected commands: `pytest tests/visual_assets` (without Aseprite); `make visual-assets-aseprite-local`; `pytest tests/static tests/architecture tests/docs`.
