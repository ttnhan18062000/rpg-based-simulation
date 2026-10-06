"""Tests for TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT.

session_role on runs and events (by session id, never the shared sidecar, separate from `agent`); the manual-action
tagger and its hook (decisions, feedback and requirements are not counted; the prompt text is never recorded); the
batch-latency triplet (`unknown`, never zero; one real finished batch reproduced by hand); the retro section.
"""
import io
import json
import sys
from pathlib import Path

import pytest

from tools.sessions import state as st

_MON = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MON) not in sys.path:
    sys.path.insert(0, str(_MON))

import batch_latency as bl  # noqa: E402
import generate_retro  # noqa: E402
import manual_actions as ma  # noqa: E402
import record_events  # noqa: E402
import record_run  # noqa: E402
import session_layer_report as slr  # noqa: E402
import session_role as sr  # noqa: E402


def _binding(role, session_id):
    return st.Binding(session_id=session_id, role=role, source="startup", worktree="/w", branch="b",
                      transcript_path="", process=None, manifest_digest="d", ts="2026-10-05T00:00:00Z")


@pytest.fixture
def roles(tmp_path, monkeypatch):
    root = tmp_path / "session-roles"
    monkeypatch.setattr(st, "state_root", lambda cwd=".": root)
    return root


# ---- session_role ------------------------------------------------------------------------------

def test_two_concurrent_sessions_never_swap_roles(roles):
    st.record_start(roles, _binding("rpg-implementer", "sess-A"))
    st.record_start(roles, _binding("agent-working-implementer", "sess-B"))
    assert sr.resolve_session_role("sess-A") == "rpg-implementer"
    assert sr.resolve_session_role("sess-B") == "agent-working-implementer"


def test_unbound_session_and_missing_session_id_are_unresolved(roles, monkeypatch):
    st.record_start(roles, _binding("rpg-implementer", "sess-A"))
    assert sr.resolve_session_role("sess-other") == sr.UNRESOLVED
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    assert sr.resolve_session_role() == sr.UNRESOLVED


def test_env_session_id_is_the_default_and_the_shared_sidecar_is_never_read(roles, monkeypatch, tmp_path):
    st.record_start(roles, _binding("rpg-planner", "sess-A"))
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sess-A")
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "current_run").write_text(json.dumps({"agent": "rpg-implementer", "session_role": "rpg-implementer"}))
    assert sr.resolve_session_role() == "rpg-planner"


def test_a_resolution_failure_is_unresolved_not_an_exception(monkeypatch):
    monkeypatch.setattr(st, "state_root", lambda cwd=".": (_ for _ in ()).throw(OSError("boom")))
    assert sr.resolve_session_role("sess-A") == sr.UNRESOLVED


def test_stamp_keeps_an_explicit_value_and_does_not_mutate(roles):
    rec = {"run_id": "r"}
    assert sr.stamp(rec, "nobody")["session_role"] == "unresolved" and "session_role" not in rec
    assert sr.stamp({"session_role": "x"}, "nobody")["session_role"] == "x"


def test_session_role_does_not_disturb_validation_or_the_agent_field(roles):
    st.record_start(roles, _binding("rpg-implementer", "sess-A"))
    event = sr.stamp({"run_id": "r", "seq": 1, "ts": "2026-10-05T00:00:00Z", "phase": "Scope", "agent": "implementer",
                      "summary": "s", "status": "ok"}, "sess-A")
    assert record_events.validate_record(event) == [] and event["agent"] == "implementer"
    assert event["session_role"] == "rpg-implementer"
    run = sr.stamp({"run_id": "r", "start_ts": "2026-10-05T00:00:00Z", "workflow": "implement-ticket", "tier": "standard",
                    "final_status": "DONE", "agent_count": 1}, "sess-A")
    assert record_run.validate_record(run) == []


