"""TCK-20261020-HAND-CLOSURE-RECORDS-FOLDED-PHASES-AS-SKIPPED: Review, Document-Update and Architecture-Verify, which the
hand path folds into Implement/Verify, are recorded (not omitted) so `phases_omitted` names only real gaps."""
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[2] / "tools" / "agent-monitoring"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import path_record  # noqa: E402
import record_events  # noqa: E402
import record_hand_orchestrated_closure as rec  # noqa: E402
from vocabulary import SKIP_REASONS  # noqa: E402

NARRATED = [{"phase": p, "status": "ok", "summary": p} for p in ("Scope", "Implement", "Test", "Verify", "Finalize")]


def _by_phase(events):
    return {e["phase"]: e for e in events}


def test_standard_closure_records_review_and_architecture_verify_as_no_hand_tool():
    added = _by_phase(rec.folded_phase_events("standard", NARRATED, "claude", set()))
    for phase in ("Review", "Architecture-Verify"):
        assert (added[phase]["status"], added[phase]["skip_reason"], added[phase]["agent"]) == ("skipped", "no_hand_tool", "claude")
        assert "recorder" in added[phase]["summary"]
    merged = rec.insert_in_plan_order(NARRATED, list(added.values()))
    omitted = path_record.phases_omitted("standard", [e["phase"] for e in merged])
    assert "Review" not in omitted and "Architecture-Verify" not in omitted and "Document-Update" not in omitted


def test_document_update_is_ok_when_a_docs_file_changed_and_names_up_to_three():
    changed = {"docs/guides/x.md", "docs/a.md", "docs/b.md", "docs/c.md", "docs/REGISTRY.yaml", "tools/t.py"}
    event = _by_phase(rec.folded_phase_events("standard", NARRATED, "claude", changed))["Document-Update"]
    assert event["status"] == "ok" and "skip_reason" not in event
    assert "derived by the recorder" in event["summary"] and "docs/a.md, docs/b.md, docs/c.md (+1 more)" in event["summary"]
    assert "REGISTRY" not in event["summary"]


def test_document_update_is_skipped_when_only_registry_and_parity_ledger_changed():
    event = _by_phase(rec.folded_phase_events("standard", NARRATED, "claude", {"docs/REGISTRY.yaml", "docs/parity_ledger/y.yaml"}))["Document-Update"]
    assert (event["status"], event["skip_reason"]) == ("skipped", "no_hand_tool")


def test_document_update_is_skipped_when_the_changed_files_are_unreadable():
    event = _by_phase(rec.folded_phase_events("standard", NARRATED, "claude", None))["Document-Update"]
    assert (event["status"], event["skip_reason"]) == ("skipped", "no_hand_tool") and "could not" in event["summary"]


def test_a_narrated_event_for_any_of_the_three_is_kept_and_nothing_is_added():
    narrated = NARRATED + [{"phase": p, "status": "ok", "summary": "mine"} for p in ("Review", "Document-Update", "Architecture-Verify")]
    assert rec.folded_phase_events("standard", narrated, "claude", {"docs/x.md"}) == []


def test_hotfix_adds_only_document_update():
    added = rec.folded_phase_events("hotfix", NARRATED, "claude", {"docs/x.md"})
    assert [e["phase"] for e in added] == ["Document-Update"]
    assert rec.folded_phase_events("hotfix", NARRATED, "claude", set())[0]["skip_reason"] == "no_hand_tool"


def test_added_events_keep_the_plan_order_and_other_phases_are_untouched():
    added = rec.folded_phase_events("standard", NARRATED, "claude", {"docs/x.md"})
    phases = [e["phase"] for e in rec.insert_in_plan_order(NARRATED, added)]
    order = {n: i for i, n in enumerate(path_record.phase_order())}
    assert phases == sorted(phases, key=order.__getitem__)
    assert {"Investigate", "Plan"}.isdisjoint(e["phase"] for e in added)


def test_added_events_pass_record_events_validation():
    assert "no_hand_tool" in SKIP_REASONS
    for e in rec.folded_phase_events("standard", NARRATED, "claude", {"docs/x.md"}):
        record = {**e, "run_id": "r", "execution_id": "x", "provider": "claude", "ticket_id": "TCK-20261020-T", "seq": 1,
                  "timestamp": "2026-10-20T00:00:00Z"}
        assert not [err for err in record_events.validate_record(record) if "run_id" in err or "skip_reason" in err or "seq" in err]


def test_epic_and_an_unreadable_plan_add_nothing(tmp_path):
    assert rec.folded_phase_events("epic", NARRATED, "claude", set()) == []
    assert rec.folded_phase_events("standard", NARRATED, "claude", set(), plan_path=tmp_path / "missing.yaml") == []


