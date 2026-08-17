"""
Tests for tools/knowledge_search.py

Groups:
  1. build happy path                (AC1)
  2. query happy path                (AC2, AC3)
  3. graceful degradation            (AC4, AC7)
  4. make target                     (AC5)
  5. .gitignore coverage             (AC8)
  6. corpus scope guard              (boundary enforcement)
  7. pyproject.toml deps             (anti-drift)
"""

import importlib
import importlib.util
import pickle
import sqlite3
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module import — tools/ is not a package; add repo root to sys.path.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_KS_PATH = _REPO_ROOT / "tools" / "knowledge_search.py"


def _load_module() -> types.ModuleType:
    """Load knowledge_search as a module without executing __main__ block."""
    spec = importlib.util.spec_from_file_location("knowledge_search", _KS_PATH)
    mod: types.ModuleType = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_ks = _load_module()
# knowledge_search.py's own top-level `from hybrid_retrieval import hybrid_fuse_and_filter`
# (executed above by _load_module()) guarantees "hybrid_retrieval" is registered in sys.modules
# by this point -- reuse that exact object so monkeypatching its `_dense_candidates` seam affects
# calls made from `_ks.cmd_query()`.
_hr = sys.modules["hybrid_retrieval"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_corpus(tmp_path: Path) -> None:
    """Create a minimal but valid corpus tree under tmp_path."""
    # tickets/done/
    done_dir = tmp_path / "tickets" / "done"
    done_dir.mkdir(parents=True)
    (done_dir / "TCK-20260101-ALPHA.md").write_text(
        "---\nstatus: active\n---\n\n## Request Summary\nAlpha ticket: test stamina pressure mechanics.\n",
        encoding="utf-8",
    )
    (done_dir / "TCK-20260101-BETA.md").write_text(
        "---\nstatus: active\n---\n\n## Request Summary\nBeta ticket: economic trade route optimization.\n",
        encoding="utf-8",
    )

    # stored_artifacts/*/investigation.md
    art_dir = tmp_path / "stored_artifacts" / "TCK-20260101-ALPHA"
    art_dir.mkdir(parents=True)
    (art_dir / "investigation.md").write_text(
        "---\nstatus: active\n---\n\nInvestigation of stamina pressure: entity depletes energy during combat.\n",
        encoding="utf-8",
    )

    # tickets/working_log.csv
    wl_path = tmp_path / "tickets" / "working_log.csv"
    wl_path.write_text(
        "ticket_id,title,summary,date\n"
        "TCK-20260101-ALPHA,Alpha Ticket,stamina pressure mechanics,2026-01-01\n"
        "TCK-20260101-BETA,Beta Ticket,economic trade route,2026-01-02\n",
        encoding="utf-8",
    )


def _deps_available() -> bool:
    """Return True if sentence-transformers and sqlite-vec are importable."""
    ok, _ = _ks._check_deps()
    return ok


def _numpy_available() -> bool:
    """Return True if numpy is importable. Not covered by _deps_available()'s
    sentence-transformers/sqlite-vec check -- cmd_query()'s hybrid-fusion branch imports it
    separately (tools/knowledge_search.py:998), and it is not installed in CI's lean
    requirements.txt environment (requirements-knowledge.txt is dev-only, per that file's own
    header comment; numpy isn't declared in either)."""
    try:
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


def _bm25_deps_available() -> bool:
    """Return True if rank_bm25 and numpy are importable. Unlike sentence-transformers/
    sqlite-vec (requirements-knowledge.txt, local-dev-only per requirements.txt's own
    header comment), these two are the minimum needed for BM25/hybrid-fusion code paths and
    are not installed in CI's lean requirements.txt environment either."""
    try:
        import rank_bm25  # noqa: F401
    except ImportError:
        return False
    return _numpy_available()


# ---------------------------------------------------------------------------
# Group 1 — Build happy path (AC1)
# ---------------------------------------------------------------------------

class TestBuildHappyPath:

    @pytest.mark.slow
    def test_build_produces_db(self, tmp_path):
        """AC1: build command completes and produces knowledge-index/knowledge.db."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        result = subprocess.run(
            [
                sys.executable,
                str(_KS_PATH),
                "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"build failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert db_path.exists(), "knowledge.db was not created"

    @pytest.mark.slow
    def test_build_prints_document_count(self, tmp_path):
        """AC1: build prints 'N documents embedded'."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "documents embedded" in result.stdout.lower() or "documents embedded" in result.stderr.lower()

    @pytest.mark.slow
    def test_build_prints_per_source_summary(self, tmp_path):
        """AC1: build prints per-source summary with ticket, investigation, working_log counts."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        combined = result.stdout + result.stderr
        # Should mention ticket summaries, investigation files, and working log rows
        assert "ticket" in combined.lower()
        assert "investigation" in combined.lower()
        assert "working log" in combined.lower()

    @pytest.mark.slow
    def test_build_idempotent(self, tmp_path):
        """AC1: Running build twice overwrites old db without error."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        for _ in range(2):
            result = subprocess.run(
                [
                    sys.executable, str(_KS_PATH), "build",
                    "--corpus-root", str(tmp_path),
                    "--db-path", str(db_path),
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
        assert db_path.exists()


# ---------------------------------------------------------------------------
# Group 2 — Query happy path (AC2, AC3)
# ---------------------------------------------------------------------------

class TestQueryHappyPath:

    @pytest.mark.slow
    def test_query_returns_results(self, tmp_path):
        """AC2: query returns top-k results (vector search works)."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        # First build
        build_result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert build_result.returncode == 0, f"build failed: {build_result.stderr}"

        # Then query
        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "query",
                "stamina pressure combat",
                "--top-k", "2",
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1, f"Expected at least 1 result, got: {result.stdout!r}"

    @pytest.mark.slow
    def test_query_completes_within_2_seconds(self, tmp_path):
        """AC2: query returns within 2 seconds on a minimal corpus.

        This test uses a small local corpus. The 2-second SLA applies to the
        full corpus (AC2) and is tested here on a proxy — if this tiny corpus
        exceeds 2s, the full corpus certainly will.
        """
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        # Use the live knowledge-index if available
        live_db = _REPO_ROOT / "knowledge-index" / "knowledge.db"
        if not live_db.exists():
            pytest.skip("knowledge index not built — run make knowledge-index")

        start = time.monotonic()
        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "query",
                "player fatigue during extended combat",
                "--top-k", "5",
                "--db-path", str(live_db),
            ],
            capture_output=True,
            text=True,
        )
        elapsed = time.monotonic() - start
        assert result.returncode == 0
        assert elapsed < 2.0, f"query took {elapsed:.2f}s — exceeded 2s SLA"

    @pytest.mark.slow
    def test_query_result_format_tab_separated(self, tmp_path):
        """AC3: results include ticket ID, file path, and snippet (tab-separated)."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "query",
                "stamina",
                "--top-k", "1",
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1, "Expected at least one result"
        parts = lines[0].split("\t")
        assert len(parts) == 8, f"Expected 8 tab-separated fields, got {len(parts)}: {lines[0]!r}"
        doc_id, path, heading, section, final_score, semantic_score, keyword_score, snippet = parts
        assert doc_id, "doc_id field is empty"
        assert path, "path field is empty"
        assert isinstance(heading, str), "heading field must be a string"
        assert isinstance(section, str), "section field must be a string"
        assert snippet, "snippet field is empty"

    @pytest.mark.slow
    def test_query_ticket_id_in_result(self, tmp_path):
        """AC3: ticket ID format (TCK-...) appears in results."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "query",
                "stamina",
                "--top-k", "3",
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # At least one result should contain a TCK- ID
        assert "TCK-" in result.stdout, f"No TCK- ID in results:\n{result.stdout}"


# ---------------------------------------------------------------------------
# Group 3 — Graceful degradation (AC4, AC7)
# ---------------------------------------------------------------------------

class TestGracefulDegradation:

    def test_missing_index_warning_and_exit_0(self, tmp_path):
        """AC4: If knowledge-index/ does not exist, query prints warning and exits 0."""
        nonexistent_db = tmp_path / "no-such-dir" / "knowledge.db"

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "query",
                "test query",
                "--db-path", str(nonexistent_db),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}"
        combined = result.stdout + result.stderr
        assert "knowledge index not found" in combined.lower() or "not found" in combined.lower(), \
            f"Expected 'knowledge index not found' warning in output:\n{combined}"

    def test_missing_sentence_transformers_build_exits_0(self, tmp_path):
        """AC7: build degrades gracefully when sentence-transformers is missing."""
        env_script = f"""
import sys
# Block sentence_transformers import
import unittest.mock
sys.modules['sentence_transformers'] = None

import importlib.util
spec = importlib.util.spec_from_file_location('knowledge_search', r'{_KS_PATH}')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

import types, argparse
args = types.SimpleNamespace(
    corpus_root=r'{tmp_path}',
    db_path=r'{tmp_path / "knowledge-index" / "k.db"}',
)
result = mod.cmd_build(args)
sys.exit(result)
"""
        result = subprocess.run(
            [sys.executable, "-c", env_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, \
            f"Expected exit 0 on missing deps, got {result.returncode}:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        combined = result.stdout + result.stderr
        assert "not installed" in combined.lower() or "warning" in combined.lower(), \
            f"Expected warning about missing package:\n{combined}"

    def test_missing_sqlite_vec_query_exits_0(self, tmp_path):
        """AC7: query degrades gracefully when sqlite-vec is missing."""
        # Create a fake db file so the 'not found' branch is not taken
        fake_db = tmp_path / "knowledge.db"
        fake_db.write_bytes(b"SQLite fake db for test")

        env_script = f"""
import sys
# Block sqlite_vec import
sys.modules['sqlite_vec'] = None

import importlib.util
spec = importlib.util.spec_from_file_location('knowledge_search', r'{_KS_PATH}')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

import types
args = types.SimpleNamespace(
    query='test query',
    top_k=5,
    db_path=r'{fake_db}',
    mode='hybrid',
)
result = mod.cmd_query(args)
sys.exit(result)
"""
        result = subprocess.run(
            [sys.executable, "-c", env_script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, \
            f"Expected exit 0 on missing deps, got {result.returncode}:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        combined = result.stdout + result.stderr
        assert "not installed" in combined.lower() or "warning" in combined.lower(), \
            f"Expected warning about missing package:\n{combined}"


# ---------------------------------------------------------------------------
# Group 4 — make target (AC5)
# ---------------------------------------------------------------------------

class TestMakeTarget:

    def test_makefile_has_knowledge_index_target(self):
        """AC5: Makefile contains a knowledge-index target."""
        makefile = _REPO_ROOT / "Makefile"
        assert makefile.exists(), "Makefile not found"
        content = makefile.read_text(encoding="utf-8")
        assert "knowledge-index:" in content, \
            "Makefile does not have a 'knowledge-index:' target"

    def test_makefile_knowledge_index_calls_build(self):
        """AC5: knowledge-index target runs python3 tools/knowledge_search.py build."""
        makefile = _REPO_ROOT / "Makefile"
        content = makefile.read_text(encoding="utf-8")
        assert "tools/knowledge_search.py build" in content, \
            "knowledge-index target does not call 'python3 tools/knowledge_search.py build'"

    def test_makefile_dry_run_knowledge_index(self):
        """AC5: make --dry-run knowledge-index exits 0 and references the build command."""
        result = subprocess.run(
            ["make", "--dry-run", "knowledge-index"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0, \
            f"make --dry-run knowledge-index failed:\n{result.stdout}\n{result.stderr}"
        combined = result.stdout + result.stderr
        assert "knowledge_search.py" in combined, \
            f"Expected 'knowledge_search.py' in make dry-run output:\n{combined}"

    def test_knowledge_index_not_in_test_target(self):
        """AC5 guard: make knowledge-index must NOT be a dependency of test, ci, or all."""
        makefile = _REPO_ROOT / "Makefile"
        content = makefile.read_text(encoding="utf-8")
        # Find the test, ci, and all target lines and confirm knowledge-index is not listed as dep
        for target_line in content.split("\n"):
            if target_line.startswith(("test:", "ci:", "all:")):
                assert "knowledge-index" not in target_line, \
                    f"'knowledge-index' must not be a dependency of CI targets, found in: {target_line!r}"


# ---------------------------------------------------------------------------
# Group 5 — .gitignore coverage (AC8)
# ---------------------------------------------------------------------------

class TestGitignore:

    def test_knowledge_index_in_gitignore(self):
        """AC8: knowledge-index/ is listed in .gitignore."""
        gitignore = _REPO_ROOT / ".gitignore"
        assert gitignore.exists(), ".gitignore not found"
        content = gitignore.read_text(encoding="utf-8")
        assert "knowledge-index/" in content, \
            "knowledge-index/ is not listed in .gitignore"

    def test_git_check_ignore(self, tmp_path):
        """AC8: git check-ignore confirms knowledge-index/ is ignored."""
        result = subprocess.run(
            ["git", "check-ignore", "-v", "knowledge-index/knowledge.db"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        # git check-ignore returns 0 if the path is ignored, 1 if not ignored
        assert result.returncode == 0, \
            "git check-ignore reports knowledge-index/knowledge.db is NOT ignored"


# ---------------------------------------------------------------------------
# Group 6 — Corpus scope guard
# ---------------------------------------------------------------------------

class TestCorpusScopeGuard:

    def test_collect_corpus_only_reads_defined_roots(self, tmp_path):
        """Corpus collection must only read tickets/done, stored_artifacts, working_log.csv, and docs/.

        docs/ is a valid corpus source (added by TCK-20260612-LOCAL-CTX-DOCS-CORPUS).
        src/ and other non-corpus paths must remain excluded.
        """
        _make_minimal_corpus(tmp_path)

        # docs/extra.md is now a valid corpus source (docs/ is indexed since TCK-20260612-LOCAL-CTX-DOCS-CORPUS)
        (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
        (tmp_path / "docs" / "extra.md").write_text(
            "## Extra Section\n\nExtra docs content for indexing.\n", encoding="utf-8"
        )

        # src/ must still NOT be included
        (tmp_path / "src").mkdir(parents=True, exist_ok=True)
        (tmp_path / "src" / "engine.py").write_text("# source code", encoding="utf-8")

        corpus = _ks._collect_corpus(tmp_path)

        # src/ must not appear in corpus
        paths = [d["path"] for d in corpus]
        for path in paths:
            assert "src/engine.py" not in path, f"src/ leaked into corpus: {path}"

        # docs/extra.md SHOULD appear in corpus (it is a valid docs/ file)
        doc_paths = [d["path"] for d in corpus if d.get("source_type") == "doc_chunk"]
        assert any("extra.md" in p for p in doc_paths), \
            f"docs/extra.md should now be in corpus as doc_chunk source, but paths were: {doc_paths}"

    def test_collect_corpus_includes_all_three_sources(self, tmp_path):
        """Corpus must include docs from all three source types."""
        _make_minimal_corpus(tmp_path)
        corpus = _ks._collect_corpus(tmp_path)

        source_types = {d["source_type"] for d in corpus}
        assert "ticket" in source_types, "No ticket documents in corpus"
        assert "investigation" in source_types, "No investigation documents in corpus"
        assert "working_log" in source_types, "No working_log documents in corpus"


# ---------------------------------------------------------------------------
# Group 7 — pyproject.toml deps (anti-drift)
# ---------------------------------------------------------------------------

class TestPyprojectDeps:

    def test_knowledge_group_declared(self):
        """knowledge optional-dependencies group must be present in pyproject.toml."""
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        pyproject = _REPO_ROOT / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        opt_deps = data.get("project", {}).get("optional-dependencies", {})
        assert "knowledge" in opt_deps, \
            "pyproject.toml missing [project.optional-dependencies.knowledge]"

    def test_knowledge_group_contains_expected_packages(self):
        """knowledge group must list sentence-transformers and sqlite-vec."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        pyproject = _REPO_ROOT / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        knowledge_deps = data.get("project", {}).get("optional-dependencies", {}).get("knowledge", [])

        dep_names = [d.split(">=")[0].split("==")[0].strip() for d in knowledge_deps]
        assert "sentence-transformers" in dep_names, \
            f"sentence-transformers not in knowledge deps: {knowledge_deps}"
        assert "sqlite-vec" in dep_names, \
            f"sqlite-vec not in knowledge deps: {knowledge_deps}"

    def test_knowledge_deps_not_in_core_dependencies(self):
        """sentence-transformers and sqlite-vec must NOT appear in core [project.dependencies]."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        pyproject = _REPO_ROOT / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        core_deps = data.get("project", {}).get("dependencies", [])
        core_names = [d.split(">=")[0].split("==")[0].strip() for d in core_deps]

        assert "sentence-transformers" not in core_names, \
            "sentence-transformers must NOT be in core [project.dependencies]"
        assert "sqlite-vec" not in core_names, \
            "sqlite-vec must NOT be in core [project.dependencies]"


# ---------------------------------------------------------------------------
# Unit tests — _extract_request_summary
# ---------------------------------------------------------------------------

class TestExtractRequestSummary:

    def test_extracts_section(self):
        text = "---\nstatus: active\n---\n\n## Request Summary\nThis is the summary.\n\n## Other Section\n"
        result = _ks._extract_request_summary(text)
        assert result == "This is the summary."

    def test_fallback_on_missing_section(self):
        text = "---\nstatus: active\n---\n\n## Title\nSome content here without Request Summary.\n"
        result = _ks._extract_request_summary(text)
        # Should fallback to first 500 chars of non-frontmatter content
        assert "Some content here" in result
        assert len(result) <= 500

    def test_multiline_section(self):
        text = "## Request Summary\nLine one.\nLine two.\nLine three.\n\n## Next\nOther\n"
        result = _ks._extract_request_summary(text)
        assert "Line one" in result
        assert "Line two" in result
        assert "Line three" in result

    def test_empty_file(self):
        result = _ks._extract_request_summary("")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Unit tests — _extract_working_log_rows
# ---------------------------------------------------------------------------

class TestExtractWorkingLogRows:

    def test_basic_csv(self, tmp_path):
        csv_file = tmp_path / "working_log.csv"
        csv_file.write_text(
            "ticket_id,title,summary,date\n"
            "TCK-001,First Ticket,First summary,2026-01-01\n"
            "TCK-002,Second Ticket,Second summary,2026-01-02\n",
            encoding="utf-8",
        )
        rows = _ks._extract_working_log_rows(csv_file)
        assert len(rows) == 2
        assert rows[0]["id"] == "TCK-001"
        assert rows[0]["title"] == "First Ticket"
        assert rows[0]["summary"] == "First summary"

    def test_missing_file_returns_empty(self, tmp_path):
        rows = _ks._extract_working_log_rows(tmp_path / "nonexistent.csv")
        assert rows == []

    def test_empty_csv_returns_empty(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("ticket_id,title,summary\n", encoding="utf-8")
        rows = _ks._extract_working_log_rows(csv_file)
        assert rows == []


# ---------------------------------------------------------------------------
# Unit tests — _collect_corpus (boundaries)
# ---------------------------------------------------------------------------

class TestCollectCorpus:

    def test_empty_corpus_root(self, tmp_path):
        """Empty corpus root returns empty list without error."""
        corpus = _ks._collect_corpus(tmp_path)
        assert corpus == []

    def test_ticket_text_is_request_summary_only(self, tmp_path):
        """Ticket corpus text is the Request Summary section, not full file."""
        done_dir = tmp_path / "tickets" / "done"
        done_dir.mkdir(parents=True)
        (done_dir / "TCK-20260101-TEST.md").write_text(
            "---\nstatus: active\n---\n\n## Request Summary\nExact summary text.\n\n## Scope\nScope text.\n",
            encoding="utf-8",
        )
        (tmp_path / "tickets").joinpath("working_log.csv").write_text(
            "ticket_id,title,summary\n", encoding="utf-8"
        )

        corpus = _ks._collect_corpus(tmp_path)
        ticket_docs = [d for d in corpus if d["source_type"] == "ticket"]
        assert len(ticket_docs) == 1
        assert "Exact summary text." in ticket_docs[0]["text"]
        assert "Scope text." not in ticket_docs[0]["text"]

    def test_investigation_text_is_first_500_chars(self, tmp_path):
        """Investigation corpus text is capped at 500 characters."""
        art_dir = tmp_path / "stored_artifacts" / "TCK-20260101-TEST"
        art_dir.mkdir(parents=True)
        long_text = "A" * 1000
        (art_dir / "investigation.md").write_text(long_text, encoding="utf-8")
        (tmp_path / "tickets").mkdir(parents=True)
        (tmp_path / "tickets" / "working_log.csv").write_text(
            "ticket_id,title,summary\n", encoding="utf-8"
        )

        corpus = _ks._collect_corpus(tmp_path)
        inv_docs = [d for d in corpus if d["source_type"] == "investigation"]
        assert len(inv_docs) == 1
        assert len(inv_docs[0]["text"]) <= 500


# ---------------------------------------------------------------------------
# Group 8 — TestDocsChunkExtraction (non-slow unit tests)
# ---------------------------------------------------------------------------

def _make_md_with_h2s(sections: list[tuple[str, str]], frontmatter: str = "") -> str:
    """Build a markdown string with optional frontmatter and H2 sections."""
    parts = []
    if frontmatter:
        parts.append(frontmatter)
    for heading, body in sections:
        parts.append(f"## {heading}\n\n{body}")
    return "\n\n".join(parts)


class TestDocsChunkExtraction:
    """Group 8: Unit tests for _collect_docs_chunks, _heading_slug, _strip_frontmatter."""

    def test_collect_docs_chunks_basic(self, tmp_path):
        """Returns 2 chunks for a file with 2 H2 sections; checks keys and section."""
        docs_root = tmp_path / "docs"
        mech_dir = docs_root / "mechanics"
        mech_dir.mkdir(parents=True)
        content = (
            "---\nstatus: authoritative\n---\n\n"
            "## Section One\n\n" + ("word " * 80) + "\n\n"
            "## Section Two\n\n" + ("word " * 80) + "\n"
        )
        (mech_dir / "02_combat_laws.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"
        required_keys = {"id", "doc_id", "path", "text", "source_type", "heading", "section"}
        for chunk in chunks:
            assert required_keys.issubset(chunk.keys()), f"Missing keys: {required_keys - chunk.keys()}"
            assert chunk["source_type"] == "doc_chunk"
            assert chunk["section"] == "mechanics"

    def test_collect_docs_chunks_preserves_full_nested_path(self, tmp_path):
        """doc_id preserves the full nested relative path under docs_root, not just the
        immediate subdirectory. Fixes TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION."""
        docs_root = tmp_path / "docs"
        nested_dir = docs_root / "engine" / "contracts" / "knowledge_gateway_mcp"
        nested_dir.mkdir(parents=True)
        content = "## Overview\n\n" + ("word " * 80) + "\n"
        (nested_dir / "foo.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) >= 1
        doc_ids = {c["doc_id"] for c in chunks}
        assert doc_ids == {"engine/contracts/knowledge_gateway_mcp/foo"}, (
            f"Expected full nested doc_id, got: {doc_ids}"
        )
        # Pre-fix (buggy) behavior would have truncated to "engine/foo" — assert that
        # truncated form is NOT what was produced, proving this test exercises the bug.
        assert "engine/foo" not in doc_ids

    def test_collect_docs_chunks_no_collision_same_stem_different_subdir(self, tmp_path):
        """Two docs with the same stem under different nested subdirectories of the same
        top-level section must produce distinct doc_id values, not collide."""
        docs_root = tmp_path / "docs"
        dir_a = docs_root / "engine" / "a"
        dir_b = docs_root / "engine" / "b"
        dir_a.mkdir(parents=True)
        dir_b.mkdir(parents=True)
        content = "## Overview\n\n" + ("word " * 80) + "\n"
        (dir_a / "foo.md").write_text(content, encoding="utf-8")
        (dir_b / "foo.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        doc_ids = {c["doc_id"] for c in chunks}
        assert doc_ids == {"engine/a/foo", "engine/b/foo"}, (
            f"Expected distinct doc_ids for same-stem nested docs, got: {doc_ids}"
        )

    def test_collect_docs_chunks_single_level_path_unchanged(self, tmp_path):
        """A depth-1 doc still produces the same doc_id shape as before the fix — a strict
        generalization, not a behavior change, for the common non-nested case."""
        docs_root = tmp_path / "docs"
        mech_dir = docs_root / "mechanics"
        mech_dir.mkdir(parents=True)
        content = "## Overview\n\n" + ("word " * 80) + "\n"
        (mech_dir / "02_combat_laws.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk["doc_id"] == "mechanics/02_combat_laws"

    def test_chunk_id_anchor_suffix_unaffected_by_nesting_fix(self, tmp_path):
        """Chunk-level id anchor composition (heading-slug, #, zero-padded seq) stays
        byte-identical for nested docs — only the pre-# doc_id portion's shape changes."""
        docs_root = tmp_path / "docs"
        nested_dir = docs_root / "engine" / "contracts" / "knowledge_gateway_mcp"
        nested_dir.mkdir(parents=True)
        content = "## The Overview Section\n\n" + ("word " * 80) + "\n"
        (nested_dir / "foo.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) == 1
        chunk = chunks[0]
        expected_doc_id = "engine/contracts/knowledge_gateway_mcp/foo"
        assert chunk["doc_id"] == expected_doc_id
        assert chunk["id"] == f"{expected_doc_id}#{_ks._heading_slug('The Overview Section')}-000"

    def test_collect_docs_chunks_heading_text(self, tmp_path):
        """Chunk heading field preserves the H2 heading text."""
        docs_root = tmp_path / "docs"
        mech_dir = docs_root / "mechanics"
        mech_dir.mkdir(parents=True)
        content = "## The Damage Formula\n\n" + ("formula word " * 50) + "\n"
        (mech_dir / "combat.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) >= 1
        headings = [c["heading"] for c in chunks]
        assert "The Damage Formula" in headings, f"Expected heading, got: {headings}"

    def test_collect_docs_chunks_no_headings_fallback(self, tmp_path):
        """File with no H2/H3 headings produces exactly 1 chunk with heading=''."""
        docs_root = tmp_path / "docs"
        arch_dir = docs_root / "architecture"
        arch_dir.mkdir(parents=True)
        content = "---\nstatus: authoritative\n---\n\nThis is body text without any headings.\n" + ("word " * 50)
        (arch_dir / "cognition_domain.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
        assert chunks[0]["heading"] == "", f"Expected empty heading, got: {chunks[0]['heading']!r}"

    def test_collect_docs_chunks_frontmatter_stripped(self, tmp_path):
        """Frontmatter block is not present in any chunk text."""
        docs_root = tmp_path / "docs"
        eng_dir = docs_root / "engine"
        eng_dir.mkdir(parents=True)
        content = (
            "---\nstatus: authoritative\ntitle: Test Doc\n---\n\n"
            "## Overview\n\nThis is the overview section.\n"
        )
        (eng_dir / "overview.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) >= 1
        for chunk in chunks:
            assert "status: authoritative" not in chunk["text"], \
                f"Frontmatter leaked into chunk text: {chunk['text'][:100]!r}"
            assert "---" not in chunk["text"], \
                f"Frontmatter delimiters leaked into chunk text: {chunk['text'][:100]!r}"

    def test_collect_docs_chunks_empty_body_skipped(self, tmp_path):
        """File with only frontmatter and no body produces 0 chunks."""
        docs_root = tmp_path / "docs"
        eng_dir = docs_root / "engine"
        eng_dir.mkdir(parents=True)
        content = "---\nstatus: authoritative\ntitle: Empty Doc\n---\n"
        (eng_dir / "empty.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) == 0, f"Expected 0 chunks for frontmatter-only file, got {len(chunks)}"

    def test_collect_docs_chunks_emoji_heading_slug(self, tmp_path):
        """Chunk id is ASCII-only even when heading contains emoji; heading preserves emoji."""
        docs_root = tmp_path / "docs"
        eng_dir = docs_root / "engine"
        eng_dir.mkdir(parents=True)
        content = "## \U0001f3c3 Phase 7: Locomotion Routing\n\n" + ("word " * 60) + "\n"
        (eng_dir / "pipeline.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) >= 1
        chunk = chunks[0]
        # id must be ASCII-safe (no emoji)
        chunk_id = chunk["id"]
        assert chunk_id.isascii(), f"Chunk id contains non-ASCII characters: {chunk_id!r}"
        # heading should preserve original text
        assert "Phase 7" in chunk["heading"], f"Heading lost content: {chunk['heading']!r}"

    def test_collect_docs_chunks_large_section_split(self, tmp_path):
        """H2 section >600 words with 2 H3 sub-sections produces 2 chunks (one per H3)."""
        docs_root = tmp_path / "docs"
        eng_dir = docs_root / "engine"
        eng_dir.mkdir(parents=True)
        # Build content: H2 with two H3 sub-sections of ~300 words each
        h3_body = "word " * 300
        content = (
            "## Large Section\n\n"
            "### Sub-Section Alpha\n\n" + h3_body + "\n\n"
            "### Sub-Section Beta\n\n" + h3_body + "\n"
        )
        (eng_dir / "large.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        assert len(chunks) == 2, f"Expected 2 chunks (one per H3), got {len(chunks)}"
        headings = {c["heading"] for c in chunks}
        assert "Sub-Section Alpha" in headings
        assert "Sub-Section Beta" in headings

    def test_collect_docs_chunks_hard_split_overlap(self, tmp_path):
        """H2 section >600 words with no H3 produces multiple chunks with 50-word overlap."""
        docs_root = tmp_path / "docs"
        eng_dir = docs_root / "engine"
        eng_dir.mkdir(parents=True)
        # Unique words to detect overlap: word_0 word_1 ... word_999
        unique_words = [f"word{i}" for i in range(1000)]
        body = " ".join(unique_words)
        content = f"## Big Section\n\n{body}\n"
        (eng_dir / "big.md").write_text(content, encoding="utf-8")

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        # Should produce multiple chunks (total >500 words after H2 line)
        assert len(chunks) >= 2, f"Expected multiple chunks from hard-split, got {len(chunks)}"
        # Each chunk must be <=800 words
        for chunk in chunks:
            wc = len(chunk["text"].split())
            assert wc <= 800, f"Chunk too large: {wc} words"
        # Verify 50-word overlap: last 50 words of chunk N should appear in chunk N+1
        if len(chunks) >= 2:
            chunk0_words = chunks[0]["text"].split()
            chunk1_words = chunks[1]["text"].split()
            overlap_words = chunk0_words[-50:]
            # Check that the first overlap words from chunk0 appear at start of chunk1
            assert chunk1_words[:50] == overlap_words, \
                f"50-word overlap not found between chunk 0 and chunk 1"


# ---------------------------------------------------------------------------
# Group 8 continued — TestDocsCorpusScopeGuard (non-slow)
# ---------------------------------------------------------------------------

class TestDocsCorpusScopeGuard:
    """Group 8: Scope guards ensuring archive/lab never appear in corpus."""

    def test_archive_excluded_from_collect_corpus(self, tmp_path):
        """docs/archive/ files must not appear in _collect_docs_chunks output."""
        docs_root = tmp_path / "docs"
        archive_dir = docs_root / "archive"
        archive_dir.mkdir(parents=True)
        (archive_dir / "old_doc.md").write_text(
            "## Old Section\n\nThis is stale archive content.\n",
            encoding="utf-8",
        )

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        for chunk in chunks:
            assert "docs/archive" not in chunk["path"].replace("\\", "/"), \
                f"Archive path leaked into corpus: {chunk['path']}"

    def test_lab_excluded_from_collect_corpus(self, tmp_path):
        """docs/lab/ files must not appear in _collect_docs_chunks output."""
        docs_root = tmp_path / "docs"
        lab_dir = docs_root / "lab"
        lab_dir.mkdir(parents=True)
        (lab_dir / "experimental.md").write_text(
            "## Experimental\n\nThis is experimental content.\n",
            encoding="utf-8",
        )

        chunks = _ks._collect_docs_chunks(docs_root, tmp_path)

        for chunk in chunks:
            assert "docs/lab" not in chunk["path"].replace("\\", "/"), \
                f"Lab path leaked into corpus: {chunk['path']}"

    def test_collect_corpus_includes_doc_source_type(self, tmp_path):
        """When docs/ has a valid .md file, source_type 'doc_chunk' appears in corpus."""
        _make_minimal_corpus(tmp_path)
        docs_root = tmp_path / "docs"
        mech_dir = docs_root / "mechanics"
        mech_dir.mkdir(parents=True)
        (mech_dir / "test.md").write_text(
            "## Combat Overview\n\nThis covers the basics of combat.\n",
            encoding="utf-8",
        )

        corpus = _ks._collect_corpus(tmp_path)
        source_types = {d["source_type"] for d in corpus}
        assert "doc_chunk" in source_types, \
            f"Expected 'doc_chunk' in corpus source types, got: {source_types}"

    def test_collect_corpus_existing_sources_unaffected(self, tmp_path):
        """Adding docs/ does not change ticket or investigation content."""
        _make_minimal_corpus(tmp_path)
        docs_root = tmp_path / "docs"
        mech_dir = docs_root / "mechanics"
        mech_dir.mkdir(parents=True)
        (mech_dir / "test.md").write_text(
            "## Some Section\n\nSome mechanics content.\n",
            encoding="utf-8",
        )

        corpus = _ks._collect_corpus(tmp_path)
        source_types = {d["source_type"] for d in corpus}

        # All four source types should be present
        assert "ticket" in source_types
        assert "investigation" in source_types
        assert "working_log" in source_types
        assert "doc_chunk" in source_types

        # Ticket text should be unchanged
        ticket_docs = [d for d in corpus if d["source_type"] == "ticket"]
        assert any("stamina" in d["text"].lower() for d in ticket_docs), \
            "Ticket content appears to have changed"


# ---------------------------------------------------------------------------
# Group 9 — Slow build tests with docs corpus (subprocess + tmp_path)
# ---------------------------------------------------------------------------

class TestDocsBuildSummary:
    """Group 9: Build summary includes docs chunks count."""

    @pytest.mark.slow
    def test_build_prints_docs_chunks_count(self, tmp_path):
        """Build output contains 'docs chunks' and count >= 1 when docs/ has .md files."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        docs_root = tmp_path / "docs" / "mechanics"
        docs_root.mkdir(parents=True)
        (docs_root / "test.md").write_text(
            "## Section One\n\nFirst section content with enough words to chunk.\n\n"
            "## Section Two\n\nSecond section with different content about game mechanics.\n",
            encoding="utf-8",
        )
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"build failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        combined = result.stdout + result.stderr
        assert "docs chunks" in combined.lower(), \
            f"Expected 'docs chunks' in build output:\n{combined}"
        # Extract the docs chunks count from output
        import re as _re
        m = _re.search(r"(\d+)\s+docs\s+chunks", combined, _re.IGNORECASE)
        assert m is not None, f"Could not find docs chunks count in: {combined}"
        count = int(m.group(1))
        assert count >= 1, f"Expected at least 1 docs chunk, got {count}"

    @pytest.mark.slow
    def test_build_summary_includes_all_four_sources(self, tmp_path):
        """Build summary mentions all four corpus sources: ticket, investigation, working log, docs."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        docs_root = tmp_path / "docs" / "mechanics"
        docs_root.mkdir(parents=True)
        (docs_root / "test.md").write_text(
            "## Overview\n\nThis covers mechanics overview content.\n",
            encoding="utf-8",
        )
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        combined = result.stdout + result.stderr
        assert "ticket" in combined.lower(), f"'ticket' not in build output:\n{combined}"
        assert "investigation" in combined.lower(), f"'investigation' not in build output:\n{combined}"
        assert "working log" in combined.lower(), f"'working log' not in build output:\n{combined}"
        assert "docs" in combined.lower(), f"'docs' not in build output:\n{combined}"


# ---------------------------------------------------------------------------
# Group 10 — Slow live-query tests (require knowledge-index/knowledge.db)
# ---------------------------------------------------------------------------

_LIVE_DB = _REPO_ROOT / "knowledge-index" / "knowledge.db"


def _live_db_available() -> bool:
    return _LIVE_DB.exists()


class TestLiveQueryDocsMechanics:
    """Group 10: Live query tests against the real knowledge index."""

    @pytest.mark.slow
    def test_query_returns_docs_mechanics_result(self):
        """AC-2: Query about damage formula returns at least one result from docs/mechanics/."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")
        if not _live_db_available():
            pytest.skip("knowledge index not built — run make knowledge-index")

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "query",
                "damage formula attacker vs defender",
                "--top-k", "5",
                "--db-path", str(_LIVE_DB),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1, "No results returned"
        paths = [line.split("\t")[1] for line in lines if "\t" in line]
        assert any("docs/mechanics" in p.replace("\\", "/") for p in paths), \
            f"No result from docs/mechanics/ in: {paths}"

    @pytest.mark.slow
    def test_query_returns_docs_engine_result(self):
        """AC-3: Query about authoritative mutation pipeline returns result from docs/engine/."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")
        if not _live_db_available():
            pytest.skip("knowledge index not built — run make knowledge-index")

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "query",
                "authoritative mutation pipeline phases",
                "--top-k", "5",
                "--db-path", str(_LIVE_DB),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1, "No results returned"
        paths = [line.split("\t")[1] for line in lines if "\t" in line]
        assert any("docs/engine" in p.replace("\\", "/") for p in paths), \
            f"No result from docs/engine/ in: {paths}"

    @pytest.mark.slow
    def test_query_result_has_five_fields(self):
        """AC-4: Every result line has exactly 5 tab-separated fields."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")
        if not _live_db_available():
            pytest.skip("knowledge index not built — run make knowledge-index")

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "query",
                "entity combat stamina",
                "--top-k", "1",
                "--db-path", str(_LIVE_DB),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1, "No results returned"
        parts = lines[0].split("\t")
        assert len(parts) == 8, \
            f"Expected 8 tab-separated fields, got {len(parts)}: {lines[0]!r}"

    @pytest.mark.slow
    def test_query_no_archive_results(self):
        """AC-5: No result path contains docs/archive/ or docs/lab/."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")
        if not _live_db_available():
            pytest.skip("knowledge index not built — run make knowledge-index")

        queries = [
            "combat resolution mechanics",
            "entity stamina fatigue",
            "world evolution ecology",
            "strategic goal hierarchy",
            "economic harvesting resources",
        ]
        for query in queries:
            result = subprocess.run(
                [
                    sys.executable, str(_KS_PATH), "query",
                    query,
                    "--top-k", "10",
                    "--db-path", str(_LIVE_DB),
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
            lines = [l for l in result.stdout.strip().split("\n") if l]
            for line in lines:
                parts = line.split("\t")
                if len(parts) >= 2:
                    path = parts[1].replace("\\", "/")
                    assert "docs/archive/" not in path, \
                        f"Archive result leaked for query '{query}': {path}"
                    assert "docs/lab/" not in path, \
                        f"Lab result leaked for query '{query}': {path}"

    @pytest.mark.slow
    def test_build_docs_chunk_count_exceeds_500(self, tmp_path):
        """AC-1: Full build against real repo reports > 500 docs chunks."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        db_path = tmp_path / "knowledge-index" / "knowledge.db"
        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(_REPO_ROOT),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
            timeout=360,
        )
        assert result.returncode == 0, \
            f"build failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        combined = result.stdout + result.stderr
        import re as _re
        m = _re.search(r"(\d+)\s+docs\s+chunks", combined, _re.IGNORECASE)
        assert m is not None, f"Could not find docs chunks count in: {combined}"
        count = int(m.group(1))
        assert count > 500, f"Expected > 500 docs chunks, got {count}"

    @pytest.mark.slow
    def test_build_completes_under_five_minutes(self, tmp_path):
        """AC-6: Full build completes in under 5 minutes."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        db_path = tmp_path / "knowledge-index" / "knowledge.db"
        start = time.monotonic()
        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(_REPO_ROOT),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
            timeout=360,
        )
        elapsed = time.monotonic() - start
        assert result.returncode == 0, \
            f"build failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert elapsed < 300, f"build took {elapsed:.1f}s — exceeded 5-minute SLA"

    @pytest.mark.slow
    def test_existing_ticket_query_still_works(self):
        """AC-7: Existing ticket/investigation queries still return results < 2s."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")
        if not _live_db_available():
            pytest.skip("knowledge index not built — run make knowledge-index")

        start = time.monotonic()
        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "query",
                "player fatigue during extended combat",
                "--top-k", "5",
                "--db-path", str(_LIVE_DB),
            ],
            capture_output=True,
            text=True,
        )
        elapsed = time.monotonic() - start
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1, "No results returned for existing ticket query"
        # At least one result should come from tickets/done/ or stored_artifacts/
        paths = [line.split("\t")[1] for line in lines if "\t" in line]
        has_ticket_result = any(
            "tickets/done" in p.replace("\\", "/") or "stored_artifacts" in p.replace("\\", "/")
            for p in paths
        )
        assert has_ticket_result, f"No ticket/investigation result in: {paths}"
        assert elapsed < 2.0, f"Query took {elapsed:.2f}s — exceeded 2s SLA"


# ---------------------------------------------------------------------------
# Group A — TestTokenize (unit, non-slow)
# ---------------------------------------------------------------------------

class TestTokenize:
    """Unit tests for _tokenize()."""

    def test_basic_lowercase(self):
        result = _ks._tokenize("Hello World")
        assert result == ["hello", "world"]

    def test_splits_on_punctuation(self):
        result = _ks._tokenize("foo.bar,baz")
        assert result == ["foo", "bar", "baz"]

    def test_preserves_underscores(self):
        result = _ks._tokenize("authoritative_pipeline")
        assert result == ["authoritative_pipeline"]

    def test_preserves_numbers(self):
        result = _ks._tokenize("phase7 step3")
        assert result == ["phase7", "step3"]

    def test_camelcase_not_split(self):
        result = _ks._tokenize("WorldRepository")
        assert result == ["worldrepository"]

    def test_empty_string(self):
        result = _ks._tokenize("")
        assert result == []

    def test_only_punctuation(self):
        result = _ks._tokenize("!@#$%")
        assert result == []

    def test_mixed_content(self):
        result = _ks._tokenize("apply_packet() -> Result")
        assert "apply_packet" in result
        assert "result" in result


# ---------------------------------------------------------------------------
# Group B — TestBm25BuildLoad (unit, non-slow)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _bm25_deps_available(), reason="rank_bm25/numpy not installed")
class TestBm25BuildLoad:
    """Unit tests for _build_bm25_index() and _load_bm25()."""

    def test_build_creates_pkl(self, tmp_path):
        corpus = [
            {"id": "doc1", "text": "The combat engine resolves attacks"},
            {"id": "doc2", "text": "WorldRepository stores world state"},
        ]
        bm25_path = tmp_path / "bm25.pkl"
        _ks._build_bm25_index(corpus, bm25_path)
        assert bm25_path.exists(), "bm25.pkl was not created"

    def test_build_pkl_is_valid_pickle(self, tmp_path):
        corpus = [
            {"id": "doc1", "text": "stamina pressure entity"},
            {"id": "doc2", "text": "economic trade route"},
        ]
        bm25_path = tmp_path / "bm25.pkl"
        _ks._build_bm25_index(corpus, bm25_path)
        bm25_obj, doc_ids = _ks._load_bm25(bm25_path)
        assert bm25_obj is not None, "Loaded BM25 object is None"
        assert doc_ids == ["doc1", "doc2"], f"doc_ids mismatch: {doc_ids}"

    def test_build_doc_ids_order_preserved(self, tmp_path):
        corpus = [{"id": f"doc{i}", "text": f"content {i}"} for i in range(5)]
        bm25_path = tmp_path / "bm25.pkl"
        _ks._build_bm25_index(corpus, bm25_path)
        _, doc_ids = _ks._load_bm25(bm25_path)
        assert doc_ids == [f"doc{i}" for i in range(5)]

    def test_load_missing_file_returns_none(self, tmp_path):
        bm25_obj, doc_ids = _ks._load_bm25(tmp_path / "nonexistent.pkl")
        assert bm25_obj is None
        assert doc_ids == []

    def test_load_corrupt_file_returns_none(self, tmp_path):
        corrupt = tmp_path / "bm25.pkl"
        corrupt.write_bytes(b"not a valid pickle")
        bm25_obj, doc_ids = _ks._load_bm25(corrupt)
        assert bm25_obj is None
        assert doc_ids == []

    def test_load_missing_prints_warning(self, tmp_path, capsys):
        _ks._load_bm25(tmp_path / "missing.pkl")
        captured = capsys.readouterr()
        assert "warning" in captured.err.lower() or "not found" in captured.err.lower()


# ---------------------------------------------------------------------------
# Group C — TestHybridScore and TestComputeBoosts (unit, non-slow)
# ---------------------------------------------------------------------------

class TestHybridScore:
    """Unit tests for _hybrid_score()."""

    def test_all_zeros(self):
        result = _ks._hybrid_score(0.0, 0.0, 0.0, 0.0, 0.0)
        assert result == 0.0

    def test_all_ones(self):
        result = _ks._hybrid_score(1.0, 1.0, 1.0, 1.0, 1.0)
        assert abs(result - 1.0) < 1e-9

    def test_weights_sum_to_one(self):
        # 0.55 + 0.25 + 0.10 + 0.05 + 0.05 = 1.0
        assert abs(0.55 + 0.25 + 0.10 + 0.05 + 0.05 - 1.0) < 1e-9

    def test_semantic_only(self):
        result = _ks._hybrid_score(1.0, 0.0, 0.0, 0.0, 0.0)
        assert abs(result - 0.55) < 1e-9

    def test_keyword_only(self):
        result = _ks._hybrid_score(0.0, 1.0, 0.0, 0.0, 0.0)
        assert abs(result - 0.25) < 1e-9

    def test_title_boost_only(self):
        result = _ks._hybrid_score(0.0, 0.0, 1.0, 0.0, 0.0)
        assert abs(result - 0.10) < 1e-9

    def test_heading_boost_only(self):
        result = _ks._hybrid_score(0.0, 0.0, 0.0, 1.0, 0.0)
        assert abs(result - 0.05) < 1e-9

    def test_code_boost_only(self):
        result = _ks._hybrid_score(0.0, 0.0, 0.0, 0.0, 1.0)
        assert abs(result - 0.05) < 1e-9

    def test_partial_scores(self):
        result = _ks._hybrid_score(0.8, 0.6, 1.0, 0.0, 0.0)
        expected = 0.8 * 0.55 + 0.6 * 0.25 + 1.0 * 0.10
        assert abs(result - expected) < 1e-9


class TestComputeBoosts:
    """Unit tests for _compute_boosts()."""

    def test_title_boost_match(self):
        title, _, _ = _ks._compute_boosts(["worldrepository"], "architecture/WorldRepository", "", "")
        assert title == 1.0

    def test_title_boost_no_match(self):
        title, _, _ = _ks._compute_boosts(["combat"], "architecture/WorldRepository", "", "")
        assert title == 0.0

    def test_heading_boost_match(self):
        _, heading, _ = _ks._compute_boosts(["pipeline"], "", "The Authoritative Pipeline", "")
        assert heading == 1.0

    def test_heading_boost_no_match(self):
        _, heading, _ = _ks._compute_boosts(["stamina"], "", "Economic Laws", "")
        assert heading == 0.0

    def test_code_boost_match(self):
        _, _, code = _ks._compute_boosts(["apply_packet"], "", "", "Call `apply_packet` here.")
        assert code == 1.0

    def test_code_boost_no_match(self):
        _, _, code = _ks._compute_boosts(["stamina"], "", "", "Call `apply_packet` here.")
        assert code == 0.0

    def test_all_zero_on_empty(self):
        title, heading, code = _ks._compute_boosts([], "", "", "")
        assert title == 0.0
        assert heading == 0.0
        assert code == 0.0

    def test_code_boost_case_insensitive(self):
        _, _, code = _ks._compute_boosts(["worldrepository"], "", "", "Use `WorldRepository` here.")
        assert code == 1.0


# ---------------------------------------------------------------------------
# Group D — Extend TestBuildHappyPath: bm25.pkl tests (slow)
# ---------------------------------------------------------------------------

class TestBuildProducesBm25:
    """Group D: slow tests verifying build produces bm25.pkl."""

    @pytest.mark.slow
    def test_build_produces_bm25_pkl(self, tmp_path):
        """AC1: build also produces knowledge-index/bm25.pkl."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"build failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        bm25_path = tmp_path / "knowledge-index" / "bm25.pkl"
        assert bm25_path.exists(), "bm25.pkl was not created alongside knowledge.db"

    @pytest.mark.slow
    def test_build_bm25_pkl_is_valid_pickle(self, tmp_path):
        """bm25.pkl produced by build is a valid (BM25Okapi, doc_ids) pickle."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        bm25_path = tmp_path / "knowledge-index" / "bm25.pkl"
        bm25_obj, doc_ids = _ks._load_bm25(bm25_path)
        assert bm25_obj is not None, "Loaded BM25 object is None"
        assert isinstance(doc_ids, list), f"doc_ids should be a list, got {type(doc_ids)}"
        assert len(doc_ids) > 0, "doc_ids list is empty"

    @pytest.mark.slow
    def test_build_prints_bm25_message(self, tmp_path):
        """build prints BM25 index message including doc count."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        result = subprocess.run(
            [
                sys.executable, str(_KS_PATH), "build",
                "--corpus-root", str(tmp_path),
                "--db-path", str(db_path),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        combined = result.stdout + result.stderr
        assert "bm25" in combined.lower(), f"Expected BM25 message in output:\n{combined}"


# ---------------------------------------------------------------------------
# Group E — TestQueryModeRouting (slow)
# ---------------------------------------------------------------------------

class TestQueryModeRouting:
    """Group E: slow tests verifying --mode routing works correctly."""

    @pytest.mark.slow
    def test_query_mode_hybrid_default(self, tmp_path):
        """Default mode (no --mode flag) produces 8-field output."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [sys.executable, str(_KS_PATH), "build",
             "--corpus-root", str(tmp_path), "--db-path", str(db_path)],
            capture_output=True, text=True, check=True,
        )

        result = subprocess.run(
            [sys.executable, str(_KS_PATH), "query", "stamina",
             "--top-k", "1", "--db-path", str(db_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1
        assert len(lines[0].split("\t")) == 8, \
            f"Expected 8 fields in hybrid mode, got: {lines[0]!r}"

    @pytest.mark.slow
    def test_query_mode_vector_skips_bm25(self, tmp_path):
        """--mode vector completes without loading bm25.pkl."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [sys.executable, str(_KS_PATH), "build",
             "--corpus-root", str(tmp_path), "--db-path", str(db_path)],
            capture_output=True, text=True, check=True,
        )

        # Remove bm25.pkl to confirm vector mode doesn't need it
        bm25_path = tmp_path / "knowledge-index" / "bm25.pkl"
        if bm25_path.exists():
            bm25_path.unlink()

        result = subprocess.run(
            [sys.executable, str(_KS_PATH), "query", "stamina",
             "--top-k", "1", "--db-path", str(db_path), "--mode", "vector"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"vector mode failed: {result.stderr}"
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1
        # vector mode should NOT print BM25 warning since it never attempts to load it
        assert "bm25" not in result.stderr.lower(), \
            f"vector mode should not mention bm25: {result.stderr}"

    @pytest.mark.slow
    def test_query_mode_keyword_skips_embedding(self, tmp_path):
        """--mode keyword with bm25.pkl returns results without embedding."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [sys.executable, str(_KS_PATH), "build",
             "--corpus-root", str(tmp_path), "--db-path", str(db_path)],
            capture_output=True, text=True, check=True,
        )

        result = subprocess.run(
            [sys.executable, str(_KS_PATH), "query", "stamina",
             "--top-k", "2", "--db-path", str(db_path), "--mode", "keyword"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"keyword mode failed: {result.stderr}"


# ---------------------------------------------------------------------------
# Group F — TestQueryScoreFields (slow)
# ---------------------------------------------------------------------------

class TestQueryScoreFields:
    """Group F: verify score fields in 8-field output."""

    @pytest.mark.slow
    def test_query_output_has_8_fields(self, tmp_path):
        """Each result line has exactly 8 tab-separated fields."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [sys.executable, str(_KS_PATH), "build",
             "--corpus-root", str(tmp_path), "--db-path", str(db_path)],
            capture_output=True, text=True, check=True,
        )
        result = subprocess.run(
            [sys.executable, str(_KS_PATH), "query", "stamina",
             "--top-k", "3", "--db-path", str(db_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1
        for line in lines:
            parts = line.split("\t")
            assert len(parts) == 8, f"Expected 8 fields, got {len(parts)}: {line!r}"

    @pytest.mark.slow
    def test_query_output_score_fields_are_floats(self, tmp_path):
        """final_score, semantic_score, keyword_score fields are valid float strings."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [sys.executable, str(_KS_PATH), "build",
             "--corpus-root", str(tmp_path), "--db-path", str(db_path)],
            capture_output=True, text=True, check=True,
        )
        result = subprocess.run(
            [sys.executable, str(_KS_PATH), "query", "trade economic",
             "--top-k", "2", "--db-path", str(db_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1
        for line in lines:
            parts = line.split("\t")
            assert len(parts) == 8
            final_score, semantic_score, keyword_score = parts[4], parts[5], parts[6]
            for field_name, field_val in [
                ("final_score", final_score),
                ("semantic_score", semantic_score),
                ("keyword_score", keyword_score),
            ]:
                try:
                    val = float(field_val)
                    assert 0.0 <= val <= 1.0, \
                        f"{field_name}={val} out of [0,1] range"
                except ValueError:
                    raise AssertionError(
                        f"{field_name} is not a float: {field_val!r}"
                    )

    @pytest.mark.slow
    def test_query_hybrid_final_score_in_range(self, tmp_path):
        """Hybrid final_score is in [0.0, 1.0] for all result rows."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [sys.executable, str(_KS_PATH), "build",
             "--corpus-root", str(tmp_path), "--db-path", str(db_path)],
            capture_output=True, text=True, check=True,
        )
        result = subprocess.run(
            [sys.executable, str(_KS_PATH), "query", "stamina combat",
             "--top-k", "5", "--db-path", str(db_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        lines = [l for l in result.stdout.strip().split("\n") if l]
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 5:
                final = float(parts[4])
                assert 0.0 <= final <= 1.0, f"final_score {final} out of range"


# ---------------------------------------------------------------------------
# Group G — Extend TestGracefulDegradation: missing bm25.pkl
# ---------------------------------------------------------------------------

class TestMissingBm25Fallback:
    """Group G: fallback behavior when bm25.pkl is absent."""

    @pytest.mark.slow
    def test_query_missing_bm25_fallback_vector_only(self, tmp_path):
        """AC5: If bm25.pkl is missing, hybrid query falls back to vector-only, no exception."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        # Build vector index only (no bm25.pkl)
        subprocess.run(
            [sys.executable, str(_KS_PATH), "build",
             "--corpus-root", str(tmp_path), "--db-path", str(db_path)],
            capture_output=True, text=True, check=True,
        )

        # Delete bm25.pkl if it was created
        bm25_path = tmp_path / "knowledge-index" / "bm25.pkl"
        if bm25_path.exists():
            bm25_path.unlink()

        result = subprocess.run(
            [sys.executable, str(_KS_PATH), "query", "stamina",
             "--top-k", "2", "--db-path", str(db_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, \
            f"query should not fail when bm25.pkl missing:\n{result.stderr}"
        lines = [l for l in result.stdout.strip().split("\n") if l]
        assert len(lines) >= 1, "Expected results even without bm25.pkl"

    @pytest.mark.slow
    def test_query_missing_bm25_warning_text(self, tmp_path):
        """AC5: Missing bm25.pkl emits exactly one warning mentioning bm25 or not found."""
        if not _deps_available():
            pytest.skip("sentence-transformers / sqlite-vec not installed")

        _make_minimal_corpus(tmp_path)
        db_path = tmp_path / "knowledge-index" / "knowledge.db"

        subprocess.run(
            [sys.executable, str(_KS_PATH), "build",
             "--corpus-root", str(tmp_path), "--db-path", str(db_path)],
            capture_output=True, text=True, check=True,
        )

        bm25_path = tmp_path / "knowledge-index" / "bm25.pkl"
        if bm25_path.exists():
            bm25_path.unlink()

        result = subprocess.run(
            [sys.executable, str(_KS_PATH), "query", "stamina",
             "--top-k", "1", "--db-path", str(db_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        combined = result.stderr
        assert "warning" in combined.lower() or "not found" in combined.lower(), \
            f"Expected warning about missing bm25.pkl:\n{combined}"


# ---------------------------------------------------------------------------
# Group I — Extend TestPyprojectDeps: rank-bm25 entry
# ---------------------------------------------------------------------------

class TestPyprojectRankBm25:
    """Group I: verify rank-bm25 is in knowledge optional-dependencies."""

    def test_knowledge_group_contains_rank_bm25(self):
        """knowledge optional-deps must include rank-bm25>=0.2.2."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        pyproject = _REPO_ROOT / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        knowledge_deps = data.get("project", {}).get("optional-dependencies", {}).get("knowledge", [])

        dep_names = [d.split(">=")[0].split("==")[0].strip() for d in knowledge_deps]
        assert "rank-bm25" in dep_names, \
            f"rank-bm25 not in knowledge deps: {knowledge_deps}"

    def test_rank_bm25_not_in_core_dependencies(self):
        """rank-bm25 must NOT appear in core [project.dependencies]."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]

        pyproject = _REPO_ROOT / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        core_deps = data.get("project", {}).get("dependencies", [])
        core_names = [d.split(">=")[0].split("==")[0].strip() for d in core_deps]
        assert "rank-bm25" not in core_names, \
            "rank-bm25 must NOT be in core [project.dependencies]"


# ---------------------------------------------------------------------------
# Group J: Manifest and incremental rebuild helpers
# ---------------------------------------------------------------------------

class TestManifestHelpers:
    """Group J: _write_manifest and _load_manifest round-trip."""

    def _make_corpus(self, tmp_path: Path) -> tuple[list[dict], Path]:
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_text("hello")
        f2.write_text("world")
        corpus = [
            {"id": "a", "path": str(f1), "text": "hello", "source_type": "doc_chunk"},
            {"id": "b", "path": str(f2), "text": "world", "source_type": "doc_chunk"},
        ]
        db = tmp_path / "knowledge.db"
        return corpus, db

    def test_write_and_load_round_trip(self, tmp_path):
        corpus, db = self._make_corpus(tmp_path)
        _ks._write_manifest(corpus, db)
        manifest = _ks._load_manifest(db)
        assert str(corpus[0]["path"]) in manifest
        assert str(corpus[1]["path"]) in manifest

    def test_manifest_stores_mtime(self, tmp_path):
        corpus, db = self._make_corpus(tmp_path)
        _ks._write_manifest(corpus, db)
        manifest = _ks._load_manifest(db)
        for doc in corpus:
            p = doc["path"]
            import os
            assert abs(manifest[p] - os.path.getmtime(p)) < 0.1

    def test_load_manifest_returns_empty_when_missing(self, tmp_path):
        db = tmp_path / "nonexistent.db"
        manifest = _ks._load_manifest(db)
        assert manifest == {}

    def test_manifest_file_written_to_index_dir(self, tmp_path):
        corpus, db = self._make_corpus(tmp_path)
        _ks._write_manifest(corpus, db)
        manifest_path = tmp_path / "manifest.json"
        assert manifest_path.exists()

    def test_incremental_fast_path_when_nothing_changed(self, tmp_path, monkeypatch):
        """When manifest matches current mtimes, incremental reports up to date."""
        corpus, db = self._make_corpus(tmp_path)
        # Write manifest first
        _ks._write_manifest(corpus, db)

        # Monkeypatch _collect_corpus to return the same corpus
        monkeypatch.setattr(_ks, "_collect_corpus", lambda root: corpus)
        # Monkeypatch db to point to tmp_path/knowledge.db (must exist)
        db.write_bytes(b"fake")

        import types, io
        args = types.SimpleNamespace(
            corpus_root=str(tmp_path),
            db_path=str(db),
            incremental=True,
        )
        # Capture stdout
        import io as _io
        buf = _io.StringIO()
        monkeypatch.setattr("sys.stdout", buf)
        result = _ks.cmd_build_incremental(args)
        output = buf.getvalue()
        assert result == 0
        assert "up to date" in output.lower() or "0 files changed" in output.lower()

    def test_build_incremental_noop_leaves_stale_doc_id_documented(self, tmp_path, monkeypatch):
        """Locks in the (now-understood) contract that cmd_build_incremental()'s only
        change-detection signal is per-path mtime, not corpus content/derivation logic — so an
        in-process doc_id-scheme change with no corpus-tracked file mtime change is a silent
        no-op that leaves knowledge.db holding stale doc_id values. This is not a bug being
        fixed here; it is a guard against a future "optimization" that swaps a required full
        rebuild for --incremental without a deliberate, scoped change to add scheme versioning.
        See TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION."""
        corpus, db = self._make_corpus(tmp_path)
        _ks._write_manifest(corpus, db)
        db_bytes_before = b"pre-existing knowledge.db contents"
        db.write_bytes(db_bytes_before)

        # Simulate a doc_id-scheme change: _collect_corpus now returns different doc_id/id
        # values for the same on-disk paths (no mtime change), mirroring this ticket's fix.
        changed_corpus = [
            {**doc, "id": doc["id"] + "-new-scheme", "doc_id": doc.get("doc_id", doc["id"]) + "-new-scheme"}
            for doc in corpus
        ]
        monkeypatch.setattr(_ks, "_collect_corpus", lambda root: changed_corpus)

        args = types.SimpleNamespace(
            corpus_root=str(tmp_path),
            db_path=str(db),
            incremental=True,
        )
        result = _ks.cmd_build_incremental(args)

        assert result == 0
        assert db.read_bytes() == db_bytes_before, (
            "cmd_build_incremental() must not rewrite knowledge.db when no tracked path's "
            "mtime changed, even if in-process derivation logic did — a pure doc_id-scheme "
            "change requires a full `make knowledge-index` rebuild, not --incremental."
        )

    def test_hook_script_is_executable_shell(self):
        hook = _REPO_ROOT / "tools" / "hooks" / "post-commit-reindex.sh"
        assert hook.exists(), "post-commit-reindex.sh missing"
        content = hook.read_text()
        assert content.startswith("#!/usr/bin/env bash")
        assert "knowledge_search.py" in content
        assert "incremental" in content


# ---------------------------------------------------------------------------
# Group H — TestHybridFusionWiring (TCK-20260729-HYBRID-RETRIEVAL-FUSION)
# ---------------------------------------------------------------------------

class _FakeBM25ScoresH(list):
    def max(self):
        return max(self) if self else 0.0


class _FakeBM25H:
    """Minimal get_scores()-only stand-in for rank_bm25.BM25Okapi -- picklable (module-level),
    no rank_bm25 dependency required."""

    def get_scores(self, tokens):
        return _FakeBM25ScoresH([0.0, 9.0])


class TestHybridFusionWiring:
    """Proves cmd_query()'s hybrid branch routes through
    hybrid_retrieval.hybrid_fuse_and_filter instead of the old dense-candidate-gated
    ANN-then-BM25-lookup sequence, and that the fix surfaces a lexical-only exact match outside
    the dense channel's candidate cut (AC1) -- exercised in-process against the real function,
    with only the sqlite-vec-dependent ANN query itself (`_dense_candidates`) stubbed, so this
    runs without sentence-transformers/sqlite-vec installed.
    """

    def test_lexical_only_match_surfaced_through_cmd_query(self, tmp_path, monkeypatch, capsys):
        if not _numpy_available():
            pytest.skip("numpy not installed")
        fake_db = tmp_path / "knowledge.db"
        conn = sqlite3.connect(str(fake_db))
        conn.execute(
            """
            CREATE TABLE knowledge_docs (
                rowid       INTEGER PRIMARY KEY,
                doc_id      TEXT NOT NULL,
                path        TEXT NOT NULL,
                text        TEXT NOT NULL,
                source_type TEXT NOT NULL,
                heading     TEXT NOT NULL DEFAULT '',
                section     TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.executemany(
            "INSERT INTO knowledge_docs (rowid, doc_id, path, text, source_type, heading, section) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (0, "doc-a", "docs/a.md", "alpha text", "doc_chunk", "A", "docs"),
                (1, "doc-rare", "docs/rare.md", "zzqfrobnicate_widget appears here",
                 "doc_chunk", "Rare", "docs"),
            ],
        )
        conn.commit()
        conn.close()

        # Dense channel never surfaces doc-rare -- the confirmed bug's exact shape.
        monkeypatch.setattr(
            _hr, "_dense_candidates",
            lambda conn, query_vec_bytes, dense_candidate_k: [
                (0, "doc-a", "docs/a.md", "A", "docs", "alpha text", "doc_chunk", 0.1),
            ],
        )

        bm25_path = fake_db.parent / "bm25.pkl"
        with open(bm25_path, "wb") as fh:
            pickle.dump((_FakeBM25H(), ["doc-a", "doc-rare"]), fh)

        fake_st_module = types.ModuleType("sentence_transformers")

        class _FakeArray(list):
            def tolist(self):
                return list(self)

        class _FakeModel:
            def __init__(self, *_a, **_kw):
                pass

            def encode(self, texts, **_kw):
                return _FakeArray([_FakeArray([0.0] * 8) for _ in texts])

        fake_st_module.SentenceTransformer = _FakeModel
        fake_vec_module = types.ModuleType("sqlite_vec")
        fake_vec_module.load = lambda conn: None
        monkeypatch.setitem(sys.modules, "sentence_transformers", fake_st_module)
        monkeypatch.setitem(sys.modules, "sqlite_vec", fake_vec_module)

        args = types.SimpleNamespace(
            query="zzqfrobnicate_widget", top_k=5, db_path=str(fake_db), mode="hybrid"
        )
        rc = _ks.cmd_query(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "doc-rare" in out, f"lexical-only hit missing from hybrid cmd_query output:\n{out}"
