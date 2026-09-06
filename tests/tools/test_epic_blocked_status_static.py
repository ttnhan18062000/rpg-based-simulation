"""Tests for tools/gate_checks/epic_blocked_status_static.py (TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS).

Doubles as the real, deterministic demonstration this ticket's own ACs ask for: a synthetic
folder (or scattered epic_id-mode child tickets) containing one normal ticket and one
`## Status: BLOCKED` ticket must produce a `blocked` list that names the blocked one and excludes
it, with a normal (all-non-blocked) batch's result unaffected.
"""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.epic_blocked_status_static import (  # noqa: E402
    find_blocked_ticket_ids,
    find_ticket_path,
    read_ticket_status,
)


def _write_ticket(path: Path, status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\nstatus: active\nlayer: ai\nauthority: P2\naudience: agent\n"
        f"ticket_id: {path.stem}\nphase: open\ndate: 2026-09-04\ntags: []\n---\n\n"
        f"# {path.stem}\n\n## Title\nTest ticket\n\n## Status\n{status}\n\n## Tier\nhotfix\n"
    )


class TestReadTicketStatus:
    def test_reads_real_status_value(self, tmp_path):
        path = tmp_path / "TCK-A.md"
        _write_ticket(path, "BLOCKED")
        assert read_ticket_status(path) == "BLOCKED"

    def test_normalizes_case(self, tmp_path):
        path = tmp_path / "TCK-A.md"
        _write_ticket(path, "blocked")
        assert read_ticket_status(path) == "BLOCKED"

    def test_returns_empty_for_missing_file(self, tmp_path):
        assert read_ticket_status(tmp_path / "TCK-NONEXISTENT.md") == ""

    def test_returns_empty_when_no_status_section(self, tmp_path):
        path = tmp_path / "TCK-A.md"
        path.write_text("# TCK-A\n\n## Title\nNo status section here\n")
        assert read_ticket_status(path) == ""

    def test_open_status_is_not_blocked(self, tmp_path):
        path = tmp_path / "TCK-A.md"
        _write_ticket(path, "OPEN")
        assert read_ticket_status(path) == "OPEN"


class TestFindTicketPath:
    def test_finds_direct_child(self, tmp_path):
        path = tmp_path / "TCK-A.md"
        _write_ticket(path, "OPEN")
        assert find_ticket_path("TCK-A", [str(tmp_path)]) == str(path)

    def test_finds_one_level_subfolder(self, tmp_path):
        path = tmp_path / "some-batch" / "TCK-A.md"
        _write_ticket(path, "OPEN")
        assert find_ticket_path("TCK-A", [str(tmp_path)]) == str(path)

    def test_returns_none_when_not_found_under_any_root(self, tmp_path):
        assert find_ticket_path("TCK-MISSING", [str(tmp_path)]) is None

    def test_first_matching_root_wins(self, tmp_path):
        root_a, root_b = tmp_path / "a", tmp_path / "b"
        path_a = root_a / "TCK-A.md"
        _write_ticket(path_a, "BLOCKED")
        _write_ticket(root_b / "TCK-A.md", "OPEN")
        assert find_ticket_path("TCK-A", [str(root_a), str(root_b)]) == str(path_a)


class TestFindBlockedTicketIds:
    def test_synthetic_folder_excludes_and_names_the_blocked_ticket(self, tmp_path):
        """The exact scenario this ticket's own AC #3 describes: one normal ticket, one
        ## Status: BLOCKED ticket, in the same folder."""
        _write_ticket(tmp_path / "TCK-NORMAL.md", "OPEN")
        _write_ticket(tmp_path / "TCK-BLOCKED.md", "BLOCKED")

        blocked = find_blocked_ticket_ids(["TCK-NORMAL", "TCK-BLOCKED"], [str(tmp_path)])

        assert blocked == ["TCK-BLOCKED"]
        assert "TCK-NORMAL" not in blocked

    def test_epic_id_mode_scattered_children_across_multiple_search_roots(self, tmp_path):
        """AC #4: the epic_id-mode code path (children scattered across tickets/inprogress/,
        tickets/todos/, tickets/done/, not a single folder) gets the equivalent fix."""
        inprogress = tmp_path / "inprogress"
        todos = tmp_path / "todos"
        _write_ticket(inprogress / "TCK-INPROGRESS-NORMAL.md", "INPROGRESS")
        _write_ticket(todos / "some-batch" / "TCK-TODOS-BLOCKED.md", "BLOCKED")

        blocked = find_blocked_ticket_ids(
            ["TCK-INPROGRESS-NORMAL", "TCK-TODOS-BLOCKED"],
            [str(inprogress), str(todos)],
        )

        assert blocked == ["TCK-TODOS-BLOCKED"]

    def test_normal_batch_with_no_blocked_tickets_returns_empty_unchanged_behavior(self, tmp_path):
        """AC #5: a normal (non-blocked) folder's behavior is unchanged."""
        _write_ticket(tmp_path / "TCK-A.md", "OPEN")
        _write_ticket(tmp_path / "TCK-B.md", "INPROGRESS")

        assert find_blocked_ticket_ids(["TCK-A", "TCK-B"], [str(tmp_path)]) == []

    def test_preserves_input_order(self, tmp_path):
        _write_ticket(tmp_path / "TCK-A.md", "BLOCKED")
        _write_ticket(tmp_path / "TCK-B.md", "BLOCKED")
        _write_ticket(tmp_path / "TCK-C.md", "OPEN")

        assert find_blocked_ticket_ids(["TCK-C", "TCK-B", "TCK-A"], [str(tmp_path)]) == ["TCK-B", "TCK-A"]

    def test_unresolvable_ticket_id_is_not_silently_flagged_blocked(self, tmp_path):
        """A ticket_id that can't be resolved to a real file must never be reported as blocked --
        that would be a fabricated status, not a real one."""
        assert find_blocked_ticket_ids(["TCK-DOES-NOT-EXIST"], [str(tmp_path)]) == []
