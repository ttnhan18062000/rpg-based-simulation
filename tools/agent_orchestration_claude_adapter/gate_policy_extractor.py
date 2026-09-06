"""Live gate-policy extraction from a Claude workflow `.js` source file.

Mirrors `terminal_status_extractor.py`'s read-only `Path.read_text()` + regex technique (no JS
parser, no subprocess, never opens the target file in write mode) but pairs matches across a
**wider, structurally-bounded** span than that module's fixed `_CONTEXT_WINDOW_CHARS` (400)
constant — this was flagged as a non-blocking open question by architecture-review for this
ticket's plan (TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST) and empirically checked against
the real live workflow source file (passed in by the caller as `workflow_js_path` — this module
never hardcodes that path itself) before writing this module (measured character distances, not
assumed):

  - `run_finalize_selfcheck` import (:1544) -> its two `writeMonitoring('FINALIZE_INCOMPLETE')`
    call sites (:1567, :1579): 1073 / 1614 chars.
  - `tag_registry` import (:411) -> `writeMonitoring('TAGS_NOT_REGISTERED')` (:459): 2300 chars.
  - `doc_staleness_check` CLI invocation (:892) -> `writeMonitoring('DOC_STALENESS_BLOCKED')`
    (:941): 2935 chars.
  - Each `verdict: { type: 'string', enum: [...] }` schema block -> its own guarding
    `if (X.verdict !== 'Y')` check: 1273-3416 chars (large agent-prompt text sits in between).

All of these exceed `_CONTEXT_WINDOW_CHARS` (400) by a wide margin — reusing it verbatim for these
pairings would either silently fail to find the paired match (enum -> if-check) or, worse,
silently pair against the wrong, more-distant match. This module therefore uses three different,
non-arbitrary pairing strategies instead of one fixed char window, each justified by what is
actually stable in the source text:

  1. **verdict-enum <-> guarding if-check**: paired *positionally* (Nth enum block with Nth
     if-check, in source order), not by proximity. Both occur exactly 4 times, in the same
     relative order, in the live file — confirmed by direct grep before writing this module. This
     sidesteps the enum<->if distance entirely (no window needed for this pairing).
  2. **if-check <-> its `writeMonitoring(...)` call**: bounded by a wider fixed window,
     `_AGENT_VERDICT_GATE_WINDOW_CHARS` (600) — comfortably above the largest measured distance
     (421 chars, the Verify/done-checker gate) with margin, still importing and citing
     `terminal_status_extractor._CONTEXT_WINDOW_CHARS` in this docstring for direct comparison
     (400 vs. 600) rather than silently picking an unexplained number.
  3. **static-check import/CLI line <-> its `writeMonitoring('LITERAL')` call**: bounded
     *structurally* by the next gate-defining line (the next `from gate_checks.X import Y` /
     `from tag_registry import Y` / `python3 tools/gate_checks/X.py` occurrence), not by a fixed
     char count. The live workflow source has 13 such import/CLI lines total, but only 6 of them
     actually gate a phase (fail to a `writeMonitoring('LITERAL')` call before the next such line);
     the other 7 are informational-only (feed an agent's own judgment, or write only a non-blocking
     advisory `pushEvent`, never `writeMonitoring`) — e.g. `architecture_reviewer_static.
     run_architecture_checks` (:966) feeds Architecture-Verify's *agent_verdict* gate, it is not
     itself a second, redundant static_check gate for that same phase. A fixed char window large
     enough for the real gates (e.g. >=2935, the doc-staleness case) would be large enough to also
     wrongly capture a later, unrelated phase's `writeMonitoring` call for one of the 7
     informational-only lines (confirmed: `parity_updater_static.cross_reference_touched` (:1303)
     sits close enough to Verify's `DOD_BLOCKED` literal (:1470) that a >=170-char window bridges
     them, well inside any window wide enough to also reach doc-staleness's 2935-char case) — the
     structural next-import-line bound avoids this because an informational-only import's own
     window (up to the *next* import line) generally contains no literal `writeMonitoring` call at
     all, so it naturally excludes itself without an explicit allowlist. The next-import-line bound
     alone is still not sufficient, though: Scope's phase text has 3 independent literal
     `writeMonitoring` call sites (CONFLICTS_DETECTED, TAGS_NOT_REGISTERED, EPIC_SCOPED) with no
     import-line boundary between them at all — a naive "nearest literal call in the bounded
     window" would wrongly pair the `tag_registry` import with the *closer* but unrelated
     CONFLICTS_DETECTED (an agent_result_field gate's own status) instead of its real pairing,
     TAGS_NOT_REGISTERED (confirmed empirically before this design was finalized). See
     `_static_check_exclusion_values` for the fix: literal values already known to belong to
     agent_result_field or agent_verdict gates are excluded from static_check's own candidate
     search, so the search skips past them to the real match.

Phase attribution for every extracted gate uses the nearest **preceding** `pushEvent('<Phase>',
...)` call's literal phase argument (relative to the gate's own `writeMonitoring` call), not the
nearest preceding `phase('<Phase>')` block marker the sibling `extract_meta_phases` scans for. This
is a deliberate, evidence-driven deviation from a naive "nearest phase() marker" design: the
doc-staleness gate's `pushEvent`/`writeMonitoring` calls (source lines 927-941) sit textually
*after* `phase('Document-Update')` (:805) but *before* `phase('Architecture-Verify')` (:959) — a
nearest-preceding-`phase()`-marker approach would misattribute this gate to Document-Update,
contradicting its own inline `pushEvent('Implement', ...)` call at :927 and the `gate_policy:
Implement` phase this ticket's `agent-orchestration/gate-policy.yaml` records for it (matching
CLAUDE.md's own documented workflow structure: Document-Update happens between Implement and its
own doc-staleness gate, but the gate's outcome folds back into the *Implement* phase event, not a
new Document-Update event — see the source file's own comment at lines 920-922). The
nearest-preceding-`pushEvent`-literal approach gets this right automatically (and also correctly
resolves NEEDS_HUMAN_INPUT to Plan, not Investigate, matching `agent-orchestration/gate-policy.yaml`'s
own corrective note) because every gate's failure branch always emits its own `pushEvent('<Phase>',
...)` call naming its real phase immediately before (or in place of) its `writeMonitoring` call —
confirmed true for all 13 gate/status call sites in the live file.
"""
from __future__ import annotations

