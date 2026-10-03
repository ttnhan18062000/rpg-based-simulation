---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E23C-QUEST-REWARDS
phase: done
date: 2026-06-20
tags: [quest-generation, rewards, economy, authoritative-pipeline, phase-2]
---

# TCK-20260619-E23C-QUEST-REWARDS

## Title
Epic 2.3C · Quest Completion Reward Application

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
When a quest transitions to `COMPLETED`, the entity that completed it must receive gold + XP rewards through the authoritative mutation pipeline. No reward path currently exists for pressure-generated quests (prior static quests have their own path; this uses `QuestOpportunity.reward_spec`).

**Requires:** TCK-20260619-E23B-QUEST-LIFECYCLE

## Scope

### Apply `reward_spec` on COMPLETED transition

When `QuestStatusUpdate(new_status=COMPLETED)` is applied in the authoritative pipeline:

1. Read `quest.reward_spec`: `{"gold": int, "xp": int, "faction_rep": float}`
2. Produce a `ResourceTransferIntent` for the completing entity: gold delta + XP reward
3. Apply via existing authoritative reward path (follow pattern from `src/engine/quests.py:L203` — the prior static quest reward)

Per Mechanics Bible Chapter 03 (economic laws): reward transfers must satisfy conservation laws. Gold is transferred from a "world treasury" source, not created from nothing. XP rewards bypass conservation (XP is not conserved).

### Emit `quest_completed` event

In the apply path: after reward is applied, emit a simulation event `event_type="quest_completed"` with `quest_id`, `entity_id`, `reward_spec` in the payload.

### `diplomatic_errand` stub

Quest with `reward_spec={}` → no reward applied. Just transition to COMPLETED with no transfer. This is the Phase 5 stub.

## Out of Scope
- Faction reputation delta (requires Phase 5 faction system)
- Multi-entity shared rewards (Phase 4 party system)

## Acceptance Criteria
- When a quest reaches `COMPLETED`, the completing entity's gold increases by `reward_spec["gold"]`
- XP increases by `reward_spec["xp"]`
- A `quest_completed` simulation event appears in the event log
- `test_quest_completion_adds_gold_and_xp` passes
- `test_quest_completion_is_authoritative` passes (reward goes through apply path, not direct mutation)

## Related Tickets
- TCK-20260619-E23-QUEST-GENERATION (parent epic)
- TCK-20260619-E23B-QUEST-LIFECYCLE (required — lifecycle must exist before reward applies)

## Related Docs
- `docs/mechanics/03_economic_laws.md` (conservation law — gold is transferred not created)
- `docs/engine/authoritative_pipeline.md` (find the correct phase for reward injection)
- `docs/parity_ledger/town_resource.yaml` (update quest reward entries to `verified` after this ticket)
- `docs/parity_ledger/progression.yaml` (update XP reward entries to `verified` after this ticket)

## Related Code Areas
- `src/engine/quests.py:L203` (existing `ResourceTransferIntent` for quest reward — pattern reference)
- `src/engine/authoritative_pipeline.py` or equivalent (find QuestStatusUpdate apply path; inject reward there)
- `tests/unit/quest/test_quest_rewards.py` (new)

## Assumptions / Open Questions
- Where does the "world treasury" gold come from for quest rewards? Check how `src/engine/quests.py:L203` handles the source_id for quest gold. Use the same pattern.
- Is XP rewarded through `ResourceTransferIntent` or a separate `RewardUpdate`? The `ResourceTransferIntent.xp_reward` field exists — use it.

## Implementation Notes
- Added `QuestOpportunityRewardIntent(entity_id, quest_id)` dataclass and `quest_opportunity_reward_intents: List[...]` field to `StateUpdate` (`src/core/updates.py`). Updated `is_noop()` and `merge_many()` accordingly.
- Created `src/engine/pipeline_phases/quest_opportunity_rewards.py` with `QuestOpportunityRewardSystem.enforce()` and `_emit_terminal_removals()` helper. Reads `reward_spec` from `state.quest_registry`, emits `ResourceTransferIntent(source_kind="QUEST")` with `reward_upd=RewardUpdate(xp_gain=...)`, and appends `WorldEvent(category=QUEST_COMPLETED)`. Zero-reward quests are removed immediately; non-zero-reward quests defer removal until the transaction_id appears in `state.processed_transaction_ids`.
- Extended `QuestRewardPhase.resolve()` (`src/engine/pipeline_phases/quests.py`) to call `QuestOpportunityRewardSystem.enforce()` after the existing `QuestResolutionSystem.enforce()`.
- Added phase-specific dirty-set bypass in `src/engine/phase_graph.py`: `quest_rewards` and `resource_transactions` run unconditionally when `update.quest_opportunity_reward_intents` is non-empty. Required because the dirty_set is refreshed before `quest_rewards`, so `resource_transactions` would otherwise see a stale clean dirty_set and skip processing the generated `ResourceTransferIntent`.
- 10 tests in `tests/unit/quest/test_quest_rewards.py` (7 AC + 3 anti-drift). All pass. Full quest domain regression (61 tests) green.

## Test Summary
```bash
pytest tests/unit/quest/test_quest_rewards.py -x -v
pytest tests/unit/quest/ -x -v  # regression
```

## Files Changed
- `src/core/updates.py` — `QuestOpportunityRewardIntent` dataclass + `StateUpdate.quest_opportunity_reward_intents` field
- `src/engine/pipeline_phases/quest_opportunity_rewards.py` — new file: `QuestOpportunityRewardSystem`
- `src/engine/pipeline_phases/quests.py` — wire `QuestOpportunityRewardSystem` into `QuestRewardPhase.resolve()`
- `src/engine/phase_graph.py` — dirty-set bypass for `quest_rewards` and `resource_transactions` phases
- `tests/unit/quest/test_quest_rewards.py` — new file: 10 tests

## Completion Summary
Implemented `QuestOpportunityRewardSystem` delivering gold + XP to completing entities via the authoritative `ResourceTransferIntent` path with `WorldEvent(category=QUEST_COMPLETED)` emission and deferred registry removal.

Key deliverables:
- `QuestOpportunityRewardIntent` dataclass added to `src/core/updates.py`; `StateUpdate.quest_opportunity_reward_intents` field wired with `is_noop()` and `merge_many()` support.
- New `src/engine/pipeline_phases/quest_opportunity_rewards.py`: `QuestOpportunityRewardSystem.enforce()` reads `reward_spec` from `state.quest_registry`, emits `ResourceTransferIntent(source_kind="QUEST")` with `RewardUpdate(xp_gain=...)`, appends `WorldEvent(category=QUEST_COMPLETED)`. Zero-reward quests removed immediately; non-zero-reward quests defer removal until `transaction_id` appears in `state.processed_transaction_ids`.
- `QuestRewardPhase.resolve()` in `src/engine/pipeline_phases/quests.py` extended to call `QuestOpportunityRewardSystem.enforce()` after existing `QuestResolutionSystem.enforce()`.
- `src/engine/phase_graph.py`: dirty-set bypass added for `quest_rewards` and `resource_transactions` phases when `update.quest_opportunity_reward_intents` is non-empty.
- 10 tests in `tests/unit/quest/test_quest_rewards.py` (7 AC + 3 anti-drift). All pass. Full quest domain regression (61 tests) green.
- Parity ledger entries updated in `docs/parity_ledger/town_resource.yaml` and `docs/parity_ledger/progression.yaml` (quest reward entries set to `verified`).
