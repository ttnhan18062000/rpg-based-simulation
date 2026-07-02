from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class SocialScorer(PillarScorer):
    """Scores Social pillar: SQ-12, SQ-13, SQ-14 (primary).

    Does NOT score alliance_formed — that is FactionScorer.
    """

    EVENT_TYPES = (
        "cooperation_event",
        "group_joined",
        "group_expelled",
        "contract_offer_created",
        "contract_offer_accepted",
        "contract_milestone_completed",
        "contract_completed",
        "contract_lapsed",
        "contract_expired_offer",
        "reputation_delta",
        "social_memory_created",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._cooperation_dormant_fired: bool = False
        self._reputation_flat_fired: bool = False

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
                pillar=PillarId.SOCIAL,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=envelope.entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        if et == "cooperation_event":
            # Check cooperation dormancy
            zero_gate = self.weights.int_param("stagnation_window")
            if (
                not self._cooperation_dormant_fired
                and tick > zero_gate
                and context.pillar_event_counts.get(PillarId.SOCIAL, 0) == 0
            ):
                self._cooperation_dormant_fired = True
                return _rec(
                    self.weights["cooperation_dormant"],
                    "zero cooperation events in multi-class world after gate",
                    ("cooperation_dormant",),
                )
            return _rec(self.weights["cooperation_active"], "cooperation event (joint task or help accepted)", ("cooperation_active",))

        if et == "group_joined":
            return _rec(self.weights["group_forming"], "entity joined a group", ("group_forming",))

        if et == "group_expelled":
            return _rec(self.weights["group_enforcement"], "entity expelled from group", ("group_enforcement",))

        if et == "contract_offer_accepted":
            return _rec(self.weights["negotiation_active"], "contract offer accepted", ("negotiation_active",))

        if et == "contract_offer_created":
            return None  # no direct score; tracked for context only

        if et == "contract_milestone_completed":
            return _rec(self.weights["contract_honored"], "contract milestone completed", ("contract_honored",))

        if et == "contract_completed":
            return _rec(self.weights["contract_complete"], "contract fully completed", ("contract_complete",))

        if et == "contract_lapsed":
            return _rec(self.weights["contract_broken"], "contract lapsed (obligor missed milestone)", ("contract_broken",))

        if et == "contract_expired_offer":
            return _rec(self.weights["offer_dead"], "contract offer expired without acceptance", ("offer_dead",))

        if et == "reputation_delta":
            delta_val = payload.get("delta", 0.0)
            # Check reputation flat
            if not self._reputation_flat_fired and payload.get("all_flat", False):
                self._reputation_flat_fired = True
                return _rec(
                    self.weights["reputation_flat"],
                    "all entities with reputation=0 at tick gate",
                    ("reputation_flat",),
                )
            if abs(delta_val) > 0.5:
                return _rec(self.weights["reputation_shifting"], "significant reputation shift", ("reputation_shifting",))
            return None

        if et == "social_memory_created":
            return _rec(self.weights["relationship_depth"], "social memory created for significant interaction", ("relationship_depth",))

        return None
