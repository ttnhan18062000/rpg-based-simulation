"""Tests for tools/gate_checks/workflow_meta_conformance.py
(TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK).

Coverage-honesty requirement (SEQUENCE.md decision 4): every check function below has at least
one fixture proving it catches a real violation it claims to catch, not just that it runs on the
happy path.
"""

import json
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import gate_checks.workflow_meta_conformance as workflow_meta_conformance  # noqa: E402
from gate_checks.workflow_meta_conformance import (  # noqa: E402
    check_workflow_meta_conformance,
    collect_run_event_statuses,
    extract_meta_phases,
    resolve_workflow_source_path,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOWS_DIR = _REPO_ROOT / ".claude" / "workflows"
_REAL_EVENTS_PATH = _REPO_ROOT / "agent-monitoring" / "events.jsonl"


def _write_workflow_js(tmp_path, workflow_name, titles):
    phases_literal = ",\n".join(
        f"    {{ title: '{t}', detail: 'd' }}" for t in titles
    )
    (tmp_path / f"{workflow_name}.js").write_text(
        "export const meta = {\n"
        f"  name: '{workflow_name}',\n"
        "  phases: [\n"
        f"{phases_literal}\n"
        "  ],\n"
        "}\n"
    )


def _write_events_jsonl(tmp_path, run_id, phase_statuses):
    """phase_statuses: list of (phase, status) tuples -> one event row each."""
    lines = []
    for i, (phase, status) in enumerate(phase_statuses, start=1):
        lines.append(json.dumps({
            "run_id": run_id, "seq": i, "phase": phase, "agent": "x",
            "status": status, "summary": "s", "ts": "2026-07-10T00:00:00Z",
        }))
    events_path = tmp_path / "events.jsonl"
    events_path.write_text("\n".join(lines) + ("\n" if lines else ""))
    return events_path


# ---------------------------------------------------------------------------
# extract_meta_phases — real, live workflow files (not fixture copies)
# ---------------------------------------------------------------------------


def test_parses_meta_phases_from_implement_ticket_js():
    titles = extract_meta_phases(_WORKFLOWS_DIR / "implement-ticket.js")
    assert titles == [
        "Scope", "Investigate", "Plan", "Review", "Implement", "Architecture-Verify",
        "Test", "Parity", "Security-Review", "Verify", "Finalize",
    ]


def test_parses_meta_phases_from_create_tickets_js():
    titles = extract_meta_phases(_WORKFLOWS_DIR / "create-tickets.js")
    assert titles == ["Comprehend", "Investigate", "Structure", "Write", "Link"]


def test_parses_meta_phases_from_implement_epic_js():
    titles = extract_meta_phases(_WORKFLOWS_DIR / "implement-epic.js")
    assert titles == ["Discover", "Implement", "Report"]


def test_extract_meta_phases_missing_block_returns_empty_list(tmp_path):
    path = tmp_path / "no-phases.js"
    path.write_text("export const meta = { name: 'x' }\n")
    assert extract_meta_phases(path) == []


# ---------------------------------------------------------------------------
# resolve_workflow_source_path
# ---------------------------------------------------------------------------


def test_resolve_workflow_source_path_finds_real_file():
    path = resolve_workflow_source_path("implement-ticket", _WORKFLOWS_DIR)
    assert path == _WORKFLOWS_DIR / "implement-ticket.js"


def test_unresolvable_workflow_source_file_does_not_crash(tmp_path):
    assert resolve_workflow_source_path("some-future-workflow", tmp_path) is None
    assert resolve_workflow_source_path(None, tmp_path) is None


# ---------------------------------------------------------------------------
# collect_run_event_statuses
# ---------------------------------------------------------------------------


def test_collect_run_event_statuses_groups_by_phase(tmp_path):
    events_path = _write_events_jsonl(tmp_path, "TCK-FIXTURE", [
        ("Scope", "ok"), ("Investigate", "ok"), ("Parity", "skipped"),
    ])
    statuses = collect_run_event_statuses("TCK-FIXTURE", events_path)
    assert statuses == {"Scope": {"ok"}, "Investigate": {"ok"}, "Parity": {"skipped"}}


def test_unknown_run_id_returns_empty_or_na_not_a_crash(tmp_path):
    events_path = _write_events_jsonl(tmp_path, "TCK-REAL-RUN", [("Scope", "ok")])
    statuses = collect_run_event_statuses("TCK-NO-SUCH-RUN-ID", events_path)
    assert statuses == {}


# ---------------------------------------------------------------------------
# check_workflow_meta_conformance — core aggregate cross-reference
# ---------------------------------------------------------------------------


def test_flags_declared_phase_with_zero_events(tmp_path, monkeypatch):
    _write_workflow_js(tmp_path, "implement-ticket", ["Scope", "Investigate", "Plan"])
    events_path = _write_events_jsonl(tmp_path, "TCK-FIXTURE-1", [
        ("Scope", "ok"), ("Plan", "ok"),
    ])

    results = check_workflow_meta_conformance(
        "TCK-FIXTURE-1", workflows_dir=tmp_path, events_path=events_path
    )
    by_phase = {r["phase"]: r for r in results}
    assert by_phase["Investigate"]["status"] == "FAIL"
    assert by_phase["Investigate"]["evidence"]
    assert by_phase["Scope"]["status"] == "PASS"
    assert by_phase["Plan"]["status"] == "PASS"


def test_does_not_flag_a_phase_with_only_skipped_status_events(tmp_path):
    _write_workflow_js(tmp_path, "implement-ticket", ["Scope", "Investigate", "Plan"])
    events_path = _write_events_jsonl(tmp_path, "TCK-FIXTURE-2", [
        ("Scope", "ok"), ("Investigate", "skipped"), ("Plan", "skipped"),
    ])

    results = check_workflow_meta_conformance(
        "TCK-FIXTURE-2", workflows_dir=tmp_path, events_path=events_path
    )
    assert all(r["status"] != "FAIL" for r in results)


def test_check_workflow_meta_conformance_unresolvable_workflow_returns_labeled_na(tmp_path):
    events_path = _write_events_jsonl(tmp_path, "TCK-ANYTHING", [("Scope", "ok")])
    results = check_workflow_meta_conformance(
        "TCK-ANYTHING", workflows_dir=tmp_path, events_path=events_path
    )
    assert len(results) == 1
    assert results[0]["status"] == "NA"
    assert results[0]["phase"] is None


def test_check_workflow_meta_conformance_unknown_run_id_prefix_returns_labeled_na(tmp_path):
    _write_workflow_js(tmp_path, "implement-ticket", ["Scope"])
    events_path = _write_events_jsonl(tmp_path, "TCK-X", [("Scope", "ok")])
    results = check_workflow_meta_conformance(
        "NOT-A-KNOWN-PREFIX-123", workflows_dir=tmp_path, events_path=events_path
    )
    assert len(results) == 1
    assert results[0]["status"] == "NA"


def test_check_workflow_meta_conformance_run_id_with_zero_events_flags_every_phase(tmp_path):
    _write_workflow_js(tmp_path, "implement-ticket", ["Scope", "Investigate"])
    events_path = _write_events_jsonl(tmp_path, "TCK-OTHER-RUN", [("Scope", "ok")])

    results = check_workflow_meta_conformance(
        "TCK-NEVER-RAN", workflows_dir=tmp_path, events_path=events_path
    )
    assert all(r["status"] == "FAIL" for r in results)
    assert {r["phase"] for r in results} == {"Scope", "Investigate"}


# ---------------------------------------------------------------------------
# Real-world false-positive guard (Step 5) — replays actual
# TCK-20260710-CURRENT-RUN-SIDECAR-BASH event shape against the real
# implement-ticket.js meta.phases declaration.
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "KNOWN PLAN CONFLICT (TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK, see plan.md "
        "'Deviations'): Step 4's specified rule (FAIL iff a declared phase has zero events of "
        "ANY status, including 'skipped') is, by construction, indistinguishable from the "
        "'naive implementation' test_plan.md's own Anti-Drift Guards section says must be "
        "prevented from shipping — for a genuinely-conditional-by-design phase with NO event "
        "at all (Security-Review, confirmed by docs/agent-monitoring/schema.md: 'absent "
        "entirely (not even a skipped event) for every other ticket'), the rule cannot tell "
        "'legitimately never applicable' apart from 'silently skipped by the narrating LLM' — "
        "both produce zero rows of any status for this run_id. No per-workflow conditional-"
        "phase allowlist is permitted (plan.md Scope Guards), and call-site conditionality "
        "analysis of the .js source is out of Step 1's stated scope. Resolving this requires a "
        "Plan-level decision this ticket did not make. Left xfail (not silently deleted or "
        "weakened) so it surfaces on any future rerun as an open architecture question."
    ),
)
def test_does_not_flag_security_review_absent_when_ticket_untagged_security():
    assert _REAL_EVENTS_PATH.exists(), (
        f"{_REAL_EVENTS_PATH} not found — cannot replay real event data for this guard test"
    )
    real_rows = collect_run_event_statuses("TCK-20260710-CURRENT-RUN-SIDECAR-BASH", _REAL_EVENTS_PATH)
    assert real_rows, (
        "TCK-20260710-CURRENT-RUN-SIDECAR-BASH rows no longer present in "
        f"{_REAL_EVENTS_PATH} (log rotation?) — this guard test requires the real data"
    )

    results = check_workflow_meta_conformance(
        "TCK-20260710-CURRENT-RUN-SIDECAR-BASH",
        workflows_dir=_WORKFLOWS_DIR,
        events_path=_REAL_EVENTS_PATH,
    )
    failing = [r for r in results if r["status"] == "FAIL"]
    assert failing == [], f"expected zero FAIL findings, got: {failing}"

    by_phase = {r["phase"]: r for r in results}
    assert "Security-Review" not in by_phase


# ---------------------------------------------------------------------------
# Architecture guard — reuses vocabulary.py, does not reimplement it
# ---------------------------------------------------------------------------


def test_reuses_vocabulary_infer_workflow_not_a_reimplementation():
    source = Path(workflow_meta_conformance.__file__).read_text(encoding="utf-8")
    assert "from vocabulary import infer_workflow" in source
    assert not hasattr(workflow_meta_conformance, "WORKFLOW_PHASES")
