---
status: active
artifact_type: investigation
ticket_id: TCK-20260619-E21D-SCARCITY-VERIFY
date: 2026-06-20
---

# Investigation — TCK-20260619-E21D-SCARCITY-VERIFY

## Current Behavior (file:line refs)

### ResourceEcologyService (src/world/ecology.py)
- `ECOLOGY_INTERVAL = 200` ticks (L17)
- `process_ecology()` (L20): runs only when `state.tick % 200 == 0`
- Regen loop (L30–50): for nodes with `regen_rate_per_tick > 0`, `remaining_charges < max_charges`, `cooldown_remaining == 0` — computes delta, emits `ResourceNodeUpdate` and optionally `RESOURCE_RECOVERED` event when `was_depleted` (L37, L44–50)
- Returns `StateUpdate(world_events_add=regen_events, node_updates=regen_node_updates, ...)`

### RESOURCE_DEPLETED emitter (src/engine/economy.py)
- Emits `WorldEvent(RESOURCE_DEPLETED)` when a harvest reduces `remaining_charges` to 0 (guarded by `depleted_nodes` set to avoid duplicates per tick)
- Confirmed by TOWN-173 (verified, test: `test_depleted_event_emitted_when_last_charge_harvested`)

### RegionalPressureModel (src/domains/world_emergence/models.py:L100–L115)
- In the resource pressure block: counts `RESOURCE_DEPLETED` aggregates → contributes `dep_cnt * 0.15` to `res_intensity`
- Emits `RegionalPressure(pressure_kind="resource", ...)` if `harv_cnt > 0 or dep_cnt > 0`

### ScarcityModel (src/domains/world_emergence/models.py:L164)
- Counts `RESOURCE_DEPLETED` aggregates per `(region_id, subject)` pair → `depl * 0.25` into `scarcity` formula
- Emits `ResourceScarcitySignal(scarcity_level=..., trend=..., ...)`

### WorldEmergencePhase (src/domains/world_emergence/phase.py)
- Calls `RegionalPressureModel.evaluate()` then `ScarcityModel.evaluate()` on recent events
- Uses 100-tick window: `min_t = max(0, state.tick - 100)`

### State accumulation (src/engine/apply.py:L311–313)
- `apply.py` merges `update.world_events_add` into `state.recent_world_events` (sliding window via `WORLD_EVENT_WINDOW`)
- `state.recent_world_events: List[WorldEvent]` (src/core/state.py:L1053)

### Parity ledger entries (docs/parity_ledger/town_resource.yaml)
- **TOWN-137**: regen determinism — verified, test at `test_resource_ecology.py::test_regen_increments_charges_per_ecology_interval`
- **TOWN-173**: RESOURCE_DEPLETED emitter — verified
- **TOWN-174**: RESOURCE_RECOVERED emitter — verified
- **TOWN-175**: regen cap/skip guards — verified
- **TOWN-176 (needed)**: integration: RESOURCE_DEPLETED + RESOURCE_RECOVERED both appear in multi-tick run + scarcity signal rises — NOT YET IN LEDGER

### docs/mechanics/03_economic_laws.md § 3
- Current §3 mentions charge depletion for regular nodes but does NOT document:
  - `regen_rate_per_tick` field and semantics
  - `ECOLOGY_INTERVAL = 200` cadence
  - `RESOURCE_DEPLETED` / `RESOURCE_RECOVERED` event kinds
  - Depletion-aware scoring (from E21C)

## Mechanics / Engine Constraints

- Ecology runs at tick-200 cadence (not every tick) — integration test must advance enough ticks to trigger it
- `RESOURCE_DEPLETED` events enter `recent_world_events` via `apply.py`; `WorldEmergencePhase` consumes them via 100-tick window
- For scarcity test: must inject `RESOURCE_DEPLETED` events into state OR run long enough for harvest depletion + ecology cycle to produce the event naturally
- Scarcity rises when `RESOURCE_DEPLETED` aggregates appear in the 100-tick window — the key is that `WorldEmergencePhase` sees these events

## Parity Ledger Overlap

- TOWN-173, TOWN-174, TOWN-175: already verified — regression surface only
- **TOWN-137**: already verified — regression surface only
- **New entry needed**: integration-level verification that the full depletion→scarcity pipeline fires end-to-end (no TOWN-XXX entry exists for this)

## Prior Work

- TCK-20260619-E21A-NODE-SCHEMA: added `regen_rate_per_tick`, `max_charges`, `cooldown_remaining` fields to `ResourceNodeState`
- TCK-20260619-E21B-REGEN-SERVICE: implemented the regen loop and both emitters; unit tests in `tests/unit/world/test_resource_ecology.py`
- TCK-20260619-E21C-SCORING-WIRE: wired depletion-aware scoring into `AdventureRouteScorer`; updated `docs/mechanics/04_strategic_cognition.md` §6.2

## Risks and Open Questions

1. **Test isolation for 1000-tick slow test**: kernel-based 1000-tick run may be slow. Ticket explicitly marks it `@pytest.mark.slow`. For the `test_regional_scarcity_rises_after_depletion` test, a non-kernel approach (direct `ResourceEcologyService` + `WorldEmergencePhase` calls) is faster and more deterministic.
2. **region_id on RESOURCE_RECOVERED**: ecology emits `RESOURCE_RECOVERED` with `region_id=None` (ecology.py L48). The `ScarcityModel` keys by `(agg.region_id, agg.subject)` — so `RESOURCE_RECOVERED` doesn't flow into scarcity directly, only `RESOURCE_DEPLETED` does. The scarcity test must use `RESOURCE_DEPLETED` events.
3. **No entity required for scarcity test**: `ScarcityModel.evaluate()` only needs `aggregates`; `RegionalPressureModel.evaluate()` iterates `state.regions`. A minimal `AuthoritativeState` with one region and injected events suffices — no kernel needed.

## Anti-Drift Hazards

- Do not add new consumer logic to `RegionalPressureModel` or `ScarcityModel` — out of scope
- Do not alter `RegionalPressureModel.evaluate()` or `ScarcityModel.evaluate()` — verify only
- `recent_world_events` window is 100 ticks; WorldEmergencePhase uses that window — events must fall within it
