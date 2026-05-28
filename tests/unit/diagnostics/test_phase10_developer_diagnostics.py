# TDD tests for DeveloperDiagnostics
import pytest
from src.domains.optimization.diagnostics import DeveloperDiagnostics, DiagnosticIssue

def test_diagnostics_report_budget_skip():
    diag = DeveloperDiagnostics()
    diag.record_issue(DiagnosticIssue(
        category="budget_skip",
        entity_id=12,
        message="Phase self_model skipped due to budget",
        evidence_event_ids=["ev_1001"]
    ))
    report = diag.generate_report()
    assert len(report["issues"]) == 1
    assert report["issues"][0]["category"] == "budget_skip"
    assert "ev_1001" in report["issues"][0]["evidence_event_ids"]

def test_diagnostics_report_no_provider_options():
    diag = DeveloperDiagnostics()
    diag.record_issue(DiagnosticIssue(
        category="no_provider_options",
        entity_id=12,
        message="Resource provider returned empty",
        evidence_event_ids=["ev_1034"]
    ))
    report = diag.generate_report()
    assert report["issues"][0]["category"] == "no_provider_options"

def test_diagnostics_report_repeated_blocker_loop():
    diag = DeveloperDiagnostics()
    diag.record_issue(DiagnosticIssue(
        category="repeated_blocker",
        entity_id=12,
        message="Actor repeatedly selected blocked route",
        evidence_event_ids=["ev_1050"]
    ))
    report = diag.generate_report()
    assert "repeated_blocker" in report["issues"][0]["category"]

def test_diagnostics_report_hidden_knowledge_suspicion():
    diag = DeveloperDiagnostics()
    diag.record_issue(DiagnosticIssue(
        category="hidden_knowledge_suspicion",
        entity_id=12,
        message="Suspicion fact evicted by memory manager",
        evidence_event_ids=["ev_1090"]
    ))
    report = diag.generate_report()
    assert report["issues"][0]["category"] == "hidden_knowledge_suspicion"

def test_diagnostics_include_evidence_event_ids():
    diag = DeveloperDiagnostics()
    diag.record_issue(DiagnosticIssue(
        category="trace_dropped",
        entity_id=1,
        message="Dropped 5 low-severity traces",
        evidence_event_ids=["ev_trace_1", "ev_trace_2"]
    ))
    report = diag.generate_report()
    assert len(report["issues"][0]["evidence_event_ids"]) == 2
