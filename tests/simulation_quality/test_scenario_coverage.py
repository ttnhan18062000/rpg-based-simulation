"""Scenario coverage tests — all 22 scenarios from §6 of quality_scoring_contract.md.

Each test:
1. Emits the correct event_type(s) for that scenario
2. Verifies the correct primary pillar scores it (positive or negative as appropriate)
3. Verifies the listed secondary pillar does NOT score the same event with the same delta sign
   (or returns None for that event type — unless §6 explicitly grants secondary scoring)
"""
from __future__ import annotations
import os
import uuid
import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoringContext
from src.simulation_quality.weights import ScoringWeights
from src.simulation_quality.scorers.agency import AgencyScorer
from src.simulation_quality.scorers.combat import CombatScorer
from src.simulation_quality.scorers.cognition import CognitionScorer
from src.simulation_quality.scorers.economy import EconomyScorer
from src.simulation_quality.scorers.faction import FactionScorer
from src.simulation_quality.scorers.information import InformationScorer
from src.simulation_quality.scorers.narrative import NarrativeScorer
from src.simulation_quality.scorers.progression import ProgressionScorer
from src.simulation_quality.scorers.social import SocialScorer
from src.simulation_quality.scorers.world_dynamics import WorldDynamicsScorer


_WEIGHTS_PATH = os.path.join("config/simulation_quality/scoring_weights.yaml")
_GRADE_PATH = os.path.join("config/simulation_quality/grade_thresholds.yaml")
_DETECTION_PATH = os.path.join("config/simulation_quality/detection_params.yaml")


@pytest.fixture(scope="module")
def weights() -> ScoringWeights:
    return ScoringWeights.load(_WEIGHTS_PATH, _GRADE_PATH, _DETECTION_PATH, "default")


def _env(event_type: str, tick: int = 10, payload: dict | None = None) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=uuid.uuid4().hex, run_id="scenario-test", tick=tick, entity_id=1,
        event_type=event_type, event_category="test", severity="INFO",
        source_system="test", message="", payload=payload or {},
    )


def _ctx(tick: int = 10) -> ScoringContext:
    return ScoringContext(
        run_id="scenario-test", current_tick=tick, entity_count=10,
        pillar_scores={p: 0.0 for p in PillarId},
        pillar_event_counts={p: 0 for p in PillarId},
        window_tag_counts={p: {} for p in PillarId},
    )


# ─── SQ-01: Behavioral loop detection (AGENCY primary, COGNITION excluded) ──

def test_sq01_agency_owns_defer_with_reason(weights: ScoringWeights) -> None:
    agency = AgencyScorer(weights)
    cognition = CognitionScorer(weights)
    env = _env("defer_with_reason", payload={"reason": "no_valid_route"})
    ctx = _ctx()

    agency_rec = agency.score(env, ctx)
    cognition_rec = cognition.score(env, ctx)
    assert agency_rec is not None, "AGENCY must score defer_with_reason (SQ-01)"
    assert cognition_rec is None, "COGNITION must not score defer_with_reason (SQ-01 ownership)"


def test_sq01_agency_owns_route_selected(weights: ScoringWeights) -> None:
    agency = AgencyScorer(weights)
    cognition = CognitionScorer(weights)
    env = _env("route_selected")
    agency_rec = agency.score(env, _ctx())
    cognition_rec = cognition.score(env, _ctx())
    assert agency_rec is not None
    assert cognition_rec is None


# ─── SQ-02: Why do entities all do the same thing? (AGENCY primary) ─────────

def test_sq02_agency_primary_route_novelty(weights: ScoringWeights) -> None:
    agency = AgencyScorer(weights)
    env = _env("route_family_first_use")
    rec = agency.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.AGENCY


# ─── SQ-03: Combat balance (COMBAT primary, WORLD excluded from entity_killed) ─

def test_sq03_combat_owns_combat_initiated(weights: ScoringWeights) -> None:
    combat = CombatScorer(weights)
    world = WorldDynamicsScorer(weights)
    env = _env("combat_initiated")
    combat_rec = combat.score(env, _ctx())
    world_rec = world.score(env, _ctx())
    assert combat_rec is not None and combat_rec.pillar == PillarId.COMBAT
    assert world_rec is None, "WORLD must not score combat_initiated (SQ-03)"


def test_sq03_combat_owns_entity_killed(weights: ScoringWeights) -> None:
    combat = CombatScorer(weights)
    world = WorldDynamicsScorer(weights)
    env = _env("entity_killed")
    combat_rec = combat.score(env, _ctx())
    world_rec = world.score(env, _ctx())
    assert combat_rec is not None
    assert world_rec is None


