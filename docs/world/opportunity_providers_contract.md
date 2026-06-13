---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-06-13
---

# Opportunity Providers Contract

**Source:** `src/world/providers/resources.py`, `src/world/providers/services.py`, `src/world/providers/information.py`, `src/world/providers/requirements.py`, `src/world/perception/gate.py`, `src/world/motivation/pressure_resolver.py`
**Related docs:** [docs/simulation/domains/world_emergence_contract.md](../simulation/domains/world_emergence_contract.md), [docs/simulation/domains/adventure_contract.md](../simulation/domains/adventure_contract.md), [docs/simulation/domains/information_contract.md](../simulation/domains/information_contract.md)

---

## Purpose

Opportunity providers are the world-side sources of actionable signals that entities perceive and route toward. They run before domain phases and populate the opportunity pool that world_emergence and adventure consume. This document covers the four provider types plus the perception gate and motivation pressure resolver that pre-process signals before entities see them.

---

## Resource Opportunity Provider — `providers/resources.py`

Generates `gather_resource` and `harvest_resource` opportunities from active resource nodes.

### What it produces

For each active resource node (charges > 0):
- Opportunity kind: `gather_resource` or `harvest_resource` (node.kind-mapped)
- Location: node position
- Value: scaled by node charges remaining × base_yield
- Blocker reward: scaled by how depleted the node is (lower charges → higher blocker reward to incentivise competing routes)

### Depletion awareness

Nodes near depletion (charges ≤ 1) receive a `near_depletion` flag on their opportunity. The adventure scoring system uses this to down-score gather opportunities that will yield very little.

### Node kind → opportunity kind mapping

| Node kind | Opportunity kind |
|---|---|
| LOOT | gather_loot (fully depletes on harvest — see resource_conservation_contract.md) |
| WOOD, IRON, STONE | gather_resource |
| HERB, FISH | harvest_resource |

---

## Service Opportunity Provider — `providers/services.py`

Generates affordance-dispatched service opportunities from towns and structures.

### Service types

| Affordance | Opportunity kind |
|---|---|
| Forge present | craft opportunity |
| Repair station | repair opportunity |
| Guild hall | ask_info opportunity |
| Market stall | buy/sell opportunity |
| Inn | rest opportunity |

Service opportunities are generated only for structures reachable from the entity's current region (within routing range). Faction-locked structures generate opportunities only for faction-aligned entities.

---

## Information Providers — `providers/information.py`

Three information provider classes handle query-response flows rather than generating standing opportunities:

| Class | What it returns |
|---|---|
| `RegionInformationProvider` | Region state facts (threat level, resource availability) |
| `EntityInformationProvider` | Entity location and status facts (for scouting) |
| `GuildInformationProvider` | Guild membership and quest facts |

**Phase 1 stub:** `GuildInformationProvider` currently returns mock data. This is documented in the source as a Phase 1 placeholder — do not rely on its output for production logic.

Information providers feed the information domain (Phase 5), not the world_emergence opportunity pool directly. An entity asking "what is in region X?" goes through an information provider; an entity routing toward an opportunity goes through the resource or service provider.

---

## Requirements — `providers/requirements.py`

Validates whether an entity meets the prerequisites for a given opportunity before it is included in the entity's opportunity pool. Checks:
- Inventory requirements (must have/not have specific items)
- Skill level requirements (minimum skill level for crafting/guild opportunities)
- Faction requirements (must belong to faction or not be hostile)
- Quest state requirements (must have/not have active quest)

Opportunities that fail requirements are filtered out before reaching the adventure domain.

---

## Perception Gate — `src/world/perception/gate.py`

The perception gate runs **before** the domain perception phase (Phase 12). It is a catalog-driven binary sense-channel filter.

### Sense channels

7 channels: `vision`, `hearing`, `smell`, `magic_sense`, `life_sense`, `vibration`, `social_reading`

### Gating formula

For each (entity, signal) pair:
```
score = sense_strength × signal_intensity × (1 / (1 + distance)) × terrain_modifier × alertness_modifier
```

Signals with `score < 0.2` are gated out — the entity cannot perceive them regardless of salience. Entities without a `sense_profile_id` in the catalog use a baseline humanoid profile (vision + hearing only).

This gate determines WHICH signals reach an entity. The perception domain phase (Phase 12) then determines WHICH of the reachable signals the entity actually attends to (salience filtering).

---

## Motivation Pressure Resolver — `src/world/motivation/pressure_resolver.py`

Runs before domain phases. Converts catalog `need_profile_id` / `drive_profile_id` into a `MotivationPressureSet` — 8 normalised pressure dimensions.

### 8 pressure dimensions

`survival`, `comfort`, `social`, `achievement`, `curiosity`, `safety`, `greed`, `purpose`

### Resolution algorithm

For each dimension: `max(need_profile[dim], drive_profile[dim])` — the higher of need or drive wins. Values normalised 0.0–1.0.

This output feeds the motivation domain's `MotivationBiasService`, which converts pressures into route scoring multipliers. Agents looking for "what drives entity routing" start here.

---

## Pipeline position

```
World state read →
  ResourceOpportunityProvider → opportunity pool
  ServiceOpportunityProvider  → opportunity pool
  PerceptionGate              → filtered signals per entity
  MotivationPressureResolver  → MotivationPressureSet per entity
  RequirementsFilter          → prune ineligible opportunities
→ Domain phases (adventure Phase 3 reads filtered opportunity pool)
```

---

## Regression tests

- `tests/unit/test_resource_provider.py` — node-to-opportunity mapping, depletion flags, blocker reward scaling
- `tests/unit/test_service_provider.py` — affordance dispatch, faction lock filtering
- `tests/unit/test_perception_gate.py` — sense channel formula, threshold 0.2, baseline profile fallback
- `tests/unit/test_pressure_resolver.py` — 8-dimension max-merge, normalisation

---

## Extension rules

1. To add a new resource node kind: add a mapping in `resources.py`. The LOOT full-depletion rule is special-cased — all other kinds use charge-decrement.
2. To add a new service affordance: add to the affordance dispatch table in `services.py`.
3. To add a new sense channel: extend the catalog schema and `gate.py` scoring. Update the baseline humanoid profile.
4. To add a new pressure dimension: extend `MotivationPressureSet` and update `MotivationPressureResolver`. Update all downstream consumers (motivation domain services) that read pressure dimensions by name.
5. `GuildInformationProvider` must be replaced with real guild state reads before Phase 2 feature completion — do not build new logic on top of the mock.
