"""Measures tools/validate_working_log.py's duplicate-ticket-ID scan
(TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS item 1).

`tools/validate_working_log.py` implements a "Duplicate ticket IDs in working_log.csv" check with
its own passing tests, but `grep -rln validate_working_log tools .github/workflows Makefile
.claude tests` returned exactly two files: the module itself and its test -- no CI job, no
Makefile target, no gate check, nothing in `.claude/` ever invoked it. It had never run outside
its own test.

**This module used to also gate on the count (a ratchet ceiling, `DUPLICATE_TICKET_ID_CEILING`);
that gate was removed by TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION
(2026-09-16). Do not rebuild it.** The count moves whenever a ticket goes through a legitimate
multi-phase closure (e.g. BLOCKED -> DONE, writing two working_log rows for the same ticket_id) --
confirmed directly: `TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE`'s own ordinary
two-phase closure moved this count 84 -> 85 on 2026-09-14, consuming ratchet headroom for doing
nothing wrong. The real corpus also carries 57+ pre-existing `ticket_id` NAMESPACE COLLISIONS
(`TCK-20260401-FINAL-CONVERGENCE` alone names three unrelated tickets) that are historical reuse,
not the dual-writer/CRLF-duplication defect this measurement exists to catch -- a threshold over
the combined count cannot distinguish "a ticket legitimately reopened" from "a new namespace
collision" from "the CRLF dual-writer defect recurred," so it fires on ordinary activity as often
as on a real regression. Same inverted-signal shape as the deleted sidecar-attribution and
citation-resolution floors (see `sidecar_attribution_coverage_check.py`'s own docstring for the
full precedent this follows). The measurement stays -- it is genuinely useful reported context --
just not something to block on.

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


def compute_working_log_duplicate_ticket_ids(
    log_path: Path = DEFAULT_LOG_PATH,
    done_dir: Path = DEFAULT_DONE_DIR,
) -> "tuple[list, int]":
    """Returns (duplicate_ticket_ids, count) -- the real duplicate-ticket_id set in
    working_log.csv, unchanged in shape from before the gate's removal."""
    result = run_validation(log_path, done_dir)
    dupes = result["duplicate_ticket_ids"]
    return dupes, len(dupes)


def check_working_log_duplicate_ticket_ids(
    log_path: Path = DEFAULT_LOG_PATH,
    done_dir: Path = DEFAULT_DONE_DIR,
) -> List[dict]:
    """Reports the real duplicate-ticket_id count -- always PASS (see module docstring for why
    this is no longer a gate)."""
    dupes, count = compute_working_log_duplicate_ticket_ids(log_path, done_dir)
    return [{
        "status": "PASS",
        "evidence": f"{count} duplicate ticket_id(s) in {log_path}",
    }]


if __name__ == "__main__":
    result = check_working_log_duplicate_ticket_ids()
    print("MARKER:" + json.dumps(result))
