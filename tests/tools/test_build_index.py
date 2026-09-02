"""
Tests for tools/agent-monitoring/build_index.py.

Groups:
  1. build happy path + schema             (AC1)
  2. source files byte-identical            (AC2)
  3. resolved_status / completeness parity  (AC3, AC4)
  4. legacy-shape regression guards
  5. row-count stability across reruns      (AC5)
  6. Makefile target + .gitignore           (AC6)
  7. architecture guards (anti-drift)
"""
import hashlib
import importlib.util
import json
import sqlite3
import subprocess
import sys
import types
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_MODULE_PATH = _REPO_ROOT / "tools" / "agent-monitoring" / "build_index.py"


def _load_module() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("build_index", _MODULE_PATH)
    mod: types.ModuleType = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_bi = _load_module()

_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from generate_retro import _resolve_status  # noqa: E402
from validate import _record_is_complete  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_BASE_RUN = {
    "run_id": "TCK-FAKE",
    "start_ts": "2026-07-08T00:00:00Z",
    "end_ts": "2026-07-08T01:00:00Z",
    "workflow": "implement-ticket",
    "tier": "standard",
    "final_status": "DONE",
}

_TYPE_CHECKER_LEGACY_RECORD = {
    "run_id": "TCK-20260623-TYPE-CHECKER",
    "ticket_id": "TCK-20260623-TYPE-CHECKER",
    "tier": "standard",
    "phase": "implement",
    "ts": "2026-06-23T14:36:28Z",
    "agent": "claude-sonnet-4-6",
    "outcome": "success",
    "files_changed": ["pyproject.toml"],
}

_OFFSCHEMA_TOOLS_RECORDS = [
    {
        "tool": "implement-epic",
        "last_run": "2026-06-28T04:10:00Z",
        "result": "DONE 1/6",
        "tickets": ["TCK-A"],
    },
    {
        "run_id": "TCK-20260628-SIMQ-E1-FOUNDATION",
        "ts": "2026-06-28T00:00:00Z",
        "tools_used": ["Read", "Write"],
        "files_written": 20,
    },
    {
        "session_id": "sess-1",
        "run_id": "TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP",
        "seq": 4,
        "ts": "2026-07-16T12:06:04",
    },
]


def _write_jsonl(path: Path, records: list) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + ("\n" if records else ""), encoding="utf-8")


def _make_corpus(tmp_path: Path, runs=None, events=None, tools=None) -> dict:
    runs_path = tmp_path / "runs.jsonl"
    events_path = tmp_path / "events.jsonl"
    tools_path = tmp_path / "tools.jsonl"
    db_path = tmp_path / "index" / "monitoring.db"

    _write_jsonl(runs_path, runs or [])
    _write_jsonl(events_path, events or [])
    _write_jsonl(tools_path, tools or [])

    return {
        "runs_path": runs_path,
        "events_path": events_path,
        "tools_path": tools_path,
        "db_path": db_path,
    }


def _args(paths: dict) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        runs_file=str(paths["runs_path"]),
        events_file=str(paths["events_path"]),
        tools_file=str(paths["tools_path"]),
        db_path=str(paths["db_path"]),
    )


# ---------------------------------------------------------------------------
# Group 1 — build happy path + schema (AC1)
# ---------------------------------------------------------------------------

class TestBuildHappyPath:

    def test_build_creates_gitignored_sqlite_db(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            runs=[dict(_BASE_RUN)],
            events=[{"run_id": "TCK-FAKE", "seq": 1, "phase": "Implement", "agent": "implementer"}],
            tools=[{"run_id": "TCK-FAKE", "seq": 1, "tool": "Read"}],
        )
        exit_code = _bi.build(_args(paths))

        assert exit_code == 0
        assert paths["db_path"].exists()

        conn = sqlite3.connect(str(paths["db_path"]))
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"runs", "events", "tools"} <= tables
        assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM tools").fetchone()[0] == 1
        conn.close()


# ---------------------------------------------------------------------------
# Group 1b — sharded tools/ directory source (TCK-20260902-MONITORING-SHARD-CONSUMERS)
# ---------------------------------------------------------------------------

