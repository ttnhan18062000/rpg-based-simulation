"""Regression test for TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT (AC1).

The native Claude Code `Workflow` tool parses a `.claude/workflows/*.js` script with acorn using
`sourceType: 'module'`, `allowReturnOutsideFunction: true`, and `allowAwaitOutsideFunction: true`
(the same options this file uses) before it will run it at all. `create-tickets.js` failed this
parse before the pilot ticket (unescaped backticks nested inside outer template-literal prompt
strings at lines 613 and 778 prematurely closed the outer literal) — `Workflow({name:
'create-tickets'})` surfaced this as a bare "parse error" with no file/line pointer, so this test
pins the fix with an actual acorn parse, not just a text-pattern check.

acorn itself is a transitive `frontend/` devDependency (pulled in by eslint/vite, not declared
directly) — this test skips cleanly, not fails, when `frontend/node_modules/acorn` or `node`
itself is absent (e.g. a worktree that has never run `npm ci`/`npm install` under `frontend/`).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOWS_DIR = _REPO_ROOT / ".claude" / "workflows"
_ACORN_DIR = _REPO_ROOT / "frontend" / "node_modules" / "acorn"
_NODE = shutil.which("node")

# The exact options the native Workflow runtime's own acorn parse uses, per
# TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT's confirmed-by-trying investigation.
_PARSE_SCRIPT = """
const acorn = require(process.argv[1]);
const fs = require('fs');
const files = JSON.parse(process.argv[2]);
const results = {};
for (const [name, path] of Object.entries(files)) {
  try {
    acorn.parse(fs.readFileSync(path, 'utf8'), {
      ecmaVersion: 'latest',
      sourceType: 'module',
      allowReturnOutsideFunction: true,
      allowAwaitOutsideFunction: true,
    });
    results[name] = { ok: true };
  } catch (e) {
    results[name] = { ok: false, message: e.message };
  }
}
process.stdout.write(JSON.stringify(results));
"""


def _acorn_parse_all_workflows():
    files = {p.name: str(p) for p in sorted(_WORKFLOWS_DIR.glob("*.js"))}
    proc = subprocess.run(
        [_NODE, "-e", _PARSE_SCRIPT, str(_ACORN_DIR), json.dumps(files)],
        capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=30,
    )
    assert proc.returncode == 0, f"node parse-check script itself failed: {proc.stderr}"
    return json.loads(proc.stdout)


@pytest.mark.skipif(_NODE is None, reason="node not found on PATH")
@pytest.mark.skipif(not _ACORN_DIR.exists(), reason="frontend/node_modules/acorn not installed (run `cd frontend && npm ci`)")
def test_create_tickets_js_parses_under_workflow_runtime_acorn_options():
    results = _acorn_parse_all_workflows()
    assert "create-tickets.js" in results
    assert results["create-tickets.js"]["ok"] is True, (
        f"create-tickets.js failed the Workflow runtime's own acorn parse: "
        f"{results['create-tickets.js'].get('message')}"
    )


@pytest.mark.skipif(_NODE is None, reason="node not found on PATH")
@pytest.mark.skipif(not _ACORN_DIR.exists(), reason="frontend/node_modules/acorn not installed (run `cd frontend && npm ci`)")
def test_acorn_parse_status_matches_pilot_recorded_baseline():
    # Pins the acorn parse status pilot_measurement.md records for every workflow script at pilot
    # time (TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT AC7's "one-line acorn parse status
    # for all .claude/workflows/*.js"), so a future silent regression or fix is visible here first.
    # implement-ticket.js and simq-audit.js are OUT OF SCOPE for this ticket (their own backtick
    # fix is a future porting ticket's job, not asserted as a requirement here) — this only pins
    # today's known status so drift is visible, not enforced.
    results = _acorn_parse_all_workflows()
    assert results["create-tickets.js"]["ok"] is True
    assert results["implement-epic.js"]["ok"] is True
    assert results["implement-ticket.js"]["ok"] is False
    assert results["simq-audit.js"]["ok"] is False
