---
ticket_id: TCK-20260619-E23-QUEST-GENERATION
phase: investigation
date: 2026-06-20
---

# Investigation: Pressure-Driven Quest Generation

## Current State (verified 2026-06-20)

### WorldOpportunityPressure + DynamicQuestSeedService — `src/domains/world_emergence/services.py`
Already exists. Key pattern:
- `suggested_opportunity_kinds` is a string tuple: `("clear_threat", "scout_region")`, `("gather_resource", "trade_material")`, `("camp_clear", "defend_town")`
- `DynamicQuestSeedService` at L70 produces "deterministic, capped quest seeds from opportunity pressures" from `WorldOpportunityPressure` inputs
- This is the generation infrastructure E23 builds on top of

### QuestKind — `src/core/models/quests.py:L7`
`QuestKind` enum exists with `HUNT` and ~4 others (all via `auto()`). Strings like `"gather_resource"`, `"resource_crisis"` are NOT in this enum — they exist only as informal strings in `services.py`. E23A must bridge string opportunity kinds → typed `QuestOpportunity` model.

### QuestState — `src/core/models/quests.py:L27`
`QuestState` exists with `quest_kind: QuestKind`. No OFFERED/ACTIVE/PROGRESSED/EXPIRED lifecycle states. Current states: likely OPEN/COMPLETED only (check in implementation).

### quest_registry — `src/core/state.py`
NOT FOUND. No `quest_registry` field in `AuthoritativeState`. Quests may be tracked per-entity in entity state. E23B must add a world-level `quest_registry: Dict[str, QuestOpportunity]` to `AuthoritativeState` (or equivalent durable location).

### Adventure Routing Integration
No HERO-specific quest scoring in `src/domains/adventure/scoring.py`. HERO entities don't currently weight quest opportunities above generic harvesting. E23D adds this.

## Gap Summary

| Gap | Location | Size |
|---|---|---|
| `QuestOpportunity` typed model missing | `src/core/models/quests.py` | ~20 lines |
| `QuestOpportunityGenerator` missing | `src/domains/world_emergence/services.py` | ~50 lines |
| Quest lifecycle state machine (OFFERED→ACTIVE→PROGRESSED→COMPLETED/FAILED/EXPIRED) missing | New service | ~60 lines |
| `quest_registry` field missing from `AuthoritativeState` | `src/core/state.py` | 1 field |
| Reward application for quest completion missing | Authoritative pipeline | ~30 lines |
| HERO capability matching for quest routes missing | `src/domains/adventure/scoring.py` | ~20 lines |

## Key Design Note
`DynamicQuestSeedService` already generates quest seeds from pressure. E23A upgrades these seeds into fully typed `QuestOpportunity` objects with `expiry_ticks`, `objective_chain`, `reward_spec`, and `faction_source`. The seed service becomes an input to the `QuestOpportunityGenerator` (not replaced).
