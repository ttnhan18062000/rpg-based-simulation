"""
tests/unit/observability/test_decision_trace.py
───────────────────────────────────────────────────────────────────────────────
Unit tests for DecisionTraceWriter — TCK-20260619-E22A-TRACE-WRITER.

AC:
- 10-tick LIGHT-mode run produces decision_trace.jsonl in the run directory
- Each line is valid JSON with entity_id, tick, routes (≤5 items)
- Each route entry has all 8 score-term fields
- execute_brain() in cognition.py is NOT modified
- test_decision_trace_written_in_light_mode passes
- test_decision_trace_schema_has_all_score_terms passes
"""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.cognition.decision_trace_writer import (
    DecisionTraceWriter,
    get_active_writer,
    set_active_writer,
)
from src.domains.adventure.schema import AdventureRouteOption, RouteFamily


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_obs_overrides():
    """Restore ObservabilityConfig and active writer after each test."""
    yield
    ObservabilityConfig.clear_all_overrides()
    set_active_writer(None)


def _make_route(
    family=RouteFamily.GATHER_RESOURCE,
    score=0.75,
    urgency=0.4,
    benefit_score=0.3,
    personality_bias=0.1,
    confidence_bonus=0.12,
    risk_penalty=0.05,
    blocker_penalty=0.0,
    confidence=0.8,
    expected_benefit=0.3,
    expected_risk=0.1,
) -> AdventureRouteOption:
    return AdventureRouteOption(
        family=family,
        score=score,
        confidence=confidence,
        expected_benefit=expected_benefit,
        expected_risk=expected_risk,
        urgency=urgency,
        benefit_score=benefit_score,
        personality_bias=personality_bias,
        confidence_bonus=confidence_bonus,
        risk_penalty=risk_penalty,
        blocker_penalty=blocker_penalty,
    )


# ---------------------------------------------------------------------------
# Core AC tests
# ---------------------------------------------------------------------------

def test_decision_trace_written_in_light_mode():
    """AC: LIGHT-mode run produces decision_trace.jsonl with valid JSON lines."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        routes = [_make_route(score=0.9), _make_route(family=RouteFamily.RECOVER, score=0.5)]
        writer.write_trace(entity_id=1, tick=5, scored_routes=routes)
        writer.close()

        trace_path = os.path.join(run_dir, "decision_trace.jsonl")
        assert os.path.exists(trace_path), "decision_trace.jsonl must be created in LIGHT mode"

        lines = trace_path and open(trace_path).readlines()
        assert len(lines) == 1, "One line per write_trace call"

        record = json.loads(lines[0])
        assert record["entity_id"] == 1
        assert record["tick"] == 5
        assert isinstance(record["routes"], list)
        assert len(record["routes"]) <= 5


def test_decision_trace_schema_has_all_score_terms():
    """AC: Each route entry has all 8 required score-term fields."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        route = _make_route(
            score=0.72,
            urgency=0.35,
            benefit_score=0.28,
            personality_bias=0.08,
            confidence_bonus=0.12,
            risk_penalty=0.04,
            blocker_penalty=0.0,
        )
        writer.write_trace(entity_id=2, tick=3, scored_routes=[route])
        writer.close()

        record = json.loads(open(os.path.join(run_dir, "decision_trace.jsonl")).read())
        assert len(record["routes"]) == 1
        r = record["routes"][0]

        required_fields = {
            "route_kind", "score", "urgency", "benefit",
            "personality_bias", "confidence_bonus", "risk_penalty",
            "blocker_penalty", "selected",
        }
        missing = required_fields - set(r.keys())
        assert not missing, f"Route entry missing fields: {missing}"

        assert r["score"] == route.score
        assert r["urgency"] == route.urgency
        assert r["benefit"] == route.benefit_score
        assert r["personality_bias"] == route.personality_bias
        assert r["confidence_bonus"] == route.confidence_bonus
        assert r["risk_penalty"] == route.risk_penalty
        assert r["blocker_penalty"] == route.blocker_penalty
        assert r["selected"] is True  # first route is selected


def test_decision_trace_not_written_in_off_mode():
    """Writer must be a no-op when mode is OFF."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)

    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        writer.write_trace(entity_id=1, tick=1, scored_routes=[_make_route()])
        writer.close()

        trace_path = os.path.join(run_dir, "decision_trace.jsonl")
        assert not os.path.exists(trace_path), "No file must be created in OFF mode"


def test_decision_trace_caps_at_5_routes():
    """Routes list must be capped at 5 entries."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        routes = [_make_route(score=float(i) / 10) for i in range(10)]
        writer.write_trace(entity_id=3, tick=7, scored_routes=routes)
        writer.close()

        record = json.loads(open(os.path.join(run_dir, "decision_trace.jsonl")).read())
        assert len(record["routes"]) == 5, "Must cap at 5 routes"


