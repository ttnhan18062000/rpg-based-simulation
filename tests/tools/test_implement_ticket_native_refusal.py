"""A native ``implement-ticket`` run is refused up front while gate sites still call the bare ``bash()``.

TCK-20261004-IMPLEMENT-TICKET-NATIVE-REFUSE-UP-FRONT-WHEN-GATE-SITES-UNPORTED. Natively ``bash`` is undefined, so a
non-epic run used to die with ``ReferenceError: bash is not defined`` after Scope (one run spent ~277k tokens). The real
script runs in a node ``vm`` with no ``bash`` (native) or a stubbed one (legacy), every dispatch stubbed and counted.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"
_NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(_NODE is None, reason="node not installed")

_HARNESS = """
const vm = require('vm');
const fs = require('fs');
const scenario = JSON.parse(process.argv[2]);
const source = fs.readFileSync(process.argv[1], 'utf8').replace(/^export const meta = /m, 'const meta = ');
const dispatches = [], commands = [];
const args = Object.assign({ start_ts: '2026-01-01T00:00:00Z', execution_id_suffix: 'smoke' }, scenario.args || {});
const sandbox = {
  args,
  agent: async (prompt, opts) => {
    dispatches.push({ label: opts && opts.label, prompt: String(prompt) });
    if (scenario.recorderThrows && opts && opts.label === 'refusal-record') throw new Error('recorder exploded');
    if (opts && opts.label === 'scope') {
      return { ticket_id: 'TCK-20260101-SMOKE', ticket_path: 'agent-working/tickets/inprogress/TCK-20260101-SMOKE.md',
        status: 'CREATED', conflicts: [], tier: 'epic', tags: [], suggested_skills: [], mistag_warning: false, summary: 's' };
    }
    return { exit_code: 0, stdout: '' };
  },
  log: () => {}, phase: () => {}, console,
};
if (!scenario.native) sandbox.bash = async (cmd) => { commands.push(String(cmd)); return ''; };
vm.createContext(sandbox);
(async () => {
  let thrown = null, returned = null;
  try { returned = await vm.runInContext('(async () => {' + source + '\\n})()', sandbox); }
  catch (e) { thrown = e.message; }
  process.stdout.write(JSON.stringify({ thrown, returned, dispatches, commands }));
})();
"""


def _run(**scenario) -> dict:
    proc = subprocess.run(
        [_NODE, "-e", _HARNESS, str(SCRIPT), json.dumps(scenario)],
        capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _pipeline_dispatches(result: dict) -> list:
    return [d for d in result["dispatches"] if d["label"] != "refusal-record"]


@pytest.mark.parametrize("args", [{"tier": "standard"}, {"tier": "hotfix"}, {}])
def test_native_non_epic_or_unknown_tier_is_refused_with_no_pipeline_agent(args):
    result = _run(native=True, args=args)
    assert result["thrown"] is None
    assert result["returned"]["status"] == "NATIVE_GATE_SITES_UNPORTED"
    assert "legacy runtime" in result["returned"]["message"]
    assert _pipeline_dispatches(result) == []


def test_positive_control_same_input_reaches_scope_when_the_refusal_is_absent():
    """Without the refusal list the same native input would dispatch Scope: prove the counter can see it by running
    the script with the list emptied (what the port tickets will eventually do)."""
    source = SCRIPT.read_text(encoding="utf-8")
    emptied = re.sub(r"const NATIVE_UNPORTED_GATE_SITES = \[.*?\n\]", "const NATIVE_UNPORTED_GATE_SITES = []", source, flags=re.S)
    assert emptied != source
    tmp = SCRIPT.parent / "_tmp_refusal_control.js"
    tmp.write_text(emptied, encoding="utf-8")
    try:
        proc = subprocess.run(
            [_NODE, "-e", _HARNESS, str(tmp), json.dumps({"native": True, "args": {"tier": "standard"}})],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60,
        )
    finally:
        tmp.unlink()
    result = json.loads(proc.stdout)
    assert any(d["label"] == "scope" for d in result["dispatches"]), "control: Scope must be reachable without the refusal"


def test_native_epic_tier_is_not_refused():
    result = _run(native=True, args={"tier": "epic"})
    assert (result["returned"] or {}).get("status") != "NATIVE_GATE_SITES_UNPORTED"
    assert any(d["label"] == "scope" for d in result["dispatches"])


def test_legacy_runtime_is_unaffected():
    result = _run(native=False, args={"tier": "standard"})
    assert (result["returned"] or {}).get("status") != "NATIVE_GATE_SITES_UNPORTED"
    assert any(d["label"] == "scope" for d in result["dispatches"])


def test_refusal_writes_a_run_row_and_event_best_effort():
    result = _run(native=True, args={"tier": "standard"})
    recorder = [d["prompt"] for d in result["dispatches"] if d["label"] == "refusal-record"]
    assert len(recorder) == 2
    assert any('"final_status":"NATIVE_GATE_SITES_UNPORTED"' in p and "record_run.py" in p for p in recorder)
    assert any("record_events.py" in p for p in recorder)


def test_recorder_failure_never_changes_the_refusal_status():
    result = _run(native=True, args={"tier": "standard"}, recorderThrows=True)
    assert result["thrown"] is None
    assert result["returned"]["status"] == "NATIVE_GATE_SITES_UNPORTED"


def _bare_bash_sites(source: str) -> set[str]:
    """Variables assigned from a bare ``bash(`` call on a non-comment line."""
    sites = set()
    for line in source.splitlines():
        if line.lstrip().startswith("//"):
            continue
        m = re.search(r"const (\w+) = (?:.*?)\bawait bash\(", line)
        if m:
            sites.add(m.group(1))
        elif re.search(r"(?<![\w.])bash\(", line) and "legacyBash" not in line:
            raise AssertionError(f"bare bash( site not assigned to a const, cannot be keyed: {line.strip()[:100]}")
    return sites


def test_unported_site_list_equals_the_actual_bare_bash_call_sites():
    source = SCRIPT.read_text(encoding="utf-8")
    listed = set(re.search(r"const NATIVE_UNPORTED_GATE_SITES = \[(.*?)\n\]", source, re.S).group(1).replace("'", "").replace(",", " ").split())
    assert listed == _bare_bash_sites(source), (
        "NATIVE_UNPORTED_GATE_SITES must list exactly the variables assigned from a bare `bash(` call: add a new "
        "site to the list, or remove a site you ported to sh()/shOmit()"
    )
