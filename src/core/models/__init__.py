from .enums import AIState, DamageType, Element, EnemyTier, EntityRole, TraitType, HeroClass, Domain, Material, ActionType, Direction
from .vectors import Vector2, FloatVector2, DIRECTION_OFFSETS
from src.core.aspects.inventory import InventoryAspect as Inventory # Legacy transition shim
# Removed Snapshot and Entity to prevent circular imports with Aspects
