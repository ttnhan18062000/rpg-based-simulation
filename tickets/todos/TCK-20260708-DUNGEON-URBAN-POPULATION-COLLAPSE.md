---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE
phase: open
date: 2026-07-08
tags: [simulation-quality, world, corpus, calibration]
---

# TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE

## Title
`dungeon_crawl` and `urban_political` fail `test_population_stability`'s 60%-alive floor at seed 42/300 ticks

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP` extended `test_population_stability`'s
`POPULATION_STABILITY_WORLDS` (and `test_hazard_kind_completeness`'s new
`HAZARD_KIND_COMPLETENESS_WORLDS`) to cover `dungeon_crawl`, `sandbox_world`,
`generated_frontier_3_42`, and `urban_political` — 4 compiled corpus worlds that previously had
neither test running against them at all. Per that ticket's scope, adding coverage is required to
surface genuine defects, not paper over them; running the newly-added worlds through both tests at
seed 42 found:

- `sandbox_world` and `generated_frontier_3_42`: both tests pass cleanly.
- `dungeon_crawl`: **fails** `test_population_stability` at the very first checkpoint (tick 50) —
  `alive=14/32 (43.8%)` against a 60% (19.2) floor. This is an early-tick collapse matching the
  same failure shape as `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md`
  Finding 3 (the bug `test_population_stability` was originally written to guard against).
- `urban_political`: **fails** `test_population_stability` at the last checkpoint (tick 300) —
  `alive=17/30 (56.7%)` against a 60% (18.0) floor, a narrow 1-entity miss late in the run (not an
  early collapse — population erodes gradually over the full 300 ticks rather than crashing early).
- Both worlds pass `test_hazard_kind_completeness` cleanly, so the immediate cause is not a missing
  `hazard_kind`/`hazard_immunities` declaration (that class of bug is ruled out) — the collapse is
  either a genuine combat/economy/attrition balance gap in these two worlds' content, or a shared
  mechanic issue that the 8 previously-covered worlds happen not to trigger.

`TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP` is scoped test-coverage-only (no
FACTION/INFORMATION/AGENCY or other content changes), so it added the coverage, confirmed both
failures are genuine (not a coverage-list mistake), and marked both parametrize cases
`@pytest.mark.xfail(strict=True, ...)` pointing at this ticket rather than silently excluding them
or leaving the suite red. This ticket is the actual root-cause investigation and fix.

## Scope
1. Investigate why `dungeon_crawl` collapses below the 60% floor by tick 50 (early-tick pattern —
   check faction hostility/military-conflict config, starting entity roster balance, and whether
   any content gap mirrors Finding 3's root cause).
2. Investigate why `urban_political` erodes below the 60% floor by tick 300 (late/gradual pattern —
   likely a different root cause than `dungeon_crawl`'s; do not assume they share one fix).
3. Fix each world's genuine content/config gap (or engine-level shared cause, if the investigation
   finds one), and remove the `xfail` markers added by
   `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP` once each world passes
   `test_population_stability` cleanly.

## Out of Scope
- `sandbox_world` / `generated_frontier_3_42` — already pass cleanly, no action needed.
- Re-litigating `test_hazard_kind_completeness` coverage — both worlds already pass it.

## Acceptance Criteria
- [ ] Root cause identified for `dungeon_crawl`'s early-tick collapse and `urban_political`'s
      late-tick erosion (documented separately — different failure shapes).
- [ ] Fix applied (content/config, or engine fix if a shared cause is found and confirmed).
- [ ] `test_population_stability[dungeon_crawl]` and `test_population_stability[urban_political]`
      pass without `xfail`; the `xfail` markers in `tests/unit/worldassembly/test_corpus_diversity.py`
      are removed.

## Related Tickets
- TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP — added the coverage that surfaced this;
  added the `xfail` markers this ticket must remove once fixed.
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — origin of `test_population_stability` and Finding 3, the
  early-tick collapse pattern `dungeon_crawl`'s failure resembles.

## Related Docs
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/investigation.md` — Finding 3.
- `docs/mechanics/02_combat_laws.md`, `docs/mechanics/03_economic_laws.md` — likely relevant laws
  depending on root cause (combat attrition vs. economic starvation).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP/` — where this was found.

## Related Code Areas
- `data/worlds/dungeon_crawl/`, `data/worlds/urban_political/`
- `tests/unit/worldassembly/test_corpus_diversity.py`

## Assumptions / Open Questions
- Unconfirmed whether `dungeon_crawl` and `urban_political`'s failures share a root cause or are
  independent — the differing failure shapes (early crash vs. late erosion) suggest independent
  causes; investigation must verify rather than assume.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
