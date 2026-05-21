"""
ReviewStore — persists finding reviews as JSONL in the run artifact directory.
"""
from __future__ import annotations
import json
import logging
import os
from typing import Dict, List, Optional

from src.observability.understanding.review.models import FindingReview, ReviewLabel

logger = logging.getLogger(__name__)

REVIEW_FILENAME = "finding_reviews.jsonl"


class ReviewStore:
    """
    Reads and writes finding reviews to `finding_reviews.jsonl` inside a run directory.

    Each line is a JSON-encoded FindingReview dict.
    On write, new reviews are appended. On update, the whole file is rewritten.
    """

    def __init__(self, run_dir: str) -> None:
        self.run_dir = run_dir
        self._path = os.path.join(run_dir, REVIEW_FILENAME)

    def add(self, review: FindingReview) -> None:
        """Append a new review to the store."""
        os.makedirs(self.run_dir, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(review.to_dict()) + "\n")

    def list_all(self) -> List[FindingReview]:
        """Return all reviews in the store."""
        if not os.path.exists(self._path):
            return []
        reviews = []
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        reviews.append(FindingReview.from_dict(json.loads(line)))
                    except Exception as e:
                        logger.warning(f"Skipping malformed review line: {e}")
        return reviews

    def get_by_finding(self, finding_id: str) -> List[FindingReview]:
        """Return all reviews for a specific finding_id."""
        return [r for r in self.list_all() if r.finding_id == finding_id]

    def update_label(self, review_id: str, new_label: ReviewLabel, comment: str = "") -> bool:
        """
        Update the label (and optionally comment) for an existing review.
        Rewrites the entire file. Returns True if the review was found.
        """
        all_reviews = self.list_all()
        updated = False
        for r in all_reviews:
            if r.review_id == review_id:
                r.label = new_label
                if comment:
                    r.comment = comment
                updated = True
        if updated:
            os.makedirs(self.run_dir, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                for r in all_reviews:
                    f.write(json.dumps(r.to_dict()) + "\n")
        return updated

    def label_summary(self) -> Dict[str, int]:
        """Return a summary dict of label → count."""
        summary: Dict[str, int] = {}
        for r in self.list_all():
            summary[r.label.value] = summary.get(r.label.value, 0) + 1
        return summary
