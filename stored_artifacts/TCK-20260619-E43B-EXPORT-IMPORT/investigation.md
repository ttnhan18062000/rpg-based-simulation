# Investigation — TCK-20260619-E43B-EXPORT-IMPORT

## Summary

This ticket wires the `SocialMemoryRecord` data model (from E43A) into
`CampaignOrchestrator._advance_state()` as end-of-episode export and
start-of-episode import hooks. It also extends `CampaignState` with a
`social_memories` dict and extends `_build_initial_state()` to apply the
imported social records to entity state.

## Key Findings

### SocialComponent fields available at export time

`EntityState.social` is a `SocialComponent` (src/core/models/social.py) with:
- `public_reputation: float` — unified rep score (0.0–2.0)
- `trust_history: Dict[int, float]` — per-entity trust
- `grudge_history: Dict[int, float]` — per-entity grudge
- `familiarity_history: Dict[int, float]`
- `fear_history: Dict[int, float]`
- `bonds: Dict[int, SocialBond]` — first-class directed relationships
- `nemesis_ids: Set[int]`
- `place_attachment: Dict[str, float]`
- `betrayal_count: int`
- `heroism_score: float`, `notoriety_score: float`

There is NO `faction_reputation` or `relationship_scores` field on
SocialComponent. The ticket sketch references them, but the actual
SocialComponent does not have them. Resolution:
- `relationship_scores` → derived from `trust_history` (normalized trust scores per entity)
- `faction_reputation` → not directly available; the existing `public_reputation`
  float is the closest proxy. For E43B, we use `public_reputation` as the
  single-score faction proxy (per EntityCarryForward pattern — "public_reputation
  — single score; E43 adds per-faction detail"). Per-faction detail is left for
  a later E43 child ticket.
- `last_betrayal_tick` / `last_cooperation_tick` → not tracked in SocialComponent;
  set to None at export time (to be enriched by E43C if needed).

### EntityUpdate / SocialUpdate pattern for import

The authoritative mutation path uses `EntityUpdate` + `SocialUpdate`. To apply
social memory at episode start, the importer constructs a `SocialUpdate` with:
- `trust_delta` → relationship_scores from the decayed record
- `reputation_set` → faction_reputation["default"] (the public_reputation proxy)

This goes through `_build_initial_state()` which already calls `dc_replace` on
individual component fields. The cleaner approach for the importer is to return a
modified `EntityState` (via `dc_replace`) rather than an `EntityUpdate`, since
`_build_initial_state()` builds `EntityState` objects directly (not via the
authoritative pipeline). The importer therefore returns a modified `EntityState`.

### CampaignState extension

`CampaignState` is mutable (not frozen). Adding
`social_memories: Dict[int, SocialMemoryRecord]` follows the same pattern as
`persistent_entities`. The field must be serialized in `to_dict()` /
`from_dict()` with `str(k)` / `int(k)` key conversion for JSON compatibility.

### Orchestrator hook points

In `_advance_state()`: export is called after entity carry-forwards are extracted
(entities are still accessible from `final_state`). The export result is stored
into `self._state.social_memories`.

In `_build_initial_state()`: import is called after entities are reconstructed
from `alive_carry_forwards`. For each entity, if a social memory record exists,
it is applied via `SocialMemoryImporter.apply()`.

### Test strategy

Integration test in `tests/integration/scenarios/test_social_memory.py` (new
file). Uses the same `_make_spec` / `_make_entity_state` helpers from
`test_campaign_runtime.py`. Runs two episodes; verifies that social memory from
episode 0 (trust/reputation) is present in the campaign state after episode 0
ends, and that the importer seeds the entity correctly for episode 1.

### Architecture constraints satisfied

- `SocialMemoryExporter` and `SocialMemoryImporter` live in
  `src/domains/campaigns/social_memory.py` — no imports from `src.engine`.
- Export reads from `EntityState` (pure read, no mutation).
- Import returns a modified `EntityState` (via `dc_replace`) — durable state
  mutated only by `_build_initial_state()`, which is the authoritative
  construction path for each episode.
- `CampaignState.social_memories` persists through `to_dict()`/`from_dict()`.
- No raw file I/O; all state goes through `CampaignState`.
