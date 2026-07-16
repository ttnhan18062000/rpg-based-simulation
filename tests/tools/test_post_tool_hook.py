"""Tests for TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK.

`post_tool_hook.py` appends one JSON record per tool call to
`agent-monitoring/tools.jsonl`. Before this ticket, the append (`with open(tools_file, "a") as
f: f.write(...)`) had no synchronization across processes, and a real two-session race produced
one corrupted, unparseable line in production (see the ticket's Request Summary). The fix wraps
the write in `fcntl.flock(f, fcntl.LOCK_EX)` / `fcntl.flock(f, fcntl.LOCK_UN)`.

The hook is a top-level script (not importable as a module of functions — reading `sys.stdin`
executes immediately on import), so every test here drives it the way Claude Code itself does:
as a subprocess fed a JSON payload on stdin, with `cwd` pointed at a temp dir so
`agent-monitoring/tools.jsonl` is created fresh per test.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_HOOK_PATH = _REPO_ROOT / "tools" / "agent-monitoring" / "post_tool_hook.py"

_RECORD_FIELDS = {
    "session_id", "run_id", "seq", "ts", "tool",
    "input_summary", "status", "duration_ms",
}


def _payload(session_id="sess-1", command="pytest tests/"):
    return {
        "session_id": session_id,
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_response": {},
    }


def _run_hook(cwd, payload):
    return subprocess.run(
        [sys.executable, str(_HOOK_PATH)],
        input=json.dumps(payload),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
    )


def _tools_lines(cwd):
    tools_file = cwd / "agent-monitoring" / "tools.jsonl"
    return tools_file.read_text().splitlines()


def test_single_writer_produces_one_well_formed_line(tmp_path):
    result = _run_hook(tmp_path, _payload())
    assert result.returncode == 0

    lines = _tools_lines(tmp_path)
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert set(record.keys()) == _RECORD_FIELDS
    assert record["session_id"] == "sess-1"
    assert record["tool"] == "Bash"
    assert record["input_summary"] == "pytest tests/"
    assert record["status"] == "ok"
    assert record["run_id"] is None
    assert record["seq"] is None
    assert record["duration_ms"] is None


def test_concurrent_writers_produce_no_interleaved_or_truncated_lines(tmp_path):
    n_writers = 10
    iterations_per_writer = 15

    def _worker(worker_idx):
        for i in range(iterations_per_writer):
            result = _run_hook(
                tmp_path,
                _payload(session_id=f"sess-{worker_idx}", command=f"cmd-{worker_idx}-{i}"),
            )
            assert result.returncode == 0

    with ThreadPoolExecutor(max_workers=n_writers) as pool:
        list(pool.map(_worker, range(n_writers)))

    lines = _tools_lines(tmp_path)
    assert len(lines) == n_writers * iterations_per_writer

    seen_commands = set()
    for line in lines:
        record = json.loads(line)
        assert set(record.keys()) == _RECORD_FIELDS
        seen_commands.add(record["input_summary"])

    expected_commands = {
        f"cmd-{worker_idx}-{i}"
        for worker_idx in range(n_writers)
        for i in range(iterations_per_writer)
    }
    assert seen_commands == expected_commands


def test_locking_failure_does_not_propagate(tmp_path):
    hook_source = _HOOK_PATH.read_text()
    shim_source = (
        "import fcntl\n"
        "def _raise_flock(*args, **kwargs):\n"
        "    raise OSError('forced lock failure for test')\n"
        "fcntl.flock = _raise_flock\n"
        "\n"
        + hook_source
    )
    shim = tmp_path / "post_tool_hook_locking_failure_shim.py"
    shim.write_text(shim_source)

    result = subprocess.run(
        [sys.executable, str(shim)],
        input=json.dumps(_payload()),
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert result.stderr == ""
