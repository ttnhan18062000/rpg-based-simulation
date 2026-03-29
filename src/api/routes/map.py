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

    # RLE encode: [value, count, value, count, ...]
    tiles = grid._tiles
    total = grid.width * grid.height
    rle: list[int] = []
    if total > 0:
        cur_val = int(tiles[0])
        cur_count = 1
        for i in range(1, total):
            v = int(tiles[i])
            if v == cur_val:
                cur_count += 1
            else:
                rle.append(cur_val)
                rle.append(cur_count)
                cur_val = v
                cur_count = 1
        rle.append(cur_val)
        rle.append(cur_count)

    return MapResponse(width=grid.width, height=grid.height, grid=rle)
