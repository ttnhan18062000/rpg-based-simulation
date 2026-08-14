---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK
artifact_type: plan
tags: [ai, agent-monitoring, determinism]
---

# Implementation Plan — TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK

## Summary

Add `tools/gate_checks/workflow_meta_conformance.py`, a new standalone static-analysis tool that,
given a `run_id`, resolves the owning `.claude/workflows/*.js` file, extracts its declared
`meta.phases` title list via lightweight regex (not a JS parser), collects the set of phases that
actually have at least one event (of any status, including `skipped`) in that run's
`agent-monitoring/events.jsonl` slice, and returns a `PASS`/`FAIL`-per-phase list flagging any
declared phase with literally zero matching events. The aggregate function is a single-call shape
(mirroring `done_checker_static.py::run_finalize_selfcheck`), not the two-call
`expected_subsystems_for_files`/`cross_reference_touched` split, because there is no agent-prompt
injection point this check needs to feed (investigation Risk #4). The tool reuses
`tools/agent-monitoring/vocabulary.py::infer_workflow` for `run_id` → workflow-name mapping and does
not duplicate its `WORKFLOW_PHASES` knowledge. This ticket ships the verifier and its test suite
only — it does not wire the check into `implement-ticket.js` or any other workflow's Finalize phase,
and it does not fix `implement-epic.js`'s own long-standing Discover/Report event-emission gap that
the generalized parser will correctly surface as a real finding when pointed at an `implement-epic`
run.

## Resolved Open Questions (decided here, not left open)

**1. Advisory vs. hard block — DECIDED: advisory only, no blocking status anywhere in this tool's
output.** The aggregate function's return shape uses `PASS`/`FAIL` per phase (matching the
`run_finalize_selfcheck`/`cross_reference_touched` precedent's field naming) but this ticket does
not wire the result into any gate that can change a workflow's terminal `status`. Reasoning
(from investigation): a missing-phase-event finding is discovered only after that phase's window has
already closed — there is no in-workflow retry path that re-executes one named earlier phase — so a
hard block would strand a ticket in `BLOCKED` with no remedy, the exact "silently reversing the Hard
Rule" failure mode architecture review already rejected once for `check_monitoring_write_recorded`'s
original design (`stored_artifacts/TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING/plan.md`, Design
Decision 2). This decision only shapes the tool's internal semantics in this ticket (see Resolved
Open Question 3 below on why wiring itself is deferred).

