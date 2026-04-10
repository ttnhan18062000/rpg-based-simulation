from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from src.core.models.strategy import ConcernRecord, ProjectRecord

if TYPE_CHECKING:
    from src.ai.states.base import AIContext
    from src.ai.strategy.candidate_builder import StrategicCandidate

class StrategicInterruptionService:
    """Handles the comparison between current project commitment and incoming concern pressure.
    
    This implements phase_2_stage_7. It ensures entities stick to projects unless
    a sufficiently high-pressure interrupt (Concern) or high-priority new project appears.
    """

    def find_best_commitment(self, ctx: AIContext, candidates: list[StrategicCandidate]) -> StrategicCandidate:
        """Determines if the entity should continue its current project or switch."""
        current = ctx.current_project
        if not current:
            # If no current commitment, pick the highest priority option available
            return max(candidates, key=lambda c: c.priority) if candidates else None
            
        # 1. Strategic Hysteresis (Lock) [phase_2_stage_3]
        # Prevents rapid switching (thrashing) within a short window.
        if ctx.strategic.project_lock_until > ctx.snapshot.tick:
            return current
            
        # 2. Score Current Commitment
        # we reward persistence: the longer we've worked on it, the harder it is to stop
        duration = ctx.snapshot.tick - current.committed_at
        # Persistence boost ramps up over ~100 ticks, capped by abandonment_cost
        persistence_boost = min(1.0, duration / 100.0) * current.abandonment_cost
        current_score = current.priority + persistence_boost
        
        # 3. Evaluate Interrupters
        best_interrupter: Optional[StrategicCandidate] = None
        max_pressure = -1.0
        
        for cand in candidates:
            if cand == current:
                continue
                
            # Pressure calculation
            pressure = cand.priority
            
            # Extra weight for immediate concerns (Interrupts)
            if isinstance(cand, ConcernRecord):
                # Concerns are often time-sensitive or high-salience (Survival, Threats)
                pressure += 0.5 
            
            # Interruption Threshold Check
            # Only switch if the new pressure exceeds current score + defined threshold
            if pressure > current_score + current.interruption_threshold:
                if pressure > max_pressure:
                    max_pressure = pressure
                    best_interrupter = cand
                    
        return best_interrupter or current
