"""Tests for tools/agent-monitoring/scope_ticket_relocate.py and the orchestrator wiring in
.claude/workflows/implement-ticket.js (TCK-20260711-EPIC-SCOPE-ORPHAN-FIX).

Covers: the epic-tier move (copy-then-delete) vs. standard/hotfix copy-only behavior, the
load-bearing placement of the new orchestrator bash() call relative to captureTs()/agent(), and
the removal of the old unconditional-copy prompt text.
"""
import sys
from pathlib import Path

_MONITORING_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from scope_ticket_relocate import resolve_and_relocate_ticket  # noqa: E402

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_JS = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"


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
    done_dir = tmp_path / "done"
    inprogress_dir.mkdir(parents=True)
    todos_dir.mkdir(parents=True)
    done_dir.mkdir(parents=True)
    return inprogress_dir, todos_dir, done_dir


# ---------------------------------------------------------------------------
# 1. Placement guard — the new bash() call must precede captureTs(), never sit
#    between it and agent(), which would break test_step0_ts_orchestrator.py's
#    exact literal-adjacency assertion.
# ---------------------------------------------------------------------------


def test_step1c_orphan_bash_precedes_capturets():
    source = _IMPLEMENT_TICKET_JS.read_text(encoding="utf-8")

    adjacency = "const scopeTs = await captureTs()\nconst ticketInfo = await agent("
    assert adjacency in source

    orphan_call_index = source.index("resolveScopeTicketLocation(ticketId)")
    capture_ts_index = source.index(adjacency)
    assert orphan_call_index < capture_ts_index, (
        "resolveScopeTicketLocation(ticketId) must be called before captureTs(), "
        "never inserted between captureTs() and agent()"
    )


# ---------------------------------------------------------------------------
# 2. Epic-tier move — copy-then-delete, exactly one on-disk copy afterward.
# ---------------------------------------------------------------------------


def test_epic_tier_move_deletes_todos_original(tmp_path):
    inprogress_dir, todos_dir, done_dir = _make_dirs(tmp_path)
    folder = todos_dir / "some-epic-folder"
    folder.mkdir()
    todos_path = folder / "TCK-20260711-SOME-EPIC.md"
    _write_ticket(todos_path, "TCK-20260711-SOME-EPIC", "epic")

    result = resolve_and_relocate_ticket("TCK-20260711-SOME-EPIC", inprogress_dir, todos_dir, done_dir)

    assert result["action"] == "moved_from_todos"
    assert result["tier"] == "epic"
    assert (inprogress_dir / "TCK-20260711-SOME-EPIC.md").exists()
    assert not todos_path.exists()
    assert result["ticket_path"] == str(inprogress_dir / "TCK-20260711-SOME-EPIC.md")
    assert result["todos_source_path"] == str(todos_path)


# ---------------------------------------------------------------------------
# 3. Standard/hotfix tier — copy-only, todos original preserved.
# ---------------------------------------------------------------------------


def test_standard_hotfix_tier_still_copy_only(tmp_path):
    for tier in ("standard", "hotfix"):
        inprogress_dir, todos_dir, done_dir = _make_dirs(tmp_path / tier)
        folder = todos_dir / "some-folder"
        folder.mkdir()
        ticket_id = f"TCK-20260711-{tier.upper()}-TICKET"
        todos_path = folder / f"{ticket_id}.md"
        _write_ticket(todos_path, ticket_id, tier)

        result = resolve_and_relocate_ticket(ticket_id, inprogress_dir, todos_dir, done_dir)

        assert result["action"] == "copied_from_todos"
        assert result["tier"] == tier
        assert (inprogress_dir / f"{ticket_id}.md").exists()
        assert todos_path.exists(), f"todos original must be preserved for tier={tier}"


# ---------------------------------------------------------------------------
# 4. Already-located cases and not-found.
# ---------------------------------------------------------------------------


def test_already_in_inprogress_is_not_touched(tmp_path):
    inprogress_dir, todos_dir, done_dir = _make_dirs(tmp_path)
    _write_ticket(inprogress_dir / "TCK-20260711-X.md", "TCK-20260711-X", "standard")

    result = resolve_and_relocate_ticket("TCK-20260711-X", inprogress_dir, todos_dir, done_dir)

    assert result["action"] == "already_in_inprogress"
    assert result["todos_source_path"] == ""


def test_already_in_done_is_not_touched(tmp_path):
    inprogress_dir, todos_dir, done_dir = _make_dirs(tmp_path)
    _write_ticket(done_dir / "TCK-20260711-Y.md", "TCK-20260711-Y", "standard")

    result = resolve_and_relocate_ticket("TCK-20260711-Y", inprogress_dir, todos_dir, done_dir)

    assert result["action"] == "already_in_done"
    assert result["todos_source_path"] == ""


def test_not_found_returns_empty_fields(tmp_path):
    inprogress_dir, todos_dir, done_dir = _make_dirs(tmp_path)

    result = resolve_and_relocate_ticket("TCK-20260711-NOWHERE", inprogress_dir, todos_dir, done_dir)

    assert result["action"] == "not_found"
    assert result["ticket_path"] == ""
    assert result["tier"] == ""
    assert result["todos_source_path"] == ""


# ---------------------------------------------------------------------------
# 5. Prompt text no longer unconditionally copies; pre-computed facts stated.
# ---------------------------------------------------------------------------


def test_ticket_scoper_prompt_no_longer_unconditionally_copies():
    source = _IMPLEMENT_TICKET_JS.read_text(encoding="utf-8")

    assert (
        'Copy it to tickets/inprogress/${ticketId}.md so it enters the standard workflow location'
        not in source
    )
    assert "scopeOrphanInfo.ticket_path" in source
    assert "scopeOrphanInfo.tier" in source
    assert "scopeOrphanInfo.todos_source_path" in source
