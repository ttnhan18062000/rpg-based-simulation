"""Tests for tools/agent-monitoring/epic_scope_orphan_check.py (TCK-20260711-EPIC-SCOPE-ORPHAN-FIX).

The check flags the actual orphan signature — an epic-tier ticket present in both
tickets/inprogress/ and tickets/todos/** simultaneously — not merely "epic ticket resting in
inprogress/" (legitimate, per docs/ai/ticket-lifecycle.md:440) and not non-epic dual presence
(the normal, expected mid-workflow state pending Finalize reconciliation).
"""
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
_MONITORING_TOOLS_DIR = _TOOLS_DIR / "agent-monitoring"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from epic_scope_orphan_check import (  # noqa: E402
    check_single_epic_orphan,
    scan_epic_scope_orphans,
)
from gate_checks.done_checker_static import (  # noqa: E402
    check_ticket_finalized,
    check_ticket_location,
)

_REPO_ROOT = Path(__file__).parent.parent.parent
REAL_INPROGRESS_DIR = _REPO_ROOT / "tickets" / "inprogress"
REAL_TODOS_DIR = _REPO_ROOT / "tickets" / "todos"


def _write_ticket(path: Path, ticket_id: str, tier: str):
    path.write_text(
        "---\n"
        "status: active\n"
        "layer: ai\n"
        f"ticket_id: {ticket_id}\n"
        "date: 2026-07-11\n"
        "---\n\n"
        f"# {ticket_id}\n\n"
        f"## Tier\n{tier}\n\n"
        "## Related Tickets\nnone\n"
    )


def _make_dirs(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    todos_dir = tmp_path / "todos"
    inprogress_dir.mkdir()
    todos_dir.mkdir()
    return inprogress_dir, todos_dir


# ---------------------------------------------------------------------------
# 1. Flags dual presence (the actual orphan signature).
# ---------------------------------------------------------------------------


def test_new_orphan_check_flags_dual_presence(tmp_path):
    inprogress_dir, todos_dir = _make_dirs(tmp_path)
    ticket_id = "TCK-20260711-DUAL-EPIC"
    _write_ticket(inprogress_dir / f"{ticket_id}.md", ticket_id, "epic")
    folder = todos_dir / "dual-epic-folder"
    folder.mkdir()
    _write_ticket(folder / f"{ticket_id}.md", ticket_id, "epic")

    results = scan_epic_scope_orphans(inprogress_dir, todos_dir)

    assert len(results) == 1
    assert results[0]["ticket_id"] == ticket_id
    assert results[0]["status"] == "FAIL"
    assert str(inprogress_dir / f"{ticket_id}.md") in results[0]["evidence"]
    assert str(folder / f"{ticket_id}.md") in results[0]["evidence"]


# ---------------------------------------------------------------------------
# 2. Passes when the todos original is absent.
# ---------------------------------------------------------------------------


def test_new_orphan_check_passes_when_todos_original_absent(tmp_path):
    inprogress_dir, todos_dir = _make_dirs(tmp_path)
    ticket_id = "TCK-20260711-NO-DUAL-EPIC"
    _write_ticket(inprogress_dir / f"{ticket_id}.md", ticket_id, "epic")

    results = scan_epic_scope_orphans(inprogress_dir, todos_dir)

    assert len(results) == 1
    assert results[0]["status"] == "PASS"


# ---------------------------------------------------------------------------
# 3. Does not flag an epic legitimately resting in inprogress/ with no todos
#    original — the documented, normal epic_id-mode resting state.
# ---------------------------------------------------------------------------


def test_new_orphan_check_does_not_flag_legitimate_epic_resting_in_inprogress(tmp_path):
    inprogress_dir, todos_dir = _make_dirs(tmp_path)
    ticket_id = "TCK-20260711-RESTING-EPIC"
    _write_ticket(inprogress_dir / f"{ticket_id}.md", ticket_id, "epic")

    status, _ = check_single_epic_orphan(ticket_id, inprogress_dir / f"{ticket_id}.md", todos_dir)

    assert status == "PASS"


# ---------------------------------------------------------------------------
# 4. Ignores non-epic dual presence — normal mid-workflow state for
#    hotfix/standard tickets pending Finalize.
# ---------------------------------------------------------------------------


def test_new_orphan_check_ignores_non_epic_dual_presence(tmp_path):
    inprogress_dir, todos_dir = _make_dirs(tmp_path)
    ticket_id = "TCK-20260711-STANDARD-MIDFLIGHT"
    _write_ticket(inprogress_dir / f"{ticket_id}.md", ticket_id, "standard")
    folder = todos_dir / "standard-folder"
    folder.mkdir()
    _write_ticket(folder / f"{ticket_id}.md", ticket_id, "standard")

    results = scan_epic_scope_orphans(inprogress_dir, todos_dir)

    assert results == []


# ---------------------------------------------------------------------------
# 5. Live-repo AC #4 check — the sweep returns zero orphans against real state.
# ---------------------------------------------------------------------------


def test_live_repo_orphan_check_returns_zero_findings():
    results = scan_epic_scope_orphans(REAL_INPROGRESS_DIR, REAL_TODOS_DIR)

    failing = [r for r in results if r["status"] == "FAIL"]
    assert failing == [], f"unexpected live orphan(s): {failing}"


# ---------------------------------------------------------------------------
# 6. done_checker_static.py's existing signatures/shapes are untouched.
# ---------------------------------------------------------------------------


def test_check_ticket_location_and_finalized_signatures_unchanged(tmp_path):
    inprogress_dir = tmp_path / "inprogress"
    inprogress_dir.mkdir()
    (inprogress_dir / "TCK-20260711-SHAPE.md").write_text("placeholder")

    status, evidence = check_ticket_location("TCK-20260711-SHAPE", inprogress_dir)
    assert (status, isinstance(evidence, str)) == ("PASS", True)

    status, evidence = check_ticket_location("TCK-20260711-MISSING", inprogress_dir)
    assert (status, isinstance(evidence, str)) == ("FAIL", True)

    status, evidence = check_ticket_finalized("TCK-20260711-DOES-NOT-EXIST-ANYWHERE")
    assert status == "FAIL"
    assert isinstance(evidence, str)