class TestShardedToolsSource:

    def test_build_index_reads_multiple_shard_files_from_directory(self, tmp_path):
        runs_path = tmp_path / "runs.jsonl"
        events_path = tmp_path / "events.jsonl"
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        db_path = tmp_path / "index" / "monitoring.db"

        _write_jsonl(runs_path, [])
        _write_jsonl(events_path, [])
        _write_jsonl(
            tools_dir / "tools-2026-W01.jsonl",
            [
                {"run_id": "TCK-A", "seq": 1, "tool": "Read"},
                {"run_id": "TCK-A", "seq": 2, "tool": "Edit"},
            ],
        )
        _write_jsonl(
            tools_dir / "tools-2026-W02.jsonl",
            [
                {"run_id": "TCK-B", "seq": 1, "tool": "Read"},
                {"run_id": "TCK-B", "seq": 2, "tool": "Bash"},
                {"run_id": "TCK-B", "seq": 3, "tool": "Write"},
            ],
        )

        args = types.SimpleNamespace(
            runs_file=str(runs_path),
            events_file=str(events_path),
            tools_file=str(tools_dir),
            db_path=str(db_path),
        )
        exit_code = _bi.build(args)
        assert exit_code == 0

        conn = sqlite3.connect(str(db_path))
        assert conn.execute("SELECT COUNT(*) FROM tools").fetchone()[0] == 5
        conn.close()

    def test_build_index_includes_unknown_week_shard(self, tmp_path):
        runs_path = tmp_path / "runs.jsonl"
        events_path = tmp_path / "events.jsonl"
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        db_path = tmp_path / "index" / "monitoring.db"

        _write_jsonl(runs_path, [])
        _write_jsonl(events_path, [])
        _write_jsonl(
            tools_dir / "tools-2026-W05.jsonl",
            [{"run_id": "TCK-A", "seq": 1, "tool": "Read"}],
        )
        _write_jsonl(
            tools_dir / "tools-unknown-week.jsonl",
            [{"run_id": "TCK-B", "seq": 1, "tool": "Bash"}],
        )

        args = types.SimpleNamespace(
            runs_file=str(runs_path),
            events_file=str(events_path),
            tools_file=str(tools_dir),
            db_path=str(db_path),
        )
        exit_code = _bi.build(args)
        assert exit_code == 0

        conn = sqlite3.connect(str(db_path))
        assert conn.execute("SELECT COUNT(*) FROM tools").fetchone()[0] == 2
        run_ids = {row[0] for row in conn.execute("SELECT run_id FROM tools")}
        assert run_ids == {"TCK-A", "TCK-B"}
        conn.close()

    def test_build_index_glob_result_is_sorted(self, tmp_path):
        runs_path = tmp_path / "runs.jsonl"
        events_path = tmp_path / "events.jsonl"
        tools_dir = tmp_path / "tools"
        tools_dir.mkdir()
        db_path = tmp_path / "index" / "monitoring.db"

        _write_jsonl(runs_path, [])
        _write_jsonl(events_path, [])
        # Write the chronologically-later shard to disk FIRST, so an unsorted
        # glob (filesystem/creation order) would concatenate out of order.
        _write_jsonl(
            tools_dir / "tools-2026-W10.jsonl",
            [{"run_id": "TCK-LATER", "seq": 1, "tool": "Read"}],
        )
        _write_jsonl(
            tools_dir / "tools-2026-W03.jsonl",
            [{"run_id": "TCK-EARLIER", "seq": 1, "tool": "Read"}],
        )

        args = types.SimpleNamespace(
            runs_file=str(runs_path),
            events_file=str(events_path),
            tools_file=str(tools_dir),
            db_path=str(db_path),
        )
        exit_code = _bi.build(args)
        assert exit_code == 0

        conn = sqlite3.connect(str(db_path))
        rows = [row[0] for row in conn.execute("SELECT run_id FROM tools ORDER BY id")]
        conn.close()
        assert rows == ["TCK-EARLIER", "TCK-LATER"]


# ---------------------------------------------------------------------------
# Group 2 — source files byte-identical after build (AC2)
# ---------------------------------------------------------------------------

