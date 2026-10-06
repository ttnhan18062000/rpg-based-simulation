"""Tests for TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING: a search says when its worktree's index is stale."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import types
from argparse import Namespace
from pathlib import Path

import pytest

from tools.agent_working_paths import STORED_ARTIFACTS, TICKETS

_REPO_ROOT = Path(__file__).parent.parent.parent


def _load(name: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # a dataclass in the module resolves its own module through sys.modules
    spec.loader.exec_module(mod)
    return mod


_ks = _load("knowledge_search_staleness_under_test", _REPO_ROOT / "tools" / "knowledge_search.py")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture()
def corpus(tmp_path, monkeypatch):
    """A built index over a tiny corpus, built the way a real build is: corpus root "." as cwd."""
    root = tmp_path / "wt"
    _write(root / TICKETS / "done" / "TCK-20260101-A.md", "# TCK-20260101-A\n\n## Request Summary\nFix the thing.\n\n## Scope\nx\n")
    _write(root / STORED_ARTIFACTS / "TCK-20260101-A" / "investigation.md", "Findings about the thing.")
    _write(root / TICKETS / "working_log.csv", "timestamp,ticket_id,title,status,summary,artifacts_path\n2026-01-01,TCK-20260101-A,T,DONE,S,none\n")
    _write(root / "docs" / "mechanics" / "one.md", "# One\n\nBody of one.\n")
    _write(root / "docs" / "archive" / "old.md", "# Old\n\nNever indexed.\n")
    monkeypatch.chdir(root)
    db = root / "index" / "knowledge.db"
    db.parent.mkdir()
    db.touch()
    _ks._write_manifest(_ks._collect_corpus(Path(".")), db)
    return root, db


def _bump(path: Path) -> None:
    stat = path.stat()
    os.utime(path, (stat.st_atime + 100, stat.st_mtime + 100))


def test_a_current_index_has_no_staleness(corpus):
    root, db = corpus
    assert _ks.index_staleness(db, root) is None
    assert _ks.stale_warning(None) is None


def test_the_stat_walk_covers_exactly_what_the_build_indexed(corpus):
    root, _ = corpus
    built = {d["path"] for d in _ks._collect_corpus(Path("."))}
    assert set(_ks._corpus_source_paths(root)) == built


def test_a_touched_file_counts_as_one_changed(corpus):
    root, db = corpus
    _bump(root / "docs" / "mechanics" / "one.md")
    assert _ks.index_staleness(db, root) == {"changed": 1, "new": 0, "removed": 0}
    assert "1 changed, 0 new, 0 removed" in _ks.stale_warning(_ks.index_staleness(db, root))
    assert "make knowledge-index-update" in _ks.stale_warning(_ks.index_staleness(db, root))


def test_an_added_and_a_removed_file_are_counted_apart(corpus):
    root, db = corpus
    _write(root / "docs" / "mechanics" / "two.md", "# Two\n\nBody.\n")
    (root / "docs" / "mechanics" / "one.md").unlink()
    assert _ks.index_staleness(db, root) == {"changed": 0, "new": 1, "removed": 1}


def test_an_excluded_docs_subtree_never_counts(corpus):
    root, db = corpus
    _write(root / "docs" / "archive" / "more.md", "# More\n\nStill never indexed.\n")
    assert _ks.index_staleness(db, root) is None


@pytest.mark.parametrize("manifest", [None, "{not json", json.dumps({"version": 1}), json.dumps(["x"])])
def test_a_missing_or_unreadable_manifest_is_unknown_and_never_raises(corpus, manifest):
    root, db = corpus
    manifest_path = db.parent / "manifest.json"
    manifest_path.unlink()
    if manifest is not None:
        manifest_path.write_text(manifest)
    stale = _ks.index_staleness(db, root)
    assert stale == {"unknown": True} and "staleness unknown" in _ks.stale_warning(stale)


def _query(root, db):
    """Run the CLI query. The warning is printed before any model work, so a lean environment without the embedding
    packages (the search itself then fails on import) still shows it."""
    try:
        _ks.cmd_query(Namespace(db_path=str(db), corpus_root=str(root), query="thing", top_k=1, mode="keyword"))
    except ImportError:
        pass


def test_cli_query_prints_one_stale_line_and_still_runs(corpus, capsys):
    root, db = corpus
    _bump(root / "docs" / "mechanics" / "one.md")
    _query(root, db)
    err = capsys.readouterr().err
    assert err.count("knowledge index is stale: 1 changed") == 1


def test_cli_query_is_silent_on_a_current_index(corpus, capsys):
    root, db = corpus
    _query(root, db)
    assert "stale" not in capsys.readouterr().err


def _mcp(monkeypatch, db, root, results):
    mod = _load("search_mcp_staleness_under_test", _REPO_ROOT / "tools" / "search_mcp.py")
    monkeypatch.setattr(mod, "_ks", types.SimpleNamespace(index_staleness=lambda p: _ks.index_staleness(p, root)))
    monkeypatch.setattr(mod, "_DB_PATH", db)
    monkeypatch.setattr(mod, "_search", lambda *a, **k: results)
    return mod


def test_mcp_returns_results_plus_stale_when_the_index_is_behind(corpus, monkeypatch):
    root, db = corpus
    _bump(root / "docs" / "mechanics" / "one.md")
    out = _mcp(monkeypatch, db, root, [{"doc_id": "d"}])._run_search("q", with_staleness=True)
    assert out == {"results": [{"doc_id": "d"}], "stale": {"changed": 1, "new": 0, "removed": 0}}


def test_mcp_returns_the_bare_list_when_current_and_without_the_flag(corpus, monkeypatch):
    root, db = corpus
    mod = _mcp(monkeypatch, db, root, [{"doc_id": "d"}])
    assert mod._run_search("q", with_staleness=True) == [{"doc_id": "d"}]
    _bump(root / "docs" / "mechanics" / "one.md")
    assert mod._run_search("q") == [{"doc_id": "d"}]


def test_mcp_never_wraps_an_error(corpus, monkeypatch):
    root, db = corpus
    err = {"error": "index not found", "action": "run make knowledge-index"}
    assert _mcp(monkeypatch, db, root, err)._run_search("q", with_staleness=True) == err
