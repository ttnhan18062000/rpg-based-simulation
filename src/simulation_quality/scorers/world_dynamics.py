from __future__ import annotations
from typing import Optional

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord, ScoringContext
from src.simulation_quality.scorers.base import PillarScorer
from src.simulation_quality.weights import ScoringWeights


class WorldDynamicsScorer(PillarScorer):
    """Scores World Dynamics pillar: SQ-17, SQ-18 (primary).

    ecology_cycle_completed is scored HERE (not in EconomyScorer) per SQ-08 conflict note.
    """

    PILLAR_ID = PillarId.WORLD

    EVENT_TYPES = (
        "calamity_spawned",
        "boss_spawned",
        "raid_party_spawned",
        "region_transformed",
        "region_trauma_delta",
        "region_ownership_changed",
        "ecology_cycle_completed",  # owned by WorldDynamicsScorer per SQ-08
        "spawn_cadence_fired",
        "demographic_birth",
        "demographic_mortality",
        "camp_constructed",
        "hazard_drain_applied",
        "threat_evolved",
        "node_recharged",
        "building_sabotaged",
        "spawn_occupancy_violation",
    )

    def __init__(self, weights: ScoringWeights) -> None:
        super().__init__(weights)
        self._calamity_dormant_fired: bool = False
        self._spawn_dormant_fired: bool = False
        self._world_static_fired: bool = False
        self._ecology_broken_fired: bool = False
        self._demographics_dormant_fired: bool = False

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
                pillar=PillarId.WORLD,
                delta=delta,
                reason=reason,
                event_type=et,
                entity_id=envelope.entity_id,
                region_id=payload.get("region_id"),
                tags=tags,
            )

        window_tags = context.window_tag_counts.get(PillarId.WORLD, {})

        if et == "calamity_spawned":
            calamity_gate = self.weights.int_param("zero_emergence_by_tick")
            if (
                not self._calamity_dormant_fired
                and tick > calamity_gate
                and window_tags.get("calamity_active", 0) == 0
            ):
                self._calamity_dormant_fired = True
                return _rec(
                    self.weights["calamity_dormant"],
                    "zero calamity events in run of 500+ ticks",
                    ("calamity_dormant",),
                )
            return _rec(self.weights["calamity_active"], "calamity spawned", ("calamity_active",))

        if et == "boss_spawned":
            if payload.get("spawn_blocked", False):
                return _rec(
                    self.weights["boss_spawn_blocked"],
                    "boss spawn cadence never fired despite threat threshold exceeded",
                    ("boss_spawn_blocked",),
                )
            return _rec(self.weights["boss_active"], "boss entity spawned", ("boss_active",))

        if et == "raid_party_spawned":
            return _rec(self.weights["raid_active"], "raid party spawned", ("raid_active",))

        if et == "region_transformed":
            world_static_gate = self.weights.int_param("loop_sustained_window")
            if (
                not self._world_static_fired
                and tick > world_static_gate * 10  # proxy for 1000 ticks
                and window_tags.get("world_evolving", 0) == 0
            ):
                self._world_static_fired = True
                return _rec(
                    self.weights["world_static"],
                    "zero region transformations in run of 1000+ ticks",
                    ("world_static",),
                )
            return _rec(self.weights["world_evolving"], "region type transformation fired", ("world_evolving",))

        if et == "region_trauma_delta":
            trauma_delta = payload.get("delta", 0.0)
            if trauma_delta > 0:
                # Check trauma_hazard_broken: trauma increasing with no hazard effect
                if payload.get("hazard_level_zero", False):
                    return _rec(
                        self.weights["trauma_hazard_broken"],
                        "regional trauma rising with no hazard_level effect",
                        ("trauma_hazard_broken",),
                    )
                return _rec(self.weights["trauma_feedback"], "regional trauma escalating from combat deaths", ("trauma_feedback",))
            return None

        if et == "region_ownership_changed":
            return _rec(self.weights["political_change"], "region ownership transition", ("political_change",))

        if et == "ecology_cycle_completed":
            # Ecology broken: all nodes depleted with zero ecology fires
            if payload.get("ecology_broken", False):
                if not self._ecology_broken_fired:
                    self._ecology_broken_fired = True
                    return _rec(
                        self.weights["ecology_broken"],
                        "all resource nodes permanently depleted with zero ecology fires",
                        ("ecology_broken",),
                    )
                return None
            return _rec(self.weights["ecology_cycling"], "resource ecology cycle completed", ("ecology_cycling",))

        if et == "spawn_cadence_fired":
            if (
                not self._spawn_dormant_fired
                and payload.get("no_spawn", False)
            ):
                self._spawn_dormant_fired = True
                return _rec(
                    self.weights["world_depopulating"],
                    "zero spawn cadence fires — no monster repopulation after depletion",
                    ("world_depopulating",),
                )
            return _rec(self.weights["world_repopulating"], "monster spawn cadence fired and populated region", ("world_repopulating",))

        if et == "demographic_birth":
            if (
                not self._demographics_dormant_fired
                and payload.get("demographics_dormant", False)
            ):
                self._demographics_dormant_fired = True
                return _rec(
                    self.weights["demographics_dormant"],
                    "zero demographic events in world with demographic config",
                    ("demographics_dormant",),
                )
            return _rec(self.weights["demographics_active"], "demographic birth event", ("demographics_active",))

        if et == "demographic_mortality":
            return _rec(self.weights["natural_lifecycle"], "demographic mortality event", ("natural_lifecycle",))

        if et == "camp_constructed":
            return _rec(self.weights["persistent_structure"], "camp constructed", ("persistent_structure",))

        if et == "hazard_drain_applied":
            return _rec(self.weights["hazard_active"], "hazard drain applied in hazardous region", ("hazard_active",))

        if et == "building_sabotaged":
            return _rec(self.weights["infrastructure_damaged"], "building took sabotage damage — real infrastructure consequence", ("infrastructure_damaged",))

        if et == "spawn_occupancy_violation":
            return _rec(self.weights["spawn_occupancy_violation"], "spawn placement violated occupancy/terrain legality — correctness fault, zero occurrences is the target", ("spawn_occupancy_violation",))

        if et == "threat_evolved":
            return None  # threat_evolved not in scoring table but in event bus; no score defined

        if et == "node_recharged":
            return None  # node_recharged triggers ecology cycle; scored via ecology_cycle_completed

        return None
