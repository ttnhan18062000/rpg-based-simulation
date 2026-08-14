"""Tests for tools/agent-monitoring/writer.py — the shared Linux-only
append-only writer (TCK-20260721-MONITORING-WRITER-UNIFICATION).

Promotes tests/tools/test_monitoring_writer_lockfile_candidate.py's evidence
(kept in place, unmodified) to production coverage against the real module,
plus the non-raising/diagnostic-sidecar contract and a stale-lock recovery
test that proves the actual recovery mechanism, not just eventual success.

Test-side safety guard (mirrors the candidate's own `_assert_not_real_corpus`,
enforced here rather than in writer.py, since writer.py's whole purpose is to
write under the real agent-monitoring/ directory in production): every test
below targets a path under pytest's own `tmp_path` fixture, never a path
resolving under this repo's real `agent-monitoring/` directory.
"""
import builtins
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import writer  # noqa: E402


def test_no_test_target_path_resolves_under_real_agent_monitoring_dir():
    """Guard: no test in this file may hardcode a path under the real repo's
    agent-monitoring/ directory — every target below must be tmp_path-rooted.

    Scans every other test function's source (excluding this guard's own body,
    which necessarily names the forbidden patterns as string literals) for a
    real-corpus-shaped path construction.
    """
    import inspect

    module = sys.modules[__name__]
    this_function_name = "test_no_test_target_path_resolves_under_real_agent_monitoring_dir"
    real_dir = str((_REPO_ROOT / "agent-monitoring").resolve())
    forbidden = [real_dir, "Path(" + '"agent-monitoring"' + ")", "Path(" + "'agent-monitoring'" + ")"]

    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if name == this_function_name or obj.__module__ != __name__:
            continue
        source = inspect.getsource(obj)
        for pattern in forbidden:
            assert pattern not in source, f"{name} references a real-corpus-shaped path: {pattern!r}"


# ---------------------------------------------------------------------------
# Step 2 — core lock-file mechanics, single writer + malformed-line tolerance
# ---------------------------------------------------------------------------


def test_single_writer_produces_one_well_formed_line(tmp_path):
    target_path = tmp_path / "tools.jsonl"
    result = writer.write_line(target_path, json.dumps({"marker": "only-line"}))
    assert result is True

    lines = target_path.read_text().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"marker": "only-line"}
    assert not writer._lock_path_for(target_path).exists()


def test_malformed_partial_line_is_rejected_by_downstream_reader(tmp_path):
    target_path = tmp_path / "tools.jsonl"
    target_path.write_text('{"session_id": "abc", "run_i\n')

    for i in range(5):
        assert writer.write_line(target_path, json.dumps({"i": i, "marker": f"valid-{i}"})) is True

    valid_records = []
    rejected_count = 0
    for line in target_path.read_text().splitlines():
        if not line:
            continue
        try:
            valid_records.append(json.loads(line))
        except json.JSONDecodeError:
            rejected_count += 1

    assert rejected_count == 1
    assert len(valid_records) == 5
    assert {r["marker"] for r in valid_records} == {f"valid-{i}" for i in range(5)}


# ---------------------------------------------------------------------------
# Step 3 — diagnostic sidecar + non-raising contract, structural classification
# ---------------------------------------------------------------------------


def test_forced_lock_acquire_failure_returns_false_and_writes_diagnostic(tmp_path, monkeypatch):
    target_path = tmp_path / "corpus.jsonl"
    real_open = os.open

    def _fake_os_open(path, flags, *a, **kw):
        if str(path).endswith(".lock"):
            raise OSError("forced lock failure for test")
        return real_open(path, flags, *a, **kw)

    monkeypatch.setattr(writer.os, "open", _fake_os_open)

    result = writer.write_line(target_path, json.dumps({"marker": "x"}))
    assert result is False

    diagnostic_path = writer._diagnostic_path_for(target_path)
    lines = diagnostic_path.read_text().splitlines()
    assert len(lines) == 1
    diag = json.loads(lines[0])
    assert diag["stage"] == "lock_acquire"
    assert diag["target"] == "corpus.jsonl"
    # Structural classification: the injected OSError is not a TimeoutError
    # (it never reaches _acquire_lock's own retry-exhaustion raise), proving
    # "lock_acquire" is assigned by *which region* caught it, not by type.
    assert diag["error_type"] == "OSError"


def test_forced_write_failure_returns_false_and_writes_diagnostic(tmp_path, monkeypatch):
    target_path = tmp_path / "corpus.jsonl"
    real_open = builtins.open

    def _fake_open(path, mode="r", *a, **kw):
        if str(path) == str(target_path) and "a" in mode:
            raise OSError("forced write failure for test")
        return real_open(path, mode, *a, **kw)

    monkeypatch.setattr(builtins, "open", _fake_open)

    result = writer.write_line(target_path, json.dumps({"marker": "x"}))
    assert result is False
    # Lock released in `finally` regardless of the write failure.
    assert not writer._lock_path_for(target_path).exists()

    diagnostic_path = writer._diagnostic_path_for(target_path)
    lines = diagnostic_path.read_text().splitlines()
    assert len(lines) == 1
    diag = json.loads(lines[0])
    assert diag["stage"] == "write"
    assert diag["error_type"] == "OSError"


