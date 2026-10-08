"""The retro's Failures section (TCK-20261007-RETRO-FAILURES-SECTION), following test_path_report.py / test_gate_ledger.py."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

_MON = Path(__file__).resolve().parents[2] / "tools" / "agent-monitoring"
if str(_MON) not in sys.path:
    sys.path.insert(0, str(_MON))

import generate_retro  # noqa: E402
import retro_failures  # noqa: E402


def _run(run_id, status="DONE", **kw):
    return {"run_id": run_id, "execution_id": f"e-{run_id}", "start_ts": "2026-10-06T10:00:00Z", "workflow": "implement-ticket",
            "final_status": status, **kw}


def _event(run_id, status="failed", agent="done-checker", summary="x", reason_code=None, seq=1, phase="Verify", **kw):
    return {"run_id": run_id, "seq": seq, "phase": phase, "agent": agent, "status": status, "summary": summary,
            "reason_code": reason_code, **kw}


def _render(runs, events):
    return generate_retro._failures_section(runs, events)


def test_a_blocked_run_is_listed_with_its_run_id_and_status():
    section = _render([_run("TCK-A", "BLOCKED"), _run("TCK-B", "DONE"), _run("TCK-C", "EPIC_SCOPED"), _run("TCK-D", "IN_PROGRESS")], [])
    assert "### Non-DONE runs (1)" in section and "`TCK-A` — BLOCKED" in section
    assert "TCK-B" not in section and "TCK-C" not in section and "TCK-D" not in section


def test_failed_and_blocked_events_are_grouped_by_agent_then_reason_with_counts():
    events = [
        _event("TCK-A", agent="done-checker", reason_code="dod_condition_failed", summary="DOD_BLOCKED: one"),
        _event("TCK-B", agent="done-checker", reason_code="dod_condition_failed", summary="DOD_BLOCKED: two"),
        _event("TCK-B", "blocked", agent="done-checker", summary="old event without a reason"),
        _event("TCK-C", agent="implementer", reason_code="needs_changes", summary="N"),
        _event("TCK-C", "ok", agent="implementer", summary="not a failure"),
    ]
    section = _render([], events)
    assert "### Failed and blocked events (4)" in section
    assert "**done-checker** — 3" in section and "**implementer** — 1" in section
    assert "`dod_condition_failed` × 2" in section and "`unspecified` × 1" in section and "`needs_changes` × 1" in section
    assert "DOD_BLOCKED: one" in section and "DOD_BLOCKED: two" in section and "not a failure" not in section


def test_a_test_failing_under_two_distinct_tickets_is_flagged_once_and_a_single_one_is_not():
    events = [
        _event("TCK-A", summary="FAILED tests/tools/test_x.py::test_flaky - assert 1 == 2"),
        _event("TCK-B", summary="tests/tools/test_x.py::test_flaky[param] failed again"),
        _event("TCK-B", summary="tests/tools/test_x.py::test_flaky again, same ticket"),
        _event("TCK-A", summary="tests/tools/test_y.py::test_once failed"),
    ]
    section = _render([], events)
    assert "- `test_flaky` × 2: TCK-A, TCK-B" in section
    assert "test_once" not in section.split("### Tests failing under two or more tickets")[1]


def test_the_same_ticket_failing_a_test_twice_is_not_recurring():
    events = [_event("TCK-A", summary="tests/t.py::test_z failed"), _event("TCK-A", summary="tests/t.py::test_z failed again", seq=2)]
    assert retro_failures.recurring_tests(events) == []


def test_a_bare_test_name_counts_only_without_a_node_id():
    assert retro_failures.test_names("test_alpha and test_beta failed") == ["test_alpha", "test_beta"]
    assert retro_failures.test_names("tests/a.py::test_alpha failed, also test_beta") == ["test_alpha"]


def test_a_period_with_nothing_failed_renders_an_explicit_zero_line():
    section = _render([_run("TCK-A", "DONE")], [_event("TCK-A", "ok")])
    assert section.startswith("## Failures") and "No non-DONE runs and no failed or blocked events" in section
    assert "###" not in section


def test_summaries_are_one_line_and_capped():
    section = _render([], [_event("TCK-A", summary="line one\nline two " + "x" * 400)])
    line = next(l for l in section.splitlines() if "TCK-A" in l)
    assert "line one line two" in line and len(line) < 300 and line.rstrip().endswith("…")


def test_an_exception_while_building_the_section_returns_none_and_the_retro_still_writes(monkeypatch, tmp_path):
    monkeypatch.setattr(retro_failures, "render_section", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert _render([_run("TCK-A", "BLOCKED")], []) is None
    report = generate_retro.generate([], [], "2026-W41", "2026-W41", failures=None)
    out = tmp_path / "RETRO.md"
    generate_retro._write_report_preserving_notes(report, out, False)
    assert "## Failures" not in out.read_text() and out.exists()


def test_the_section_sits_right_after_gate_failure_breakdown_and_moves_nothing_else():
    without = generate_retro.generate([], [], "2026-W41", "2026-W41")
    with_section = generate_retro.generate([], [], "2026-W41", "2026-W41", failures="## Failures\n\n_x_")
    assert "## Failures" not in without
    headings = lambda text: [l for l in text.splitlines() if l.startswith("## ")]
    base, added = headings(without), headings(with_section)
    assert added.index("## Failures") == added.index("## Gate Failure Breakdown") + 1
    assert [h for h in added if h != "## Failures"] == base


def test_building_the_section_leaves_every_shard_unchanged(tmp_path):
    shard = tmp_path / "2026-W41" / "a.events.jsonl"
    shard.parent.mkdir()
    shard.write_text('{"run_id":"TCK-A","status":"failed"}\n')
    before = hashlib.sha256(shard.read_bytes()).hexdigest()
    _render([_run("TCK-A", "BLOCKED")], [_event("TCK-A")])
    assert hashlib.sha256(shard.read_bytes()).hexdigest() == before
