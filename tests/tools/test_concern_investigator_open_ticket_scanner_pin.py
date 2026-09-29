"""Pin for `.claude/agents/concern-investigator.md` Step 3's open-ticket overlap scanner call
(TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER).

`working_log.csv` only covers closed tickets; Step 3 must also run
`tools/open_ticket_overlap.py` to see open ones, and must keep framing hits as informational
(never a blocking duplicate call on its own).
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_CONCERN_INVESTIGATOR_PATH = _REPO_ROOT / ".claude" / "agents" / "concern-investigator.md"

_OPEN_ANCHOR = "─── Step 3: Prior ticket history via working_log.csv"
_CLOSE_ANCHOR = "─── Step 4: Code files"


def _step_3_text() -> str:
    text = _CONCERN_INVESTIGATOR_PATH.read_text(encoding="utf-8")
    open_idx = text.find(_OPEN_ANCHOR)
    close_idx = text.find(_CLOSE_ANCHOR)
    assert open_idx != -1, "Step 3's opening anchor not found — has the step moved or been reworded?"
    assert close_idx != -1, "Step 4's opening anchor not found — has the step moved or been reworded?"
    assert open_idx < close_idx, "Step 3 must precede Step 4"
    return text[open_idx:close_idx]


def test_step_3_runs_the_open_ticket_overlap_scanner():
    step_3 = _step_3_text()
    assert "open_ticket_overlap.py" in step_3, (
        "Step 3 no longer calls tools/open_ticket_overlap.py — "
        "see TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER"
    )


def test_step_3_frames_scanner_hits_as_informational_not_automatically_duplicate():
    step_3 = _step_3_text()
    assert "never sets" in step_3 and "is_duplicate=true" in step_3, (
        "Step 3 no longer states a scanner hit can't set is_duplicate=true on its own — "
        "see TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER"
    )