**2. Conditional-phase handling — DECIDED: option (b), "zero events of ANY status including
`skipped`."** No per-workflow allowlist of conditional phase names (`Security-Review`, `Link`) is
built. Every confirmed-legitimate skip in this codebase (hotfix tier's
Investigate/Plan/Review/Architecture-Verify) already emits an explicit `pushEvent(..., 'skipped',
...)` — only genuinely-conditional phases (`Security-Review`, `Link`) and genuinely-vanished phases
(`implement-epic.js`'s `Discover`/`Report`) have zero rows of any status. This rule requires no
per-phase maintenance and generalizes to any future conditional phase without code changes —
directly avoids the "hardcoded `if phase == 'Security-Review'`" anti-drift hazard the investigation
flags.

**3. Scope of `implement-epic.js` — DECIDED: parser and cross-reference function are built generic
enough to correctly parse and check `implement-epic.js` (this is required anyway, since
`test_parses_meta_phases_from_implement_epic_js` is a mandatory test_plan item and a parser that only
works for one file's exact formatting would fail that test). The tool will therefore correctly
report `Discover`/`Report` as `FAIL` findings for any real `implement-epic`/`EPIC-*`/`FOLDER-*`
run_id. This ticket does NOT fix `implement-epic.js`'s own hardcoded `phase: 'Implement'`
event-emission bug (lines 221-227) that causes this — that is a workflow-authoring bug fix, a
different kind of change (editing a live orchestrator's event-emission logic) than "build a
verifier," and is not listed anywhere in this ticket's Scope bullets. Flag it as a candidate
follow-up ticket (e.g. `TCK-yyyymmdd-FIX-IMPLEMENT-EPIC-PHASE-EVENTS`) rather than absorbing it here.

**Additional scope decision surfaced during planning (not one of the 3 flagged questions, but
required to make Step ordering unambiguous): wiring this check into `implement-ticket.js`'s Finalize
phase is explicitly OUT of scope for this ticket.** The ticket's own Scope section lists only "Add
`tools/gate_checks/workflow_meta_conformance.py`" and lists `.claude/workflows/*.js` in Related Code
Areas solely as "source of the `meta.phases` declarative array" (a read source), never as a file this
ticket edits. Editing `implement-ticket.js` to add a new call site (per the
`check_monitoring_write_recorded` wiring precedent) is a distinct, separately-scoped change to a
live, high-stakes orchestrator file. Per test_plan.md's own conditional framing ("If Plan chooses NOT
to wire this into `implement-ticket.js` in this ticket... test #9 should be dropped from this list
entirely"), test #9 (`test_finalize_phase_writes_advisory_warning_never_blocks_status`) is dropped
from this plan's step list. The tool ships as a standalone, manually/future-invokable script with a
`MARKER:`-prefixed JSON CLI contract identical in shape to every other `gate_checks` script, ready to
be wired in by a future ticket without any interface change.

## Steps

### Step 1 — `meta.phases` regex/AST-lite parser
**Files:** `tools/gate_checks/workflow_meta_conformance.py` (new)
**Change:** Add `extract_meta_phases(workflow_js_path: Path) -> List[str]`. Read the file text,
locate the `phases: [` ... matching `]` block (simple bracket-depth scan, not a general JS
parser — the block never nests further per investigation confirmation), and within it apply
`re.findall(r"title:\s*'([^']+)'", block_text)` to return titles in declared order. Do not attempt
to parse `detail` — only `title` is needed. Function must not raise on a missing `phases: [` block;
return `[]` in that case (feeds Step 2's not-crash requirement).
**Do NOT touch:** `.claude/workflows/implement-ticket.js`, `create-tickets.js`, `implement-epic.js`
(read-only sources — parse, never edit). Do not add a `node`/JS-runtime subprocess dependency.
**Verify:** `test_parses_meta_phases_from_implement_ticket_js` (11 titles, declared order, run
against the real live file, not a fixture copy), `test_parses_meta_phases_from_create_tickets_js` (5
titles), `test_parses_meta_phases_from_implement_epic_js` (3 titles: Discover, Implement, Report).

### Step 2 — Workflow-name → source-file resolution, reusing `vocabulary.py`
**Files:** `tools/gate_checks/workflow_meta_conformance.py`
**Change:** Add `resolve_workflow_source_path(workflow_name: str) -> Optional[Path]` using the
confirmed convention `Path(".claude/workflows") / f"{workflow_name}.js"`, returning `None` (not
raising) if the file doesn't exist. Import `infer_workflow` from
`tools/agent-monitoring/vocabulary.py` (add its directory to `sys.path` the same way
`done_checker_static.py` / other `gate_checks` modules already do — check the existing import idiom
in `done_checker_static.py` and mirror it exactly) to map a `run_id` to a workflow name. Do not
define a second `run_id`-prefix-to-workflow-name mapping and do not copy `WORKFLOW_PHASES` into this
module.
**Do NOT touch:** `tools/agent-monitoring/vocabulary.py` (import only, no edits). Do not build a
registry/lookup file — the direct-convention path is confirmed to hold for all 3 in-scope workflow
files.
**Verify:** `test_unresolvable_workflow_source_file_does_not_crash` (unknown/future workflow name ->
explicit non-crashing `None`/labeled-result, never an exception).
`test_reuses_vocabulary_infer_workflow_not_a_reimplementation` (architecture guard: module source
contains an import from `vocabulary.py`; module namespace defines no second `WORKFLOW_PHASES`-shaped
dict).

### Step 3 — Per-run event-phase collection
**Files:** `tools/gate_checks/workflow_meta_conformance.py`
**Change:** Add `collect_run_event_statuses(run_id: str, events_path: Path = DEFAULT_EVENTS_PATH) ->
Dict[str, Set[str]]` mapping each `phase` value seen for that `run_id` to the set of `status` values
recorded for it (e.g. `{"Parity": {"skipped"}, "Scope": {"ok"}}`). Reuse
`done_checker_static.py`'s existing `_jsonl_rows_for_run_id` helper (import it directly — it is a
pure filter function with no side effects) rather than re-implementing JSONL-by-run_id filtering.
Must return `{}` (not raise) when `run_id` has zero rows in `events.jsonl` at all (e.g. a typo, or a
run that crashed before `writeMonitoring` ran).
**Do NOT touch:** `tools/gate_checks/done_checker_static.py` (import only, no edits — do not move or
rename `_jsonl_rows_for_run_id`). Do not touch `agent-monitoring/events.jsonl` itself (read-only
data source).
**Verify:** `test_unknown_run_id_returns_empty_or_na_not_a_crash` (zero-row `run_id` produces an
explicit "no events found" result the caller can distinguish from "all phases present," mirroring
`check_monitoring_write_recorded`'s `("FAIL", "No row with run_id == ...")` shape).

### Step 4 — Core aggregate cross-reference function
**Files:** `tools/gate_checks/workflow_meta_conformance.py`
**Change:** Add `check_workflow_meta_conformance(run_id: str) -> List[dict]`, the single aggregate
entry point (mirrors `run_finalize_selfcheck`'s one-function, list-of-dicts shape — not the two-call
`parity_updater_static.py` split, per Resolved Open Question 4-in-investigation / no agent-prompt
injection need). Logic: `workflow_name = infer_workflow(run_id)` -> if `None`, return a single
labeled non-crashing result (e.g. `[{"phase": None, "status": "NA", "evidence": "could not infer
workflow for run_id"}]`); resolve source path via Step 2 -> if unresolvable, similar single labeled
result; `declared_phases = extract_meta_phases(path)` (Step 1); `event_statuses =
collect_run_event_statuses(run_id)` (Step 3); for each declared phase, status is `"FAIL"` if
`event_statuses.get(phase)` is empty/missing (**zero events of ANY status, including `skipped`** —
the Resolved Open Question 2 rule, no per-phase allowlist), else `"PASS"` — a phase with only
`skipped`-status events still counts as `"PASS"` (it has events; it's the declared-phase-with-zero
that's the finding). Each dict carries `{"phase", "status", "evidence"}` matching the existing
`gate_checks` dict shape convention.
**Do NOT touch:** Do not add a `workflow_name`-keyed conditional-phase allowlist (explicitly rejected
in Resolved Open Question 2). Do not change the function's return value based on advisory-vs-blocking
severity — severity is a caller-side interpretation, not encoded as a different status string here.
**Verify:** `test_flags_declared_phase_with_zero_events` (synthetic fixture, a 3-phase declared
workflow with one phase's events fully absent -> that phase returns `"FAIL"` with non-empty
evidence). `test_does_not_flag_a_phase_with_only_skipped_status_events` (a phase with only
`status=="skipped"` events -> `"PASS"`, not flagged).

### Step 5 — Real-world false-positive guard (conditional-phase rule validated against live data)
**Files:** `tests/tools/test_workflow_meta_conformance.py` (new — this step is test-only; no
production code change)
**Change:** Add `test_does_not_flag_security_review_absent_when_ticket_untagged_security`, replaying
the real `TCK-20260710-CURRENT-RUN-SIDECAR-BASH` event shape (10 of `implement-ticket.js`'s 11
declared phases present, `Security-Review` genuinely absent, ticket not `security`-tagged) either by
reading the real `agent-monitoring/events.jsonl` rows for that `run_id` directly, or by writing an
equivalent fixture reproducing that exact shape if reading live data would make the test fragile to
future log rotation/cleanup — prefer the real data read first, per the same "read the real file, not
a copy" principle Step 1 already applies, and fall back to a faithful fixture only if the live rows
are not stably retained. Must assert `check_workflow_meta_conformance` produces **zero** `"FAIL"`
findings for this run, not one.
**Do NOT touch:** Do not modify `agent-monitoring/events.jsonl` (read-only). Do not special-case
`"Security-Review"` by name in production code — this test validates that Step 4's general
zero-events-any-status rule already handles it, it does not add new production logic.
**Verify:** the test itself, run via `pytest tests/tools/test_workflow_meta_conformance.py -v`.

### Step 6 — CLI entrypoint with `MARKER:`-prefixed JSON output contract
**Files:** `tools/gate_checks/workflow_meta_conformance.py`
**Change:** Add a `if __name__ == "__main__":` block accepting `run_id` as `sys.argv[1]`, calling
`check_workflow_meta_conformance(run_id)`, and printing `MARKER:` + `json.dumps(result)` to stdout —
matching every existing `gate_checks` script's established output contract (`archCheckOutput`,
`p0ScanOutput`, `finalizeCheckOutput`, etc. in `implement-ticket.js` all consume this exact
`MARKER:`-prefix + `indexOf` + `try/catch JSON.parse` shape). This makes the tool ready for a future
ticket to wire in via `bash()` without any interface change, without this ticket itself adding that
call site.
**Do NOT touch:** `.claude/workflows/implement-ticket.js` or any other workflow file — no call site
is added in this ticket (see Resolved Open Questions, additional scope decision). Do not embed the
`run_id` or any JSON payload inside a double-quoted `python3 -c "..."` string if writing any
accompanying invocation example/doc comment — pass as a separate argv element, per the file's own
documented quoting hazard.
**Verify:** manual smoke invocation (`python3 tools/gate_checks/workflow_meta_conformance.py
TCK-20260710-CURRENT-RUN-SIDECAR-BASH`) producing valid `MARKER:`-prefixed JSON; no dedicated
test_plan entry for this step specifically (it delivers the ticket's "mirror the shape of
`parity_updater_static.py`" scope bullet without expanding scope into live-workflow wiring).

## Scope Guards

- Do not edit `.claude/workflows/implement-ticket.js`, `create-tickets.js`, or `implement-epic.js` —
  all three are read-only parse sources in this ticket. In particular, do not fix
  `implement-epic.js`'s hardcoded `phase: 'Implement'` batch-event bug (lines 221-227) — that is a
  distinct workflow-authoring bug fix, explicitly deferred to a follow-up ticket (Resolved Open
  Question 3).
- Do not wire `check_workflow_meta_conformance` into any workflow's Finalize phase or any other
  in-workflow call site in this ticket (additional scope decision above). Do not drop test #9's
  intent silently either — it is explicitly dropped here with reasoning, not forgotten.
- Do not build a full JavaScript parser or shell out to `node` — regex/bracket-scan only, per the
  idea doc's explicit constraint and the investigation's confirmation that no JS-runtime dependency
  exists anywhere else in `tools/`.
- Do not modify `tools/agent-monitoring/vocabulary.py` or `tools/gate_checks/done_checker_static.py`
  — both are import-only dependencies for this ticket.
- Do not add or modify any `docs/parity_ledger/*.yaml` entry — investigation confirmed zero overlap;
  this is agent-infrastructure tooling, not simulation-mechanics behavior.
- Do not build a per-workflow conditional-phase allowlist (e.g. a dict keyed by workflow name listing
  `Security-Review`/`Link` as "expected absent") — the zero-events-any-status rule supersedes it
  (Resolved Open Question 2).
- Do not touch `simq-audit.js` — a 4th workflow file out of this ticket's stated scope (investigation
  Risk #6); the parser must not be exercised against it in this ticket's tests.

## Dependency Map

- Step 1 (parser) — independent.
- Step 2 (resolution + vocabulary reuse) — independent of Step 1's internals, but Step 4 needs both.
- Step 3 (event collection) — independent.
- Step 4 (aggregate function) — depends on Steps 1, 2, and 3 (calls all three).
- Step 5 (real-world fixture test) — depends on Step 4 (exercises the aggregate function).
- Step 6 (CLI entrypoint) — depends on Step 4 (wraps the aggregate function's output).

Steps 1, 2, and 3 can be implemented and verified in any order or in parallel; Steps 4-6 are strictly
sequential after them.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| (provisional) parses `meta.phases` from at least `implement-ticket.js` | Step 1 | `test_parses_meta_phases_from_implement_ticket_js` |
| (provisional) cross-reference correctly flags a synthetic run missing an event for a declared phase | Step 4 | `test_flags_declared_phase_with_zero_events` |
| (provisional) advisory-vs-blocking decision resolved during Plan, not assumed | Resolved Open Question 1 (this document) + Step 4's status semantics | N/A — a design decision, not a runtime behavior; documented in this plan's module-level reasoning, no dedicated test |

## Anti-Drift Notes

- The parser (Step 1) must stay regex/bracket-scan only — reintroducing a JS parser or `node`
  subprocess would violate the idea doc's explicit constraint and the investigation's confirmed
  "no JS toolchain anywhere in `tools/`" fact.
- The zero-events-any-status rule (Resolved Open Question 2, Step 4) is the single anti-false-positive
  mechanism. Do not let a future edit special-case any phase name — that regresses the moment a new
  conditional phase is added (the investigation's stated failure mode for a hardcoded
  `if phase == 'Security-Review'` check).
- Step 5's test must use real historical data (or a faithful reproduction of it) precisely because a
  synthetic-only fixture could accidentally omit the exact conditional-phase edge case that matters —
  `Security-Review` legitimately absent for a non-`security`-tagged ticket is the investigation's
  concrete confirmed false-positive risk, not a hypothetical.
- Any test exercising the parser against `implement-epic.js` (Step 1's third fixture) must only
  assert on the *parsed phase list* (`[Discover, Implement, Report]`) — it must not assert a clean,
  zero-`FAIL` cross-reference result against that workflow's real event data, since doing so would
  either (a) incidentally require "fixing" `implement-epic.js`'s event-emission gap to make the
  assertion true, which is explicitly out of scope, or (b) falsely suppress a real, correct finding.
  Investigation Risk #3 and the Out-of-Scope decision above both govern this.
- `check_workflow_meta_conformance`'s output must always be a JSON-serializable list of dicts (or a
  single labeled non-crashing dict for the "workflow unresolvable" / "no events for run_id" cases) —
  never a bare string, never an uncaught exception — so that a future ticket wiring this into
  `implement-ticket.js` via the `MARKER:` + `indexOf` + `try/catch JSON.parse` convention (Step 6)
  cannot be silently broken by this ticket's design.
- No parity ledger entry is added or updated for this ticket — confirmed zero overlap in
  investigation; do not create one speculatively.

## Deviations

**Step 5 (real-world false-positive guard) — discovered a genuine self-contradiction between
this plan's Step 4 and this plan's own Step 5 / test_plan.md, not an implementation error.**

Step 4's specified rule is literal and unambiguous: a declared phase is `"FAIL"` iff
`event_statuses.get(phase)` is empty/missing — i.e., zero events of ANY status recorded for that
run_id, including `skipped`. Implemented exactly as specified, this rule was run against Step 5's
mandated real fixture (`TCK-20260710-CURRENT-RUN-SIDECAR-BASH`'s actual
`agent-monitoring/events.jsonl` rows — confirmed by direct read: exactly 10 rows for that run_id,
covering `Scope, Investigate, Plan, Review, Implement, Architecture-Verify, Test, Parity(skipped),
Verify, Finalize`, zero rows with `phase == "Security-Review"`). Because `Security-Review` has
zero events of any status for this run — by design, per `docs/agent-monitoring/schema.md`:
"absent entirely (not even a `skipped` event) for every other ticket" — Step 4's rule produces a
`"FAIL"` finding for it. Step 5 requires the opposite: zero `FAIL` findings for this exact run.

This is not a coding mistake to fix by tweaking the test. `test_plan.md`'s own Anti-Drift Guards
section names the precise failure mode Step 4's literal rule embodies: "the naive implementation
(flag any declared phase with zero events, full stop) ... would immediately false-positive on
every non-security-tagged ticket." Step 4 as written IS that naive implementation for the
`Security-Review`/`Link` conditional-phase case — the "zero events of ANY status, including
`skipped`" wording in Resolved Open Question 2 correctly closes the *hotfix-skip-status* false
positive (a phase with `skipped`-status events now correctly counts as covered) but does nothing
for the *zero-rows-at-all* conditional-phase case, since both "legitimately never applicable" and
"silently skipped by the narrating LLM" produce identical zero-row shapes in `events.jsonl` for a
given run_id. Resolved Open Question 2's own text conflates these two distinct risks (missing-
status vs. zero-rows) into a single rule that only actually resolves one of them.

No fix was applied unilaterally. Per project instruction ("stop and report a plan conflict, do
not silently work around it"), the implementer: (1) implemented Step 4 exactly as specified — it
is internally consistent and correct for everything except this one case; (2) implemented Step 5's
test exactly as specified against the real fixture; (3) did NOT weaken the test's assertion and
did NOT add a forbidden per-workflow conditional-phase allowlist (explicitly banned by this plan's
Scope Guards) to force a pass; (4) marked the test `@pytest.mark.xfail(strict=True, reason=...)`
with the full evidence trail inline, so the gap is maximally visible and will loudly resurface
(via `strict=True`) if silently deleted or if the underlying behavior is ever fixed without
updating the marker.

**Recommended follow-up** (not undertaken here — out of this ticket's approved scope): the only
generic (non-allowlist) signal available to distinguish "legitimately conditional by workflow
design" from "silently vanished" is call-site conditionality in the `.js` source itself — i.e.,
whether the `phase(...)`/`pushEvent(...)` call site for a given title sits inside an `if (...) {
... }` block. This requires extending the parser beyond Step 1's stated scope (title extraction
only) into call-site structural analysis, a distinct enough change to warrant its own ticket
(e.g. `TCK-yyyymmdd-CONDITIONAL-PHASE-CALLSITE-DETECTION`) rather than being absorbed into this
one's Step 4 after the fact.
