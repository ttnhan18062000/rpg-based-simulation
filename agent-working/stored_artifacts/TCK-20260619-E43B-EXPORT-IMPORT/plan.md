# Plan — TCK-20260619-E43B-EXPORT-IMPORT

## Objective

Add `SocialMemoryExporter` and `SocialMemoryImporter` to
`src/domains/campaigns/social_memory.py`, extend `CampaignState` with
`social_memories`, and wire both hooks into `CampaignOrchestrator`.

## Changes

### 1. `src/domains/campaigns/social_memory.py` — add Exporter + Importer

**SocialMemoryExporter.export(entity: EntityState, episode: int) -> SocialMemoryRecord**

Reads from `entity.social` (pure, no mutation):
- `entity_id` = entity.id
- `relationship_scores` = dict of `trust_history` (entity_id → trust score)
- `faction_reputation` = `{"default": entity.social.public_reputation}` — single
  scalar as faction-level proxy; per-faction breakdown deferred to later E43 child
- `interaction_history` = () — E43B produces an empty tuple; E43C will enrich
  this from grudge/cooperation tracking
- `last_betrayal_tick` = None (to be enriched by E43C)
- `last_cooperation_tick` = None (to be enriched by E43C)

NOTE: `SocialMemoryExporter` imports `EntityState` from `src.core.state` via
TYPE_CHECKING only (or uses duck typing) to remain consistent with the
no-engine-import constraint. EntityState is accessed by attribute only; the
import is guarded under `TYPE_CHECKING`.

**SocialMemoryImporter.apply(entity: EntityState, record: SocialMemoryRecord) -> EntityState**

Returns a new EntityState with social fields seeded from the record:
- `trust_history` updated additively with `record.relationship_scores`
  (merge: existing + carried, not replace)
- `public_reputation` set to `record.faction_reputation.get("default", entity.social.public_reputation)`
  — only overrides if a "default" key is present in the record

Uses `dataclasses.replace` (aliased as `dc_replace`) to produce an immutable
replacement, consistent with `_build_initial_state()` pattern.

### 2. `src/domains/campaigns/state.py` — add social_memories to CampaignState

Add field:
```python
social_memories: Dict[int, SocialMemoryRecord] = field(default_factory=dict)
```

Add to `to_dict()`:
```python
"social_memories": {
    str(k): v.to_dict()
    for k, v in sorted(self.social_memories.items())
},
```

Add to `from_dict()`:
```python
social_memories={
    int(k): SocialMemoryRecord.from_dict(v)
    for k, v in d.get("social_memories", {}).items()
},
```

Import `SocialMemoryRecord` at top of `state.py` from `.social_memory`.

### 3. `src/domains/campaigns/orchestrator.py` — wire hooks

In `_advance_state()` (after extracting entity/faction carry-forwards):
```python
social_memories = self._extract_social_memories(final_state, summary.episode_index)
self._state.social_memories.update(social_memories)
```

Add `_extract_social_memories(state, episode_index) -> Dict[int, SocialMemoryRecord]`:
- Iterates `state.entities.items()`
- Calls `SocialMemoryExporter.export(entity, episode_index)` for each entity
- Returns `{entity_id: record}`

In `_build_initial_state()` (after reconstructing entities from carry-forwards):
- For each entity in `entities`, if `entity_id in self._state.social_memories`:
  call `SocialMemoryImporter.apply(entity, self._state.social_memories[entity_id])`
  and replace the entity in the dict.

Import `SocialMemoryExporter`, `SocialMemoryImporter` from
`src.domains.campaigns.social_memory`.

### 4. Tests

**Unit tests** (`tests/unit/social/test_social_memory.py` — extend existing):
- `test_exporter_produces_record_from_entity_state` — mock EntityState with known
  trust_history and public_reputation; verify SocialMemoryRecord fields
- `test_importer_applies_trust_history` — verify trust_history merged into entity
- `test_importer_applies_reputation` — verify public_reputation set from record
- `test_importer_additive_merge` — existing trust + carried trust summed correctly
- `test_importer_no_default_reputation_leaves_original` — no "default" key means
  reputation unchanged

**Integration test** (`tests/integration/scenarios/test_social_memory.py` — new):
- `test_reputation_transfer_across_episodes` (@slow) — runs 2 episodes via
  CampaignOrchestrator; verifies `state.social_memories` populated after ep0;
  verifies ep1 entity has trust_history seeded from ep0 social memory.

## Architecture Gate

- No raw file I/O — all state flows through CampaignState
- Durable state is typed (SocialMemoryRecord)
- Export = pure read; import = dc_replace (no live mutation)
- Determinism preserved: dict keys sorted in to_dict()
- No circular imports: TYPE_CHECKING guard for EntityState
