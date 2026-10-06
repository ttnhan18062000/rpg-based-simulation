"""generate_retro.py with provenance-labelled hand closures (TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE).

Owner decision 2026-10-06: derived (tool_activity) durations never enter the headline average; they are averaged beside it with
their n; unknown durations are counted, never averaged."""
from __future__ import annotations

import sys
from pathlib import Path

_TOOLS = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import generate_retro  # noqa: E402
import retro_provenance as rp  # noqa: E402


def _run(rid, mode, dur, source=None, **extra):
    row = {"run_id": rid, "ticket_id": rid, "start_ts": "2026-10-05T08:00:00Z", "end_ts": "2026-10-05T09:00:00Z", "workflow": "implement-ticket",
           "tier": "standard", "final_status": "DONE", "agent_count": 2, "execution_mode": mode, "duration_s": dur, **extra}
    if source:
        row["duration_source"] = source
    return row


def _event(rid, seq, phase, cost=None, source=None):
    row = {"run_id": rid, "seq": seq, "phase": phase, "agent": "claude", "status": "ok", "summary": "s", "ts": "2026-10-05T09:00:00Z"}
    if cost is not None:
        row.update(tool_call_count=3, cost_proxy_score=cost)
    if source:
        row["cost_source"] = source
    return row


RUNS = [
    _run("P1", "pipeline", 600),                        # measured, 10 min
    _run("H-DECL", "hand", 1200, "declared"),           # declared, 20 min
    _run("H-DECL2", "hand", 3600, "declared"),          # declared, 60 min (slow)
    _run("H-DER", "hand", 7200, "tool_activity", claim_peers=0),  # derived, 120 min
    _run("H-UNK1", "hand", None, "unknown"),
    _run("H-UNK2", "hand", None, "unknown"),
    _run("H-OLD", "hand", 0),                           # unlabelled, predates the field
]
EVENTS = [
    _event("H-DER", 3, "Finalize", cost=40.0, source="session_window"),
    _event("H-DECL", 1, "Scope", cost=5.0, source="sidecar"),
    _event("P1", 1, "Scope", cost=7.0),
    _event("H-UNK1", 1, "Scope"),
]


def _text(runs=RUNS, events=EVENTS):
    return generate_retro.generate(runs, events, "2026-W41", week_str="2026-W41")


def test_headline_average_excludes_derived_and_the_derived_average_is_shown_beside_it_with_n():
    text = _text()
    # measured/declared: 600, 1200, 3600 -> 1800 s -> 30 min, n = 3 (the unlabelled 0 and the nulls have no duration)
    assert "| Avg duration (measured/declared, n=3) | 30 min (unknown, not averaged: 2) |" in text
    assert "| Avg duration, derived from tool activity (n=1) | 120 min |" in text
    assert "| Avg duration | " not in text


def test_the_unknown_count_is_shown_where_an_average_is_shown():
    text = _text()
    assert "| Hand-closed | 6 | 6 (100%) | 40 min (unknown, not averaged: 2) |" in text


def test_runs_by_duration_source_table_and_coverage_line():
    text = _text()
    block = text.split("**Hand-closed runs by duration source**")[1].split("## ")[0]
    assert "| Declared | 2 | 2 | 40 min |" in block
    assert "| Derived (tool activity) | 1 | 1 | 120 min |" in block
    assert "| Unknown (not averaged) | 2 | 0 | not averaged |" in block
    assert "| Unlabelled (pre-field) | 1 | 0 | n/a |" in block  # H-OLD only: pipeline runs are not hand closures
    assert "duration known for 3 of 6 (50%); a cost value for 2 of 6 (33%)" in block


def test_the_changed_meaning_note_renders_once_at_the_top_and_names_the_first_week():
    text = _text()
    assert text.count("Duration provenance: from 2026-W41") == 1
    assert text.index("Duration provenance") < text.index("## Run Summary")


def test_derived_runs_are_not_slow_runs_and_declared_ones_are():
    slow = generate_retro.compute_retro_metrics(RUNS, EVENTS)["slow_runs"]
    assert [r["run_id"] for r in slow] == ["H-DECL2"]


def test_session_window_cost_stays_out_of_the_spend_tables_and_is_reported_on_its_own_line():
    metrics = generate_retro.compute_retro_metrics(RUNS, EVENTS)
    assert metrics["spend_proxy_by_phase"].get("Finalize") is None and set(metrics["spend_proxy_by_phase"]) == {"Scope"}
    text = _text()
    assert "Derived ticket-level cost (`session_window`): 1 hand closure(s), total score 40.0" in text


def test_a_window_with_no_provenance_fields_renders_exactly_as_before():
    old = [_run("A", "hand", 0), _run("B", "pipeline", 600)]
    text = _text(old, [])
    assert "Duration provenance" not in text and "| Avg duration | 10 min |" in text
    assert generate_retro.compute_retro_metrics(old, [])["run_summary"]["provenance"] is None


def test_coverage_numbers_come_from_the_hand_runs_only():
    cov = rp.summary(RUNS, EVENTS)["hand_coverage"]
    assert cov == {"hand_runs": 6, "duration_known": 3, "cost_known": 2}
