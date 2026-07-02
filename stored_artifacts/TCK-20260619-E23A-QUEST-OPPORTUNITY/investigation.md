---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E23A-QUEST-OPPORTUNITY
artifact_type: investigation
tags: [quest-generation, pressure-driven, opportunity-type, world-emergence]
---

# Investigation — TCK-20260619-E23A-QUEST-OPPORTUNITY
## Epic 2.3A · QuestOpportunity Model + Generator

---

## Current Behavior

### 1. `src/core/models/quests.py` — no `QuestOpportunity` dataclass

File contains `QuestKind`, `QuestStatus`, `RewardState`, and `QuestState` (a ProjectState subclass).
No `QuestOpportunity` dataclass exists. `QuestState` is the per-entity active quest state, not a
world-level opportunity. The two are distinct concepts; `QuestOpportunity` must be added without
disturbing `QuestState`.

### 2. `src/domains/world_emergence/services.py` — `DynamicQuestSeedService` produces `QuestSeed` only

`DynamicQuestSeedService.generate()` produces typed `QuestSeed` objects (in schema.py) from
`WorldOpportunityPressure` objects. There is no `QuestOpportunityGenerator` class. The
`QuestSeed` model carries string tags (`valid_resolution_tags`) and a `source_pressure_id`, but no
typed objective chain or reward spec.

### 3. `src/domains/world_emergence/schema.py` — `WorldEvent.category` already has `RESOURCE_DEPLETED`

`WorldEventCategory.RESOURCE_DEPLETED` exists (L15). `WorldEvent` dataclass (L31) carries:
- `category: WorldEventCategory`
- `tick: int`
- `region_id: Optional[str]`
- `subject: Optional[str]`  ← resource type e.g. "iron_ore"
- `severity: float = 1.0`
- `payload: Dict[str, float]`

`source_event_id` can be derived as `f"{event.category.value}_{event.region_id}_{event.tick}"`.

### 4. `src/domains/world_emergence/phase.py` — `WorldEmergencePhase.execute()` returns typed `WorldEmergenceResult`

Phase returns `(StateUpdate, WorldEmergenceResult)`. `WorldEmergenceResult` (schema.py L109) has:
`pressures`, `scarcity`, `opportunities`, `quest_seeds`, `rumor_seeds`, `service_pressures` — all tuples.
Adding `quest_opportunities: Tuple[QuestOpportunity, ...] = field(default_factory=tuple)` is the
correct approach.

### 5. `WorldOpportunityPressureService.evaluate()` — produces `WorldOpportunityPressure` objects per region

The pressure service already classifies:
- `danger_pressure > 0.1` → `kind="clear_threat"`
- `scarcity_level > 0.2` → `kind="gather_resource"`
- `camp_pressure > 0.1` → `kind="camp_clear"`

`QuestOpportunityGenerator` will consume world events **directly** (not the pressure objects) per
the ticket scope: `from_resource_depleted(event, tick, seed)`.

### 6. Existing test file `tests/unit/quest/test_quest_generation.py` — tests `QuestGenerator`, not world-emergence

Uses `src/quests/generator.py::QuestGenerator` and `src/core/quests.QuestKind` (legacy). New tests
for `QuestOpportunityGenerator` will live in the same file, importing from the new locations.

### 7. `WorldEmergencePhase.execute()` pipeline — step 5 is `DynamicQuestSeedService`

After step 4 (opportunities), step 5 calls `DynamicQuestSeedService.generate(opportunities, state)`.
New step 5b (after quest seeds) will call `QuestOpportunityGenerator` over raw `RESOURCE_DEPLETED`
events. This is additive — no existing steps change.

---

## Mechanics/Engine Constraints

- **Architecture rule:** Decision logic (QuestOpportunityGenerator) reads state. It must NOT write
  to `quest_registry` or any durable store. Opportunities are returned as part of `WorldEmergenceResult`
  and consumed by downstream systems (E23B onwards).
