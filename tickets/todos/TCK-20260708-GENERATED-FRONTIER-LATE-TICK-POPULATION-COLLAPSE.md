---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE
phase: open
date: 2026-07-08
tags: [simulation-quality, world, corpus, calibration]
---

# TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE

## Title
`generated_frontier_3_42` collapses below the 60%-alive floor between tick 800 and tick 1000 (seed 42)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS` established `generated_frontier_3_42`'s
first-ever 1000-tick calibration data point (Step 5, an ad hoc population cross-check extending
past `test_population_stability`'s existing 300-tick scope). Driving `WorldCompiler.compile` →
`Kernel.tick_once()` to 1000 ticks at seed 42 and sampling `alive_count` every 100 ticks against the
60%-alive-of-starting-44 floor (26.4), population **holds** through tick 800 (81.8% → 79.5% → 65.9%
→ 70.5% → 63.6%, all above floor) but then **collapses** between tick 800 and tick 1000: 28/44
(63.6%) at tick 800 → 15/44 (34.1%) at tick 900 → 4/44 (9.1%) at tick 1000 — well below the 60%
floor at both the 900 and 1000 checkpoints. This correlates with 6 `entity_killed` COMBAT events
observed at ticks 982–1000 in the same 1000t calibration report, though the checkpoint data shows
erosion beginning by tick 900, earlier than those specific worst-events entries suggest.

This is a genuine new finding, not previously known: `generated_frontier_3_42` was previously absent
from `KNOWN_POPULATION_COLLAPSE_WORLDS` (`tests/unit/worldassembly/test_corpus_diversity.py`), and
`test_population_stability` only runs to 300 ticks, so this late-tick collapse (800→1000) was never
previously exercised or observed. It is a different failure shape than either
`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`'s `dungeon_crawl` (early-tick, fails by tick 50) or
`urban_political` (gradual erosion across the full 300-tick window) patterns — this world holds
comfortably through 800 ticks then collapses sharply in the final 200, a distinct late-cliff shape
that must not be assumed to share either of those root causes.

`TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS` is scoped to establishing calibration
anchors only (no content/config fixes), so it documented the finding and landed the 1000t anchor
reflecting the world's actual measured behavior (collapse included), per that ticket's
evidence-first convention, rather than fixing or silently excluding it. This ticket is the actual
root-cause investigation and fix.

## Scope
1. Investigate why `generated_frontier_3_42` collapses between tick 800 and tick 1000 at seed 42 —
   check faction hostility/military-conflict config, `moon_cult_ruins` module content, and whether
   the 6 `entity_killed` COMBAT events at ticks 982–1000 are cause or symptom of the earlier
   (tick 800–900) erosion onset.
2. Determine whether this is a late-tick variant of an existing known pattern or a genuinely
   distinct root cause specific to this world's content composition.
3. Fix the genuine content/config gap (or engine-level shared cause, if found and confirmed), then
   add a `test_population_stability`-style regression guard extended to at least tick 1000 for this
   world (the existing test only checks to tick 300, which would not have caught this).

## Out of Scope
- `dungeon_crawl` / `urban_political` — already tracked by
  `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`; do not duplicate that investigation here.
- Extending `test_population_stability`'s 300-tick window for every other corpus world — scope this
  fix/guard to `generated_frontier_3_42` only unless the root cause is proven to be a shared,
  corpus-wide mechanism.

## Acceptance Criteria
- [ ] Root cause identified for the tick 800→1000 collapse (document whether shared with the
      `DUNGEON-URBAN` ticket's findings or genuinely distinct).
- [ ] Fix applied (content/config, or engine fix if a shared cause is found and confirmed).
- [ ] A regression guard (extended-window population-stability test or equivalent) exists for
      `generated_frontier_3_42` covering at least tick 1000, and passes cleanly.
- [ ] `data/calibration/generated_frontier_3_42_seed42_1000t/quality_report.json` and the
      corresponding `grade_anchors.json` entry are re-verified (or re-generated) once the fix lands,
      since the anchor was established pre-fix and reflects the collapse.

## Related Tickets
- TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS — established the 1000t calibration data
  that surfaced this finding; landed the anchor reflecting pre-fix (collapse-included) behavior.
- TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE — analogous population-collapse investigation for
  `dungeon_crawl`/`urban_political`, different failure shapes; use as a methodology precedent, not
  an assumed shared root cause.

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — "generated_frontier_3_42 — first-ever grade
  anchors" section, Population-health finding subsection (source of this ticket).
- `docs/mechanics/02_combat_laws.md`, `docs/mechanics/03_economic_laws.md` — likely relevant laws
  depending on root cause (combat attrition vs. economic starvation).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS/` — where this was found.

## Related Code Areas
- `data/worlds/generated_frontier_3_42/`, `data/content/world_modules/moon_cult_ruins.yaml`
- `tests/unit/worldassembly/test_corpus_diversity.py`

## Assumptions / Open Questions
- Unconfirmed whether the tick 982–1000 `entity_killed` COMBAT events are the cause of the collapse
  or a downstream symptom of erosion that began by tick 900 — investigation must trace this rather
  than assume causality from temporal correlation alone.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
