---
ticket_id: TCK-20260619-E33B-ALERTS-REST
phase: investigation
date: 2026-06-21
---

# Investigation: Economic Alert Events + REST Endpoint

## Current Behavior (file:line refs)

### E33A foundation (DONE)
`src/economy/health_monitor.py` — `EconomyHealthMonitor.sample()` computes
`EconomyHealthSnapshot(tick, gini_coefficient, transaction_velocity, avg_price_index)`
every `WINDOW_SIZE=100` ticks. It reads `e.inventory.gold` (authoritative scalar) and
`e.combat.alive`. Returns `None` on off-window ticks. Stateless — no durable mutation.

`src/observability/reporting/metric_recorder.py` — `MetricWindowRecord` now carries
three optional economy fields (`economy_gini_coefficient`, `economy_transaction_velocity`,
`economy_avg_price_index_json`) added by E33A. `MetricWindowRecorder.record_economy_snapshot(snapshot)`
passes through to the current accumulator; `flush()` serialises economy fields into each
JSONL record. Kernel wires `EconomyHealthMonitor.sample()` before `record_tick()`.

### Alert event kinds — not yet defined
`src/observability/events.py` defines `SimulationEvent` (Pydantic BaseModel) and several
typed subclasses (`CombatDamageEvent`, `GoldTransactionEvent`, etc.) following the pattern:
- Subclass `SimulationEvent`
- Set default `event_type`, `event_category`, `severity`, `source_system`
- Optionally override `__init__` to set a default `message`
- `EventCategory` is a `Literal` type alias at L44 — already includes `"economy"`

No `DEFLATION_RISK`, `INFLATION_SPIRAL`, `ECONOMIC_COLLAPSE`, or `GOLD_HOARDING` events exist yet.

### WorldEvent vs SimulationEvent distinction
`src/domains/world_emergence/schema.py` defines `WorldEvent` (frozen dataclass) with
`WorldEventCategory` enum and `world_events_add` list on `StateUpdate` (updates.py L876).
`WorldEvent` is used for **world-level emergence signals** (camp raids, resource depletion, etc.)
consumed by the narrative/strategy layer — it is not the correct vehicle for economy health alerts.

Economy health alerts should be **`SimulationEvent` subclasses** (`event_category="economy"`) — this
is consistent with `GoldTransactionEvent` and how the observability pipeline (`LiveEventPublisher`,
`ObservabilityEventEnvelope`) consumes events. The ticket scope says "emit events via
`StateUpdate(events_add=[...])"`— but `StateUpdate` has no `events_add` field; it has
`world_events_add: List[WorldEvent]`. The correct approach is to emit `SimulationEvent`
instances, not `WorldEvent`s. See Risks section.

### How SimulationEvents flow out of EconomyHealthMonitor
`EconomyHealthMonitor.sample()` is called from `kernel.py` inside `if self._metric_recorder:`
(after ADVANCEMENT). The kernel's `_event_listeners` list (list of callbacks) is the existing
push channel for `SimulationEvent` objects (`kernel.py` — `_event_listeners` is populated
by `V2EngineManager` in `engine_manager.py` L132). The monitor does not currently have
access to the kernel's event dispatch path.

**Simplest viable approach**: `EconomyHealthMonitor.sample()` returns both a snapshot
*and* a list of alert `SimulationEvent` objects. The caller (kernel) collects them and
dispatches via `_event_listeners`. This keeps the monitor stateless and decoupled.

### REST endpoint — no economy route yet
`src/api/routes/` has: `behavior.py`, `campaigns.py`, `control.py`, `decisions.py`,
`health.py` (single line, empty), `history.py`, `scenarios.py`, `search.py`, `state.py`.
No `economy.py` route exists.

`src/api/server.py` registers routes with `app.include_router(...)` under `/api/v1` prefix.
Adding `economy.py` follows the same pattern as `behavior.py` / `scenarios.py`.

### Accessing latest state for the REST endpoint
`V2EngineManager.latest_state` (engine_manager.py L217–219) returns the most recent
`AuthoritativeState` under `_state_lock`. The route can call `get_engine_manager()` from
`src/api/dependencies.py` and read `manager.latest_state`. Per-region health is computed
on-the-fly from `state.entities` (grouped by `e.region_id`) and the latest
`EconomyHealthMonitor.sample()` output — no separate durable store is needed.

### Region grouping
`EntityState.region_id: Optional[str]` (state.py L335–336) is the authoritative
per-entity region tag. `state.regions: Dict[str, RegionState]` (state.py L1006) holds
the canonical region registry. The REST endpoint should group alive entities by
`e.region_id`, compute per-region Gini, and compute per-region alert status.

