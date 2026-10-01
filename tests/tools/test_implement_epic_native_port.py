"""TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT: implement-epic.js runs on the native Workflow runtime.

Text-level pins (no JS test runner exists for `.claude/workflows/*.js`; same approach as the sibling
create-tickets pins), plus the acorn parse the runtime itself performs.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from workflow_bash_sites import find_bash_call_sites  # noqa: E402

SCRIPT = REPO / ".claude" / "workflows" / "implement-epic.js"
SRC = SCRIPT.read_text(encoding="utf-8")
ACORN = REPO / "frontend" / "node_modules" / "acorn"
NODE = shutil.which("node")


def _code_lines():
    out = []
    in_block = False
    for line in SRC.splitlines():
        s = line.strip()
        if in_block:
            in_block = "*/" not in s
            continue
        if s.startswith("/*"):
            in_block = "*/" not in s
            continue
        if s.startswith("//") or s.startswith("*"):
            continue
        out.append(line)
    return "\n".join(out)


def test_no_bash_call_sites_remain():
    assert find_bash_call_sites(SCRIPT) == []


def test_no_nondeterministic_calls_remain_in_code():
    code = _code_lines()
    assert "Date.now(" not in code
    assert "Math.random(" not in code
    assert not re.search(r"new Date\(\s*\)", code)


@pytest.mark.skipif(NODE is None or not ACORN.exists(), reason="node or frontend/node_modules/acorn missing")
def test_parses_under_the_runtimes_acorn_options():
    script = (
        "const a=require(process.argv[1]);const fs=require('fs');"
        "try{a.parse(fs.readFileSync(process.argv[2],'utf8'),{ecmaVersion:'latest',sourceType:'module',"
        "allowReturnOutsideFunction:true,allowAwaitOutsideFunction:true});console.log(JSON.stringify({ok:true}))}"
        "catch(e){console.log(JSON.stringify({ok:false,message:e.message}))}"
    )
    out = subprocess.run([NODE, "-e", script, str(ACORN), str(SCRIPT)], capture_output=True, text=True, timeout=30)
    assert json.loads(out.stdout)["ok"] is True, out.stdout


def test_missing_start_ts_returns_structured_invalid_args_before_any_work():
    assert "const startTs = (args && args.start_ts) || ''" in SRC
    start = SRC.index("if (!startTs) {")
    block = SRC[start:SRC.index("\n}", start)]
    assert "status: 'INVALID_ARGS'" in block and "start_ts" in block
    # ... and it comes before the first agent dispatch, the folder/epic/request check and Discover.
    assert start < SRC.index("if (!folder && !epicId && !request)") < SRC.index("phase('Discover')")
    assert "agent(" not in block and "runCommand(" not in block  # no record: there is no truthful timestamp


def test_run_start_time_is_args_start_ts_not_a_shell_capture():
    assert "const discoverTs = startTs" in SRC
    assert "captureTs" not in _code_lines()


def test_monitoring_writes_are_fail_open_and_label_the_run_as_workflow():
    helper = SRC[SRC.index("const runMonitoringCommand"):SRC.index("if (!folder && !epicId && !request)")]
    assert "MONITORWRITE_EXIT:" in helper and "log(`WARNING" in helper
    assert "throw" not in helper
    for call in re.findall(r"record_run\.py --data '(\{.*?\})'", SRC, re.DOTALL):
        assert '"execution_mode":"workflow"' in call


def test_every_command_goes_through_the_narrow_runner_with_exit_markers():
    for helper, marker in (("writeSidecar", "WRITESIDECAR_EXIT:"), ("clearSidecar", "CLEARSIDECAR_EXIT:")):
        body = SRC[SRC.index(f"const {helper} = async"):]
        body = body[: body.index("\n}\n")]
        assert "runCommand(" in body and marker in body, helper
        assert "log(`WARNING" in body, helper  # fail-open: warn, never throw


def test_every_site_ported_was_classified_bookkeeping_not_a_gate():
    """The 11 original sites were timestamps, sidecar writes and monitoring records; none decided a
    verdict, so the plain runCommand route is safe (classification in the ticket's stored artifact).
    A verdict-producing command added later must not reuse runMonitoringCommand."""
    for label in re.findall(r"runMonitoringCommand\(\s*`.*?`,\s*'([^']+)'", SRC, re.DOTALL):
        assert label.startswith("record-"), label


def test_unavailable_child_workflow_is_reported_with_the_fallback():
    assert "workflow('implement-ticket', ticketArgs)" in SRC  # nesting is one level: allowed here
    assert "status: 'WORKFLOW_ERROR'" in SRC
    assert "TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT" in SRC
    assert "dispatch the children from the top-level session" in SRC
