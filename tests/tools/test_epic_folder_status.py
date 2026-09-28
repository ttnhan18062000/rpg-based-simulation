"""Tests for tools/epic_folder_status.py (TCK-20260928-EPIC-FOLDER-ARCHIVE-BLOCKED-BY-EPIC-PARENT).

Shared by both `.claude/workflows/implement-epic.js`'s folder-cleanup block and
`.claude/workflows/implement-ticket.js`'s Finalize step 3 (see test_implement_epic_close_step.py
and test_finalize_epic_parent_advisory_pin.py for those callers' own raw-source-text pins) --
this file covers the actual Python logic directly.
"""

import json
import subprocess
import sys
from pathlib import Path

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from epic_folder_status import get_epic_folder_status, main  # noqa: E402


def _write_ticket(path: Path, ticket_id: str, tier: str, status: str) -> Path:
    path.write_text(
        f"---\nstatus: active\nlayer: ai\nauthority: P1\naudience: agent\n"
        f"ticket_id: {ticket_id}\nphase: open\ndate: 2026-01-01\ntags: []\n---\n\n"
        f"# {ticket_id}\n\n## Title\nFixture\n\n## Status\n{status}\n\n## Tier\n{tier}\n"
    )
    return path


def test_epic_parent_only_case_reports_all_children_done_and_no_open_children(tmp_path):
    folder = tmp_path / "tickets" / "todos" / "myepic"
    done_dir = tmp_path / "tickets" / "done"
    folder.mkdir(parents=True)
    done_dir.mkdir(parents=True)

    _write_ticket(folder / "TCK-1-EPIC.md", "TCK-1-EPIC", "epic", "EPIC_SCOPED")
    _write_ticket(folder / "TCK-2-CHILD.md", "TCK-2-CHILD", "hotfix", "DONE")
    (done_dir / "TCK-2-CHILD.md").touch()

    result = get_epic_folder_status(folder, done_dir)

    assert result["epic_parent"] == str(folder / "TCK-1-EPIC.md")
    assert result["epic_parent_ticket_id"] == "TCK-1-EPIC"
    assert result["open_children"] == []
    assert result["all_children_done"] is True


def test_one_open_child_reports_all_children_done_false(tmp_path):
    folder = tmp_path / "tickets" / "todos" / "myepic"
    done_dir = tmp_path / "tickets" / "done"
    folder.mkdir(parents=True)
    done_dir.mkdir(parents=True)

    _write_ticket(folder / "TCK-1-EPIC.md", "TCK-1-EPIC", "epic", "EPIC_SCOPED")
    _write_ticket(folder / "TCK-2-CHILD.md", "TCK-2-CHILD", "hotfix", "OPEN")
    # TCK-2-CHILD is NOT in done_dir -- still open.

    result = get_epic_folder_status(folder, done_dir)

    assert result["epic_parent_ticket_id"] == "TCK-1-EPIC"
    assert result["open_children"] == ["TCK-2-CHILD"]
    assert result["all_children_done"] is False


def test_non_epic_folder_with_no_parent(tmp_path):
    folder = tmp_path / "tickets" / "todos" / "plainbatch"
    done_dir = tmp_path / "tickets" / "done"
    folder.mkdir(parents=True)
    done_dir.mkdir(parents=True)

    _write_ticket(folder / "TCK-1.md", "TCK-1", "hotfix", "DONE")
    (done_dir / "TCK-1.md").touch()

    result = get_epic_folder_status(folder, done_dir)

    assert result["epic_parent"] is None
    assert result["epic_parent_ticket_id"] is None
    assert result["open_children"] == []
    assert result["all_children_done"] is True


def test_epic_identified_by_tier_body_field_not_filename_no_epic_string_in_epic_filename(tmp_path):
    folder = tmp_path / "tickets" / "todos" / "myepic"
    done_dir = tmp_path / "tickets" / "done"
    folder.mkdir(parents=True)
    done_dir.mkdir(parents=True)

    # Real epic, filename deliberately has no "-EPIC-" substring.
    _write_ticket(folder / "TCK-1-FOUNDATION.md", "TCK-1-FOUNDATION", "epic", "EPIC_SCOPED")
    result = get_epic_folder_status(folder, done_dir)
    assert result["epic_parent_ticket_id"] == "TCK-1-FOUNDATION", (
        "a real epic-tier ticket must be found via its ## Tier field even without '-EPIC-' in its name"
    )


def test_epic_identified_by_tier_body_field_not_filename_false_positive_filename(tmp_path):
    folder = tmp_path / "tickets" / "todos" / "myfolder"
    done_dir = tmp_path / "tickets" / "done"
    folder.mkdir(parents=True)
    done_dir.mkdir(parents=True)

    # Non-epic ticket whose filename happens to contain "-EPIC-".
    _write_ticket(folder / "TCK-1-EPIC-THEMED-QUEST.md", "TCK-1-EPIC-THEMED-QUEST", "hotfix", "OPEN")
    result = get_epic_folder_status(folder, done_dir)
    assert result["epic_parent"] is None, (
        "a non-epic ticket must not be misclassified as the epic parent just because '-EPIC-' "
        "appears in its filename"
    )
    assert result["open_children"] == ["TCK-1-EPIC-THEMED-QUEST"]


def test_cli_prints_json_to_stdout_and_exits_zero(tmp_path, capsys):
    folder = tmp_path / "tickets" / "todos" / "myepic"
    done_dir = tmp_path / "tickets" / "done"
    folder.mkdir(parents=True)
    done_dir.mkdir(parents=True)
    _write_ticket(folder / "TCK-1-EPIC.md", "TCK-1-EPIC", "epic", "EPIC_SCOPED")

    exit_code = main([str(folder), "--done-dir", str(done_dir)])

    assert exit_code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["epic_parent_ticket_id"] == "TCK-1-EPIC"
    assert out["all_children_done"] is True


def test_cli_real_subprocess_invocation(tmp_path):
    # At least one real subprocess invocation, matching how the workflow prompts actually call
    # this script (`python3 tools/epic_folder_status.py <folder>`), not just an in-process main().
    folder = tmp_path / "tickets" / "todos" / "myepic"
    done_dir = tmp_path / "tickets" / "done"
    folder.mkdir(parents=True)
    done_dir.mkdir(parents=True)
    _write_ticket(folder / "TCK-1-EPIC.md", "TCK-1-EPIC", "epic", "EPIC_SCOPED")

    script = _TOOLS_DIR / "epic_folder_status.py"
    result = subprocess.run(
        [sys.executable, str(script), str(folder), "--done-dir", str(done_dir)],
        capture_output=True, text=True, timeout=30,
    )

    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["epic_parent_ticket_id"] == "TCK-1-EPIC"
    assert out["all_children_done"] is True


def test_default_done_dir_is_sibling_tickets_done(tmp_path):
    # No --done-dir override: default resolves to <folder>/../../done (tickets/done/ as a sibling
    # of tickets/todos/), matching the real repo layout.
    folder = tmp_path / "tickets" / "todos" / "myepic"
    done_dir = tmp_path / "tickets" / "done"
    folder.mkdir(parents=True)
    done_dir.mkdir(parents=True)
    _write_ticket(folder / "TCK-1-EPIC.md", "TCK-1-EPIC", "epic", "EPIC_SCOPED")
    _write_ticket(folder / "TCK-2-CHILD.md", "TCK-2-CHILD", "hotfix", "DONE")
    (done_dir / "TCK-2-CHILD.md").touch()

    result = get_epic_folder_status(folder, folder.parent.parent / "done")

    assert result["all_children_done"] is True
