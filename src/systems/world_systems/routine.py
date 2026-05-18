# Compliance IDs: PROG-060, PROG-062, PROG-063, SUB-289, SUB-290, SUB-291, SUB-292, SUB-293, SUB-294, SUB-295, SUB-296, SUB-297, SUB-298, SUB-299, SUB-300, SUB-301, SUB-302, SUB-303, SUB-304, SUB-305, SUB-306, TOWN-025, TOWN-026, TOWN-027, TOWN-028, TOWN-029, TOWN-032, TOWN-033, TOWN-034, TOWN-035, TOWN-036, TOWN-037, TOWN-057, TOWN-058, TOWN-059, TOWN-060, TOWN-061, TOWN-062, TOWN-063, TOWN-064, TOWN-065, TOWN-066, TOWN-067, TOWN-068, TOWN-069, TOWN-070, TOWN-071
# Compliance IDs: PROG-060, PROG-062, PROG-063, TOWN-025, TOWN-026, TOWN-027, TOWN-028, TOWN-029, TOWN-032, TOWN-033, TOWN-034, TOWN-035, TOWN-036, TOWN-037, TOWN-057, TOWN-058, TOWN-059, TOWN-060, TOWN-061, TOWN-062, TOWN-063, TOWN-064, TOWN-065, TOWN-066, TOWN-067, TOWN-068, TOWN-069, TOWN-070, TOWN-071
from __future__ import annotations
from dataclasses import replace
from typing import List, Optional
from src.core.state import EntityState, AuthoritativeState
from src.core.strategic import ConcernState
from src.core.enums import ReasonCode

class RoutineService:
    """
    Handles routine-based goal biasing and biological pressure transitions.
    Phase 9: Routine, Biological Needs, and Life-Rhythm.
    """

    @staticmethod
    def evaluate_biological_needs(entity: EntityState, world_time: int) -> List[ConcernState]:
        """
        Generate concerns based on hunger, sleep debt, and rest pressure.
        VERIFIED v2: biological_need_concerns
        """
        concerns = []
        bio = entity.biological

        # 1. Hunger
        if bio.hunger > 50.0:
            concerns.append(ConcernState(
                id="concern_hunger",
                kind="hunger",
                urgency=bio.hunger / 100.0,
                created_tick=0 
            ))

        # 2. Sleep
        is_night = (world_time >= 1800 or world_time < 600)
        sleep_urgency = bio.sleep_debt / 100.0
        if is_night:
            sleep_urgency += 0.3 
        
        if sleep_urgency > 0.4:
            concerns.append(ConcernState(
                id="concern_sleep",
                kind="fatigue",
                urgency=min(1.0, sleep_urgency),
                created_tick=0
            ))

        # 3. Rest Pressure
        if bio.rest_pressure > 70.0:
            concerns.append(ConcernState(
                id="concern_forced_rest",
                kind="fatigue",
                urgency=bio.rest_pressure / 100.0,
                created_tick=0
            ))

        # 4. Critical Health (Safety Concern)
        hp_percent = entity.combat.hp / max(1, entity.combat.max_hp)
        if hp_percent < 0.3:
            concerns.append(ConcernState(
                id="concern_low_hp",
                kind="danger",
                urgency=1.0 - hp_percent,
                created_tick=0
            ))

        return concerns

    @staticmethod
    def evaluate_environmental_concerns(entity: EntityState) -> List[ConcernState]:
        """
        Generate concerns based on inventory status and pending goals.
        """
        concerns = []
        
        # 1. Inventory Full
        inv = entity.inventory
        if inv.max_slots > 0 and len(inv.items) >= inv.max_slots:
            concerns.append(ConcernState(
                id="concern_inventory_full",
                kind="inventory_full",
                urgency=0.9,
                created_tick=0
            ))
            
        # 2. Reward Pending (Quests)
        from src.core.quests import QuestStatus
        for p in entity.strategic.projects.values():
            if p.kind == "quest" and hasattr(p, "quest_status"):
                 if p.quest_status == QuestStatus.COMPLETED:
                      concerns.append(ConcernState(
                          id=f"concern_reward_{p.id}",
                          kind="opportunity",
                          source=p.id,
                          urgency=0.7,
                          created_tick=0
                      ))

        return concerns

    @staticmethod
    def get_routine_utility_boost(entity: EntityState, project_kind: str, world_time: int) -> float:
        """
        Returns a utility boost for routine-related projects.
        VERIFIED v2: routine_goal_biasing
        """
        age = entity.lifecycle.age_ticks
        max_age = entity.lifecycle.max_age_ticks
        is_elder = age > max_age * 0.7
        is_young = age < max_age * 0.2

        if project_kind == "sleep":
            is_night = (world_time >= 1800 or world_time < 600)
            boost = (entity.biological.sleep_debt / 10.0) # 0 to 10
            if is_night:
                boost *= 2.0
            if is_elder:
                boost *= 1.5 # Elders need more rest
            return boost
        
        if project_kind == "eating":
            return (entity.biological.hunger / 10.0) # 0 to 10
            
        if project_kind == "exploration" and is_young:
            return 5.0 # Young entities are curious
            
        return 0.0

    @staticmethod
    def get_role_utility_boost(entity: EntityState, project_kind: str) -> float:
        """
        Returns a utility boost based on the entity's role identity.
        """
        from src.core.enums import EntityRole
        role = entity.identity.role
        pk = project_kind.upper()
        
        if role == EntityRole.SHOPKEEPER and pk == "SHOPKEEPING":
            return 20.0
        if role == EntityRole.HERO and pk == "QUEST":
            return 10.0
        if role == EntityRole.WORKER and pk == "HARVESTING":
            return 15.0
        if role == EntityRole.GUARD and pk == "PATROLLING":
            return 12.0
            
        return 0.0

    @staticmethod
    def apply_role_based_biasing(entity: EntityState, projects: List[ProjectState], world_time: int) -> List[ProjectState]:
        biased_projects = []
        for p in projects:
            boost = RoutineService.get_routine_utility_boost(entity, p.kind, world_time)
            role_boost = RoutineService.get_role_utility_boost(entity, p.kind)
            
            if boost > 0 or role_boost > 0:
                biased_projects.append(replace(p, score=p.score + boost + role_boost))
            else:
                biased_projects.append(p)
        return biased_projects

    @staticmethod
    def evaluate_anchored_behavior(
        entity: EntityState,
        state: AuthoritativeState
    ) -> List[ConcernState]:
        """
        Phase 9: Anchored-World Behavior.
        If entity is idle and away from home, generate a return-home concern.
        VERIFIED v2: anchored_world_behavior
        """
        if not entity.strategic.home_region_id:
            return []
            
        home_region = state.regions.get(entity.strategic.home_region_id)
        if not home_region:
            return []
            
        # Check if already in home region
        from src.engine.legality import LegalityServiceV2
        curr_region = LegalityServiceV2.get_region_for_position(entity.navigation.position, state)
        if curr_region and curr_region.id == home_region.id:
            return []
            
        # If idle (no active project)
        if entity.strategic.current_project_id is None:
             from src.core.strategic import ConcernState
             return [ConcernState(
                 id="concern_return_home",
                 kind="opportunity",
                 source=home_region.id,
                 urgency=0.4,
                 created_tick=state.tick
             )]
             
        return []
