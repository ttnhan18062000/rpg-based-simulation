---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP
artifact_type: test_plan
tags: [simulation-quality, progression]
---

# Test Plan: TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP

## New tests — `tests/unit/quest/test_quest_generation.py`

| Test | Behavior verified |
|---|---|
| `test_wolf_hunt_quest_gets_real_target_kind` | `q_wolf_hunt` quests carry `metadata["target_kind"] == "wolf"` |
| `test_slime_cull_quest_has_no_target_kind` | `q_slime_cull` quests never carry a `target_kind` key (deliberately, no real content) |
| `test_evaluate_combat_victory_completes_wolf_hunt_quest_on_matching_kill` | A "wolf" kill produces a `QuestUpdate` completing progress |
| `test_evaluate_combat_victory_does_not_progress_wolf_hunt_quest_on_unrelated_kill` | A "goblin" kill against the same quest produces zero updates |
| `test_wolf_hunt_quest_reaches_completed_status_through_real_kill_loop` | Full real lifecycle: `generate()` → `evaluate_combat_victory()` → `QuestService.add_progress()` reaches `QuestStatus.COMPLETED` after real repeated kills |

## Regression coverage
- Full `tests/unit/quest/` suite (30 tests after this change) re-run to confirm no existing
  determinism/level-banding/pressure-weighting/EXPLORE test broke.
- `tests/unit/world/test_guild_pipeline.py`, `tests/unit/world/test_guild_intel.py`,
  `tests/unit/ai/test_guild_need_scorer.py`, `tests/unit/engine/test_guild_visit_phase.py`,
  `tests/architecture/test_guild_action_dormancy.py` — guild-wiring callers of the changed
  generator, to confirm no regression in the sibling ticket's own live-dispatch path.
- `tests/unit/entities/test_entity_identity_resolver.py` — unaffected (this fix uses
  `EntityState.kind`/`race_id`, not `EntityIdentityResolver`, but included as a sanity check
  since the investigation explicitly distinguished the two).

## Results
`tests/unit/quest/`: 30/30 pass. Wider sweep (guild pipeline/intel/scorer/phase/architecture-guard
+ identity resolver): 106/106 pass. No pre-existing or new failures.

## Out of scope for this test plan
- `q_slime_cull` — remains untested for completion (there is nothing to test; it stays
  permanently uncompletable by design, disclosed not fixed).
- GATHER/BOUNTY/LIBERATE — unaffected, no `evaluate_*` method exists for them.