import re
from pathlib import Path

from tools.agent_orchestration_claude_adapter.terminal_status_extractor import (
    _CONTEXT_WINDOW_CHARS as _TERMINAL_STATUS_CONTEXT_WINDOW_CHARS,  # noqa: F401 -- cited in docstring only, not used as a window here (see module docstring for why).
)

_LITERAL_WRITE_MONITORING_RE = re.compile(r"writeMonitoring\('([^']+)'\)")
_VERDICT_PASSTHROUGH_WRITE_MONITORING_RE = re.compile(r"writeMonitoring\(\w+\.verdict\)")
_VERDICT_ENUM_RE = re.compile(r"verdict:\s*\{\s*type:\s*'string',\s*enum:\s*\[([^\]]+)\]\s*\}")
_VERDICT_IF_RE = re.compile(r"if\s*\(\s*\w+\.verdict\s*!==\s*'(\w+)'\s*\)")
_PUSH_EVENT_PHASE_RE = re.compile(r"pushEvent\(\s*'([A-Za-z-]+)'")
_IMPORT_LINE_RE = re.compile(r"from (tag_registry|gate_checks\.\w+) import (\w+)")
_CLI_LINE_RE = re.compile(r"python3 tools/gate_checks/(\w+)\.py")

# Empirically verified against the real file (see module docstring): the largest measured
# if-check -> writeMonitoring distance across the 4 agent_verdict gates is 421 chars
# (Verify/done-checker). 600 gives comfortable margin without reaching into an unrelated gate.
_AGENT_VERDICT_GATE_WINDOW_CHARS = 600

# A CLI invocation line does not name its own function the way an `import` line does — fixed,
# documented constant, not scraped, mirroring terminal_status_extractor.py's own
# `_VERDICT_DERIVED_STATUSES` precedent for "structurally un-scrapable, so state it directly."
_CLI_FUNCTION_NAMES = {"doc_staleness_check": "check_doc_staleness"}

# Fixed, documented constant — these are structural truthiness checks on agent-schema fields
# (a plain non-verdict boolean/array field), not a single regex-extractable literal-plus-enum
# shape the way agent_verdict gates are. See `count_agent_result_field_call_sites` for the
# companion sanity check that the live source still contains the literal comparisons these two
# entries describe.
_AGENT_RESULT_FIELD_GATES: tuple[dict, ...] = (
    {
        "phase": "Scope",
        "gate_type": "agent_result_field",
        "result_field": "conflicts",
        "pass_value": [],
        "on_fail_status": ["CONFLICTS_DETECTED"],
    },
    {
        "phase": "Test",
        "gate_type": "agent_result_field",
        "result_field": "passed",
        "pass_value": True,
        "on_fail_status": ["TESTS_FAILED"],
    },
)
_CONFLICTS_LITERAL_RE = re.compile(r"ticketInfo\.conflicts\.length > 0")
_TESTS_FAILED_LITERAL_RE = re.compile(r"!testResult\.passed")


