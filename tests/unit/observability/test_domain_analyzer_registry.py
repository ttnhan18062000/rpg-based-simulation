"""
Unit tests — DomainAnalyzerRegistry

Validates:
- Registry runs multiple analyzers in order
- Failed analyzer is reported without crashing others
- Missing signals produce SKIPPED_MISSING_SIGNAL
- Analyzer runtime is tracked
"""
import pytest

from src.observability.understanding.context import AnalysisContext
from src.observability.understanding.domain.base import (
    DomainAnalyzer, DomainAnalysisResult, DomainAnalysisStatus,
    DomainFinding, DomainAnalyzerRegistry, ConfidenceLevel
)


# ── Stub analyzers for testing ────────────────────────────────────────────────

class _AlwaysPassAnalyzer(DomainAnalyzer):
    domain_id = "always_pass"
    required_event_categories = []

    def analyze(self, ctx):
        return DomainAnalysisResult(
            domain_id=self.domain_id,
            status=DomainAnalysisStatus.PASSED
        )


class _FindingAnalyzer(DomainAnalyzer):
    domain_id = "always_finds"
    required_event_categories = []

    def analyze(self, ctx):
        finding = DomainFinding(
            domain=self.domain_id,
            severity="WARNING",
            title="Test Finding",
            summary="A test finding.",
            confidence=ConfidenceLevel.LOW,
        )
        return DomainAnalysisResult(
            domain_id=self.domain_id,
            status=DomainAnalysisStatus.FINDINGS_FOUND,
            findings=[finding]
        )


class _CrashingAnalyzer(DomainAnalyzer):
    domain_id = "always_crashes"
    required_event_categories = []

    def analyze(self, ctx):
        raise RuntimeError("Simulated analyzer crash")


class _MissingSignalAnalyzer(DomainAnalyzer):
    domain_id = "needs_combat"
    required_event_categories = ["combat"]

    def analyze(self, ctx):
        if not ctx.has_events("combat"):
            return self._missing_signal_result("No combat events.")
        return DomainAnalysisResult(
            domain_id=self.domain_id,
            status=DomainAnalysisStatus.PASSED
        )


def _empty_ctx():
    return AnalysisContext(run_id="test-run", scenario_type="mixed_sandbox")


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestDomainAnalyzerRegistry:

    def test_registry_runs_all_analyzers(self):
        reg = DomainAnalyzerRegistry()
        reg.register(_AlwaysPassAnalyzer())
        reg.register(_FindingAnalyzer())

        results = reg.run_all(_empty_ctx())
        assert len(results) == 2
        assert results[0].domain_id == "always_pass"
        assert results[1].domain_id == "always_finds"

    def test_registry_run_order_is_stable(self):
        reg = DomainAnalyzerRegistry()
        reg.register(_AlwaysPassAnalyzer())
        reg.register(_MissingSignalAnalyzer())
        reg.register(_FindingAnalyzer())

        results = reg.run_all(_empty_ctx())
        domain_ids = [r.domain_id for r in results]
        assert domain_ids == ["always_pass", "needs_combat", "always_finds"]

    def test_crashed_analyzer_does_not_crash_registry(self):
        reg = DomainAnalyzerRegistry()
        reg.register(_AlwaysPassAnalyzer())
        reg.register(_CrashingAnalyzer())
        reg.register(_FindingAnalyzer())

        results = reg.run_all(_empty_ctx())
        assert len(results) == 3
        assert results[1].status == DomainAnalysisStatus.FAILED
        assert "Simulated analyzer crash" in results[1].error_message
        # Other analyzers still ran
        assert results[0].status == DomainAnalysisStatus.PASSED
        assert results[2].status == DomainAnalysisStatus.FINDINGS_FOUND

    def test_missing_signal_produces_skipped_status(self):
        reg = DomainAnalyzerRegistry()
        reg.register(_MissingSignalAnalyzer())

        results = reg.run_all(_empty_ctx())
        assert results[0].status == DomainAnalysisStatus.SKIPPED_MISSING_SIGNAL
        assert results[0].skipped_reason == "No combat events."

    def test_analyzer_runtime_is_tracked(self):
        reg = DomainAnalyzerRegistry()
        reg.register(_AlwaysPassAnalyzer())

        results = reg.run_all(_empty_ctx())
        assert results[0].analyzer_runtime_ms >= 0.0

    def test_empty_registry_returns_empty_results(self):
        reg = DomainAnalyzerRegistry()
        results = reg.run_all(_empty_ctx())
        assert results == []

    def test_findings_are_collected_in_result(self):
        reg = DomainAnalyzerRegistry()
        reg.register(_FindingAnalyzer())

        results = reg.run_all(_empty_ctx())
        assert len(results[0].findings) == 1
        assert results[0].findings[0].title == "Test Finding"

    def test_result_to_dict_serializes(self):
        reg = DomainAnalyzerRegistry()
        reg.register(_FindingAnalyzer())

        results = reg.run_all(_empty_ctx())
        d = results[0].to_dict()
        assert d["domain_id"] == "always_finds"
        assert d["status"] == "FINDINGS_FOUND"
        assert d["findings_count"] == 1

    def test_default_registry_has_four_analyzers(self):
        reg = DomainAnalyzerRegistry.default()
        ctx = _empty_ctx()
        results = reg.run_all(ctx)
        domain_ids = {r.domain_id for r in results}
        assert "movement" in domain_ids
        assert "economy" in domain_ids
        assert "quest" in domain_ids
        assert "runtime" in domain_ids
