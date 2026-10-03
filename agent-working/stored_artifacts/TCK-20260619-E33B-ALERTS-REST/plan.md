---
ticket_id: TCK-20260619-E33B-ALERTS-REST
phase: plan
date: 2026-06-21
---

# Implementation Plan: Economic Alert Events + REST Endpoint

## Ordered Steps

### Step 1 — Add 4 alert `SimulationEvent` subclasses to `src/observability/events.py`

**Files:** `src/observability/events.py`

Add four typed `SimulationEvent` subclasses at the end of the file:
- `DeflationRiskEvent` — `event_type="DEFLATION_RISK"`, `event_category="economy"`, `severity="WARNING"`, `source_system="economy_health_monitor"`
- `InflationSpiralEvent` — `event_type="INFLATION_SPIRAL"`, `event_category="economy"`, `severity="WARNING"`
- `EconomicCollapseEvent` — `event_type="ECONOMIC_COLLAPSE"`, `event_category="economy"`, `severity="CRITICAL"`
- `GoldHoardingEvent` — `event_type="GOLD_HOARDING"`, `event_category="economy"`, `severity="WARNING"`

Each carries: `gini_coefficient: float`, `region_id: Optional[str] = None` as extra fields.
Default message set in `__init__` (following existing pattern in `CombatDamageEvent`).

**Scope guard**: do NOT add to `WorldEventCategory` or `WorldEvent`. Do NOT add a new `EventCategory` literal — `"economy"` already exists.

**Dependency**: none (first step).

**AC mapped**: "4 alert event kinds" defined.

---

### Step 2 — Add `check_alerts()` to `EconomyHealthMonitor` in `src/economy/health_monitor.py`

**Files:** `src/economy/health_monitor.py`

Add a new `@staticmethod` method:

```python
INFLATION_SPIRAL_GINI_THRESHOLD: float = 0.7
GOLD_HOARDING_GINI_THRESHOLD: float = 0.8

@staticmethod
def check_alerts(
    snapshot: EconomyHealthSnapshot,
    tick: int,
    region_id: Optional[str] = None,
) -> list[SimulationEvent]:
    """Evaluate alert conditions on a snapshot. Returns list of alert events (may be empty)."""
    alerts = []
    gini = snapshot.gini_coefficient
    if gini > EconomyHealthMonitor.GOLD_HOARDING_GINI_THRESHOLD:
        alerts.append(GoldHoardingEvent(tick=tick, gini_coefficient=gini, region_id=region_id))
    elif gini > EconomyHealthMonitor.INFLATION_SPIRAL_GINI_THRESHOLD:
        alerts.append(InflationSpiralEvent(tick=tick, gini_coefficient=gini, region_id=region_id))
    # ECONOMIC_COLLAPSE and DEFLATION_RISK deferred to E33C (velocity is stub=0.0)
    return alerts
```

Import: add `from src.observability.events import (InflationSpiralEvent, GoldHoardingEvent, EconomicCollapseEvent, DeflationRiskEvent, SimulationEvent)` at top of file.

**Scope guard**: do NOT modify `sample()`. Do NOT store alerts in any durable field. Do NOT import from kernel.

**Dependency**: Step 1 must be complete.

**AC mapped**: "alert event kinds wired after snapshot computed".

---

### Step 3 — Wire alert dispatch in `src/engine/kernel.py`

**Files:** `src/engine/kernel.py`

In the existing block where `EconomyHealthMonitor.sample()` is called (inside `if self._metric_recorder:`):

```python
# Existing (from E33A):
snapshot = EconomyHealthMonitor.sample(self._state, self._tick)
if snapshot is not None:
    self._metric_recorder.record_economy_snapshot(snapshot)
    # NEW — evaluate and dispatch alerts
    from src.economy.health_monitor import EconomyHealthMonitor as _EHM
    alerts = _EHM.check_alerts(snapshot, tick=self._tick)
    if alerts and self._event_listeners:
        for cb in self._event_listeners:
            try:
                cb(alerts)
            except Exception:
                pass
```

Keep the `try/except` guard around the whole block as in E33A's implementation to prevent monitor errors from failing ticks.