def _nearest_preceding_phase(text: str, offset: int) -> str | None:
    """The literal phase argument of the nearest `pushEvent('<Phase>', ...)` call strictly before
    `offset`. See module docstring for why this, not the nearest `phase('<Phase>')` block marker,
    is the correct phase-attribution anchor for gate_policy."""
    phase = None
    for match in _PUSH_EVENT_PHASE_RE.finditer(text):
        if match.start() >= offset:
            break
        phase = match.group(1)
    return phase


def extract_agent_verdict_gates(workflow_js_path: Path) -> list[dict]:
    """Every `verdict: { type: 'string', enum: [...] }` schema block paired with its guarding
    `if (X.verdict !== 'Y')` check (positionally, in source order — see module docstring) and the
    resulting `writeMonitoring(...)` call: either a passthrough (`writeMonitoring(X.verdict)`,
    `on_fail_status` = every non-pass enum value) or a fixed literal
    (`writeMonitoring('LITERAL')`, `on_fail_status` = `[LITERAL]`).

    4 call sites exist in the live file (Review, Architecture-Verify, Security-Review, Verify/
    done-checker) — this function does not assume a fixed count of 3.
    """
    text = workflow_js_path.read_text(encoding="utf-8")
    enum_matches = list(_VERDICT_ENUM_RE.finditer(text))
    if_matches = list(_VERDICT_IF_RE.finditer(text))

    gates = []
    for enum_match, if_match in zip(enum_matches, if_matches):
        enum_values = [v.strip().strip("'\"") for v in enum_match.group(1).split(",")]
        pass_value = if_match.group(1)

        window_start = if_match.end()
        window = text[window_start:window_start + _AGENT_VERDICT_GATE_WINDOW_CHARS]
        passthrough_match = _VERDICT_PASSTHROUGH_WRITE_MONITORING_RE.search(window)
        literal_match = _LITERAL_WRITE_MONITORING_RE.search(window)

        if passthrough_match and (literal_match is None or passthrough_match.start() < literal_match.start()):
            on_fail_status = [value for value in enum_values if value != pass_value]
            write_monitoring_offset = window_start + passthrough_match.start()
        elif literal_match:
            on_fail_status = [literal_match.group(1)]
            write_monitoring_offset = window_start + literal_match.start()
        else:
            continue

        gates.append({
            "phase": _nearest_preceding_phase(text, write_monitoring_offset),
            "gate_type": "agent_verdict",
            "verdict_enum": enum_values,
            "pass_value": pass_value,
            "on_fail_status": on_fail_status,
        })
    return gates


# Literal `writeMonitoring('...')` values that are known, by construction, to belong to a
# *different* gate_type — never a candidate match for a static_check pairing. `EPIC_SCOPED` is a
# tier-routing exit (excluded_outcomes, not a gate at all) and `DONE` is the success status, never
# a failure. The agent_result_field values (CONFLICTS_DETECTED, TESTS_FAILED) are added
# dynamically from `_AGENT_RESULT_FIELD_GATES` below, and the agent_verdict values (SECURITY_BLOCKED,
# DOD_BLOCKED, and any future literal-collapsed verdict gate) are added dynamically from
# `extract_agent_verdict_gates`'s own output — see `_static_check_exclusion_values` docstring for
# why this must be derived, not a second hardcoded copy of those two functions' own values.
_NON_GATE_LITERAL_STATUS_VALUES = frozenset({"EPIC_SCOPED", "DONE"})


