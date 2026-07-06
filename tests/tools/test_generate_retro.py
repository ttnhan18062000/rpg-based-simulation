"""Targeted tests for tools/agent-monitoring/generate_retro.py's reason-code section
(TCK-20260706-MONITORING-REASON-CODE, extended by TCK-20260706-SCOPE-TAG-REGISTRY-CHECK and
TCK-20260706-CREATE-TICKETS-TAG-CHECK). Not full coverage of the pre-existing script (which had no
test file before the first of these tickets) — scoped to the behavior these tickets changed.
"""

import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from generate_retro import generate  # noqa: E402

_BASE_RUN = {
    "run_id": "TCK-FAKE",
    "start_ts": "2026-07-06T00:00:00Z",
    "end_ts": "2026-07-06T01:00:00Z",
    "workflow": "implement-ticket",
    "tier": "standard",
    "final_status": "DOD_BLOCKED",
    "agent_count": 9,
    "duration_s": 3600,
}


def test_reason_code_section_omitted_when_no_reason_codes_present():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked"},
    ]

    report = generate(runs, events, "test-label")

    assert "## Reason Codes" not in report


def test_reason_code_section_tallies_present_codes():
    runs = [_BASE_RUN, dict(_BASE_RUN, run_id="TCK-FAKE-2")]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked", "reason_code": "tag_registry_rejection"},
        {"run_id": "TCK-FAKE-2", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked", "reason_code": "tag_registry_rejection"},
        {"run_id": "TCK-FAKE-2", "seq": 2, "phase": "Test", "agent": "test-scoper", "status": "ok", "summary": "passed"},
    ]

    report = generate(runs, events, "test-label")

    assert "## Reason Codes" in report
    assert "| tag_registry_rejection | 2 |" in report


def test_reason_code_section_ignores_null_and_missing_fields():
    runs = [_BASE_RUN]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Verify", "agent": "done-checker", "status": "failed", "summary": "blocked", "reason_code": None},
        {"run_id": "TCK-FAKE", "seq": 2, "phase": "Test", "agent": "test-scoper", "status": "ok", "summary": "passed"},
    ]

    report = generate(runs, events, "test-label")

    assert "## Reason Codes" not in report


def test_reason_code_aggregation_is_workflow_agnostic():
    """Confirms TCK-20260706-CREATE-TICKETS-TAG-CHECK's claim: no code change was needed for
    generate_retro.py to also tally reason_code values from create-tickets.js's events, since the
    aggregation already iterates every event regardless of which workflow wrote it."""
    runs = [
        dict(_BASE_RUN, workflow="implement-ticket", final_status="TAGS_NOT_REGISTERED"),
        dict(_BASE_RUN, run_id="CREATE-TICKETS-FAKE", workflow="create-tickets", tier="n/a", final_status="DONE"),
    ]
    events = [
        {"run_id": "TCK-FAKE", "seq": 1, "phase": "Scope", "agent": "ticket-scoper", "status": "failed", "summary": "blocked", "reason_code": "tag_registry_rejection"},
        {"run_id": "CREATE-TICKETS-FAKE", "seq": 1, "phase": "Structure", "agent": "create-tickets", "status": "blocked", "summary": "1 task skipped", "reason_code": "tag_registry_rejection"},
    ]

    report = generate(runs, events, "test-label")

    assert "| tag_registry_rejection | 2 |" in report
