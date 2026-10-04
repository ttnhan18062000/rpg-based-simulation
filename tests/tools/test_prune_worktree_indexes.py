"""TCK-20261004-WORKTREE-INDEX-DUPLICATION: idle-worktree index pruning and cwd-independent index paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from tools import prune_worktree_indexes as pw
from tools.agent_working_paths import AGENT_MONITORING_INDEX, KNOWLEDGE_INDEX, PARITY_INDEX

DAY = 86400.0


def _make_index(wt: Path, rel: Path, age_days: float, now: float, size: int = 10) -> Path:
    d = wt / rel
    d.mkdir(parents=True)
    f = d / "data.bin"
    f.write_bytes(b"x" * size)
    t = now - age_days * DAY
    os.utime(f, (t, t))
    os.utime(d, (t, t))
    return d


def test_only_idle_non_current_non_main_worktrees_are_candidates(tmp_path):
    now = 1_000_000_000.0
    main, idle, fresh, cur = (tmp_path / n for n in ("main", "idle", "fresh", "cur"))
    for wt in (main, idle, fresh, cur):
        _make_index(wt, KNOWLEDGE_INDEX, age_days=30, now=now)
    _make_index(fresh, AGENT_MONITORING_INDEX, age_days=1, now=now)
    # fresh's knowledge index is old, monitoring index is recent: each folder is judged on its own mtime.
    found = pw.find_candidates([main, idle, fresh, cur], current=cur, idle_days=7, now=now)
    got = {(c.worktree.name, c.index_dir.name) for c in found}
    assert got == {("idle", "knowledge-index"), ("fresh", "knowledge-index")}
    assert all(c.size_bytes == 10 for c in found)


def test_parity_index_is_never_a_candidate(tmp_path):
    now = 1_000_000_000.0
    main, other, cur = (tmp_path / n for n in ("main", "other", "cur"))
    for wt in (main, cur):
        wt.mkdir()
    _make_index(other, PARITY_INDEX, age_days=90, now=now)
    assert pw.find_candidates([main, other, cur], current=cur, idle_days=1, now=now) == []


def test_apply_deletes_and_dry_run_does_not(tmp_path, monkeypatch, capsys):
    now = 1_000_000_000.0
    main, idle, cur = (tmp_path / n for n in ("main", "idle", "cur"))
    main.mkdir()
    cur.mkdir()
    d = _make_index(idle, KNOWLEDGE_INDEX, age_days=30, now=now)
    monkeypatch.chdir(cur)
    monkeypatch.setattr(pw, "list_worktrees", lambda _cwd: [main, idle, cur])
    monkeypatch.setattr(pw.time, "time", lambda: now)

    assert pw.main(["--days", "7"]) == 0
    assert d.exists() and "would remove" in capsys.readouterr().out

    assert pw.main(["--days", "7", "--apply"]) == 0
    assert not d.exists() and "removed" in capsys.readouterr().out


def test_index_paths_do_not_depend_on_cwd(tmp_path, monkeypatch):
    """MCP search_docs reported 'index not found' when started outside the worktree root."""
    monkeypatch.chdir(tmp_path)
    for name in ("tools.knowledge_search", "tools.retrieval_cache"):
        sys.modules.pop(name, None)
    import tools.knowledge_search as ks
    import tools.retrieval_cache as rc

    assert ks._DEFAULT_DB.is_absolute() and rc.CACHE_DB_PATH.is_absolute()
    assert ks._DEFAULT_DB.parent == rc.CACHE_DB_PATH.parent
