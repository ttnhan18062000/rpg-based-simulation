---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-PERF-M1-PHASE-INVENTORY-REGEN
phase: done
date: 2026-10-04
tags: [performance, testing]
---

# TCK-20261004-PERF-M1-PHASE-INVENTORY-REGEN

## Title
Regenerate the stale committed phase inventory and stop it going stale silently

## Status
DONE

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

- Owner decision 2026-10-04 (relayed by perf-planner): the new check stays blocking in the Tools CI job, so replace the "None of these checks runs in CI yet" paragraph under the Ask 2 table of `rpg_core_handoff.md` with a dated note giving the regeneration commands (copied from the `.md` headers) and the PERF-D1 A1 reminder

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
- `docs/plans/design_enhancement/performance_optimization/rpg_core_handoff.md` (Ask 2 note, added 2026-10-04)

## Assumptions / Open Questions
- The inventories embed a source commit id in their markdown header. If that makes `--check`
  fail after every unrelated commit, the check must compare only the content fields. Verify this
  before adding the test

## Implementation Notes
- Drift found: only `phase_inventory` (`--check` exit 1). `hash_callsite_inventory` and `wall_clock_inventory` both exit 0, so neither was regenerated.
- Cause: `TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT` removed the stated phase count from `docs/engine/authoritative_pipeline.md`'s heading, the generator note and the epic prose. The tool now reports `stated_count`/`stated_in` as null for those three sources (39/39/37 before). The code half is unchanged.
- Regenerated with the tool (`--format json` / `--format md`, `--source-commit` = the branch base `262d7e57b`), not by hand. The md header commit id moved from `fdc44f958` to `262d7e57b`.
- `--check` ignores line numbers and the embedded commit id, so the new test does not fail on unrelated commits. Verified: the other two checks passed with older commit ids.
- New `tests/tools/test_perf_inventories_committed_in_sync.py`: one parametrized case per inventory, plus a guard that an edited committed value exits 1. Whole file takes about 10 s, mostly `wall_clock_inventory` (about 5 s), so it is not marked `slow`; a `slow` mark would drop it from the CI tools job (`-m "not slow and not extra_slow"`), which defeats the purpose.

## Test Summary
- `pytest tests/tools/test_perf_inventories_committed_in_sync.py tests/tools/test_phase_inventory.py`: 34 passed.
- Proof (AC2): with the old stale `phase_inventory.json` restored, the `[phase_inventory]` case fails; with the regenerated file it passes.
- All three `--check` commands exit 0 on the branch.

## Files Changed
- `docs/performance/phase_inventory.json`, `docs/performance/phase_inventory.md` (regenerated)
- `tests/tools/test_perf_inventories_committed_in_sync.py` (new)
- `docs/plans/design_enhancement/performance_optimization/rpg_core_handoff.md` (Ask 2 paragraph replaced by a dated note; the memory-cap sentence is kept)
- `docs/REGISTRY.yaml` (regenerated)

## Completion Summary
The stale `phase_inventory` report is regenerated and a blocking Tools CI test now fails when any of the three inventories drifts. Only `phase_inventory` had drifted. The handoff doc now tells RPG-core sessions the check is blocking, with the regeneration commands. All three `--check` commands exit 0, the new test file and `tests/docs` pass, and there were no `src/` edits.
