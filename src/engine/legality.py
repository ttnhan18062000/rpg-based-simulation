# Compliance IDs: API-003, COMBAT-002, COMBAT-003, COMBAT-016, COMBAT-030, COMBAT-031, COMBAT-033, COMBAT-036, WORLD-118, WORLD-160, WORLD-170, WORLD-171, WORLD-172, WORLD-173
# Compliance IDs: COMB-001, COMB-002, COMB-004, COMB-005, COMB-108, COMB-121, COMB-197, COMB-198, COMB-217, COMB-218, COMB-253, COMB-256, COMB-257, COMB-258, COMB-259, COMB-260, COMB-261, COMB-262, COMB-266, PROG-077, PROG-084, SOC-185
# Compliance IDs: COMB-108, COMB-121
# src/engine/legality.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Optional, Any, List, Dict

from src.engine.domain.view import DomainView
from src.core.enums import ReasonCode, EntityRole
from src.engine.spatial_query import SpatialQueryService
from src.engine.rpg_depth import TerrainCostService
from src.world.environment import EnvironmentService
from src.core.skills import SKILL_REGISTRY

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState, RegionState

class LegalityServiceV2:
    """ Authoritative simulation laws for V2. """

    _spatial_cache: Dict[int, Dict[Tuple[int, int], EntityState]] = {}

    @staticmethod
    def get_spatial_index(state: AuthoritativeState) -> Dict[Tuple[int, int], EntityState]:
        """
        Returns a spatial index of active/alive entities.
        """
        if hasattr(state, "occupancy_snapshot") and state.occupancy_snapshot is not None:
            return {pos: state.entities[e_id] for pos, e_id in state.occupancy_snapshot.occupancy_by_tile.items() if e_id in state.entities}
        occ_map = SpatialQueryService.get_occupancy_map(state)
        return {pos: state.entities[e_id] for pos, e_id in occ_map.items()}


    # VERIFIED v2: manhattan_spatial_metric
    @staticmethod
    def get_manhattan_dist(a: Tuple[float, float], b: Tuple[float, float]) -> int:
        """
        Calculates Manhattan distance between two points.
        Logic ID: COMB-001 (Manhattan distance is the shared spatial metric)
        """
        return int(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    @staticmethod
    def get_region_for_position(pos: Tuple[float, float], state: AuthoritativeState) -> Optional[RegionState]:
        """Returns the region containing the given position."""
        return SpatialQueryService.get_region_at(state, pos)

    @staticmethod
    def is_adjacent(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
        return LegalityServiceV2.get_manhattan_dist(a, b) == 1

    # VERIFIED v2: cardinal_occupancy_legality
    @staticmethod
    def verify_occupancy(
        pos: Tuple[float, float], 
        state_or_context: Any, 
        ignore_entity_id: Optional[int] = None
    ) -> Tuple[bool, ReasonCode]:
        """
        V2 Authoritative Occupancy Rule:
        Enforces Static Terrain (WALL), Buildings, and Dynamic Entities.
        VERIFIED v2: cardinal_occupancy_legality
        Logic ID: COMB-002 (Cardinal/tile movement and occupancy legality are explicit)
        Logic ID: COMB-003 (Occupied-tile movement is rejected)
        Logic ID: COMB-198 (Pathfinding avoids occupied tiles)
        """
        target_grid_pos = (int(pos[0]), int(pos[1]))
        
        # Logic ID: COMB-253 (Movement tests include invalid terrain vs occupied terrain distinction)
        # 1. Static Terrain (WALL / blocked_tiles)
        terrain_map = getattr(state_or_context, 'terrain', {})
        if terrain_map.get(target_grid_pos) == "WALL":
            return False, ReasonCode.PATH_NOT_FOUND
            
        blocked_tiles = getattr(state_or_context, 'blocked_tiles', set())
        if target_grid_pos in blocked_tiles:
            return False, ReasonCode.PATH_NOT_FOUND

        # 2. Buildings (Solid structures)
        # Optimization: Use building_tiles map for O(1) if available, otherwise fallback.
        building_tiles = getattr(state_or_context, 'building_tiles', None)
        if building_tiles is not None:
            if target_grid_pos in building_tiles:
                return False, ReasonCode.BUILDING_OBSTRUCTION
        else:
            buildings = getattr(state_or_context, 'buildings', {})
            for b in buildings.values():
                if (int(b.position[0]), int(b.position[1])) == target_grid_pos:
                    return False, ReasonCode.BUILDING_OBSTRUCTION

        # 3. Dynamic Claims (Position claimed this tick)
        claims = getattr(state_or_context, 'transient_claims', None) or []
        if target_grid_pos in claims:
            return False, ReasonCode.IDEMPOTENCY_VIOLATION

        # 4. Dynamic Entities
        if hasattr(state_or_context, "occupancy_snapshot") and state_or_context.occupancy_snapshot is not None:
            occ_id = state_or_context.occupancy_snapshot.occupant_at(target_grid_pos)
            if occ_id is not None and occ_id != ignore_entity_id:
                return False, ReasonCode.OCCUPANCY_VIOLATION
        else:
            try:
                occ_map = SpatialQueryService.get_occupancy_map(state_or_context)
                occ_id = occ_map.get(target_grid_pos)
                if occ_id is not None and occ_id != ignore_entity_id:
                    return False, ReasonCode.OCCUPANCY_VIOLATION
            except (AttributeError, TypeError):
                 # Fallback context handling
                 entities = getattr(state_or_context, 'entities', {})
                 for eid, ent in entities.items():
                    if eid == ignore_entity_id or not ent.lifecycle.active:
                        continue
                    if (int(ent.navigation.position[0]), int(ent.navigation.position[1])) == target_grid_pos:
                        return False, ReasonCode.OCCUPANCY_VIOLATION

        return True, ReasonCode.LEGAL

    @staticmethod
    def verify_action_legality(
        actor: EntityState,
        action_kind: str,
        state: AuthoritativeState
    ) -> Tuple[bool, ReasonCode]:
        """
        Checks if the current region suppresses specific actions and enforces actor validity.
        """
        # 1. Actor Validity (Hardening)
        # VERIFIED v2: actor_validity_enforcement
        if not actor.lifecycle.active or not actor.combat.alive:
            return False, ReasonCode.TARGET_INVALID
            
        if any(s.kind in ("frozen", "stunned") for s in actor.combat.status_effects):
            return False, ReasonCode.ATTACKER_STATUS_BLOCKED

        # 2. Regional Suppression
        region = LegalityServiceV2.get_region_for_position(actor.navigation.position, state)
        if region and region.suppression_active:
            if action_kind in ["SABOTAGE", "RECRUIT", "THEFT"]:
                 return False, ReasonCode.REGIONAL_SUPPRESSION
        return True, ReasonCode.LEGAL
        
    @staticmethod
    def verify_readiness(entity: EntityState) -> Tuple[bool, ReasonCode]:
        """
        Action Readiness Law: Every ENTITY_ACT requires 100.0 readiness.
        Logic ID: COMB-266 (Readiness/cooldown affects tactical choice)
        Logic ID: COMB-289 (Combat tests cover exhaustion/readiness rejection)
        """
        if entity.combat.readiness < 100.0:
            return False, ReasonCode.INSUFFICIENT_READINESS
        return True, ReasonCode.LEGAL

    @staticmethod
    def verify_movement_legality(
        entity: EntityState,
        target_pos: Tuple[float, float],
        state_or_context: Any,
        move_speed_mult: float = 1.0
    ) -> Tuple[bool, ReasonCode]:
        """
        V2 Authoritative Movement Law:
        Validates if entity has enough readiness for the specific terrain cost of the target tile.
        VERIFIED v2: movement_readiness_gating
        """
        # 0. Status Check
        if any(s.kind in ("frozen", "stunned") for s in entity.combat.status_effects):
            return False, ReasonCode.ATTACKER_STATUS_BLOCKED
        # 1. Occupancy Check
        ok, reason = LegalityServiceV2.verify_occupancy(target_pos, state_or_context, ignore_entity_id=entity.id)
        if not ok:
            return False, reason

        # 2. Terrain Cost Check
        tile = (int(target_pos[0]), int(target_pos[1]))
        terrain_cost = TerrainCostService.get_tile_cost(tile, state_or_context)
        
        # Combined cost
        readiness_cost = (entity.combat.move_cost * terrain_cost) / max(0.1, move_speed_mult)
        
        if entity.combat.readiness < readiness_cost:
            return False, ReasonCode.ACTION_EXHAUSTION
            
        return True, ReasonCode.LEGAL

    # VERIFIED v2: melee_engagement_rules
    @staticmethod
    def verify_attack_legality(
        attacker: EntityState,
        target: EntityState,
        state_or_context: Any,
        is_opportunity_attack: bool = False
    ) -> Tuple[bool, ReasonCode]:
        """
        Authoritative validation for a combat interaction.
        Logic ID: COMB-004 (Melee legality depends on adjacency/engagement)
        Logic ID: COMB-005 (Ranged legality depends on range and line-of-sight)
        Logic ID: COMB-256 (Melee attack requires valid adjacency/engagement)
        Logic ID: COMB-257 (Ranged attack requires valid range)
        Logic ID: COMB-258 (Ranged attack requires valid line-of-sight)
        Logic ID: COMB-283 (Combat tests cover melee legality)
        Logic ID: COMB-284 (Combat tests cover ranged legality)
        Logic ID: COMB-286 (Combat tests cover invalid target rejection)
        Logic ID: COMB-287 (Combat tests cover dead target rejection)
        """
        # 1. State Validity
        if not attacker.lifecycle.active or not attacker.combat.alive:
            return False, ReasonCode.ATTACKER_INCAPACITATED
        if not target.lifecycle.active or not target.combat.alive:
            return False, ReasonCode.TARGET_INCAPACITATED
        if attacker.id == target.id:
            return False, ReasonCode.SELF_ATTACK_ILLEGAL

        # 2. Readiness / Status Law
        # Opportunity Attacks bypass readiness (Milestone 8 P0)
        if not is_opportunity_attack and attacker.combat.readiness < 100.0:
            return False, ReasonCode.INSUFFICIENT_READINESS
        
        if any(s.kind in ("frozen", "stunned") for s in attacker.combat.status_effects):
            return False, ReasonCode.ATTACKER_STATUS_BLOCKED

        # 3. Faction Validity (Friendly Fire Law / Dynamic Relationship Check)
        from src.content_semantics.faction import get_faction_semantics_service, get_faction_id_str, get_race_id_str
        from src.content_semantics.relation import RelationContext

        attacker_faction_str = get_faction_id_str(attacker)
        target_faction_str = get_faction_id_str(target)

        dist = LegalityServiceV2.get_manhattan_dist(attacker.navigation.position, target.navigation.position)
        # Check if they are already engaged in combat
        combat_engaged = False
        if attacker.task.payload.get("target_id") == target.id or target.task.payload.get("target_id") == attacker.id:
            combat_engaged = True

        # `intruding` is left unset (None): no real territorial-trespass detector exists in
        # src/ (confirmed via grep, TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION).
        # Hardcoding False here previously forced RelationProjectionService's own
        # contextual_intruder_groups handling to resolve to "neutral" unconditionally
        # (relation.py's `if context.intruding is False: label = "neutral"` treats an explicit
        # False as a confirmed non-intrusion, permanently overriding combat_engaged), making any
        # faction relationship defined via contextual_intruder_groups (e.g. wild_beast_pack's
        # real content-defined stance toward town_council/hero_guild) structurally unable to
        # ever attack through this path.
        context = RelationContext(
            distance=float(dist),
            combat_engaged=combat_engaged,
            source_race=get_race_id_str(attacker),
            target_race=get_race_id_str(target),
        )

        semantics_service = get_faction_semantics_service()
        # Verify if clean relationship or perspective data exists
        has_clean = False
        source = attacker_faction_str
        target_fac = target_faction_str
        for p in semantics_service.repo.perspectives.values():
            if p.chosen_faction == source or p.id == source:
                has_clean = True
                break
        if not has_clean:
            for rel in semantics_service.repo.faction_relationships.values():
                if rel.source_faction == source and rel.target_faction == target_fac:
                    has_clean = True
                    break

        if has_clean:
            if not semantics_service.is_hostile_compat(attacker_faction_str, target_faction_str, context):
                return False, ReasonCode.FRIENDLY_FIRE_ILLEGAL
        else:
            if attacker.identity.faction == target.identity.faction:
                return False, ReasonCode.FRIENDLY_FIRE_ILLEGAL

        # 4. Range Validity
        dist = LegalityServiceV2.get_manhattan_dist(attacker.navigation.position, target.navigation.position)
        
        # Environmental Range Penalty (Weather/Perception)
        region = LegalityServiceV2.get_region_for_position(attacker.navigation.position, state_or_context)
        range_mult = 1.0
        if region:
            weather_mults = EnvironmentService.get_weather_multipliers(region)
            range_mult = weather_mults.get("perception", 1.0)
            
        effective_range = attacker.combat.range * range_mult
        
        # VERIFIED v2: ranged_legality_matrix
        if dist > effective_range:
            return False, ReasonCode.OUT_OF_RANGE
            
        # Specific Melee Law: Range must be 1
        if effective_range <= 1.5 and dist > 1:
             return False, ReasonCode.OUT_OF_RANGE


        # 5. LoS / Obstruction
        if not LegalityServiceV2.has_line_of_sight(attacker.navigation.position, target.navigation.position, state_or_context):
            return False, ReasonCode.LOS_OBSTRUCTED
            
        return True, ReasonCode.LEGAL

    @staticmethod
    def verify_aoe_legality(
        attacker: EntityState,
        target_pos: Tuple[float, float],
        state_or_context: Any
    ) -> Tuple[bool, ReasonCode]:
        """
        Validation for Area-of-Effect positioning and execution.
        Logic ID: COMB-197 (AoE legality is a function of target position and radius)
        Logic ID: COMB-259 (Area attack requires valid target position)
        Logic ID: COMB-260 (Area attack affects only entities inside AoE radius)
        Logic ID: COMB-261 (AoE friendly-fire behavior is explicit)
        Logic ID: COMB-285 (Combat tests cover AoE legality)
        """
        # VERIFIED v2: aoe_radius_legality
        # 1. Attacker Validity
        if not attacker.lifecycle.active or not attacker.combat.alive:
            return False, ReasonCode.ATTACKER_INCAPACITATED
        if attacker.combat.readiness < 100.0:
            return False, ReasonCode.INSUFFICIENT_READINESS
        if any(s.kind in ("frozen", "stunned") for s in attacker.combat.status_effects):
            return False, ReasonCode.ATTACKER_STATUS_BLOCKED

        # 2. Range Validity
        dist = LegalityServiceV2.get_manhattan_dist(attacker.navigation.position, target_pos)
        if dist > attacker.combat.range:
            return False, ReasonCode.OUT_OF_RANGE

        # 3. LoS / Obstruction (Check path to center of AoE)
        if not LegalityServiceV2.has_line_of_sight(attacker.navigation.position, target_pos, state_or_context):
            return False, ReasonCode.LOS_OBSTRUCTED

        return True, ReasonCode.LEGAL

    @staticmethod
    def verify_skill_legality(
        actor: EntityState,
        skill_id: str,
        state: AuthoritativeState
    ) -> Tuple[bool, ReasonCode]:
        """
        Pillar 8: Skill Execution Law.
        Skills require cost and cooldown verification.
        Logic ID: PROG-077 (Skill definition includes cost/cooldown)
        Logic ID: PROG-084 (Active skills require legality checks)
        """
        # 1. Learned check
        if skill_id not in actor.identity.learned_skills:
            return False, ReasonCode.SKILL_NOT_LEARNED
            
        # 2. Cooldown check
        if actor.identity.cooldowns.get(skill_id, 0) > 0:
            return False, ReasonCode.SKILL_ON_COOLDOWN
            
        # 3. Cost check
        skill = SKILL_REGISTRY.get(skill_id)
        if skill and actor.stamina.current < skill.cost:
            return False, ReasonCode.ACTION_EXHAUSTION
            
        return True, ReasonCode.LEGAL

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
            # CORE-PERF-017: O(1) building check via spatial index
            building_tiles = getattr(state_or_context, 'building_tiles', {})
            if building_tiles and (curr_x, curr_y) in building_tiles:
                return False
            elif not building_tiles:
                # Fallback for tests/legacy where spatial index might be empty
                buildings = getattr(state_or_context, 'buildings', {})
                for b in buildings.values():
                    if (int(b.position[0]), int(b.position[1])) == (curr_x, curr_y):
                        return False
                
        curr_x = x1
        while curr_y != y1:
            curr_y += step_y
            if (curr_x, curr_y) == (x1, y1): break
            if terrain.get((curr_x, curr_y)) == "WALL": return False
            # CORE-PERF-017: O(1) building check via spatial index
            building_tiles = getattr(state_or_context, 'building_tiles', {})
            if building_tiles and (curr_x, curr_y) in building_tiles:
                return False
            elif not building_tiles:
                # Fallback for tests/legacy where spatial index might be empty
                buildings = getattr(state_or_context, 'buildings', {})
                for b in buildings.values():
                    if (int(b.position[0]), int(b.position[1])) == (curr_x, curr_y):
                        return False
                
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
    def check_flanking(defender_id: int, state: AuthoritativeState) -> Tuple[bool, bool]:
        """
        Authoritative geometric flanking check.
        Returns: (is_flanked, is_surrounded)
        """
        # VERIFIED v2: flanking_geometric
        defender = state.entities.get(defender_id)
        if not defender or not defender.combat.alive:
            return False, False
            
        x, y = int(defender.navigation.position[0]), int(defender.navigation.position[1])
        
        spatial_index = LegalityServiceV2.get_spatial_index(state)
        def has_hostile_at(pos: Tuple[int, int]) -> bool:
            entity = spatial_index.get(pos)
            if entity:
                return entity.identity.faction != defender.identity.faction
            return False

        n = has_hostile_at((x, y - 1))
        s = has_hostile_at((x, y + 1))
        e = has_hostile_at((x + 1, y))
        w = has_hostile_at((x - 1, y))
        ne = has_hostile_at((x + 1, y - 1))
        nw = has_hostile_at((x - 1, y - 1))
        se = has_hostile_at((x + 1, y + 1))
        sw = has_hostile_at((x - 1, y + 1))

        hostile_count = sum([n, s, e, w, ne, nw, se, sw])
        # VERIFIED v2: RPG-COMBAT-200
        is_flanked = (n and s) or (e and w) or (ne and sw) or (nw and se)
        is_surrounded = hostile_count >= 3
        
        return is_flanked, is_surrounded

    @staticmethod
    def check_cover(attacker_pos: Tuple[float, float], defender_pos: Tuple[float, float], state: AuthoritativeState) -> bool:
        """
        Verify if defender is behind wall cover relative to attacker.
        Logic ID: COMB-262 (Cover behavior is explicit)
        """
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
    def get_entity_priority(entity: EntityState, state: Optional[Any] = None) -> int:
        """Calculate movement/tie-breaking priority."""
        if state is not None and hasattr(state, "occupancy_snapshot") and state.occupancy_snapshot is not None:
            return state.occupancy_snapshot.get_priority(entity.id)

        base = 0
        if entity.identity.role == EntityRole.HERO: base = 100
        elif entity.identity.role == EntityRole.MONSTER: base = 50
        
        hp_ratio = (entity.combat.hp / entity.combat.max_hp) if entity.combat.max_hp > 0 else 1.0
        return base + (100 if hp_ratio < 0.3 else 0)

    @staticmethod
    def get_engaged_hostiles(entity: EntityState, state: Any) -> List[int]:
        """Find hostile entities currently in melee engagement with this entity."""
        return LegalityServiceV2.get_engaged_hostiles_at_pos(entity.navigation.position, entity, state)

    @staticmethod
    def get_engaged_hostiles_at_pos(pos: Tuple[float, float], entity: EntityState, state: Any) -> List[int]:
        """Find hostile entities that would be in melee engagement with this entity at a hypothetical position."""
        if getattr(state, "_has_hostiles_or_dead_cache", None) is False:
            return []
        my_faction = entity.identity.faction
        px, py = int(pos[0]), int(pos[1])
        engaged = []

        if hasattr(state, "occupancy_snapshot") and state.occupancy_snapshot is not None:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                other_id = state.occupancy_snapshot.occupant_at((px + dx, py + dy))
                if other_id and other_id != entity.id:
                    other = state.entities.get(other_id)
                    if other and other.combat.alive and other.lifecycle.active and my_faction != other.identity.faction:
                        engaged.append(other_id)
            engaged.sort()
            return engaged

        try:
            occ_map = SpatialQueryService.get_occupancy_map(state)
            # Check the 4 cardinal directions (Manhattan distance 1)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                other_id = occ_map.get((px + dx, py + dy))
                if other_id and other_id != entity.id:
                    other = state.entities.get(other_id)
                    if other and other.combat.alive and other.lifecycle.active:
                        if my_faction != other.identity.faction:
                            engaged.append(other_id)
                            
            engaged.sort()
            return engaged
        except (AttributeError, TypeError):
            # Fallback
            entities = getattr(state, 'entities', state if isinstance(state, dict) else {})
            if isinstance(entities, dict):
                for other_id, other in entities.items():
                    if other_id == entity.id or not other.combat.alive or not other.lifecycle.active:
                        continue
                    dist = LegalityServiceV2.get_manhattan_dist(pos, other.navigation.position)
                    if dist <= 1 and entity.identity.faction != other.identity.faction:
                        engaged.append(other_id)
            engaged.sort()
            return engaged

    @staticmethod
    def get_occupant(pos: Tuple[float, float], state: Any, ignore_entity_id: Optional[int] = None) -> Optional[int]:
        """Return the ID of the entity occupying the specified tile."""
        target_grid_pos = (int(pos[0]), int(pos[1]))
        if hasattr(state, "occupancy_snapshot") and state.occupancy_snapshot is not None:
            occ_id = state.occupancy_snapshot.occupant_at(target_grid_pos)
            if occ_id is not None and occ_id != ignore_entity_id:
                return occ_id
            return None

        try:
            occ_map = SpatialQueryService.get_occupancy_map(state)
            occ_id = occ_map.get(target_grid_pos)
            if occ_id is not None and occ_id != ignore_entity_id:
                return occ_id
        except (AttributeError, TypeError):
             # Fallback
             entities = getattr(state, 'entities', state if isinstance(state, dict) else {})
             if isinstance(entities, dict):
                 for eid, ent in entities.items():
                     if eid == ignore_entity_id: continue
                     if (int(ent.navigation.position[0]), int(ent.navigation.position[1])) == target_grid_pos and ent.combat.alive and ent.lifecycle.active:
                         return eid
        return None
