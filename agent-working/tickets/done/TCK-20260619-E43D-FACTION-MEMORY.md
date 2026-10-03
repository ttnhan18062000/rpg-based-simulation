---
status: historical
layer: social
authority: P1
audience: agent
ticket_id: TCK-20260619-E43D-FACTION-MEMORY
phase: done
date: 2026-06-20
tags: [social-memory, faction-memory, collective-hostility, phase-4]
---

# TCK-20260619-E43D-FACTION-MEMORY

## Title
Epic 4.3D · Faction Memory (Collective Hostility)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Faction hostility must persist collectively even when all known faction members die in an episode. This ticket implements `FactionSocialMemory` as the collective-level parallel to per-entity `SocialMemoryRecord`.

**Requires:** TCK-20260619-E43B-EXPORT-IMPORT

Can run in parallel with TCK-20260619-E43C-DECAY.

## Scope

In `src/domains/campaigns/social_memory.py`, add:

```python
@dataclass(frozen=True, slots=True)
class FactionSocialMemory:
    faction_id: str
    entity_hostility: Dict[int, float] = field(default_factory=dict)  # entity_id → hostility
    episode_of_offense: Dict[int, int] = field(default_factory=dict)  # entity_id → episode#
```

Add `faction_social_memories: Dict[str, FactionSocialMemory] = field(default_factory=dict)` to `CampaignState`.

**Exporter**: at episode end, scan `social_events.jsonl` for faction offense events (betrayal, attack) → populate `FactionSocialMemory.entity_hostility`.

**Persistency rule**: `FactionSocialMemory` persists across episodes regardless of whether individual NPCs are alive. The faction-as-collective holds the grudge.

## Acceptance Criteria
- `test_faction_hostility_persists_after_key_member_death` passes
- `FactionSocialMemory` serializes to JSON in `CampaignState`

## Related Tickets
- TCK-20260619-E43-SOCIAL-MEMORY (parent epic)
- TCK-20260619-E43B-EXPORT-IMPORT (required)
- TCK-20260619-E43E-CONSEQUENCE-EVENTS (blocked on this + E43C)

## Related Code Areas
- `src/domains/campaigns/social_memory.py` (FactionSocialMemory)
- `src/domains/campaigns/state.py` (CampaignState.faction_social_memories)

## Test Summary
```bash
pytest tests/unit/social/test_social_memory.py::test_faction_hostility_persists_after_key_member_death -x -v
```
## Files Changed
- `src/domains/campaigns/social_memory.py` — added `FactionSocialMemory` (frozen dataclass with `with_offense()`, `to_dict()`, `from_dict()`), `FactionSocialMemoryExporter` (pure static method `build_from_events()`), `FACTION_OFFENSE_KINDS` constant
- `src/domains/campaigns/state.py` — added `faction_social_memories: Dict[str, FactionSocialMemory]` field to `CampaignState`; extended `to_dict()` and `from_dict()` to serialize/deserialize it
- `tests/unit/social/test_social_memory.py` — added 19 new tests covering FactionSocialMemory construction, immutability, round-trip, key conventions, with_offense semantics; FactionSocialMemoryExporter event handling; CampaignState integration; AC test `test_faction_hostility_persists_after_key_member_death`
- `docs/parity_ledger/social_narrative.yaml` — added entry SOC-CROSS-EP-004

## Completion Summary
Implemented `FactionSocialMemory` as a frozen dataclass in `src/domains/campaigns/social_memory.py` with `entity_hostility` (max-hostility semantics) and `episode_of_offense` (first-offense semantics) fields. Int keys are str-converted for JSON, sorted for determinism. `FactionSocialMemoryExporter.build_from_events()` processes social event dicts, recognizing "betrayal" and "attack" offense kinds, and merges into existing faction memories. Added `faction_social_memories: Dict[str, FactionSocialMemory]` to `CampaignState` with full to_dict/from_dict round-trip. All 46 tests pass (27 pre-existing + 19 new). SOC-CROSS-EP-004 added to parity ledger.
