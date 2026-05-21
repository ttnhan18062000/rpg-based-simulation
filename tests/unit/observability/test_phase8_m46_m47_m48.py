"""
Unit tests — StoryDetector and story patterns (M46)
Unit tests — FindingReview + ReviewStore (M47)
Unit tests — AnalyzerQualityReporter + BaselineEvolutionPolicy (M48)
"""
import json
import os
import pytest
import tempfile

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.stories.detector import StoryDetector
from src.observability.understanding.stories.patterns import (
    ResourceCrisis, QuestHero, UnexpectedSurvivor
)
from src.observability.understanding.review.models import ReviewLabel, FindingReview
from src.observability.understanding.review.store import ReviewStore
from src.observability.understanding.quality.models import BaselineStatus, BaselineStatusRecord
from src.observability.understanding.quality.quality_report import AnalyzerQualityReporter
from src.observability.understanding.quality.baseline_evolution import (
    BaselineEvolutionPolicy, BaselinePromotionWorkflow, PromotionCriteria
)
from src.observability.understanding.quality.stale_detector import StaleBaselineDetector
from src.observability.events import SimulationEvent


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_event(category, event_type, tick=10, entity_id=None, payload=None):
    return SimulationEvent(
        event_type=event_type,
        event_category=category,
        tick=tick,
        source_system="test",
        message="test",
        entity_id=entity_id,
        payload=payload or {},
        run_id="test"
    )


def _ctx(**kwargs):
    return AnalysisContext(run_id="test", scenario_type="mixed_sandbox", **kwargs)


# ── M46 Story Detector ────────────────────────────────────────────────────────

class TestStoryDetector:

    def test_resource_crisis_detected_on_long_gap(self):
        events = [
            _make_event("economy", "gold_transaction", tick=5),
            _make_event("economy", "gold_transaction", tick=10),
            _make_event("economy", "gold_transaction", tick=200),
        ]
        ctx = _ctx(events=events)
        pattern = ResourceCrisis()
        stories = pattern.detect(ctx)
        assert len(stories) == 1
        assert "Crisis" in stories[0].title

    def test_quest_hero_detected(self):
        events = [
            _make_event("quest", "quest_event", tick=i, entity_id=99,
                        payload={"quest_id": f"q{i}", "status": "completed"})
            for i in range(1, 6)
        ] + [
            _make_event("quest", "quest_event", tick=i, entity_id=1,
                        payload={"quest_id": f"q{i+100}", "status": "completed"})
            for i in range(1, 2)
        ]
        ctx = _ctx(events=events)
        stories = QuestHero().detect(ctx)
        assert len(stories) >= 1
        assert stories[0].entities == [99]

    def test_clean_run_produces_no_stories(self):
        events = [_make_event("movement", "movement", tick=i) for i in range(1, 10)]
        ctx = _ctx(events=events)
        detector = StoryDetector()
        stories = detector.detect(ctx)
        assert stories == []

    def test_crashed_pattern_does_not_crash_detector(self):
        from src.observability.understanding.stories.models import StoryPattern

        class _Crash(StoryPattern):
            pattern_id = "crash"
            def detect(self, ctx):
                raise RuntimeError("crash!")

        ctx = _ctx()
        detector = StoryDetector(patterns=[_Crash()])
        stories = detector.detect(ctx)
        assert stories == []

    def test_stories_sorted_by_interestingness(self):
        events = [
            _make_event("economy", "gold_transaction", tick=5),
            _make_event("economy", "gold_transaction", tick=10),
            _make_event("economy", "gold_transaction", tick=200),
        ]
        ctx = _ctx(events=events)
        detector = StoryDetector()
        stories = detector.detect(ctx)
        if len(stories) >= 2:
            scores = [s.interestingness_score for s in stories]
            assert scores == sorted(scores, reverse=True)

    def test_story_to_dict_serializes(self):
        events = [
            _make_event("economy", "gold_transaction", tick=5),
            _make_event("economy", "gold_transaction", tick=200),
        ]
        ctx = _ctx(events=events)
        stories = ResourceCrisis().detect(ctx)
        if stories:
            d = stories[0].to_dict()
            assert "story_id" in d
            assert "interestingness_score" in d


# ── M47 Finding Review ────────────────────────────────────────────────────────