def test_record_run_and_record_events_write_session_role(roles, monkeypatch, tmp_path):
    st.record_start(roles, _binding("agent-working-implementer", "sess-A"))
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sess-A")
    runs, evs = tmp_path / "w" / "runs.jsonl", tmp_path / "w" / "events.jsonl"
    monkeypatch.setattr(record_run, "resolve_write_target", lambda *a, **k: runs)
    monkeypatch.setattr(record_events, "resolve_write_target", lambda *a, **k: evs)
    run = {"run_id": "TCK-1", "start_ts": "2026-10-05T00:00:00Z", "end_ts": "2026-10-05T00:01:00Z",
           "workflow": "implement-ticket", "tier": "standard", "final_status": "DONE", "agent_count": 1}
    monkeypatch.setattr(sys, "argv", ["record_run.py", "--data", json.dumps(run)])
    record_run.main()
    event = {"run_id": "TCK-1", "seq": 1, "ts": "2026-10-05T00:00:30Z", "phase": "Scope", "agent": "implementer",
             "summary": "s", "status": "ok"}
    monkeypatch.setattr(sys, "argv", ["record_events.py", "--data", json.dumps([event])])
    record_events.main()
    assert json.loads(runs.read_text())["session_role"] == "agent-working-implementer"
    assert json.loads(evs.read_text())["session_role"] == "agent-working-implementer"
    assert json.loads(evs.read_text())["agent"] == "implementer"


def test_unbound_session_writes_unresolved(roles, monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "plain")
    evs = tmp_path / "events.jsonl"
    monkeypatch.setattr(record_events, "resolve_write_target", lambda *a, **k: evs)
    event = {"run_id": "TCK-1", "seq": 1, "ts": "2026-10-05T00:00:30Z", "phase": "Scope", "agent": "implementer",
             "summary": "s", "status": "ok"}
    monkeypatch.setattr(sys, "argv", ["record_events.py", "--data", json.dumps([event])])
    record_events.main()
    assert json.loads(evs.read_text())["session_role"] == "unresolved"


# ---- headline metric: tagging ------------------------------------------------------------------

_FIXTURE = [
    ("continue as agent-working-implementer", "handover_recovery"),
    ("read your handover first", "handover_recovery"),
    ("you are the rpg-planner", "role_reminder"),
    ("send questions to the planner instead of me", "routing_correction"),
    ("ask the planner, not me", "routing_correction"),
    ("wake up the implementer", "manual_wake"),
    ("any update from agent-working-implementer", "manual_wake"),
    ("you are in the wrong worktree", "worktree_correction"),
    ("use your own worktree", "worktree_correction"),
    ("that's not yours, stay in your lane", "boundary_reminder"),
    # decisions, design feedback and requirements are NOT repeated instructions
    ("yes, merge it", None),
    ("I decided we keep both fields; the owner choice is final", None),
    ("should the planner own this?", None),
    ("the dashboard needs a new filter for the retro report by role", None),
    ("good design, but rename the module to boundary", None),
    ("x" * 400 + " read your handover", None),
    ("", None),
]


@pytest.mark.parametrize("prompt,expected", _FIXTURE)
def test_tagger_fixture(prompt, expected):
    assert ma.tag_prompt(prompt) == expected


def test_fixture_batch_counts_exclude_decisions_and_requirements():
    records = [{"category": c, "source": "sample"} for p, c in _FIXTURE if c]
    counts = ma.count_by_category(records)
    assert sum(v["sample"] for v in counts.values()) == 10 and counts["handover_recovery"]["sample"] == 2
    assert all(set(v) == {"sample", "tally"} for v in counts.values()) and set(counts) == set(ma.CATEGORIES)


def test_hook_records_category_only_never_the_prompt(roles, tmp_path):
    st.record_start(roles, _binding("rpg-implementer", "sess-A"))
    prompt = "continue as rpg-implementer, secret-token-123"
    rec = ma.record_prompt({"prompt": prompt, "session_id": "sess-A", "cwd": "."}, tmp_path)
    text = next(tmp_path.glob("*/manual_actions.jsonl")).read_text()
    assert rec["category"] == "handover_recovery" and rec["session_role"] == "rpg-implementer"
    assert "secret-token-123" not in text and "prompt" not in json.loads(text)


