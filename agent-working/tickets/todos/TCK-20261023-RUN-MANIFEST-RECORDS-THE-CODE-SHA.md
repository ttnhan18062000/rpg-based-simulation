---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261023-RUN-MANIFEST-RECORDS-THE-CODE-SHA
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-RUN-MANIFEST-RECORDS-THE-CODE-SHA

## Title
run_manifest.json records the code sha (and a dirty flag) of the tree the kernel imports from, so a comparison tool can refuse a run from the wrong code

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Finding from testing-planner (2026-10-23), found by testing-implementer while proving the SimQ re-anchor pairs ran on the pinned v1 tree 341f700d0: `run_manifest.json` records engine_version 2.0.0 but no commit or code sha. The proof had to come from the process cwd. Comparison tools (simq_reanchor, simq_pillar_compare, the rpg gate candidate, paired.py) can check host-independence from the manifest (audit_mode, signals_zeroed; src/observability/reporting/run_determinism.py) but not which code produced the run, so a run from the wrong tree passes silently.

## Scope
1. RunManifest (written by the kernel, src/engine/kernel.py ~184/388) gains `code_sha` (git HEAD of the tree the kernel's `src` package is imported from) and `code_dirty` (bool), typed like audit_mode / signals_zeroed; both None when not in a git tree. Computed once at kernel build, never per tick, and never read by simulation logic (not hashed state).
2. A helper in run_determinism.py to read it (None for older manifests).

## Out of Scope
Refusal logic in testing's tools (a separate testing ticket once this lands). Gate candidate provenance (TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE).

## Acceptance Criteria
- A run in a git worktree records its HEAD sha and dirty flag; outside git both are None (tests).
- No change to the simulation: paired --neutral IDENTICAL on one step; the state hash is unchanged.

## Related Tickets
TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE; TCK-20261023-PAIRED-WRITES-ONE-RUN-LEDGER-ROW-PER-INVOCATION.

## Related Docs
docs/engine/kernel.md (manifest); docs/engine/performance_contract.md.

## Related Stored Artifacts

## Related Code Areas
src/engine/kernel.py; src/observability/reporting/run_determinism.py; src/lab/repository.py.

## Assumptions / Open Questions
- Use the import path of `src` (not cwd) to find the tree.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
