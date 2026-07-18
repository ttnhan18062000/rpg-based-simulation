r"""Detect stale `## Status` body text in `tickets/done/*.md` and lowercase `final_status` values
in `agent-monitoring/runs.jsonl`.

Built for TCK-20260718-STATUS-DRIFT-REPAIR: 71 files in `tickets/done/` had a body `## Status`
section reading something other than `DONE` (mostly `OPEN`/`INPROGRESS`) despite frontmatter
already correctly showing `status: historical, phase: done` — predating `implement-ticket.js`'s
current Finalize phase, which now reliably sets `## Status` to `DONE` on every close. 7 records in
`runs.jsonl` had a lowercase `final_status` (`"done"`/`"success"`) predating the current
all-uppercase status-enum convention, causing `dashboard-frontend/src/components/GanttBar.tsx`'s
`classifyFinalStatus()` (exact-match on the literal `'DONE'`) to render genuinely-successful runs
in the neutral/gray bucket instead of green. This module gives both drift classes a deterministic,
repeatable check so the fix does not silently regress.

**Extraction fix (this revision)**: the original implementation used a first-token-only regex
(`^## Status\s*\n+\s*(\S+)`) that captured just the first word after the heading. That missed
real drift the actual dashboard shows, because `src/api/agent_ops_dashboard/ingest.py` extracts
`workflow_status` via `tools/generate_registry.py::parse_body_section`, which captures the ENTIRE
section body up to the next `## ` heading — not just the first token. Two follow-up tickets
(TCK-20260718-STATUS-SUFFIX-TRIM and this one) each independently rediscovered real dashboard-
visible fragmentation that the first-token regex's own "clean" verdict had missed: a stray
leftover `INPROGRESS` line after `DONE`, and 11 legacy-format files where `DONE` bled into a
trailing `**Tier:**`/`**Type:**`/`**Priority:**` bold-text block because there was no `## Tier`
heading to stop at. This module now imports and calls `parse_body_section` directly, so it always
validates the exact same extraction the dashboard performs — eliminating this whole class of
"checker says clean, dashboard shows garbage" gap by construction rather than by patching in a
fourth regex for a fourth discovered shape.

**Known, intentional limitation**: same-line colon-suffixed `## Status: X` tickets (12 files
corpus-wide, 6 non-`DONE` as of 2026-07-18) still resolve to `""` via `parse_body_section` (its
own regex also requires a newline directly after the heading, so `: X` on the same line never
matches) and are silently skipped here, exactly as under the old regex. This is unchanged,
deliberate scope — TCK-20260718-STATUS-DRIFT-REPAIR's plan.md explicitly excluded those 6 files
(see "Colon-Suffixed Files Decision"), and TCK-20260718-STATUS-MULTILINE-FIX (this ticket) did not
revisit that exclusion. Candidate for a future, separately-scoped ticket.

Mirrors `doc_staleness_check.py`'s and `workflow_meta_conformance.py`'s shape: aggregate
`check_*()` functions returning `List[dict]` (`{"status": "PASS"|"FAIL", "evidence": "..."}`), a
`MARKER:` + `json.dumps(result)` stdout contract in `__main__`. Ships unwired — no `Makefile`
target, no `.claude/workflows/*.js` invocation added in this ticket; a future ticket decides
where/whether to call it, matching this directory's own stated precedent.
"""

import json
import sys
from pathlib import Path
from typing import List

DEFAULT_DONE_DIR = Path("tickets/done")
DEFAULT_RUNS_PATH = Path("agent-monitoring/runs.jsonl")

_TOOLS_DIR = Path(__file__).parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from generate_registry import parse_body_section, _strip_frontmatter  # noqa: E402

EPIC_TIER_VALUES = {"EPIC_SCOPED", "SCOPED"}


def check_ticket_status_drift(done_dir: Path = DEFAULT_DONE_DIR) -> List[dict]:
    """Flag `tickets/done/*.md` files whose body `## Status` value is not `DONE`.

    Extracts via `parse_body_section` — the same function `ingest.py` uses for the dashboard's
    `workflow_status` field — so a file only passes here if the dashboard would also show it as
    plain `DONE`. Skips (does not flag) three structural exemptions: an empty extraction (same-line
    colon-suffixed `## Status: X` tickets and any file with no `## Status` heading at all — both
    return `""` from `parse_body_section` and are out of this check's scope, see module docstring),
    `## Status` values in `{"EPIC_SCOPED", "SCOPED"}` (epic-tier terminal text is legitimate, not
    drift), and files whose name does not start with `TCK-` (pre-TCK-naming legacy files, out of
    scope per project precedent). All three exemptions are value-based / filename-pattern-based,
    never a hardcoded literal filename list, so a future epic closure or legacy backfill does not
    require a checker update to stay correctly exempt.
    """
    findings = []
    for path in sorted(done_dir.glob("*.md")):
        text = path.read_text(errors="ignore")
        value = parse_body_section(_strip_frontmatter(text), "Status")
        if not value:
            continue
        if value.upper() == "DONE":
            continue
        if value.upper() in EPIC_TIER_VALUES:
            continue
        if not path.name.startswith("TCK-"):
            continue
        findings.append({
            "status": "FAIL",
            "evidence": f"{path.name}: ## Status reads {value!r}, expected DONE",
        })

    if not findings:
        return [{
            "status": "PASS",
            "evidence": f"no non-DONE ## Status drift found in {done_dir} "
                        f"(excluding epic-tier, pre-TCK-naming legacy, and empty-extraction "
                        f"exemptions)",
        }]
    return findings


def check_runs_jsonl_final_status_drift(runs_path: Path = DEFAULT_RUNS_PATH) -> List[dict]:
    """Flag `runs.jsonl` records whose `final_status` value is not its own uppercase form.

    Skips (does not evaluate) any record lacking a `final_status` key — the legacy
    `status`/`started_at` schema is a different shape entirely, out of this check's scope by
    design, not a parsing failure.
    """
    findings = []
    for line in runs_path.read_text().splitlines():
        if not line:
            continue
        record = json.loads(line)
        final_status = record.get("final_status")
        if final_status is None:
            continue
        if final_status != final_status.upper():
            findings.append({
                "status": "FAIL",
                "evidence": f"run_id={record.get('run_id')!r}: final_status={final_status!r} "
                            f"is not uppercase",
            })

    if not findings:
        return [{
            "status": "PASS",
            "evidence": f"no lowercase final_status drift found in {runs_path}",
        }]
    return findings


def check_status_drift(
    done_dir: Path = DEFAULT_DONE_DIR, runs_path: Path = DEFAULT_RUNS_PATH
) -> List[dict]:
    """Aggregate entry point combining both scans' results."""
    return check_ticket_status_drift(done_dir) + check_runs_jsonl_final_status_drift(runs_path)


if __name__ == "__main__":
    done_dir_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DONE_DIR
    runs_path_arg = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_RUNS_PATH
    result = check_status_drift(done_dir_arg, runs_path_arg)
    print("MARKER:" + json.dumps(result))
    if any(r["status"] == "FAIL" for r in result):
        sys.exit(1)
