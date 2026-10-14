"""tools/graphify_link.py, tools/graphify_prune.py and the edit hook's condition
(TCK-20261011-GRAPHIFY-SHARED-GRAPH-FROM-WORKTREES). Real git worktrees; a fake `graphify` records calls."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import graphify_link as gl  # noqa: E402
from tools import graphify_prune as gp  # noqa: E402

_ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, env=_ENV)


@pytest.fixture
def main(tmp_path):
    repo = tmp_path / "main"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "keep.py").write_text("x = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "i")
    return repo


def _graph(repo, nodes=(("a", "keep.py"), ("b", "gone.py"), ("c", None)), links=(("a", "b"), ("a", "c"), ("b", "c")),
           hyper=(("h1", ("a", "b", "c")), ("h2", ("b", "c")))):
    out = repo / "graphify-out"
    out.mkdir(exist_ok=True)
    data = {"directed": False, "multigraph": False,
            "graph": {"hyperedges": [{"id": i, "nodes": list(n)} for i, n in hyper]},
            "nodes": [{"id": i, **({"source_file": s} if s else {})} for i, s in nodes],
            "links": [{"source": s, "target": t, "relation": "r"} for s, t in links],
            "hyperedges": [{"id": i, "nodes": list(n)} for i, n in hyper], "built_at_commit": "abc"}
    (out / "graph.json").write_text(json.dumps(data, indent=2))
    return out / "graph.json"


def _worktree(main, tmp_path, name="wt"):
    wt = tmp_path / name
    _git(main, "worktree", "add", "-q", "-b", name, str(wt))
    return wt


# ---- link ----------------------------------------------------------------------------------------

def test_a_fresh_worktree_gets_a_link_to_the_main_graph(main, tmp_path):
    graph = _graph(main)
    wt = _worktree(main, tmp_path)
    assert gl.link_shared_graph(wt) == gl.LINKED
    assert (wt / "graphify-out").is_symlink() and (wt / "graphify-out" / "graph.json").resolve() == graph.resolve()
    assert gl.link_shared_graph(wt) == gl.HAS_OWN  # idempotent


def test_a_real_directory_a_foreign_symlink_and_a_broken_symlink_are_left_alone(main, tmp_path):
    _graph(main)
    real = _worktree(main, tmp_path, "real")
    (real / "graphify-out").mkdir()
    (real / "graphify-out" / "own.txt").write_text("mine")
    foreign = _worktree(main, tmp_path, "foreign")
    (foreign / "graphify-out").symlink_to(tmp_path / "elsewhere")
    for wt in (real, foreign):
        assert gl.link_shared_graph(wt) == gl.HAS_OWN
    assert not (real / "graphify-out").is_symlink() and (real / "graphify-out" / "own.txt").read_text() == "mine"
    assert os.readlink(foreign / "graphify-out") == str(tmp_path / "elsewhere")


def test_the_main_checkout_is_never_linked_and_no_main_graph_means_no_link(main, tmp_path):
    assert gl.link_shared_graph(main) == gl.MAIN and not (main / "graphify-out").exists()
    wt = _worktree(main, tmp_path)
    assert gl.link_shared_graph(wt) == gl.NO_SHARED_GRAPH and not os.path.lexists(wt / "graphify-out")
    assert gl.link_shared_graph(tmp_path / "not-a-repo-at-all") in (gl.UNKNOWN, gl.FAILED)


def test_the_link_is_ignored_by_git(main, tmp_path):
    _graph(main)
    (main / ".gitignore").write_text((ROOT / ".gitignore").read_text())
    _git(main, "add", ".gitignore")
    _git(main, "commit", "-q", "-m", "ignore")
    wt = _worktree(main, tmp_path)
    gl.link_shared_graph(wt)
    out = subprocess.run(["git", "status", "--porcelain"], cwd=wt, capture_output=True, text=True, check=True).stdout
    assert "graphify-out" not in out


def test_session_start_links_a_launched_worktree(main, tmp_path):
    from tools.sessions import session_start_hook as hook

    _graph(main)
    wt = _worktree(main, tmp_path)
    assert hook.link_shared_graph is gl.link_shared_graph
    gl.link_shared_graph(wt)
    assert (wt / "graphify-out").is_symlink()


# ---- the edit hook's condition --------------------------------------------------------------------

def _hook_command():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
    for group in settings["hooks"]["PostToolUse"]:
        for h in group["hooks"]:
            if "graphify update" in h["command"]:
                return h["command"]
    raise AssertionError("no graphify update hook")


def _run_hook(cwd, file_path, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    log = tmp_path / "graphify.log"
    fake = bin_dir / "graphify"
    fake.write_text(f"#!/bin/sh\necho \"$@\" >> {log}\n")
    fake.chmod(0o755)
    subprocess.run(["bash", "-c", _hook_command()], cwd=cwd, input=json.dumps({"tool_input": {"file_path": file_path}}),
                   text=True, env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}, check=True)
    return log.read_text().strip() if log.exists() else ""


def test_the_edit_hook_updates_only_a_real_graphify_out_directory(main, tmp_path):
    _graph(main)
    wt = _worktree(main, tmp_path)
    gl.link_shared_graph(wt)
    assert _run_hook(wt, str(wt / "src" / "a.py"), tmp_path) == ""            # linked worktree: never writes the shared graph
    assert _run_hook(main, str(main / "src" / "a.py"), tmp_path) == "update ."  # main checkout: still refreshes
    assert _run_hook(main, str(main / "docs" / "a.md"), tmp_path) == "update ."  # unchanged: no new calls for non-code paths
    assert (tmp_path / "graphify.log").read_text().count("update") == 1


# ---- prune ----------------------------------------------------------------------------------------

def test_prune_removes_stale_nodes_their_links_and_hyperedge_members(main, capsys):
    graph = _graph(main)
    assert gp.main(["--graph", str(graph)]) == 0
    data = json.loads(graph.read_text())
    assert [n["id"] for n in data["nodes"]] == ["a", "c"]
    assert [(e["source"], e["target"]) for e in data["links"]] == [("a", "c")]
    assert data["hyperedges"] == [{"id": "h1", "nodes": ["a", "c"]}]  # h2 fell below two members and was dropped
    assert data["graph"]["hyperedges"] == data["hyperedges"] and data["built_at_commit"] == "abc"
    assert "removed 1 nodes, 2 links, 1 hyperedges" in capsys.readouterr().out


def test_prune_is_idempotent_and_a_second_run_leaves_the_bytes_alone(main):
    graph = _graph(main)
    gp.main(["--graph", str(graph)])
    first = graph.read_bytes()
    gp.main(["--graph", str(graph)])
    assert graph.read_bytes() == first


def test_prune_dry_run_and_symlinked_graphs_write_nothing(main, tmp_path, capsys):
    graph = _graph(main)
    before = graph.read_bytes()
    gp.main(["--graph", str(graph), "--dry-run"])
    assert graph.read_bytes() == before and "dry run" in capsys.readouterr().out
    wt = _worktree(main, tmp_path)
    gl.link_shared_graph(wt)
    gp.main(["--graph", str(wt / "graphify-out" / "graph.json"), "--root", str(main)])
    assert graph.read_bytes() == before and "symlink" in capsys.readouterr().out


def test_prune_reports_size_warns_above_the_threshold_and_never_fails(main, capsys):
    graph = _graph(main)
    assert gp.main(["--graph", str(graph), "--warn-mb", "0.0001"]) == 0
    out = capsys.readouterr().out
    assert "MB" in out and "WARNING" in out and "nodes" in out
    assert gp.main(["--graph", str(main / "missing.json")]) == 0
    (main / "bad.json").write_text("{not json")
    assert gp.main(["--graph", str(main / "bad.json")]) == 0


def test_prune_keeps_a_graph_with_nothing_stale_exactly_as_it_was(main):
    graph = _graph(main, nodes=(("a", "keep.py"), ("c", None)), links=(("a", "c"),), hyper=(("h1", ("a", "c")),))
    before = graph.read_bytes()
    gp.main(["--graph", str(graph)])
    assert graph.read_bytes() == before


# ---- ignore list, owner, ignore rule ---------------------------------------------------------------

def test_graphifyignore_lists_the_bulky_folders_and_agent_working_owns_it():
    lines = (ROOT / ".graphifyignore").read_text().split()
    assert {"scratch/", "experiments/", "reviews/"} <= set(lines)
    out = subprocess.run([sys.executable, "-m", "tools.sessions.route", ".graphifyignore"], cwd=ROOT, capture_output=True,
                         text=True, env={**os.environ, "PYTHONPATH": str(ROOT)}).stdout
    assert "domain: agent-working" in out
