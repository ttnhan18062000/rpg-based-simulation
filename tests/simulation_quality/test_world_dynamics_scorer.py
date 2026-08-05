"""Unit tests for WorldDynamicsScorer — SQ-17, SQ-18. Verifies ecology_cycle_completed IS scored here."""
from __future__ import annotations
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.scorers.economy import EconomyScorer
from src.simulation_quality.scorers.world_dynamics import WorldDynamicsScorer
from src.simulation_quality.weights import ScoringWeights


def _ctx(tick: int = 10, window_tags: dict | None = None) -> ScoringContext:
    return ScoringContext(
        run_id="test", current_tick=tick, entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: 0 for p in PillarId},
        window_tag_counts={p: (window_tags or {}) if p == PillarId.WORLD else {} for p in PillarId},
    )


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="test", tick=tick, entity_id=1,
        event_type=event_type, event_category="world", severity="INFO",
        source_system="test", message="", payload=payload or {},
    )


@pytest.fixture
def scorer(scoring_weights: ScoringWeights) -> WorldDynamicsScorer:
    return WorldDynamicsScorer(scoring_weights)


class TestEcologyOwnership:
    def test_ecology_owned_by_world_scorer(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        """ecology_cycle_completed must be in WorldDynamicsScorer.EVENT_TYPES per SQ-08."""
        assert "ecology_cycle_completed" in WorldDynamicsScorer.EVENT_TYPES

    def test_ecology_not_in_economy_scorer(self) -> None:
        """ecology_cycle_completed must NOT be in EconomyScorer.EVENT_TYPES per SQ-08 conflict note."""
        assert "ecology_cycle_completed" not in EconomyScorer.EVENT_TYPES

    def test_ecology_cycling_positive(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("ecology_cycle_completed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights.for_pillar("WORLD")["ecology_cycling"]

    def test_ecology_broken_once(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("ecology_cycle_completed", payload={"ecology_broken": True}), _ctx())
        assert rec is not None
        assert "ecology_broken" in rec.tags
        rec2 = scorer.score(_env("ecology_cycle_completed", payload={"ecology_broken": True}), _ctx())
        assert rec2 is None


class TestCalamity:
    def test_calamity_active(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("calamity_spawned"), _ctx(window_tags={"calamity_active": 1}))
        assert rec is not None
        assert rec.delta == scoring_weights["calamity_active"]

    def test_calamity_dormant_after_gate(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        gate = scoring_weights.int_param("zero_emergence_by_tick")
        rec = scorer.score(_env("calamity_spawned", tick=gate + 1), _ctx(tick=gate + 1, window_tags={}))
        assert rec is not None
        assert "calamity_dormant" in rec.tags
        assert rec.delta == scoring_weights["calamity_dormant"]


class TestBossAndRaid:
    def test_boss_active(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("boss_spawned"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["boss_active"]

    def test_boss_spawn_blocked(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("boss_spawned", payload={"spawn_blocked": True}), _ctx())
        assert rec is not None
        assert "boss_spawn_blocked" in rec.tags

    def test_raid_active(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("raid_party_spawned"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["raid_active"]


class TestRegion:
    def test_region_transformed(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("region_transformed"), _ctx(window_tags={"world_evolving": 1}))
        assert rec is not None
        assert rec.delta == scoring_weights["world_evolving"]

    def test_region_trauma_positive_delta(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("region_trauma_delta", payload={"delta": 2.0}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["trauma_feedback"]

    def test_region_trauma_hazard_broken(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("region_trauma_delta", payload={"delta": 1.0, "hazard_level_zero": True}), _ctx())
        assert rec is not None
        assert "trauma_hazard_broken" in rec.tags

    def test_region_trauma_non_positive_returns_none(self, scorer: WorldDynamicsScorer) -> None:
        assert scorer.score(_env("region_trauma_delta", payload={"delta": -1.0}), _ctx()) is None

    def test_region_ownership_changed(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("region_ownership_changed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["political_change"]


class TestSpawnAndDemographics:
    def test_spawn_cadence_repopulating(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("spawn_cadence_fired"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["world_repopulating"]

    def test_spawn_cadence_no_spawn(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("spawn_cadence_fired", payload={"no_spawn": True}), _ctx())
        assert rec is not None
        assert "world_depopulating" in rec.tags

    def test_demographic_birth(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("demographic_birth"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["demographics_active"]

    def test_demographic_mortality(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("demographic_mortality"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["natural_lifecycle"]


class TestStructureAndHazard:
    def test_camp_constructed(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("camp_constructed"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["persistent_structure"]

    def test_hazard_drain_applied(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("hazard_drain_applied"), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["hazard_active"]


class TestBuildingSabotage:
    def test_building_sabotaged_registered_in_scorer_registry(self) -> None:
        assert "building_sabotaged" in WorldDynamicsScorer.EVENT_TYPES

    def test_building_sabotaged_scored_by_world_dynamics(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("building_sabotaged", payload={"region_id": "r1"}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["infrastructure_damaged"]
        assert rec.pillar == PillarId.WORLD
        assert "infrastructure_damaged" in rec.tags


class TestSpawnOccupancyViolation:
    def test_spawn_occupancy_violation_in_world_dynamics_event_types(self) -> None:
        assert "spawn_occupancy_violation" in WorldDynamicsScorer.EVENT_TYPES

    def test_spawn_occupancy_violation_scores_negative(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("spawn_occupancy_violation", payload={"region_id": "r1"}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["spawn_occupancy_violation"]
        assert rec.delta < 0
        assert rec.pillar == PillarId.WORLD
        assert "spawn_occupancy_violation" in rec.tags

    def test_scoring_weights_yaml_has_spawn_occupancy_key(self, scoring_weights: ScoringWeights) -> None:
        assert scoring_weights.for_pillar(PillarId.WORLD)["spawn_occupancy_violation"] < 0

    def test_spawn_occupancy_weight_is_negative(self, scoring_weights: ScoringWeights) -> None:
        assert scoring_weights["spawn_occupancy_violation"] < 0


class TestWorldHardLawViolation:
    """TCK-20260805-SIMQ-HARDLAW-BRIDGE-COVERAGE-GAP: covers LAW-STAMINA-NONNEGATIVE,
    LAW-POSITION-FINITE, and LAW-OCCUPANCY-COLLISION, none of which had an existing
    pillar-generic signal to reuse (unlike HP/READINESS -> combat_hard_law_violation and
    GOLD -> conservation_law_violated)."""

    def test_world_hard_law_violation_in_event_types(self) -> None:
        assert "world_hard_law_violation" in WorldDynamicsScorer.EVENT_TYPES

    def test_world_hard_law_violation_scores_negative(self, scorer: WorldDynamicsScorer, scoring_weights: ScoringWeights) -> None:
        rec = scorer.score(_env("world_hard_law_violation", payload={"law_id": "LAW-STAMINA-NONNEGATIVE"}), _ctx())
        assert rec is not None
        assert rec.delta == scoring_weights["world_hard_law"]
        assert rec.delta < 0
        assert rec.pillar == PillarId.WORLD
        assert "world_hard_law" in rec.tags

    def test_scoring_weights_yaml_has_world_hard_law_key(self, scoring_weights: ScoringWeights) -> None:
        assert scoring_weights.for_pillar(PillarId.WORLD)["world_hard_law"] < 0


class TestNullReturn:
    def test_threat_evolved_returns_none(self, scorer: WorldDynamicsScorer) -> None:
        assert scorer.score(_env("threat_evolved"), _ctx()) is None

    def test_node_recharged_returns_none(self, scorer: WorldDynamicsScorer) -> None:
        assert scorer.score(_env("node_recharged"), _ctx()) is None

    def test_null_unknown(self, scorer: WorldDynamicsScorer) -> None:
        assert scorer.score(_env("combat_initiated"), _ctx()) is None
