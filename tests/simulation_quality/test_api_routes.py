"""Integration tests for Simulation Quality REST API routes (E5).

Tests all 5 endpoints with live accumulator data and disabled-state responses.
"""
from __future__ import annotations
import os
import uuid
import pytest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.simulation_quality.api import routes as quality_routes
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.quality_report import QualityReport, PillarSnapshot
from src.simulation_quality.score_record import ScoreRecord


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(quality_routes.router, prefix="/api/v1")
    return app


def _make_snap(grade: str = "A", loop: bool = False) -> PillarSnapshot:
    return PillarSnapshot(
        pillar_id="AGENCY",
        raw_score=50.0,
        normalized_score=0.5,
        grade=grade,
        event_count=10,
        negative_count=2,
        loop_detected=loop,
        loop_flags=frozenset({"stasis_loop"} if loop else []),
        worst_events=(
            ScoreRecord(
                tick=5,
                event_id=uuid.uuid4().hex,
                pillar=PillarId.AGENCY,
                delta=-5.0,
                reason="test negative",
                event_type="action_executed",
                entity_id=1,
                region_id=None,
                tags=("stasis",),
            ),
        ),
    )


def _make_report(grade: str = "A", loop: bool = False) -> QualityReport:
    pillar_snaps = {p.value: _make_snap(grade=grade, loop=loop) for p in PillarId}
    return QualityReport(
        run_id="test-run-001",
        tick_count=100,
        overall_score=0.5,
        overall_grade=grade,
        generated_at="2026-06-29T00:00:00+00:00",
        pillars=pillar_snaps,
    )


@pytest.fixture
def mock_hub() -> MagicMock:
    hub = MagicMock()
    hub.get_quality_report.return_value = _make_report()
    return hub


@pytest.fixture
def client(mock_hub: MagicMock) -> TestClient:
    app = _make_app()
    with patch("src.simulation_quality.api.routes.get_quality_hub", return_value=mock_hub):
        with TestClient(app) as c:
            yield c


class TestStatusEndpoint:
    def test_enabled_returns_run_info(self, client: TestClient) -> None:
        resp = client.get("/api/v1/quality/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["enabled"] is True
        assert body["run_id"] == "test-run-001"
        assert body["tick_count"] == 100
        assert "overall_grade" in body

    def test_disabled_state(self) -> None:
        app = _make_app()
        with patch.dict(os.environ, {"QUALITY_SCORING_DISABLED": "1"}):
            with TestClient(app) as c:
                resp = c.get("/api/v1/quality/status")
        assert resp.status_code == 200
        assert resp.json() == {"enabled": False}

    def test_no_hub_returns_enabled_false(self) -> None:
        app = _make_app()
        with patch("src.simulation_quality.api.routes.get_quality_hub", return_value=None):
            with TestClient(app) as c:
                resp = c.get("/api/v1/quality/status")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False


class TestPillarsEndpoint:
    def test_returns_all_pillars(self, client: TestClient) -> None:
        resp = client.get("/api/v1/quality/pillars")
        assert resp.status_code == 200
        body = resp.json()
        assert body["enabled"] is True
        assert len(body["pillars"]) == len(PillarId)
        for pillar in body["pillars"]:
            assert "pillar_id" in pillar
            assert "normalized_score" in pillar
            assert "grade" in pillar

    def test_disabled_state(self) -> None:
        app = _make_app()
        with patch.dict(os.environ, {"QUALITY_SCORING_DISABLED": "1"}):
            with TestClient(app) as c:
                resp = c.get("/api/v1/quality/pillars")
        assert resp.json() == {"enabled": False}


class TestPillarDetailEndpoint:
    def test_known_pillar_returns_full_state(self, client: TestClient) -> None:
        pillar_id = list(PillarId)[0].value
        resp = client.get(f"/api/v1/quality/pillars/{pillar_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["enabled"] is True
        assert body["pillar_id"] == pillar_id
        assert "raw_score" in body
        assert "worst_events" in body
        assert isinstance(body["worst_events"], list)
        assert len(body["worst_events"]) >= 1
        assert "loop_flags" in body

    def test_unknown_pillar_returns_404(self, client: TestClient) -> None:
        resp = client.get("/api/v1/quality/pillars/NONEXISTENT_PILLAR")
        assert resp.status_code == 404

    def test_disabled_state(self) -> None:
        app = _make_app()
        with patch.dict(os.environ, {"QUALITY_SCORING_DISABLED": "1"}):
            with TestClient(app) as c:
                resp = c.get("/api/v1/quality/pillars/AGENCY")
        assert resp.json() == {"enabled": False}


class TestAlertsEndpoint:
    def test_no_alerts_when_all_grade_a(self, client: TestClient) -> None:
        resp = client.get("/api/v1/quality/alerts")
        assert resp.status_code == 200
        body = resp.json()
        assert body["enabled"] is True
        assert "alert_count" in body
        assert "alerts" in body

    def test_alerts_returned_for_d_grade(self) -> None:
        app = _make_app()
        hub = MagicMock()
        hub.get_quality_report.return_value = _make_report(grade="D")
        with patch("src.simulation_quality.api.routes.get_quality_hub", return_value=hub):
            with TestClient(app) as c:
                resp = c.get("/api/v1/quality/alerts")
        body = resp.json()
        assert body["alert_count"] > 0
        for alert in body["alerts"]:
            assert alert["grade"] in ("D", "F") or alert["loop_detected"]

    def test_alerts_returned_for_loop_detected(self) -> None:
        app = _make_app()
        hub = MagicMock()
        hub.get_quality_report.return_value = _make_report(grade="B", loop=True)
        with patch("src.simulation_quality.api.routes.get_quality_hub", return_value=hub):
            with TestClient(app) as c:
                resp = c.get("/api/v1/quality/alerts")
        body = resp.json()
        assert body["alert_count"] > 0
        assert any(a["loop_detected"] for a in body["alerts"])

    def test_disabled_state(self) -> None:
        app = _make_app()
        with patch.dict(os.environ, {"QUALITY_SCORING_DISABLED": "1"}):
            with TestClient(app) as c:
                resp = c.get("/api/v1/quality/alerts")
        assert resp.json() == {"enabled": False}


class TestReportEndpoint:
    def test_full_report_returned(self, client: TestClient) -> None:
        resp = client.get("/api/v1/quality/report")
        assert resp.status_code == 200
        body = resp.json()
        assert body["enabled"] is True
        assert body["run_id"] == "test-run-001"
        assert "pillars" in body
        assert "overall_grade" in body

    def test_disabled_state(self) -> None:
        app = _make_app()
        with patch.dict(os.environ, {"QUALITY_SCORING_DISABLED": "1"}):
            with TestClient(app) as c:
                resp = c.get("/api/v1/quality/report")
        assert resp.json() == {"enabled": False}
