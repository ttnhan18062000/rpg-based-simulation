"""Core data models: Vector2, Stats, Entity.

Refactored for AOA Stabilization:
- Composition-based actor following the Aspect-Oriented Architecture (AOA).
- Explicit aspect fields: identity, spatial, combat, progression, mind, inventory.
- Removed legacy property shims and StatsProxy.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator, PrivateAttr

# Import aspects directly to avoid forward reference issues during rebuild
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.aspects.combat import CombatAspect
from src.core.aspects.inventory import InventoryAspect
Inventory = InventoryAspect # Legacy shim
from src.core.aspects.progression import ProgressionAspect
from src.core.aspects.mind import MindAspect
from src.core.aspects.interaction import InteractionAspect
from src.core.models.vectors import Vector2
from dataclasses import dataclass

@dataclass
class Stats:
    """DEPRECATED: Legacy stats shim for test compatibility."""
    level: int = 1
    xp: int = 0
    hp: int = 100
    max_hp: int = 100
    atk: int = 10
    def_: int = 5
    spd: int = 5
    stamina: int = 50
    max_stamina: int = 50
    luck: int = 0
    crit_rate: float = 0.05
    crit_dmg: float = 1.5
    evasion: float = 0.02
    vision: int = 6
    matk: int = 0
    mdef: int = 0

class Entity(BaseModel):
    """A simulation entity — character, generator, or any world actor.
    
    Composition-based actor following the Aspect-Oriented Architecture (AOA).
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    id: int
    kind: str
    next_act_at: float = 0.0
    
    # Explicit Aspect Composition
    identity: IdentityAspect = Field(default_factory=lambda: IdentityAspect())
    spatial: SpatialAspect = Field(default_factory=lambda: SpatialAspect())
    combat: CombatAspect = Field(default_factory=lambda: CombatAspect())
    progression: ProgressionAspect = Field(default_factory=lambda: ProgressionAspect())
    mind: MindAspect = Field(default_factory=lambda: MindAspect())
    interaction: InteractionAspect = Field(default_factory=lambda: InteractionAspect())
    inventory: InventoryAspect | None = None
    
    # Internal immutability (Phase-Boundary Enforcement)
    _frozen: bool = PrivateAttr(default=False)

    @model_validator(mode="before")
    @classmethod
    def _validate_before(cls, data: Any) -> Any:
        """Ensure core fields have correct types before Pydantic validation."""
        if isinstance(data, dict):
            if "id" in data and isinstance(data["id"], (float, str)):
                data["id"] = int(data["id"])
            if "next_act_at" in data and isinstance(data["next_act_at"], (int, str)):
                data["next_act_at"] = float(data["next_act_at"])
        return data

    def model_post_init(self, __context: Any) -> None:
        """Ensure all aspects are correctly attached to their parent entity."""
        aspect_fields = ["identity", "spatial", "combat", "progression", "mind", "interaction", "inventory"]
        for field_name in aspect_fields:
            if hasattr(self, field_name):
                aspect = getattr(self, field_name)
                if aspect and hasattr(aspect, "on_attach"):
                    aspect.on_attach(self)

    # --- Lifecycle ---
    
    def on_tick(self, tick: int) -> None:
        """Propagate tick to all active aspects."""
        self.identity.on_tick(tick)
        self.spatial.on_tick(tick)
        self.combat.on_tick(tick)
        self.progression.on_tick(tick)
        self.mind.on_tick(tick)
        self.interaction.on_tick(tick)
        if self.inventory:
            self.inventory.on_tick(tick)

    def has_trait(self, trait: Any) -> bool:
        """Check if entity has a specific TraitType via its identity aspect."""
        return trait in self.identity.traits

    @property
    def threat_table(self) -> dict[int, float]:
        """Compatibility shim for legacy threat system tests."""
        return self.mind.perception.threat_table

    @property
    def pos(self) -> Vector2:
        """Compatibility shim for legacy spatial tests."""
        return self.spatial.pos

    @property
    def stats(self) -> CombatAspect:
        """Compatibility shim for legacy combat stats tests."""
        return self.combat

    @property
    def alive(self) -> bool:
        """Compatibility shim for legacy life-state tests."""
        return self.combat.alive

    @property
    def combat_target_id(self) -> int | None:
        """Compatibility shim for legacy targeting tests."""
        return self.combat.combat_target_id

    # --- Copying ---

    def copy(self) -> Entity:
        """Absolute deep copy for snapshot generation.
        
        Uses Pydantic's recursive deep_copy to ensure all aspect data 
        (including nested lists/dicts) is fully isolated.
        """
        new_ent = self.model_copy(deep=True)
        new_ent.model_post_init(None)
        return new_ent

    def freeze(self) -> None:
        """Lock the entity for read-only access (e.g. in Snapshot)."""
        self._frozen = True
        # Recursive freeze on aspects
        aspect_fields = ["identity", "spatial", "combat", "progression", "mind", "interaction"]
        if self.inventory:
            aspect_fields.append("inventory")
        for f in aspect_fields:
            asp = getattr(self, f)
            if hasattr(asp, "freeze"):
                asp.freeze()

    def __setattr__(self, name: str, value: Any) -> None:
        if getattr(self, "_frozen", False) and not name.startswith("_"):
            raise RuntimeError(f"Cannot mutate frozen Entity {self.id} (Field: {name})")
        super().__setattr__(name, value)

# Rebuild models to finalize Pydantic setup
Entity.model_rebuild()
IdentityAspect.model_rebuild()
SpatialAspect.model_rebuild()
CombatAspect.model_rebuild()
InventoryAspect.model_rebuild()
ProgressionAspect.model_rebuild()
MindAspect.model_rebuild()
InteractionAspect.model_rebuild()
