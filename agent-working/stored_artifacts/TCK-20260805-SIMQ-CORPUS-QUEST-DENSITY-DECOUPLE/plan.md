---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE
artifact_type: plan
tags: [simulation-quality, world, progression, corpus, calibration]
---

# plan.md — TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE

## Ordered Steps

1. **Verify gap #5 against real corpus data** before authoring anything — confirmed genuinely open
   (unlike gaps #1/#2), ratio range 0.19-0.64 with no deliberately-authored outlier.
2. **Author, resolve, compile a draft world** (frontier_village_core + 3 zero-population terrain
   modules) — 13 entities/7 quests/ratio 0.538 — found insufficient (below `wilderness_survival`'s
   incidental 0.636).
3. **Redesign using a smaller standalone population base** (`ruins_mystery_quest` instead of
   `frontier_village_core`) — 6 entities/6 quests/ratio 1.0, genuinely beyond the corpus's prior
   maximum.
   - Files: `data/worlds/quest_dense_frontier/world.yaml`.
4. **Calibrate 3 seeds (42/123/456, 200t)**, commit anchors.
   - Files: `tests/simulation_quality/fixtures/grade_anchors.json`,
     `tests/simulation_quality/test_grade_regression.py` (`FAST_ANCHOR_KEYS`, entry-count test).
5. **Classify and document** in `corpus_tier_taxonomy.md` — new per-world table row, gap #5 marked
   CLOSED in the gap-list section.
   - Files: `docs/simulation_quality/corpus_tier_taxonomy.md`.
6. **Fill this ticket's Completion Summary.**

## Scope Guards

- Do NOT fix `river_crossing`'s pre-existing quest-tag mismatch (`survey_river_route` requires a
  `river` tag its own region doesn't declare) — confirmed pre-existing (already affects the
  shipped `highland_traverse` world), a shared-module content bug out of this ticket's scope.
- Do NOT author new module content — this ticket only composes existing modules.

## Dependency Map

Step 3 depends on step 2's finding (insufficient ratio). Step 4 depends on step 3. Step 5 is
independent, can run in parallel with step 4.

## Acceptance Criteria Map

- AC1 (new world with density decoupled) → Step 3, verified via real compile data.
- AC2 (classified in corpus_tier_taxonomy.md) → Step 5.
- AC3 (anchors committed, tests pass) → Step 4, verified 68/69 pass (1 pre-existing unrelated
  failure).
- AC4 (gap #5 entry marked closed, citing this ticket) → Step 5.

No unresolved questions requiring human review.
