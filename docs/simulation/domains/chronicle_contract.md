---
status: authoritative
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-22
tags: [domains, chronicle, history, rest-api, contract]
---

# Chronicle Domain Contract

**Source:** `src/domains/chronicle/` (5 files + `__init__.py`)  
**Authoritative status:** Analysis output domain — produces persistent historical narrative records from campaign NarrativeLedger entries.

---

## Purpose

The Chronicle domain compresses flat `NarrativeLedger` event streams into a four-level narrative hierarchy (events → incidents → episodes → eras) and renders them into human-readable `Chronicle.md` and machine-readable `chronicle.json`. The REST layer (E51E) exposes chronicle.json for external tooling.

---

## Pipeline Overview

```
CampaignState.narrative_ledger
    → EventSignificanceScorer  (E51A) — filter at CHRONICLE_THRESHOLD=0.5
    → ChronicleGrouper         (E51B) — cluster into Incidents/Episodes/Eras
    → ChronicleNamer           (E51C) — assign human names to milestones/eras
    → ChronicleRenderer        (E51D) — render Chronicle.md + chronicle.json
    → ChronicleCompiler        (E51D) — orchestrate + write files
    → REST API                 (E51E) — expose chronicle.json via GET endpoints
```

All stages are stateless. `ChronicleCompiler.compile()` is the sole public entry point for end-to-end execution.

---

## Significance Scoring Formula (E51A)

File: `src/domains/chronicle/significance.py`

```
CHRONICLE_THRESHOLD = 0.5

BASE_SIGNIFICANCE = {
    "entity_death":     0.6,
    "quest_completed":  0.7,
    "faction_shift":    0.8,
    "battle_won":       0.7,
    "item_crafted":     0.4,
    "trade_completed":  0.3,
    "skill_learned":    0.5,
}
HERO_BONUS = 0.3

score(entry) = min(1.0, BASE_SIGNIFICANCE.get(event_type, 0.4) + (HERO_BONUS if subject_id == "hero" else 0.0))
is_chronicle_worthy(entry) = score(entry) >= CHRONICLE_THRESHOLD
```

---

## Hierarchy Definitions (E51B)

File: `src/domains/chronicle/grouper.py`

| Level | Class | Definition |
|---|---|---|
| Event | `NarrativeLedgerEntry` | Chronicle-worthy individual event |
| Incident | `Incident` | Cluster of events within `INCIDENT_TICK_WINDOW=50` ticks in the same episode |
| Episode | `Episode` | All incidents within one episode index |
| Era | `Era` | Batch of `ERA_EPISODE_MIN=3` consecutive episodes |

**Incident ID format:** `ep{episode}:t{start_tick}-{end_tick}`  
**Episode ID format:** `episode:{index}`  
**Era ID format:** `era:{ordinal}` (0-based)

All hierarchy objects are frozen dataclasses.

---

## Naming (E51C)

File: `src/domains/chronicle/naming.py`

- `ChronicleNamer.name_milestone(entry, entity_names)` — resolves subject name via `entity_names` dict (int key), applies event-type template.
- `ChronicleNamer.name_era(ordinal, dominant_event_type)` — maps dominant event type to age name (e.g. "Age of Conflict"). Falls back to `"Era {ordinal+1}"`.

---

## chronicle.json Schema (E51D)

File: `src/domains/chronicle/renderer.py` — `ChronicleRenderer.render_json()`

```json
{
  "campaign_id": "str",
  "eras": [
    {
      "id": "era:{ordinal}",
      "ordinal": 0,
      "name": "Age of Conflict",
      "significance": 0.9,
      "episode_ids": ["episode:0", "episode:1", "episode:2"]
    }
  ],
  "episodes": [
    {
      "id": "episode:{index}",
      "index": 0,
      "significance": 0.8,
      "incident_ids": ["ep0:t5-55"]
    }
  ],
  "named_milestones": [
    {
      "name": "Death of the Goblin King",
      "tick": 5,
      "episode": 0,
      "event_type": "entity_death",
      "significance": 0.8,
      "entry_id": "0:5:entity_death:goblin_king"
    }
  ]
}
```

All three top-level array keys are always present (may be empty lists).

---

## REST API (E51E)

File: `src/api/routes/chronicle.py`

### Registry

`_CHRONICLE_REGISTRY: Dict[str, dict]` — keyed by `campaign_id`. Populated by callers after `ChronicleCompiler.compile()` via `register_chronicle(campaign_id, data)`.

### Endpoints

#### `GET /api/v1/chronicle/{campaign_id}`

Returns full chronicle.json as a shaped response (no raw dicts).

**Response model:** `ChronicleResponse` (`src/api/presenters/chronicle.py`)

```json
{
  "campaign_id": "str",
  "eras": [ChronicleEraPresenter, ...],
  "episodes": [ChronicleEpisodePresenter, ...],
  "named_milestones": [ChronicleMilestonePresenter, ...]
}
```

**Errors:** 404 if campaign_id not registered, 500 on shape failure.

#### `GET /api/v1/chronicle/{campaign_id}/eras/{era_id}/summary`

Returns era summary with milestone count and name strings.

**Path params:**
- `campaign_id` — campaign identifier
- `era_id` — era identifier string (e.g. `era:0`)

**Response model:** `ErasSummaryResponse`

```json
{
  "era_id": "era:0",
  "name": "Age of Conflict",
  "milestone_count": 3,
  "named_milestones": ["Death of the Goblin King", "..."]
}
```

`named_milestones` contains the names of all milestones whose `episode` index falls within the era's `episode_ids`.

**Errors:** 404 if campaign_id or era_id not found, 500 on unexpected failure.

---

## Parity Ledger

| Entry ID | Status | File |
|---|---|---|
| SOC-CHRON-001 | verified | `docs/parity_ledger/social_narrative.yaml` |
| SOC-CHRON-002 | verified | `docs/parity_ledger/social_narrative.yaml` |
| SOC-CHRON-003 | verified | `docs/parity_ledger/social_narrative.yaml` |
| SOC-CHRON-004 | verified | `docs/parity_ledger/social_narrative.yaml` |
| SOC-CHRON-005 | verified | `docs/parity_ledger/social_narrative.yaml` |

---

## File Map

| File | Role |
|---|---|
| `src/domains/chronicle/significance.py` | EventSignificanceScorer |
| `src/domains/chronicle/grouper.py` | ChronicleGrouper, hierarchy dataclasses |
| `src/domains/chronicle/naming.py` | ChronicleNamer |
| `src/domains/chronicle/renderer.py` | ChronicleRenderer |
| `src/domains/chronicle/compiler.py` | ChronicleCompiler (top-level entry) |
| `src/api/routes/chronicle.py` | FastAPI router + registry |
| `src/api/presenters/chronicle.py` | Pydantic response models |
| `tests/api/test_chronicle_api.py` | REST API tests (7 tests) |
| `tests/unit/domains/chronicle/test_chronicle_compiler.py` | Unit tests for pipeline |
