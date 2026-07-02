---
status: authoritative
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-21
tags: [domains, campaigns, orchestrator, narrative-ledger, episode, carry-forward, rest-api]
---

# Campaign Orchestrator Contract

**Source:** `src/domains/campaigns/orchestrator.py`, `src/domains/campaigns/state.py`,
`src/domains/campaigns/narrative_ledger.py`  
**Implemented by:** TCK-20260619-E32C-ORCHESTRATOR, TCK-20260619-E32D-NARRATIVE-LEDGER,
TCK-20260619-E32E-REST-HISTORY  
**REST endpoint:** `GET /api/v1/campaigns/{id}/history`

---

## Purpose

`CampaignOrchestrator` drives a sequence of **episodes** defined by a
`CampaignManifest`. It owns one `CampaignState` across the full campaign
lifetime, applying carry-forward rules between episodes and accumulating the
`NarrativeLedger`.

---

## CampaignOrchestrator Lifecycle

```
CampaignManifest → CampaignOrchestrator → run_episode() × N → CampaignState
```

| Phase | Description |
|---|---|
| **Created** | `CampaignOrchestrator(manifest)` creates fresh `CampaignState(campaign_id, episode_index=0)`. |
| **Episode Run** | `run_episode()` builds `initial_state` (carry-forwards injected), runs `ScenarioRuntimeService`, calls `_advance_state(final_state, summary)`. |
| **State Advance** | `_advance_state()` extracts entity/faction carry-forwards and narrative entries, extends `CampaignState`, increments `episode_index`. |
| **Done** | All episodes exhausted. `state.episode_history` has N entries. `state.narrative_ledger` accumulates across all episodes. |

The orchestrator raises `RuntimeError` if `run_episode()` is called when
`episode_index >= len(manifest.episodes)`.

---

## Episode Seed Determinism

Episode N uses `seed = CampaignManifest.base_seed + N`. Both
`AuthoritativeState.seed` and `DeterministicRNG` use this value. This
guarantees bit-identical results for the same manifest and the same episode
index.

---

## CampaignManifest

| Field | Type | Description |
|---|---|---|
| `id` | str | Campaign identifier (used as registry key for REST) |
| `episodes` | List[SimulationScenarioDefinition] | Ordered episode sequence |
| `base_seed` | int | Base RNG seed (episode N uses base_seed + N) |
| `carry_forward_rules` | CarryForwardRules | Boolean toggles for carry-forward categories |

`CampaignManifest` is frozen (immutable after construction).

---

## CarryForwardRules

All fields default to `True` (full carry-forward):

| Field | Default | Controls |
|---|---|---|
| `carry_xp` | True | Entity XP (`identity.evolution_points`) |
| `carry_level` | True | Entity level (`identity.evolution_level`) |
| `carry_equipment` | True | Equipment slots and durability |
| `carry_reputation` | True | `social.public_reputation` |
| `carry_injury` | True | `lifecycle.active` (False = dead, carried but not spawned) |
| `carry_faction_state` | True | Faction tension and alive status |

**Alive rule:** Entity liveness uses `lifecycle.active` (NOT `combat.alive`).  
**Dead entities:** Carried in `persistent_entities` for history, NOT spawned in next episode.

---

## Episode Handoff Rules

At the end of each episode, `_advance_state()` runs these extractions in order:

1. **Entity carry-forwards** — for every entity in `final_state.entities`, extract
   `EntityCarryForward` (level, xp, equipment, reputation, alive). Missing carry
   rules use defaults (xp=0, level=1, equipment={}).

2. **Faction carry-forwards** — synthesized by grouping entity faction ints.
   A faction is alive if at least one entity with that faction int has
   `lifecycle.active=True`. Faction ID: `f"faction_{faction_int}"`.

3. **Narrative entries** — convert `AuthoritativeState.recent_world_events`
   to `NarrativeLedgerEntry` records via `_SIGNIFICANCE_MAP`. Only mapped
   categories are recorded.

4. **State update** — `CampaignState` is mutated in-place: persistent_entities
   updated, persistent_factions updated, episode_history appended, narrative_ledger
   extended, episode_index incremented.

---

## NarrativeLedger Schema

The `NarrativeLedger` is a queryable facade over `CampaignState.narrative_ledger:
List[NarrativeLedgerEntry]`. Each entry is a frozen record:

| Field | Type | Description |
|---|---|---|
| `episode` | int | 0-based episode index |
| `tick` | int | Simulation tick at which the event was recorded |
| `event_type` | str | "quest_completed" \| "entity_death" \| "faction_shift" \| "calamity" |
| `subject_id` | str | Entity/faction/node id (empty string if unavailable) |
| `payload` | dict | Event-specific numeric data (may be empty) |
| `significance` | float | 0.0–1.0 relevance weight |
| `entry_id` | str | Deterministic dedup key: `"{episode}:{tick}:{event_type}:{subject_id}"` |

### Significance Map

WorldEventCategory → (event_type, significance):

| WorldEventCategory | event_type | significance |
|---|---|---|
| ENTITY_DEATH | entity_death | 0.5 |
| QUEST_COMPLETED | quest_completed | 0.7 |
| CAMP_CLEARED | faction_shift | 0.9 |
| CAMP_RAID | faction_shift | 0.6 |
| PARTY_ABANDONED | entity_death | 0.4 |
| QUEST_FAILED | quest_completed | 0.3 |

Only categories in this map produce NarrativeLedgerEntry records.

---

## NarrativeLedger Query API

`NarrativeLedger.query(event_type, min_significance, episode)` — all parameters
optional. Returns a new list of matching entries. Empty list if no match.

The query service is a **pure read facade** — it wraps the list at access time
and does not own or mutate `CampaignState.narrative_ledger`.

---

## REST Endpoint Contract

```
GET /api/v1/campaigns/{id}/history
```

### Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `event_type` | str (optional) | null | Filter by event type |
| `min_significance` | float | 0.0 | Minimum significance (inclusive) |
| `episode` | int (optional) | null | Filter by episode index |

### Response Shape (HTTP 200)

```json
{
  "campaign_id": "my_campaign",
  "entry_count": 3,
  "entries": [
    {
      "episode": 0,
      "tick": 15,
      "event_type": "entity_death",
      "subject_id": "goblin_chief",
      "payload": {},
      "significance": 0.5,
      "entry_id": "0:15:entity_death:goblin_chief"
    }
  ]
}
```

### Error Responses

| Code | Condition |
|---|---|
| 404 | Campaign ID not registered in the runtime registry |
| 500 | Unexpected internal error during ledger query |

### Architecture Notes

- All responses go through the presenter layer (`src/api/presenters/campaigns.py`).
  No raw `NarrativeLedgerEntry` domain objects are returned.
- The campaign registry (`_CAMPAIGN_REGISTRY` in `src/api/routes/campaigns.py`)
  is populated by calling `register_campaign(campaign_id, state)` after creating
  a `CampaignOrchestrator`.
- The endpoint has no dependency on `V2EngineManager` — campaigns run
  independently of the scenario runtime.

---

## Constraints

- `CampaignOrchestrator` must not be imported from `src.engine.*` at module
  level — uses deferred import inside `run_episode()` to avoid circular imports.
- `CampaignState` is mutable by design (NOT frozen). Only the orchestrator
  should mutate it.
- `NarrativeLedger` is a read-only façade — it MUST NOT mutate `CampaignState`.
- The REST presenter layer must remain a one-way boundary: presenter may import
  domain types; domain must never import presenter types.
