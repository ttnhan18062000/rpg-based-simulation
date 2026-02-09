"""GET /api/v1/map — static grid data (fetch once)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import MapResponse

router = APIRouter()


@router.get("/map", response_model=MapResponse)
def get_map(manager: EngineManager = Depends(get_engine_manager)) -> MapResponse:
    grid = manager.get_grid()
    if grid is None:
        raise HTTPException(status_code=503, detail="Simulation not initialized yet.")

    grid_2d: list[list[int]] = []
    for y in range(grid.height):
        row = [int(grid._tiles[y * grid.width + x]) for x in range(grid.width)]
        grid_2d.append(row)

    return MapResponse(width=grid.width, height=grid.height, grid=grid_2d)