# ─── SQ-04: Class dominance in combat (COMBAT primary) ─────────────────────

def test_sq04_combat_owns_combat_resolved(weights: ScoringWeights) -> None:
    combat = CombatScorer(weights)
    progression = ProgressionScorer(weights)
    env = _env("combat_resolved")
    combat_rec = combat.score(env, _ctx())
    prog_rec = progression.score(env, _ctx())
    assert combat_rec is not None
    assert prog_rec is None, "PROGRESSION must not score combat_resolved (SQ-04)"


# ─── SQ-05: Faction domination (FACTION primary, not COMBAT) ────────────────

def test_sq05_faction_owns_territory_ownership_changed(weights: ScoringWeights) -> None:
    faction = FactionScorer(weights)
    combat = CombatScorer(weights)
    env = _env("territory_ownership_changed", payload={"faction_territory_pct": 0.6})
    faction_rec = faction.score(env, _ctx())
    combat_rec = combat.score(env, _ctx())
    assert faction_rec is not None and faction_rec.pillar == PillarId.FACTION
    assert combat_rec is None, "COMBAT must not score territory_ownership_changed (SQ-05)"


# ─── SQ-06: Alliance formation (FACTION primary, SOCIAL excluded from alliance_formed) ─

def test_sq06_faction_owns_alliance_proposed(weights: ScoringWeights) -> None:
    faction = FactionScorer(weights)
    social = SocialScorer(weights)
    env = _env("alliance_proposed")
    faction_rec = faction.score(env, _ctx())
    social_rec = social.score(env, _ctx())
    assert faction_rec is not None and faction_rec.pillar == PillarId.FACTION
    # SOCIAL must not score alliance_proposed (per SQ-06 and TestAllianceExclusion)
    assert "alliance_proposed" not in SocialScorer.EVENT_TYPES


# ─── SQ-07: Economic loop alive (ECONOMY primary) ───────────────────────────

def test_sq07_economy_owns_resource_harvested(weights: ScoringWeights) -> None:
    economy = EconomyScorer(weights)
    world = WorldDynamicsScorer(weights)
    env = _env("resource_harvested")
    eco_rec = economy.score(env, _ctx())
    world_rec = world.score(env, _ctx())
    assert eco_rec is not None and eco_rec.pillar == PillarId.ECONOMY
    assert world_rec is None, "WORLD must not score resource_harvested (SQ-07)"


def test_sq07_economy_owns_item_crafted(weights: ScoringWeights) -> None:
    economy = EconomyScorer(weights)
    env = _env("item_crafted")
    rec = economy.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.ECONOMY


def test_sq07_economy_owns_trade_executed(weights: ScoringWeights) -> None:
    economy = EconomyScorer(weights)
    env = _env("trade_executed")
    rec = economy.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.ECONOMY


# ─── SQ-08: Ecology (WORLD primary, ecology_cycle_completed NOT in ECONOMY) ─

def test_sq08_world_owns_ecology_cycle_completed(weights: ScoringWeights) -> None:
    world = WorldDynamicsScorer(weights)
    economy = EconomyScorer(weights)
    env = _env("ecology_cycle_completed")
    world_rec = world.score(env, _ctx())
    eco_rec = economy.score(env, _ctx())
    assert world_rec is not None and world_rec.pillar == PillarId.WORLD
    assert eco_rec is None, "ECONOMY must not score ecology_cycle_completed (SQ-08)"


# ─── SQ-09: Gold inflation (ECONOMY primary only) ───────────────────────────

def test_sq09_economy_owns_gold_transferred(weights: ScoringWeights) -> None:
    economy = EconomyScorer(weights)
    faction = FactionScorer(weights)
    env = _env("gold_transferred")
    eco_rec = economy.score(env, _ctx())
    fac_rec = faction.score(env, _ctx())
    assert eco_rec is not None and eco_rec.pillar == PillarId.ECONOMY
    assert fac_rec is None, "FACTION must not score gold_transferred (SQ-09)"


# ─── SQ-10: XP and leveling (PROGRESSION primary only) ──────────────────────

def test_sq10_progression_owns_xp_granted(weights: ScoringWeights) -> None:
    progression = ProgressionScorer(weights)
    economy = EconomyScorer(weights)
    env = _env("xp_granted", payload={"amount": 10})
    prog_rec = progression.score(env, _ctx())
    eco_rec = economy.score(env, _ctx())
    assert prog_rec is not None and prog_rec.pillar == PillarId.PROGRESSION
    assert eco_rec is None, "ECONOMY must not score xp_granted even from quest rewards (SQ-10)"


