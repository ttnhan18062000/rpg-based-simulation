"""
AnalyzerQualityReporter — computes per-rule quality metrics from
DomainFindings + FindingReviews.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.observability.understanding.quality.models import (
    AnalyzerQualityReport, RuleQualityMetrics
)
from src.observability.understanding.review.models import FindingReview, ReviewLabel


class AnalyzerQualityReporter:
    """
    Aggregates finding + review data across one or many run directories
    to produce per-rule quality metrics.
    """

    def compute(
        self,
        findings: List[Dict[str, Any]],  # list of finding dicts with "domain" or "rule_name"
        reviews: List[FindingReview],
    ) -> AnalyzerQualityReport:
        """
        Build quality metrics from a set of findings and their reviews.

        findings: list of dicts with at least {"finding_id": ..., "domain": ...}
                  or {"finding_id": ..., "rule_name": ...}
        reviews: list of FindingReview objects from ReviewStore
        """
        # Index reviews by finding_id
        reviews_by_finding: Dict[str, List[FindingReview]] = defaultdict(list)
        for r in reviews:
            reviews_by_finding[r.finding_id].append(r)

        # Group findings by rule / domain
        rule_data: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            "total": 0, "reviewed": 0, "confirmed_bugs": 0,
            "false_positives": 0, "expected_behavior": 0, "balance_issues": 0, "unreviewed": 0
        })

        for finding in findings:
            # Support both domain-based findings and rule-name-based anomalies
            rule_key = (
                finding.get("rule_name")
                or finding.get("domain")
                or "unknown"
            )
            fid = finding.get("finding_id") or finding.get("anomaly_id", "")
            rule_data[rule_key]["total"] += 1

            finding_reviews = reviews_by_finding.get(fid, [])
            if not finding_reviews:
                rule_data[rule_key]["unreviewed"] += 1
            else:
                rule_data[rule_key]["reviewed"] += 1
                # Use the most recent review label
                latest = sorted(finding_reviews, key=lambda r: r.reviewed_at)[-1]
                label = latest.label
                if label == ReviewLabel.CONFIRMED_BUG:
                    rule_data[rule_key]["confirmed_bugs"] += 1
                elif label == ReviewLabel.FALSE_POSITIVE:
                    rule_data[rule_key]["false_positives"] += 1
                elif label == ReviewLabel.EXPECTED_BEHAVIOR:
                    rule_data[rule_key]["expected_behavior"] += 1
                elif label == ReviewLabel.BALANCE_ISSUE:
                    rule_data[rule_key]["balance_issues"] += 1

        metrics_list = [
            RuleQualityMetrics(
                rule_name=rule,
                total_findings=d["total"],
                reviewed=d["reviewed"],
                confirmed_bugs=d["confirmed_bugs"],
                false_positives=d["false_positives"],
                expected_behavior=d["expected_behavior"],
                balance_issues=d["balance_issues"],
                unreviewed=d["unreviewed"],
            )
            for rule, d in sorted(rule_data.items())
        ]

        return AnalyzerQualityReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            rule_metrics=metrics_list,
        )
