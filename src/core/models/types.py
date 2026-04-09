from typing import Union, Any, TYPE_CHECKING
from .base import SimulationModel
from .vectors import Vector2

class BuildingTarget(SimulationModel):
    """A target that is a building instead of an entity."""
    building_id: str # Building IDs are strings like "store", "blacksmith"

TargetUnion = Union[int, Vector2, BuildingTarget, str, list[Any], tuple[Any, ...], None]