def test_sq10_progression_owns_level_up(weights: ScoringWeights) -> None:
    progression = ProgressionScorer(weights)
    env = _env("level_up")
    rec = progression.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.PROGRESSION


# ─── SQ-11: Progression plateau (PROGRESSION primary, AGENCY excluded) ──────

def test_sq11_progression_owns_progression_plateau_detected(weights: ScoringWeights) -> None:
    progression = ProgressionScorer(weights)
    agency = AgencyScorer(weights)
    env = _env("progression_plateau_detected", payload={"type": "xp_freeze"})
    prog_rec = progression.score(env, _ctx())
    agency_rec = agency.score(env, _ctx())
    assert prog_rec is not None
    assert agency_rec is None, "AGENCY must not score progression_plateau_detected (SQ-11)"


# ─── SQ-12: Cooperation (SOCIAL primary, AGENCY excluded from cooperation_event) ─

def test_sq12_social_owns_cooperation_event(weights: ScoringWeights) -> None:
    social = SocialScorer(weights)
    agency = AgencyScorer(weights)
    env = _env("cooperation_event")
    social_rec = social.score(env, _ctx())
    agency_rec = agency.score(env, _ctx())
    assert social_rec is not None and social_rec.pillar == PillarId.SOCIAL
    assert agency_rec is None, "AGENCY must not score cooperation_event (SQ-12)"


# ─── SQ-13: Contracts (SOCIAL primary only) ─────────────────────────────────

def test_sq13_social_owns_contract_completed(weights: ScoringWeights) -> None:
    social = SocialScorer(weights)
    economy = EconomyScorer(weights)
    env = _env("contract_completed")
    social_rec = social.score(env, _ctx())
    eco_rec = economy.score(env, _ctx())
    assert social_rec is not None and social_rec.pillar == PillarId.SOCIAL
    assert eco_rec is None, "ECONOMY must not score contract_completed (SQ-13)"


def test_sq13_social_owns_contract_lapsed(weights: ScoringWeights) -> None:
    social = SocialScorer(weights)
    env = _env("contract_lapsed")
    rec = social.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.SOCIAL


# ─── SQ-14: Reputation (SOCIAL only) ────────────────────────────────────────

def test_sq14_social_owns_reputation_delta(weights: ScoringWeights) -> None:
    social = SocialScorer(weights)
    faction = FactionScorer(weights)
    env = _env("reputation_delta", payload={"delta": 1.5})
    social_rec = social.score(env, _ctx())
    fac_rec = faction.score(env, _ctx())
    assert social_rec is not None and social_rec.pillar == PillarId.SOCIAL
    assert fac_rec is None, "FACTION must not score reputation_delta (SQ-14)"


# ─── SQ-15: Information asymmetry (INFORMATION primary) ─────────────────────

def test_sq15_information_owns_decision_diverged_by_belief(weights: ScoringWeights) -> None:
    information = InformationScorer(weights)
    cognition = CognitionScorer(weights)
    env = _env("decision_diverged_by_belief")
    info_rec = information.score(env, _ctx())
    cog_rec = cognition.score(env, _ctx())
    assert info_rec is not None and info_rec.pillar == PillarId.INFORMATION
    assert cog_rec is None, "COGNITION must not score decision_diverged_by_belief (SQ-15)"


def test_sq15_information_owns_belief_assimilated(weights: ScoringWeights) -> None:
    information = InformationScorer(weights)
    env = _env("belief_assimilated")
    rec = information.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.INFORMATION


# ─── SQ-16: Knowledge economy (INFORMATION primary) ─────────────────────────

def test_sq16_information_owns_paid_information_transaction(weights: ScoringWeights) -> None:
    information = InformationScorer(weights)
    env = _env("paid_information_transaction")
    rec = information.score(env, _ctx(tick=1))
    assert rec is not None and rec.pillar == PillarId.INFORMATION


# ─── SQ-17: World alive (WORLD primary only) ─────────────────────────────────

def test_sq17_world_owns_calamity_spawned(weights: ScoringWeights) -> None:
    world = WorldDynamicsScorer(weights)
    faction = FactionScorer(weights)
    combat = CombatScorer(weights)
    env = _env("calamity_spawned")
    world_rec = world.score(env, _ctx())
    fac_rec = faction.score(env, _ctx())
    combat_rec = combat.score(env, _ctx())
    assert world_rec is not None and world_rec.pillar == PillarId.WORLD
    assert fac_rec is None
    assert combat_rec is None


