"""Perception system — what an entity can see and remember.

All methods are stateless and operate on immutable snapshots.
Enemy/ally detection uses the faction system instead of string comparisons,
so adding new factions or changing alliances requires zero changes here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.faction import FactionRegistry
from src.core.models import Entity, Vector2

if TYPE_CHECKING:
    from src.core.snapshot import Snapshot


class Perception:
    """Stateless perception utilities operating on immutable snapshots."""

    __slots__ = ()

    # ------------------------------------------------------------------
    # Vision
    # ------------------------------------------------------------------

    @staticmethod
    def visible_entities(
        actor: Entity,
        snapshot: Snapshot,
        vision_range: int,
    ) -> list[Entity]:
        """Return entities within Manhattan distance *vision_range* of *actor*."""
        return [
            e
            for e in snapshot.entities.values()
            if e.id != actor.id and e.alive and actor.pos.manhattan(e.pos) <= vision_range
        ]

    # ------------------------------------------------------------------
    # Faction-aware target selection
    # ------------------------------------------------------------------

    @staticmethod
    def nearest_enemy(
        actor: Entity,
        visible: list[Entity],
        faction_reg: FactionRegistry | None = None,
    ) -> Entity | None:
        """Return the closest visible hostile entity, tie-broken by lowest ID.

        Uses the FactionRegistry when provided; falls back to faction != actor.faction.
        """
        if faction_reg is not None:
            enemies = [
                e for e in visible
                if e.alive and faction_reg.is_hostile(actor.faction, e.faction)
            ]
        else:
            enemies = [e for e in visible if e.alive and e.faction != actor.faction]
        if not enemies:
            return None
        return min(enemies, key=lambda e: (actor.pos.manhattan(e.pos), e.id))

    @staticmethod
    def nearest_ally(
        actor: Entity,
        visible: list[Entity],
        faction_reg: FactionRegistry | None = None,
    ) -> Entity | None:
        """Return the closest visible allied entity, tie-broken by lowest ID."""
        if faction_reg is not None:
            allies = [
                e for e in visible
                if e.alive and e.id != actor.id and faction_reg.is_allied(actor.faction, e.faction)
            ]
        else:
            allies = [
                e for e in visible
                if e.alive and e.id != actor.id and e.faction == actor.faction
            ]
        if not allies:
            return None
        return min(allies, key=lambda e: (actor.pos.manhattan(e.pos), e.id))

    @staticmethod
    def count_nearby_allies(
        actor: Entity,
        visible: list[Entity],
        faction_reg: FactionRegistry | None = None,
    ) -> int:
        """Count visible allies (same faction, excluding self)."""
        if faction_reg is not None:
            return sum(
                1 for e in visible
                if e.alive and e.id != actor.id and faction_reg.is_allied(actor.faction, e.faction)
            )
        return sum(
            1 for e in visible
            if e.alive and e.id != actor.id and e.faction == actor.faction
        )

    # ------------------------------------------------------------------
    # Direction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def direction_away_from(origin: Vector2, threat: Vector2) -> Vector2:
        """Return a unit-step Vector2 moving *origin* away from *threat*."""
        dx = origin.x - threat.x
        dy = origin.y - threat.y
        if abs(dx) >= abs(dy):
            return Vector2(1 if dx >= 0 else -1, 0)
        return Vector2(0, 1 if dy >= 0 else -1)

    @staticmethod
    def direction_toward(origin: Vector2, target: Vector2) -> Vector2:
        """Return a unit-step Vector2 moving *origin* toward *target*."""
        dx = target.x - origin.x
        dy = target.y - origin.y
        if dx == 0 and dy == 0:
            return Vector2(0, 0)
        if abs(dx) >= abs(dy):
            return Vector2(1 if dx > 0 else -1, 0)
        return Vector2(0, 1 if dy > 0 else -1)

    # ------------------------------------------------------------------
    # Tile queries
    # ------------------------------------------------------------------

    @staticmethod
    def is_in_town(actor: Entity, snapshot: Snapshot) -> bool:
        """Return True if the actor is standing on a TOWN tile."""
        return snapshot.grid.is_town(actor.pos)

    @staticmethod
    def is_in_sanctuary(actor: Entity, snapshot: Snapshot) -> bool:
        """Return True if the actor is standing on a SANCTUARY tile."""
        return snapshot.grid.is_sanctuary(actor.pos)

    @staticmethod
    def is_in_camp(actor: Entity, snapshot: Snapshot) -> bool:
        """Return True if the actor is standing on a CAMP tile."""
        return snapshot.grid.is_camp(actor.pos)

    @staticmethod
    def is_on_home_territory(
        actor: Entity,
        snapshot: Snapshot,
        faction_reg: FactionRegistry,
    ) -> bool:
        """Return True if the actor is standing on its own faction's territory."""
        mat = snapshot.grid.get(actor.pos)
        return faction_reg.is_home_territory(actor.faction, mat)

    @staticmethod
    def is_on_enemy_territory(
        actor: Entity,
        snapshot: Snapshot,
        faction_reg: FactionRegistry,
    ) -> bool:
        """Return True if the actor is standing on a hostile faction's territory."""
        mat = snapshot.grid.get(actor.pos)
        return faction_reg.is_enemy_territory(actor.faction, mat)

    # ------------------------------------------------------------------
    # Loot & camps
    # ------------------------------------------------------------------

    @staticmethod
    def ground_loot_nearby(actor: Entity, snapshot: Snapshot, radius: int = 3) -> Vector2 | None:
        """Return the position of the nearest ground loot pile within radius, or None."""
        best_pos: Vector2 | None = None
        best_dist = radius + 1
        for (gx, gy), items in snapshot.ground_items.items():
            if not items:
                continue
            dist = abs(actor.pos.x - gx) + abs(actor.pos.y - gy)
            if dist <= radius and dist < best_dist:
                best_dist = dist
                best_pos = Vector2(gx, gy)
        return best_pos

    @staticmethod
    def find_frontier_target(
        actor: Entity,
        snapshot: Snapshot,
        rng_val: int,
    ) -> Vector2 | None:
        """Find an unexplored tile on the frontier (adjacent to explored tiles).

        Returns a walkable unexplored tile near the actor, biased by *rng_val*
        to avoid all entities converging on the same spot.
        """
        explored = actor.terrain_memory
        grid = snapshot.grid
        # Gather frontier tiles: unexplored + adjacent to at least one explored tile
        frontier: list[Vector2] = []
        checked: set[tuple[int, int]] = set()
        for (ex, ey) in explored:
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                nx, ny = ex + dx, ey + dy
                if (nx, ny) in checked or (nx, ny) in explored:
                    continue
                checked.add((nx, ny))
                candidate = Vector2(nx, ny)
                if grid.in_bounds(candidate) and grid.is_walkable(candidate):
                    frontier.append(candidate)
        if not frontier:
            return None
        # Sort by distance to actor, then pick from the closest cluster with some randomness
        frontier.sort(key=lambda p: actor.pos.manhattan(p))
        # Pick from the closest ~8 candidates using rng_val for variety
        pool = frontier[:min(8, len(frontier))]
        return pool[rng_val % len(pool)]

    @staticmethod
    def remembered_enemy_strength(actor: Entity, target_id: int) -> dict | None:
        """Return the remembered entity_memory entry for a specific entity, or None."""
        for em in actor.entity_memory:
            if em["id"] == target_id:
                return em
        return None

    @staticmethod
    def strongest_remembered_enemy(actor: Entity) -> dict | None:
        """Return the remembered enemy with the highest ATK, or None."""
        enemies = [em for em in actor.entity_memory if em.get("atk", 0) > 0]
        if not enemies:
            return None
        return max(enemies, key=lambda em: em.get("atk", 0))

    @staticmethod
    def nearest_camp(actor: Entity, snapshot: Snapshot) -> Vector2 | None:
        """Return the nearest camp center from the snapshot."""
        if not snapshot.camps:
            return None
        best: tuple[int, int] | None = None
        best_dist = 9999
        for cx, cy in snapshot.camps:
            d = abs(actor.pos.x - cx) + abs(actor.pos.y - cy)
            if d < best_dist:
                best_dist = d
                best = (cx, cy)
        return Vector2(best[0], best[1]) if best else None
