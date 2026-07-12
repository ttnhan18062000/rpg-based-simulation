---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260712-SIMQ-DUNGEON-URBAN-ANCHOR-DRIFT
phase: open
date: 2026-07-12
tags: [simulation-quality, corpus, calibration]
---

# TCK-20260712-SIMQ-DUNGEON-URBAN-ANCHOR-DRIFT

## Title
`dungeon_crawl_seed42_200t` (COMBAT, PROGRESSION) and `urban_political_seed42_200t`
(PROGRESSION) grade anchors no longer match live engine output — pre-existing drift,
unrelated to SOCIAL activation

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Discovered during `TCK-20260710-SIMQ-DEPTH-SOCIAL`'s required Step 3 full corpus regression
sweep (`python3 tools/evaluate_simq.py`, the non-`--dry-run` `make evaluate-full` equivalent).
That ticket's own scope only touches `config/simulation_quality/profiles/{frontier_living_world,
highland_traverse}.yaml` and the corresponding 6 `grade_anchors.json` entries — `dungeon_crawl`
and `urban_political` profiles were confirmed zero-diff throughout. The sweep nonetheless
reported 3 REGRESS pillars, all in these two untouched worlds:

```
dungeon_crawl_seed42_200t      COMBAT        A -> C   REGRESS
dungeon_crawl_seed42_200t      PROGRESSION   A -> C   REGRESS
urban_political_seed42_200t    PROGRESSION   A -> C   REGRESS
```

Reproduced independently and deterministically outside the sweep via standalone
`python3 tools/calibrate_simq.py --name dungeon_crawl --seed 42 --ticks 200` and
`--name urban_political --seed 42 --ticks 200` runs (both against untouched, currently-committed
profile YAML) — same grades both times, so this is not run-to-run flakiness, it is a real,
repeatable mismatch between the committed anchors and current live engine behavior.

Likely cause (not confirmed, needs investigation): `git log` shows the most recent commits
touching these two worlds are `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` and
`TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC` (population-collapse fixes for exactly these two worlds).
The anchors currently on disk (COMBAT=A/PROGRESSION=A for both) most likely predate one of those
fixes' behavioral change and were never re-verified against a fresh calibration run after it
landed.

## Scope
- Investigate whether the COMBAT/PROGRESSION event-count drop in `dungeon_crawl_seed42_200t` and
  `urban_political_seed42_200t` is (a) a legitimate anchor staleness (engine behavior changed for
  a documented, correct reason — anchors just need updating) or (b) an actual regression
  introduced by the population-collapse fix commits.
- If (a): update the affected anchor fields in `tests/simulation_quality/fixtures/grade_anchors.json`
  to match live output, with `v2_evidence`/commit citation for why the change is legitimate.
- If (b): fix the regression in the relevant engine/content code.

## Out of Scope
- Any world/profile outside `dungeon_crawl` and `urban_political`.
- `TCK-20260710-SIMQ-DEPTH-SOCIAL`'s own SOCIAL-pillar work — this drift is confirmed unrelated
  (both worlds' profile YAML and calibration mechanism are untouched by that ticket; reproduced
  standalone with zero relation to `ENABLE_SOCIAL_COOPERATION`).

## Acceptance Criteria
- [ ] Root cause identified (stale anchor vs. real regression).
- [ ] `make evaluate` / `make evaluate-full` shows 0 REGRESS for `dungeon_crawl_seed42_200t` and
      `urban_political_seed42_200t`.

## Related Tickets
- `TCK-20260710-SIMQ-DEPTH-SOCIAL` (done) — discovered this drift during its Step 3 corpus sweep;
  did not fix it (out of scope for that ticket, which only touches `frontier_living_world`/
  `highland_traverse`).
- `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` (done) — most likely source of the behavioral
  change; needs re-verification against its own anchor updates.

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md`

## Related Stored Artifacts
None yet — filed directly from a sibling ticket's Verify-phase finding, hotfix tier.

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json` (`dungeon_crawl_seed42_200t`,
  `urban_political_seed42_200t` entries)
- `data/worlds/dungeon_crawl/`, `data/worlds/urban_political/`

## Assumptions / Open Questions
- Not yet confirmed which of the two recent population-collapse-fix commits caused the drop, or
  whether it's a third, unrelated cause — flagged for Investigate, not assumed here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
