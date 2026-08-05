"""Tests for tools/agent-monitoring/security_gate_firing_check.py
(TCK-20260805-SECURITY-GATE-FIRING-MONITOR).

Mirrors tests/tools/test_retrieval_baseline_metrics.py's design: synthetic-fixture unit tests for
the classification logic itself, plus an integration test against the REAL agent-monitoring/
corpus asserting today's known-correct classification — never a tmp_path copy for the live-corpus
assertion, which would make it vacuous.
"""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "security_gate_firing_check.py"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import security_gate_firing_check as sgfc  # noqa: E402
from security_gate_firing_check import (  # noqa: E402
    _BOOTSTRAP_EXCEPTION_TICKETS,
    check_security_gate_firing,
)


# ---------------------------------------------------------------------------
# Synthetic-fixture unit tests — verify the classification logic itself,
# independent of today's live corpus contents.
# ---------------------------------------------------------------------------

def _fake_corpus(ticket_tags, runs, events):
    """Patches the three data sources check_security_gate_firing() reads, so the
    classification logic can be tested against hand-built shapes."""
    return (
        patch.object(sgfc, "_collect_tagged_tickets", return_value=ticket_tags),
        patch.object(sgfc, "_load_runs_and_events", return_value=(runs, events)),
    )


def test_flags_the_gate_bypass_hardening_miss_shape():
    """Reproduces the real GATE-BYPASS-HARDENING shape: DONE, zero Security-Review events."""
    ticket_tags = {"TCK-FAKE-MISS": ["security"]}
    runs = [{"run_id": "TCK-FAKE-MISS", "final_status": "DONE"}]
    events = []
    p1, p2 = _fake_corpus(ticket_tags, runs, events)
    with p1, p2:
        report = check_security_gate_firing()
    assert report["missed"] == ["TCK-FAKE-MISS"]
    assert report["clean"] == []


def test_does_not_flag_a_clean_fire_shape():
    """Reproduces the real CODEX-LIVE-TRANSPORT shape: NEEDS_CHANGES then DONE, with a
    Security-Review event present on the run."""
    ticket_tags = {"TCK-FAKE-CLEAN": ["security"]}
    runs = [
        {"run_id": "TCK-FAKE-CLEAN", "final_status": "NEEDS_CHANGES"},
        {"run_id": "TCK-FAKE-CLEAN", "final_status": "DONE"},
    ]
    events = [{"run_id": "TCK-FAKE-CLEAN", "phase": "Security-Review"}]
    p1, p2 = _fake_corpus(ticket_tags, runs, events)
    with p1, p2:
        report = check_security_gate_firing()
    assert report["clean"] == ["TCK-FAKE-CLEAN"]
    assert report["missed"] == []


def test_security_blocked_without_done_lands_in_pending_not_clean():
    """A run whose only final_status is SECURITY_BLOCKED (never reached DONE) proves the gate
    can fire, but isn't itself evidence the *completed* pipeline includes the gate — so it lands
    in pending, same as any other non-DONE ticket, not clean."""
    ticket_tags = {"TCK-FAKE-BLOCKED": ["security"]}
    runs = [{"run_id": "TCK-FAKE-BLOCKED", "final_status": "SECURITY_BLOCKED"}]
    events = []
    p1, p2 = _fake_corpus(ticket_tags, runs, events)
    with p1, p2:
        report = check_security_gate_firing()
    # SECURITY_BLOCKED alone has no DONE record, so this lands in pending, not clean —
    # a ticket that never reached DONE is not evaluable for "did the gate fire on completion."
    assert report["pending"] == ["TCK-FAKE-BLOCKED"]
    assert report["missed"] == []
    assert report["clean"] == []


def test_non_security_tagged_ticket_is_ignored():
    ticket_tags = {"TCK-FAKE-OTHER": ["economy"]}
    runs = [{"run_id": "TCK-FAKE-OTHER", "final_status": "DONE"}]
    events = []
    p1, p2 = _fake_corpus(ticket_tags, runs, events)
    with p1, p2:
        report = check_security_gate_firing()
    for bucket in ("missed", "clean", "pending", "excluded"):
        assert "TCK-FAKE-OTHER" not in report[bucket]


