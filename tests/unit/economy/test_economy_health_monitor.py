"""Unit tests for EconomyHealthMonitor and EconomyHealthSnapshot.

Test plan reference: staging_artifacts/TCK-20260619-E33A-HEALTH-MONITOR/test_plan.md
Ticket: TCK-20260619-E33A-HEALTH-MONITOR
"""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.economy.health_monitor import EconomyHealthMonitor, EconomyHealthSnapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entity(eid: int, gold: int, alive: bool = True):
    """Build a minimal entity with a given gold balance and liveness."""
    builder = (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(hp=100, max_hp=100, atk=5, def_stat=5,
                attack_range=1, alive=alive, readiness=100.0)
        .inventory(gold=gold)
    )
    return builder.build()


def _make_state(entities: dict, tick: int = 100) -> AuthoritativeState:
    return AuthoritativeState(tick=tick, seed=42, entities=entities)


# ---------------------------------------------------------------------------
# TC-01: Gini coefficient computed correctly for known distributions
# ---------------------------------------------------------------------------

def test_gini_coefficient_computed_correctly():
    """Verify Gini formula against pre-verified distributions."""
    # Perfect equality → 0.0
    assert EconomyHealthMonitor._gini([10.0, 10.0, 10.0, 10.0]) == pytest.approx(0.0, abs=1e-9)

    # Perfect inequality (n=4): (n-1)/n = 0.75
    assert EconomyHealthMonitor._gini([0.0, 0.0, 0.0, 100.0]) == pytest.approx(0.75, abs=1e-9)

    # [1, 2, 3, 4]: cum=1+4+9+16=30; G=60/40−5/4=1.5−1.25=0.25
    assert EconomyHealthMonitor._gini([1.0, 2.0, 3.0, 4.0]) == pytest.approx(0.25, abs=1e-9)


# ---------------------------------------------------------------------------
# TC-02: Gini edge cases
# ---------------------------------------------------------------------------

def test_gini_edge_cases():
    """Empty list, all-zero, single entity, large uniform produce correct values."""
    # Empty list → 0.0
    assert EconomyHealthMonitor._gini([]) == 0.0

    # All zero → 0.0 (sum == 0 guard)
    assert EconomyHealthMonitor._gini([0.0, 0.0, 0.0]) == 0.0

    # Single entity → 0.0 (G = 2*1*v / (1*v) - 2/1 = 2 - 2 = 0)
    assert EconomyHealthMonitor._gini([50.0]) == pytest.approx(0.0, abs=1e-9)

    # Large uniform list → 0.0
    assert EconomyHealthMonitor._gini([100.0] * 1000) == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# TC-03: sample() returns None for off-window ticks
# ---------------------------------------------------------------------------

def test_sample_returns_none_off_window():
    """sample() must return None for ticks not on a WINDOW_SIZE boundary."""
    entity = _make_entity(1, gold=10)
    state = _make_state({1: entity})

    for tick in (1, 50, 99, 101, 150):
        # Override tick on state for each case
        state_at_tick = AuthoritativeState(tick=tick, seed=42, entities={1: entity})
        result = EconomyHealthMonitor.sample(state_at_tick, tick)
        assert result is None, f"Expected None at tick {tick}, got {result}"


# ---------------------------------------------------------------------------
# TC-04: sample() returns snapshot on window boundaries
# ---------------------------------------------------------------------------

def test_sample_returns_snapshot_on_window_boundary():
    """sample() must return an EconomyHealthSnapshot at multiples of WINDOW_SIZE."""
    entity = _make_entity(1, gold=10)

    for tick in (100, 200, 500, 1000):
        state = AuthoritativeState(tick=tick, seed=42, entities={1: entity})
        result = EconomyHealthMonitor.sample(state, tick)
        assert result is not None, f"Expected snapshot at tick {tick}, got None"
        assert isinstance(result, EconomyHealthSnapshot)
        assert result.tick == tick


# ---------------------------------------------------------------------------
# TC-05: sample() reads e.inventory.gold (not item stacks)
# ---------------------------------------------------------------------------

def test_sample_reads_inventory_gold_not_items():
    """Wealth source must be e.inventory.gold — not gold_coin item stacks.

    entity_b has gold_coin item stacks but inventory.gold=0; its contribution
    to the Gini must be 0, not 50. Wealth vector is [0, 100, 200] → G≈0.4444.
    """
    from src.core.state import ItemStack

    entity_a = _make_entity(1, gold=100)   # inventory.gold=100, no items
    entity_b = (                            # inventory.gold=0, has gold_coin items
        V2EntityBuilder(2)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(hp=100, max_hp=100, atk=5, def_stat=5,
                attack_range=1, alive=True, readiness=100.0)
        .inventory(gold=0, items=[ItemStack("gold_coin", 50)])
        .build()
    )
    entity_c = _make_entity(3, gold=200)   # inventory.gold=200

    state = AuthoritativeState(tick=100, seed=42, entities={1: entity_a, 2: entity_b, 3: entity_c})
    snapshot = EconomyHealthMonitor.sample(state, 100)

    assert snapshot is not None
    # Wealth vector [0, 100, 200]: cum=0+200+600=800; G=1600/900 - 4/3 = 4/9
    expected_gini = 4 / 9
    assert snapshot.gini_coefficient == pytest.approx(expected_gini, abs=1e-6)


