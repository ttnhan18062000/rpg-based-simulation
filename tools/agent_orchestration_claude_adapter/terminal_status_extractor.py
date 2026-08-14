"""Live terminal-status extraction from a Claude workflow `.js` source file.

Mirrors tools/gate_checks/workflow_meta_conformance.py::extract_meta_phases's read-only
`Path.read_text()` + regex technique exactly: no JS parser, no subprocess, never opens the target
file in write mode.

Terminal statuses reach `agent-monitoring/*.jsonl` through three distinct mechanisms in the live
workflow source, each with its own extraction function:
  - `literal`         — `await writeMonitoring('STRING')` call sites.
  - `verdict_derived` — `await writeMonitoring(<var>.verdict)` call sites; the value is not a
                         source string literal, so it is a fixed, documented constant here rather
                         than scraped from the REVIEW_SCHEMA/ARCH_VERIFY_SCHEMA enum text (fragile).
  - `bypass`          — values written via a raw `bash()`-embedded `record_run.py --data` JSON
                         payload that never calls `writeMonitoring()` at all (currently only
                         SCOPE_AGENT_FAILED, before `tid`/`writeMonitoring` exist yet).

`extract_all_terminal_statuses` aggregates all three and dedupes by `value` (not by call-site
count) — `FINALIZE_INCOMPLETE` has two call sites and must collapse to one entry with two recorded
`call_sites`, never double-counted as a conflict.
"""
from __future__ import annotations

import re
from pathlib import Path

_LITERAL_STATUS_RE = re.compile(r"writeMonitoring\('([^']+)'\)")
_VERDICT_DERIVED_CALL_SITE_RE = re.compile(r"writeMonitoring\(\w+\.verdict\)")
# Excludes `$` from the captured value: the same `record_run.py --data` payload shape is also
# quoted, with `"final_status":"${finalStatus}"` templated, inside writeMonitoring()'s own prompt
# text (documenting the *normal* call, not a bypass) — only a bare string literal (no `${...}`
# interpolation) is a genuine bypass value.
_BYPASS_FINAL_STATUS_RE = re.compile(r'"final_status"\s*:\s*"([^"$]+)"')

# Fixed, documented constant — not scraped from REVIEW_SCHEMA/ARCH_VERIFY_SCHEMA enum text, per
# this ticket's test_plan explicit "fixture-based, not scraping the real enum text" instruction.
# `writeMonitoring(review.verdict)` at :582 and `writeMonitoring(archVerify.verdict)` at :760 both
# draw from the same two-value verdict enum (`['APPROVED', 'NEEDS_CHANGES', 'BLOCKED']`, only
# firing when verdict != 'APPROVED').
_VERDICT_DERIVED_STATUSES: tuple[dict, ...] = (
    {"value": "NEEDS_CHANGES", "kind": "verdict_derived"},
    {"value": "BLOCKED", "kind": "verdict_derived"},
)


def extract_literal_statuses(workflow_js_path: Path) -> list[dict]:
    """Every `writeMonitoring('STRING')` call site, in source order, one dict per call site.

    Returns one entry per call site (not deduped) — `FINALIZE_INCOMPLETE`'s two call sites yield
    two separate entries here; deduping by value happens only in `extract_all_terminal_statuses`.
    """
    text = workflow_js_path.read_text(encoding="utf-8")
    entries = []
    for match in _LITERAL_STATUS_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        entries.append({"value": match.group(1), "kind": "literal", "line": line})
    return entries


def extract_verdict_derived_statuses() -> list[dict]:
    """The fixed, documented verdict-derived status vocabulary (NEEDS_CHANGES, BLOCKED).

    Does not read the workflow source — the value set is a documented constant, not scraped from
    the live enum text. Use `count_verdict_derived_call_sites` to confirm the live file still
    contains the expected number of call sites drawing from this value set.
    """
    return [dict(entry) for entry in _VERDICT_DERIVED_STATUSES]


def count_verdict_derived_call_sites(workflow_js_path: Path) -> int:
    """Count of `writeMonitoring(<var>.verdict)` call sites in the live source.

    A companion check to `extract_verdict_derived_statuses`'s fixed constant: if this count drifts
    from 2 (e.g. a future edit adds or removes a verdict-derived call site), that is a signal the
    fixed constant needs re-review — the value set itself still does not depend on parsing the
    enum text.
    """
    text = workflow_js_path.read_text(encoding="utf-8")
    return len(_VERDICT_DERIVED_CALL_SITE_RE.findall(text))


def extract_bypass_statuses(workflow_js_path: Path) -> list[dict]:
    """Terminal-status values written via a raw `bash()`-embedded `record_run.py --data` payload.

    These bypass `writeMonitoring()` entirely, so `extract_literal_statuses`'s regex cannot find
    them. Scoped to lines that reference `record_run.py`, extracting the `"final_status"` JSON key
    from the embedded payload — currently only SCOPE_AGENT_FAILED (written before `tid`/
    `writeMonitoring` exist yet, at Scope-phase failure).
    """
    text = workflow_js_path.read_text(encoding="utf-8")
    entries = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "record_run.py" not in line:
            continue
        match = _BYPASS_FINAL_STATUS_RE.search(line)
        if match:
            entries.append({"value": match.group(1), "kind": "bypass", "line": lineno})
    return entries


def extract_all_terminal_statuses(workflow_js_path: Path) -> list[dict]:
    """Aggregate literal, verdict-derived, and bypass statuses, deduped by `value`.

    Returns one entry per distinct `value`: `{"value": str, "kind": str, "call_sites": [int, ...]}`.
    `call_sites` is empty for verdict-derived entries (no source-literal call site to record).
    """
    aggregated: dict[str, dict] = {}

    for entry in extract_literal_statuses(workflow_js_path):
        bucket = aggregated.setdefault(
            entry["value"], {"value": entry["value"], "kind": "literal", "call_sites": []}
        )
        bucket["call_sites"].append(entry["line"])

    for entry in extract_bypass_statuses(workflow_js_path):
        aggregated.setdefault(
            entry["value"], {"value": entry["value"], "kind": "bypass", "call_sites": []}
        )["call_sites"].append(entry["line"])

    for entry in extract_verdict_derived_statuses():
        aggregated.setdefault(
            entry["value"], {"value": entry["value"], "kind": "verdict_derived", "call_sites": []}
        )

    return list(aggregated.values())