### Alert thresholds (from ticket scope)
- `DEFLATION_RISK`: gini < threshold (ticket doesn't specify; use sentinel — needs a defined
  threshold; `transaction_velocity < 0.5` is a reasonable proxy, but velocity is stub=0.0).
  Actually ticket scope defines event kinds but defers thresholds to implementation.
  Safe defaults: `gini_coefficient > 0.7` → INFLATION_SPIRAL; `gini_coefficient > 0.8` → GOLD_HOARDING;
  `transaction_velocity == 0.0 for >= 200 ticks` → ECONOMIC_COLLAPSE; `gini_coefficient < 0.1 and velocity < 0.5` → DEFLATION_RISK.
  Since `transaction_velocity` is stub=0.0, ECONOMIC_COLLAPSE and DEFLATION_RISK cannot be
  reliably detected until E33C fills velocity. The AC only requires `INFLATION_SPIRAL` to be
  emitted in a 2000-tick rapid-gold-creation run — this is achievable if `gini > threshold`.

---

## Mechanics / Engine Constraints

- **Atomic Conservation Law** (03_economic_laws.md §1): alerts are read-only observations;
  no gold transfer occurs. No conservation constraint applies.
- **Durable State Rule**: Alert events must not be stored in `AuthoritativeState`. They are
  transient outputs emitted via event dispatch callbacks.
- **API boundary rule** (CLAUDE.md Architecture Rule): REST endpoint must return a
  shaped read model dict — not a raw `EconomyHealthSnapshot` or `AuthoritativeState`.
  A presenter function in `src/api/presenters/economy.py` (new) shapes the response.
- **Read-only law**: The GET endpoint reads `latest_state` under state lock; it never
  writes to `AuthoritativeState`.
- **No new TickPhase**: TickPhase enum is FROZEN. Alert evaluation is a read-only step
  inside the existing PERSISTENCE-phase hook where `sample()` already runs.

---

## Parity Ledger Overlap (IDs + status)

- **TOWN-177** (`verified`): EconomyHealthMonitor samples gold read-only into metric_windows.jsonl.
  Will need to be extended or a sibling entry added for alert emission.
- New entry **TOWN-178** required: alert events emitted by EconomyHealthMonitor when
  thresholds crossed; not stored in AuthoritativeState.

---

## Prior Work

- **TCK-20260619-E33A-HEALTH-MONITOR** (DONE): `src/economy/health_monitor.py`,
  8 unit tests pass, TOWN-177 verified, kernel wired.
- **TCK-20260619-E12A-BALANCE-MEASURE**: confirmed `e.inventory.gold` and `e.combat.alive`
  as canonical access paths.

---

## Risks and Open Questions

### Risk 1 — StateUpdate.events_add does not exist (HIGH)
The ticket scope says "emit events via `StateUpdate(events_add=[...])`". `StateUpdate`
has `world_events_add: List[WorldEvent]` — not a generic `events_add` for `SimulationEvent`.
**Decision**: emit `SimulationEvent` alert instances through the kernel's `_event_listeners`
callbacks, mirroring the existing event dispatch path. `EconomyHealthMonitor.sample()` will
return `(snapshot, alerts)` tuple (or `sample()` + new `check_alerts()` method). The kernel
caller dispatches alerts via its existing `_notify_event_listeners(alerts)` mechanism.

### Risk 2 — INFLATION_SPIRAL threshold (MEDIUM)
No canonical threshold is defined in docs/mechanics/03_economic_laws.md for "inflation spiral".
The AC requires a 2000-tick rapid-gold-creation run to emit ≥1 INFLATION_SPIRAL. A
`gini_coefficient > 0.7` threshold is a reasonable sentinel; this must be tested to fire
during the integration test. Implementation will use `INFLATION_SPIRAL_GINI_THRESHOLD = 0.7`.

### Risk 3 — transaction_velocity is stub (MEDIUM)
ECONOMIC_COLLAPSE requires "zero transactions for 200 ticks" but `transaction_velocity=0.0`
always (E33A stub). This means ECONOMIC_COLLAPSE would always trigger if threshold is
`velocity == 0`. Resolution: skip ECONOMIC_COLLAPSE alert when velocity is stub (add guard:
only emit if `velocity > 0.0 or tick_count_at_zero >= 200` — since velocity is always 0,
the 200-tick counter needs a stateful tracker). **Simplest**: ECONOMIC_COLLAPSE deferred
to E33C when velocity is wired; for E33B, only emit INFLATION_SPIRAL and GOLD_HOARDING
from Gini (no velocity dependency). DEFLATION_RISK also deferred.

### Risk 4 — REST endpoint data source (LOW)
The REST endpoint should return "per-region health state". The cleanest source is
computing per-region Gini live from `latest_state.entities` (grouped by `e.region_id`).
This is O(N) but N is small (≤100 entities in the API server scenario). The alert status
for a region comes from re-evaluating alert conditions on the per-region snapshot.

---

## Anti-Drift Hazards

1. **Do not add to WorldEvent/WorldEventCategory**: alerts are SimulationEvent subclasses,
   not WorldEvents.
2. **StateUpdate.events_add does not exist**: do not reference it; use event listener callbacks.
3. **transaction_velocity=0.0 stub**: ECONOMIC_COLLAPSE and DEFLATION_RISK must not
   fire unconditionally — guard them or defer to E33C.
4. **REST presenter must not expose raw AuthoritativeState**: use `EconomyPresenter` to
   shape the dict response.
5. **e.region_id can be None**: group None-region entities as "global" or skip them in
   per-region breakdown.
