---
ticket_id: TCK-20260619-E33A-HEALTH-MONITOR
phase: test_plan
date: 2026-06-21
---

# Test Plan: EconomyHealthMonitor + Metrics

## Regression Surface (existing tests that must pass)

These tests exercise code paths that the monitor touches or neighbours. Run them
before and after the implementation to confirm no regression.

| Test | Location | Why it matters |
|---|---|---|
| `test_full_tick_determinism` | `tests_v2/test_deterministic_baseline.py` | Monitor must not perturb state hash |
| `test_subsystem_order_documentation` | `tests_v2/test_deterministic_baseline.py` | Phase order is frozen; no new TickPhase |
| `tests_v2/replay/` (all) | `tests_v2/replay/` | Monitor is observability — must not affect replay output |
| `test_resource_conservation_v2` | `tests/rpg/test_resource_conservation_v2.py` | Gold totals used by monitor must be conservation-correct |
| Metric recorder tests | `tests/observability/` (any) | `MetricWindowRecorder`/`MetricsService` must still produce valid output |

Scoped run:
```bash
pytest tests_v2/test_deterministic_baseline.py tests_v2/replay/ tests/rpg/test_resource_conservation_v2.py -x -v --tb=short
```

---

## New Tests Required (per AC)

### Test file: `tests/unit/economy/test_economy_health_monitor.py`

#### TC-01 · `test_gini_coefficient_computed_correctly` (AC-required by name)

Verify the Gini formula produces the expected value for a known wealth distribution.

```python
from src.engine.economy_health_monitor import EconomyHealthMonitor

def test_gini_coefficient_computed_correctly():
    # Perfect equality → Gini = 0.0
    assert EconomyHealthMonitor._gini([10, 10, 10, 10]) == pytest.approx(0.0, abs=1e-9)
    # Perfect inequality (one entity has all) → Gini ≈ (n-1)/n
    assert EconomyHealthMonitor._gini([0, 0, 0, 100]) == pytest.approx(0.75, abs=1e-6)
    # Known distribution: [1, 2, 3, 4] → verify against formula
    # sorted=[1,2,3,4], n=4, sum=10
    # cum = 1*1 + 2*2 + 3*3 + 4*4 = 1+4+9+16 = 30
    # G = (2*30)/(4*10) - 5/4 = 1.5 - 1.25 = 0.25
    assert EconomyHealthMonitor._gini([1, 2, 3, 4]) == pytest.approx(0.25, abs=1e-6)
```

#### TC-02 · `test_gini_edge_cases`

```python
def test_gini_edge_cases():
    # Empty list → 0.0 (no entities)
    assert EconomyHealthMonitor._gini([]) == 0.0
    # All-zero wealth → 0.0 (avoid division by zero)
    assert EconomyHealthMonitor._gini([0, 0, 0]) == 0.0
    # Single entity → 0.0 (no inequality possible)
    assert EconomyHealthMonitor._gini([42]) == 0.0
    # Large uniform → still 0.0
    assert EconomyHealthMonitor._gini([100] * 100) == pytest.approx(0.0, abs=1e-9)
```

#### TC-03 · `test_sample_returns_none_off_window`

Verify the monitor returns `None` for ticks that are not multiples of WINDOW_SIZE.

```python
def test_sample_returns_none_off_window(minimal_state):
    for tick in [1, 50, 99, 101, 150]:
        result = EconomyHealthMonitor.sample(minimal_state, tick)
        assert result is None, f"Expected None at tick {tick}, got {result}"
```

#### TC-04 · `test_sample_returns_snapshot_on_window_boundary`

Verify that ticks that are exact multiples of WINDOW_SIZE return a populated snapshot.

```python
def test_sample_returns_snapshot_on_window_boundary(minimal_state):
    for tick in [100, 200, 500, 1000]:
        result = EconomyHealthMonitor.sample(minimal_state, tick)
        assert result is not None, f"Expected snapshot at tick {tick}"
        assert hasattr(result, "gini_coefficient")
        assert hasattr(result, "transaction_velocity")
        assert hasattr(result, "avg_price_index")
        assert result.tick == tick
```

#### TC-05 · `test_sample_reads_inventory_gold_not_items`

Verify gold is read from `inventory.gold`, not from `inventory.items` item stacks,
so the Gini is computed over actual entity wealth.

```python
def test_sample_reads_inventory_gold_not_items(state_with_entities):
    # state_with_entities has 3 entities:
    #   entity_a: inventory.gold = 100, no gold_coin items
    #   entity_b: inventory.gold = 0,   has ItemStack("gold_coin", quantity=50)
    #   entity_c: inventory.gold = 200, no gold_coin items
    # If gold is read from inventory.gold → wealth = [100, 0, 200]
    # Gini([0, 100, 200]) == known value ~0.333...
    result = EconomyHealthMonitor.sample(state_with_entities, 100)
    assert result is not None
    # Gini of [0, 100, 200]: sorted=[0,100,200], n=3, sum=300
    # cum = 1*0 + 2*100 + 3*200 = 0+200+600 = 800
    # G = (2*800)/(3*300) - 4/3 = 1600/900 - 4/3 = 16/9 - 12/9 = 4/9 ≈ 0.4444
    assert result.gini_coefficient == pytest.approx(4/9, abs=1e-6)
```

#### TC-06 · `test_sample_excludes_dead_entities`

Dead entities (combat.alive == False) must not contribute to the wealth distribution.

