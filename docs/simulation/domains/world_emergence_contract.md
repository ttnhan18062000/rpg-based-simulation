---
status: active
layer: simulation
authority: P1
audience: agent
last_verified: 2026-06-13
---

# World Emergence Domain Contract

**Source:** `src/domains/world_emergence/` (phase.py, aggregator.py, pressure_model.py, scarcity_model.py, opportunity_service.py, quest_seed_service.py, rumor_service.py, bridge.py)  
**Pipeline phase:** the World Emergence stage (`WorldEmergencePhase`)  
**Authoritative status:** World-level emergent event processing domain — translates regional pressure and event history into opportunities, quest seeds, and entity-facing signals. Does not directly execute any strategic or combat action.

---

## Purpose

The world emergence domain translates raw world state — event history, regional trauma, resource node charges — into **structured opportunities and entity-facing signals** each tick. Entities do not observe world state directly; they receive shaped signals from this domain that inform their route decisions. The domain owns opportunity generation, regional pressure modeling, quest and rumor seeding, and the signal bridge that pushes derived state into entity properties. All processing is **deterministic**: the same world state and tick number always produce the same outputs.

---

## Engine Phase

**World Emergence stage — `WorldEmergencePhase.execute(state, context)`**

Runs every tick as a world-level phase — it processes the full world state rather than a per-entity iteration. The phase is a sequential seven-step pipeline:

| Step | Component | Output |
|---|---|---|
| 1 | `WorldEventAggregator` | Aggregated event groups (by region, category, subject) |
| 2 | `RegionalPressureModel` | Per-region danger / resource / camp pressure values |
| 3 | `ScarcityModel` | Per-(region, resource_type) availability score |
| 4 | `WorldOpportunityPressureService` | Typed `OpportunityRecord` list |
| 5 | `DynamicQuestSeedService` | Up to 10 deterministic quest seeds |
| 6 | `RumorSeedService` | Lower-certainty rumor seeds (when thresholds exceeded) |
| 7 | `WorldToEntitySignalBridge` | Entity property updates: `exposed_world_signals`, `force_route_reevaluation` |

---

## What It Owns

- **World event aggregation**: collapsing the recent-events window into grouped signals by (region, category, subject)
- **Regional pressure modeling**: danger, resource, and camp pressures per region, derived from world state
- **Scarcity modeling**: per-(region, resource_type) availability based on node state and recent harvest events
- **Opportunity generation**: translating regional pressures into typed opportunity records
- **Quest seed generation**: deterministic seeds for new quests drawn from opportunities
- **Rumor seed generation**: lower-certainty signals seeded when danger or scarcity exceed thresholds
- **Entity signal delivery**: spatial filtering and property-writing of world signals into entity state

The world emergence domain does not own strategic route selection, entity tactics, combat resolution, or world node charges (read-only access).

---

## What It Reads

From world event log:

| Field | Purpose |
|---|---|
| `recent_events` (last 100 ticks) | Source for event aggregation — bounded window prevents unbounded growth |

From region state (per region):

| Field | Purpose |
|---|---|
| `region.trauma_score` | Input to `RegionalPressureModel` — recent damage and disruption |
| `region.hazard_level` | Input to `RegionalPressureModel` — baseline environmental danger |

From resource node state (per node):

| Field | Purpose |
|---|---|
| `node.charges` | Remaining resource availability — input to `ScarcityModel` |
| `node.resource_type` | Resource category — determines which (region, type) bucket scarcity applies to |

From entity state (in `WorldToEntitySignalBridge`):

| Field | Purpose |
|---|---|
| `entity.position` | Spatial filtering — only signals within spatial relevance range are pushed to a given entity |

---

## Step-by-Step Pipeline

### Step 1 — WorldEventAggregator

Groups `recent_events` from the last 100 ticks deterministically by `(region_id, category, subject)`. Events with `severity ≤ 0.05` are filtered out as noise. Produces a list of aggregated event groups, each carrying the group key, event count, peak severity, and contributing event ids.

The 100-tick window is configurable in phase config — do not hardcode.

### Step 2 — RegionalPressureModel

Calculates three pressure values per region:

| Pressure type | Derivation |
|---|---|
| `danger_pressure` | Function of `region.trauma_score` and `region.hazard_level` |
| `resource_pressure` | Function of aggregate scarcity across nodes in the region |
| `camp_pressure` | Function of event aggregation signals indicating camp disruption or settlement threat |

Pressure values are normalized to [0.0, 1.0].

### Step 3 — ScarcityModel

Derives per-(region, resource_type) availability from node charges and recent harvest event volume. A heavily-harvested node with low remaining charges contributes high scarcity for its (region, type) key.

### Step 4 — WorldOpportunityPressureService

Translates regional pressures into typed `OpportunityRecord` objects:

| Pressure | Opportunity type generated |
|---|---|
| `danger_pressure` | `clear_threat` |
| `resource_scarcity` | `gather_resource` |
| `camp_pressure` | `camp_clear` |

Additional opportunity types may be mapped here. Each opportunity carries: opportunity id, type, region_id, priority score, and expiry tick.

### Step 5 — DynamicQuestSeedService

Generates deterministic quest seeds from the opportunity list:

```
seed_id = MD5(opportunity_id + str(tick))
```

Maximum 10 quest seeds generated per tick. The MD5 function over `(opp_id, tick)` ensures the same world state and tick produce the same seeds — no external randomness source is used or permitted.

### Step 6 — RumorSeedService

Generates lower-certainty seeds when:
- `danger_pressure > 0.2` for any region, **or**
- `scarcity > 0.3` for any (region, type) bucket