- **Determinism:** `QuestOpportunity.id` must be deterministic: no uuid(), no time-based seed.
  Formula: `f"{kind}_{source_event_id}_{tick % 10000}"` as per ticket spec. If `source_event_id`
  is None, use `f"{kind}_{entity_id}_{tick % 10000}"`.
- **Frozen dataclass:** `QuestOpportunity` must use `frozen=True, slots=True` matching project
  pattern (`QuestState`, `WorldOpportunityPressure`, etc.).
- **objective_chain is a tuple:** `tuple[str, ...]` — immutable, frozen-safe. E.g. `("fetch:iron_ore:3",)`.
- **diplomatic_errand is a stub:** `reward_spec={}`, `faction_source="stub"` per ticket notes.
- **Authoritative pipeline rule:** `QuestOpportunity` objects are NOT added to quest_registry here.
  They are part of `WorldEmergenceResult` — the authoritative apply path (E23B) will handle durable
  registration. This is the read-only branch of the 6-phase deterministic loop.
- **No import inside execute_brain():** `QuestOpportunity` must not be imported in hot-path code
  per ticket implementation notes.

---

## Parity Ledger Overlap

Checked `docs/parity_ledger/world_dynamics.yaml`: no existing entry covers quest opportunity
generation from world pressure. WORLD-094 (same-seed world generation) and WORLD-065 (deterministic
world generation) are adjacent but do not overlap. New entries required:
- `WORLD-098`: `QuestOpportunity` is generated deterministically from `RESOURCE_DEPLETED` events.
- `WORLD-099`: Same input + same tick + same seed → same `QuestOpportunity.id`.

No P0 entries are mutated.

---

## Prior Work

### E21A (TCK-20260619-E21A-NODE-SCHEMA) — DONE
Confirmed: `WorldEventCategory.RESOURCE_DEPLETED` exists in `schema.py:L15`. `WorldEvent` dataclass
is ready. Resource ecology schema fields (`regen_rate_per_tick`) added.

### E21B (TCK-20260619-E21B-REGEN-SERVICE) — DONE
Confirmed (from stored investigation): `RESOURCE_DEPLETED` events are now emitted when node charges
reach 0 after successful harvest in `economy.py`. `recent_world_events` is stored on
`AuthoritativeState`. Events flow into `WorldEmergencePhase.execute()` via `recent_events` param.

### E13A (TCK-20260619-E13A-QUEST-DEFS) — DONE
Stored artifacts confirm quest definition schema is in place.

---

## Risks and Open Questions

All open questions from ticket are resolvable via code inspection:

**Q1: Does `WorldEmergencePhase.run()` return typed outputs or mutate directly?**
RESOLVED: Returns `(StateUpdate, WorldEmergenceResult)`. `QuestOpportunity` tuple goes into
`WorldEmergenceResult.quest_opportunities`. No durable mutation in this phase.

**Q2: What does `DynamicQuestSeedService.produce()` return?**
RESOLVED: The method is called `generate()`, returns `Tuple[QuestSeed, ...]`. `QuestSeed` is a
separate typed model in schema.py. `QuestOpportunity` is a peer concept at a higher abstraction.

**Q3: Is there an existing `entity_need` pressure signal?**
RESOLVED: No. Ticket scope guards this: "entity-need trigger is optional". Implement
`from_entity_need` as a stub returning `None` per the ticket note on diplomatic_errand.

---

## Anti-Drift Hazards

1. Do NOT add `QuestOpportunity` to `quest_registry` inside `WorldEmergencePhase` — that's E23B.
2. Do NOT use `uuid()` or any non-deterministic ID.
3. Do NOT change `DynamicQuestSeedService` — it stays; `QuestOpportunityGenerator` is additive.
4. Do NOT import `QuestOpportunity` in hot-path simulation code (`execute_brain()` etc.).
5. Do NOT add `objective_chain` as a list — must be `tuple[str, ...]` for frozen dataclass compatibility.
6. `WorldEmergenceResult` is `frozen=True` — adding `quest_opportunities` requires adding it to the
   dataclass definition in `schema.py`, not at runtime.
