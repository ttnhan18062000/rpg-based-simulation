---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP
artifact_type: plan
tags: [simulation-quality, world, faction, corpus, calibration]
---

# plan.md — TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP

## Ordered Steps

1. **Authored a draft world** (`faction_dense_frontier`) per the ticket's original scope, resolved
   and compiled it, verified real populated-faction counts via `WorldCompiler.compile()`.
2. **Compared against the existing corpus** before calibrating anchors — found `crowded_frontier`
   and `generated_frontier_3_42` already close this exact gap, with the draft world's footprint
   identical to `generated_frontier_3_42`'s.
3. **Reverted all draft-world artifacts**: `data/worlds/faction_dense_frontier/`,
   `data/calibration/faction_dense_frontier_*`, the 3 anchor entries added to
   `grade_anchors.json`, and the `FAST_ANCHOR_KEYS`/entry-count edits to
   `test_grade_regression.py` — via `git checkout` (uncommitted) and manual directory removal
   (gitignored dirs).
   - Files reverted: `tests/simulation_quality/fixtures/grade_anchors.json`,
     `tests/simulation_quality/test_grade_regression.py` (both back to their last-committed state).
4. **Corrected `corpus_tier_taxonomy.md`'s stale gap-list section** — marked gap #1 CLOSED,
   explained the staleness, cited both worlds that already close it.
   - Files: `docs/simulation_quality/corpus_tier_taxonomy.md`.
5. **Fill this ticket's Completion Summary** documenting the finding and the decision not to ship
   a redundant world.

## Scope Guards

- Do NOT author a new world once the redundancy was confirmed — shipping a 3rd world with the
  same footprint as an existing one would be padding the corpus, not real coverage.
- Do NOT touch `crowded_frontier` or `generated_frontier_3_42` themselves — both are correct,
  already-anchored, already-committed worlds; this ticket only corrects documentation about them.

## Dependency Map

Step 2 depends on step 1. Step 3 depends on step 2's finding. Step 4 is independent, can run in
parallel with step 3.

## Acceptance Criteria Map

- AC1 (new world with 6-9 factions, small footprint) → **not met, deliberately** — found
  unnecessary; investigation.md documents why.
- AC2 (classified in corpus_tier_taxonomy.md as stress-tier) → N/A, no new world.
- AC3 (anchors committed, tests pass) → N/A, no new anchors; existing regression suite unaffected
  (verified identical pass/fail counts before and after revert).
- AC4 (gap #1 entry marked closed, citing this ticket) → Step 4, citing the 2 pre-existing worlds
  and this ticket for the correction.

No unresolved questions requiring human review.
