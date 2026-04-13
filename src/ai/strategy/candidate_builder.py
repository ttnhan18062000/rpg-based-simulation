from __future__ import annotations
from typing import TYPE_CHECKING, Union
from src.core.models.strategy import StrategicStatus, ProjectRecord, ProjectKind, ConcernRecord, ConcernKind
from src.core.models.vectors import Vector2

if TYPE_CHECKING:
    from src.ai.states.base import AIContext

StrategicCandidate = Union[ProjectRecord, ConcernRecord]

class StrategicCandidateBuilder:
    """Filters the latent strategic space into a small, salient 'active decision slice'.
    
    This implements phase_2_stage_4 logic. It bounds cognition by ensuring the
    evaluator only considers the most relevant candidates.
    """

    @staticmethod
    def build_decision_slice(ctx: AIContext, max_candidates: int = 5, fresh_concerns: list[ConcernRecord] | None = None) -> list[StrategicCandidate]:
        """Surfaces the most salient strategic options for evaluation."""
        # 0. Sense immediate environment for new concerns [STAGE 4 RESTORATION]
        environmental_concerns = StrategicCandidateBuilder._sense_world_events(ctx)
        
        candidates: list[StrategicCandidate] = []
        candidates.extend(environmental_concerns)
        
        # 0a. Inject ephemeral/proposed concerns from the current cycle [BUGFIX-2026-04-12]
        if fresh_concerns:
            candidates.extend(fresh_concerns)
        
        # 1. Current commitment (always include to allow continuation scoring)
        if ctx.current_project:
            candidates.append(ctx.current_project)
            
        # 2. Active concerns (Immediate interrupts)
        # Ordered by priority; concerns are often high-priority interruptions.
        concerns = sorted(ctx.active_concerns, key=lambda c: c.priority, reverse=True)
        candidates.extend(concerns)
        
        # 3. Top-priority suspended project
        # Only consider one suspended project at a time to keep the slice thin.
        suspended = [p for p in ctx.strategic.projects if p.status == StrategicStatus.SUSPENDED]
        if suspended:
            candidates.append(max(suspended, key=lambda p: p.priority))

        # 4. Propose new projects from high-priority directives if nothing is active
        if not ctx.current_project and not concerns:
            # Promote directives to potential projects
            for directive in ctx.active_directives:
                # Simple convention: one project per directive
                prj_id = f"project_{directive.directive_id}"
                # Only if not already present in some form
                if not any(p.project_id == prj_id for p in ctx.strategic.projects):
                    # Create a virtual project record for the evaluator to rank
                    potential_prj = ProjectRecord(
                        project_id=prj_id,
                        kind=ProjectKind.SOCIAL, # Default or mapped from directive kind
                        label=directive.label,
                        priority=directive.priority,
                        created_tick=ctx.snapshot.tick
                    )
                    candidates.append(potential_prj)

            inactive = [p for p in ctx.strategic.projects if p.status == StrategicStatus.ACTIVE and p.project_id != ctx.strategic.current_project_id]
            candidates.extend(sorted(inactive, key=lambda p: p.priority, reverse=True))

        # Deduplicate and cap
        seen_ids = set()
        final_slice = []
        for item in candidates:
            # Use specific ID fields
            uid = getattr(item, "project_id", None) or getattr(item, "concern_id", None)
            if uid and uid not in seen_ids:
                seen_ids.add(uid)
                final_slice.append(item)
                if len(final_slice) >= max_candidates:
                    break
                    
        return final_slice

    @staticmethod
    def _sense_world_events(ctx: AIContext) -> list[ConcernRecord]:
        """Detects high-salience world events that should be promoted to concerns."""
        concerns = []
        world = ctx.snapshot # Use snapshot for side-effect-free sensing
        entity = ctx.actor
        pos = entity.spatial.pos
        
        # 1. Regional Danger Sensing
        region_id = entity.spatial.region_id
        if region_id:
            # Check regional consequences (mapped in world state)
            # In our system, this is often in world.region_consequence_registry
            reg = getattr(world, "region_consequence_registry", {}).get(region_id)
            if reg and reg.danger_level > 0.7:
                concerns.append(ConcernRecord(
                    concern_id="concern_regional_threat",
                    kind=ConcernKind.THREAT,
                    label=f"Regional Instability: {region_id}",
                    priority=8.0,
                    created_tick=world.tick
                ))
        
        # 2. Scar Detection (Historical Trauma)
        scars = getattr(world, "scar_registry", [])
        for scar in scars:
            if scar.location_pos.manhattan(pos) < 10:
                concerns.append(ConcernRecord(
                    concern_id="concern_nearby_scar",
                    kind=ConcernKind.OPPORTUNITY,
                    label=f"Trauma Site: {scar.kind.name}",
                    priority=5.0,
                    source_event_id=getattr(scar, "source_event_id", None),
                    created_tick=world.tick
                ))
                # Only sense the most salient scar to prevent flood
                break
                
        # 3. Biological Need Sensing [phase_2_stage_1]
        routine = entity.mind.routine
        if routine.hunger_level > 0.8:
            concerns.append(ConcernRecord(
                concern_id="concern_survival_hunger",
                kind=ConcernKind.THREAT,
                label="Starvation Risk",
                priority=9.0,
                created_tick=world.tick
            ))
        if routine.sleep_debt > 0.8:
            concerns.append(ConcernRecord(
                concern_id="concern_survival_exhaustion",
                kind=ConcernKind.THREAT,
                label="Extreme Exhaustion",
                priority=8.5,
                created_tick=world.tick
            ))
                
        return concerns
