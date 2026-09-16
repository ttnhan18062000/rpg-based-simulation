"""Ratchet-based gate check over tools/validate_working_log.py's duplicate-ticket-ID scan
(TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS item 1).

`tools/validate_working_log.py` implements a "Duplicate ticket IDs in working_log.csv" check with
its own passing tests, but `grep -rln validate_working_log tools .github/workflows Makefile
.claude tests` returned exactly two files: the module itself and its test -- no CI job, no
Makefile target, no gate check, nothing in `.claude/` ever invoked it. It had never run outside
its own test.

**Why this is a ratchet, not a zero-tolerance gate**: the real corpus has 57 duplicate ticket_ids
even with item 2's fix landed (measured 2026-09-14, both by this session and independently by
agent-working-design). 39 of those carry more than one distinct title (`TCK-20260401-FINAL-
CONVERGENCE` alone has three unrelated ones: "Final Convergence and Stabilization", "AOA
Introspection Hardening", "API Presenter Convergence") -- genuine historical `ticket_id` NAMESPACE
COLLISIONS, not the dual-writer/CRLF-duplication defect this wiring exists to catch going forward.
Wiring the existing check as a hard zero-tolerance gate would be immediately red on 57 pre-existing
violations this ticket does not fix and is not scoped to fix -- the same "unlandable exact-equality
assertion" failure mode as `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` and
this same ticket's own item 6. A ratchet freezes the 57 (forbidding new collisions) rather than
resolving them -- whether the historical ID reuse itself needs its own cleanup ticket is a separate
question this one deliberately does not answer.

Mirrors `status_drift_check.py`'s shape: an aggregate `check_*()` function returning `List[dict]`
(`{"status": "PASS"|"FAIL", "evidence": "..."}`), a `MARKER:` + `json.dumps(result)` stdout
contract in `__main__`.
"""
import json
import sys
from pathlib import Path
from typing import List

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from validate_working_log import run_validation  # noqa: E402

DEFAULT_LOG_PATH = Path("tickets/working_log.csv")
DEFAULT_DONE_DIR = Path("tickets/done")

# Ratchet ceiling: the real corpus's own duplicate-ticket_id count as of 2026-09-14, AFTER item
# 2's exclusion fix landed (item 2 intentionally widened what this scan sees -- it now includes
# is_duplicate=True rows too -- so the correct baseline is post-fix, not the 57 measured before
# item 2, which the ticket cites as the pre-fix reference figure). May only decrease. Raising it
# to paper over a newly-introduced duplicate defeats the entire point of this check -- see the
# module docstring above for why a zero-tolerance assertion is not landable here.
#
# Re-pinned 84 -> 85 the same day: traced directly, not guessed --
# TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE has two real, legitimate
# working_log.csv rows (2026-09-14, BLOCKED -- investigation complete, pending peer/user review;
# 2026-09-15, DONE -- Option A implemented after that review resolved it), the exact
# multi-invocation-continuation shape this check's own module docstring already documents as
# tolerated, not a new duplicate-ticket_id defect class.
DUPLICATE_TICKET_ID_CEILING = 85


def check_working_log_duplicate_ticket_ids(
    log_path: Path = DEFAULT_LOG_PATH,
    done_dir: Path = DEFAULT_DONE_DIR,
    ceiling: int = DUPLICATE_TICKET_ID_CEILING,
) -> List[dict]:
    """Ratcheted duplicate-ticket_id check: PASS if the real count is at or below `ceiling`
    (the known historical baseline), FAIL if it has grown (a new duplicate was introduced)."""
    result = run_validation(log_path, done_dir)
    dupes = result["duplicate_ticket_ids"]
    count = len(dupes)

    if count > ceiling:
        new_count = count - ceiling
        return [{
            "status": "FAIL",
            "evidence": (
                f"{count} duplicate ticket_id(s) in {log_path} exceeds the ratchet ceiling "
                f"({ceiling}) by {new_count} -- a new duplicate was introduced. Full set: {dupes}"
            ),
        }]

    return [{
        "status": "PASS",
        "evidence": f"{count} duplicate ticket_id(s) (ceiling {ceiling}) -- no new duplicates",
    }]


if __name__ == "__main__":
    result = check_working_log_duplicate_ticket_ids()
    print("MARKER:" + json.dumps(result))
