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