**Scope guard**: do NOT add a new TickPhase. Do NOT store alerts on state. Only modify inside the existing `if self._metric_recorder:` guard.

**Dependency**: Steps 1 and 2.

**AC mapped**: "alert events emitted via authoritative path (PERSISTENCE phase hook)".

---

### Step 4 — Add `EconomyPresenter` in `src/api/presenters/economy.py` (new)

**Files:** `src/api/presenters/economy.py` (new)

```python
class EconomyPresenter:
    @staticmethod
    def present_health(state: AuthoritativeState) -> dict:
        """Shape per-region economy health from latest state. No raw domain models."""
        ...
```

Logic:
- Group alive entities by `e.region_id` (None → `"global"`).
- For each region group: compute `EconomyHealthMonitor._gini([e.inventory.gold for e in group])`.
- Evaluate `EconomyHealthMonitor.check_alerts(snapshot, tick=state.tick, region_id=region_id)` → pick first alert's `event_type` or `null`.
- Return: `{"tick": state.tick, "regions": {region_id: {"gini": float, "transaction_velocity": 0.0, "alert": str|null}}}`.

**Scope guard**: presenter is read-only; no mutation of state. Only imports from `src/economy/` and `src/core/`.

**Dependency**: Steps 1 and 2.

---

### Step 5 — Add `GET /api/v1/economy/health` in `src/api/routes/economy.py` (new)

**Files:** `src/api/routes/economy.py` (new)

```python
router = APIRouter(prefix="/economy", tags=["Economy"])

@router.get("/health")
async def get_economy_health():
    manager = get_engine_manager()
    state = manager.latest_state
    if state is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    return EconomyPresenter.present_health(state)
```

**Scope guard**: no query params for now; no POST; no write operations.

**Dependency**: Step 4.

---

### Step 6 — Register economy router in `src/api/server.py`

**Files:** `src/api/server.py`

Add after existing route imports:
```python
from src.api.routes import economy
app.include_router(economy.router, prefix="/api/v1")
```

**Scope guard**: add only this import/include block; do not restructure server.py.

**Dependency**: Step 5.

---

### Step 7 — Write unit tests

**Files:**
- `tests/unit/economy/test_economy_alerts.py` (new)
- `tests/unit/api/test_economy_route.py` (new)

Implement TC-B01 through TC-B08 from test_plan.md.

**Dependency**: Steps 1–6.

---

### Step 8 — Write integration test

**Files:** `tests/integration/scenarios/test_macro_economy.py` (new or append)

Implement TC-B09: `test_inflation_spiral_alert_emitted` — 2000-tick run with rapid gold
creation using a modified entity list. Since gini depends on wealth disparity, the test
must seed entities with very unequal gold (e.g., one entity with 10000 gold, rest with 1).
Register a list-callback event listener before the run; assert ≥1 `InflationSpiralEvent`
is captured after the run.

Mark `@pytest.mark.slow`.

**Dependency**: Steps 1–6.

---

## Dependency Map

```
Step 1 → Step 2 → Step 3
Step 1, 2 → Step 4 → Step 5 → Step 6
Step 1-6 → Step 7
Step 1-6 → Step 8
```

## Scope Guards (global)

- Do NOT add `events_add` to `StateUpdate` — this field does not exist and is not needed.
- Do NOT add to `WorldEventCategory` or `WorldEvent`.
- Do NOT add a new `TickPhase` value.
- Do NOT store alert events in `AuthoritativeState`.
- Do NOT expose raw `EconomyHealthSnapshot` or `AuthoritativeState` from the API.
- Do NOT implement ECONOMIC_COLLAPSE or DEFLATION_RISK logic that depends on `transaction_velocity` (it is stub=0.0 in E33B).

## Acceptance Criteria Mapped to Steps

| AC | Steps |
|---|---|
| 4 alert event kinds defined | Step 1 |
| Alert evaluation wired after snapshot computed | Steps 2, 3 |
| `test_inflation_spiral_alert_emitted` passes | Steps 1, 2, 3, 8 |
| `GET /api/v1/economy/health` returns per-region health | Steps 4, 5, 6 |

## Deviations

_None yet — to be filled if implementation differs from plan._
