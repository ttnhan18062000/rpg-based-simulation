"""Flag a behavior-changing diff that touches no `docs/` path.

Built for TCK-20260711-DOC-STALENESS-GATE-CHECK: the 2026-W28 agent-monitoring retro
(`agent-monitoring/retro/RETRO-2026-W28.md`) found done-checker's Verify phase failing its first
attempt on 22/61 calls (36%) in one week, every failure tagged `reason_code=dod_condition_failed`,
and traced (Notes items 1 and 3) to one recurring root cause: a behavior-changing Implement phase
touching `src/` or a `.claude/workflows/*.js` file without a corresponding `docs/` update, caught
only reactively by done-checker instead of before Verify. `TCK-20260711-EPIC-SCOPE-ORPHAN-FIX` and
`TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK` hit this exact shape in the same session.

Mirrors `workflow_meta_conformance.py`'s one-function, list-of-dicts shape (not
`parity_updater_static.py`'s two-call `expected_subsystems_for_files`/`cross_reference_touched`
split) — there is no agent-prompt injection point this check needs to feed, only a single
`files_changed`/`behavior_changed` -> PASS/FAIL verdict.

This ticket ships the check and its tests only. It is NOT wired into
`.claude/workflows/implement-ticket.js` or `tools/gate_checks/done_checker_static.py` — a future
ticket decides where/whether to call it, exactly as `workflow_meta_conformance.py` itself remains
unwired today. Built to the same `MARKER:`-prefixed JSON CLI contract every other `gate_checks`
script uses.
"""

import json
import sys
from typing import List


def check_doc_staleness(files_changed: List[str], behavior_changed: bool) -> List[dict]:
    """Aggregate verdict: did a behavior-changing src/workflow diff skip its docs/ update.

    Single aggregate entry point (mirrors `check_workflow_meta_conformance`'s one-function,
    list-of-dicts shape). `FAIL` only when all three hold: `behavior_changed` is `True`, at least
    one path in `files_changed` starts with `src/` or is a `.claude/workflows/*.js` path, and zero
    paths in `files_changed` start with `docs/`. Otherwise `PASS` — including when
    `behavior_changed` is `False` (e.g. a pure test-only change) or when a `docs/` path is present
    alongside the src/workflow change.
    """
    flagged_paths = [
        path for path in files_changed
        if path.startswith("src/")
        or (path.startswith(".claude/workflows/") and path.endswith(".js"))
    ]
    docs_paths = [path for path in files_changed if path.startswith("docs/")]

    if behavior_changed and flagged_paths and not docs_paths:
        return [{
            "status": "FAIL",
            "evidence": f"behavior_changed=True touched {flagged_paths} with no docs/ path in "
                        f"files_changed",
        }]

    return [{
        "status": "PASS",
        "evidence": f"behavior_changed={behavior_changed}, "
                    f"{len(flagged_paths)} src/workflow path(s) flagged, "
                    f"{len(docs_paths)} docs/ path(s) present",
    }]


if __name__ == "__main__":
    behavior_changed_arg = sys.argv[1].lower() == "true"
    files_changed_arg = sys.argv[2:]
    result = check_doc_staleness(files_changed_arg, behavior_changed_arg)
    print("MARKER:" + json.dumps(result))
