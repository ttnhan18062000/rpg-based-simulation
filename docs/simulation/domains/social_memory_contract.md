---
status: authoritative
layer: social
authority: P1
audience: agent
last_verified: 2026-09-04
tags: [domains, campaigns, social-memory, consequence-events, cross-episode, contract]
---

# Social Memory Contract (Epic 4.3)

**Source:** `src/domains/campaigns/social_memory.py`, `src/systems/social_systems/consequence_events.py`  
**Parity ledger:** `docs/parity_ledger/social_narrative.yaml` (SOC-CROSS-EP-001 through SOC-CROSS-EP-005)  
**Ticket scope:** TCK-20260619-E43A through TCK-20260619-E43E

---

## Purpose

Cross-episode social memory allows the simulation to carry meaningful interpersonal and factional history between episodes. Entities and factions do not start each episode with a blank social slate — prior betrayals, cooperative bonds, and reputation are preserved, decayed, and then re-expressed as consequence events when relevant entities meet.

---

## Data Layer (E43A · SOC-CROSS-EP-001)

### `SocialMemoryRecord`

Per-entity cross-episode social snapshot. Frozen dataclass with `to_dict()` / `from_dict()` JSON round-trip.

| Field | Type | Description |
|---|---|---|
| `entity_id` | `int` | Subject entity |
| `relationship_scores` | `Dict[int, float]` | Positive = bond, negative = grudge, per other-entity-id |
| `faction_reputation` | `Dict[str, float]` | Reputation with named factions; `"default"` key = public_reputation proxy |
| `last_seen_episode` | `int` | Episode index when this record was last written |
| `interaction_log` | `List[InteractionRecord]` | Individual social events (helped, betrayed, traded, etc.) |

### `InteractionRecord`

Individual social event record. Frozen dataclass.

| Field | Type | Description |
|---|---|---|
| `kind` | `str` | One of: `helped`, `betrayed`, `traded`, `fought_alongside`, `conflict` |
| `episode` | `int` | Episode index |
| `tick` | `int` | Tick within episode |
| `magnitude` | `float` | Strength of the interaction |
| `other_entity_id` | `Optional[int]` | The other party (if applicable) |
| `faction_id` | `Optional[str]` | Relevant faction (if applicable) |

### `FactionSocialMemory`

Collective faction-level hostility record. Frozen dataclass. Persists regardless of individual faction member survival.

| Field | Type | Description |
|---|---|---|
| `faction_id` | `str` | Identifying faction |
| `entity_hostility` | `Dict[int, float]` | 0.0–1.0 hostility score per entity-id (max-hostility semantics) |
| `episode_of_offense` | `Dict[int, int]` | First episode when each entity offense was recorded |

**Max-hostility semantics:** `entity_hostility` scores are never lowered — only increased by new offenses.  
**First-offense semantics:** `episode_of_offense` records only the first episode an entity was flagged.

---

## Export / Import Hooks (E43B · SOC-CROSS-EP-002)

### `SocialMemoryExporter.export(entity, episode_index) -> SocialMemoryRecord`

- Pure read of `entity.social.trust_history` and `entity.social.public_reputation`
- Called at episode end by `CampaignOrchestrator._advance_state()`
- Stores result in `CampaignState.social_memories[entity_id]`
- **Does not read `entity.social.regional_reputation`** (added by
  TCK-20260904-REPUTATION-LOCALITY-SCOPE, SOC-266) — the region-scoped reputation dimension is not
  part of this export today; only the flat global `public_reputation` scalar crosses episode
  boundaries, via the same `faction_reputation["default"]` proxy key as before.

### `SocialMemoryImporter.apply(entity, record, episode_index)`

- Merges `record.relationship_scores` into `entity.social.trust_history` (additive)
- Seeds `entity.social.public_reputation` from `record.faction_reputation["default"]`
- Applies `SocialMemoryDecay` before merging (see E43C below)
- Called at episode start by `CampaignOrchestrator._build_initial_state()`
- **Write path corrected (TCK-20260904-REPUTATION-LOCALITY-SCOPE):** this seed previously bypassed
  `RelationshipService.process_update()` via a direct `dc_replace(entity.social, ...,
  public_reputation=new_reputation)` call — a real, pre-existing violation of SOC-217's "no second
  write path" rule, found by a new architecture guard test
  (`tests/architecture/test_social_write_paths.py`). It now routes through
  `RelationshipService.process_update(entity.social, SocialUpdate(reputation_set=...))`, a
  zero-behavior-change fix (same computed value, authoritative write mechanism). The same class of
  bypass was independently found and fixed in `CampaignOrchestrator._build_initial_state()`'s own
  carried-reputation seeding. Does not seed `entity.social.regional_reputation` — that field is not
  yet carried across episode boundaries; see the disclosed gap below.

