from __future__ import annotations
from typing import Dict
from src.core.state import LifeStage

_STAGE_ORDINAL: Dict[LifeStage, int] = {
    LifeStage.CHILD: 0,
    LifeStage.ADULT: 1,
    LifeStage.ELDER: 2,
}


class LifeStageService:
    """Provides utility multipliers based on life stage."""

    @staticmethod
    def get_goal_multipliers(stage: LifeStage) -> Dict[str, float]:
        """
        Returns a map of GoalKind -> multiplier.
        Base multiplier is 1.0.
        """
        multipliers = {
            LifeStage.CHILD: {
                "exploration": 1.5,
                "social": 1.2,
                "harvesting": 0.5, # Children don't like work
                "combat": 0.2,     # Children avoid combat
                "fatigue": 0.8     # High energy
            },
            LifeStage.ADULT: {
                # Neutral baseline
            },
            LifeStage.ELDER: {
                "fatigue": 1.5,    # Elders need more rest
                "combat": 0.5,     # Elders avoid physical combat
                "social": 1.3,     # Elders socialize more
                "harvesting": 0.7  # Elders work less
            }
        }
        return multipliers.get(stage, {})

    @staticmethod
    def get_stage_for_age(age_ticks: int) -> LifeStage:
        """
        Pure per-entity age->LifeStage mapping. Numeric boundaries (3000/7000) are
        intentionally duplicated from get_age_bracket() (src/domains/demographics/cohort.py,
        WORLD-DEMO-003 in docs/parity_ledger/world_dynamics.yaml) rather than imported --
        separate vocabularies for separate subsystems (per-entity strategic cognition vs.
        cohort-level aggregate demographics; see TCK-20260824-LIFE-STAGE-TRANSITIONS
        investigation.md Design Decision 1), same underlying tick boundaries. If
        get_age_bracket()'s thresholds ever change, this function's literals must change too.
        """
        if age_ticks < 3000:
            return LifeStage.CHILD
        if age_ticks < 7000:
            return LifeStage.ADULT
        return LifeStage.ELDER

    @staticmethod
    def is_forward_transition(current: LifeStage, target: LifeStage) -> bool:
        """True only if target has a strictly higher ordinal than current -- enforces the
        monotonic forward-only rule (never demote), since every world-generated entity starts
        at age_ticks=0 with life_stage=ADULT already set as a construction default, not a
        literal newborn fact (src/core/builder.py's V2EntityBuilder.identity(), confirmed by
        direct read: life_stage defaults via IdentityComponent's own LifeStage.ADULT default,
        src/core/state.py, whenever the builder's life_stage= kwarg is left None)."""
        return _STAGE_ORDINAL[target] > _STAGE_ORDINAL[current]
