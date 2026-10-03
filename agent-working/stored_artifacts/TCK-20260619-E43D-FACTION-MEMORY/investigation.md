# Investigation — TCK-20260619-E43D-FACTION-MEMORY

## What exists

### E43A–E43C (done)
- `src/domains/campaigns/social_memory.py` contains:
  - `InteractionRecord` — frozen dataclass for a single social event
  - `SocialMemoryRecord` — per-entity cross-episode snapshot (relationship_scores, faction_reputation, interaction_history)
  - `SocialMemoryDecay` — applies FRIENDSHIP_DECAY=0.40 / GRUDGE_DECAY=0.10 per episode
  - `SocialMemoryExporter` — reads EntityState at episode end → SocialMemoryRecord
  - `SocialMemoryImporter` — merges SocialMemoryRecord into EntityState at episode start (with decay)
- `src/domains/campaigns/state.py` contains:
  - `CampaignState` — mutable container; already has `social_memories: Dict[int, SocialMemoryRecord]`
  - `FactionCarryForward` — exists but only tracks alive/tension, not hostility history

### Gap being addressed
When all members of a hostile faction die in episode N, the per-entity `SocialMemoryRecord` records are lost (no live entity → no export). The faction's collective grudge vanishes. This ticket adds `FactionSocialMemory` as a faction-level record that survives regardless of member mortality.

## Architecture notes

- `FactionSocialMemory` is a frozen dataclass, parallel to `SocialMemoryRecord`.
- `entity_hostility: Dict[int, float]` maps offending entity_id → hostility score.
- `episode_of_offense: Dict[int, int]` maps offending entity_id → episode index of the offense.
- Int keys must be str-converted for JSON (same pattern as `relationship_scores` in SocialMemoryRecord).
- `CampaignState.faction_social_memories: Dict[str, FactionSocialMemory]` — keyed by faction_id string.
- Ticket scope specifies exporter scans `social_events.jsonl` for faction offense events. Since that log file exists per-episode during a run, the exporter is a static method taking a list of event dicts (testable without live IO).
- `CampaignState` is not frozen (intentional), so adding `faction_social_memories` field follows the existing pattern.

## Design decisions

1. **Dataclass approach**: `frozen=True` without `slots=True` to match existing `SocialMemoryRecord` style (E43A dropped `slots=True` from the actual implementation).
2. **Exporter strategy**: `FactionSocialMemoryExporter.build_from_events(events, episode)` — takes a list of event dicts (normalized from `social_events.jsonl`) and returns `Dict[str, FactionSocialMemory]`. Pure function, no IO.
3. **Merge semantics**: When updating existing `FactionSocialMemory` across episodes, `update()` classmethod merges new offenses in (max of existing vs new hostility score per entity).
4. **Persistency rule**: `faction_social_memories` is always serialized to/from `CampaignState.to_dict()`/`from_dict()`, so it persists even when all faction members are dead.
5. **Offense event filter**: Kinds `"betrayal"` and `"attack"` on an entity targeting a faction are treated as offenses. The `faction_id` field in the event dict identifies the offended faction.

## Files to change

- `src/domains/campaigns/social_memory.py` — add `FactionSocialMemory`, `FactionSocialMemoryExporter`
- `src/domains/campaigns/state.py` — add `faction_social_memories` field to `CampaignState` + to_dict/from_dict
- `tests/unit/social/test_social_memory.py` — add `test_faction_hostility_persists_after_key_member_death` + supporting tests
- `docs/parity_ledger/social_narrative.yaml` — add SOC-CROSS-EP-004

## No conflicts found
- No duplicate work; E43B/E43C are done and don't touch faction-level memory.
- No architectural mismatch; pattern follows existing `SocialMemoryRecord`.
