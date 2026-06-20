"""
tests/api/test_decision_api.py
───────────────────────────────────────────────────────────────────────────────
Tests for Epic 2.2C: Decision Explanation REST Endpoints.

Pattern: @pytest.mark.anyio, direct handler invocation (no TestClient),
patches at src.api.routes.decisions.<symbol>.

Coverage:
  Group 1 — Single tick (get_entity_decisions):
    - Returns shaped {"entity_id", "tick", "routes"} with all 8 score fields
    - 404 when run directory missing
    - 404 when trace file missing
    - 400 on invalid (path-traversal) run_id
    - 200 + empty routes list when tick absent from index

  Group 2 — Range query (get_entity_decisions_range):
    - Returns list of tick objects for ticks with data; omits empty ticks
    - 400 when from > to
    - 400 when range > 100 ticks
    - 404 when run directory missing
    - 400 on invalid run_id

  Group 3 — Summary (get_entity_decisions_summary):
    - Returns {"entity_id", "tick_count", "route_kind_distribution"}
    - Values derived from shaped presenter (not raw dicts)
    - 404 when run directory missing
    - Empty index → tick_count=0, route_kind_distribution={}
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch, AsyncMock

from src.api.routes.decisions import (
    get_entity_decisions,
    get_entity_decisions_range,
    get_entity_decisions_summary,
)


# ---------------------------------------------------------------------------
# Fixtures / shared mock data
# ---------------------------------------------------------------------------

def _make_entry(entity_id: int, tick: int, route_kind: str = "GATHER_RESOURCE", selected: bool = True) -> dict:
    """Build a realistic decision trace entry dict."""
    return {
        "entity_id": entity_id,
        "tick": tick,
        "routes": [
            {
                "route_kind": route_kind,
                "score": 1.85,
                "urgency": 0.6,
                "benefit": 0.4,
                "personality_bias": 0.25,
                "confidence_bonus": 0.15,
                "risk_penalty": 0.3,
                "blocker_penalty": 0.0,
                "selected": selected,
            },
            {
                "route_kind": "RETREAT",
                "score": 0.70,
                "urgency": 0.2,
                "benefit": 0.3,
                "personality_bias": 0.05,
                "confidence_bonus": 0.0,
                "risk_penalty": 0.1,
                "blocker_penalty": 0.0,
                "selected": False,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Group 1 — Single tick
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_decision_api_returns_score_breakdown():
    """Shaped response includes all 8 score fields and correct entity/tick."""
    entry = _make_entry(entity_id=7, tick=5)

    mock_index = MagicMock()
    mock_index.lookup.return_value = [entry]

    with (
        patch("src.api.routes.decisions.os.path.isdir", return_value=True),
        patch("src.api.routes.decisions.os.path.exists", return_value=True),
        patch("src.api.routes.decisions.DecisionTraceIndex", return_value=mock_index),
    ):
        result = await get_entity_decisions(entity_id=7, run_id="run_abc", tick=5)

    assert result["entity_id"] == 7
    assert result["tick"] == 5
    assert isinstance(result["routes"], list)
    assert len(result["routes"]) == 2

    first_route = result["routes"][0]
    for field in ("route_kind", "score", "urgency", "benefit", "personality_bias",
                  "confidence_bonus", "risk_penalty", "blocker_penalty", "selected"):
        assert field in first_route, f"Missing field: {field}"

    # No internal fields from DecisionTraceIndex should leak
    assert "_index" not in result
    assert "_trace_path" not in result
    assert "_index_path" not in result


@pytest.mark.anyio
async def test_decision_api_404_missing_run_dir():
    """Returns 404 when run directory does not exist."""
    with patch("src.api.routes.decisions.os.path.isdir", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await get_entity_decisions(entity_id=7, run_id="ghost_run", tick=0)
    assert exc_info.value.status_code == 404


@pytest.mark.anyio
async def test_decision_api_404_missing_trace_file():
    """Returns 404 when trace file is absent (but run dir exists)."""
    with (
        patch("src.api.routes.decisions.os.path.isdir", return_value=True),
        patch("src.api.routes.decisions.os.path.exists", return_value=False),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_entity_decisions(entity_id=7, run_id="run_no_trace", tick=0)
    assert exc_info.value.status_code == 404
    assert "decision trace" in exc_info.value.detail


@pytest.mark.anyio
async def test_decision_api_400_invalid_run_id():
    """Returns 400 when run_id contains path traversal characters."""
    with pytest.raises(HTTPException) as exc_info:
        await get_entity_decisions(entity_id=7, run_id="../evil", tick=0)
    assert exc_info.value.status_code == 400


@pytest.mark.anyio
async def test_decision_api_200_empty_tick():
    """Returns 200 with empty routes list when tick is absent from index."""
    mock_index = MagicMock()
    mock_index.lookup.return_value = []

    with (
        patch("src.api.routes.decisions.os.path.isdir", return_value=True),
        patch("src.api.routes.decisions.os.path.exists", return_value=True),
        patch("src.api.routes.decisions.DecisionTraceIndex", return_value=mock_index),
    ):
        result = await get_entity_decisions(entity_id=7, run_id="run_abc", tick=999)

    assert result["entity_id"] == 7
    assert result["tick"] == 999
    assert result["routes"] == []


@pytest.mark.anyio
async def test_decision_api_filters_by_entity_id():
    """Only routes belonging to the requested entity_id are returned."""
    entries = [
        _make_entry(entity_id=7, tick=5, route_kind="GATHER_RESOURCE"),
        _make_entry(entity_id=99, tick=5, route_kind="ENGAGE_COMBAT"),
    ]

    mock_index = MagicMock()
    mock_index.lookup.return_value = entries

    with (
        patch("src.api.routes.decisions.os.path.isdir", return_value=True),
        patch("src.api.routes.decisions.os.path.exists", return_value=True),
        patch("src.api.routes.decisions.DecisionTraceIndex", return_value=mock_index),
    ):
        result = await get_entity_decisions(entity_id=7, run_id="run_abc", tick=5)

    # Should only include entity 7's routes
    assert len(result["routes"]) == 2  # 2 routes from entity 7's entry
    for route in result["routes"]:
        assert route["route_kind"] != "ENGAGE_COMBAT"


# ---------------------------------------------------------------------------
# Group 2 — Range query
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_decision_api_range_query():
    """Range query returns list of tick objects; empty ticks are omitted."""
    def _lookup(tick: int):
        if tick in (3, 4, 5):
            return [_make_entry(entity_id=7, tick=tick)]
        return []

    mock_index = MagicMock()
    mock_index.lookup.side_effect = _lookup

    with (
        patch("src.api.routes.decisions.os.path.isdir", return_value=True),
        patch("src.api.routes.decisions.os.path.exists", return_value=True),
        patch("src.api.routes.decisions.DecisionTraceIndex", return_value=mock_index),
    ):
        result = await get_entity_decisions_range(
            entity_id=7, run_id="run_abc", from_tick=3, to_tick=7
        )

    # Ticks 6 and 7 have no data and should be omitted
    assert isinstance(result, list)
    assert len(result) == 3
    ticks_returned = [item["tick"] for item in result]
    assert ticks_returned == [3, 4, 5]
    for item in result:
        assert item["entity_id"] == 7
        assert "routes" in item


@pytest.mark.anyio
async def test_decision_api_range_400_from_gt_to():
    """Returns 400 when from > to."""
    with (
        patch("src.api.routes.decisions.os.path.isdir", return_value=True),
        patch("src.api.routes.decisions.os.path.exists", return_value=True),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_entity_decisions_range(
                entity_id=7, run_id="run_abc", from_tick=7, to_tick=3
            )
    assert exc_info.value.status_code == 400
    assert "'to' must be >=" in exc_info.value.detail


@pytest.mark.anyio
async def test_decision_api_range_400_exceeds_100_ticks():
    """Returns 400 when range exceeds 100 ticks."""
    with (
        patch("src.api.routes.decisions.os.path.isdir", return_value=True),
        patch("src.api.routes.decisions.os.path.exists", return_value=True),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_entity_decisions_range(
                entity_id=7, run_id="run_abc", from_tick=0, to_tick=101
            )
    assert exc_info.value.status_code == 400
    assert "100" in exc_info.value.detail


@pytest.mark.anyio
async def test_decision_api_range_404_missing_run():
    """Returns 404 when run directory is missing (range endpoint)."""
    with patch("src.api.routes.decisions.os.path.isdir", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await get_entity_decisions_range(
                entity_id=7, run_id="ghost_run", from_tick=0, to_tick=5
            )
    assert exc_info.value.status_code == 404


@pytest.mark.anyio
async def test_decision_api_range_400_invalid_run_id():
    """Returns 400 when run_id is invalid (range endpoint)."""
    with pytest.raises(HTTPException) as exc_info:
        await get_entity_decisions_range(
            entity_id=7, run_id="../../passwd", from_tick=0, to_tick=5
        )
    assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# Group 3 — Summary
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_decision_api_summary():
    """Summary returns entity_id, tick_count, route_kind_distribution."""
    entries_by_tick = {
        1: [_make_entry(entity_id=7, tick=1, route_kind="GATHER_RESOURCE")],
        2: [_make_entry(entity_id=7, tick=2, route_kind="GATHER_RESOURCE")],
        3: [_make_entry(entity_id=7, tick=3, route_kind="RETREAT")],
    }

    def _lookup(tick: int):
        return entries_by_tick.get(tick, [])

    mock_index = MagicMock()
    mock_index._index = {1: 0, 2: 100, 3: 200}
    mock_index._load = MagicMock()  # no-op
    mock_index.lookup.side_effect = _lookup

    with (
        patch("src.api.routes.decisions.os.path.isdir", return_value=True),
        patch("src.api.routes.decisions.os.path.exists", return_value=True),
        patch("src.api.routes.decisions.DecisionTraceIndex", return_value=mock_index),
    ):
        result = await get_entity_decisions_summary(entity_id=7, run_id="run_abc")

    assert result["entity_id"] == 7
    assert isinstance(result["tick_count"], int)
    assert result["tick_count"] == 3
    dist = result["route_kind_distribution"]
    assert isinstance(dist, dict)
    # 2 GATHER_RESOURCE + 1 RETREAT → fractions should sum to 1.0
    total = sum(dist.values())
    assert abs(total - 1.0) < 1e-3
    assert "GATHER_RESOURCE" in dist
    assert "RETREAT" in dist
    assert dist["GATHER_RESOURCE"] > dist["RETREAT"]

    # No raw internal fields in response
    assert "_index" not in result
    assert "_trace_path" not in result


@pytest.mark.anyio
async def test_decision_api_summary_404_missing_run():
    """Returns 404 when run directory is missing (summary endpoint)."""
    with patch("src.api.routes.decisions.os.path.isdir", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await get_entity_decisions_summary(entity_id=7, run_id="ghost_run")
    assert exc_info.value.status_code == 404


@pytest.mark.anyio
async def test_decision_api_summary_empty_index():
    """Empty index → tick_count=0, route_kind_distribution={}."""
    mock_index = MagicMock()
    mock_index._index = {}
    mock_index._load = MagicMock()

    with (
        patch("src.api.routes.decisions.os.path.isdir", return_value=True),
        patch("src.api.routes.decisions.os.path.exists", return_value=True),
        patch("src.api.routes.decisions.DecisionTraceIndex", return_value=mock_index),
    ):
        result = await get_entity_decisions_summary(entity_id=7, run_id="run_empty")

    assert result["entity_id"] == 7
    assert result["tick_count"] == 0
    assert result["route_kind_distribution"] == {}


@pytest.mark.anyio
async def test_decision_api_summary_400_invalid_run_id():
    """Returns 400 when run_id is invalid (summary endpoint)."""
    with pytest.raises(HTTPException) as exc_info:
        await get_entity_decisions_summary(entity_id=7, run_id="../hack")
    assert exc_info.value.status_code == 400
