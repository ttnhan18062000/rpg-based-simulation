---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Memory Domain Contract

**Source:** `src/domains/memory/` (phase.py, causal_service.py, spatial_service.py, temporal_service.py); `src/cognition/knowledge_model.py` (separate cognition layer — documented here for disambiguation only)  
**Pipeline phase:** Phase 13 — MemoryUpdatePhase  
**Authoritative status:** Entity memory update domain — updates causal lessons, spatial familiarity, and temporal urgency each tick. Operates on the entity list, not world state.

---

## Purpose

The memory domain maintains three distinct memory subsystems for each entity: **causal memory** (lessons extracted from failure events), **spatial memory** (region danger and familiarity derived from experience), and **temporal memory** (deadline-driven urgency recalculation). These subsystems inform future decisions in the adventure, motivation, and cognition layers — they do not directly execute actions. All memory updates use `dataclasses.replace` semantics; no raw field mutation outside this phase is permitted.

This domain is **not** the same as the cognition-layer knowledge model (`src/cognition/knowledge_model.py`). See the disambiguation section below.

---

## Engine Phase

**Phase 13 — `MemoryUpdatePhase.run(entities, state, context)`**

Operates on the full entity list each tick, following the same per-entity iteration pattern as the perception domain. For each entity, three services are invoked in sequence:

| Service | Always runs | Condition |
|---|---|---|
| `TemporalPressureService` | Yes — every tick | Unconditional recalculation |
| `CausalAttributionService` | No — event-triggered | Only when a matching trigger event is present for this entity |
| `SpatialMemoryUpdateService` | Yes — every tick | Region visit always recorded; danger update only on qualifying events |

---

## What It Owns

- **Causal memory**: bounded list of `CausalMemoryEntry` records on the entity, each identifying the cause and future advice derived from a failure event
- **Spatial memory**: per-region danger flag and familiarity score (0.0–1.0) in the entity's spatial memory map
- **Temporal urgency**: the `urgency` field on the entity's `TemporalModel`, recalculated from active project deadlines and need-profile urgency dimensions each tick

The memory domain does not own the knowledge model (separate cognition layer), strategic projects, entity identity, or inventory.

---

## What It Reads

From entity cognition state:

| Field | Purpose |
|---|---|
| `entity.cognition.causal_memory` | Bounded list — read to check capacity before appending |
| `entity.cognition.spatial_memory` | Region danger and familiarity map — read and updated |
| `entity.cognition.temporal_model` | Current urgency and deadline fields — recalculated |

From world and event state:

| Field | Purpose |
|---|---|
| `trigger_event` (current tick's event log) | Checked against each entity to determine if causal attribution should run |
| `current_region_id` (entity position) | Used by `SpatialMemoryUpdateService` for region visit update |
| `world state` (region context) | Used to confirm the entity's current region id |

From entity needs and projects:

| Field | Purpose |
|---|---|
| Active project deadlines | Input to `TemporalPressureService` urgency calculation |
| `entity.need_profile` urgency dimensions | Input to `TemporalPressureService` urgency calculation |

---

## Three Memory Subsystems

### 1 — Temporal Memory (TemporalPressureService)

Runs unconditionally every tick for every entity.

Recalculates `TemporalModel.urgency` by examining:
- Active project deadlines relative to current tick
- Urgency dimensions in the entity's `need_profile`

The resulting urgency value is written back via `dataclasses.replace`. The `TemporalModel.urgency` field is the authoritative urgency signal consumed by the motivation domain each tick.

### 2 — Causal Memory (CausalAttributionService)

Triggered **only** when a qualifying event in the current tick's event log matches the entity. It does **not** run every tick.

**Qualifying trigger events:**

| Event kind | Causal lesson type |
|---|---|
| `combat_loss` | Identifies combat approach, opponent type, or equipment gap as cause |
| `failed_search` | Identifies region familiarity gap or incorrect lead as cause |
| `failed_craft` | Identifies missing ingredient, skill gap, or wrong recipe as cause |
| `party_abandoned` | Identifies trust failure, low cohesion, or misaligned goals as cause |

When a trigger is matched, `CausalAttributionService.attribute()` produces a `CausalMemoryEntry`:

```
CausalMemoryEntry(
    event_kind=<trigger_event_kind>,
    cause=<attributed cause string>,
    advice=<future advice string>,
    tick=<current_tick>,
    confidence=0.8
)
```

Confidence is fixed at 0.8 for all causal entries. The entry is appended to the entity's bounded causal list. When the list is at capacity, the oldest entry is evicted (FIFO). Capacity is defined in the entity schema — it is not hardcoded in the service.

### 3 — Spatial Memory (SpatialMemoryUpdateService)

Runs every tick for every entity.

Two operations are performed:

| Operation | Condition | Effect |
|---|---|---|
| `update_region_visit()` | Always — current region every tick | Familiarity for current region +0.15, capped at 1.0 |
| `mark_region_danger()` | Only on `combat_loss` or `near_death` event in this tick | Current region flagged as dangerous in spatial memory |

The familiarity increment (+0.15) and cap (1.0) are the authoritative values. Spatial danger flags persist until explicitly cleared by a separate process (not within this domain).

---

## Disambiguation: Memory Domain vs. Knowledge Model

These are two distinct layers with different ownership and purpose. Confusing them leads to incorrect attribution of where entity cognition state is managed.

| Question | Correct layer | Location |
|---|---|---|
| "What lessons has this entity learned from failures?" | Memory domain — causal memory | `src/domains/memory/attribution.py` |
| "How familiar is this entity with region X?" | Memory domain — spatial memory | `src/domains/memory/spatial_update.py` |
| "How urgently does this entity need to act?" | Time domain — temporal pressure | `src/domains/time/service.py` |
| "What does this entity know about world locations, factions, or facts?" | Cognition layer — knowledge model | `src/cognition/knowledge_model.py` |
| "What leads or unknowns is this entity tracking?" | Cognition layer — knowledge model | `src/cognition/knowledge_model.py` |

`KnowledgeModelService` handles assimilation of facts, unknowns, and leads from `InformationResponse` into `KnowledgeModelComponent`. It is updated separately from `MemoryUpdatePhase` and is not part of this domain's execution.

---

## What It May Mutate

All memory domain mutations use `dataclasses.replace` — the same read-phase direct update pattern used by the perception domain. No typed intents are emitted for memory state; memory fields are updated in-place on entity cognition objects via replace semantics.

| Field | Mutation | Mechanism |
|---|---|---|
| `entity.cognition.causal_memory` | Append `CausalMemoryEntry`; evict oldest if at capacity | `dataclasses.replace` |
| `entity.cognition.spatial_memory` | `mark_region_danger()`, `update_region_visit()` | `dataclasses.replace` |
| `entity.cognition.temporal_model.urgency` | Recalculated urgency value | `dataclasses.replace` |

---

## What It Must NOT Mutate

- `entity.cognition.knowledge_model` — this is the separate cognition layer managed by `KnowledgeModelService`; do not write to it from the memory domain
- Strategic projects or objective assignments (memory informs decisions but does not make them)
- Entity identity, inventory, or gold
- World state: regions, resource nodes, ecology records
- Combat state (`alive`, HP, durability)
- Other entities' memory state (each entity's memory is updated in isolation)

