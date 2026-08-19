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

**Colon-suffix fix (TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP)**: same-line colon-suffixed
`## Status: X` tickets used to resolve to `""` via `parse_body_section` (its regex requires a
newline directly after the heading, so `: X` on the same line never matched) and were silently
skipped — a gap this module's own docstring had documented since TCK-20260718-STATUS-DRIFT-REPAIR
(12 files corpus-wide, 6 non-`DONE`, as of 2026-07-18) without a follow-up ticket ever landing.
`_extract_status_value` now falls back to a local `## Status: X` regex when `parse_body_section`
returns empty, so this format is detected without changing `parse_body_section` itself (other
callers — `ticket_field_values.py`, `ticket_stats_report.py`, `generate_registry.py`,
`src/api/agent_ops_dashboard/ingest.py` — all rely on its newline-separated-only behavior for
other fields, and the ticket's Out of Scope explicitly excluded touching that shared function
beyond this module's own extraction). Re-measured live corpus at fix time: still 12 files / 6
non-`DONE` — all 6 were legacy tickets with frontmatter already reading `status: historical,
phase: done` (predating the current Finalize phase, same root cause as the original
STATUS-DRIFT-REPAIR corpus) whose body `## Status: INPROGRESS` line was simply never updated;
fixed to `## Status: DONE` in this same ticket, matching the tool's established
detect-and-fix-real-drift precedent from its two prior rounds.

Mirrors `doc_staleness_check.py`'s and `workflow_meta_conformance.py`'s shape: aggregate
`check_*()` functions returning `List[dict]` (`{"status": "PASS"|"FAIL", "evidence": "..."}`), a
`MARKER:` + `json.dumps(result)` stdout contract in `__main__`. Ships unwired — no `Makefile`
target, no `.claude/workflows/*.js` invocation added in this ticket; a future ticket decides
where/whether to call it, matching this directory's own stated precedent.
"""

import json
import re
import sys
from pathlib import Path
from typing import List

DEFAULT_DONE_DIR = Path("tickets/done")
DEFAULT_RUNS_PATH = Path("agent-monitoring/runs.jsonl")

_TOOLS_DIR = Path(__file__).parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from generate_registry import parse_body_section, _strip_frontmatter  # noqa: E402

# Local fallback for the same-line colon-suffixed `## Status: X` shape `parse_body_section` does
# not match (see module docstring). Deliberately narrow: only the heading line's own value, not
# the multi-line "capture until next '## ' heading" semantics `parse_body_section` uses for the
# newline-separated shape — the colon-suffixed corpus only ever puts the value on the heading line
# itself, and any lines below it are prose/other fields, not part of the status value.
_COLON_SUFFIX_STATUS_RE = re.compile(r"^## Status\s*:\s*(.+?)\s*$", re.MULTILINE)


def _extract_status_value(body: str) -> str:
    """Extract the `## Status` value, falling back to same-line colon-suffixed extraction.

    Tries `parse_body_section` first (the same extraction the dashboard's `ingest.py` uses) and
    only falls back to `_COLON_SUFFIX_STATUS_RE` when that returns `""` — so newline-separated
    files are unaffected and always resolve exactly as before.
    """
    value = parse_body_section(body, "Status")
    if value:
        return value
    match = _COLON_SUFFIX_STATUS_RE.search(body)
    if match:
        return match.group(1).strip()
    return ""


# Tightened from {"EPIC_SCOPED", "SCOPED"} by TCK-20260718-STATUS-FACET-CANONICAL:
# TCK-20260718-STATUS-MULTILINE-FIX normalized the corpus's one remaining bare "SCOPED" ticket to
# "EPIC_SCOPED" (matching its 6 siblings), and the dashboard's own WORKFLOW_STATUS_VALUES canonical
# list (src/api/agent_ops_dashboard/ingest.py) now defines EPIC_SCOPED as the sole epic-tier
# terminal value. Keeping this checker's exemption looser than the canonical set it's meant to
# validate against would let a future bare "SCOPED" ticket silently pass here while never being a
# selectable dashboard filter value — this checker should reject exactly what the dashboard
# wouldn't recognize as canonical, not more.
EPIC_TIER_VALUES = {"EPIC_SCOPED"}


def check_ticket_status_drift(done_dir: Path = DEFAULT_DONE_DIR) -> List[dict]:
    """Flag `tickets/done/*.md` files whose body `## Status` value is not `DONE`.

    Extracts via `_extract_status_value`, which tries `parse_body_section` first — the same
    function `ingest.py` uses for the dashboard's `workflow_status` field — then falls back to a
    local same-line colon-suffixed `## Status: X` regex (see module docstring) so a file only
    passes here if the dashboard would also show it as plain `DONE`, for either heading shape.
    Skips (does not flag) three structural exemptions: an empty extraction (no `## Status` heading
    at all — the only remaining case that returns `""`), `## Status` values in `EPIC_TIER_VALUES`
    (`{"EPIC_SCOPED"}` — the sole canonical epic-tier terminal value; legitimate, not drift), and
    files whose name does not start with `TCK-` (pre-TCK-naming legacy files, out of scope per
    project precedent). All three exemptions are value-based / filename-pattern-based, never a
    hardcoded literal filename list, so a future epic closure or legacy backfill does not require a
    checker update to stay correctly exempt.
    """
    findings = []
    for path in sorted(done_dir.glob("*.md")):
        text = path.read_text(errors="ignore")
        value = _extract_status_value(_strip_frontmatter(text))
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
