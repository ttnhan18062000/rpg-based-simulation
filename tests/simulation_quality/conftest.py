from __future__ import annotations
import os
import pytest

from src.simulation_quality.pillars import PillarId
from src.simulation_quality.score_record import ScoreRecord
from src.simulation_quality.weights import ScoringWeights
from src.simulation_quality.pillar_accumulator import PillarAccumulator


_WEIGHTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../config/simulation_quality/scoring_weights.yaml",
)
_GRADE_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../config/simulation_quality/grade_thresholds.yaml",
)
_DETECTION_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../config/simulation_quality/detection_params.yaml",
)


@pytest.fixture(scope="session")
def scoring_weights() -> ScoringWeights:
    return ScoringWeights.load(
        weights_path=_WEIGHTS_PATH,
        grade_path=_GRADE_PATH,
        detection_path=_DETECTION_PATH,
        profile="default",
    )


@pytest.fixture
def sample_score_record() -> ScoreRecord:
    return ScoreRecord(
        tick=10,
        event_id="test-event-001",
        pillar=PillarId.ECONOMY,
        delta=3.0,
        reason="resource_harvested",
        event_type="resource_harvested",
        entity_id=1,
        region_id="hometown",
        tags=("harvest_active",),
    )


@pytest.fixture
def managed_accumulator(scoring_weights: ScoringWeights):
    acc = PillarAccumulator(
        pillar_id=PillarId.ECONOMY,
        weights=scoring_weights,
    )
    yield acc
