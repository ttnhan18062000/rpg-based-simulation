"""tools/sessions/reset_boundary.py and the seat-suffix pin (TCK-20261015-SESSION-LAYER-MEASURES-SEAT-SUFFIX-RESET-RECORD-NOTE-CAP)."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REAL_ROOT = Path(__file__).resolve().parents[2]
if str(REAL_ROOT) not in sys.path:
    sys.path.insert(0, str(REAL_ROOT))

from tools.sessions import boundary as bd  # noqa: E402
from tools.sessions import reset_boundary as rb  # noqa: E402
from tools.sessions.roster import load_roster  # noqa: E402

ROSTER = load_roster(REAL_ROOT)


def test_declare_writes_exactly_one_row_with_the_documented_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "sess-1")
    monkeypatch.setenv("SESSION_ROLE", "agent-working-implementer")
    assert rb.main(["declare", "--kind", "HARD", "--row", "a ticket closed", "--data-dir", str(tmp_path)]) == 0
    (path,) = list(tmp_path.glob("*/reset_boundary.jsonl"))
    (row,) = [json.loads(x) for x in path.read_text().splitlines()]
    assert set(row) == {"ts", "session_id", "session_role", "kind", "row", "handover_rel", "handover_sha256"}
    assert (row["kind"], row["row"], row["session_id"], row["session_role"]) == ("HARD", "a ticket closed", "sess-1", "agent-working-implementer")
    assert row["handover_rel"] == ".claude/handover/agent-working-implementer.md"
    assert path.parent.name == datetime.now(timezone.utc).strftime("%G-W%V")


def test_an_instance_gets_its_own_handover_path_and_a_bad_kind_is_refused(tmp_path, monkeypatch, capsys):
    row = rb.build_row("SOFT", "x", "s", "rpg-implementer-2", REAL_ROOT)
    assert row["handover_rel"] == ".claude/handover/rpg-implementer-2.md" and row["session_role"] == "rpg-implementer-2"
    import pytest

    with pytest.raises(SystemExit):
        rb.main(["declare", "--kind", "MAYBE", "--row", "x"])


def test_declare_never_fails_its_caller(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rb, "build_row", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert rb.main(["declare", "--kind", "HARD", "--row", "x", "--data-dir", str(tmp_path)]) == 0
    assert "not recorded" in capsys.readouterr().out


def test_advisory_for_clear_is_pure_and_names_the_two_cases():
    hard = {"session_id": "p", "kind": "HARD", "ts": "T1", "handover_sha256": "aaa"}
    assert rb.advisory_for_clear([], "p", "aaa", "r") and "no HARD" in rb.advisory_for_clear([], "p", "aaa", "r")
    assert rb.advisory_for_clear([{**hard, "kind": "SOFT"}], "p", "aaa", "r")          # a SOFT is not a HARD
    assert rb.advisory_for_clear([{**hard, "session_id": "other"}], "p", "aaa", "r")   # someone else's HARD does not count
    assert rb.advisory_for_clear([hard], "p", "aaa", "r") is None
    assert "changed after" in rb.advisory_for_clear([hard], "p", "bbb", "r")
    assert rb.advisory_for_clear([hard], "p", None, "r") is None                        # no note to compare: say nothing


def test_read_rows_skips_bad_lines_and_a_missing_directory(tmp_path):
    assert rb.read_rows(tmp_path, tmp_path / "nope") == []
    p = tmp_path / "2026-W42" / "reset_boundary.jsonl"
    p.parent.mkdir()
    p.write_text('{"kind":"HARD"}\nnot json\n[1]\n')
    assert rb.read_rows(tmp_path, tmp_path) == [{"kind": "HARD"}]


# --- the seat suffix: a host seat maps to its base role through the registry -------------------------------------

def _edit(role_id, rel):
    role = ROSTER.role(role_id)
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(REAL_ROOT / rel)}, "cwd": str(REAL_ROOT)}
    return bd.check_edit(payload, role, ROSTER)


def test_the_host_seat_resolves_to_its_base_roles_owner_seats_and_its_own_page_is_not_flagged():
    flagged = _edit("lead-planner-u24", "agent-working/lead/board.md")
    assert flagged and flagged[2]["owner_seats"] == ["lead-planner"]   # the base seat, found by the registry
    assert _edit("lead-planner-u24", "agent-working/lead/hosts/u24desktop.md") is None
    back = _edit("lead-planner", "agent-working/lead/hosts/u24desktop.md")
    assert back and back[2]["owner_seats"] == ["lead-planner-u24"]     # and the other way round
    assert _edit("lead-planner", "agent-working/lead/board.md") is None


def test_a_numbered_instance_is_the_same_seat_as_its_base_role():
    assert bd._base_role("rpg-implementer-2", ROSTER).role == "rpg-implementer"
    assert bd._base_role("lead-planner-u24", ROSTER).role == "lead-planner-u24"   # a registered seat is never string-stripped
