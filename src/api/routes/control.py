"""POST /api/v1/control/{action} — simulation lifecycle controls."""

from __future__ import annotations

from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import ControlResponse

router = APIRouter()


class ControlAction(str, Enum):
    start = "start"
    pause = "pause"
    resume = "resume"
    step = "step"
    reset = "reset"


@router.post("/control/{action}", response_model=ControlResponse)
def control(
    action: ControlAction,
    manager: EngineManager = Depends(get_engine_manager),
) -> ControlResponse:
    snapshot = manager.get_snapshot()
    tick = snapshot.tick if snapshot else 0

    match action:
        case ControlAction.start:
            if manager.running:
                return ControlResponse(status="noop", message="Already running.", tick=tick)
            manager.start()
            return ControlResponse(status="ok", message="Simulation started.", tick=tick)

        case ControlAction.pause:
            if not manager.running:
                return ControlResponse(status="error", message="Not running.", tick=tick)
            manager.pause()
            return ControlResponse(status="ok", message="Simulation paused.", tick=tick)

        case ControlAction.resume:
            if not manager.running:
                return ControlResponse(status="error", message="Not running.", tick=tick)
            manager.resume()
            return ControlResponse(status="ok", message="Simulation resumed.", tick=tick)

        case ControlAction.step:
            if not manager.running:
                manager.start()
                manager.pause()
            manager.step()
            return ControlResponse(status="ok", message="Single tick executed.", tick=tick)

        case ControlAction.reset:
            manager.reset()
            snapshot = manager.get_snapshot()
            new_tick = snapshot.tick if snapshot else 0
            return ControlResponse(status="ok", message="Simulation reset.", tick=new_tick)


@router.post("/speed")
def set_speed(
    tps: float = Query(20.0, gt=0.5, le=100.0, description="Ticks per second"),
    manager: EngineManager = Depends(get_engine_manager),
) -> ControlResponse:
    manager.tick_rate = 1.0 / tps
    snapshot = manager.get_snapshot()
    tick = snapshot.tick if snapshot else 0
    return ControlResponse(status="ok", message=f"Speed set to {tps:.1f} tps.", tick=tick)
