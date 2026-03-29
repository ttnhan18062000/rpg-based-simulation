from __future__ import annotations
from dataclasses import dataclass, field
from src.core.models.vectors import Vector2

@dataclass(slots=True)
class HomeStorage:
    """Persistent storage located at the hero's home."""
    items: list[str] = field(default_factory=list)
    max_slots: int = 20
    level: int = 0

    @property
    def used_slots(self) -> int:
        return len(self.items)

    @property
    def is_full(self) -> bool:
        return self.used_slots >= self.max_slots

    def add_item(self, item_id: str) -> bool:
        if self.is_full:
            return False
        self.items.append(item_id)
        return True

    def remove_item(self, item_id: str) -> bool:
        if item_id in self.items:
            self.items.remove(item_id)
            return True
        return False

    def upgrade_cost(self) -> int | None:
        """Gold cost to upgrade storage capacity."""
        costs = {0: 200, 1: 500}
        return costs.get(self.level)

    def upgrade(self) -> bool:
        cost = self.upgrade_cost()
        if cost is None:
            return False
        self.level += 1
        self.max_slots += 20 if self.level == 1 else 30
        return True

    def copy(self) -> HomeStorage:
        return HomeStorage(
            items=list(self.items),
            max_slots=self.max_slots,
            level=self.level,
        )


@dataclass(slots=True)
class TreasureChest:
    """A respawning treasure chest placed in the world."""
    chest_id: int
    pos: Vector2
    tier: int = 1
    looted: bool = False
    respawn_at: int | None = None
    guard_entity_id: int | None = None

    @property
    def is_available(self) -> bool:
        return not self.looted

    def loot(self, current_tick: int, respawn_ticks: int = 50) -> None:
        self.looted = True
        self.respawn_at = current_tick + respawn_ticks

    def try_respawn(self, current_tick: int) -> bool:
        if not self.looted or self.respawn_at is None:
            return False
        if current_tick >= self.respawn_at:
            self.looted = False
            self.respawn_at = None
            return True
        return False

    def copy(self) -> TreasureChest:
        return TreasureChest(
            chest_id=self.chest_id,
            pos=self.pos,
            tier=self.tier,
            looted=self.looted,
        )

@dataclass(slots=True)
class CorpseNode:
    """A retrievable 'grave' left by a deceased entity (Hero/Boss)."""
    node_id: int
    entity_id: int
    pos: Vector2
    items: list[str] = field(default_factory=list)
    gold: int = 0
    created_tick: int = 0

    def copy(self) -> CorpseNode:
        return CorpseNode(
            node_id=self.node_id,
            entity_id=self.entity_id,
            pos=self.pos,
            items=list(self.items),
            gold=self.gold,
            created_tick=self.created_tick
        )
