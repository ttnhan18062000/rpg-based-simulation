"""Tests for TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE and
TCK-20261005-CLOSE-LEAVES-STALE-TODOS-COPY-FOR-DIRECTLY-FILED-TICKETS.

The registry indexes only files git tracks or has staged, plus explicitly included paths (the closing ticket), so an
untracked draft never reaches it and local `--check` agrees with CI; a closed ticket's stale `todos/` copy fails the
finalize check and is removed by the closure tool.
"""
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.agent_working_paths import STORED_ARTIFACTS, TICKETS

_TOOLS = Path(__file__).parent.parent.parent / "tools"
for p in (_TOOLS, _TOOLS / "agent-monitoring"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import generate_registry as gr  # noqa: E402
import record_hand_orchestrated_closure as closure  # noqa: E402
from gate_checks.done_checker_static import check_ticket_finalized  # noqa: E402

_FM = ("status: {status}\nlayer: engine\nauthority: P1\naudience: agent\nticket_id: {tid}\nphase: {phase}\n"
       "date: 2026-10-05\ntags: []")


def _ticket(root: Path, rel: str, tid: str, status="active", phase="open") -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{_FM.format(status=status, tid=tid, phase=phase)}\n---\n\n# {tid}\n", encoding="utf-8")
    return path


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t", *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _ticket(tmp_path, f"{TICKETS}/todos/TCK-20261005-TRACKED.md", "TCK-20261005-TRACKED")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "base")
    return tmp_path


def _paths(root: Path, **kw) -> set:
    out = root / "REG.yaml"
    gr.generate_registry(root, out, **kw)
    return {e["path"] for e in yaml.safe_load(out.read_text())}


UNTRACKED = f"{TICKETS}/todos/TCK-20261005-UNTRACKED-DRAFT.md"


def test_an_untracked_ticket_is_not_indexed_and_a_tracked_one_is(repo):
    _ticket(repo, UNTRACKED, "TCK-20261005-UNTRACKED-DRAFT")
    paths = _paths(repo)
    assert UNTRACKED not in paths and f"{TICKETS}/todos/TCK-20261005-TRACKED.md" in paths


def test_a_staged_file_is_indexed(repo):
    _ticket(repo, UNTRACKED, "TCK-20261005-UNTRACKED-DRAFT")
    _git(repo, "add", UNTRACKED)
    assert UNTRACKED in _paths(repo)


def test_an_untracked_doc_is_not_indexed(repo):
    doc = repo / "docs" / "x.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("---\nstatus: active\nlayer: engine\nauthority: P1\naudience: agent\ntags: []\n---\n\n# X\n")
    assert "docs/x.md" not in _paths(repo)


def test_the_closing_ticket_is_indexed_via_include_even_though_untracked(repo):
    done = f"{TICKETS}/done/TCK-20261005-CLOSING.md"
    _ticket(repo, done, "TCK-20261005-CLOSING", status="historical", phase="done")
    _ticket(repo, UNTRACKED, "TCK-20261005-UNTRACKED-DRAFT")
    paths = _paths(repo, include=[done])
    assert done in paths and UNTRACKED not in paths


def test_include_accepts_a_glob_for_a_nested_epic_ticket_and_a_directory(repo):
    nested = f"{TICKETS}/done/epic/TCK-20261005-CHILD.md"
    _ticket(repo, nested, "TCK-20261005-CHILD", status="historical", phase="done")
    assert nested in _paths(repo, include=[f"{TICKETS}/done/*/TCK-20261005-CHILD.md"])
    art = repo / STORED_ARTIFACTS / "TCK-20261005-CLOSING"
    art.mkdir(parents=True)
    (art / "plan.md").write_text("x")
    done = f"{TICKETS}/done/TCK-20261005-CLOSING.md"
    _ticket(repo, done, "TCK-20261005-CLOSING", status="historical", phase="done")
    out = repo / "R.yaml"
    gr.generate_registry(repo, out, include=[done, f"{STORED_ARTIFACTS}/TCK-20261005-CLOSING"])
    entry = next(e for e in yaml.safe_load(out.read_text()) if e["path"] == done)
    assert f"{STORED_ARTIFACTS}/TCK-20261005-CLOSING/plan.md" in entry["artifact_files"]


def test_untracked_artifact_files_are_dropped_from_a_tracked_tickets_list(repo):
    art = repo / STORED_ARTIFACTS / "TCK-20261005-TRACKED"
    art.mkdir(parents=True)
    (art / "plan.md").write_text("x")
    out = repo / "R.yaml"
    gr.generate_registry(repo, out)
    entry = next(e for e in yaml.safe_load(out.read_text()) if e["ticket_id"] == "TCK-20261005-TRACKED")
    assert not entry.get("artifact_files")


def test_a_non_git_root_is_indexed_as_before(tmp_path):
    _ticket(tmp_path, UNTRACKED, "TCK-20261005-UNTRACKED-DRAFT")
    assert gr.indexable_paths(tmp_path) is None and UNTRACKED in _paths(tmp_path)


def test_a_subdirectory_of_a_repo_is_not_filtered(repo):
    sub = repo / "export"
    _ticket(sub, UNTRACKED, "TCK-20261005-UNTRACKED-DRAFT")
    assert gr.indexable_paths(sub) is None


def test_check_mode_agrees_with_the_committed_tree_despite_an_untracked_draft(repo):
    out = repo / "docs" / "REGISTRY.yaml"
    gr.generate_registry(repo, out)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "registry")
    _ticket(repo, UNTRACKED, "TCK-20261005-UNTRACKED-DRAFT")
    assert gr.generate_registry(repo, out, check=True) == 0


