"""Pin for TCK-20260929-RUN-EXECUTION-MODE-FIELD, extended by
TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT: every real `.claude/workflows/*.js` run-writer
must include the same `execution_mode` literal in every `record_run.py --data '{...}'` invocation
it has, not just one -- an early-exit path (INVALID_ARGS, SCOPE_AGENT_FAILED, EPIC_CREATED,
NOTHING_TO_DO) is still a real execution of that script, not a hand closure, and leaving any of
them unlabelled would recreate the exact "unlabelled ambiguity" this ticket exists to eliminate.

Two literals are in play now, not one: `create-tickets.js` was ported to run on the native
Claude Code `Workflow` tool by the pilot ticket above, so its own record_run.py call always
writes `"execution_mode":"workflow"` — this code path only ever executes through that tool (hand-
narration, by definition, never runs this literal JS, it reads it and manually issues equivalent
tool calls instead). The other three workflow scripts are still hand-narrated only and keep
`"execution_mode":"pipeline"` until each gets its own porting ticket (out of scope here — see the
pilot ticket's Out of Scope and pilot_measurement.md's go/no-go).

Mirrors `test_finalize_working_log_uses_helper_pin.py`'s raw-source-text-parsing pattern (no JS
test runner exists in this repo for `.claude/workflows/*.js` files) — pure text assertions,
never a JS execution.
"""
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
_WORKFLOWS_DIR = _REPO_ROOT / ".claude" / "workflows"

_RECORD_RUN_CALL_RE = re.compile(
    r"record_run\.py --data '(\{.*?\})'", re.DOTALL
)


def _record_run_calls(js_path: Path) -> list:
    text = js_path.read_text(encoding="utf-8")
    calls = _RECORD_RUN_CALL_RE.findall(text)
    assert calls, f"{js_path.name}: no record_run.py --data '{{...}}' call found — has it moved?"
    return calls


@pytest.mark.parametrize(
    "filename,expected_min_calls,expected_mode",
    [
        ("implement-ticket.js", 2, "pipeline"),
        ("implement-epic.js", 4, "pipeline"),
        ("create-tickets.js", 1, "workflow"),
        ("simq-audit.js", 1, "pipeline"),
    ],
)
def test_every_record_run_call_site_sets_its_expected_execution_mode(filename, expected_min_calls, expected_mode):
    js_path = _WORKFLOWS_DIR / filename
    calls = _record_run_calls(js_path)
    assert len(calls) >= expected_min_calls, (
        f"{filename}: expected at least {expected_min_calls} record_run.py call sites, "
        f"found {len(calls)} — has a call site been added or removed?"
    )
    for call_text in calls:
        assert f'"execution_mode":"{expected_mode}"' in call_text, (
            f'{filename}: a record_run.py --data call is missing "execution_mode":"{expected_mode}" '
            f"-- every real run-writer call site must set it, including early-exit paths "
            f"(INVALID_ARGS/SCOPE_AGENT_FAILED/etc.), not just the main success path. "
            f"Call text: {call_text!r}"
        )


def test_no_workflow_js_file_sets_execution_mode_hand():
    # execution_mode: "hand" is exclusively written by record_hand_orchestrated_closure.py — a
    # workflow .js file writing "hand" would misrepresent its own execution as a hand closure and
    # defeat the whole point of the split.
    for js_path in _WORKFLOWS_DIR.glob("*.js"):
        text = js_path.read_text(encoding="utf-8")
        assert '"execution_mode":"hand"' not in text, (
            f"{js_path.name} sets execution_mode to 'hand' -- only "
            f"record_hand_orchestrated_closure.py should ever write that value"
        )


def test_only_create_tickets_js_sets_execution_mode_workflow():
    # "workflow" means the native Workflow tool actually executed the script (TCK-20260929-
    # CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT). The other three scripts are still hand-narration-
    # only until each gets its own porting ticket — a stray "workflow" literal in one of them
    # would claim native execution that was never actually piloted or measured.
    for js_path in _WORKFLOWS_DIR.glob("*.js"):
        text = js_path.read_text(encoding="utf-8")
        if js_path.name == "create-tickets.js":
            assert '"execution_mode":"workflow"' in text
        else:
            assert '"execution_mode":"workflow"' not in text, (
                f"{js_path.name} sets execution_mode to 'workflow' but has not been piloted on "
                f"the native Workflow tool -- only create-tickets.js has, so far"
            )