# ---------------------------------------------------------------------------
# TC-06: sample() excludes dead entities from Gini
# ---------------------------------------------------------------------------

def test_sample_excludes_dead_entities():
    """Dead entities (combat.alive=False) must not contribute to wealth distribution."""
    entity_alive_a = _make_entity(1, gold=100, alive=True)
    entity_alive_b = _make_entity(2, gold=200, alive=True)
    entity_dead   = _make_entity(3, gold=999, alive=False)  # must be excluded

    state = AuthoritativeState(tick=100, seed=42, entities={
        1: entity_alive_a,
        2: entity_alive_b,
        3: entity_dead,
    })
    snapshot = EconomyHealthMonitor.sample(state, 100)

    assert snapshot is not None
    # Wealth vector [100, 200]: cum=100+400=500; G=1000/600 - 3/2 = 1/6
    expected_gini = 1 / 6
    assert snapshot.gini_coefficient == pytest.approx(expected_gini, abs=1e-6)


# ---------------------------------------------------------------------------
# TC-07: snapshot fields present and in valid ranges
# ---------------------------------------------------------------------------

def test_snapshot_fields_present():
    """EconomyHealthSnapshot must have gini_coefficient∈[0,1], transaction_velocity: float, avg_price_index: dict."""
    entity = _make_entity(1, gold=100)
    state = AuthoritativeState(tick=100, seed=42, entities={1: entity})
    snapshot = EconomyHealthMonitor.sample(state, 100)

    assert snapshot is not None
    assert isinstance(snapshot.gini_coefficient, float)
    assert 0.0 <= snapshot.gini_coefficient <= 1.0
    assert isinstance(snapshot.transaction_velocity, float)
    assert isinstance(snapshot.avg_price_index, dict)
    # Stubs per plan: velocity=0.0, price_index={}
    assert snapshot.transaction_velocity == 0.0
    assert snapshot.avg_price_index == {}


# ---------------------------------------------------------------------------
# TC-08: sample() does not mutate state
# ---------------------------------------------------------------------------

def test_snapshot_is_not_mutating_state():
    """State fingerprint must be unchanged before and after sample()."""
    entity = _make_entity(1, gold=100)
    state = AuthoritativeState(tick=100, seed=42, entities={1: entity})

    fp_before = state.fingerprint()
    EconomyHealthMonitor.sample(state, 100)
    fp_after = state.fingerprint()

    assert fp_before == fp_after, "sample() must not mutate AuthoritativeState"


# ---------------------------------------------------------------------------
# TC-09: 2000-tick integration — metric_windows.jsonl has ≥20 entries with economy fields
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_metric_windows_produced_in_2000_tick_run(tmp_path):
    """Integration: 2000-tick run must produce ≥20 metric_windows.jsonl entries
    with economy_gini_coefficient, economy_transaction_velocity, and
    economy_avg_price_index_json fields present at window boundaries."""
    import json
    from src.observability.reporting.metric_recorder import MetricWindowRecorder
    from src.economy.health_monitor import EconomyHealthMonitor

    run_dir = str(tmp_path / "run")
    recorder = MetricWindowRecorder(run_id="test-e33a", run_dir=run_dir, window_size=100)

    entity = _make_entity(1, gold=50)
    base_state = AuthoritativeState(tick=0, seed=42, entities={1: entity})

    for tick in range(1, 2001):
        state = AuthoritativeState(tick=tick, seed=42, entities={1: entity})

        # Mirror what kernel.py does: sample BEFORE record_tick
        try:
            snapshot = EconomyHealthMonitor.sample(state, tick)
            if snapshot is not None:
                recorder.record_economy_snapshot(snapshot)
        except Exception:
            pass

        recorder.record_tick(
            tick=tick,
            world_metrics=None,
            pressure_signals=None,
            runtime_status=None,
            event_count_delta=0,
            violation_count_delta=0,
        )

    recorder.shutdown(2000)

    # Parse JSONL and verify
    jsonl_path = tmp_path / "run" / "metric_windows.jsonl"
    assert jsonl_path.exists(), "metric_windows.jsonl was not created"

    entries = [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]
    assert len(entries) >= 20, f"Expected ≥20 entries, got {len(entries)}"

    # All entries must carry the economy fields (populated at window boundary ticks)
    economy_entries = [e for e in entries if e.get("economy_gini_coefficient") is not None]
    assert len(economy_entries) >= 20, (
        f"Expected ≥20 entries with economy_gini_coefficient, got {len(economy_entries)}"
    )

    for entry in economy_entries:
        assert "economy_gini_coefficient" in entry
        assert "economy_transaction_velocity" in entry
        assert "economy_avg_price_index_json" in entry
        assert isinstance(entry["economy_gini_coefficient"], float)
        assert isinstance(entry["economy_transaction_velocity"], float)
        # avg_price_index_json must be a valid JSON string encoding a dict
        parsed_price = json.loads(entry["economy_avg_price_index_json"])
        assert isinstance(parsed_price, dict)