def test_sq17_world_owns_boss_spawned(weights: ScoringWeights) -> None:
    world = WorldDynamicsScorer(weights)
    env = _env("boss_spawned")
    rec = world.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.WORLD


def test_sq17_world_owns_region_transformed(weights: ScoringWeights) -> None:
    world = WorldDynamicsScorer(weights)
    env = _env("region_transformed")
    rec = world.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.WORLD


# ─── SQ-18: Ecology regeneration (WORLD primary) ────────────────────────────

def test_sq18_world_owns_ecology_cycle_completed(weights: ScoringWeights) -> None:
    world = WorldDynamicsScorer(weights)
    economy = EconomyScorer(weights)
    env = _env("ecology_cycle_completed")
    world_rec = world.score(env, _ctx())
    eco_rec = economy.score(env, _ctx())
    assert world_rec is not None and world_rec.pillar == PillarId.WORLD
    assert eco_rec is None


# ─── SQ-19: Quests (NARRATIVE primary) ───────────────────────────────────────

def test_sq19_narrative_owns_quest_started(weights: ScoringWeights) -> None:
    narrative = NarrativeScorer(weights)
    economy = EconomyScorer(weights)
    env = _env("quest_started")
    narr_rec = narrative.score(env, _ctx())
    eco_rec = economy.score(env, _ctx())
    assert narr_rec is not None and narr_rec.pillar == PillarId.NARRATIVE
    assert eco_rec is None, "ECONOMY must not score quest_started (SQ-19)"


def test_sq19_narrative_owns_quest_completed(weights: ScoringWeights) -> None:
    narrative = NarrativeScorer(weights)
    env = _env("quest_completed")
    rec = narrative.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.NARRATIVE


# ─── SQ-20: History (NARRATIVE primary) ──────────────────────────────────────

def test_sq20_narrative_owns_chronicle_entry_created(weights: ScoringWeights) -> None:
    narrative = NarrativeScorer(weights)
    faction = FactionScorer(weights)
    env = _env("chronicle_entry_created")
    narr_rec = narrative.score(env, _ctx())
    fac_rec = faction.score(env, _ctx())
    assert narr_rec is not None and narr_rec.pillar == PillarId.NARRATIVE
    assert fac_rec is None


def test_sq20_narrative_owns_narrative_milestone(weights: ScoringWeights) -> None:
    narrative = NarrativeScorer(weights)
    env = _env("narrative_milestone")
    rec = narrative.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.NARRATIVE


# ─── SQ-21: Archetype divergence (COGNITION primary) ─────────────────────────

def test_sq21_cognition_owns_decision_divergence_detected(weights: ScoringWeights) -> None:
    cognition = CognitionScorer(weights)
    progression = ProgressionScorer(weights)
    env = _env("decision_divergence_detected")
    cog_rec = cognition.score(env, _ctx())
    prog_rec = progression.score(env, _ctx())
    assert cog_rec is not None and cog_rec.pillar == PillarId.COGNITION
    assert prog_rec is None, "PROGRESSION must not score decision_divergence_detected (SQ-21)"


def test_sq21_progression_owns_trait_expressed(weights: ScoringWeights) -> None:
    progression = ProgressionScorer(weights)
    cognition = CognitionScorer(weights)
    env = _env("trait_expressed")
    prog_rec = progression.score(env, _ctx())
    cog_rec = cognition.score(env, _ctx())
    assert prog_rec is not None and prog_rec.pillar == PillarId.PROGRESSION
    assert cog_rec is None


# ─── SQ-22: Scenario objectives (NARRATIVE primary, AGENCY excluded) ─────────

def test_sq22_narrative_owns_scenario_objective_progressed(weights: ScoringWeights) -> None:
    narrative = NarrativeScorer(weights)
    agency = AgencyScorer(weights)
    env = _env("scenario_objective_progressed")
    narr_rec = narrative.score(env, _ctx())
    agency_rec = agency.score(env, _ctx())
    assert narr_rec is not None and narr_rec.pillar == PillarId.NARRATIVE
    assert agency_rec is None, "AGENCY must not score scenario_objective_progressed (SQ-22)"


def test_sq22_narrative_owns_scenario_stalled(weights: ScoringWeights) -> None:
    narrative = NarrativeScorer(weights)
    env = _env("scenario_stalled")
    rec = narrative.score(env, _ctx())
    assert rec is not None and rec.pillar == PillarId.NARRATIVE
