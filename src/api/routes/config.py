"""GET /api/v1/config — expose simulation configuration."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.dependencies import get_engine_manager
from src.api.engine_manager import EngineManager
from src.api.schemas import SimulationConfigResponse

router = APIRouter()


@router.get("/config", response_model=SimulationConfigResponse)
def get_config(
    manager: EngineManager = Depends(get_engine_manager),
) -> SimulationConfigResponse:
    cfg = manager._config
    return SimulationConfigResponse(
        world_seed=cfg.world_seed,
        grid_width=cfg.grid_width,
        grid_height=cfg.grid_height,
        max_ticks=cfg.max_ticks,
        num_workers=cfg.num_workers,
        initial_entity_count=cfg.initial_entity_count,
        generator_spawn_interval=cfg.generator_spawn_interval,
        generator_max_entities=cfg.generator_max_entities,
        vision_range=cfg.vision_range,
        flee_hp_threshold=cfg.flee_hp_threshold,
        tick_rate=manager.tick_rate,
    )