```python
def test_sample_excludes_dead_entities(state_with_mixed_alive):
    # state has 2 alive entities (gold=100, gold=200) and 1 dead entity (gold=999)
    # Gini must be over [100, 200] only
    result = EconomyHealthMonitor.sample(state_with_mixed_alive, 100)
    assert result is not None
    # Gini([100, 200]): sorted=[100,200], n=2, sum=300
    # cum = 1*100 + 2*200 = 100+400 = 500
    # G = (2*500)/(2*300) - 3/2 = 1000/600 - 3/2 = 5/3 - 3/2 = 10/6 - 9/6 = 1/6 ≈ 0.1667
    assert result.gini_coefficient == pytest.approx(1/6, abs=1e-6)
```

#### TC-07 · `test_snapshot_fields_present`

Validate `EconomyHealthSnapshot` has all three required fields with correct types.

```python
def test_snapshot_fields_present(minimal_state):
    result = EconomyHealthMonitor.sample(minimal_state, 100)
    assert isinstance(result.gini_coefficient, float)
    assert isinstance(result.transaction_velocity, float)
    assert isinstance(result.avg_price_index, dict)
    assert 0.0 <= result.gini_coefficient <= 1.0
```

#### TC-08 · `test_snapshot_is_not_mutating_state`

Confirm the state fingerprint is identical before and after a sample call.

```python
def test_snapshot_is_not_mutating_state(minimal_state):
    fingerprint_before = minimal_state.fingerprint()
    EconomyHealthMonitor.sample(minimal_state, 100)
    fingerprint_after = minimal_state.fingerprint()
    assert fingerprint_before == fingerprint_after
```

#### TC-09 · `test_metric_windows_produced_in_2000_tick_run` (integration / AC verification)

Verify that a 2000-tick run produces `metric_windows.jsonl` with ≥20 entries
containing the required economy health fields.

```python
import json, pathlib

def test_metric_windows_produced_in_2000_tick_run(tmp_path, standard_kernel_factory):
    kernel = standard_kernel_factory(ticks=2000, run_dir=tmp_path)
    for _ in range(2000):
        kernel.tick_once()
    kernel.shutdown()

    mw_path = pathlib.Path(tmp_path) / kernel.run_id / "metric_windows.jsonl"
    assert mw_path.exists(), "metric_windows.jsonl must be written"

    lines = [json.loads(l) for l in mw_path.read_text().splitlines() if l.strip()]
    assert len(lines) >= 20, f"Expected ≥20 entries, got {len(lines)}"

    for entry in lines:
        metrics = json.loads(entry["metrics_json"]) if "metrics_json" in entry else entry
        assert "gini_coefficient" in metrics, f"Missing gini_coefficient in entry: {entry}"
        assert "transaction_velocity" in metrics
        assert "avg_price_index" in metrics
```

---

## Scoped Pytest Commands

```bash
# Primary AC test (named in ticket)
pytest tests/unit/economy/test_economy_health_monitor.py::test_gini_coefficient_computed_correctly -x -v

# Full new test file
pytest tests/unit/economy/test_economy_health_monitor.py -x -v

# Regression surface (no slow tests)
pytest tests_v2/test_deterministic_baseline.py tests_v2/replay/ tests/rpg/test_resource_conservation_v2.py -x -v --tb=short -m "not slow"

# Integration (2000-tick run — mark as slow)
pytest tests/unit/economy/test_economy_health_monitor.py::test_metric_windows_produced_in_2000_tick_run -v -m slow
```

---

## Anti-Drift Test Guards

### Guard 1 — `inventory.gold` is the wealth source
`TC-05` (`test_sample_reads_inventory_gold_not_items`) is the sentinel against
the gold access path drift. If someone switches the implementation to scan
`inventory.items` for `gold_coin` stacks, `TC-05` will fail because the entity
holding `gold` in `inventory.gold` will contribute zero to the Gini, producing
a wrong coefficient.

### Guard 2 — `combat.alive` is the liveness field
`TC-06` (`test_sample_excludes_dead_entities`) will catch any attempt to use
`e.is_alive` (AttributeError) or `e.alive` (AttributeError). The test fixture
explicitly sets `combat.alive = False` on the dead entity and verifies the wealth
vector excludes it.

### Guard 3 — Read-only contract
`TC-08` (`test_snapshot_is_not_mutating_state`) compares `state.fingerprint()`
before and after a sample call. Any accidental write to state — including setting
a field via `object.__setattr__` — will be caught by the fingerprint check.

### Guard 4 — Window boundary is exact
`TC-03` and `TC-04` together ensure `tick % WINDOW_SIZE == 0` is the exact gate,
not `tick % WINDOW_SIZE < threshold` or similar drift. Both off-boundary and
on-boundary ticks are explicitly tested.

### Guard 5 — No new TickPhase
The regression test `test_subsystem_order_documentation` in
`tests_v2/test_deterministic_baseline.py` verifies the phase sequence. If anyone
adds a new `TickPhase` enum value for the monitor, this test will fail. The monitor
must be wired as a hook inside an existing phase (PERSISTENCE), not as a new phase.

### Guard 6 — Gini formula stability
`TC-01` pins three known correct values (perfect equality, perfect inequality,
[1,2,3,4] distribution). If the formula is accidentally refactored (e.g. 1-indexed
vs 0-indexed enumerate), at least one known value will drift and the test will fail.
These are not fuzzy bounds — they are exact floating-point expectations with tight
tolerances.
