"""The ConfigChange hook script (TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION): notifies by terminalSequence, logs, never blocks, fails open."""
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tools.sessions import config_change_warning as ccw

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "tools" / "sessions" / "config_change_warning.py"
_EVENT = {"hook_event_name": "ConfigChange", "source": "project_settings", "file_path": ".claude/settings.json", "session_id": "s", "cwd": "/x"}
_ALLOWED = re.compile(r"(\x1b\](?:9|777);[^\x00-\x1f]*\x07|\x07)+")


def _run(stdin_text, log_path):
    out = io.StringIO()
    rc = ccw.main(stdin=io.StringIO(stdin_text), stdout=out, log_path=log_path)
    return rc, out.getvalue()


def test_the_output_is_a_terminal_sequence_of_allowlisted_parts_only_and_no_system_message(tmp_path):
    rc, out = _run(json.dumps(_EVENT), tmp_path / "log")
    assert rc == 0 and out.count("\n") == 1
    body = json.loads(out)
    assert set(body) == {"terminalSequence"}
    seq = body["terminalSequence"]
    assert _ALLOWED.fullmatch(seq)
    assert seq.startswith("\x1b]9;") and "\x1b]777;notify;" in seq and seq.endswith("\x07")
    assert "project_settings" in seq and ".claude/settings.json" in seq


def test_control_characters_in_the_event_never_reach_the_sequence(tmp_path):
    evil = {"source": "skills\x1b]52;c;abc\x07;x", "file_path": "a\x1b[31m\nb\x00;c" + "z" * 500}
    seq = json.loads(_run(json.dumps(evil), tmp_path / "log")[1])["terminalSequence"]
    assert _ALLOWED.fullmatch(seq)
    assert "\x1b[" not in seq and "52;c" not in seq and "\x00" not in seq and "\n" not in seq
    assert len(seq) < 500
    assert seq.count("\x1b") == 2 and seq.count(";") == 4  # OSC 9 has one separator, OSC 777 has three


def test_one_log_line_holds_only_time_event_source_path_and_sorted_key_names(tmp_path):
    log = tmp_path / "sub" / "c.log"
    _run(json.dumps({**_EVENT, "secret_value": "hunter2"}), log)
    _run(json.dumps(_EVENT), log)
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert set(row) == {"time", "hook_event_name", "source", "file_path", "keys"}
    assert row["source"] == "project_settings" and row["file_path"] == ".claude/settings.json"
    assert row["keys"] == sorted(row["keys"]) and "secret_value" in row["keys"]
    assert "hunter2" not in lines[0]
    assert datetime.strptime(row["time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def test_a_log_failure_still_notifies_and_exits_zero(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    rc, out = _run(json.dumps(_EVENT), blocker / "c.log")
    assert rc == 0 and "terminalSequence" in json.loads(out)


@pytest.mark.parametrize("text", ["", "not json", "[]", "null", "3"])
def test_malformed_input_exits_zero_silently_and_logs_nothing(text, tmp_path):
    log = tmp_path / "c.log"
    rc, out = _run(text, log)
    assert rc == 0 and out == "" and not log.exists()


def test_the_script_runs_as_a_hook_and_exits_zero(tmp_path):
    env = {**os.environ, "CONFIG_CHANGE_WARNING_LOG": str(tmp_path / "c.log")}
    done = subprocess.run([sys.executable, str(_SCRIPT)], input=json.dumps(_EVENT), capture_output=True, text=True, env=env)
    assert done.returncode == 0 and "terminalSequence" in json.loads(done.stdout)
    assert (tmp_path / "c.log").exists()


_REPO = Path(__file__).resolve().parents[2]


def _wired_command():
    groups = json.loads((_REPO / ".claude" / "settings.json").read_text(encoding="utf-8"))["hooks"]["ConfigChange"]
    assert len(groups) == 1 and len(groups[0]["hooks"]) == 1
    hook = groups[0]["hooks"][0]
    assert hook["type"] == "command"
    return hook["command"]


def test_settings_wires_exactly_one_config_change_hook_that_fails_open_and_never_swallows_or_blocks():
    command = _wired_command()
    assert "tools/sessions/config_change_warning.py" in command
    assert "|| exit 0" in command and not command.rstrip().endswith("|| true")
    assert "exit 2" not in command


def test_the_wired_command_runs_from_the_repo_and_prints_the_warning(tmp_path):
    log = tmp_path / "c.log"
    env = {**os.environ, "CONFIG_CHANGE_WARNING_LOG": str(log)}
    before = (_REPO / "tmp" / "config_change.log").stat().st_size if (_REPO / "tmp" / "config_change.log").exists() else None
    done = subprocess.run(["bash", "-c", _wired_command()], input=json.dumps({"source": "project_settings", "file_path": "f"}),
                          capture_output=True, text=True, cwd=_REPO, env=env)
    assert done.returncode == 0 and "project_settings" in json.loads(done.stdout)["terminalSequence"]
    assert log.exists()
    after = (_REPO / "tmp" / "config_change.log").stat().st_size if (_REPO / "tmp" / "config_change.log").exists() else None
    assert after == before


def test_the_wired_command_exits_zero_silently_outside_a_git_repo(tmp_path):
    done = subprocess.run(["bash", "-c", _wired_command()], input="{}", capture_output=True, text=True, cwd=tmp_path)
    assert done.returncode == 0 and done.stdout == ""


def test_the_hook_is_registered_in_the_capability_envelope():
    lines = (_REPO / "registries" / "capability_envelope_registry.jsonl").read_text(encoding="utf-8").splitlines()
    values = {json.loads(line)["value"] for line in lines if line.strip() and json.loads(line)["field"] == "hooks"}
    assert f"ConfigChange||{_wired_command()}" in values
