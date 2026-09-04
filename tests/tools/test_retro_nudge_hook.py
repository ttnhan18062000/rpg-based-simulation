"""Tests for tools/agent-monitoring/retro_nudge_hook.py
(TCK-20260903-MONITORING-DATA-CONSUMERS-CORE).

Before this ticket, RUNS_FILE pointed at the dead `agent-monitoring/runs.jsonl` path (retired by
TCK-20260903-MONITORING-DATA-MIGRATION), so `_count_done_since()` always returned 0 and this hook
could never fire — a permanent silent no-op. This file is genuinely new coverage (no test file for
this script existed before this ticket, confirmed by grep).

Like `post_tool_hook.py`, the module's top level (below the function definitions) reads
`sys.stdin` and executes unconditionally on import — not gated behind `if __name__ ==
"__main__":`. `test_retro_nudge_hook_counts_done_runs_across_multiple_week_folders` loads the
module via `importlib` with `sys.stdin` patched to a valid payload so `_count_done_since()` itself
remains directly callable afterward. `test_retro_nudge_hook_fail_silent_on_malformed_data_dir`
drives the hook as a subprocess (mirroring test_post_tool_hook.py's `_run_hook()` pattern) since
it specifically needs to prove the whole script body never raises out to the OS.
"""
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_HOOK_PATH = _MONITORING_TOOLS_DIR / "retro_nudge_hook.py"


def _write_jsonl(path: Path, records: list) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def _import_hook_module(monkeypatch, cwd: Path, payload: dict):
    monkeypatch.chdir(cwd)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    spec = importlib.util.spec_from_file_location("retro_nudge_hook_under_test", _HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_hook(cwd, payload):
    return subprocess.run(
        [sys.executable, str(_HOOK_PATH)],
        input=json.dumps(payload),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_retro_nudge_hook_counts_done_runs_across_multiple_week_folders(tmp_path, monkeypatch):
    week1 = tmp_path / "agent-monitoring" / "data" / "2026-W01"
    week1.mkdir(parents=True)
    _write_jsonl(week1 / "runs.jsonl", [
        {"workflow": "implement-ticket", "final_status": "DONE", "start_ts": "2026-01-05T00:00:00Z"},
        {"workflow": "implement-ticket", "final_status": "DONE", "start_ts": "2026-01-06T00:00:00Z"},
    ])

    week2 = tmp_path / "agent-monitoring" / "data" / "2026-W02"
    week2.mkdir(parents=True)
    _write_jsonl(week2 / "runs.jsonl", [
        {"workflow": "implement-ticket", "final_status": "DONE", "start_ts": "2026-01-12T00:00:00Z"},
        {"workflow": "implement-ticket", "final_status": "DONE", "start_ts": "2026-01-13T00:00:00Z"},
        {"workflow": "implement-ticket", "final_status": "DONE", "start_ts": "2026-01-14T00:00:00Z"},
    ])

    module = _import_hook_module(monkeypatch, tmp_path, {"session_id": "sess-test"})

    # No agent-monitoring/retro/RETRO-*.md exists in this fixture -> _last_dated_retro_mtime()
    # returns 0.0 (threshold already crossed), so every seeded record's start_ts (all in 2026,
    # well after epoch) counts.
    assert module._count_done_since(0.0) == 5, (
        "must count DONE runs from BOTH week folders, not just one — a same-week-only fix "
        "could pass a weaker version of this test while leaving the cross-week case broken"
    )


def test_retro_nudge_hook_fail_silent_on_malformed_data_dir(tmp_path):
    # Case 1: agent-monitoring/data/ entirely absent.
    result_missing = _run_hook(tmp_path, {"session_id": "sess-missing-dir"})
    assert result_missing.returncode == 0
    assert "Traceback" not in result_missing.stderr

    # Case 2: a malformed JSON line inside a real week folder's runs.jsonl.
    week1 = tmp_path / "agent-monitoring" / "data" / "2026-W01"
    week1.mkdir(parents=True)
    (week1 / "runs.jsonl").write_text("not valid json\n", encoding="utf-8")

    result_malformed = _run_hook(tmp_path, {"session_id": "sess-malformed"})
    assert result_malformed.returncode == 0
    assert "Traceback" not in result_malformed.stderr