class TestReadOnlyGuarantee:

    def test_source_jsonl_files_byte_identical_after_build(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            runs=[dict(_BASE_RUN), _TYPE_CHECKER_LEGACY_RECORD],
            events=[{"run_id": "TCK-FAKE", "seq": 1, "phase": "Implement", "agent": "implementer"}],
            tools=[{"run_id": "TCK-FAKE", "seq": 1, "tool": "Read"}] + _OFFSCHEMA_TOOLS_RECORDS,
        )

        def _hashes():
            return {
                name: hashlib.sha256(paths[f"{name}_path"].read_bytes()).hexdigest()
                for name in ("runs", "events", "tools")
            }

        before = _hashes()
        _bi.build(_args(paths))
        after = _hashes()

        assert before == after


# ---------------------------------------------------------------------------
# Group 3 — resolved_status / completeness parity (AC3, AC4)
# ---------------------------------------------------------------------------

class TestNormalizationParity:

    def test_resolved_status_matches_generate_retro_resolve_status(self, tmp_path):
        records = [
            dict(_BASE_RUN, run_id="TCK-A", final_status="DONE"),
            dict(_BASE_RUN, run_id="TCK-B", final_status=None, status="complete"),
            dict(_BASE_RUN, run_id="TCK-C", final_status=None, status=None),
        ]
        paths = _make_corpus(tmp_path, runs=records)
        _bi.build(_args(paths))

        conn = sqlite3.connect(str(paths["db_path"]))
        for record in records:
            row = conn.execute(
                "SELECT resolved_status FROM runs WHERE run_id = ?", (record["run_id"],)
            ).fetchone()
            assert row[0] == _resolve_status(record)
        conn.close()

    def test_completeness_matches_validate_legacy_allowlists(self, tmp_path):
        records = [
            dict(_BASE_RUN, run_id="TCK-D", end_ts=None, final_status="DONE"),
            dict(_BASE_RUN, run_id="TCK-E", end_ts=None, final_status=None, status="NEEDS_HUMAN_INPUT"),
            dict(_BASE_RUN, run_id="TCK-F", end_ts=None, final_status=None, status=None),
            dict(_BASE_RUN, run_id="TCK-G", end_ts="2026-07-09T00:00:00Z", final_status=None, status=None),
        ]
        paths = _make_corpus(tmp_path, runs=records)
        _bi.build(_args(paths))

        conn = sqlite3.connect(str(paths["db_path"]))
        for record in records:
            row = conn.execute(
                "SELECT is_complete FROM runs WHERE run_id = ?", (record["run_id"],)
            ).fetchone()
            expected = 1 if _record_is_complete(record) else 0
            assert row[0] == expected
        conn.close()


# ---------------------------------------------------------------------------
# Group 4 — legacy-shape regression guards
# ---------------------------------------------------------------------------

class TestLegacyShapeGuards:

    def test_type_checker_legacy_shape_does_not_crash_build(self, tmp_path):
        paths = _make_corpus(tmp_path, runs=[_TYPE_CHECKER_LEGACY_RECORD])

        exit_code = _bi.build(_args(paths))

        assert exit_code == 0
        conn = sqlite3.connect(str(paths["db_path"]))
        row = conn.execute(
            "SELECT resolved_status FROM runs WHERE run_id = ?",
            (_TYPE_CHECKER_LEGACY_RECORD["run_id"],),
        ).fetchone()
        assert row[0] is None
        conn.close()

    def test_build_index_skips_offschema_tools_records(self, tmp_path, capsys):
        interactive_use_record = {
            "session_id": "sess-2", "run_id": None, "seq": None, "phase": None, "agent": None,
            "ts": "2026-07-28T00:00:00Z", "tool": "Bash", "input_summary": "ls", "status": "ok",
            "duration_ms": 10,
        }
        paths = _make_corpus(
            tmp_path,
            tools=[{"run_id": "TCK-FAKE", "seq": 1, "tool": "Read"}, interactive_use_record]
            + _OFFSCHEMA_TOOLS_RECORDS,
        )

        exit_code = _bi.build(_args(paths))
        captured = capsys.readouterr()

        assert exit_code == 0
        conn = sqlite3.connect(str(paths["db_path"]))
        # 2 valid rows: the run-scoped call and the interactive-use call (run_id=null/seq=null
        # is a legitimate, present-but-null shape — distinct from the 3 off-schema records
        # below, which are missing the run_id/seq/tool *keys* outright).
        assert conn.execute("SELECT COUNT(*) FROM tools").fetchone()[0] == 2
        conn.close()
        assert captured.err.count("WARNING: tools.jsonl record skipped") == 3

    def test_events_table_tolerates_duplicate_run_id_seq(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            events=[
                {"run_id": "TCK-COLLIDED", "seq": 1, "phase": "Scope", "agent": "ticket-scoper"},
                {"run_id": "TCK-COLLIDED", "seq": 1, "phase": "Scope", "agent": "ticket-scoper"},
            ],
        )

        exit_code = _bi.build(_args(paths))

        assert exit_code == 0
        conn = sqlite3.connect(str(paths["db_path"]))
        assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 2
        conn.close()


