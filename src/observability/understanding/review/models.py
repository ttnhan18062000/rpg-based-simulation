"""Human Review Workflow models."""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class ReviewLabel(str, Enum):
    CONFIRMED_BUG = "CONFIRMED_BUG"
    BALANCE_ISSUE = "BALANCE_ISSUE"
    EXPECTED_BEHAVIOR = "EXPECTED_BEHAVIOR"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"
    DUPLICATE = "DUPLICATE"
    IGNORED_FOR_NOW = "IGNORED_FOR_NOW"


@dataclass
class FindingReview:
    run_id: str
    finding_id: str
    label: ReviewLabel
    review_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    comment: str = ""
    reviewed_by: str = "unknown"
    reviewed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_id": self.review_id,
            "run_id": self.run_id,
            "finding_id": self.finding_id,
            "label": self.label.value,
            "comment": self.comment,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "FindingReview":
        return FindingReview(
            review_id=d["review_id"],
            run_id=d["run_id"],
            finding_id=d["finding_id"],
            label=ReviewLabel(d["label"]),
            comment=d.get("comment", ""),
            reviewed_by=d.get("reviewed_by", "unknown"),
            reviewed_at=d.get("reviewed_at", ""),
        )