---

## Domain Interactions

| Domain / System | Relationship |
|---|---|
| **Adventure domain** | Causal lessons in `CausalMemoryEntry` feed adventure route scoring — advice from past failures (e.g., avoid a region, change approach) influences route selection. Spatial danger flags from `mark_region_danger()` block certain routes when the entity's spatial memory records a region as dangerous. |
| **Motivation domain** | `TemporalModel.urgency` — updated by `TemporalPressureService` each tick — is read as an urgency dimension in `MotivationPressureSet`. High temporal urgency biases the motivation domain toward deadline-related route families. |
| **Cognition layer (knowledge_model)** | The knowledge model is updated separately (by `KnowledgeModelService`, not by this domain). The memory domain reads entity cognition state that the knowledge model also reads, but they write to strictly non-overlapping fields. |
| **Cooperation domain** | The cooperation domain reads `entity.timeline` (recent events) for help-need trigger detection. The memory domain reads the same event log for causal attribution triggering. Neither writes to the other's memory state. |
| **Perception domain** | Both memory and perception operate on the entity list in a per-entity loop. Memory is Phase 13; perception runs at an earlier phase. Memory reads the state that perception has already populated for the current tick. |

---

## Test Protection

Primary test targets:

```
grep -r "MemoryUpdatePhase\|CausalAttributionService\|SpatialMemoryUpdateService\|TemporalPressureService\|causal_memory" tests/
```

Tests must cover:

| Scenario | Required |
|---|---|
| Temporal urgency recalculated every tick — urgency reflects current deadlines | Yes |
| No causal entry appended when no trigger event matches the entity | Yes |
| `combat_loss` trigger → CausalMemoryEntry with confidence=0.8 appended | Yes |
| `failed_search` trigger → CausalMemoryEntry appended | Yes |
| `failed_craft` trigger → CausalMemoryEntry appended | Yes |
| `party_abandoned` trigger → CausalMemoryEntry appended | Yes |
| Causal list at capacity → oldest entry evicted on new append | Yes |
| Region visit every tick → familiarity +0.15, capped at 1.0 | Yes |
| `combat_loss` or `near_death` in region → region marked dangerous | Yes |
| No danger flag set when event is not `combat_loss` or `near_death` | Yes |
| Knowledge model NOT mutated by `MemoryUpdatePhase` | Yes |
| Familiarity does not exceed 1.0 after repeated visits | Recommended |

---

## Extension Rules

**Adding a new causal trigger event:**
1. Add a handler branch in `CausalAttributionService.attribute()` for the new `event_kind`.
2. Define the `cause` and `advice` strings the new event produces — these should be deterministic from the event content, not from RNG.
3. Add tests: trigger fires on the new event kind, does not fire on unrelated events.

**Adding a new spatial memory field:**
1. Extend the spatial memory schema (in entity definition, not in the service).
2. Add the corresponding update logic in `SpatialMemoryUpdateService`.
3. Define the conditions under which the new field is written and the valid value range.
4. Add tests: field set under correct conditions, not set otherwise.

**Causal list capacity:**
Capacity is defined in the entity schema. Do not hardcode a maximum in `CausalAttributionService`. If a new entity class requires a different capacity, set it in the entity schema for that class.

**Do not write to knowledge_model from this domain.** If a use case requires bridging causal lessons into world-fact knowledge, that bridge belongs in the cognition layer (`src/cognition/`), not in `src/domains/memory/`.
