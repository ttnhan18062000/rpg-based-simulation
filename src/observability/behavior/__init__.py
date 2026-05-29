"""
Behavior Observability Package.

Provides semantic behavior event modeling, normalization, and worker
for async/post-run processing outside the hot path.
"""
from src.observability.behavior.behavior_event import BehaviorEvent, BEHAVIOR_CATEGORIES
from src.observability.behavior.normalization_context import BehaviorNormalizationContext
from src.observability.behavior.normalizer import BehaviorEventNormalizer
from src.observability.behavior.worker import BehaviorWorker, WorkerHealth
from src.observability.behavior.behavior_metric_window import BehaviorMetricWindow
from src.observability.behavior.metrics_aggregator import BehaviorMetricsAggregator
from src.observability.behavior.behavior_episode import BehaviorEpisode
from src.observability.behavior.behavior_timeline_store import EntityBehaviorTimeline, BehaviorTimelineStore
from src.observability.behavior.episode_detector import EpisodeDetector
from src.observability.behavior.behavior_finding import BehaviorFinding
from src.observability.behavior.pattern_detectors import (
    RepeatedFailureLoopDetector,
    BehaviorChangeProofDetector,
    HiddenKnowledgeSuspicionDetector,
)
from src.observability.behavior.behavior_insight import BehaviorInsight, BehaviorInsightGenerator
from src.observability.behavior.behavior_scorecard import EntityBehaviorScorecard, RunBehaviorScorecard
from src.observability.behavior.cohort_analyzer import CohortAnalyzer
from src.observability.behavior.run_comparison import RunBehaviorComparison

__all__ = [
    "BehaviorEvent",
    "BEHAVIOR_CATEGORIES",
    "BehaviorNormalizationContext",
    "BehaviorEventNormalizer",
    "BehaviorWorker",
    "WorkerHealth",
    "BehaviorMetricWindow",
    "BehaviorMetricsAggregator",
    "BehaviorEpisode",
    "EntityBehaviorTimeline",
    "BehaviorTimelineStore",
    "EpisodeDetector",
    "BehaviorFinding",
    "BehaviorInsight",
    "RepeatedFailureLoopDetector",
    "BehaviorChangeProofDetector",
    "HiddenKnowledgeSuspicionDetector",
    "BehaviorInsightGenerator",
    "EntityBehaviorScorecard",
    "RunBehaviorScorecard",
    "CohortAnalyzer",
    "RunBehaviorComparison",
]