class TestFindingReview:

    def test_review_label_enum_values(self):
        assert ReviewLabel.CONFIRMED_BUG.value == "CONFIRMED_BUG"
        assert ReviewLabel.FALSE_POSITIVE.value == "FALSE_POSITIVE"

    def test_finding_review_to_dict(self):
        review = FindingReview(
            run_id="run-001",
            finding_id="abc123",
            label=ReviewLabel.CONFIRMED_BUG,
            comment="Definitely a bug",
            reviewed_by="dev1"
        )
        d = review.to_dict()
        assert d["label"] == "CONFIRMED_BUG"
        assert d["finding_id"] == "abc123"
        assert d["reviewed_by"] == "dev1"

    def test_finding_review_from_dict_roundtrip(self):
        review = FindingReview(
            run_id="run-001",
            finding_id="abc123",
            label=ReviewLabel.FALSE_POSITIVE,
            comment="Not a real issue",
        )
        d = review.to_dict()
        restored = FindingReview.from_dict(d)
        assert restored.label == ReviewLabel.FALSE_POSITIVE
        assert restored.finding_id == "abc123"


class TestReviewStore:

    def test_add_and_list_reviews(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ReviewStore(tmpdir)
            r1 = FindingReview(run_id="r1", finding_id="f1", label=ReviewLabel.CONFIRMED_BUG)
            r2 = FindingReview(run_id="r1", finding_id="f2", label=ReviewLabel.FALSE_POSITIVE)
            store.add(r1)
            store.add(r2)
            all_reviews = store.list_all()
            assert len(all_reviews) == 2

    def test_get_by_finding(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ReviewStore(tmpdir)
            store.add(FindingReview(run_id="r1", finding_id="f1", label=ReviewLabel.CONFIRMED_BUG))
            store.add(FindingReview(run_id="r1", finding_id="f2", label=ReviewLabel.FALSE_POSITIVE))
            results = store.get_by_finding("f1")
            assert len(results) == 1
            assert results[0].finding_id == "f1"

    def test_update_label(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ReviewStore(tmpdir)
            r = FindingReview(run_id="r1", finding_id="f1", label=ReviewLabel.NEEDS_MORE_DATA)
            store.add(r)
            updated = store.update_label(r.review_id, ReviewLabel.CONFIRMED_BUG, comment="now confirmed")
            assert updated is True
            all_reviews = store.list_all()
            assert all_reviews[0].label == ReviewLabel.CONFIRMED_BUG

    def test_empty_store_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ReviewStore(tmpdir)
            assert store.list_all() == []

    def test_label_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ReviewStore(tmpdir)
            store.add(FindingReview(run_id="r1", finding_id="f1", label=ReviewLabel.CONFIRMED_BUG))
            store.add(FindingReview(run_id="r1", finding_id="f2", label=ReviewLabel.CONFIRMED_BUG))
            store.add(FindingReview(run_id="r1", finding_id="f3", label=ReviewLabel.FALSE_POSITIVE))
            summary = store.label_summary()
            assert summary["CONFIRMED_BUG"] == 2
            assert summary["FALSE_POSITIVE"] == 1


# ── M48 Quality + Baseline Evolution ─────────────────────────────────────────

class TestAnalyzerQualityReporter:

    def test_all_unreviewed(self):
        findings = [
            {"finding_id": f"f{i}", "domain": "movement"}
            for i in range(5)
        ]
        reporter = AnalyzerQualityReporter()
        report = reporter.compute(findings, reviews=[])
        assert report.rule_metrics[0].total_findings == 5
        assert report.rule_metrics[0].unreviewed == 5
        assert report.rule_metrics[0].unreviewed_rate == 1.0

    def test_false_positive_rate_computed(self):
        findings = [{"finding_id": f"f{i}", "domain": "economy"} for i in range(4)]
        reviews = [
            FindingReview(run_id="r1", finding_id=f"f{i}", label=ReviewLabel.FALSE_POSITIVE)
            for i in range(3)
        ] + [
            FindingReview(run_id="r1", finding_id="f3", label=ReviewLabel.CONFIRMED_BUG)
        ]
        reporter = AnalyzerQualityReporter()
        report = reporter.compute(findings, reviews)
        m = report.rule_metrics[0]
        assert m.false_positives == 3
        assert m.confirmed_bugs == 1
        assert abs(m.false_positive_rate - 0.75) < 0.01

    def test_noisy_rule_identified(self):
        findings = [{"finding_id": f"f{i}", "domain": "runtime"} for i in range(6)]
        reviews = [
            FindingReview(run_id="r1", finding_id=f"f{i}", label=ReviewLabel.FALSE_POSITIVE)
            for i in range(6)
        ]
        reporter = AnalyzerQualityReporter()
        report = reporter.compute(findings, reviews)
        assert len(report.noisy_rules()) == 1

    def test_report_to_dict(self):
        reporter = AnalyzerQualityReporter()
        report = reporter.compute([], [])
        d = report.to_dict()
        assert "generated_at" in d
        assert "rule_metrics" in d


class TestBaselineEvolutionPolicy:

    def test_validates_sufficient_runs(self):
        policy = BaselineEvolutionPolicy(PromotionCriteria(min_accepted_run_count=5))
        baseline = {"accepted_run_count": 3, "is_weak_baseline": True, "metrics": {}}
        result = policy.validate_for_promotion(baseline)
        assert result.passed is False
        assert any("Insufficient" in r for r in result.reasons)

    def test_validates_no_hard_law_violations(self):
        policy = BaselineEvolutionPolicy()
        baseline = {
            "accepted_run_count": 10,
            "is_weak_baseline": False,
            "metrics": {
                "hard_law_violation_count": {"max": 2.0, "min": 0.0, "mean": 0.2}
            }
        }
        result = policy.validate_for_promotion(baseline)
        assert result.passed is False
        assert any("hard law" in r.lower() for r in result.reasons)

    def test_valid_baseline_passes(self):
        policy = BaselineEvolutionPolicy()
        baseline = {
            "accepted_run_count": 10,
            "is_weak_baseline": False,
            "metrics": {
                "hard_law_violation_count": {"max": 0.0, "min": 0.0, "mean": 0.0},
                "health_score": {"p10": 75.0, "min": 70.0, "mean": 85.0}
            }
        }
        result = policy.validate_for_promotion(baseline)
        assert result.passed is True


class TestBaselinePromotionWorkflow:

    def test_promote_candidate_to_active(self):
        record = BaselineStatusRecord(
            baseline_id="b1", scenario_type="resource_economy",
            status=BaselineStatus.CANDIDATE
        )
        workflow = BaselinePromotionWorkflow()
        updated, success = workflow.promote(record, reviewer="dev1")
        assert success is True
        assert updated.status == BaselineStatus.ACTIVE
        assert updated.reviewer == "dev1"
        assert updated.promotion_timestamp is not None

    def test_cannot_promote_non_candidate(self):
        record = BaselineStatusRecord(
            baseline_id="b1", scenario_type="resource_economy",
            status=BaselineStatus.ACTIVE
        )
        _, success = BaselinePromotionWorkflow().promote(record)
        assert success is False

    def test_deprecate_active_baseline(self):
        record = BaselineStatusRecord(
            baseline_id="b1", scenario_type="resource_economy",
            status=BaselineStatus.ACTIVE
        )
        updated, success = BaselinePromotionWorkflow().deprecate(record, reason="engine updated")
        assert success is True
        assert updated.status == BaselineStatus.DEPRECATED
        assert "engine updated" in updated.deprecation_reason

    def test_cannot_deprecate_candidate(self):
        record = BaselineStatusRecord(
            baseline_id="b1", scenario_type="resource_economy",
            status=BaselineStatus.CANDIDATE
        )
        _, success = BaselinePromotionWorkflow().deprecate(record, reason="n/a")
        assert success is False


class TestStaleBaselineDetector:

    def test_detects_schema_version_mismatch(self):
        detector = StaleBaselineDetector()
        result = detector.check(
            {"artifact_schema_version": "baseline_v1"},
            {"artifact_schema_version": "baseline_v2"}
        )
        assert result.is_stale is True
        assert any(w.field_name == "artifact_schema_version" for w in result.warnings)

    def test_detects_scenario_type_mismatch(self):
        detector = StaleBaselineDetector()
        result = detector.check(
            {"scenario_type": "resource_economy"},
            {"scenario_type": "combat_heavy"}
        )
        assert result.is_stale is True

    def test_no_staleness_on_matching_metadata(self):
        detector = StaleBaselineDetector()
        meta = {
            "artifact_schema_version": "baseline_v1",
            "scenario_type": "resource_economy",
        }
        result = detector.check(meta, meta)
        assert result.is_stale is False

    def test_result_to_dict(self):
        detector = StaleBaselineDetector()
        result = detector.check({"artifact_schema_version": "v1"}, {"artifact_schema_version": "v2"})
        d = result.to_dict()
        assert "is_stale" in d
        assert "warnings" in d
