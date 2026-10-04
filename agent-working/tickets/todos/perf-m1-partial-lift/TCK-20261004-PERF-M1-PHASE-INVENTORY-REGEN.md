---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-M1-PHASE-INVENTORY-REGEN
phase: open
date: 2026-10-04
tags: [performance, testing]
---

# TCK-20261004-PERF-M1-PHASE-INVENTORY-REGEN

## Title
Regenerate the stale committed phase inventory and stop it going stale silently

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
`python3 tools/perf/phase_inventory.py --check docs/performance/phase_inventory.json` exits 1 on
`origin/main` `9793aee08`. perf-planner diffed the live output against the committed file on
2026-10-04. Only the `documented_sources` half differs: `docs/engine/authoritative_pipeline.md` no
longer states a count in its heading (`stated_count` 39 → `null`, changed by
`TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT`). The code half (the `run_phase()` calls in
`AuthoritativeApplyPipeline.refine`) still matches `main`. Nothing failed, because no test or CI
job runs the `--check`. The RPG-core handoff (`rpg_core_handoff.md`, Ask 2) tells RPG-core sessions
to compare against this file, so it has to be current.

## Scope
- Regenerate `docs/performance/phase_inventory.json` and `docs/performance/phase_inventory.md` with
  the tool (never by hand)
- Check `tools/perf/hash_callsite_inventory.py --check` and `tools/perf/wall_clock_inventory.py --check`
  against their committed JSON; regenerate any that drifted and record which
- Add a fast test (in `tests/tools/`) that runs each of the three inventories' `--check` against its
  committed JSON, so drift fails the tools CI job instead of passing silently. If an inventory reads
  the whole of `src/` and takes more than a few seconds, mark that test `slow` and say so in the
  ticket instead

## Out of Scope
- Any `src/` edit
- Changing what the inventories count or how they render
- The PERF-D6 phase catalog itself (gated: `src/engine/`)

## Acceptance Criteria
1. All three `--check` commands exit 0 on the branch head
2. A test fails when a committed inventory JSON differs from the live output (proved once by
   editing a committed value locally, then reverting the edit)
3. The ticket records which inventories drifted and why

## Related Tickets
- `TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT` (caused the documentation-half drift)
- `TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY`

## Related Docs
- `docs/performance/phase_inventory.md`
- `docs/plans/design_enhancement/performance_optimization/rpg_core_handoff.md` (Ask 2)
- `docs/architecture/performance_optimization_decisions.md` (PERF-D6)

## Related Stored Artifacts
- none

## Related Code Areas
- `tools/perf/phase_inventory.py`, `tools/perf/hash_callsite_inventory.py`, `tools/perf/wall_clock_inventory.py`
- `docs/performance/*.json`

## Assumptions / Open Questions
- The inventories embed a source commit id in their markdown header. If that makes `--check`
  fail after every unrelated commit, the check must compare only the content fields. Verify this
  before adding the test

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
