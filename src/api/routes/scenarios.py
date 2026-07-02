from __future__ import annotations

import yaml
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.observability.reporting.history_query import sanitize_id
from src.engine.scenario_registry import get, register
from src.engine.scenario_checkpoint import ScenarioCheckpointer
from src.api.presenters.scenarios import ScenarioPresenter

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


class CheckpointRequest(BaseModel):
    name: str


class RestoreRequest(BaseModel):
    spec_path: Optional[str] = None


@router.get("/{scenario_id}/status")
async def get_scenario_status(scenario_id: str):
    scenario_id = sanitize_id(scenario_id)
    svc = get(scenario_id)
    if svc is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    return ScenarioPresenter.present_status(svc)


@router.post("/{scenario_id}/checkpoint")
async def create_checkpoint(scenario_id: str, body: CheckpointRequest):
    scenario_id = sanitize_id(scenario_id)
    svc = get(scenario_id)
    if svc is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")
    path = f"checkpoints/{scenario_id}/{sanitize_id(body.name)}.ckpt"
    try:
        ScenarioCheckpointer.save(svc, Path(path))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ScenarioPresenter.present_checkpoint(path, svc.tick)


@router.post("/{scenario_id}/restore/{checkpoint_name}")
async def restore_checkpoint(scenario_id: str, checkpoint_name: str, body: Optional[RestoreRequest] = None):
    scenario_id = sanitize_id(scenario_id)
    checkpoint_name = sanitize_id(checkpoint_name)
    path = Path(f"checkpoints/{scenario_id}/{checkpoint_name}.ckpt")

    spec_path = body.spec_path if body is not None else None
    if spec_path is not None:
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            from src.scenarios.schema import SimulationScenarioDefinition
            spec = SimulationScenarioDefinition(**raw)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Spec file not found: {spec_path}")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid spec: {e}")
    else:
        from src.scenarios.schema import SimulationScenarioDefinition
        spec = SimulationScenarioDefinition(
            id=scenario_id,
            world_composition="default",
            perspective="default",
        )

    try:
        restored_svc = ScenarioCheckpointer.restore(path, spec)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    register(scenario_id, restored_svc)
    return ScenarioPresenter.present_restore(restored_svc)