def test_untagged_prompt_writes_nothing_and_bad_input_never_raises(tmp_path):
    assert ma.record_prompt({"prompt": "merge it", "session_id": "s"}, tmp_path) is None and not list(tmp_path.glob("*"))
    assert ma.main(["hook"], stdin=io.StringIO("not json")) == 0
    assert ma.main(["hook"], stdin=io.StringIO("[1]")) == 0


def test_tally_is_recorded_as_typed_and_validated(tmp_path):
    rec = ma.record_tally("manual_wake", "batch-1", 2, tmp_path)
    assert rec["source"] == "tally" and rec["count"] == 2 and rec["batch"] == "batch-1"
    with pytest.raises(ValueError):
        ma.record_tally("decision", None, 1, tmp_path)
    with pytest.raises(ValueError):
        ma.record_tally("manual_wake", None, 0, tmp_path)
    assert ma.count_by_category([rec])["manual_wake"]["tally"] == 2


# ---- latency -----------------------------------------------------------------------------------

# PR 346 (merged), read from `gh pr view 346` and computed by hand: first commit 07:11:27Z, last check completed
# 07:53:13Z, merged 07:56:20Z -> implementation 41m46s (2506 s), finalization 3m07s (187 s), cycle 44m53s (2693 s).
_PR346 = {
    "commits": [{"committedDate": "2026-10-05T07:16:30Z"}, {"committedDate": "2026-10-05T07:11:27Z"}],
    "mergedAt": "2026-10-05T07:56:20Z",
    "statusCheckRollup": [
        {"conclusion": "SUCCESS", "completedAt": "2026-10-05T07:50:49Z"},
        {"conclusion": "SKIPPED", "completedAt": "2026-10-05T07:53:12Z"},
        {"conclusion": "SUCCESS", "completedAt": "2026-10-05T07:53:13Z"},
    ],
}


def test_latency_reproduces_the_hand_computed_value_for_a_real_batch():
    out = bl.from_pr(_PR346)
    assert (out["implementation_s"], out["finalization_s"], out["cycle_s"]) == (2506, 187, 2693)
    assert out["dispatch_source"] == "first_commit" and bl.fmt(2506) == "0h41m46s"


def test_a_given_dispatch_overrides_the_first_commit():
    out = bl.from_pr(_PR346, dispatch_ts="2026-10-05T07:00:00Z")
    assert out["cycle_s"] == 56 * 60 + 20 and out["dispatch_source"] == "given"


def test_missing_timestamps_are_unknown_never_zero():
    out = bl.from_pr({"commits": [], "mergedAt": None, "statusCheckRollup": []})
    assert out["implementation_s"] == out["finalization_s"] == out["cycle_s"] == bl.UNKNOWN
    unmerged = bl.from_pr({**_PR346, "mergedAt": None})
    assert unmerged["implementation_s"] == 2506 and unmerged["finalization_s"] == bl.UNKNOWN == unmerged["cycle_s"]


def test_a_red_or_unfinished_check_means_pr_green_is_unknown():
    red = [{"conclusion": "FAILURE", "completedAt": "2026-10-05T07:50:49Z"}]
    pending = [{"conclusion": "", "completedAt": "0001-01-01T00:00:00Z", "state": "PENDING"}]
    assert bl.pr_green_ts(red) is None and bl.pr_green_ts(pending) is None and bl.pr_green_ts([]) is None


def test_a_negative_span_is_unknown():
    assert bl.latencies("2026-10-05T08:00:00Z", "2026-10-05T07:00:00Z", None)["implementation_s"] == bl.UNKNOWN


# ---- retro section -----------------------------------------------------------------------------

