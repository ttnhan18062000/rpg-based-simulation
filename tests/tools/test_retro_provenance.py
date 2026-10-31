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
    _run("H-OLD", "hand", 0),                           # predates the field, 0 s: counted as unknown
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
    # measured/declared: 600, 1200, 3600 -> 1800 s -> 30 min, n = 3 (the pre-field 0 and the nulls have no duration)
    assert "| Avg duration (measured/declared, n=3) | 30 min (unknown, not averaged: 3) |" in text
    assert "| Avg duration, derived from tool activity (n=1) | 120 min |" in text
    assert "| Avg duration | " not in text


def test_the_unknown_count_is_shown_where_an_average_is_shown():
    text = _text()
    assert "| Hand-closed | 6 | 6 (100%) | 40 min (unknown, not averaged: 3) |" in text


def test_runs_by_duration_source_table_and_coverage_line():
    text = _text()
    block = text.split("**Hand-closed runs by duration source**")[1].split("## ")[0]
    assert "| Declared | 2 | 2 | 40 min |" in block
    assert "| Derived (tool activity) | 1 | 1 | 120 min |" in block
    assert "| Unknown (not averaged) | 3 | 0 | not averaged |" in block
    assert "| Unlabelled (pre-field) | 0 | 0 | n/a |" in block  # H-OLD (a pre-field hand closure at 0 s) is now unknown, TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS
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


# --- TCK-20261015-TOOLS-TELEMETRY-FAILURES-AND-DURATIONS: pre-field zero hand closures are unknown -----------------

def test_a_prefield_hand_closure_with_a_zero_duration_is_unknown_not_unlabelled():
    assert rp.source_of(_run("Z", "hand", 0)) == "unknown"
    assert rp.source_of(_run("N", "hand", None)) == "unknown"
    assert rp.source_of(_run("REAL", "hand", 900)) == "unlabelled"       # pre-field but measured: keeps its old treatment
    assert rp.source_of(_run("PIPE", "pipeline", 0)) == "unlabelled"      # only a hand closure writes 0 for "no evidence"
    assert rp.source_of(_run("D", "hand", 0, "declared")) == "declared"   # a labelled row is never relabelled


def test_the_provenance_block_counts_prefield_zero_rows_as_unknown_never_averaged():
    runs = [_run("H-DECL", "hand", 1200, "declared"), _run("OLD0a", "hand", 0), _run("OLD0b", "hand", 0), _run("OLD", "hand", 600)]
    block = rp.summary(runs, [])
    assert block["headline"]["unknown"] == 2
    assert block["by_source"]["unknown"]["count"] == 2 and block["by_source"]["unknown"]["avg_min"] is None
    assert block["by_source"]["unlabelled"]["count"] == 1  # OLD at 600 s is pre-field but measured


def test_the_hand_coverage_line_says_how_many_durations_a_week_close_re_derived():
    # TCK-20261021-HAND-CLOSURE-DURATION-FROM-LAST-ACTIVITY-AND-WEEK-CLOSE-REDERIVE
    base = {"execution_mode": "hand", "duration_source": "tool_activity", "duration_s": 600}
    runs = [dict(base, run_id="a", duration_rederived="week_close"), dict(base, run_id="b")]
    p = rp.summary(runs, [])
    assert p["rederived"] == 1 and "1 duration(s) re-derived at week close" in "\n".join(rp.by_source_lines(p))
    p = rp.summary([dict(base, run_id="b")], [])
    assert p["rederived"] == 0 and "re-derived" not in "\n".join(rp.by_source_lines(p))


# --- TCK-20261031-RETRO-SAYS-MID-WEEK-UNKNOWN-DURATIONS-DERIVE-AT-WEEK-CLOSE ----------------------------------------------

_OPEN_NOTE = "the week is not finished, so these get a derived duration at `make agent-monitoring-close-week`"


def test_an_open_week_says_where_its_unknown_durations_come_from():
    text = generate_retro.generate(RUNS, EVENTS, "2026-W41", week_str="2026-W41", week_open=True)
    assert f"| Avg duration (measured/declared, n=3) | 30 min (unknown, not averaged: 3; {_OPEN_NOTE}) |" in text
    assert text.count(_OPEN_NOTE) == 1  # next to the unknown count in the Run Summary only


def test_a_closed_week_is_byte_identical_to_before():
    default = generate_retro.generate(RUNS, EVENTS, "2026-W41", week_str="2026-W41")
    explicit = generate_retro.generate(RUNS, EVENTS, "2026-W41", week_str="2026-W41", week_open=False)
    assert default == explicit and _OPEN_NOTE not in default
    assert "| Avg duration (measured/declared, n=3) | 30 min (unknown, not averaged: 3) |" in default


def test_an_open_week_with_no_unknown_duration_adds_nothing():
    known = [r for r in RUNS if r["run_id"] in ("P1", "H-DECL", "H-DER")]
    assert _OPEN_NOTE not in generate_retro.generate(known, EVENTS, "2026-W41", week_str="2026-W41", week_open=True)


def test_week_is_open_follows_week_close_is_finished(monkeypatch):
    import datetime as dt

    class _Today(dt.date):
        current = dt.date(2026, 10, 31)

        @classmethod
        def today(cls):
            return cls.current

    monkeypatch.setattr(generate_retro, "date", _Today)
    assert generate_retro._week_is_open("2026-W44") is True      # ends Sunday 2026-11-01
    _Today.current = dt.date(2026, 11, 2)
    assert generate_retro._week_is_open("2026-W44") is False     # finished
    assert generate_retro._week_is_open("2026-W43") is False
    assert generate_retro._week_is_open(None) is False           # a rolling window
    assert generate_retro._week_is_open("not-a-week") is False   # an unreadable id never fails the report
