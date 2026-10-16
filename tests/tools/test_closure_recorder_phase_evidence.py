"""TCK-20261015-CLOSURE-RECORDER-PHASE-EVIDENCE-AND-PARITY-SKIP-REASON: phases that left artifacts are recorded as ran,
a skipped Parity on a src/ change needs a structured reason, and the retro shows ledger blocks beside run gate failures."""
import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[2] / "tools" / "agent-monitoring"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import generate_retro  # noqa: E402
import record_hand_orchestrated_closure as rec  # noqa: E402

TID = "TCK-20261015-X"


def _artifacts(tmp_path, *names, root="stored_artifacts"):
    folder = tmp_path / root / TID
    folder.mkdir(parents=True)
    for n in names:
        (folder / n).write_text("# x\n")
    return (tmp_path / "stored_artifacts", tmp_path / "staging_artifacts")


# --- phase evidence ------------------------------------------------------------------------------------------------

def test_a_standard_ticket_with_artifacts_records_investigate_and_plan_as_ran(tmp_path):
    roots = _artifacts(tmp_path, "investigation.md", "plan.md", "test_plan.md")
    derived = rec.evidence_phase_events(TID, "standard", [{"phase": "Scope"}, {"phase": "Implement"}], "claude", roots)
    assert [e["phase"] for e in derived] == ["Investigate", "Plan"]
    assert all(e["status"] == "ok" and e["agent"] == "claude" for e in derived)
    assert f"stored_artifacts/{TID}/investigation.md" in derived[0]["summary"] and "not narrated" in derived[0]["summary"]


def test_without_artifacts_the_phases_stay_absent_so_phases_omitted_names_the_real_gap(tmp_path):
    roots = (tmp_path / "stored_artifacts", tmp_path / "staging_artifacts")
    assert rec.evidence_phase_events(TID, "standard", [{"phase": "Scope"}], "claude", roots) == []


def test_staging_artifacts_count_too_and_one_file_gives_one_phase(tmp_path):
    folder = tmp_path / "staging_artifacts" / TID
    folder.mkdir(parents=True)
    (folder / "investigation.md").write_text("# x\n")
    derived = rec.evidence_phase_events(TID, "epic", [], "claude", (tmp_path / "stored_artifacts", tmp_path / "staging_artifacts"))
    assert [e["phase"] for e in derived] == ["Investigate"]


def test_a_phase_the_closer_already_gave_is_not_duplicated_and_hotfix_derives_nothing(tmp_path):
    roots = _artifacts(tmp_path, "investigation.md", "plan.md")
    given = [{"phase": "Investigate"}, {"phase": "Plan"}]
    assert rec.evidence_phase_events(TID, "standard", given, "claude", roots) == []
    assert rec.evidence_phase_events(TID, "hotfix", [], "claude", roots) == []


def test_derived_events_remove_the_phases_from_phases_omitted(tmp_path):
    roots = _artifacts(tmp_path, "investigation.md", "plan.md")
    events = [{"phase": "Scope", "status": "ok", "summary": "s"}, {"phase": "Implement", "status": "ok", "summary": "i"}]
    with_evidence = events[:1] + rec.evidence_phase_events(TID, "standard", events, "claude", roots) + events[1:]
    omitted_before = rec.compute_phases_omitted("standard", [e["phase"] for e in events])
    omitted_after = rec.compute_phases_omitted("standard", [e["phase"] for e in with_evidence])
    assert omitted_before is not None and "Investigate" in omitted_before and "Plan" in omitted_before
    assert "Investigate" not in omitted_after and "Plan" not in omitted_after


# --- the Parity skip reason ----------------------------------------------------------------------------------------

def _parity(status="skipped", **extra):
    return [{"phase": "Parity", "status": status, "summary": "n/a", **extra}]


def test_a_skipped_parity_on_a_src_change_without_an_enum_reason_is_refused():
    err = rec.parity_skipped_without_enum_reason(_parity(), {"src/engine/x.py", "tests/a.py"})
    assert err and "skip_reason" in err and "condition_false" in err
    assert rec.parity_skipped_without_enum_reason(_parity(skip_reason="unstated"), {"src/x.py"})


def test_an_enum_reason_a_non_src_change_or_an_ok_parity_is_accepted():
    assert rec.parity_skipped_without_enum_reason(_parity(skip_reason="condition_false"), {"src/x.py"}) is None
    assert rec.parity_skipped_without_enum_reason(_parity(), {"tools/x.py", "docs/a.md"}) is None
    assert rec.parity_skipped_without_enum_reason(_parity("ok"), {"src/x.py"}) is None
    assert rec.parity_skipped_without_enum_reason([{"phase": "Verify", "status": "skipped", "summary": "s"}], {"src/x.py"}) is None


def test_a_reason_outside_the_vocabulary_is_refused_with_the_valid_list():
    err = rec.parity_skipped_without_enum_reason(_parity(skip_reason="because"), {"src/x.py"})
    assert err and "not one of" in err and "tier_plan" in err


# --- the retro Run Summary -----------------------------------------------------------------------------------------

def _run(rid):
    return {"run_id": rid, "ticket_id": rid, "start_ts": "2026-10-14T08:00:00Z", "end_ts": "2026-10-14T09:00:00Z",
            "workflow": "implement-ticket", "tier": "standard", "final_status": "DONE", "agent_count": 2,
            "execution_mode": "hand", "duration_s": 600}


def test_the_run_summary_shows_ledger_blocks_beside_zero_run_gate_failures():
    blocks = {"verdicts": 140, "blocking": 22, "unresolved": 3}
    text = generate_retro.generate([_run("A")], [], "2026-W42", week_str="2026-W42", ledger_blocks=blocks)
    assert "| Gate failures | 0 |" in text
    assert "| Blocking gate verdicts (ledger) | 22 of 140 verdicts (3 without a recorded outcome) |" in text


def test_without_a_ledger_reading_the_run_summary_is_unchanged():
    text = generate_retro.generate([_run("A")], [], "2026-W42", week_str="2026-W42")
    assert "Blocking gate verdicts" not in text and "| Gate failures | 0 |" in text


def test_the_run_summary_shows_a_declarations_count_including_zero():
    text = generate_retro.generate([_run("A")], [], "2026-W42", week_str="2026-W42",
                                   reset_declarations={"total": 0, "HARD": 0, "SOFT": 0, "NEVER": 0})
    assert "| Reset-boundary declarations | 0 (HARD 0, SOFT 0, NEVER 0) |" in text
    assert "Reset-boundary declarations" not in generate_retro.generate([_run("A")], [], "2026-W41", week_str="2026-W41")
    assert generate_retro._reset_declarations("2026-W41") is None
