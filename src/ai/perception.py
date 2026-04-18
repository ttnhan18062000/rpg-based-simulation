"""Perception system — what an entity can see and remember.

All methods are stateless and operate on immutable snapshots.
Enemy/ally detection uses the faction system instead of string comparisons,
so adding new factions or changing alliances requires zero changes here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.gameplay.faction import FactionRegistry
from src.core.entities.entity import Entity, Vector2

if TYPE_CHECKING:
    from src.core.models.snapshot import Snapshot
    from src.core.models.local_scars import LocalScarRecord


class Perception:
    """Stateless perception utilities operating on immutable snapshots."""

    __slots__ = ()

    @staticmethod
    def visible_entities(
        actor: Entity,
        snapshot: Snapshot,
        vision_range: int,
    ) -> list[Entity]:
        """Return all entities within Manhattan vision range of actor."""
        nearby_ids = snapshot.nearby_entity_ids(
            actor.spatial.pos.x, actor.spatial.pos.y, vision_range)
        
        # Cache actor attributes outside loop to avoid redundant hasattr/getattr overhead
        per_attr = 0
        if hasattr(actor, "progression") and actor.progression.attributes:
            per_attr = getattr(actor.progression.attributes, "per", 0)
            
        actor_id = actor.id
        ax, ay = actor.spatial.pos.x, actor.spatial.pos.y
        
        result: list[Entity] = []
        for eid in nearby_ids:
            if eid == actor_id:
                continue
            e = snapshot.entities.get(eid)
            if e:
                # 1. Distance check
                if abs(ax - e.spatial.pos.x) + abs(ay - e.spatial.pos.y) > vision_range:
                    continue
                
                # 2. Stealth / Hidden check
                if getattr(e, "is_hidden", False):
                    if per_attr < 20: 
                        continue
                
                result.append(e)
        return result

    @staticmethod
    def visible_scars(
        actor: Entity,
        snapshot: Snapshot,
        scan_range: int,
    ) -> list[LocalScarRecord]:
        """Return localized scars within Manhattan distance *scan_range* of *actor*."""
        ax, ay = actor.spatial.pos.x, actor.spatial.pos.y
        scars = getattr(snapshot, 'scar_registry', [])
        result: list[LocalScarRecord] = []
        # AOA Stabilization: Robust check to avoid MagicMock iteration errors [design-03]
        if not isinstance(scars, (list, tuple, set)):
            return []
            
        for scar in scars:
            dist = actor.spatial.pos.manhattan(scar.location_pos)
            if dist <= scan_range:
                result.append(scar)
        
        return result

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

        Uses the FactionRegistry when provided; falls back to faction != actor.identity.faction.
        """
        if faction_reg is not None:
            enemies = [
                e for e in visible
                if e.combat.alive and faction_reg.is_hostile(actor.identity.faction, e.identity.faction)
            ]
        else:
            enemies = [e for e in visible if e.combat.alive and e.identity.faction != actor.identity.faction]
        
        if not enemies:
            return None
        return min(enemies, key=lambda e: (actor.spatial.pos.manhattan(e.spatial.pos), e.id))

    @staticmethod
    def highest_threat_enemy(
        actor: Entity,
        visible: list[Entity],
        faction_reg: FactionRegistry | None = None,
    ) -> Entity | None:
        """Return the visible hostile with the highest threat score on *actor*.

        Falls back to nearest enemy if no threat data exists.
        Tie-broken by distance then lowest ID.
        """
        if faction_reg is not None:
            enemies = [
                e for e in visible
                if e.combat.alive and faction_reg.is_hostile(actor.identity.faction, e.identity.faction)
            ]
        else:
            enemies = [e for e in visible if e.combat.alive and e.identity.faction != actor.identity.faction]
        if not enemies:
            return None
        # Check threat table for entries
        threat_table = actor.mind.perception.threat_table
        if threat_table:
            # Filter to visible enemies that have threat entries
            threatened = [e for e in enemies if e.id in threat_table]
            if threatened:
                return max(threatened, key=lambda e: (
                    threat_table[e.id], -actor.spatial.pos.manhattan(e.spatial.pos), -e.id))
        # Fallback: nearest enemy
        return min(enemies, key=lambda e: (actor.spatial.pos.manhattan(e.spatial.pos), e.id))

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
                if e.combat.alive and e.id != actor.id and faction_reg.is_allied(actor.identity.faction, e.identity.faction)
            ]
        else:
            allies = [
                e for e in visible
                if e.combat.alive and e.id != actor.id and e.identity.faction == actor.identity.faction
            ]
        if not allies:
            return None
        return min(allies, key=lambda e: (actor.spatial.pos.manhattan(e.spatial.pos), e.id))

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
                if e.combat.alive and e.id != actor.id and faction_reg.is_allied(actor.identity.faction, e.identity.faction)
            )
        return sum(
            1 for e in visible
            if e.combat.alive and e.id != actor.id and e.identity.faction == actor.identity.faction
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
        return snapshot.grid.is_town(actor.spatial.pos)

    @staticmethod
    def is_in_sanctuary(actor: Entity, snapshot: Snapshot) -> bool:
        """Return True if the actor is standing on a SANCTUARY tile."""
        return snapshot.grid.is_sanctuary(actor.spatial.pos)

    @staticmethod
    def is_in_camp(actor: Entity, snapshot: Snapshot) -> bool:
        """Return True if the actor is standing on a CAMP tile."""
        return snapshot.grid.is_camp(actor.spatial.pos)

    @staticmethod
    def is_on_home_territory(
        actor: Entity,
        snapshot: Snapshot,
        faction_reg: FactionRegistry,
    ) -> bool:
        """Return True if the actor is standing on its own faction's territory."""
        mat = snapshot.grid.get(actor.spatial.pos)
        return faction_reg.is_home_territory(actor.identity.faction, mat)

    @staticmethod
    def is_on_enemy_territory(
        actor: Entity,
        snapshot: Snapshot,
        faction_reg: FactionRegistry,
    ) -> bool:
        """Return True if the actor is standing on a hostile faction's territory."""
        mat = snapshot.grid.get(actor.spatial.pos)
        return faction_reg.is_enemy_territory(actor.identity.faction, mat)

    # ------------------------------------------------------------------
    # Loot & camps
    # ------------------------------------------------------------------

    @staticmethod
    def ground_loot_nearby(actor: Entity, snapshot: Snapshot, radius: int = 3) -> Vector2 | None:
        """Return the position of the nearest ground loot pile within radius, or None.
        
        Optimized: uses spatial index for O(1) cell lookup.
        """
        best_pos: Vector2 | None = None
        best_dist = radius + 1
        ax, ay = actor.spatial.pos.x, actor.spatial.pos.y
        
        # Use spatial index to only check nearby cells
        for gx, gy in snapshot.nearby_ground_positions(ax, ay, radius):
            items = snapshot.ground_items.get((gx, gy))
            if not items:
                continue
            dist = abs(ax - gx) + abs(ay - gy)
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

        Optimized: only scans a bounded neighborhood around the actor instead
        of iterating all explored tiles (which grows with the map).
        """
        explored = actor.mind.perception.terrain_memory
        grid = snapshot.grid
        ax, ay = actor.spatial.pos.x, actor.spatial.pos.y
        # Search in expanding rings up to a max scan radius
        # Heroes scan further, others scan less to save CPU
        max_r = 40 if actor.kind == "hero" else 15
        scan_radius = min(actor.spatial.vision_range * 4, max_r)
        frontier: list[tuple[int, Vector2]] = []  # (distance, pos)

        grid_w, grid_h = grid.width, grid.height
        for dy in range(-scan_radius, scan_radius + 1):
            ty = ay + dy
            if ty < 0 or ty >= grid_h:
                continue
            abs_dy = abs(dy)
            remaining = scan_radius - abs_dy
            for dx in range(-remaining, remaining + 1):
                tx = ax + dx
                if tx < 0 or tx >= grid_w:
                    continue
                pos_tuple = (tx, ty)
                if pos_tuple in explored:
                    continue
                # Check if adjacent to an explored tile (frontier condition)
                # Optimized: pre-bind lookups or use local variables
                if not (
                    (tx - 1, ty) in explored or (tx + 1, ty) in explored
                    or (tx, ty - 1) in explored or (tx, ty + 1) in explored
                ):
                    continue
                
                candidate = Vector2(tx, ty)
                if grid.is_walkable(candidate):
                    frontier.append((abs(dx) + abs_dy, candidate))
                    if len(frontier) >= 32:
                        break
            if len(frontier) >= 32:
                break

        if not frontier:
            return None
            
        # Nemesis System: Penalize regions with bad sentiment
        memory_locations = actor.mind.narrative.memory_locations
        if hasattr(actor, "mind") and memory_locations:
            from src.core.world.regions import find_region_at
            sentiment_frontier = []
            for dist, pos in frontier:
                region = find_region_at(pos, snapshot.regions)
                region_id = region.region_id if region else None
                sentiment = memory_locations.get(region_id, 0.0) if region_id else 0.0
                # If sentiment is negative, increase the effective distance (make it less attractive)
                # sentiment -1.0 adds 100 to distance
                effective_dist = dist + (abs(min(0, sentiment)) * 100)
                sentiment_frontier.append((effective_dist, pos))
            frontier = sentiment_frontier

        # Sort by distance, pick from closest candidates with randomness
        frontier.sort(key=lambda t: t[0])
        pool = [p for _, p in frontier[:min(8, len(frontier))]]
        return pool[rng_val % len(pool)]

    @staticmethod
    def nearest_camp(actor: Entity, snapshot: Snapshot) -> Vector2 | None:
        """Return the nearest camp center from the snapshot."""
        if not snapshot.camps:
            return None
        best: tuple[int, int] | None = None
        best_dist = 9999
        for cx, cy in snapshot.camps:
            d = abs(actor.spatial.pos.x - cx) + abs(actor.spatial.pos.y - cy)
            if d < best_dist:
                best_dist = d
                best = (cx, cy)
        return Vector2(best[0], best[1]) if best else None