def test_cli_include_untracked_flag(repo):
    done = f"{TICKETS}/done/TCK-20261005-CLOSING.md"
    _ticket(repo, done, "TCK-20261005-CLOSING", status="historical", phase="done")
    subprocess.run([sys.executable, str(_TOOLS / "generate_registry.py"), "--root", str(repo), "--output", "R.yaml",
                    "--include-untracked", done], check=True, capture_output=True)
    assert done in {e["path"] for e in yaml.safe_load((repo / "R.yaml").read_text())}


# ---- stale todos copy -------------------------------------------------------------------------

def _closed(root, tid="TCK-20261005-CLOSED"):
    _ticket(root, f"{TICKETS}/done/{tid}.md", tid, status="historical", phase="done")
    (root / TICKETS / "inprogress").mkdir(parents=True, exist_ok=True)


def test_finalize_fails_naming_a_stale_todos_copy_and_passes_without_it(tmp_path, monkeypatch):
    _closed(tmp_path)
    stale = _ticket(tmp_path, f"{TICKETS}/todos/TCK-20261005-CLOSED.md", "TCK-20261005-CLOSED")
    monkeypatch.chdir(tmp_path)
    status, evidence = check_ticket_finalized("TCK-20261005-CLOSED")
    assert status == "FAIL" and "stale copy" in evidence and "TCK-20261005-CLOSED.md" in evidence
    stale.unlink()
    assert check_ticket_finalized("TCK-20261005-CLOSED")[0] == "PASS"


def test_finalize_also_catches_a_copy_inside_a_todos_subfolder(tmp_path, monkeypatch):
    _closed(tmp_path)
    _ticket(tmp_path, f"{TICKETS}/todos/folder/TCK-20261005-CLOSED.md", "TCK-20261005-CLOSED")
    monkeypatch.chdir(tmp_path)
    assert check_ticket_finalized("TCK-20261005-CLOSED")[0] == "FAIL"


def test_an_unrelated_todos_ticket_does_not_fail_finalize(tmp_path, monkeypatch):
    _closed(tmp_path)
    _ticket(tmp_path, f"{TICKETS}/todos/TCK-20261005-OTHER.md", "TCK-20261005-OTHER")
    monkeypatch.chdir(tmp_path)
    assert check_ticket_finalized("TCK-20261005-CLOSED")[0] == "PASS"


def test_closure_tool_removes_the_stale_copies_only_for_a_closed_ticket(tmp_path):
    root = tmp_path / TICKETS
    _closed(tmp_path)
    a = _ticket(tmp_path, f"{TICKETS}/todos/TCK-20261005-CLOSED.md", "TCK-20261005-CLOSED")
    b = _ticket(tmp_path, f"{TICKETS}/todos/f/TCK-20261005-CLOSED.md", "TCK-20261005-CLOSED")
    c = _ticket(tmp_path, f"{TICKETS}/inprogress/TCK-20261005-CLOSED.md", "TCK-20261005-CLOSED")
    keep = _ticket(tmp_path, f"{TICKETS}/todos/TCK-20261005-OTHER.md", "TCK-20261005-OTHER")
    removed = closure.remove_stale_active_copies("TCK-20261005-CLOSED", root)
    assert len(removed) == 3 and not (a.exists() or b.exists() or c.exists()) and keep.exists()


def test_closure_tool_never_touches_an_unclosed_ticket(tmp_path):
    todo = _ticket(tmp_path, f"{TICKETS}/todos/TCK-20261005-OPEN.md", "TCK-20261005-OPEN")
    (tmp_path / TICKETS / "done").mkdir(parents=True)
    assert closure.remove_stale_active_copies("TCK-20261005-OPEN", tmp_path / TICKETS) == [] and todo.exists()
