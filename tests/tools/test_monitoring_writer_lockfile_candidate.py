"""Stress harness for TCK-20260721-MONITORING-WRITER-DECISION.

Evaluates candidate writer design 1 named in the ticket's AC3
("lock-file protocol w/ bounded retry + stale-lock recovery") as a
concurrency-safe, cross-platform-portable alternative to
`post_tool_hook.py`'s current `fcntl.flock` mechanism (POSIX-only, no
Windows equivalent).

This module is evidence-gathering only. It is deliberately self-contained
and test-local: `_acquire_lock`/`_release_lock`/`_write_record_lockfile`
below are NOT imported from or added to `tools/agent-monitoring/`, and
this file never opens any path under the real `agent-monitoring/`
directory — every write goes through a `tmp_path` fixture. Wiring this
design into the production hook is explicitly out of scope for this
ticket (follow-on, epic-gated implementation work); see
`docs/ai/monitoring_writer_decision.md` for the recorded decision and
the results this file produces.
"""
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent


def _assert_not_real_corpus(path):
    resolved = str(Path(path).resolve())
    repo_root = str(_REPO_ROOT.resolve())
    if resolved.startswith(repo_root):
        relative = Path(resolved).relative_to(repo_root)
        assert "agent-monitoring" not in relative.parts, (
            f"refusing to write to real corpus-shaped path: {resolved}"
        )


def _acquire_lock(lock_path, stale_after_s=5.0, max_retries=200, retry_sleep_s=0.005):
    _assert_not_real_corpus(lock_path)
    for _ in range(max_retries):
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            try:
                age_s = time.time() - os.path.getmtime(lock_path)
            except FileNotFoundError:
                continue
            if age_s > stale_after_s:
                try:
                    os.remove(lock_path)
                except FileNotFoundError:
                    pass
                continue
            time.sleep(retry_sleep_s)
    raise TimeoutError(f"could not acquire lock at {lock_path} after {max_retries} retries")


def _release_lock(lock_path):
    _assert_not_real_corpus(lock_path)
    os.remove(lock_path)


def _write_record_lockfile(target_path, record, lock_path):
    _assert_not_real_corpus(target_path)
    _assert_not_real_corpus(lock_path)
    _acquire_lock(lock_path)
    try:
        with open(target_path, "a") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
    finally:
        _release_lock(lock_path)


def test_lockfile_guard_rejects_real_agent_monitoring_path():
    real_corpus_path = _REPO_ROOT / "agent-monitoring" / "tools.jsonl"
    try:
        _assert_not_real_corpus(real_corpus_path)
    except AssertionError:
        pass
    else:
        raise AssertionError("_assert_not_real_corpus did not reject a real corpus path")


def test_concurrent_writers_lockfile_produce_no_interleaved_or_truncated_lines(tmp_path):
    n_writers = 10
    iterations_per_writer = 20
    target_path = tmp_path / "tools.jsonl"
    lock_path = tmp_path / "tools.jsonl.lock"

    def _worker(worker_idx):
        for i in range(iterations_per_writer):
            _write_record_lockfile(
                target_path,
                {"worker": worker_idx, "i": i, "marker": f"rec-{worker_idx}-{i}"},
                lock_path,
            )

    with ThreadPoolExecutor(max_workers=n_writers) as pool:
        list(pool.map(_worker, range(n_writers)))

    lines = target_path.read_text().splitlines()
    assert len(lines) == n_writers * iterations_per_writer

    seen_markers = set()
    for line in lines:
        record = json.loads(line)
        seen_markers.add(record["marker"])

    expected_markers = {
        f"rec-{worker_idx}-{i}"
        for worker_idx in range(n_writers)
        for i in range(iterations_per_writer)
    }
    assert seen_markers == expected_markers
    assert not lock_path.exists()


def test_malformed_partial_line_is_rejected_by_downstream_reader(tmp_path):
    target_path = tmp_path / "tools.jsonl"
    lock_path = tmp_path / "tools.jsonl.lock"
    _assert_not_real_corpus(target_path)

    with open(target_path, "a") as f:
        f.write('{"session_id": "abc", "run_i\n')

    for i in range(5):
        _write_record_lockfile(target_path, {"i": i, "marker": f"valid-{i}"}, lock_path)

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
