"""An uncaught exception in ``implement-ticket.js`` still leaves a run record and an error event, then propagates.

Runs the real script in a node ``vm`` with every dispatch stubbed. ``writeMonitoring`` hands the record writes to an
``agent()`` call whose prompt embeds the run row (``"final_status":"..."``), so the stub captures those prompts.
Before Scope has produced a ticket id the recorder falls back to raw ``record_events.py`` / ``record_run.py`` shell
commands (the ``SCOPE_AGENT_FAILED`` shape), captured through the stubbed ``bash``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_NODE = shutil.which("node")

_HARNESS = """
const vm = require('vm');
const fs = require('fs');
const scenario = JSON.parse(process.argv[2]);
const source = fs.readFileSync(process.argv[1], 'utf8').replace(/^export const meta = /m, 'const meta = ');
const prompts = [], commands = [];
const scopeReply = { ticket_id: 'TCK-20260101-SMOKE', ticket_path: 'agent-working/tickets/inprogress/TCK-20260101-SMOKE.md',
  status: 'CREATED', conflicts: scenario.conflicts || [], tier: 'hotfix', tags: [], suggested_skills: [], mistag_warning: false,
  summary: 'scoped' };
let calls = 0;
const sandbox = {
  args: { start_ts: '2026-01-01T00:00:00Z', execution_id_suffix: 'smoke' },
  agent: async (prompt, opts) => {
    calls++;
    prompts.push({ prompt: String(prompt), label: opts && opts.label });
    if (opts && opts.label === 'monitoring-write') {
      if (scenario.recorderThrows) throw new Error('recorder exploded');
      return 'monitoring written';
    }
    if (scenario.throwAtCall && calls === scenario.throwAtCall) throw new Error(scenario.message || 'boom at dispatch');
    if (opts && opts.label === 'scope') return scopeReply;
    return null;
  },
  bash: async (cmd) => { commands.push(String(cmd)); return ''; },
  log: () => {}, phase: () => {}, console,
};
vm.createContext(sandbox);
(async () => {
  let thrown = null, returned = null;
  try { returned = await vm.runInContext('(async () => {' + source + '\\n})()', sandbox); }
  catch (e) { thrown = e.message; }
  process.stdout.write(JSON.stringify({ thrown, returned, prompts, commands }));
})();
"""


def _run(**scenario) -> dict:
    proc = subprocess.run(
        [_NODE, "-e", _HARNESS, str(SCRIPT), json.dumps(scenario)],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _monitoring_prompts(result: dict) -> list:
    return [p["prompt"] for p in result["prompts"] if p["label"] == "monitoring-write"]


def _record_commands(result: dict, script: str) -> list:
    return [c for c in result["commands"] if script in c]


pytestmark = pytest.mark.skipif(_NODE is None, reason="node not installed")


def test_exception_after_scope_writes_one_error_run_and_event_then_rethrows_the_original() -> None:
    # Call 1 is the scope dispatch; the hotfix path then reaches the implement dispatch, which returns null and
    # makes `implementation.files_changed` throw a TypeError.
    result = _run()
    assert result["thrown"] and "Cannot read properties of null" in result["thrown"]
    prompts = _monitoring_prompts(result)
    assert len(prompts) == 1
    assert '"final_status":"WORKFLOW_ERROR"' in prompts[0]
    assert "WORKFLOW_ERROR after Review" in prompts[0]
    assert "implement-ticket-orchestrator" in prompts[0]


def test_exception_before_scope_finishes_uses_the_fallback_record_and_rethrows() -> None:
    result = _run(throwAtCall=1, message="scope dispatch died")
    assert result["thrown"] == "scope dispatch died"
    assert _monitoring_prompts(result) == []
    events = _record_commands(result, "record_events.py")
    runs = _record_commands(result, "record_run.py")
    assert len(events) == 1 and "WORKFLOW_ERROR before Scope finished" in events[0]
    assert len(runs) == 1 and '"final_status":"WORKFLOW_ERROR"' in runs[0]


def test_a_failing_recorder_never_masks_the_original_exception() -> None:
    result = _run(recorderThrows=True)
    assert result["thrown"] and "Cannot read properties of null" in result["thrown"]
    assert "recorder exploded" not in result["thrown"]


def test_a_normal_gate_return_writes_its_own_record_once_and_no_error_record() -> None:
    result = _run(conflicts=["duplicate of TCK-20260101-OTHER"])
    assert result["thrown"] is None
    assert result["returned"]["status"] == "CONFLICTS_DETECTED"
    prompts = _monitoring_prompts(result)
    assert len(prompts) == 1
    assert '"final_status":"CONFLICTS_DETECTED"' in prompts[0]
    assert "WORKFLOW_ERROR" not in prompts[0]


def test_an_exception_inside_the_normal_monitoring_write_does_not_write_a_second_run_row() -> None:
    result = _run(conflicts=["duplicate"], recorderThrows=True)
    assert result["thrown"] == "recorder exploded"
    assert len(_monitoring_prompts(result)) == 1
    assert _record_commands(result, "record_run.py") == []
