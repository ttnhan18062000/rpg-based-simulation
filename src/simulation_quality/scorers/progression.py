from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class ProgressionScorer(PillarScorer):
    """Scores Progression pillar: SQ-10, SQ-11 (primary), SQ-04 (secondary)."""

    PILLAR_ID = PillarId.PROGRESSION

    EVENT_TYPES = (
        "xp_granted",
        "level_up",
        "skill_unlocked",
        "trait_expressed",
        "pillar_trait_unlocked",
        "progression_conversion_applied",
        "near_death_survival",
        "progression_plateau_detected",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._all_level_1_fired: bool = False
        self._xp_plateau_fired: bool = False
        self._trait_silent_fired: bool = False

    def score(
        self,
        envelope: ObservabilityEventEnvelope,
        context: ScoringContext,
    ) -> Optional[ScoreRecord]:
        et = envelope.event_type
        tick = envelope.tick
        payload = envelope.payload or {}

        def _rec(delta: float, reason: str, tags: tuple[str, ...]) -> ScoreRecord:
            return ScoreRecord(
                tick=tick,
                event_id=envelope.event_id,
                pillar=PillarId.PROGRESSION,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=envelope.entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        window_tags = context.window_tag_counts.get(PillarId.PROGRESSION, {})

        if et == "xp_granted":
            xp_amount = payload.get("amount", 0)
            # +1 per 10 XP
            delta = self.weights["xp_active"] * max(1, xp_amount // 10)
            return _rec(delta, f"XP granted: {xp_amount}", ("xp_active",))

        if et == "level_up":
            # Check for cap: level_up with no effect
            if payload.get("at_cap", False):
                return _rec(self.weights["level_cap_reached"], "level cap reached — no effect", ("level_cap_reached",))
            # Check all_level_1 dormancy
            all_level_1_gate = self.weights.int_param("progression_frozen_by_tick")
            if (
                not self._all_level_1_fired
                and tick > all_level_1_gate
                and window_tags.get("level_milestone", 0) == 0
            ):
                self._all_level_1_fired = True
                return _rec(
                    self.weights["all_level_1"],
                    "all entities still at level 1 after tick gate",
                    ("all_level_1",),
                )
            return _rec(self.weights["level_milestone"], "entity leveled up", ("level_milestone",))

        if et == "skill_unlocked":
            return _rec(self.weights["skill_growth"], "skill unlocked", ("skill_growth",))

        if et == "trait_expressed":
            return _rec(
                self.weights["genetic_determinism_active"],
                "personality trait actively modified decision outcome",
                ("genetic_determinism_active",),
            )

        if et == "pillar_trait_unlocked":
            return _rec(self.weights["pillar_trait_milestone"], "pillar trait milestone unlocked", ("pillar_trait_milestone",))

        if et == "progression_conversion_applied":
            return _rec(
                self.weights["soft_skill_evolution"],
                "progression conversion produced permanent update",
                ("soft_skill_evolution",),
            )

        if et == "near_death_survival":
            return _rec(
                self.weights["survival_experience"],
                "entity survived near-death (hardening fired)",
                ("survival_experience",),
            )

        if et == "progression_plateau_detected":
            # Entity alive 200+ ticks with zero XP
            if payload.get("type") == "xp_freeze":
                return _rec(
                    self.weights["progression_frozen"],
                    "entity alive 200+ ticks with zero XP gain",
                    ("progression_frozen",),
                )
            # Entity level 5+ with no skills
            if payload.get("type") == "skill_silence":
                return _rec(
                    self.weights["skill_system_silent"],
                    "entity level 5+ with zero skill unlocks",
                    ("skill_system_silent",),
                )
            # XP rate dropped to zero after tick 50
            xp_gate = self.weights.int_param("xp_plateau_by_tick")
            if not self._xp_plateau_fired and tick > xp_gate and payload.get("type") == "xp_rate_zero":
                self._xp_plateau_fired = True
                return _rec(
                    self.weights["xp_plateau"],
                    "XP gain rate dropped to zero after tick gate",
                    ("xp_plateau",),
                )
            # Trait system silent
            if not self._trait_silent_fired and payload.get("type") == "trait_rate_zero":
                self._trait_silent_fired = True
                return _rec(
                    self.weights["trait_system_silent"],
                    "trait expression rate zero for entire run",
                    ("trait_system_silent",),
                )
            return None

        return None
