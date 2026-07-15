"""Locks each PillarScorer subclass's PILLAR_ID class attribute to the PillarId its own
_rec() closure hardcodes when constructing ScoreRecord(pillar=...). Manual, explicit
assertions — there is no programmatic way to introspect a closure's hardcoded literal
without parsing source, which would be fragile.
"""
from __future__ import annotations

from src.simulation_quality.pillars import PillarId
from src.simulation_quality.scorers.agency import AgencyScorer
from src.simulation_quality.scorers.cognition import CognitionScorer
from src.simulation_quality.scorers.combat import CombatScorer
from src.simulation_quality.scorers.economy import EconomyScorer
from src.simulation_quality.scorers.faction import FactionScorer
from src.simulation_quality.scorers.information import InformationScorer
from src.simulation_quality.scorers.narrative import NarrativeScorer
from src.simulation_quality.scorers.progression import ProgressionScorer
from src.simulation_quality.scorers.social import SocialScorer
from src.simulation_quality.scorers.world_dynamics import WorldDynamicsScorer
from src.simulation_quality.weights import ScoringWeights


def test_agency_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert AgencyScorer(scoring_weights).PILLAR_ID == PillarId.AGENCY  # agency.py:52 _rec()


def test_cognition_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert CognitionScorer(scoring_weights).PILLAR_ID == PillarId.COGNITION  # cognition.py:41 _rec()


def test_combat_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert CombatScorer(scoring_weights).PILLAR_ID == PillarId.COMBAT  # combat.py:43 _rec()


def test_economy_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert EconomyScorer(scoring_weights).PILLAR_ID == PillarId.ECONOMY  # economy.py:54 _rec()


def test_faction_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert FactionScorer(scoring_weights).PILLAR_ID == PillarId.FACTION  # faction.py:45 _rec()


def test_information_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert InformationScorer(scoring_weights).PILLAR_ID == PillarId.INFORMATION  # information.py:46 _rec()


def test_narrative_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert NarrativeScorer(scoring_weights).PILLAR_ID == PillarId.NARRATIVE  # narrative.py:52 _rec()


def test_progression_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert ProgressionScorer(scoring_weights).PILLAR_ID == PillarId.PROGRESSION  # progression.py:44 _rec()


def test_social_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert SocialScorer(scoring_weights).PILLAR_ID == PillarId.SOCIAL  # social.py:49 _rec()


def test_world_dynamics_scorer_pillar_id(scoring_weights: ScoringWeights) -> None:
    assert WorldDynamicsScorer(scoring_weights).PILLAR_ID == PillarId.WORLD  # world_dynamics.py:56 _rec()


def test_scorer_weights_view_matches_own_pillar_declared_value(scoring_weights: ScoringWeights) -> None:
    cognition = CognitionScorer(scoring_weights)
    information = InformationScorer(scoring_weights)
    assert cognition.weights["belief_active"] == scoring_weights.for_pillar("COGNITION")["belief_active"]
    assert information.weights["belief_active"] == scoring_weights.for_pillar("INFORMATION")["belief_active"]
    assert cognition.weights["belief_active"] != information.weights["belief_active"]


def test_scorer_weights_int_param_forwarding_is_byte_identical(scoring_weights: ScoringWeights) -> None:
    cognition = CognitionScorer(scoring_weights)
    assert cognition.weights.int_param("stasis_gate_ticks") == scoring_weights.int_param("stasis_gate_ticks") == 5