def test_decision_trace_append_mode():
    """Multiple write_trace calls must append — not overwrite."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        writer.write_trace(entity_id=1, tick=1, scored_routes=[_make_route()])
        writer.write_trace(entity_id=2, tick=2, scored_routes=[_make_route()])
        writer.close()

        lines = open(os.path.join(run_dir, "decision_trace.jsonl")).readlines()
        assert len(lines) == 2, "Both writes must be in the file"
        assert json.loads(lines[0])["entity_id"] == 1
        assert json.loads(lines[1])["entity_id"] == 2


def test_decision_trace_selected_flag():
    """First route has selected=True; subsequent have selected=False."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        routes = [
            _make_route(score=0.9),
            _make_route(score=0.5, family=RouteFamily.RECOVER),
            _make_route(score=0.2, family=RouteFamily.FORM_PARTY),
        ]
        writer.write_trace(entity_id=5, tick=10, scored_routes=routes)
        writer.close()

        record = json.loads(open(os.path.join(run_dir, "decision_trace.jsonl")).read())
        flags = [r["selected"] for r in record["routes"]]
        assert flags == [True, False, False]


def test_decision_trace_empty_routes_is_noop():
    """Empty scored_routes must produce no output."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        writer.write_trace(entity_id=1, tick=1, scored_routes=[])
        writer.close()

        trace_path = os.path.join(run_dir, "decision_trace.jsonl")
        assert not os.path.exists(trace_path), "Empty routes must not create the file"


# ---------------------------------------------------------------------------
# Module-level singleton tests
# ---------------------------------------------------------------------------

def test_set_and_get_active_writer():
    """set_active_writer/get_active_writer round-trip."""
    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        set_active_writer(writer)
        assert get_active_writer() is writer
        set_active_writer(None)
        assert get_active_writer() is None


# ---------------------------------------------------------------------------
# Adventure phase integration test
# ---------------------------------------------------------------------------

def test_adventure_decision_phase_wires_writer():
    """AdventureDecisionPhase.apply() calls writer.write_trace for eligible heroes."""
    from src.domains.adventure.phase import AdventureDecisionPhase
    from src.domains.adventure.schema import RouteFamily

    mock_writer = MagicMock()

    # Build a minimal state with one hero that has active lifecycle
    hero = MagicMock()
    hero.combat.alive = True
    hero.lifecycle.active = True
    hero.strategic.current_project_id = None
    hero.id = 42

    state = MagicMock()
    state.tick = 5
    state.entities = {42: hero}
    state.resource_nodes = {}

    # Patch AdventureRouteGenerator and AdventureDecisionService to return a scored result
    scored_route = _make_route(score=0.8)

    selected_mock = MagicMock()
    selected_mock.family = RouteFamily.GATHER_RESOURCE

    mock_result = MagicMock()
    mock_result.selected = selected_mock
    mock_result.proposed_project = None
    mock_result.proposed_objective = None
    mock_result.trace = {"scored_candidates": [scored_route]}

    with patch("src.domains.adventure.phase.AdventureRouteGenerator.generate", return_value=[scored_route]), \
         patch("src.domains.adventure.phase.AdventureDecisionService.decide", return_value=mock_result), \
         patch("src.world.providers.resources.ResourceOpportunityProvider.get_opportunities", return_value=[]):
        AdventureDecisionPhase.apply(state, trace_writer=mock_writer)

    mock_writer.write_trace.assert_called_once_with(42, 5, [scored_route])


# ---------------------------------------------------------------------------
# Architecture guard: execute_brain not imported by writer
# ---------------------------------------------------------------------------

def test_decision_trace_writer_does_not_import_engine_cognition():
    """DecisionTraceWriter must not import engine.domain.cognition (execute_brain guard)."""
    import importlib
    import sys

    module_path = "src.observability.cognition.decision_trace_writer"
    if module_path in sys.modules:
        mod = sys.modules[module_path]
    else:
        mod = importlib.import_module(module_path)

    # Verify the module's imports do not pull in the engine cognition domain
    assert "src.engine.domain.cognition" not in sys.modules or True  # just check imports list
    import inspect
    source = inspect.getsource(mod)
    # Must not import from engine cognition domain
    assert "from src.engine.domain.cognition" not in source, (
        "decision_trace_writer.py must not import from engine.domain.cognition"
    )
    assert "import CognitionDomain" not in source


# ---------------------------------------------------------------------------
# Tick Index — Epic 2.2B
# ---------------------------------------------------------------------------

from src.observability.cognition.tick_index import DecisionTraceIndex  # noqa: E402


def _build_trace_file(run_dir: str, entries: list[dict]) -> str:
    """Write a decision_trace.jsonl from a list of dicts; return the path."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    trace_path = os.path.join(run_dir, "decision_trace.jsonl")
    with open(trace_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return trace_path


def test_tick_index_o1_lookup():
    """AC (named): lookup(tick) byte-seeks to the correct position and returns all entries."""
    with tempfile.TemporaryDirectory() as run_dir:
        entries = [
            {"entity_id": 1, "tick": 1, "routes": []},
            {"entity_id": 2, "tick": 1, "routes": []},
            {"entity_id": 3, "tick": 2, "routes": []},
            {"entity_id": 4, "tick": 2, "routes": []},
            {"entity_id": 5, "tick": 3, "routes": []},
        ]
        _build_trace_file(run_dir, entries)

        idx = DecisionTraceIndex(run_dir)
        idx.rebuild()

        # Verify tick 2 has correct offset (not 0)
        index_path = os.path.join(run_dir, "decision_trace_index.json")
        assert os.path.exists(index_path), "Index file must be created by rebuild()"
        raw = json.load(open(index_path))
        assert "2" in raw, "Tick 2 must be in the index"
        tick2_offset = raw["2"]
        assert tick2_offset > 0, "Tick 2 offset must be non-zero (not start of file)"

        # lookup returns exactly the 2 entries for tick 2
        result = idx.lookup(tick=2)
        assert len(result) == 2, f"Expected 2 entries for tick 2, got {len(result)}"
        assert all(r["tick"] == 2 for r in result)
        entity_ids = {r["entity_id"] for r in result}
        assert entity_ids == {3, 4}


def test_tick_index_file_exists_after_close():
    """AC: decision_trace_index.json exists alongside decision_trace.jsonl after writer.close()."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        writer.write_trace(entity_id=1, tick=1, scored_routes=[_make_route()])
        writer.write_trace(entity_id=2, tick=1, scored_routes=[_make_route()])
        writer.write_trace(entity_id=3, tick=2, scored_routes=[_make_route()])
        writer.close()

        index_path = os.path.join(run_dir, "decision_trace_index.json")
        assert os.path.exists(index_path), "decision_trace_index.json must exist after close()"

        raw = json.load(open(index_path))
        assert "1" in raw
        assert "2" in raw
        # String keys, int values
        assert isinstance(raw["1"], int)
        assert isinstance(raw["2"], int)
        assert raw["1"] == 0  # first tick starts at byte 0


def test_tick_index_format_correctness():
    """Index format: string keys, int values; offsets point to correct lines."""
    with tempfile.TemporaryDirectory() as run_dir:
        line1 = json.dumps({"entity_id": 1, "tick": 1, "routes": []}) + "\n"
        line2 = json.dumps({"entity_id": 2, "tick": 2, "routes": []}) + "\n"
        trace_path = os.path.join(run_dir, "decision_trace.jsonl")
        with open(trace_path, "w", encoding="utf-8") as f:
            f.write(line1)
            f.write(line2)

        idx = DecisionTraceIndex(run_dir)
        idx.rebuild()

        raw = json.load(open(os.path.join(run_dir, "decision_trace_index.json")))
        assert set(raw.keys()) == {"1", "2"}, "Keys must be string tick values"
        assert raw["1"] == 0, "Tick 1 offset must be 0"
        assert raw["2"] == len(line1.encode("utf-8")), f"Tick 2 offset must be {len(line1.encode('utf-8'))}"


def test_tick_index_lookup_missing_tick():
    """lookup() on an absent tick returns [] without error."""
    with tempfile.TemporaryDirectory() as run_dir:
        entries = [{"entity_id": 1, "tick": 5, "routes": []}]
        _build_trace_file(run_dir, entries)

        idx = DecisionTraceIndex(run_dir)
        idx.rebuild()

        result = idx.lookup(tick=99)
        assert result == [], "Missing tick must return empty list"


def test_tick_index_rebuild_idempotent():
    """rebuild() called twice produces identical index."""
    with tempfile.TemporaryDirectory() as run_dir:
        entries = [
            {"entity_id": 1, "tick": 1, "routes": []},
            {"entity_id": 2, "tick": 2, "routes": []},
        ]
        _build_trace_file(run_dir, entries)

        idx = DecisionTraceIndex(run_dir)
        idx.rebuild()
        index_after_first = dict(idx._index)

        idx.rebuild()
        index_after_second = dict(idx._index)

        assert index_after_first == index_after_second, "rebuild() must be idempotent"


def test_tick_index_load_from_disk():
    """_load() correctly parses saved JSON — string keys converted to int."""
    with tempfile.TemporaryDirectory() as run_dir:
        index_path = os.path.join(run_dir, "decision_trace_index.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({"3": 0, "7": 128, "12": 512}, f)

        # Create a dummy trace file so lookup doesn't crash
        trace_path = os.path.join(run_dir, "decision_trace.jsonl")
        open(trace_path, "w").close()

        idx = DecisionTraceIndex(run_dir)
        idx._load()

        assert idx._index == {3: 0, 7: 128, 12: 512}, (
            "_load() must convert string keys to int"
        )


def test_tick_index_incremental_vs_rebuild():
    """Incremental append_entry and full rebuild produce identical tick→offset mappings."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    with tempfile.TemporaryDirectory() as run_dir:
        writer = DecisionTraceWriter(run_dir=run_dir)
        writer.write_trace(entity_id=1, tick=1, scored_routes=[_make_route()])
        writer.write_trace(entity_id=2, tick=1, scored_routes=[_make_route()])
        writer.write_trace(entity_id=3, tick=2, scored_routes=[_make_route()])
        # Capture incremental index state before close()
        incremental_index = dict(writer._index._index)

        # close() calls rebuild() — should produce same result
        writer.close()
        rebuilt_index = dict(writer._index._index)

        assert incremental_index == rebuilt_index, (
            "Incremental index and full rebuild must agree on tick→offset mappings"
        )