Rumor seeds carry lower `certainty` than quest seeds. They feed into the information domain for NPC dialogue and knowledge propagation. Rumor generation is also deterministic, derived from region id and tick.

### Step 7 — WorldToEntitySignalBridge

Applies spatial filtering to the full opportunity list, then pushes two properties into each entity whose position falls within signal range:

| Property | Content |
|---|---|
| `entity.exposed_world_signals` | List of opportunity records visible to this entity based on position |
| `entity.force_route_reevaluation` | Boolean flag — set True when new high-priority signals appear, triggering adventure domain re-evaluation next tick |

These are **direct property sets** on entity objects inside the bridge. This is the accepted pattern for signal delivery — it is not expressed as a typed intent.

---

## Determinism Guarantee

Event aggregation order is deterministic — groups are produced in sorted order by `(region_id, category, subject)`. Quest seeds use `MD5(opp_id + tick)`. Given the same world state and the same tick number, `WorldEmergencePhase.execute()` always produces bit-identical outputs.

**Do not introduce any randomness into this pipeline.** All variability must flow from world state inputs, not from RNG calls inside this domain.

---

## What It May Mutate (Via Return / Direct Bridge Write)

| Mutation | Mechanism | Notes |
|---|---|---|
| `StateUpdate` carrying world opportunity state | Returned from phase execute — applied by kernel | Authoritative path for durable opportunity state |
| `WorldEmergenceResult` | Return value consumed by caller | Not a typed intent; the phase returns this struct directly |
| `entity.exposed_world_signals` | Direct property set in `WorldToEntitySignalBridge` | Accepted bridge pattern |
| `entity.force_route_reevaluation` | Direct property set in `WorldToEntitySignalBridge` | Accepted bridge pattern |

No other entity fields are written by this domain.

---

## What It Must NOT Mutate

- Entity strategic state (projects, objectives, cognition)
- Entity inventory, gold, or equipment
- World resource node charges (read-only access in this domain)
- Regional trauma or hazard values (read-only — those are written by world runtime systems)
- Combat state of any entity

---

## Domain Interactions

| Domain / System | Relationship |
|---|---|
| **Adventure domain** | `exposed_world_signals` pushed by the signal bridge are the primary dynamic input to `AdventureRouteGenerator`. The `force_route_reevaluation` flag forces the adventure domain to re-run route generation next tick even if the entity's project lock has not expired. |
| **World runtime systems (ecology, calamity)** | Both the world emergence domain and world runtime systems track regional pressure. They do not share a mutable pressure object — world emergence reads the same region state that world runtime uses, but models its own pressure representation. |
| **Campaign / quest tracking systems** | Quest seeds generated by `DynamicQuestSeedService` feed into quest tracking — new quests are registered from seeds each tick. |
| **Information domain** | Rumor seeds from `RumorSeedService` feed into the information domain for NPC knowledge propagation and `ASK_INFORMATION` route resolution. |
| **Perception domain** | Perception determines what each entity can observe. World emergence determines what signals exist at all. The bridge applies spatial filtering so that only perceptually-reachable signals are pushed to a given entity. |

---

## Test Protection

Primary test targets:

```
grep -r "WorldEmergencePhase\|WorldEventAggregator\|DynamicQuestSeedService\|WorldToEntitySignalBridge\|RumorSeedService\|RegionalPressureModel\|ScarcityModel" tests/
```

Tests must cover:

| Scenario | Required |
|---|---|
| Determinism: same world state + tick → identical opportunity list | Yes |
| Events with severity ≤ 0.05 filtered out of aggregation | Yes |
| danger_pressure → clear_threat opportunity generated | Yes |
| resource_scarcity → gather_resource opportunity generated | Yes |
| camp_pressure → camp_clear opportunity generated | Yes |
| Quest seed cap: > 10 opportunities → exactly 10 seeds, not more | Yes |
| Rumor seeds generated when danger > 0.2 or scarcity > 0.3 | Yes |
| Rumor seeds NOT generated when both thresholds are below cutoff | Yes |
| Signal bridge: entity outside spatial range → NOT in exposed_world_signals | Yes |
| force_route_reevaluation set True when high-priority signals appear | Recommended |
| 100-tick event window bound respected — events older than window excluded | Yes |
| MD5 seed formula: MD5(opp_id + tick) produces same seed for same inputs | Recommended |

---

## Extension Rules

**Adding a new opportunity type:**
1. Add the new opportunity type value to the `OpportunityType` enum (or equivalent schema).
2. Add a pressure → opportunity mapping in `WorldOpportunityPressureService` — define which pressure type and threshold activate the new opportunity.
3. Add the new type to `RouteFamily` in the adventure domain if entities should be able to route to it (coordinate with adventure domain extension rules).
4. If the new opportunity type should generate quest seeds, confirm it is included in the `DynamicQuestSeedService` candidate pool; no change is needed if it is automatically included.
5. Add tests: pressure threshold, opportunity generation, optional quest seed generation.

**Adjusting event aggregation:**
The 100-tick window is configurable in phase config. The `severity ≤ 0.05` filter threshold is also configurable. Do not hardcode either value in aggregation logic.

**Adding a new pressure type:**
1. Add the computation in `RegionalPressureModel`.
2. Add the mapping in `WorldOpportunityPressureService`.
3. Normalize to [0.0, 1.0].
4. If the pressure should trigger rumors, add a threshold check in `RumorSeedService`.

**Do not introduce randomness.** All logic in this pipeline must be deterministic. If a new subsystem requires stochastic behavior, use `DeterministicRNG` seeded from world state and tick — never from an unseeded source.
