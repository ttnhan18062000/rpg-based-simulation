from src.core.entities.entity import Entity
from src.core.entities.stats import Stats
from src.core.entities.stats_proxy import StatsProxy
from .enums import AIState, DamageType, Element, EnemyTier, EntityRole, TraitType, HeroClass, Domain, Material, ActionType, Direction
from .vectors import Vector2, FloatVector2, DIRECTION_OFFSETS
from .snapshot import Snapshot
from .world_state import WorldState
from .base import Aspect
from .world_objects import HomeStorage, TreasureChest, CorpseNode

# Re-export InventoryAspect as Inventory for compatibility
from .inventory import Inventory
