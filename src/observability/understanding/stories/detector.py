"""StoryDetector — runs all patterns, catches errors per pattern."""
from __future__ import annotations
import logging
from typing import List, Optional

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.stories.models import StoryCandidate, StoryPattern
from src.observability.understanding.stories.patterns import ALL_STORY_PATTERNS

logger = logging.getLogger(__name__)


class StoryDetector:
    """
    Runs all story patterns and returns candidates sorted by interestingness.
    A failing pattern is logged and skipped — does not crash the detector.
    Stories do NOT affect the run health score.
    """

    def __init__(self, patterns: Optional[List[StoryPattern]] = None) -> None:
        self._patterns = patterns if patterns is not None else ALL_STORY_PATTERNS

    def detect(self, ctx: AnalysisContext) -> List[StoryCandidate]:
        candidates: List[StoryCandidate] = []
        for pattern in self._patterns:
            try:
                results = pattern.detect(ctx)
                candidates.extend(results)
            except Exception as exc:
                logger.error(f"StoryPattern '{pattern.pattern_id}' failed: {exc}", exc_info=True)

        return sorted(candidates, key=lambda c: c.interestingness_score, reverse=True)
