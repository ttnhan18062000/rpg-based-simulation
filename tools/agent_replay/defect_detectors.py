"""M2/M3 recurring-defect-class detectors for the filtered replay eval pilot
(TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, Steps 3-4).

`replay_slice()` (tools/agent_replay/runner.py) only mirrors 4 deterministic gate branches from
`implement-ticket.js` — neither of `guardrail_enforcement_epic.md`'s two named recurring defect
classes (M2, M3) has any detection logic there. This module adds two new, separate detector
functions alongside it — it never modifies `runner.py`'s existing branch points.

**M2 — doc-update self-report gap** (`detect_m2_doc_update_gap`): real-historical signal.
Reimplements the same forward/reverse comparison
`tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage`'s reverse direction
already performs against live `git status`, but against a historical closing-commit diff instead
— the live function itself is read only as a reference, never imported or modified, so this
module stays decoupled from the live gate's own internals.

**M3 — test-scoper background-hang pattern** (`detect_m3_background_hang`): synthetic-disclosed
signal. `background_tasks` is a live-runtime-only signal
(`tools/agent-monitoring/subagent_stop_background_guard.py`'s own module docstring) never
persisted to any stored artifact for a past ticket — there is no reliable way to reconstruct a
genuine per-ticket historical instance. Per investigation.md Risks #1 option (c), this detector's
known-positive fixture is an explicitly synthetic, hand-built payload
(`tests/fixtures/agent_replay/pilot/m3_synthetic_known_positive.yaml`) — never claimed to
represent a real `tickets/done/` sample member. The live hook script is read only as a reference,
never imported or subprocessed, per the unconditional containment law
(docs/ai/replay_fixture_spec.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_DOCS_PROSE_TOKEN_RE = re.compile(r"docs/[^\s`]+")

# docs/REGISTRY.yaml is regenerated unconditionally by Finalize's own post-migration self-check
# on every ticket close (see this project's CLAUDE.md Workflow Rule) — it is never expected to be
# individually declared in a ticket's own Files Changed/Related Docs prose, so counting it as a
# "gap" would false-positive-fire on essentially every historical ticket. Excluded deliberately,
# mirroring the live check_docs_to_update_coverage's own real-world behavior (its reverse check
# reads `git status` at Verify time, before Finalize's later REGISTRY.yaml regeneration has
# happened yet, so it never sees this path as touched either).
_SELF_REPORT_EXEMPT_DOC_PATHS = frozenset({"docs/REGISTRY.yaml"})


_SECTION_RE_TEMPLATE = r"^## {heading}\s*\n(.*?)(?=^## |\Z)"


def extract_ticket_section(ticket_text: str, heading: str) -> str:
    """Return the body text under a `## {heading}` markdown heading, up to the next `## `
    heading or end of file. Returns "" if the heading is not present. Local, independent
    reimplementation of `tools/gate_checks/done_checker_static.py::_extract_section_text` — never
    imports that module, per this file's own module docstring."""
    pattern = re.compile(_SECTION_RE_TEMPLATE.format(heading=re.escape(heading)), re.MULTILINE | re.DOTALL)
    match = pattern.search(ticket_text)
    return match.group(1) if match else ""


@dataclass(frozen=True)
class M2Result:
    ticket_id: str
    fired: bool
    gap_paths: list
    evidence: str


def _prose_docs_paths(text: str) -> set:
    return {match.rstrip(".,;:)") for match in _DOCS_PROSE_TOKEN_RE.findall(text or "")}


def _path_covered(touched_path: str, declared_paths: set) -> bool:
    if touched_path in declared_paths:
        return True
    return any(
        declared.rstrip("/") == touched_path.rstrip("/")
        or touched_path.startswith(declared.rstrip("/") + "/")
        or declared.startswith(touched_path.rstrip("/") + "/")
        for declared in declared_paths
    )


def detect_m2_doc_update_gap(
    ticket_id: str,
    closing_commit_diff_docs_paths: list,
    files_changed_text: str,
    related_docs_text: str,
) -> M2Result:
    """Flags a doc-update self-report gap: a real `docs/` path shown as touched by the ticket's
    own closing commit(s) that never made it into the ticket's own resolved `## Files Changed` or
    `## Related Docs` body-section text."""
    touched = {
        p
        for p in closing_commit_diff_docs_paths
        if p.startswith("docs/") and p not in _SELF_REPORT_EXEMPT_DOC_PATHS
    }
    declared = _prose_docs_paths(files_changed_text) | _prose_docs_paths(related_docs_text)
    gap = sorted(p for p in touched if not _path_covered(p, declared))

    if gap:
        return M2Result(
            ticket_id,
            True,
            gap,
            f"docs/ path(s) touched in the closing commit but not reflected in Files Changed/"
            f"Related Docs: {gap}",
        )
    return M2Result(
        ticket_id,
        False,
        [],
        f"all {len(touched)} touched docs/ path(s) reflected in Files Changed/Related Docs",
    )


@dataclass(frozen=True)
class M3Result:
    fired: bool
    evidence: str


def detect_m3_background_hang(subagent_stop_payload: dict) -> M3Result:
    """Reimplements the live hook's own detection condition (`background_tasks` non-empty and
    `stop_hook_active` false) against a fixture payload, without importing or subprocessing that
    script."""
    stop_hook_active = bool(subagent_stop_payload.get("stop_hook_active"))
    background_tasks = subagent_stop_payload.get("background_tasks") or []
    if not isinstance(background_tasks, list):
        background_tasks = []

    if stop_hook_active:
        return M3Result(
            False,
            "stop_hook_active is true — matches the live hook's own consecutive-block-cap "
            "avoidance behavior, never fires while a prior block is still being processed",
        )
    if not background_tasks:
        return M3Result(False, "background_tasks is empty — no in-flight background work")
    return M3Result(
        True,
        f"{len(background_tasks)} background task(s) still in flight at SubagentStop — matches "
        "the live hook's own fire condition",
    )
