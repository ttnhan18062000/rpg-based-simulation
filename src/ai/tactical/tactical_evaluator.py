from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional

from src.ai.tactical.contract import TacticalMode, TacticalRole, TacticalEvaluation
from src.core.models.enums import HeroClass, LifeRole, ActionType
from src.core.gameplay.items.item_registry import ITEM_REGISTRY
from src.core.models.reason_codes import ActionReason, ReasonCode

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.core.entities.entity import Entity

logger = logging.getLogger(__name__)

class TacticalEvaluator:
    """Derives deliberate tactical intent from current context."""

    @staticmethod
    def evaluate_tactics(ctx: AIContext) -> TacticalEvaluation:
        actor = ctx.actor
        role = TacticalEvaluator._derive_role(actor)
        weapon_range = TacticalEvaluator._get_weapon_range(actor)
        
        # Milestone 7: Rollout Hardening
        if ctx.config and not ctx.config.overhaul_features.get("use_tactical_evaluator_v2", True):
            enemy = ctx.nearest_enemy()
            return TacticalEvaluation(
                target_id=enemy.id if enemy else None,
                mode=TacticalMode.CLOSE,
                role=role,
                reason=ActionReason(code=ReasonCode.LEGACY_FALLBACK, metadata={"detail": "Always Close"}),
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
        reason = ActionReason(code=ReasonCode.LEGACY_FALLBACK, metadata={"detail": "Closing distance"})
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
                reason = ActionReason(code=ReasonCode.LEGACY_FALLBACK, metadata={"detail": "Closing to range"})
        elif role == TacticalRole.MELEE_STRIKER:
            preferred_dist = 1
            if dist > 1:
                mode = TacticalMode.CLOSE
                reason = ActionReason(code=ReasonCode.LEGACY_FALLBACK, metadata={"detail": "Closing for melee"})
            else:
                mode = TacticalMode.MAINTAIN
                reason = ActionReason(code=ReasonCode.MAINTAIN_DISTANCE, metadata={"detail": "Engaged (Maintain contact)"})

        # 4. Small-Group Coordination (Milestone 4 - Task 5)
        self_pos = actor.spatial.pos
        for ally in ctx.visible:
            if ally.id == actor.id: continue
            if not ctx.faction_reg.is_allied(actor.identity.faction, ally.identity.faction):
                continue
            
            # Spacing Preservation: Ranged allies avoid standing adjacent
            if role == TacticalRole.RANGED_SKIRMISHER or role == TacticalRole.SUPPORT_HEALER:
                ally_role = TacticalEvaluator._derive_role(ally)
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
    def _derive_role(actor: Entity) -> TacticalRole:
        """Map entity stats/class to a tactical role."""
        if hasattr(actor.identity, 'world_role') and actor.identity.world_role == LifeRole.HEALER:
            return TacticalRole.SUPPORT_HEALER
            
        h_class = getattr(actor.identity, 'hero_class', HeroClass.NONE)
        
        ranged_classes = {
            HeroClass.RANGER, HeroClass.SHARPSHOOTER, HeroClass.MAGE, 
            HeroClass.ARCHMAGE, HeroClass.CASTER, HeroClass.SCOUT,
            HeroClass.STORM_CALLER
        }
        if h_class in ranged_classes:
            return TacticalRole.RANGED_SKIRMISHER
            
        # Check weapon range if class is ambiguous
        if TacticalEvaluator._get_weapon_range(actor) > 1:
            return TacticalRole.RANGED_SKIRMISHER
            
        return TacticalRole.MELEE_STRIKER

    @staticmethod
    def _get_weapon_range(actor: Entity) -> int:
        if actor.inventory and actor.inventory.weapon:
            weapon_tmpl = ITEM_REGISTRY.get(actor.inventory.weapon)
            if weapon_tmpl:
                return getattr(weapon_tmpl, "weapon_range", 1)
        return 1
