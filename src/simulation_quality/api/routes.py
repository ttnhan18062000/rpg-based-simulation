"""REST API routes for the Simulation Quality Scoring module.

GET /api/v1/quality/status        — enabled, run_id, tick_count, overall_grade
GET /api/v1/quality/pillars       — all 10 pillar summaries
GET /api/v1/quality/pillars/{id}  — full pillar state + top-10 worst events
GET /api/v1/quality/alerts        — pillars graded D or F + active loop_flags
GET /api/v1/quality/report        — full QualityReport snapshot

All endpoints return {"enabled": false} when QUALITY_SCORING_DISABLED=1.
All response_model= parameters set per D13 F2 requirement.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_quality_hub
from src.simulation_quality.pillars import PillarId

router = APIRouter(prefix="/quality", tags=["Simulation Quality"])

_DISABLED_RESPONSE: Dict[str, Any] = {"enabled": False}


def _is_disabled() -> bool:
    return os.environ.get("QUALITY_SCORING_DISABLED") == "1"


@router.get(
    "/status",
    response_model=Dict[str, Any],
    summary="Quality scoring enabled state and run overview",
)
async def get_quality_status() -> Dict[str, Any]:
    if _is_disabled():
        return _DISABLED_RESPONSE
    hub = get_quality_hub()
    if hub is None:
        return {"enabled": False, "reason": "Quality hub not initialized"}
    report = hub.get_quality_report()
    return {
        "enabled": True,
        "run_id": report.run_id,
        "tick_count": report.tick_count,
        "overall_score": report.overall_score,
        "overall_grade": report.overall_grade,
    }


@router.get(
    "/pillars",
    response_model=Dict[str, Any],
    summary="All pillar normalized scores and grades",
)
async def get_quality_pillars() -> Dict[str, Any]:
    if _is_disabled():
        return _DISABLED_RESPONSE
    hub = get_quality_hub()
    if hub is None:
        return {"enabled": False, "reason": "Quality hub not initialized"}
    report = hub.get_quality_report()
    pillars_out: List[Dict[str, Any]] = []
    for pillar_id, snap in report.pillars.items():
        pillars_out.append({
            "pillar_id": pillar_id,
            "normalized_score": snap.normalized_score,
            "grade": snap.grade,
            "event_count": snap.event_count,
            "loop_detected": snap.loop_detected,
        })
    return {"enabled": True, "tick_count": report.tick_count, "pillars": pillars_out}


@router.get(
    "/pillars/{pillar_id}",
    response_model=Dict[str, Any],
    summary="Full pillar state including top-10 worst events",
)
async def get_quality_pillar_detail(pillar_id: str) -> Dict[str, Any]:
    if _is_disabled():
        return _DISABLED_RESPONSE
    # Validate pillar_id
    valid_ids = {p.value for p in PillarId}
    if pillar_id not in valid_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown pillar_id '{pillar_id}'. Valid values: {sorted(valid_ids)}",
        )
    hub = get_quality_hub()
    if hub is None:
        return {"enabled": False, "reason": "Quality hub not initialized"}
    report = hub.get_quality_report()
    snap = report.pillars.get(pillar_id)
    if snap is None:
        raise HTTPException(status_code=404, detail=f"Pillar '{pillar_id}' not in report")
    worst_out = []
    for rec in snap.worst_events:
        worst_out.append({
            "tick": rec.tick,
            "event_id": rec.event_id,
            "pillar": rec.pillar.value,
            "delta": rec.delta,
            "reason": rec.reason,
            "event_type": rec.event_type,
            "entity_id": rec.entity_id,
            "region_id": rec.region_id,
            "tags": list(rec.tags),
        })
    return {
        "enabled": True,
        "pillar_id": pillar_id,
        "raw_score": snap.raw_score,
        "normalized_score": snap.normalized_score,
        "grade": snap.grade,
        "event_count": snap.event_count,
        "negative_count": snap.negative_count,
        "loop_detected": snap.loop_detected,
        "loop_flags": sorted(snap.loop_flags),
        "worst_events": worst_out,
    }


@router.get(
    "/alerts",
    response_model=Dict[str, Any],
    summary="Pillars graded D or F and active loop flags",
)
async def get_quality_alerts() -> Dict[str, Any]:
    if _is_disabled():
        return _DISABLED_RESPONSE
    hub = get_quality_hub()
    if hub is None:
        return {"enabled": False, "reason": "Quality hub not initialized"}
    report = hub.get_quality_report()
    alerts: List[Dict[str, Any]] = []
    for pillar_id, snap in report.pillars.items():
        if snap.grade in ("D", "F") or snap.loop_detected:
            alerts.append({
                "pillar_id": pillar_id,
                "grade": snap.grade,
                "normalized_score": snap.normalized_score,
                "loop_detected": snap.loop_detected,
                "loop_flags": sorted(snap.loop_flags),
            })
    return {
        "enabled": True,
        "tick_count": report.tick_count,
        "alert_count": len(alerts),
        "alerts": alerts,
    }


@router.get(
    "/report",
    response_model=Dict[str, Any],
    summary="Full QualityReport snapshot",
)
async def get_quality_report() -> Dict[str, Any]:
    if _is_disabled():
        return _DISABLED_RESPONSE
    hub = get_quality_hub()
    if hub is None:
        return {"enabled": False, "reason": "Quality hub not initialized"}
    report = hub.get_quality_report()
    result = report.to_dict()
    result["enabled"] = True
    return result
