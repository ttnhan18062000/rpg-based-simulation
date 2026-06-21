# Investigation — TCK-20260619-E43A-SOCIAL-MEM-MODEL

## Summary

This ticket defines the pure data-model layer for cross-episode social memory.
It has no dependencies on live `EntityState` or `AuthoritativeState` — it is a
pure `dataclass` module under `src/domains/campaigns/` matching the existing
pattern established by `state.py` (EntityCarryForward, CampaignState, etc.).

## Key Findings

### What Already Exists

**CampaignState** (`src/domains/campaigns/state.py`):
- Frozen sub-records (EntityCarryForward, FactionCarryForward, EpisodeSummary,
  WorldTimelineEntry, NarrativeLedgerEntry) with `to_dict()` / `from_dict()`.
- Mutable container `CampaignState` holds lists/dicts of those records.
- Pattern: `dataclass(frozen=True)` for sub-records, with explicit round-trip
  methods. `slots=True` is used in the E43-parent plan sketches but NOT in
  existing campaign records — we match existing conventions (`frozen=True`
  without `slots` since other records don't use it).

**SocialMemoryService** (`src/systems/social_systems/memory.py`):
- Handles per-tick place-attachment and nemesis promotion only.
- No cross-episode export/import logic exists.

**Social domain investigation** (from E43 parent epic staging artifact):
- `EntityState.social` fields: `public_reputation`, `trust_history`,
  `grudge_history`, `nemesis_ids`, `place_attachment`, `faction_reputation`.
- Interaction history is not currently persisted; it must be constructed by
  E43B's exporter from SocialUpdate events at episode end.

### What Needs to Be Built (This Ticket)

1. `InteractionRecord` — immutable record of one social event across episodes.
2. `SocialMemoryRecord` — durable per-entity cross-episode social snapshot.
3. Both must support `to_dict()` / `from_dict()` for JSON round-trip (matching
   the CampaignState persistence pattern).
4. No imports from `src.engine` or `src.core.state` — pure data model.

### Architecture Constraints

- Module location: `src/domains/campaigns/social_memory.py` (new file).
- MUST NOT import from `src.engine` or `src.core.state` (same constraint as
  `state.py`).
- Frozen immutable records for sub-models; Dict/Tuple fields for collections.
- `Dict` keys that are `int` (entity_id) must be round-tripped through
  `str(k)` / `int(k)` for JSON compatibility (same pattern as CampaignState).
- `Tuple[InteractionRecord, ...]` serializes as a JSON array of dicts.
- `Optional[int]` fields (`last_betrayal_tick`, `last_cooperation_tick`,
  `other_entity_id`) serialize as `null` when None.
- `Optional[str]` fields (`faction_id`) serialize as `null` when None.

### Test Location

New file: `tests/unit/social/test_social_memory.py`
The directory already exists; `__init__.py` present.
