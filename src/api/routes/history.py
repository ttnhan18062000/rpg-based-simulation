from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.observability.reporting.history_query import (
    HistoricalRunQueryService,
    HistoricalSweepQueryService
)

router = APIRouter(prefix="/observability/history", tags=["History"])

run_service = HistoricalRunQueryService()
sweep_service = HistoricalSweepQueryService()


class ErrorResponse(BaseModel):
    detail: str


@router.get(
    "/runs",
    response_model=List[dict],
    summary="List historical simulation runs",
    description="Retrieve a paginated, sorted list of metadata for completed simulation runs."
)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=100, description="Max number of runs to return"),
    offset: int = Query(default=0, ge=0, description="Number of runs to skip")
):
    try:
        runs = run_service.list_historical_runs(limit=limit, offset=offset)
        return [r.model_dump() for r in runs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list historical runs: {e}")


@router.get(
    "/runs/{run_id}",
    response_model=dict,
    summary="Get single historical run manifest",
    description="Securely query the metadata manifest for a specific run ID.",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def get_run(run_id: str):
    try:
        manifest = run_service.get_run_manifest(run_id)
        return manifest.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/sweeps",
    response_model=List[dict],
    summary="List historical scenario sweeps",
    description="Retrieve a paginated, sorted list of metadata for multi-run sweeps."
)
async def list_sweeps(
    limit: int = Query(default=50, ge=1, le=100, description="Max number of sweeps to return"),
    offset: int = Query(default=0, ge=0, description="Number of sweeps to skip")
):
    try:
        sweeps = sweep_service.list_historical_sweeps(limit=limit, offset=offset)
        return [s.model_dump() for s in sweeps]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list historical sweeps: {e}")


@router.get(
    "/sweeps/{sweep_id}",
    response_model=dict,
    summary="Get scenario sweep summary",
    description="Securely query the aggregated statistics for a specific scenario sweep.",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def get_sweep(sweep_id: str):
    try:
        summary = sweep_service.get_sweep_summary(sweep_id)
        return summary.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Sweep '{sweep_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
