"""Pin for TCK-20260929-RUN-EXECUTION-MODE-FIELD: every real pipeline run-writer (the
`record_run.py` command text in `.claude/workflows/{implement-ticket,implement-epic,
create-tickets,simq-audit}.js`) must include `"execution_mode":"pipeline"` in every
`record_run.py --data '{...}'` invocation, not just one -- an early-exit path (INVALID_ARGS,
SCOPE_AGENT_FAILED, EPIC_CREATED, NOTHING_TO_DO) is still a real pipeline execution, not a hand
closure, and leaving any of them unlabelled would recreate the exact "unlabelled ambiguity" this
ticket exists to eliminate.

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
    "filename,expected_min_calls",
    [
        ("implement-ticket.js", 2),
        ("implement-epic.js", 4),
        ("create-tickets.js", 1),
        ("simq-audit.js", 1),
    ],
)
def test_every_record_run_call_site_sets_execution_mode_pipeline(filename, expected_min_calls):
    js_path = _WORKFLOWS_DIR / filename
    calls = _record_run_calls(js_path)
    assert len(calls) >= expected_min_calls, (
        f"{filename}: expected at least {expected_min_calls} record_run.py call sites, "
        f"found {len(calls)} — has a call site been added or removed?"
    )
    for call_text in calls:
        assert '"execution_mode":"pipeline"' in call_text, (
            f"{filename}: a record_run.py --data call is missing "
            f'"execution_mode":"pipeline" -- every real pipeline run-writer call site must '
            f"set it, including early-exit paths (INVALID_ARGS/SCOPE_AGENT_FAILED/etc.), not "
            f"just the main success path. Call text: {call_text!r}"
        )


def test_no_workflow_js_file_sets_execution_mode_hand():
    # execution_mode: "hand" is exclusively written by record_hand_orchestrated_closure.py — a
    # real pipeline .js file writing "hand" would misrepresent its own execution as a hand
    # closure and defeat the whole point of the split.
    for js_path in _WORKFLOWS_DIR.glob("*.js"):
        text = js_path.read_text(encoding="utf-8")
        assert '"execution_mode":"hand"' not in text, (
            f"{js_path.name} sets execution_mode to 'hand' -- only "
            f"record_hand_orchestrated_closure.py should ever write that value"
        )
