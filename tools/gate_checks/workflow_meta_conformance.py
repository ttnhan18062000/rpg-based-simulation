"""Cross-reference a workflow's declared `meta.phases` against a run's actual events.jsonl rows.

Built for TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK: every `.claude/workflows/*.js` file
exports a declarative `meta.phases` array describing every phase the workflow is supposed to
execute, and every phase already pushes an event to `agent-monitoring/events.jsonl` with a `phase`
field — but the two are never cross-checked today, so a phase the narrating LLM silently skips
entirely (not just under-instrumented, but never invoked at all) goes undetected. This module
gives that class of failure a deterministic, run_id-keyed verifier.

Mirrors `done_checker_static.py::run_finalize_selfcheck`'s shape (a single aggregate function
returning a list of dicts) rather than `parity_updater_static.py`'s two-call
`expected_subsystems_for_files`/`cross_reference_touched` split — there is no agent-prompt
injection point this check needs to feed (see plan.md's Resolved Open Questions), so the two-call
causality fix that split exists for does not apply here.

A declared phase is flagged FAIL only when it has zero events of ANY status for that run_id,
including `skipped`. Every confirmed-legitimate conditional phase in this codebase
(`Security-Review`, `Link`) is either genuinely absent (not run at all) or, for hotfix-tier
skips (Investigate/Plan/Review/Architecture-Verify), still emits an explicit `skipped` event —
so this single rule distinguishes "legitimately conditional" from "silently vanished" without a
per-workflow allowlist of conditional phase names (see plan.md Resolved Open Question 2).

This ticket ships the verifier and its tests only — it is not wired into any workflow's Finalize
phase. It is built to the same `MARKER:`-prefixed JSON CLI contract every other `gate_checks`
script uses, ready for a future ticket to wire in without an interface change.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

_GATE_CHECKS_DIR = Path(__file__).resolve().parent
_TOOLS_DIR = _GATE_CHECKS_DIR.parent
_AGENT_MONITORING_DIR = _TOOLS_DIR / "agent-monitoring"
for _dir in (str(_TOOLS_DIR), str(_GATE_CHECKS_DIR), str(_AGENT_MONITORING_DIR)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

from done_checker_static import _jsonl_rows_for_run_id  # noqa: E402
from vocabulary import infer_workflow  # noqa: E402

DEFAULT_WORKFLOWS_DIR = Path(".claude/workflows")
DEFAULT_EVENTS_PATH = Path("agent-monitoring/events.jsonl")

_PHASES_BLOCK_START_RE = re.compile(r"phases:\s*\[")
_TITLE_RE = re.compile(r"title:\s*'([^']+)'")


def extract_meta_phases(workflow_js_path: Path) -> List[str]:
    """Return the declared `title` values from a workflow file's `meta.phases` array, in order.

    Locates the `phases: [` ... matching `]` block via a bracket-depth scan (not a general JS
    parser — confirmed via investigation that the block never nests further in any of the three
    in-scope workflow files) and extracts every single-quoted `title` within it. Returns `[]`
    (never raises) if no `phases: [` block is found.
    """
    text = workflow_js_path.read_text(encoding="utf-8")
    start_match = _PHASES_BLOCK_START_RE.search(text)
    if not start_match:
        return []

    open_bracket_index = start_match.end() - 1
    depth = 0
    end_index = None
    for i in range(open_bracket_index, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                end_index = i
                break
    if end_index is None:
        return []

    block = text[open_bracket_index:end_index + 1]
    return _TITLE_RE.findall(block)


def resolve_workflow_source_path(
    workflow_name: Optional[str], workflows_dir: Path = DEFAULT_WORKFLOWS_DIR
) -> Optional[Path]:
    """Return `.claude/workflows/{workflow_name}.js` if it exists, else `None`.

    Reuses `vocabulary.py::infer_workflow` for the `run_id` -> `workflow_name` step (callers pass
    its result in here) rather than this module deriving a second, possibly-inconsistent mapping.
    """
    if workflow_name is None:
        return None
    path = workflows_dir / f"{workflow_name}.js"
    return path if path.exists() else None


def collect_run_event_statuses(
    run_id: str, events_path: Path = DEFAULT_EVENTS_PATH
) -> Dict[str, Set[str]]:
    """Return {phase: {status, ...}} for every event row matching `run_id`.

    Reuses `done_checker_static.py::_jsonl_rows_for_run_id` rather than reimplementing JSONL-by-
    run_id filtering. Returns `{}` (never raises) when `run_id` has zero rows in `events_path`.
    """
    statuses: Dict[str, Set[str]] = {}
    for row in _jsonl_rows_for_run_id(events_path, run_id):
        phase = row.get("phase")
        if phase is None:
            continue
        statuses.setdefault(phase, set()).add(row.get("status"))
    return statuses


def check_workflow_meta_conformance(
    run_id: str,
    workflows_dir: Path = DEFAULT_WORKFLOWS_DIR,
    events_path: Path = DEFAULT_EVENTS_PATH,
) -> List[dict]:
    """Aggregate cross-reference: which of this run's workflow's declared phases have zero events.

    Single aggregate entry point (mirrors `run_finalize_selfcheck`'s one-function, list-of-dicts
    shape). A phase is `"FAIL"` only when it has zero events of ANY status (including `skipped`)
    for this run_id — a phase with only `skipped`-status events still counts as `"PASS"`, since it
    has events; it is the declared-phase-with-literally-zero-events that is the finding.
    """
    workflow_name = infer_workflow(run_id)
    if workflow_name is None:
        return [{
            "phase": None,
            "status": "NA",
            "evidence": f"could not infer workflow for run_id {run_id!r}",
        }]

    source_path = resolve_workflow_source_path(workflow_name, workflows_dir)
    if source_path is None:
        return [{
            "phase": None,
            "status": "NA",
            "evidence": f"no workflow source file found for workflow {workflow_name!r} "
                        f"(expected under {workflows_dir})",
        }]

    declared_phases = extract_meta_phases(source_path)
    event_statuses = collect_run_event_statuses(run_id, events_path)

    results = []
    for phase in declared_phases:
        statuses = event_statuses.get(phase)
        if not statuses:
            results.append({
                "phase": phase,
                "status": "FAIL",
                "evidence": f"declared in {source_path}'s meta.phases but zero events found "
                            f"for run_id {run_id!r}",
            })
        else:
            results.append({
                "phase": phase,
                "status": "PASS",
                "evidence": f"{len(statuses)} distinct status value(s) recorded: {sorted(statuses)}",
            })
    return results


if __name__ == "__main__":
    result = check_workflow_meta_conformance(sys.argv[1])
    print("MARKER:" + json.dumps(result))