def test_recorder_added_events_leave_agent_count_unknown():
    # TCK-20261020-HAND-CLOSURE-AGENT-COUNT-UNKNOWN superseded the subtraction: a hand closure's count is null.
    added = rec.folded_phase_events("standard", NARRATED, "claude", {"docs/x.md"})
    assert len(added) == 3
    events = rec.insert_in_plan_order(NARRATED, added)
    run, event_records = rec.build_records("TCK-20261020-T", "standard", "DONE", events, None, None, "implement-ticket", "claude",
                                           "claude")
    assert len(event_records) == len(NARRATED) + 3
    assert "agent_count" in run and run["agent_count"] is None


# --- TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW: --review-ref records the planner's PR review -------------

import pytest  # noqa: E402


def _assembled(ref, tier="standard", narrated=NARRATED):
    """The events main() would hold for a closure: the ref'd Review first (when given), then the folded ones."""
    events = list(narrated)
    if ref is not None:
        events = rec.insert_in_plan_order(events, [rec.review_ref_event(ref, "claude")])
    return rec.insert_in_plan_order(events, rec.folded_phase_events(tier, events, "claude", set()))


def test_a_review_ref_records_review_ok_with_the_link_in_plan_order():
    review = _by_phase(_assembled("804#6545824938"))["Review"]
    assert (review["status"], review["agent"]) == ("ok", "claude") and "skip_reason" not in review
    assert "PR #804" in review["summary"] and "6545824938" in review["summary"] and "--review-ref 804#6545824938" in review["summary"]
    phases = [e["phase"] for e in _assembled("804#6545824938")]
    order = {n: i for i, n in enumerate(path_record.phase_order())}
    assert phases == sorted(phases, key=order.__getitem__) and phases.count("Review") == 1


def test_a_review_ref_leaves_architecture_verify_skipped():
    added = _by_phase(_assembled("804#1"))
    assert (added["Architecture-Verify"]["status"], added["Architecture-Verify"]["skip_reason"]) == ("skipped", "no_hand_tool")


def test_without_a_ref_the_events_are_exactly_todays():
    plain = rec.insert_in_plan_order(NARRATED, rec.folded_phase_events("standard", NARRATED, "claude", set()))
    assert _assembled(None) == plain
    review = _by_phase(plain)["Review"]
    assert (review["status"], review["skip_reason"]) == ("skipped", "no_hand_tool")


def test_the_review_ref_event_passes_record_events_validation():
    record = {**rec.review_ref_event("12#34", "claude"), "run_id": "r", "execution_id": "x", "provider": "claude",
              "ticket_id": "TCK-20261031-T", "seq": 1, "timestamp": "2026-10-31T00:00:00Z"}
    assert not [err for err in record_events.validate_record(record) if "run_id" in err or "status" in err or "seq" in err]


@pytest.mark.parametrize("bad", ["", "804", "#12", "804#", "a#1", "1#b", "0#5", "5#0", "1#2#3", " 4#5", "4#5 ", "04#5"])
def test_a_malformed_ref_is_refused(bad):
    with pytest.raises(ValueError, match="--review-ref"):
        rec.review_ref_event(bad, "claude")


def _argv(monkeypatch, *extra, tier="standard", events=None):
    import json
    base = ["record_hand_orchestrated_closure.py", "--ticket-id", "TCK-20261031-NO-SUCH-TICKET", "--tier", tier,
            "--title", "t", "--log-summary", "s", "--events", json.dumps(events or NARRATED)]
    monkeypatch.setattr(sys, "argv", base + list(extra))


def test_a_hotfix_close_with_a_ref_is_refused_before_anything_is_written(monkeypatch, capsys):
    _argv(monkeypatch, "--review-ref", "804#1", "--path-reason", "small_change", tier="hotfix")
    with pytest.raises(SystemExit) as exit_info:
        rec.main()
    assert exit_info.value.code == 1
    assert "no Review step" in capsys.readouterr().err


def test_a_ref_next_to_a_narrated_review_is_refused(monkeypatch, capsys):
    narrated = NARRATED + [{"phase": "Review", "status": "ok", "summary": "mine"}]
    _argv(monkeypatch, "--review-ref", "804#1", "--path-reason", "small_change", events=narrated)
    with pytest.raises(SystemExit) as exit_info:
        rec.main()
    assert exit_info.value.code == 1
    assert "narrated" in capsys.readouterr().err


def test_a_malformed_ref_on_the_command_line_is_refused(monkeypatch, capsys):
    _argv(monkeypatch, "--review-ref", "804", "--path-reason", "small_change")
    with pytest.raises(SystemExit) as exit_info:
        rec.main()
    assert exit_info.value.code == 1
    assert "<PR number>#<comment id>" in capsys.readouterr().err
