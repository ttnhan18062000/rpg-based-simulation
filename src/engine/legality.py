# src/engine/legality.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional, Any, List

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState, RegionState

class LegalityServiceV2:
    """ Authoritative simulation laws for V2. """

    # VERIFIED v2: manhattan_spatial_metric
    @staticmethod
    def get_manhattan_dist(a: Tuple[float, float], b: Tuple[float, float]) -> int:
        return int(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    @staticmethod
    def get_region_for_position(pos: Tuple[float, float], state: AuthoritativeState) -> Optional[RegionState]:
        """Returns the region containing the given position."""
        from src.core.state import RegionState
        for region in state.regions.values():
            x_min, y_min, x_max, y_max = region.bounds
            if x_min <= pos[0] <= x_max and y_min <= pos[1] <= y_max:
                return region
        return None

    @staticmethod
    def is_adjacent(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
        return LegalityServiceV2.get_manhattan_dist(a, b) == 1

    # VERIFIED v2: cardinal_occupancy_legality
    @staticmethod
    def verify_occupancy(
        pos: Tuple[float, float], 
        state_or_context: Any, 
        ignore_entity_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        V2 Authoritative Occupancy Rule:
        Enforces Static Terrain (WALL), Buildings, and Dynamic Entities.
        VERIFIED v2: cardinal_occupancy_legality
        """
        target_grid_pos = (int(pos[0]), int(pos[1]))
        
        # 1. Static Terrain (WALL / blocked_tiles)
        terrain = getattr(state_or_context, 'terrain', {})
        if terrain.get(target_grid_pos) == "WALL":
            return False, "PATH_NOT_FOUND"
            
        blocked_tiles = getattr(state_or_context, 'blocked_tiles', set())
        if target_grid_pos in blocked_tiles:
            return False, "PATH_NOT_FOUND"

        # 2. Buildings (Solid structures)
        buildings = getattr(state_or_context, 'buildings', {})
        if buildings:
            for b in buildings.values():
                if (int(b.position[0]), int(b.position[1])) == target_grid_pos:
                    return False, "BUILDING_OBSTRUCTION"

        # 3. Dynamic Claims (Position claimed this tick)
        claims = getattr(state_or_context, 'transient_claims', [])
        if target_grid_pos in claims:
            return False, "OCCUPANCY_VIOLATION"

        # 4. Dynamic Entities
        entities = getattr(state_or_context, 'entities', None)
        if entities is None:
            entities_list = getattr(state_or_context, 'neighbor_view', [])
            for eid, entity in entities_list:
                if eid == ignore_entity_id: continue
                if not entity.active: continue
                if (int(entity.position[0]), int(entity.position[1])) == target_grid_pos:
                    return False, "OCCUPANCY_VIOLATION"
        else:
            for eid, entity in entities.items():
                if eid == ignore_entity_id: continue
                if not entity.active: continue
                if (int(entity.position[0]), int(entity.position[1])) == target_grid_pos:
                    return False, "OCCUPANCY_VIOLATION"

        return True, "ADVANCING"

    @staticmethod
    def verify_action_legality(
        actor: EntityState,
        action_kind: str,
        state: AuthoritativeState
    ) -> Tuple[bool, str]:
        """
        Checks if the current region suppresses specific actions and enforces actor validity.
        """
        # 1. Actor Validity (Hardening)
        # VERIFIED v2: actor_validity_enforcement
        if not actor.active or not actor.combat.alive:
            return False, "ATTACKER_INCAPACITATED"
            
        if actor.properties.get("status_frozen") or actor.properties.get("status_stunned"):
            return False, "ATTACKER_STATUS_BLOCKED"

        # 2. Regional Suppression
        region = LegalityServiceV2.get_region_for_position(actor.position, state)
        if region and region.suppression_active:
            if action_kind in ["SABOTAGE", "RECRUIT", "THEFT"]:
                 return False, "REGIONAL_SUPPRESSION"
        return True, "LEGAL"
        
    @staticmethod
    def verify_readiness(entity: EntityState) -> Tuple[bool, str]:
        """
        Action Readiness Law: Every ENTITY_ACT requires 100.0 readiness.
        """
        if entity.readiness < 100.0:
            return False, "INSUFFICIENT_READINESS"
        return True, "READY"

    # VERIFIED v2: melee_engagement_rules
    @staticmethod
    def verify_attack_legality(
        attacker: EntityState,
        target: EntityState,
        state_or_context: Any,
        is_opportunity_attack: bool = False
    ) -> Tuple[bool, str]:
        """
        Authoritative validation for a combat interaction.
        """
        # 1. State Validity
        if not attacker.active or not attacker.combat.alive:
            return False, "ATTACKER_INCAPACITATED"
        if not target.active or not target.combat.alive:
            return False, "TARGET_INCAPACITATED"
        if attacker.id == target.id:
            return False, "SELF_ATTACK_ILLEGAL"

        # 2. Readiness / Status Law
        # Opportunity Attacks bypass readiness (Milestone 8 P0)
        if not is_opportunity_attack and attacker.readiness < 100.0:
            return False, "INSUFFICIENT_READINESS"
        
        if attacker.properties.get("status_frozen") or attacker.properties.get("status_stunned"):
            return False, "ATTACKER_STATUS_BLOCKED"

        # 3. Faction Validity (Friendly Fire Law)
        if attacker.identity.faction == target.identity.faction:
            return False, "FRIENDLY_FIRE_ILLEGAL"

        # 4. Range Validity
        dist = LegalityServiceV2.get_manhattan_dist(attacker.position, target.position)
        
        # Environmental Range Penalty (Weather/Perception)
        from src.world.environment import EnvironmentService
        region = LegalityServiceV2.get_region_for_position(attacker.position, state_or_context)
        range_mult = 1.0
        if region:
            weather_mults = EnvironmentService.get_weather_multipliers(region)
            range_mult = weather_mults.get("perception", 1.0)
            
        effective_range = attacker.combat.range * range_mult
        
        # VERIFIED v2: ranged_legality_matrix
        if dist > effective_range:
            return False, "OUT_OF_RANGE"
            
        # Specific Melee Law: Range must be 1
        if effective_range <= 1.5 and dist > 1:
             return False, "MELEE_RANGE_VIOLATION"


        # 5. LoS / Obstruction
        if not LegalityServiceV2.has_line_of_sight(attacker.position, target.position, state_or_context):
            return False, "LOS_OBSTRUCTED"
            
        return True, "LEGAL"

    @staticmethod
    def verify_aoe_legality(
        attacker: EntityState,
        target_pos: Tuple[float, float],
        state_or_context: Any
    ) -> Tuple[bool, str]:
        """
        Validation for Area-of-Effect positioning and execution.
        """
        # VERIFIED v2: aoe_radius_legality
        # 1. Attacker Validity
        if not attacker.active or not attacker.combat.alive:
            return False, "ATTACKER_INCAPACITATED"
        if attacker.readiness < 100.0:
            return False, "INSUFFICIENT_READINESS"
        if attacker.properties.get("status_frozen") or attacker.properties.get("status_stunned"):
            return False, "ATTACKER_STATUS_BLOCKED"

        # 2. Range Validity
        dist = LegalityServiceV2.get_manhattan_dist(attacker.position, target_pos)
        if dist > attacker.combat.range:
            return False, "OUT_OF_RANGE"

        # 3. LoS / Obstruction (Check path to center of AoE)
        if not LegalityServiceV2.has_line_of_sight(attacker.position, target_pos, state_or_context):
            return False, "LOS_OBSTRUCTED"

        return True, "LEGAL"

    @staticmethod
    def verify_skill_legality(
        actor: EntityState,
        skill_id: str,
        state: AuthoritativeState
    ) -> Tuple[bool, str]:
        """
        Pillar 8: Skill Execution Law.
        Skills require cost and cooldown verification.
        """
        from src.core.skills import SKILL_REGISTRY
        
        # 1. Learned check
        if skill_id not in actor.identity.learned_skills:
            return False, "SKILL_NOT_LEARNED"
            
        # 2. Cooldown check
        if actor.identity.cooldowns.get(skill_id, 0) > 0:
            return False, "SKILL_ON_COOLDOWN"
            
        # 3. Cost check
        skill = SKILL_REGISTRY.get(skill_id)
        if skill and actor.stamina.current < skill.cost:
            return False, "INSUFFICIENT_STAMINA"
            
        return True, "LEGAL"

    @staticmethod
    def has_line_of_sight(
        a: Tuple[float, float], 
        b: Tuple[float, float], 
        state_or_context: Any
    ) -> bool:
        """
        Simple Bresenham-like LoS check for WALL/Building obstructions.
        """
        # VERIFIED v2: ranged_los_rules
        x0, y0 = int(a[0]), int(a[1])
        x1, y1 = int(b[0]), int(b[1])
        
        terrain = getattr(state_or_context, 'terrain', {})
        buildings = getattr(state_or_context, 'buildings', {})
        
        dx = x1 - x0
        dy = y1 - y0
        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_y = 1 if dy > 0 else -1 if dy < 0 else 0
        
        curr_x, curr_y = x0, y0
        
        while curr_x != x1:
            curr_x += step_x
            if (curr_x, curr_y) == (x1, y1): break
            if terrain.get((curr_x, curr_y)) == "WALL": return False
            for build in buildings.values():
                if (int(build.position[0]), int(build.position[1])) == (curr_x, curr_y): return False
                
        curr_x = x1
        while curr_y != y1:
            curr_y += step_y
            if (curr_x, curr_y) == (x1, y1): break
            if terrain.get((curr_x, curr_y)) == "WALL": return False
            for build in buildings.values():
                if (int(build.position[0]), int(build.position[1])) == (curr_x, curr_y): return False
                
        return True

    @staticmethod
    def check_high_ground(attacker_pos: Tuple[float, float], defender_pos: Tuple[float, float], state: AuthoritativeState) -> bool:
        """Verify if attacker has clear elevation advantage (Terrain-based)."""
        atk_pos = (int(attacker_pos[0]), int(attacker_pos[1]))
        def_pos = (int(defender_pos[0]), int(defender_pos[1]))
        
        attacker_tile = state.terrain.get(atk_pos, "PLAIN")
        defender_tile = state.terrain.get(def_pos, "PLAIN")
        
        high_ground_tiles = {"HILL", "MOUNTAIN"}
        return attacker_tile in high_ground_tiles and defender_tile not in high_ground_tiles

    @staticmethod
    def get_engagement_state(entity_id: int, state: AuthoritativeState) -> Optional[Any]:
        """Returns the current engagement record for an entity."""
        # VERIFIED v2: engagement_detection_logic
        return state.engagements.get(entity_id)

    @staticmethod
    def check_flanking(defender_id: int, state: AuthoritativeState) -> bool:
        """
        Authoritative geometric flanking check.
        """
        # VERIFIED v2: flanking_geometric
        defender = state.entities.get(defender_id)
        if not defender or not defender.combat.alive:
            return False
            
        x, y = int(defender.position[0]), int(defender.position[1])
        
        def has_hostile_at(pos: Tuple[int, int]) -> bool:
            for entity in state.entities.values():
                if not entity.active or not entity.combat.alive: continue
                if (int(entity.position[0]), int(entity.position[1])) == pos:
                    return entity.identity.faction != defender.identity.faction
            return False

        has_ns = has_hostile_at((x, y - 1)) and has_hostile_at((x, y + 1))
        has_ew = has_hostile_at((x - 1, y)) and has_hostile_at((x + 1, y))
        
        return has_ns or has_ew

    @staticmethod
    def check_cover(attacker_pos: Tuple[float, float], defender_pos: Tuple[float, float], state: AuthoritativeState) -> bool:
        """Verify if defender is behind wall cover relative to attacker."""
        # VERIFIED v2: cover_geometric
        if LegalityServiceV2.get_manhattan_dist(attacker_pos, defender_pos) <= 1:
            return False
            
        dx = defender_pos[0] - attacker_pos[0]
        dy = defender_pos[1] - attacker_pos[1]
        
        x, y = int(defender_pos[0]), int(defender_pos[1])
        
        if abs(dx) > abs(dy):
            check_x = x - (1 if dx > 0 else -1)
            tile = state.terrain.get((check_x, y))
            if tile in {"WALL", "FOREST", "MOUNTAIN"}:
                return True
        else:
            check_y = y - (1 if dy > 0 else -1)
            tile = state.terrain.get((x, check_y))
            if tile in {"WALL", "FOREST", "MOUNTAIN"}:
                return True
                
        return False

    @staticmethod
    def get_entity_priority(entity: EntityState) -> int:
        """Calculate movement/tie-breaking priority."""
        from src.core.enums import EntityRole
        base = 0
        if entity.identity.role == EntityRole.HERO: base = 100
        elif entity.identity.role == EntityRole.MONSTER: base = 50
        
        hp_ratio = (entity.combat.hp / entity.combat.max_hp) if entity.combat.max_hp > 0 else 1.0
        return base + (100 if hp_ratio < 0.3 else 0)

    @staticmethod
    def get_engaged_hostiles(entity: EntityState, state: Any) -> List[int]:
        """Find hostile entities currently in melee engagement with this entity."""
        return LegalityServiceV2.get_engaged_hostiles_at_pos(entity.position, entity, state)

    @staticmethod
    def get_engaged_hostiles_at_pos(pos: Tuple[float, float], entity: EntityState, state: Any) -> List[int]:
        """Find hostile entities that would be in melee engagement with this entity at a hypothetical position."""
        engaged = []
        entities = getattr(state, 'entities', state if isinstance(state, dict) else {})
        if isinstance(entities, dict):
            for other_id, other in entities.items():
                if other_id == entity.id or not other.combat.alive or not other.active:
                    continue
                dist = LegalityServiceV2.get_manhattan_dist(pos, other.position)
                if dist <= 1 and entity.identity.faction != other.identity.faction:
                    engaged.append(other_id)
        elif isinstance(entities, list):
            for other_id, other in entities:
                if other_id == entity.id or not other.combat.alive or not other.active:
                    continue
                dist = LegalityServiceV2.get_manhattan_dist(pos, other.position)
                if dist <= 1 and entity.identity.faction != other.identity.faction:
                    engaged.append(other_id)
        engaged.sort()
        return engaged

    @staticmethod
    def get_occupant(pos: Tuple[float, float], state: Any, ignore_entity_id: Optional[int] = None) -> Optional[int]:
        """Return the ID of the entity occupying the specified tile."""
        entities = getattr(state, 'entities', state if isinstance(state, dict) else {})
        if isinstance(entities, dict):
            for eid, ent in entities.items():
                if eid == ignore_entity_id: continue
                if ent.position == pos and ent.combat.alive and ent.active:
                    return eid
        return None
