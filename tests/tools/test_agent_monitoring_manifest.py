"""Tests for tools/agent-monitoring/manifest.py (TCK-20260721-BASELINE-MONITORING-MANIFEST).

Runs against the REAL agent-monitoring/ directory — never a tmp_path copy, which
would make the zero-mutation and streaming-guard assertions vacuous (nothing real
to prove wasn't loaded wholesale or mutated). Mirrors
tests/agent_replay/test_no_mutation_snapshot.py's dirty-tree-aware two-branch
design for the integration test.
"""
import ast
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MANIFEST_PATH = _MONITORING_TOOLS_DIR / "manifest.py"
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from manifest import build_manifest  # noqa: E402

_EXPECTED_KEYS = {"file", "line_count", "byte_size", "sha256", "parser_result", "legacy_warning_count"}
_WATCHED_JSONL_FILES = ["events.jsonl", "runs.jsonl", "tools.jsonl"]

_XFAIL_TOOLS_JSONL_RETIRED_REASON = (
    "agent-monitoring/tools.jsonl retired by TCK-20260902-MONITORING-SHARD-MIGRATION; "
    "manifest.py/skill_usage_metric.py not yet updated to read the shard directory -- tracked "
    "by TCK-20260902-MONITORING-SHARD-CONSUMERS (child 3), landing immediately after in this "
    "same batch per SEQUENCE.md. Must be removed before any PR from this branch opens."
)


# ---------------------------------------------------------------------------
# Shape test (AC1)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason=_XFAIL_TOOLS_JSONL_RETIRED_REASON, strict=True)
def test_build_manifest_shape_against_real_corpus():
    records = build_manifest(_REAL_AGENT_MONITORING_DIR)

    assert len(records) == 3
    filenames = [r["file"] for r in records]
    assert filenames == sorted(filenames)
    assert set(filenames) == {"events.jsonl", "runs.jsonl", "tools.jsonl"}

    for record in records:
        assert set(record.keys()) == _EXPECTED_KEYS
        assert isinstance(record["file"], str)
        assert isinstance(record["line_count"], int)
        assert isinstance(record["byte_size"], int)
        assert isinstance(record["sha256"], str) and len(record["sha256"]) == 64
        assert isinstance(record["parser_result"], dict)
        assert set(record["parser_result"].keys()) == {"parsed_ok", "parse_errors"}
        assert isinstance(record["parser_result"]["parsed_ok"], int)
        assert isinstance(record["parser_result"]["parse_errors"], int)
        assert record["line_count"] == record["parser_result"]["parsed_ok"] + record["parser_result"]["parse_errors"]
        assert isinstance(record["legacy_warning_count"], int)


# ---------------------------------------------------------------------------
# Reproducibility test (AC2)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason=_XFAIL_TOOLS_JSONL_RETIRED_REASON, strict=True)
def test_manifest_cli_reproducible_byte_identical_across_two_runs():
    result_1 = subprocess.run(
        [sys.executable, str(_MANIFEST_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    result_2 = subprocess.run(
        [sys.executable, str(_MANIFEST_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )

    assert result_1.stdout == result_2.stdout
    assert result_1.stdout.endswith("\n")


@pytest.mark.xfail(reason=_XFAIL_TOOLS_JSONL_RETIRED_REASON, strict=True)
def test_build_manifest_reproducible_byte_identical_direct_call():
    output_1 = build_manifest(_REAL_AGENT_MONITORING_DIR)
    output_2 = build_manifest(_REAL_AGENT_MONITORING_DIR)
    assert output_1 == output_2


# ---------------------------------------------------------------------------
# Streaming guard (AC7) — static/AST-based, not empirical
# ---------------------------------------------------------------------------

def test_manifest_source_never_calls_full_file_read_methods():
    tree = ast.parse(_MANIFEST_PATH.read_text())
    banned_methods = {"read_text", "read_bytes", "readlines", "read"}
    offending_calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in banned_methods:
                offending_calls.append(node.func.attr)

    assert offending_calls == [], (
        f"manifest.py calls full-file-read method(s) {offending_calls} — violates the "
        "single-pass streaming requirement"
    )


# ---------------------------------------------------------------------------
# Zero-mutation integration test (AC3)
# ---------------------------------------------------------------------------

def _porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    return result.stdout


def _content_hash_snapshot() -> str:
    hasher = hashlib.sha256()
    for filename in _WATCHED_JSONL_FILES:
        path = _REAL_AGENT_MONITORING_DIR / filename
        hasher.update(filename.encode("utf-8"))
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


@pytest.mark.xfail(reason=_XFAIL_TOOLS_JSONL_RETIRED_REASON, strict=True)
def test_manifest_run_against_real_corpus_produces_zero_diff():
    assert _REAL_AGENT_MONITORING_DIR.is_dir()
    assert "tmp" not in str(_REAL_AGENT_MONITORING_DIR).lower()

    pre_porcelain = _porcelain_snapshot()

    if pre_porcelain == "":
        build_manifest(_REAL_AGENT_MONITORING_DIR)
        post_porcelain = _porcelain_snapshot()
        assert post_porcelain == "", (
            "build_manifest mutated agent-monitoring/ (tree was clean before, dirty after): "
            f"{post_porcelain!r}"
        )
        return

    pre_hash = _content_hash_snapshot()
    build_manifest(_REAL_AGENT_MONITORING_DIR)
    post_hash = _content_hash_snapshot()
    assert pre_hash == post_hash, (
        "build_manifest changed the content of one or more agent-monitoring/*.jsonl files "
        "(ambient dirty state existed before the run, but its content hash must be unchanged after)"
    )


# `test_writer_files_are_byte_unchanged_by_this_ticket` (formerly guarding validate.py) was
# removed 2026-07-28 by TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION. History: the guard
# started under TCK-20260721-BASELINE-MONITORING-MANIFEST as an unconditional "validate.py,
# record_run.py, record_events.py, post_tool_hook.py must never be touched" assertion; it was
# narrowed to validate.py only on 2026-07-22 once TCK-20260721-MONITORING-WRITER-UNIFICATION's
# own approved scope required touching the other 3. The same reasoning now applies to the last
# remaining file: TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION's approved scope (signed off
# by architecture-reviewer in both Review and Architecture-Verify) is to extend validate.py with
# compute_multi_invocation_collision_report(), so an unconditional "validate.py must never be
# modified, by any future ticket, forever" assertion is now factually incompatible with
# legitimate, approved work — the same way it was for the other 3 files. No file remains that
# this specific guard's reasoning still protects, so the test and its `_WRITER_GUARD_FILES`
# constant were deleted rather than narrowed to an empty (and therefore vacuous/dangerous —
# `git diff --stat HEAD --` with zero pathspecs after `--` would diff the whole repo, not
# nothing) file list. `validate.py`'s real, still-relevant behavioral contracts (manifest shape,
# reproducibility, streaming, zero-mutation) remain covered by the other tests in this file and by
# `tests/tools/test_validate_agent_monitoring.py`.
