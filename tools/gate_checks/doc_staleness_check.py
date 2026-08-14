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

Wired into `.claude/workflows/implement-ticket.js` by `TCK-20260720-GATE-CHECK-WIRING-DECISIONS`
as a hard blocking gate (`DOC_STALENESS_BLOCKED`). Built to the same `MARKER:`-prefixed JSON CLI
contract every other `gate_checks` script uses.

`TCK-20260802-DOC-UPDATE-DISCIPLINE` added two extensions, both additive — no existing `PASS`/`FAIL`
verdict changes shape or meaning:
- `config/` (e.g. `config/simulation_quality/*.yaml` scoring weights/thresholds — behavior-driving
  settings that live outside `src/`) is now a flagged prefix alongside `src/` and
  `.claude/workflows/*.js`.
- An optional `docs_to_update` param (paths the Investigate phase identified up front as needing an
  update) adds a separate, non-blocking `ADVISORY` result entry when one of those specific paths
  isn't in `files_changed` — even if the blanket `docs/`-path-presence check already `PASS`es. This
  is intentionally advisory-only (confirmed with the user during scoping): promoting it to a hard
  block is deferred until there's evidence of how often Investigate over-lists docs that turn out
  not to need touching once Review/Implement refine the plan — same reasoning that kept this whole
  check unwired for one ticket cycle before TCK-20260720 promoted it to blocking.
"""

import json
import sys
from typing import List, Optional


def check_doc_staleness(
    files_changed: List[str],
    behavior_changed: bool,
    docs_to_update: Optional[List[str]] = None,
) -> List[dict]:
    """Aggregate verdict: did a behavior-changing src/config/workflow diff skip its docs/ update.

    Single aggregate entry point (mirrors `check_workflow_meta_conformance`'s one-function,
    list-of-dicts shape). `FAIL` only when all three hold: `behavior_changed` is `True`, at least
    one path in `files_changed` starts with `src/`, starts with `config/`, or is a
    `.claude/workflows/*.js` path, and zero paths in `files_changed` start with `docs/`. Otherwise
    `PASS` — including when `behavior_changed` is `False` (e.g. a pure test-only change) or when a
    `docs/` path is present alongside the src/config/workflow change. `FAIL` returns early with a
    single-entry list — `docs_to_update` is not consulted in that case, since a blanket failure is
    already the strongest signal.

    When the `PASS` branch is taken and `docs_to_update` names paths not present in
    `files_changed`, a second, non-blocking `ADVISORY` entry is appended — the caller must never
    treat this as a `FAIL`.
    """
    flagged_paths = [
        path for path in files_changed
        if path.startswith("src/")
        or path.startswith("config/")
        or (path.startswith(".claude/workflows/") and path.endswith(".js"))
    ]
    docs_paths = [path for path in files_changed if path.startswith("docs/")]

    if behavior_changed and flagged_paths and not docs_paths:
        return [{
            "status": "FAIL",
            "evidence": f"behavior_changed=True touched {flagged_paths} with no docs/ path in "
                        f"files_changed",
        }]

    results = [{
        "status": "PASS",
        "evidence": f"behavior_changed={behavior_changed}, "
                    f"{len(flagged_paths)} src/config/workflow path(s) flagged, "
                    f"{len(docs_paths)} docs/ path(s) present",
    }]

    if docs_to_update:
        missing = [path for path in docs_to_update if path not in files_changed]
        if missing:
            results.append({
                "status": "ADVISORY",
                "evidence": f"investigation.md flagged {missing} as requiring an update, but "
                            f"none of these specific path(s) appear in files_changed — verify "
                            f"they don't need touching, or update them",
            })

    return results


if __name__ == "__main__":
    behavior_changed_arg = sys.argv[1].lower() == "true"
    rest_args = sys.argv[2:]
    if "--docs-to-update" in rest_args:
        split_idx = rest_args.index("--docs-to-update")
        files_changed_arg = rest_args[:split_idx]
        docs_to_update_arg = rest_args[split_idx + 1:]
    else:
        files_changed_arg = rest_args
        docs_to_update_arg = []
    result = check_doc_staleness(files_changed_arg, behavior_changed_arg, docs_to_update_arg)
    print("MARKER:" + json.dumps(result))
