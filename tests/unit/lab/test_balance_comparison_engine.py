# Compliance IDs: BALANCE-TEST-001, BALANCE-TEST-002, BALANCE-TEST-003
import pytest
from pathlib import Path
import tempfile
import json
from src.lab.comparison import BalanceComparisonEngine, BalanceComparisonReport
from src.lab.metamorphic import MetamorphicComparisonResult


def test_variant_with_better_health_score_is_marked_improved():
    """Verify that a variant with a strictly better health score and no regressions is marked IMPROVED."""
    base = {
        "health_score": 90.0,
        "critical_count": 2,
        "hard_law_violations": 0
    }
    compared = {
        "health_score": 95.0,  # improved
        "critical_count": 1,   # improved
        "hard_law_violations": 0
    }

    report = BalanceComparisonEngine.compare(base, compared)
    assert report.status == "IMPROVED"
    assert report.evidence["health_score"]["shift"] == 5.0
    assert report.evidence["critical_count"]["shift"] == -1.0


def test_variant_with_hard_law_violation_is_marked_regressed():
    """Verify that a variant introducing a hard law violation is strictly classified as REGRESSED."""
    base = {
        "health_score": 90.0,
        "hard_law_violations": 0
    }
    compared = {
        "health_score": 95.0,  # health score improved, BUT...
        "hard_law_violations": 1  # hard law violation introduced!
    }

    report = BalanceComparisonEngine.compare(base, compared)
    assert report.status == "REGRESSED"


def test_mixed_metrics_produce_mixed():
    """Verify that a variant with a mix of improved and regressed dimensions produces MIXED status."""
    base = {
        "health_score": 90.0,
        "stuck_entity_ratio": 0.05
    }
    compared = {
        "health_score": 95.0,           # improved (+5.0)
        "stuck_entity_ratio": 0.15       # worsened (+0.10 stuck ratio is bad)
    }

    report = BalanceComparisonEngine.compare(base, compared)
    assert report.status == "MIXED"


def test_missing_data_produces_insufficient_data():
    """Verify that missing crucial metric data produces INSUFFICIENT_DATA."""
    # missing health_score completely
    base = {
        "stuck_entity_ratio": 0.05
    }
    compared = {
        "stuck_entity_ratio": 0.05
    }

    report = BalanceComparisonEngine.compare(base, compared)
    assert report.status == "INSUFFICIENT_DATA"


def test_comparison_includes_evidence():
    """Verify that the balance comparison report maps and reports the full structured evidence."""
    base = {
        "health_score": 90.0,
        "resource_production_rate": 10.0
    }
    compared = {
        "health_score": 92.5,
        "resource_production_rate": 12.0
    }

    report = BalanceComparisonEngine.compare(base, compared)
    assert "health_score" in report.evidence
    assert "resource_production_rate" in report.evidence
    assert report.evidence["health_score"]["baseline"] == 90.0
    assert report.evidence["health_score"]["compared"] == 92.5
    assert report.evidence["resource_production_rate"]["shift"] == 2.0


def test_comparison_does_not_claim_root_cause():
    """Verify that the explanation strictly avoids causal claims and maintains scientific humility."""
    base = {
        "health_score": 90.0,
        "hard_law_violations": 0
    }
    compared = {
        "health_score": 95.0,
        "hard_law_violations": 0
    }

    report = BalanceComparisonEngine.compare(base, compared)
    explanation = report.explanation

    # Assert that causal-certainty phrasing is absent
    causal_certainties = ["caused by", "proves that", "directly resulted from", "is the root cause of", "causation"]
    for phrase in causal_certainties:
        assert phrase not in explanation.lower()

    # Assert that correlative phrasing is present
    assert "correlates with" in explanation.lower() or "associated with" in explanation.lower()


def test_comparison_fails_when_associated_metamorphic_rule_fails():
    """Verify that a failed associated metamorphic validation rule forces a REGRESSED status."""
    base = {
        "health_score": 90.0,
        "resource_production_rate": 10.0
    }
    compared = {
        "health_score": 92.0,
        "resource_production_rate": 10.0
    }

    # A failed metamorphic rule
    failed_rule = MetamorphicComparisonResult(
        rule_id="rule_meta_1",
        status="FAILED",
        weak_evidence=False,
        baseline_value=10.0,
        compared_value=8.0,
        message="Failed expected condition."
    )

    report = BalanceComparisonEngine.compare(base, compared, metamorphic_results=[failed_rule])
    assert report.status == "REGRESSED"
    assert report.metamorphic_summary["failed"] == 1


def test_write_reports_creates_files():
    """Verify that write_reports correctly creates balance_comparison.json and .md files."""
    base = {
        "health_score": 90.0,
        "hard_law_violations": 0
    }
    compared = {
        "health_score": 95.0,
        "hard_law_violations": 0
    }

    report = BalanceComparisonEngine.compare(base, compared)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        BalanceComparisonEngine.write_reports(tmp_path, report)

        json_file = tmp_path / "balance_comparison.json"
        md_file = tmp_path / "balance_comparison.md"

        assert json_file.is_file()
        assert md_file.is_file()

        # Check JSON parsing
        with open(json_file, "r") as f:
            data = json.load(f)
            assert data["status"] == "IMPROVED"

        # Check MD content contains the badge and explanation
        with open(md_file, "r") as f:
            md_text = f.read()
            assert "IMPROVED" in md_text
            assert "Scorecard" in md_text
