from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional

from src_legacy.ai.tactical.contract import TacticalMode, TacticalRole, TacticalEvaluation
from src_legacy.core.models.enums import HeroClass, LifeRole, ActionType, Material
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.gameplay.items.item_registry import ITEM_REGISTRY
from src_legacy.core.models.reason_codes import ActionReason, ReasonCode

if TYPE_CHECKING:
    from src_legacy.ai.states.base import AIContext
    from src_legacy.core.entities.entity import Entity

logger = logging.getLogger(__name__)

class TacticalEvaluator:
    """Derives deliberate tactical intent from current context."""

    @staticmethod
    def evaluate_tactics(ctx: AIContext) -> TacticalEvaluation:
        actor = ctx.actor
        role = actor.progression.tactical_role
        weapon_range = TacticalEvaluator._get_weapon_range(actor)
        
        # Milestone 7: Rollout Hardening
        if ctx.config and not ctx.config.overhaul_features.get("use_tactical_evaluator_v2", True):
            enemy = ctx.nearest_enemy()
            return TacticalEvaluation(
                target_id=enemy.id if enemy else None,
                mode=TacticalMode.CLOSE,
                role=role,
                reason=ActionReason(code=ReasonCode.CLOSING_RANGE, metadata={"detail": "Always Close (Legacy Rollout)"}),
                preferred_dist=1
            )
        
        # 1. Primary Target Selection
        enemy = ctx.nearest_enemy()
        if not enemy:
            return TacticalEvaluation(mode=TacticalMode.HOLD, role=role, reason=ActionReason(code=ReasonCode.NO_TARGET))

        dist = actor.spatial.pos.manhattan(enemy.spatial.pos)
        hp_ratio = actor.combat.hp / max(1, actor.combat.hp_max) if hasattr(actor.combat, "hp_max") else (actor.combat.hp / 100.0) # Fallback

        # 2. Tactical Retreat Check (Deliberate, not panic)
        # Retreat if HP is critical and we have a path
        if hp_ratio < 0.25:
            return TacticalEvaluation(
                target_id=enemy.id,
                mode=TacticalMode.RETREAT,
                role=role,
                reason=ActionReason(code=ReasonCode.LOW_HP_RETREAT),
                preferred_dist=weapon_range + 2
            )

        # 3. Distance Management
        mode = TacticalMode.CLOSE
        reason = ActionReason(code=ReasonCode.ADVANCING) # Replaced LEGACY_FALLBACK
        preferred_dist = 1
        
        if role == TacticalRole.RANGED_SKIRMISHER or role == TacticalRole.SUPPORT_HEALER:
            preferred_dist = max(2, weapon_range - 1)
            if dist < 2:
                mode = TacticalMode.WIDEN
                reason = ActionReason(code=ReasonCode.KITING)
            elif dist <= weapon_range:
                mode = TacticalMode.MAINTAIN
                reason = ActionReason(code=ReasonCode.MAINTAIN_DISTANCE)
            else:
                mode = TacticalMode.CLOSE
                reason = ActionReason(code=ReasonCode.ADVANCING, metadata={"detail": "Closing to range"})
        elif role == TacticalRole.MELEE_STRIKER:
            preferred_dist = 1
            if dist > 1:
                mode = TacticalMode.CLOSE
                reason = ActionReason(code=ReasonCode.ADVANCING, metadata={"detail": "Closing for melee"})
            else:
                mode = TacticalMode.MAINTAIN
                reason = ActionReason(code=ReasonCode.MAINTAIN_DISTANCE, metadata={"detail": "Engaged (Maintain contact)"})

        # 4. Group Coordination: Bracketing [Milestone 4]
        if role == TacticalRole.MELEE_STRIKER and dist > 1:
            bracket_pos = TacticalEvaluator._get_bracketing_target(ctx, enemy)
            if bracket_pos:
                return TacticalEvaluation(
                    target_id=enemy.id,
                    mode=TacticalMode.CLOSE,
                    role=role,
                    reason=ActionReason(code=ReasonCode.ADVANCING, metadata={"detail": "Bracketing Target"}),
                    preferred_dist=1,
                    target_pos=(bracket_pos.x, bracket_pos.y)
                )

        # 5. Chokepoint Defense [Milestone 4]
        # Only if melee or kiting needs a stand
        hostiles = [e for e in ctx.visible if ctx.faction_reg.is_hostile(actor.identity.faction, e.identity.faction)]
        choke_pos = TacticalEvaluator._find_nearby_chokepoint(ctx, hostiles)
        if choke_pos:
            return TacticalEvaluation(
                target_id=enemy.id,
                mode=TacticalMode.CHOKEPOINT,
                role=role,
                reason=ActionReason(code=ReasonCode.WAITING, metadata={"detail": "Holding Chokepoint"}),
                preferred_dist=1,
                target_pos=(choke_pos.x, choke_pos.y)
            )

        # 6. Reactive Cover-Seeking [Milestone 4]
        ranged_threats = [e for e in hostiles if TacticalEvaluator._get_weapon_range(e) > 1]
        if ranged_threats:
            cover_pos = TacticalEvaluator._find_nearby_cover(ctx, ranged_threats)
            if cover_pos and cover_pos != actor.spatial.pos:
                return TacticalEvaluation(
                    target_id=enemy.id,
                    mode=TacticalMode.COVER,
                    role=role,
                    reason=ActionReason(code=ReasonCode.SIDESTEPPING, metadata={"detail": "Seeking Cover"}),
                    preferred_dist=weapon_range,
                    target_pos=(cover_pos.x, cover_pos.y)
                )

        # 7. Small-Group Coordination (Spacing)
        self_pos = actor.spatial.pos
        for ally in ctx.visible:
            if ally.id == actor.id: continue
            if not ctx.faction_reg.is_allied(actor.identity.faction, ally.identity.faction):
                continue
            
            # Spacing Preservation: Ranged allies avoid standing adjacent
            if role == TacticalRole.RANGED_SKIRMISHER or role == TacticalRole.SUPPORT_HEALER:
                ally_role = ally.progression.tactical_role
                if (ally_role == TacticalRole.RANGED_SKIRMISHER or ally_role == TacticalRole.SUPPORT_HEALER):
                    if self_pos.manhattan(ally.spatial.pos) <= 1:
                        # Tie-break: Higher ID moves
                        if actor.id > ally.id:
                            mode = TacticalMode.WIDEN
                            reason = ActionReason(code=ReasonCode.ALLY_SPACING, metadata={"ally_id": ally.id})
                            break

        # 5. Safe-Shot Evaluation
        # A shot is safe if we are at range and no enemy is adjacent to us
        is_safe = False
        if dist > 1 and dist <= weapon_range:
            # Check for ANY adjacent enemy (Pillar-Oriented Awareness)
            adjacent_enemies = [e for e in ctx.visible if actor.spatial.pos.manhattan(e.spatial.pos) <= 1 and ctx.faction_reg.is_hostile(actor.identity.faction, e.identity.faction)]
            if not adjacent_enemies:
                is_safe = True

        return TacticalEvaluation(
            target_id=enemy.id,
            mode=mode,
            role=role,
            is_safe_shot=is_safe,
            preferred_dist=preferred_dist,
            reason=reason,
            target_pos=(enemy.spatial.pos.x, enemy.spatial.pos.y)
        )


    @staticmethod
    def _find_nearby_cover(ctx: AIContext, ranged_hostiles: list[Entity]) -> Optional[Vector2]:
        """Find adjacent walkable tile that is next to a WALL. [Milestone 4]"""
        if not ranged_hostiles: return None
        actor_pos = ctx.actor.spatial.pos
        # Check card neighbors
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            cand = actor_pos + Vector2(dx, dy)
            if ctx.snapshot.grid.is_walkable(cand) and ctx.snapshot.get_entity_at(cand) is None:
                # Check cand neighbors for wall
                for nx, ny in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    neighbor = cand + Vector2(nx, ny)
                    if ctx.snapshot.grid.get(neighbor) == Material.WALL:
                        return cand
        return None

    @staticmethod
    def _find_nearby_chokepoint(ctx: AIContext, hostiles: list[Entity]) -> Optional[Vector2]:
        """Find adjacent tile that forms a 1-tile gap corridor. [Milestone 4]"""
        if not hostiles: return None
        actor_pos = ctx.actor.spatial.pos
        # Check current and adjacent
        for dx, dy in [(0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)]:
            cand = actor_pos + Vector2(dx, dy)
            if ctx.snapshot.grid.is_walkable(cand):
                # Skip if occupied (unless it is us)
                occ = ctx.snapshot.get_entity_at(cand)
                if occ is not None and occ != ctx.actor.id:
                    continue
                    
                # Check for corridor N-S or E-W
                is_n_wall = ctx.snapshot.grid.get(cand + Vector2(0, 1)) == Material.WALL
                is_s_wall = ctx.snapshot.grid.get(cand + Vector2(0, -1)) == Material.WALL
                is_e_wall = ctx.snapshot.grid.get(cand + Vector2(1, 0)) == Material.WALL
                is_w_wall = ctx.snapshot.grid.get(cand + Vector2(-1, 0)) == Material.WALL
                
                if (is_n_wall and is_s_wall) or (is_e_wall and is_w_wall):
                     return cand
        return None

    @staticmethod
    def _get_bracketing_target(ctx: AIContext, target: Entity) -> Optional[Vector2]:
        """Find a position opposite to an ally relative to the target. [Milestone 4]"""
        target_pos = target.spatial.pos
        # Allies (excluding self) adjacent to target
        allies = [e for e in ctx.visible if e.id != ctx.actor.id 
                 and ctx.faction_reg.is_allied(ctx.actor.identity.faction, e.identity.faction) 
                 and e.spatial.pos.manhattan(target_pos) == 1]
        
        if not allies: return None
        
        # Pick the first ally and try to stand on the opposite side
        ally_pos = allies[0].spatial.pos
        diff = target_pos - ally_pos 
        bracket_pos = target_pos + diff 
        
        if ctx.snapshot.grid.is_walkable(bracket_pos) and ctx.snapshot.get_entity_at(bracket_pos) is None:
            return bracket_pos
        return None

    @staticmethod
    def _get_weapon_range(actor: Entity) -> int:
        if actor.inventory and actor.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(actor.inventory.weapon)
            if weapon_tmpl:
                return getattr(weapon_tmpl, "weapon_range", 1)
        return 1