def test_diagnostic_write_failure_itself_never_raises(tmp_path, monkeypatch):
    target_path = tmp_path / "corpus.jsonl"
    diagnostic_path = writer._diagnostic_path_for(target_path)
    real_os_open = os.open

    def _fake_os_open(path, flags, *a, **kw):
        if str(path) == str(diagnostic_path):
            raise OSError("forced diagnostic failure for test")
        return real_os_open(path, flags, *a, **kw)

    monkeypatch.setattr(writer.os, "open", _fake_os_open)

    writer._write_diagnostic(target_path, "write", RuntimeError("boom"))  # must not raise
    assert not diagnostic_path.exists()


def test_concurrent_diagnostic_writes_do_not_interleave(tmp_path):
    target_path = tmp_path / "corpus.jsonl"
    n_writers = 10
    iterations = 20

    def _worker(worker_idx):
        for i in range(iterations):
            writer._write_diagnostic(target_path, "write", RuntimeError(f"err-{worker_idx}-{i}"))

    with ThreadPoolExecutor(max_workers=n_writers) as pool:
        list(pool.map(_worker, range(n_writers)))

    diagnostic_path = writer._diagnostic_path_for(target_path)
    lines = diagnostic_path.read_text().splitlines()
    assert len(lines) == n_writers * iterations

    seen = set()
    for line in lines:
        record = json.loads(line)  # must not raise — proves no truncated/merged lines
        seen.add(record["error_message"])

    expected = {f"err-{w}-{i}" for w in range(n_writers) for i in range(iterations)}
    assert seen == expected


# ---------------------------------------------------------------------------
# Step 7 — mixed-population concurrency stress test + stale-lock recovery
# ---------------------------------------------------------------------------


def test_concurrent_writers_produce_no_interleaved_or_truncated_lines(tmp_path):
    target_path = tmp_path / "mixed.jsonl"
    n_single_writers = 5
    n_batch_writers = 5
    iterations_per_single_writer = 20
    batches_per_batch_writer = 10
    batch_size = 3

    def _single_worker(worker_idx):
        for i in range(iterations_per_single_writer):
            line = json.dumps({"kind": "single", "worker": worker_idx, "i": i, "marker": f"single-{worker_idx}-{i}"})
            assert writer.write_line(target_path, line) is True

    def _batch_worker(worker_idx):
        for b in range(batches_per_batch_writer):
            lines = [
                json.dumps(
                    {"kind": "batch", "worker": worker_idx, "b": b, "j": j, "marker": f"batch-{worker_idx}-{b}-{j}"}
                )
                for j in range(batch_size)
            ]
            assert writer.write_lines(target_path, lines) is True

    with ThreadPoolExecutor(max_workers=n_single_writers + n_batch_writers) as pool:
        futures = [pool.submit(_single_worker, idx) for idx in range(n_single_writers)]
        futures += [pool.submit(_batch_worker, idx) for idx in range(n_batch_writers)]
        for f in futures:
            f.result()

    lines = target_path.read_text().splitlines()
    expected_single = n_single_writers * iterations_per_single_writer
    expected_batch = n_batch_writers * batches_per_batch_writer * batch_size
    assert len(lines) == expected_single + expected_batch

    seen_markers = set()
    for line in lines:
        record = json.loads(line)  # must not raise — proves no interleaving/truncation
        seen_markers.add(record["marker"])

    expected_markers = {
        f"single-{w}-{i}" for w in range(n_single_writers) for i in range(iterations_per_single_writer)
    }
    expected_markers |= {
        f"batch-{w}-{b}-{j}"
        for w in range(n_batch_writers)
        for b in range(batches_per_batch_writer)
        for j in range(batch_size)
    }
    assert seen_markers == expected_markers
    assert not writer._lock_path_for(target_path).exists()


def test_stale_lock_is_removed_and_superseded(tmp_path):
    target_path = tmp_path / "stale.jsonl"
    lock_path = writer._lock_path_for(target_path)

    # A pre-existing valid line, written before the lock was abandoned — recovery
    # must not corrupt it.
    target_path.write_text(json.dumps({"marker": "pre-existing"}) + "\n")

    fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(fd)
    backdated = time.time() - writer.STALE_AFTER_S - 1
    os.utime(lock_path, (backdated, backdated))
    assert lock_path.exists()

    # Exercise _acquire_lock directly: proves the abandoned lock file is detected
    # and removed, and a fresh lock is acquired — not just "eventually succeeds
    # by unrelated retry luck".
    writer._acquire_lock(lock_path)
    assert lock_path.exists()  # a fresh lock is now held
    writer._release_lock(lock_path)
    assert not lock_path.exists()

    # End-to-end: write_line still succeeds normally afterward.
    result = writer.write_line(target_path, json.dumps({"marker": "post-recovery"}))
    assert result is True
    assert not lock_path.exists()

    lines = target_path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"marker": "pre-existing"}
    assert json.loads(lines[1]) == {"marker": "post-recovery"}
