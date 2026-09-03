---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS
phase: open
date: 2026-09-03
tags: [content, determinism]
---

# TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS

## Title
All 21 worlds' committed world_compile_report.json baselines are stale (last regenerated 2026-08-14, 83 commits ago) with no process to prevent recurrence

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Found while implementing `TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT` (idea 66): every one of the 21
worlds' `data/worlds/*/world_compile_report.json` files was last committed in the **exact same single
commit** (`29d78798`, "Simulation quality (#20)", 2026-08-14) — confirmed directly via `git log --oneline
-1 -- data/worlds/<world>/world_compile_report.json` for `dungeon_crawl`, `wilderness_survival`,
`urban_political`, and `hero_guild_routing`, all pointing to the same commit. 83 commits have landed on
`main` since then (M2's 15-ticket batch, M3's Reproduction epic, numerous hardening/hotfix tickets), none
of which regenerated these fixtures.

Confirmed via direct recompile that at least 3 of the 21 worlds (`dungeon_crawl`, `wilderness_survival`,
`urban_political`) no longer reproduce their committed `state_hash` with the committed seed — likely all
21 are equally affected, since they share the same generation commit and the same 83-commit gap.

**Not a determinism bug**: independently verified the compiler itself is fully reproducible (recompiling
identical content twice in a row with the same seed produces identical hashes every time). The staleness
is purely a fixture-maintenance gap.

**Not currently causing any failures**: checked every test that reads `world_compile_report.json`
(`tests/tools/test_corpus_registry.py`, `tests/unit/worldassembly/test_corpus_diversity.py`,
`tests/certification/test_world_compile_determinism.py`) — none of them recompile and compare
`state_hash` against a fresh build; they only consume other fields (entity counts, faction diversity,
corpus registry metadata). This drift has been silent and consequence-free until idea 66's own
Recalibration ticket (`TCK-20260902-PLACE-MIGRATION-RECALIBRATION`) planned to rely on these baselines
being trustworthy comparison points — which surfaced the gap.

## Scope
- Decide the fix direction:
  1. Batch-regenerate all 21 worlds' `world_compile_report.json` (and `resolved/` assets where
     applicable) against current `main`, bringing them back in sync.
  2. Add a process/CI gate that either regenerates these fixtures automatically or fails a check when
     they drift out of sync with a fresh recompile (mirrors the parity-ledger/registry
     regeneration-on-close pattern this repo already uses elsewhere).
  3. Some combination — regenerate now, then add the gate so it doesn't recur.
- Whichever direction is chosen, confirm which of the 21 worlds are actually affected (spot-checked 3,
  all failed — full 21-world confirmation not yet done, in scope for whoever picks this up).

## Out of Scope
- Idea 66's own migration work (`TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT` and onward) — those tickets
  work around this via a "fresh baseline" comparison method (recompile unchanged content once, use that
  as the reference point) rather than waiting on this fix, since nothing currently depends on the old
  committed hashes being accurate.
- Root-causing *why* specific worlds' compiled state changed field-by-field across the 83 commits (a
  real but much larger investigation, likely spanning M2/M3's own behavior changes) — this ticket is
  about regenerating stale fixtures and preventing recurrence, not auditing every historical diff.

## Acceptance Criteria
- [ ] All 21 worlds confirmed either stale or current (not just the 3 spot-checked here).
- [ ] A decision is recorded on the fix direction (regenerate, add a gate, or both).
- [ ] If regenerated: every world's `world_compile_report.json` reproduces on a clean recompile with its
      committed seed, verified directly (not assumed).
- [ ] If a gate is added: it's wired into the same "After Work"/CI checklist pattern this repo already
      uses for `docs/REGISTRY.yaml` and the parity index, so it doesn't silently drift again.

## Related Tickets
- TCK-20260902-PLACE-MIGRATION-STAGE-A-PILOT (where this was discovered)
- TCK-20260902-PLACE-MIGRATION-RECALIBRATION (blocked on this ticket's own methodology being trustworthy,
  though it can proceed today using the fresh-baseline workaround)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md` (Recalibration procedure
  section, whose "diff against committed baseline" premise this ticket's finding affects)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `data/worlds/*/world_compile_report.json` (all 21)
- `data/worlds/*/resolved/*` (may also be stale, not independently confirmed)
- `tests/tools/test_corpus_registry.py`, `tests/unit/worldassembly/test_corpus_diversity.py` (consumers
  that would benefit from a freshness gate)

## Assumptions / Open Questions
- Whether a full 21-world regeneration should happen as one batch ticket or be folded into idea 66's own
  Recalibration work (which will be recompiling most/all of these worlds anyway) — worth checking
  Recalibration's actual progress before deciding, to avoid duplicate compile passes.
- What specifically changed across the 83 commits to cause the drift (M2/M3 behavior changes are the
  most likely candidates, given their scale) — not required to answer before regenerating, but useful
  context for anyone auditing individual field-level diffs later.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
