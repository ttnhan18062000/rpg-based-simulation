"""LivedStructureService — handles seeding and management of roles, routines, and place attachments. [PHASE 3]"""

from typing import Any
from src.core.models.enums import LifeRole, Archetype, Faction, AttachmentKind, GoalType
from src.core.models.lived_structure import RoutineProfile, PlaceAttachment
from src.core.models.vectors import Vector2

class LivedStructureService:
    """Service for initializing and managing entity lived-structure state."""

    @staticmethod
    def get_default_routines(role: LifeRole, archetype: Archetype, faction: Faction) -> list[RoutineProfile]:
        """Returns a list of default routines based on role and identity."""
        routines = []

        # Common Sleep Routine (Default 10 PM to 6 AM)
        # 1 hour = 10 ticks. 240 ticks = 24 hours.
        routines.append(RoutineProfile(
            routine_id="sleep_cycle",
            routine_type="sleeping",
            anchor_type="home",
            schedule_window=(22, 6),
            priority=4.0,
            ideal_goal=GoalType.SLEEP
        ))

        # Role-Specific Routines
        if role == LifeRole.GUARD:
            routines.append(RoutineProfile(
                routine_id="guard_patrol",
                routine_type="patrolling",
                anchor_type="work",
                schedule_window=(8, 18),
                priority=3.0,
                ideal_goal=GoalType.GUARD
            ))
            routines.append(RoutineProfile(
                routine_id="guard_rest",
                routine_type="resting",
                anchor_type="work",
                schedule_window=(18, 22),
                priority=2.0,
                ideal_goal=GoalType.REST
            ))

        elif role == LifeRole.HERO:
            routines.append(RoutineProfile(
                routine_id="hero_quest",
                routine_type="exploring",
                anchor_type="wander",
                schedule_window=(8, 17),
                priority=3.5,
                ideal_goal=GoalType.EXPLORE
            ))
            routines.append(RoutineProfile(
                routine_id="hero_social",
                routine_type="socializing",
                anchor_type="town",
                schedule_window=(17, 21),
                priority=2.5,
                ideal_goal=GoalType.SOCIAL
            ))

        elif role == LifeRole.CRAFTER:
            routines.append(RoutineProfile(
                routine_id="craft_work",
                routine_type="crafting",
                anchor_type="work",
                schedule_window=(8, 19),
                priority=3.0,
                ideal_goal=GoalType.CRAFT
            ))

        elif role == LifeRole.MERCHANT:
            routines.append(RoutineProfile(
                routine_id="merchant_trade",
                routine_type="trading",
                anchor_type="market",
                schedule_window=(9, 17),
                priority=3.5,
                ideal_goal=GoalType.SOCIAL
            ))
            routines.append(RoutineProfile(
                routine_id="merchant_inventory",
                routine_type="organizing",
                anchor_type="work",
                schedule_window=(17, 20),
                priority=2.5,
                ideal_goal=GoalType.REST
            ))

        elif role == LifeRole.SENTRY:

            routines.append(RoutineProfile(
                routine_id="sentry_watch",
                routine_type="watching",
                anchor_type="specific",
                schedule_window=(6, 22), # Long shift for sentries
                priority=3.0,
                ideal_goal=GoalType.GUARD
            ))

        elif role == LifeRole.RAIDER:

            routines.append(RoutineProfile(
                routine_id="raid_prep",
                routine_type="waiting",
                anchor_type="home",
                schedule_window=(6, 12),
                priority=2.0,
                ideal_goal=GoalType.REST
            ))
            routines.append(RoutineProfile(
                routine_id="raid_active",
                routine_type="raiding",
                anchor_type="specific",
                schedule_window=(12, 18),
                priority=3.5,
                ideal_goal=GoalType.COMBAT
            ))

        # Archetype Adjustments (Future phase could tweak priorities here)
        if archetype == Archetype.COWARDLY_SURVIVOR:
            # Cowards prioritize sleep and rest more
            for r in routines:
                if r.routine_type in ("sleeping", "resting"):
                    r.priority += 0.5

        return routines

    @staticmethod
    def get_initial_attachments(entity_id: int, pos: Vector2, role: LifeRole, home_building_id: int | None = None) -> list[PlaceAttachment]:
        """Seeds initial place attachments (subjective importance)."""
        attachments = []

        # All entities get a HOME attachment
        attachments.append(PlaceAttachment(
            location_pos=pos,
            building_id=home_building_id,
            kind=AttachmentKind.HOME,
            importance=1.0,
            tags=["spawn_origin"]
        ))

        # Role-specific attachments
        if role in (LifeRole.GUARD, LifeRole.SENTRY):
            attachments.append(PlaceAttachment(
                location_pos=pos, # Usually guards spawn at their post
                kind=AttachmentKind.TRAINING_GROUND,
                importance=0.6,
                tags=["post"]
            ))
        
        elif role == LifeRole.HERO:
            attachments.append(PlaceAttachment(
                location_pos=pos,
                kind=AttachmentKind.MARKET,
                importance=0.4,
                tags=["favorite_shop"]
            ))

        return attachments
