"""The ConfigChange warning hook (TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION): warns, never blocks, fails open."""
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.sessions import config_change_warning as ccw

_SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "sessions" / "config_change_warning.py"


def _run(stdin_text):
    out = io.StringIO()
    rc = ccw.main(stdin=io.StringIO(stdin_text), stdout=out)
    return rc, out.getvalue()


def test_a_settings_change_prints_one_warning_naming_the_source_and_the_file():
    rc, out = _run(json.dumps({"hook_event_name": "ConfigChange", "source": "project_settings", "file_path": ".claude/settings.json"}))
    assert rc == 0
    message = json.loads(out)["systemMessage"]
    assert "project_settings" in message and ".claude/settings.json" in message and "immediately" in message
    assert out.count("\n") == 1


@pytest.mark.parametrize("text", ["", "not json", "[]", "null", "{}"])
def test_odd_input_never_fails_and_never_blocks(text):
    rc, out = _run(text)
    assert rc == 0
    if out:
        assert "systemMessage" in json.loads(out) and "decision" not in json.loads(out)


def test_the_script_runs_as_a_hook_and_exits_zero():
    done = subprocess.run([sys.executable, str(_SCRIPT)], input=json.dumps({"source": "local_settings", "file_path": "x"}),
                          capture_output=True, text=True)
    assert done.returncode == 0 and "local_settings" in done.stdout