# ---------------------------------------------------------------------------
# Group 5 — row-count stability across reruns (AC5)
# ---------------------------------------------------------------------------

class TestRerunStability:

    def test_build_twice_produces_same_row_counts(self, tmp_path):
        paths = _make_corpus(
            tmp_path,
            runs=[dict(_BASE_RUN)],
            events=[{"run_id": "TCK-FAKE", "seq": 1, "phase": "Implement", "agent": "implementer"}],
            tools=[{"run_id": "TCK-FAKE", "seq": 1, "tool": "Read"}] + _OFFSCHEMA_TOOLS_RECORDS,
        )

        def _counts():
            conn = sqlite3.connect(str(paths["db_path"]))
            result = {
                name: conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                for name in ("runs", "events", "tools")
            }
            conn.close()
            return result

        _bi.build(_args(paths))
        first = _counts()
        _bi.build(_args(paths))
        second = _counts()

        assert first == second


# ---------------------------------------------------------------------------
# Group 6 — Makefile target + .gitignore (AC6)
# ---------------------------------------------------------------------------

class TestMakeTarget:

    def test_makefile_has_agent_monitoring_index_target(self):
        makefile = _REPO_ROOT / "Makefile"
        content = makefile.read_text(encoding="utf-8")
        assert "agent-monitoring-index:" in content

    def test_makefile_agent_monitoring_index_calls_build_index(self):
        makefile = _REPO_ROOT / "Makefile"
        content = makefile.read_text(encoding="utf-8")
        assert "tools/agent-monitoring/build_index.py" in content

    def test_agent_monitoring_index_not_in_test_ci_all_targets(self):
        makefile = _REPO_ROOT / "Makefile"
        content = makefile.read_text(encoding="utf-8")
        for target_line in content.split("\n"):
            if target_line.startswith(("test:", "test-quick:", "test-cov:", "ci:", "all:")):
                assert "agent-monitoring-index" not in target_line, (
                    f"'agent-monitoring-index' must not be a dependency of CI targets, "
                    f"found in: {target_line!r}"
                )

    def test_makefile_dry_run_agent_monitoring_index(self):
        result = subprocess.run(
            ["make", "--dry-run", "agent-monitoring-index"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
        combined = result.stdout + result.stderr
        assert "build_index.py" in combined


class TestGitignore:

    def test_db_path_in_gitignore(self):
        gitignore = _REPO_ROOT / ".gitignore"
        content = gitignore.read_text(encoding="utf-8")
        assert "agent-monitoring-index/" in content

    def test_git_check_ignore(self, tmp_path):
        result = subprocess.run(
            ["git", "check-ignore", "-v", "agent-monitoring-index/monitoring.db"],
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 0, "agent-monitoring-index/monitoring.db is not git-ignored"


# ---------------------------------------------------------------------------
# Group 7 — architecture guards (anti-drift)
# ---------------------------------------------------------------------------

class TestArchitectureGuards:

    def test_no_incremental_build_flag_exists(self):
        source = _MODULE_PATH.read_text(encoding="utf-8")
        assert "--incremental" not in source

    def test_build_index_never_touches_write_path_modules(self):
        source = _MODULE_PATH.read_text(encoding="utf-8")
        forbidden = ("pre_tool_hook", "post_tool_hook", "record_run", "record_events", "writer")
        for name in forbidden:
            assert name not in source, f"build_index.py must not reference {name!r}"

    def test_build_index_imports_vocabulary_not_reencoded(self):
        assert _bi.infer_workflow is not None
        import vocabulary

        assert _bi.infer_workflow is vocabulary.infer_workflow
        assert _bi.CANONICAL_TIERS is vocabulary.CANONICAL_TIERS
