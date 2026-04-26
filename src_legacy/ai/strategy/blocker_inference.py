from __future__ import annotations
from typing import TYPE_CHECKING, List

from src_legacy.core.models.strategy import (
    ObjectiveRecord, BlockerRecord, BlockerKind, ObjectiveKind
)
from src_legacy.ai.cognition_capacity import CognitionCapacityProfile

if TYPE_CHECKING:
    from src_legacy.ai.states.base import AIContext

class BlockerInferenceService:
    """Infers structural blockers for strategic objectives. [phase_3_task_7]"""

    @staticmethod
    def infer_blockers(ctx: AIContext, objective: ObjectiveRecord, profile: CognitionCapacityProfile) -> List[BlockerRecord]:
        """Inspects an objective and its context to identify blockers."""
        blockers = []
        tick = ctx.snapshot.tick
        actor = ctx.actor
        rng = ctx.rng
        
        from src_legacy.core.models.enums import Domain
        
        # [PHASE 3 INTEL CAPACITY] 
        # Judgment Stability check for core diagnosis accuracy
        seed_offset = hash(objective.objective_id) % 10000
        is_misdiagnosed = rng.next_float(Domain.AI_DECISION, actor.id, tick, seed_offset) > profile.judgment_stability
        # 1. Knowledge Blockers (Missing coordinates)
        if objective.kind in (ObjectiveKind.VISIT, ObjectiveKind.KILL, ObjectiveKind.COLLECT):
            if objective.target_pos is None and objective.target_id is None:
                # We don't know where to go!
                blockers.append(BlockerRecord(
                    blocker_id=f"blocker_kn_{objective.objective_id}_{tick}",
                    kind=BlockerKind.KNOWLEDGE,
                    label=f"Location unknown for '{objective.label}'",
                    subject_ref=objective.objective_id,
                    severity=1.0,
                    confidence=1.0,
                    suggested_detour_types=[ObjectiveKind.INVESTIGATE, ObjectiveKind.SCOUT],
                    discovered_tick=tick
                ))
        
        # 2. Capability Blockers (Health/Stamina stressors)
        if actor.combat.hp < actor.combat.max_hp * 0.3:
             # Too injured to pursue high-risk objectives
             if objective.kind in (ObjectiveKind.KILL, ObjectiveKind.COLLECT, ObjectiveKind.SCOUT):
                  blockers.append(BlockerRecord(
                    blocker_id=f"blocker_cap_injury_{objective.objective_id}",
                    kind=BlockerKind.CAPABILITY,
                    label="Insufficient health for challenge",
                    subject_ref=objective.objective_id,
                    severity=0.8,
                    confidence=1.0,
                    suggested_detour_types=[ObjectiveKind.WAIT, ObjectiveKind.VISIT],
                    discovered_tick=tick
                ))

        # 3. Material/Gold Blockers (already often ingested, but can be inferred)
        if hasattr(objective, "gold_cost") and objective.gold_cost > actor.progression.gold:
             blockers.append(BlockerRecord(
                    blocker_id=f"blocker_mat_gold_{objective.objective_id}",
                    kind=BlockerKind.MATERIAL,
                    label=f"Insufficient gold (need {objective.gold_cost})",
                    subject_ref=objective.objective_id,
                    severity=0.9,
                    confidence=1.0,
                    suggested_detour_types=[ObjectiveKind.COLLECT, ObjectiveKind.KILL], # Loot/rewards
                    discovered_tick=tick
                ))
        
        # 4. Social Blockers (Non-solo viability) [PHASE 4]
        if objective.kind in (ObjectiveKind.KILL, ObjectiveKind.SCOUT):
            # Find the target entity in context if possible
            target_id = objective.target_id
            target = ctx.snapshot.entities.get(target_id) if target_id else None
            
            # Simple heuristic: ELITE or WORLD_BOSS tier usually requires a group
            # Also check if we are already in a group
            is_solo = not actor.identity.group_id
            
            if is_solo and target:
                from src_legacy.core.models.enums import EnemyTier
                is_elite = getattr(target.identity, "tier", 0) >= EnemyTier.ELITE
                
                # Power check (Approximate: Level + HP)
                my_power = actor.progression.level + (actor.combat.max_hp / 10.0)
                target_power = target.progression.level + (target.combat.max_hp / 10.0)
                
                if is_elite or target_power > my_power * 1.5:
                    # [PHASE 4] judgment_stability determines if we "admit" we need help
                    seed_offset_social = seed_offset + 100
                    ignore_social_need = rng.next_float(Domain.AI_DECISION, actor.id, tick, seed_offset_social) > profile.judgment_stability
                    
                    if not ignore_social_need:
                        blockers.append(BlockerRecord(
                            blocker_id=f"blocker_soc_{objective.objective_id}",
                            kind=BlockerKind.SOCIAL,
                            label=f"Cannot solo {target.identity.name if hasattr(target.identity, 'name') else 'target'}",
                            subject_ref=str(target_id),
                            severity=0.9,
                            confidence=1.0,
                            suggested_detour_types=[ObjectiveKind.INTERACT], # Recruitment
                            discovered_tick=tick
                        ))

        # [PHASE 3 INTEL CAPACITY] Apply misdiagnosis if stability check failed
        if is_misdiagnosed:
             for b in blockers:
                  # Shift kind randomly
                  kinds = [BlockerKind.KNOWLEDGE, BlockerKind.CAPABILITY, BlockerKind.MATERIAL, BlockerKind.ACCESS]
                  b.kind = kinds[rng.next_int(Domain.AI_DECISION, actor.id, tick, 0, len(kinds)-1, seed_offset + 1)]
                  b.label = f"Misfocused: {b.label}"
                  # Perturb severity
                  b.severity = max(0.1, min(1.0, b.severity + (rng.next_float(Domain.AI_DECISION, actor.id, tick, seed_offset + 2) - 0.5) * 0.4))
        
        return blockers
