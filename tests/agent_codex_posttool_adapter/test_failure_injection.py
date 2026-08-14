"""Failure-injection coverage for AC #3: writer failure/exception, parse failure, and the
narrowed bounded-I/O architecture guard (Step 6)."""
from __future__ import annotations

import ast
import json
from pathlib import Path

from tools.agent_codex_posttool_adapter import adapter, writer_bridge

_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "fixtures"
    / "codex_hook_payloads"
    / "post_tool_use_stdin_capture.json"
)
_PACKAGE_DIR = (
    Path(__file__).resolve().parent.parent.parent / "tools" / "agent_codex_posttool_adapter"
)

_TICKET_ID = "TCK-20260730-CODEX-POSTTOOL-ADAPTER"
_EXECUTION_ID = f"codex-{_TICKET_ID}-1700000000000-deadbeef"
_LIVE_ENV = {"CODEX_POSTTOOL_ADAPTER_LIVE_APPEND": "1"}


def _real_raw_payload() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))["raw_stdin_payload"]


def _run(tmp_path, raw=None):
    return adapter.process_post_tool_use(
        raw if raw is not None else _real_raw_payload(),
        target_path=tmp_path / "tools.jsonl",
        execution_id=_EXECUTION_ID,
        ticket_id=_TICKET_ID,
        env=_LIVE_ENV,
    )


def test_writer_returning_false_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.setattr(writer_bridge, "write_line", lambda target_path, line: False)
    assert _run(tmp_path) is False


def test_writer_raising_unexpected_exception_does_not_propagate(tmp_path, monkeypatch):
    def _boom(target_path, line):
        raise RuntimeError("simulated writer defect despite write_line's own no-raise contract")

    monkeypatch.setattr(writer_bridge, "write_line", _boom)
    assert _run(tmp_path) is False


def test_parse_failure_does_not_block_tool_workflow(tmp_path):
    assert _run(tmp_path, raw={"not": "a valid payload shape"}) is False
    assert _run(tmp_path, raw="not even a dict") is False


def test_bounded_timeout_behavior():
    """Narrowed per plan.md's Resolution: identity.py never touches the filesystem (format-only
    ticket_id validation), so there is no unbounded I/O in adapter.py/identity.py to bound in the
    first place. This is an architecture guard proving that absence, not a timeout-injection test
    against real I/O."""
    forbidden_io_call_names = {"open", "read_text", "read_bytes", "write_text", "write_bytes"}
    for filename in ("adapter.py", "identity.py"):
        tree = ast.parse((_PACKAGE_DIR / filename).read_text(encoding="utf-8"), filename=filename)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
                assert name not in forbidden_io_call_names, (
                    f"{filename}: unexpected filesystem I/O call {name!r}"
                )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(alias.name == "pathlib" for alias in node.names) or filename != "identity.py"
            if isinstance(node, ast.ImportFrom):
                assert node.module != "pathlib" or filename != "identity.py"


def test_diagnostic_failure_does_not_block(tmp_path, monkeypatch):
    """writer.py's own _write_diagnostic sidecar already swallows every exception internally —
    this adapter does not re-implement a second diagnostic path. This test proves the adapter's
    own boundary stays fail-open even under a simulated total writer failure (write and its
    internal diagnostic write both broken), mirroring _write_diagnostic's own swallow-everything
    precedent one level up."""

    def _totally_broken(target_path, line):
        raise OSError("disk full, and the diagnostic sidecar write also failed")

    monkeypatch.setattr(writer_bridge, "write_line", _totally_broken)
    assert _run(tmp_path) is False