**Disclosed gap — `regional_reputation` does not cross episode boundaries:** `SocialComponent.regional_reputation`
(`Dict[RegionID, float]`, TCK-20260904-REPUTATION-LOCALITY-SCOPE, SOC-266) is a region-scoped reputation
dimension additive to `public_reputation`. Neither `SocialMemoryExporter.export()` nor
`SocialMemoryImporter.apply()` reads or seeds it — only the flat `faction_reputation["default"]` proxy
(itself a *faction*-scoped placeholder, per `SocialMemoryRecord.faction_reputation`'s field description
above) carries forward across episodes, unchanged from before this ticket. Wiring a region-scoped
carry-forward is out of scope here and not yet tracked by a follow-up ticket.

---

## Decay (E43C · SOC-CROSS-EP-003)

### `SocialMemoryDecay.apply_decay(record) -> SocialMemoryRecord`

Decays relationship scores and faction reputation toward neutral before each episode import.

| Bond type | Decay rate | Half-life |
|---|---|---|
| Friendship (positive score) | 40% per episode | ≈ 3 episodes |
| Grudge (negative score) | 10% per episode | ≈ 7 episodes |
| Faction reputation | 40% per episode (friendship rate) | ≈ 3 episodes |

Deterministic: no randomness. Uses `round(..., 4)` for bounded float precision.

---

## Faction Memory Builder (E43D · SOC-CROSS-EP-004)

### `FactionSocialMemoryExporter.build_from_events(events, faction_id, episode_index, existing) -> FactionSocialMemory`

Pure function. Scans episode social event dicts for `kind in {"betrayal", "attack"}` with matching `faction_id`. Applies max-hostility and first-offense semantics. Sorted dict keys for determinism.

**CampaignState fields:**

- `social_memories: Dict[int, SocialMemoryRecord]` — keyed by entity_id
- `faction_social_memories: Dict[str, FactionSocialMemory]` — keyed by faction_id

Both participate in `CampaignState.to_dict()` / `from_dict()` round-trip with `str`/`int` key conversion for JSON compatibility.

---

## Consequence Events (E43E · SOC-CROSS-EP-005)

### `evaluate_social_consequence(entity, faction_id, campaign_state, tick=0) -> List[SimulationEvent]`

**Location:** `src/systems/social_systems/consequence_events.py`

Pure, deterministic function. Reads cross-episode memory; returns zero or more `SimulationEvent` instances. Never mutates state. Callers decide whether to emit/persist.

**Event order:** traitor check → legendary check → debt check.

#### Event kinds and thresholds

| Event kind | Constant | Threshold | Fires when |
|---|---|---|---|
| `KNOWN_TRAITOR_SPOTTED` | `src.observability.events.KNOWN_TRAITOR_SPOTTED` | `entity_hostility >= 0.5` | Entity enters a faction's territory whose memory holds a hostility score at or above the traitor threshold |
| `LEGENDARY_ARRIVAL` | `src.observability.events.LEGENDARY_ARRIVAL` | `faction_reputation["default"] >= 0.9` | Entity with outstanding cross-episode reputation enters any faction territory |
| `OLD_DEBT_COLLECTED` | `src.observability.events.OLD_DEBT_COLLECTED` | `relationship_scores[other] >= 0.5` | Entity meets a prior-episode bond-holder; at most **one** event per encounter (first qualifying bond by sorted entity_id) |

#### Event classes

All are `SimulationEvent` (Pydantic BaseModel) subclasses in `src/observability/events.py`:

- `KnownTraitorSpottedEvent` — fields: `hostility_score: float`, `episode_of_offense: int`
- `LegendaryArrivalEvent` — fields: `hostility_score: float` (unused; 0.0 default), `episode_of_offense: int` (unused; 0 default)
- `OldDebtCollectedEvent` — fields: `debtor_id: int`, `relationship_score: float`

All use `event_category="social"`, `source_system="social_consequence_evaluator"`.

#### Architecture constraints

- `consequence_events.py` MUST NOT import from `src.engine` or `src.core.state` at module level
- `CampaignState` is duck-typed at runtime (no module-level import — `TYPE_CHECKING` guard only)
- Returns `list[SimulationEvent]` — never `None`

---

## Acceptance Tests

```bash
pytest tests/unit/social/test_social_memory.py -x -v -m "not slow"
```

Key named tests (from ticket acceptance criteria):

- `test_known_traitor_event_fires_on_encounter`
- `test_faction_memory_survives_episode_without_member_npcs`
- `test_all_three_event_kinds_importable`

---

## Related

- `docs/parity_ledger/social_narrative.yaml` — SOC-CROSS-EP-001 through SOC-CROSS-EP-005
- `docs/mechanics/03_economic_laws.md` — ch03 note on E43 per-faction reputation detail
- `src/domains/campaigns/orchestrator.py` — wires export/import hooks
- `src/domains/campaigns/state.py` — `CampaignState` definition