def _static_check_exclusion_values(workflow_js_path: Path) -> frozenset[str]:
    """Literal status values that must never be mistaken for a static_check gate's own result.

    Scope's phase text has 3 independent literal `writeMonitoring` call sites
    (CONFLICTS_DETECTED, TAGS_NOT_REGISTERED, EPIC_SCOPED) with no `import`-line boundary between
    them — a naive "nearest following literal writeMonitoring after this import" search would
    wrongly pair the `tag_registry` import with CONFLICTS_DETECTED (the *closer* but unrelated
    agent_result_field gate's own status) instead of its real pairing, TAGS_NOT_REGISTERED.
    Excluding every literal value already known to belong to agent_result_field or agent_verdict
    gates from static_check's own candidate search fixes this without needing a fragile,
    JS-variable-usage-aware pairing mechanism.
    """
    agent_verdict_literal_values = {
        value
        for gate in extract_agent_verdict_gates(workflow_js_path)
        for value in gate["on_fail_status"]
        if len(gate["on_fail_status"]) == 1  # the literal (non-passthrough) shape only
    }
    agent_result_field_values = {
        value for gate in _AGENT_RESULT_FIELD_GATES for value in gate["on_fail_status"]
    }
    return frozenset(_NON_GATE_LITERAL_STATUS_VALUES | agent_verdict_literal_values | agent_result_field_values)


def extract_static_check_gates(workflow_js_path: Path) -> list[dict]:
    """Every `from gate_checks.<module> import <function>` / `from tag_registry import <function>`
    line and every `python3 tools/gate_checks/<module>.py` CLI invocation that actually gates a
    phase — i.e. is followed, before the next such line, by a literal `writeMonitoring('STRING')`
    call whose value does not already belong to a different gate_type (see
    `_static_check_exclusion_values`). A line with no such call in its bounded span is
    informational-only (feeds an agent's own judgment or an advisory-only `pushEvent`) and is
    silently excluded, not an error. See module docstring for why the structural next-import-line
    bound (not a fixed char window) is required here.
    """
    text = workflow_js_path.read_text(encoding="utf-8")
    excluded_values = _static_check_exclusion_values(workflow_js_path)

    lines: list[dict] = []
    for match in _IMPORT_LINE_RE.finditer(text):
        lines.append({
            "offset": match.start(),
            "invocation": "import",
            "check_module": match.group(1),
            "check_function": match.group(2),
        })
    for match in _CLI_LINE_RE.finditer(text):
        module = match.group(1)
        function = _CLI_FUNCTION_NAMES.get(module)
        if function is None:
            continue
        lines.append({
            "offset": match.start(),
            "invocation": "cli",
            "check_module": f"gate_checks.{module}",
            "check_function": function,
        })
    lines.sort(key=lambda entry: entry["offset"])

    gates = []
    for idx, entry in enumerate(lines):
        window_end = lines[idx + 1]["offset"] if idx + 1 < len(lines) else len(text)
        window = text[entry["offset"]:window_end]

        literal_match = None
        for candidate in _LITERAL_WRITE_MONITORING_RE.finditer(window):
            if candidate.group(1) not in excluded_values:
                literal_match = candidate
                break
        if literal_match is None:
            continue

        write_monitoring_offset = entry["offset"] + literal_match.start()
        gates.append({
            "phase": _nearest_preceding_phase(text, write_monitoring_offset),
            "gate_type": "static_check",
            "invocation": entry["invocation"],
            "check_module": entry["check_module"],
            "check_function": entry["check_function"],
            "on_fail_status": [literal_match.group(1)],
        })
    return gates


def extract_agent_result_field_gates() -> list[dict]:
    """The fixed, documented agent_result_field gate vocabulary (Scope's `conflicts`, Test's
    `passed`). Does not read the workflow source — use `count_agent_result_field_call_sites` to
    confirm the live source still contains the literal comparisons this constant describes."""
    return [dict(entry) for entry in _AGENT_RESULT_FIELD_GATES]


def count_agent_result_field_call_sites(workflow_js_path: Path) -> dict[str, int]:
    """Count of the literal truthiness comparisons `extract_agent_result_field_gates`'s fixed
    constant describes. A count of 0 for either is a signal the fixed constant needs re-review
    (mirrors `terminal_status_extractor.count_verdict_derived_call_sites`'s companion-check role)."""
    text = workflow_js_path.read_text(encoding="utf-8")
    return {
        "conflicts": len(_CONFLICTS_LITERAL_RE.findall(text)),
        "passed": len(_TESTS_FAILED_LITERAL_RE.findall(text)),
    }


def extract_gate_policy(workflow_js_path: Path) -> list[dict]:
    """Aggregate all three gate_type extractors into one flat list of gate dicts."""
    return (
        extract_agent_verdict_gates(workflow_js_path)
        + extract_static_check_gates(workflow_js_path)
        + extract_agent_result_field_gates()
    )
