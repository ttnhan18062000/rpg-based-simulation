from __future__ import annotations
import pytest

from src.simulation_quality.pillar_accumulator import PillarAccumulator
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord


def _make_record(event_id: str, delta: float, tags: tuple[str, ...] = ()) -> ScoreRecord:
    return ScoreRecord(
        tick=1,
        event_id=event_id,
        pillar=PillarId.ECONOMY,
        delta=delta,
        reason="test",
        event_type="test_event",
        entity_id=None,
        region_id=None,
        tags=tags,
    )


def test_add_updates_raw_score(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    acc.add(_make_record("e1", 3.0))
    assert acc.raw_score == pytest.approx(3.0)
    acc.add(_make_record("e2", 2.0))
    assert acc.raw_score == pytest.approx(5.0)


def test_add_updates_event_count(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    acc.add(_make_record("e1", 1.0))
    acc.add(_make_record("e2", -1.0))
    assert acc.event_count == 2


def test_add_updates_negative_count(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    acc.add(_make_record("e1", 3.0))
    acc.add(_make_record("e2", -2.0))
    acc.add(_make_record("e3", -5.0))
    assert acc.negative_count == 2


def test_duplicate_event_id_is_noop(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    acc.add(_make_record("dup-1", 10.0))
    acc.add(_make_record("dup-1", 10.0))
    assert acc.raw_score == pytest.approx(10.0)
    assert acc.event_count == 1


def test_worst_events_never_exceeds_max(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    for i in range(200):
        acc.add(_make_record(f"e{i}", -float(i + 1)))
    assert len(acc.worst_events) <= scoring_weights.detection.max_worst_events


def test_worst_events_sorted_by_abs_delta_desc(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    acc.add(_make_record("e1", -1.0))
    acc.add(_make_record("e2", -10.0))
    acc.add(_make_record("e3", -5.0))
    assert acc.worst_events[0].event_id == "e2"
    assert acc.worst_events[1].event_id == "e3"


def test_window_buffer_capped_at_maxlen(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    for i in range(500):
        acc.add(_make_record(f"e{i}", 1.0))
    assert len(acc.window_buffer) <= scoring_weights.detection.window_size


def test_loop_detection_fires_above_threshold(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights, loop_threshold=0.70)
    for i in range(180):
        acc.add(_make_record(f"e{i}", -1.0, tags=("zero_harvest",)))
    for i in range(180, 200):
        acc.add(_make_record(f"e{i}", 1.0, tags=("some_other_tag",)))
    assert "zero_harvest" in acc.loop_flags


def test_loop_detection_does_not_fire_below_threshold(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights, loop_threshold=0.70)
    # Fill window with only 30% of one tag — should never exceed 70% threshold
    for i in range(140):
        acc.add(_make_record(f"e{i}", 1.0, tags=("harvest_active",)))
    for i in range(140, 200):
        acc.add(_make_record(f"e{i}", 1.0, tags=("zero_harvest",)))
    # At most 60 out of 200 are zero_harvest — well below 0.70 threshold
    zero_harvest_count = sum(1 for r in acc.window_buffer if "zero_harvest" in r.tags)
    assert zero_harvest_count / len(acc.window_buffer) < 0.70
    assert "zero_harvest" not in acc.loop_flags


def test_snapshot_returns_copies_not_references(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    acc.add(_make_record("e1", -5.0))
    snap = acc.snapshot()
    assert isinstance(snap["worst_events"], tuple)
    assert isinstance(snap["window_buffer"], tuple)
    assert isinstance(snap["loop_flags"], frozenset)


def test_snapshot_worst_events_is_immutable_copy(scoring_weights):
    acc = PillarAccumulator(PillarId.ECONOMY, weights=scoring_weights)
    acc.add(_make_record("e1", -5.0))
    snap = acc.snapshot()
    original_len = len(snap["worst_events"])
    acc.add(_make_record("e2", -3.0))
    assert len(snap["worst_events"]) == original_len


def test_accumulator_respects_injected_window_size(scoring_weights):
    patched = scoring_weights.model_copy(
        update={"detection": scoring_weights.detection.model_copy(update={"window_size": 50})}
    )
    acc = PillarAccumulator(PillarId.ECONOMY, weights=patched)
    for i in range(100):
        acc.add(_make_record(f"e{i}", 1.0))
    assert len(acc.window_buffer) <= 50


def test_accumulator_respects_injected_loop_threshold(scoring_weights):
    patched = scoring_weights.model_copy(
        update={"detection": scoring_weights.detection.model_copy(update={"loop_threshold": 0.50})}
    )
    acc = PillarAccumulator(PillarId.ECONOMY, weights=patched)
    # 60 events tagged "x" out of 100 total = 60% — above 0.50, below 0.70
    for i in range(60):
        acc.add(_make_record(f"x{i}", 1.0, tags=("hot_tag",)))
    for i in range(40):
        acc.add(_make_record(f"y{i}", 1.0, tags=("other_tag",)))
    assert "hot_tag" in acc.loop_flags


# ---------------------------------------------------------------------------
# T-ACC-01 through T-ACC-05: last_event_tick tracking
# ---------------------------------------------------------------------------

def _make_record_at_tick(event_id: str, tick: int, delta: float) -> ScoreRecord:
    return ScoreRecord(
        tick=tick,
        event_id=event_id,
        pillar=PillarId.COMBAT,
        delta=delta,
        reason="test",
        event_type="test_event",
        entity_id=None,
        region_id=None,
        tags=(),
    )


def test_last_event_tick_zero_on_construction(scoring_weights):
    """T-ACC-01: last_event_tick is 0 on empty accumulator."""
    acc = PillarAccumulator(PillarId.COMBAT, weights=scoring_weights)
    assert acc.last_event_tick == 0


def test_last_event_tick_set_on_first_add(scoring_weights):
    """T-ACC-02: last_event_tick equals the tick of the first added event."""
    acc = PillarAccumulator(PillarId.COMBAT, weights=scoring_weights)
    acc.add(_make_record_at_tick("e1", tick=57, delta=2.0))
    assert acc.last_event_tick == 57


def test_last_event_tick_is_max_across_multiple_events(scoring_weights):
    """T-ACC-03: last_event_tick equals the maximum tick across all added events."""
    acc = PillarAccumulator(PillarId.COMBAT, weights=scoring_weights)
    acc.add(_make_record_at_tick("e1", tick=10, delta=1.0))
    acc.add(_make_record_at_tick("e2", tick=172, delta=2.0))
    acc.add(_make_record_at_tick("e3", tick=50, delta=1.0))
    assert acc.last_event_tick == 172


def test_last_event_tick_not_updated_by_duplicate_event(scoring_weights):
    """T-ACC-04: Duplicate event_id must not advance last_event_tick."""
    acc = PillarAccumulator(PillarId.COMBAT, weights=scoring_weights)
    acc.add(_make_record_at_tick("e1", tick=10, delta=1.0))
    # Same event_id but later tick — must be ignored
    acc.add(_make_record_at_tick("e1", tick=999, delta=1.0))
    assert acc.last_event_tick == 10


def test_last_event_tick_present_in_snapshot(scoring_weights):
    """T-ACC-05: last_event_tick appears in snapshot() dict."""
    acc = PillarAccumulator(PillarId.COMBAT, weights=scoring_weights)
    acc.add(_make_record_at_tick("e1", tick=42, delta=1.0))
    snap = acc.snapshot()
    assert "last_event_tick" in snap
    assert snap["last_event_tick"] == 42