def test_bootstrap_exception_ticket_never_flagged_even_if_it_looks_like_a_miss():
    (bootstrap_id,) = _BOOTSTRAP_EXCEPTION_TICKETS
    ticket_tags = {bootstrap_id: ["security"]}
    runs = [{"run_id": bootstrap_id, "final_status": "DONE"}]
    events = []  # would otherwise look exactly like a real miss
    p1, p2 = _fake_corpus(ticket_tags, runs, events)
    with p1, p2:
        report = check_security_gate_firing()
    assert report["excluded"] == [bootstrap_id]
    assert bootstrap_id not in report["missed"]
    assert bootstrap_id not in report["clean"]


def test_zero_run_records_does_not_raise_and_lands_in_pending():
    ticket_tags = {"TCK-FAKE-NORUNS": ["security"]}
    runs = []
    events = []
    p1, p2 = _fake_corpus(ticket_tags, runs, events)
    with p1, p2:
        report = check_security_gate_firing()
    assert report["pending"] == ["TCK-FAKE-NORUNS"]


def test_report_never_silently_drops_a_security_tagged_ticket():
    """Every security-tagged ticket in ticket_tag_map must land in exactly one of the four
    buckets — never absent entirely."""
    ticket_tags = {
        "TCK-A": ["security"], "TCK-B": ["security"],
        "TCK-C": ["security"], "TCK-D": ["security"],
    }
    runs = [
        {"run_id": "TCK-A", "final_status": "DONE"},  # miss
        {"run_id": "TCK-B", "final_status": "DONE"},  # clean
        {"run_id": "TCK-C", "final_status": "NEEDS_CHANGES"},  # pending
        # TCK-D: no runs at all -> pending
    ]
    events = [{"run_id": "TCK-B", "phase": "Security-Review"}]
    p1, p2 = _fake_corpus(ticket_tags, runs, events)
    with p1, p2:
        report = check_security_gate_firing()
    all_classified = set(report["missed"]) | set(report["clean"]) | set(report["pending"]) | set(report["excluded"])
    assert all_classified == set(ticket_tags.keys())


# ---------------------------------------------------------------------------
# Reuse-not-reimplement guard
# ---------------------------------------------------------------------------

def test_module_reuses_generate_retro_helpers_not_a_second_loader():
    import ast
    tree = ast.parse(_MODULE_PATH.read_text())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "_collect_tagged_tickets" in imported
    assert "_load_runs_and_events" in imported
    assert "_resolve_status" in imported


def test_does_not_import_generate_retro_tag_breakdown_internals():
    """This module must not import tag_breakdown_skill or compute_retro_metrics — its job is a
    separate strict pass/fail list, not a modification of the existing aggregate report. The
    module's own docstring names these functions in prose to explain the distinction, which is
    expected — this asserts no actual import binding exists, not a bare substring absence."""
    import ast
    tree = ast.parse(_MODULE_PATH.read_text())
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "compute_retro_metrics" not in imported
    assert "tag_breakdown_skill" not in imported


# ---------------------------------------------------------------------------
# Live-corpus integration test — today's real, known-correct classification
# ---------------------------------------------------------------------------

def test_live_corpus_matches_known_ground_truth():
    report = check_security_gate_firing()
    assert "TCK-20260731-GATE-BYPASS-HARDENING" in report["missed"]
    assert "TCK-20260801-CODEX-LIVE-TRANSPORT" in report["clean"]
    assert "TCK-20260801-CODEX-PILOT-ORCHESTRATION" in report["clean"]
    assert "TCK-20260705-WORKFLOW-SECURITY-GATE" in report["excluded"]
    assert "TCK-20260705-WORKFLOW-SECURITY-GATE" not in report["missed"]


def test_cli_runs_against_real_corpus_and_prints_json():
    # Intentionally not check=True: today's live corpus contains one real, already-known miss
    # (GATE-BYPASS-HARDENING), so exit code 1 is the correct, expected outcome right now — the
    # CLI's exit-1-on-missed behavior is itself what this test verifies.
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True,
    )
    report = json.loads(result.stdout)
    assert set(report.keys()) == {"missed", "clean", "pending", "excluded", "derivation"}
    assert result.returncode == (1 if report["missed"] else 0)


def test_causes_zero_diff_on_real_corpus():
    pre = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout
    check_security_gate_firing()
    post = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout
    assert pre == post, f"security_gate_firing_check mutated agent-monitoring/: pre={pre!r} post={post!r}"
