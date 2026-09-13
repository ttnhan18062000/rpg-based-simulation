"""Pin for `implement-ticket.js`'s Finalize step 4 instruction to use `tools/working_log_writer.py`
instead of a hand-rolled write (TCK-20260912-WORKING-LOG-APPEND-HELPER).

Mirrors `test_finalize_phase_status_instruction_pin.py`'s raw-source-text-parsing pattern (no JS
test runner exists in this repo for `.claude/workflows/*.js` files). Scoped specifically to the
Finalize agent's own prompt string -- the substring between its opening anchor
(`` `Finalize ticket ${tid}` ``, unique to this one prompt) and its closing anchor
(`` Report each step: DONE / SKIPPED (reason).`, `` -- the literal end of the template string,
immediately before `{ label: 'finalize' }`) -- not the wider `phase('Finalize')` block. That
wider block also contains 4 unrelated, legitimate orchestrator-run `python3 -c` self-checks
(`finalizeCheckOutput`/`monitoringCheckOutput`/`tagDriftCheckOutput`/`phaseMetaCheckOutput`) after
the agent's own prompt closes, so a negative assertion scanning the whole phase block would be
false from the moment it's written, before any regression ever occurs.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_IMPLEMENT_TICKET_PATH = _REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js"

_OPEN_ANCHOR = "`Finalize ticket ${tid}"
_CLOSE_ANCHOR = "Report each step: DONE / SKIPPED (reason).`,"


def _read() -> str:
    return _IMPLEMENT_TICKET_PATH.read_text(encoding="utf-8")


def _finalize_prompt() -> str:
    text = _read()
    open_idx = text.find(_OPEN_ANCHOR)
    close_idx = text.find(_CLOSE_ANCHOR)
    assert open_idx != -1, "Finalize prompt's opening anchor not found — has the prompt moved or been reworded?"
    assert close_idx != -1, "Finalize prompt's closing anchor not found — has the prompt moved or been reworded?"
    assert open_idx < close_idx, "opening anchor must precede closing anchor"
    return text[open_idx:close_idx]


def test_finalize_prompt_instructs_the_working_log_writer_helper():
    prompt = _finalize_prompt()
    assert "working_log_writer.py" in prompt, (
        "Finalize step 4 no longer points at tools/working_log_writer.py — "
        "see TCK-20260912-WORKING-LOG-APPEND-HELPER"
    )
    assert "--data-file" in prompt, (
        "Finalize step 4 no longer uses the --data-file JSON-file contract — "
        "see TCK-20260912-WORKING-LOG-APPEND-HELPER"
    )


def test_finalize_step_4_precedes_step_5():
    prompt = _finalize_prompt()
    step4_idx = prompt.find("4. Append to tickets/working_log.csv")
    step5_idx = prompt.find("5. ${tier")
    assert step4_idx != -1, "step 4's leading anchor text not found"
    assert step5_idx != -1, "step 5's leading anchor text not found"
    assert step4_idx < step5_idx, "step 4 (working_log.csv append) must precede step 5 (move staging_artifacts)"


def test_finalize_prompt_never_reintroduces_inline_python_source_embedding():
    prompt = _finalize_prompt()
    assert "python3 -c" not in prompt, (
        "Finalize's own prompt string must never construct the working_log.csv row via a "
        "`python3 -c` inline script — arbitrary agent-authored title/summary text would have to "
        "survive shell/Python source-embedding, reintroducing the exact per-agent-improvisation "
        "hazard TCK-20260912-WORKING-LOG-APPEND-HELPER closed. Use the Write-tool JSON file + "
        "--data-file contract instead."
    )
