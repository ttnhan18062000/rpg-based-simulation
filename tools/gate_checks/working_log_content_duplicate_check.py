"""Ratchet-based content check for duplicate `(ticket_id, title)` rows in
`tickets/working_log.csv` (TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS item 6).

**The defect this catches**: `tools/agent-monitoring/record_hand_orchestrated_closure.py`
internally calls `append_working_log_row()` (`TCK-20260912-WORKING-LOG-APPEND-HELPER`'s
sanctioned writer). Calling the helper directly and then running the closure tool writes two
rows for the same ticket close, both through the documented, sanctioned path -- the closure
tool's own docstring warns of this, which makes it known but not prevented. A writer-scan guard
(e.g. "only one function may call the CSV write primitive") structurally cannot catch this,
because both call sites ARE the one sanctioned writer, called twice; only a content check on the
artifact itself -- are there two rows for the same (ticket_id, title)? -- can.

**Why a ratchet, not zero-tolerance**: the real corpus has 46 duplicate `(ticket_id, title)` pairs
today (measured 2026-09-14, independently reproduced by two sessions). A hard zero-tolerance
assertion would be unlandable on day one -- the same failure mode as
`TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` and this same ticket's own
item 1 (`working_log_duplicate_check.py`). This check records the baseline and forbids growth
instead of demanding an immediate, unrealistic zero.

Note this is a DIFFERENT defect class from item 1's `working_log_duplicate_check.py`, even though
the two checks' real-corpus sets now overlap heavily in practice: as of 2026-09-14, post-item-2-fix
(which widened item 1's own duplicate-ticket_id scan to include previously `is_duplicate`-flagged
rows), item 1's 84 duplicate-ticket_ids set FULLY CONTAINS all 46 of this check's duplicate-
(ticket_id, title)-pair ids -- not "mostly disjoint" as an earlier measurement (taken before item
2's fix landed, when item 1 only caught 57 ids) had found. The distinction that justifies keeping
these as two separate checks is therefore semantic, not set-overlap: item 1 flags ticket_id reuse
regardless of title (historical ID-namespace collisions, e.g. the same id used for several
unrelated pieces of work over time) -- a naming/process problem. This check flags ticket_id reuse
with the SAME title (the same log entry written twice) -- a dual-writer data-integrity problem with
a different root cause and a different fix (item 1's fix is "don't reuse ticket_ids"; this one's is
"don't call the sanctioned writer twice for the same close"). A row that is a same-title duplicate
happens to also be a same-ticket_id duplicate, so full containment here is expected, not a sign
these checks are redundant.

Mirrors `working_log_duplicate_check.py`'s own shape: an aggregate `check_*()` function returning
`List[dict]` (`{"status": "PASS"|"FAIL", "evidence": "..."}`), a `MARKER:` + `json.dumps(result)`
stdout contract in `__main__`.
"""
import json
import sys
from collections import Counter
from pathlib import Path
from typing import List

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from working_log_parser import parse_working_log  # noqa: E402

DEFAULT_LOG_PATH = Path("tickets/working_log.csv")

# Ratchet ceiling: the real corpus's own duplicate-(ticket_id, title)-pair count as of 2026-09-14.
# May only decrease. Raising it to paper over a newly-introduced duplicate defeats the entire
# point of this check -- see the module docstring above for why a zero-tolerance assertion is not
# landable here.
DUPLICATE_PAIR_CEILING = 46


def find_duplicate_ticket_id_title_pairs(log_path: Path = DEFAULT_LOG_PATH) -> "set[tuple[str, str]]":
    """Returns every (ticket_id, title) pair that appears more than once among the tolerant
    parser's kept rows (clean + recovered records, including physical-duplicate-flagged rows --
    a genuine duplicate write is exactly what those rows often are)."""
    parse_result = parse_working_log(log_path)
    kept_rows = [r for r in parse_result.rows if r.record is not None]
    pair_counter = Counter(
        (r.record.get("ticket_id", "").strip(), r.record.get("title", "").strip())
        for r in kept_rows
    )
    return {pair for pair, count in pair_counter.items() if count > 1 and pair[0]}


def check_working_log_content_duplicates(
    log_path: Path = DEFAULT_LOG_PATH,
    ceiling: int = DUPLICATE_PAIR_CEILING,
) -> List[dict]:
    """Ratcheted duplicate-(ticket_id, title)-pair check: PASS if the real count is at or below
    `ceiling` (the known historical baseline), FAIL if it has grown (a new dual-writer-style
    duplicate was introduced)."""
    dupes = find_duplicate_ticket_id_title_pairs(log_path)
    count = len(dupes)

    if count > ceiling:
        new_count = count - ceiling
        return [{
            "status": "FAIL",
            "evidence": (
                f"{count} duplicate (ticket_id, title) pair(s) in {log_path} exceeds the ratchet "
                f"ceiling ({ceiling}) by {new_count} -- a new duplicate write was introduced. "
                f"Full set: {sorted(dupes)}"
            ),
        }]

    return [{
        "status": "PASS",
        "evidence": f"{count} duplicate (ticket_id, title) pair(s) (ceiling {ceiling}) -- no new duplicates",
    }]


if __name__ == "__main__":
    result = check_working_log_content_duplicates()
    print("MARKER:" + json.dumps(result))