def test_section_renders_zeros_unresolved_and_unknown():
    text = slr.render([], [{"session_role": "rpg-implementer"}, {}], [{"kind": "edit_outside_owns"}],
                      [("#9", bl.latencies(None, None, None) | {"dispatch_source": "unavailable"})])
    assert "| role reminder | 0 | 0 |" in text and "| unresolved | 1 |" in text and "| rpg-implementer | 1 |" in text
    assert "edit_outside_owns: 1" in text and "unknown" in text and "never zero" in text


def test_never_recorded_family_renders_the_dark_line_and_no_zero_table():
    text = slr.render([], [], [], None, manual_total=0, boundary_total=0)
    assert text.count("_Instrument not running: no manual_actions records exist in any week.") == 1
    assert "_Instrument not running: no role_boundary records exist in any week." in text
    assert "| role reminder |" not in text and "Total: 0" not in text and "None in this period." not in text


def test_nothing_in_period_keeps_the_zero_table_and_says_the_instrument_is_active():
    text = slr.render([], [], [], None, manual_total=7, boundary_total=2)
    assert "| role reminder | 0 | 0 |" in text and "Total: 0." in text
    assert "(instrument active; 7 records outside this period)" in text
    assert "(instrument active; 2 records outside this period)" in text
    assert "Instrument not running" not in text


def test_uncounted_totals_keep_the_old_output():
    text = slr.render([], [], [])
    assert "| role reminder | 0 | 0 |" in text and "instrument" not in text.lower().replace("instrument.", "")


def test_all_unresolved_runs_say_role_binding_was_not_active_and_a_mixed_set_does_not():
    assert "role binding was not active" in slr.render([], [{}, {"session_role": "unresolved"}], [])
    assert "role binding was not active" not in slr.render([], [{}, {"session_role": "rpg-implementer"}], [])
    assert "role binding was not active" not in slr.render([], [], [])


def test_load_family_and_period_filter(tmp_path):
    (tmp_path / "2026-W41").mkdir()
    (tmp_path / "2026-W41" / "manual_actions.jsonl").write_text(
        json.dumps({"ts": "2026-10-05T00:00:00Z", "category": "manual_wake"}) + "\nnot json\n")
    recs = slr.load_family(tmp_path, "manual_actions.jsonl")
    assert len(recs) == 1
    assert slr.in_period(recs, "2026-W41") == recs and slr.in_period(recs, "2026-W40") == []
    assert slr.in_period(recs, None, "2026-10-06") == []


def test_retro_generate_omits_the_section_by_default_and_includes_it_when_given():
    base = generate_retro.generate([], [], "W")
    assert "Session-Layer Measures" not in base
    section = slr.render([], [], [], None)
    assert "## Session-Layer Measures" in generate_retro.generate([], [], "W", session_layer=section)


# ---- the wired UserPromptSubmit hook -----------------------------------------------------------

import subprocess  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent


def _wired():
    hooks = json.loads((_REPO_ROOT / ".claude" / "settings.json").read_text())["hooks"]["UserPromptSubmit"]
    assert len(hooks) == 1 and "matcher" not in hooks[0]
    return hooks[0]["hooks"][0]["command"]


def _run(cwd, payload="{}"):
    return subprocess.run(["bash", "-c", _wired()], input=payload, capture_output=True, text=True, cwd=cwd)


def test_wired_hook_passes_outside_a_repo_and_when_the_script_is_missing(tmp_path):
    assert _run(tmp_path).returncode == 0
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    assert _run(tmp_path).returncode == 0  # a missing script must never block a prompt (exit 2 would)


def test_wired_hook_in_this_repo_exits_zero_with_no_output_for_an_untagged_prompt():
    result = _run(_REPO_ROOT, json.dumps({"prompt": "merge it", "session_id": "s", "cwd": str(_REPO_ROOT)}))
    assert result.returncode == 0 and result.stdout == ""
