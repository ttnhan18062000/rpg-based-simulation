---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP
artifact_type: test_plan
tags: [simulation-quality, progression]
---

# Test Plan: TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP

## Scope
EXPLORE quest metadata population and completion only, per the narrowed scope in plan.md.

## New/updated tests — `tests/unit/quest/test_quest_generation.py`

| Test | Behavior verified |
|---|---|
| `test_explore_quest_gets_target_pos_when_origin_given` | An EXPLORE-kind quest generated with `origin_pos` carries `metadata["target_pos"]` within `[_EXPLORE_TARGET_MIN_DIST, _EXPLORE_TARGET_MAX_DIST]` tiles of `origin_pos` |
| `test_explore_quest_target_pos_deterministic` | Same `(seed, level, tick, origin_pos)` produces the identical `target_pos` across two calls |
| `test_explore_quest_without_origin_pos_has_no_target_pos` | `origin_pos=None` (default, matching pre-existing callers) leaves `metadata` without a `target_pos` key — same as before this fix, not silently different |
| `test_non_explore_quest_has_empty_metadata_regardless_of_origin` | A non-EXPLORE quest (forced via level 15 → TIER 3) gets `metadata == {}` even when `origin_pos` is given — the target-pos computation is EXPLORE-only |
| `test_evaluate_explore_completes_quest_once_entity_reaches_target_pos` | End-to-end: a real generated `target_pos`, entity placed exactly there, `QuestResolutionSystem.evaluate_explore()` returns a `QuestUpdate` with `progress_delta >= goal_value` |
| `test_evaluate_explore_does_not_complete_quest_far_from_target_pos` | Same setup, entity far from `target_pos` → `evaluate_explore()` returns no updates |

## Regression coverage
- Full existing `tests/unit/quest/test_quest_generation.py` suite (25 tests total after this
  change) re-run to confirm no existing determinism/level-banding/pressure-weighting test broke.
- `tests/unit/world/test_guild_pipeline.py`, `tests/unit/world/test_guild_intel.py` — `GuildAction`
  callers, to confirm the new `origin_pos` kwarg doesn't break existing guild-visit behavior.
- `tests/unit/ai/test_guild_need_scorer.py`, `tests/unit/engine/test_guild_visit_phase.py`,
  `tests/architecture/test_guild_action_dormancy.py` — the sibling ticket's own test suite, to
  confirm this change doesn't regress the guild-wiring path that calls `generate_quests()`.

## Out of scope for this test plan
- GATHER/BOUNTY/LIBERATE evaluators — not implemented in this pass.
- HUNT metadata/matching — not implemented in this pass; its own gap is documented in
  investigation.md and tracked by the new follow-up ticket
  `TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP`.

## Results
All listed tests pass (25/25 in `test_quest_generation.py`; 79/79 across
`test_guild_pipeline.py` + `test_guild_intel.py` + `test_quest/`; 88/88 across the sibling
ticket's own guild-scorer/guild-phase/architecture-guard suite). No pre-existing failures observed
in this scope (unlike the sibling `QUEST-EVENT-TYPE-FILTER-BUG` ticket's unrelated
`test_balance_regression.py` failure, which does not intersect this ticket's changed files).
