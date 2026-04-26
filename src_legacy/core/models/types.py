from typing import Union, Any, TYPE_CHECKING
from .base import SimulationModel
from .vectors import Vector2

class BuildingTarget(SimulationModel):
    """A target that is a building instead of an entity."""
    building_id: str # Building IDs are strings like "store", "blacksmith"

class LocationTarget(SimulationModel):
    """A target that is a specific spatial position (AoE or move destination)."""
    pos: Vector2

TargetUnion = Union[int, Vector2, BuildingTarget, LocationTarget, str, list[Any], tuple[Any, ...], None]
