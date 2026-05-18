"""Regional consequence models — broad world trends. [PHASE 4]

RegionConsequenceRecords track aggregated metrics like danger and stability
for large areas of the world map.
"""

from __future__ import annotations
from pydantic import Field, ConfigDict
from src_legacy.core.models.base import SimulationModel


class RegionConsequenceRecord(SimulationModel):
    """Aggregated regional metrics driving broad behavioral shifts. [PHASE 4]"""
    model_config = ConfigDict(extra='forbid')

    region_id: str
    
    # Regional Metrics
    danger_level: float = Field(default=0.0, ge=-1.0, le=1.0)
    stability: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Pressure & Control
    # Faction ID -> Influence scalar
    control_pressure: dict[int, float] = Field(default_factory=dict)
    
    last_major_change_tick: int = 0


# Pydantic model rebuild
RegionConsequenceRecord.model_rebuild()
