"""Resource nodes — harvestable objects scattered across terrain regions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.core.enums import Material
from src.core.models import Vector2

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class ResourceNode:
    """A harvestable resource on the map."""

    node_id: int
    resource_type: str          # e.g. "herb_patch", "ore_vein", "timber"
    name: str                   # display name
    pos: Vector2
    terrain: Material           # which terrain this spawns on
    yields_item: str            # item_id produced on harvest
    remaining: int = 3          # harvests left before depletion
    max_harvests: int = 3
    respawn_cooldown: int = 30  # ticks to respawn after depletion
    cooldown_remaining: int = 0 # 0 = harvestable; >0 = depleted, counting down
    harvest_ticks: int = 2      # ticks to channel harvest

    @property
    def is_depleted(self) -> bool:
        return self.remaining <= 0

    @property
    def is_available(self) -> bool:
        return self.remaining > 0 and self.cooldown_remaining <= 0

    def harvest(self) -> str | None:
        """Consume one harvest charge, return the item_id or None."""
        if not self.is_available:
            return None
        self.remaining -= 1
        if self.remaining <= 0:
            self.cooldown_remaining = self.respawn_cooldown
        return self.yields_item

    def tick_cooldown(self) -> None:
        """Decrement cooldown; respawn if ready."""
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
            if self.cooldown_remaining <= 0:
                self.remaining = self.max_harvests

    def copy(self) -> ResourceNode:
        return ResourceNode(
            node_id=self.node_id,
            resource_type=self.resource_type,
            name=self.name,
            pos=self.pos,
            terrain=self.terrain,
            yields_item=self.yields_item,
            remaining=self.remaining,
            max_harvests=self.max_harvests,
            respawn_cooldown=self.respawn_cooldown,
            cooldown_remaining=self.cooldown_remaining,
            harvest_ticks=self.harvest_ticks,
        )


# ---------------------------------------------------------------------------
# Resource type definitions per terrain
# ---------------------------------------------------------------------------

# (resource_type, name, yields_item, max_harvests, respawn_cooldown, harvest_ticks)
TERRAIN_RESOURCES: dict[int, list[tuple[str, str, str, int, int, int]]] = {
    Material.FOREST: [
        ("herb_patch",   "Herb Patch",       "herb",           3, 25, 2),
        ("timber",       "Timber",           "wood",           4, 30, 3),
        ("berry_bush",   "Berry Bush",       "wild_berries",   2, 20, 1),
    ],
    Material.DESERT: [
        ("gem_deposit",  "Gem Deposit",      "raw_gem",        2, 35, 3),
        ("cactus_fiber", "Cactus Fiber",     "fiber",          3, 20, 2),
        ("sand_iron",    "Desert Iron",      "iron_ore",       3, 30, 3),
    ],
    Material.SWAMP: [
        ("mushroom_grove", "Mushroom Grove", "glowing_mushroom", 3, 25, 2),
        ("bog_iron",     "Bog Iron Deposit", "iron_ore",       3, 30, 3),
        ("dark_moss",    "Dark Moss",        "dark_moss",      2, 20, 2),
    ],
    Material.MOUNTAIN: [
        ("ore_vein",     "Ore Vein",         "iron_ore",       4, 30, 3),
        ("crystal_node", "Crystal Node",     "enchanted_dust", 2, 40, 4),
        ("granite_quarry", "Granite Quarry", "stone_block",    3, 35, 3),
    ],
    Material.FLOOR: [
        ("berry_bush",   "Wild Berry Bush",  "wild_berries",   2, 25, 1),
    ],
}
