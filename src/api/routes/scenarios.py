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

# Allowed base directory for ad-hoc restore spec files, mirroring the
# repo-relative "checkpoints/" convention used for checkpoint paths below.
ALLOWED_SPEC_BASE_DIR = Path("scenario_specs")


class CheckpointRequest(BaseModel):
    name: str


class RestoreRequest(BaseModel):
    spec_path: Optional[str] = None


def _resolve_spec_path(spec_path: str) -> Path:
    """Resolve spec_path and enforce containment inside ALLOWED_SPEC_BASE_DIR.

    Raises HTTPException(400) before any filesystem existence check, so an
    out-of-bounds path can't be used as a file-existence oracle.
    """
    base_resolved = ALLOWED_SPEC_BASE_DIR.resolve()
    candidate = Path(spec_path)
    resolved = (base_resolved / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    if not resolved.is_relative_to(base_resolved):
        raise HTTPException(
            status_code=400,
            detail="spec_path must resolve inside the allowed scenario spec directory",
        )
    return resolved


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
        resolved_spec_path = _resolve_spec_path(spec_path)
        try:
            with open(resolved_spec_path, "r", encoding="utf-8") as f:
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
