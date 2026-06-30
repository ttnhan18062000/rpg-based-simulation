from src.simulation_quality.scorers.base import PillarScorer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.simulation_quality.weights import ScoringWeights

__all__ = ["PillarScorer", "build_all_scorers"]


def build_all_scorers(weights: "ScoringWeights") -> list:
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

    return [
        AgencyScorer(weights), CognitionScorer(weights), CombatScorer(weights),
        EconomyScorer(weights), FactionScorer(weights), InformationScorer(weights),
        NarrativeScorer(weights), ProgressionScorer(weights), SocialScorer(weights),
        WorldDynamicsScorer(weights),
    ]
