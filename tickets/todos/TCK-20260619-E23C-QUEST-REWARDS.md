---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E23C-QUEST-REWARDS
phase: open
date: 2026-06-20
tags: [quest-generation, rewards, economy, authoritative-pipeline, phase-2]
---

# TCK-20260619-E23C-QUEST-REWARDS

## Title
Epic 2.3C · Quest Completion Reward Application

## Status
OPEN

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

## Test Summary
```bash
pytest tests/unit/quest/test_quest_rewards.py -x -v
pytest tests/unit/quest/ -x -v  # regression
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
