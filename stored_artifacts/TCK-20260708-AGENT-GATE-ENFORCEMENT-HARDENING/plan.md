---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING
artifact_type: plan
tags: [hooks, determinism, process-improvement]
---

# Implementation Plan — TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING

## Summary

**Revised after architecture-review NEEDS_CHANGES (user decision recorded below).** The
architecture-reviewer flagged that Design Decision 2's original case (a) hard block (withholding
`DONE` when the agent-monitoring write could not be verified) was an undisclosed reversal of
CLAUDE.md's explicit Hard Rule — "monitoring write failure must never fail the workflow." Given the
choice between amending that rule or redesigning case (a) to stay non-blocking, the user chose to keep
CLAUDE.md's rule intact and redesign case (a) as **loud-but-non-blocking**: a missing write now
produces a `failed`-status event and a persistent `WARNING` in Finalize's returned `message`, but the
run still reports `DONE`. Case (b) is unaffected by this revision — it remains a true hard block
(`PARITY_INCOMPLETE`), since Parity's status vocabulary does not implicate the monitoring-write Hard
Rule at all. Design Decision 2 below is rewritten accordingly; Design Decisions 1 and 3 are unchanged
from the pre-review version.

This plan escalates case (b) — the audit-flagged, silently-unenforced parity cross-reference miss — to
a real hard block inside `.claude/workflows/implement-ticket.js` (not `.claude/settings.json` hooks —
see Design Decision 3 below), introducing exactly one new phase-specific status (`PARITY_INCOMPLETE`)
where the investigation found none exists today. Case (a) is upgraded from silent to loud, but
deliberately stays within CLAUDE.md's existing Hard Rule rather than reversing it. It then documents
`lane-architecture`'s coverage boundary (AC #4) and brings both the idea doc and the audit doc back
into sync with reality (AC #5). No `src/` simulation code, Mechanics Bible chapter, or parity ledger
entry is touched — this is agent-tooling/process infrastructure only, confirmed by investigation.md's
"Parity Ledger Overlap: None found."

Three design decisions this plan makes are documented individually below, each with the specific
technical reasoning that resolved it (Decision 2 reflects the post-review revision). None is left as
an unresolved question — see the end of this plan for why.

### Design Decision 1 — case (b) failure vocabulary: introduce `PARITY_INCOMPLETE`

Investigation confirms Parity has **no pre-existing verdict enum** (unlike Verify/Architecture-Verify,
which already had `DOD_BLOCKED`/`NEEDS_CHANGES`/`BLOCKED` before their static backstops existed). This
is exactly the "concrete evidence" the ticket's AC #3 anticipates as the exception to "no new status."
Per the `FINALIZE_INCOMPLETE` precedent (introduced for the same reason — a phase with zero prior
failure status), this plan introduces **`PARITY_INCOMPLETE`** as the one new status for case (b). This
explicitly **reverses** the architecture-review-confirmed decision in
`stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/plan.md` ("no new blocking status for
Parity... a flagged miss is visibility-only, never a pipeline halt"). That reversal is this ticket's
entire premise (its own ACs ask for exactly the gate that decision declined to add), not an oversight —
Step 4 below cites this investigation finding in the code comment so a future reader does not read it
as accidental drift.

### Design Decision 2 (REVISED post-review) — case (a): loud non-blocking warning, CLAUDE.md's Hard Rule stays intact

**Original version of this decision (pre-review) proposed reusing `FINALIZE_INCOMPLETE` to hard-block
Finalize when `check_monitoring_write_recorded` found no matching write.** The architecture-reviewer
correctly flagged this as an undisclosed reversal of CLAUDE.md's Hard Rule — "monitoring write failure
must never fail the workflow" governs the *outcome* (does the workflow report failure), not just the
write call's own exception handling; withholding `DONE` because the write didn't land is the exact
outcome the rule forbids. Presented with the choice of (a) amending the Hard Rule's text to narrow it,
or (b) keeping the rule intact and making case (a) non-blocking, the user chose (b).

Revised design: `check_monitoring_write_recorded` (Step 1, unchanged — the check function itself is
still useful and still correctly implemented) is wired into Finalize **after** `await
writeMonitoring('DONE')`, but a `FAIL` result no longer changes the returned `status`. Instead:
- A `pushEvent('Finalize', 'finalizer', 'failed', ...)` record is written (so the monitoring trail
  itself — ironically — captures that its own write for this run could not be verified; this record
  necessarily lands in a *later* monitoring write, since the one being checked already happened).
- The Finalize return's `message` field carries a persistent, impossible-to-miss `WARNING:` prefix
  naming the missing write, in addition to the normal DONE message.
- `status` remains `'DONE'`. The ticket completes normally; `implement-epic.js`'s batch loop does not
  stop on it.

This satisfies the ticket's revised AC (loud, not hard-blocked) without touching CLAUDE.md's Hard Rule
text — no rule amendment is in scope for this ticket. The ordering constraint from the original
analysis still applies and is still worth stating: the check must run **after** `writeMonitoring('DONE')`
has been awaited, not as a 4th condition inside `run_finalize_selfcheck` (which runs *before* any
`writeMonitoring` call for this run — checking there would always FAIL, a guaranteed false positive on
every ticket).

Known accepted limitation (unchanged from the original analysis, now lower-stakes since this no longer
blocks anything): on a **resumed** ticket run, an earlier attempt's own `runs.jsonl`/`events.jsonl` rows
for that `ticket_id` will already exist, so `check_monitoring_write_recorded` cannot distinguish "this
attempt's write landed" from "a prior attempt's write landed but this one silently failed." Since the
check is now advisory only, this under-detection has no blocking consequence — it can only under-warn,
never wrongly block a compliant run. Not a concern for this ticket.

### Design Decision 3 — mechanism: `implement-ticket.js` control flow only, not `.claude/settings.json` hooks

Investigation found **zero precedent** anywhere in this repo for a hook that denies/blocks a tool call
(no `permissionDecision`, no exit-code-2 pattern) — every hook in `.claude/settings.json` only ever
injects `additionalContext`. Every one of the 8 existing hard-block statuses
(`CONFLICTS_DETECTED` … `DOD_BLOCKED`, `FINALIZE_INCOMPLETE`) is implemented via an early
`return { status: ... }` inside `implement-ticket.js`'s own control flow, never via a
`.claude/settings.json` hook. This plan follows that same, exclusively-used mechanism for both new
hard blocks. Consequence, stated explicitly rather than left implicit: **both hard blocks apply only
to `implement-ticket.js`-orchestrated runs** — a raw manual `git commit` or manual `mv` to
`tickets/done/` outside the workflow is not caught, exactly as no existing gate (`DOD_BLOCKED`,
`FINALIZE_INCOMPLETE`, etc.) catches manual action today either. This is not a gap introduced by this
ticket; it is the existing, universal scope boundary of every gate in this pipeline, made explicit so
a future reader doesn't mistake it for an oversight. Building genuine out-of-workflow enforcement would
require the harness to support hook-level tool-call denial, which — per this investigation — does not
exist anywhere in this repo today; that is out of scope for this ticket (it would be new
harness-capability territory, not a code change to an existing pattern).

## Steps

### Step 1 — Add `check_monitoring_write_recorded` static check function
**Files:** `tools/gate_checks/done_checker_static.py`
**Change:**
- Add `import json` to the existing import block (currently `csv`, `sys`, `datetime`, `Path` — no
  `json` yet).
- Add a small private helper, placed near `_count_rows_for_ticket` (the existing CSV analogue):
  ```python
  def _jsonl_rows_for_run_id(path: Path, run_id: str) -> list[dict]:
      """Return every parsed JSON row in `path` whose run_id == run_id. Malformed lines are
      skipped, not raised — a corrupt line elsewhere in the file must not crash this check."""
      if not path.exists():
          return []
      rows = []
      for line in path.read_text(encoding="utf-8").splitlines():
          if not line.strip():
              continue
          try:
              row = json.loads(line)
          except json.JSONDecodeError:
              continue
          if row.get("run_id") == run_id:
              rows.append(row)
      return rows
  ```
- Add the public check function in the Part B section (after `check_working_log_exactly_one_row`,
  before `run_finalize_selfcheck`):
  ```python
  def check_monitoring_write_recorded(
      ticket_id: str,
      runs_path: Path = Path("agent-monitoring/runs.jsonl"),
      events_path: Path = Path("agent-monitoring/events.jsonl"),
  ) -> tuple[str, str]:
      """Verify the agent-monitoring write for this run actually landed. Deliberately has no
      `tier` parameter and no NA branch — CLAUDE.md's Hard Rule requires the monitoring write
      "including hotfix," so unlike `check_migration_complete` this applies identically
      regardless of tier; the omission of a tier parameter is itself the design decision.
      """
      run_rows = _jsonl_rows_for_run_id(runs_path, ticket_id)
      if not run_rows:
          return ("FAIL", f"No row with run_id == {ticket_id} found in {runs_path}")
      event_rows = _jsonl_rows_for_run_id(events_path, ticket_id)
      if not event_rows:
          return (
              "FAIL",
              f"{runs_path} has a row for {ticket_id} but {events_path} has zero matching rows",
          )
      return (
          "PASS",
          f"{runs_path} ({len(run_rows)} row(s)) and {events_path} ({len(event_rows)} row(s)) "
          f"both have entries for {ticket_id}",
      )
  ```
- Do **not** add this function's result to `run_finalize_selfcheck`'s returned list — see Step 3's
  rationale (Design Decision 2) for why it is wired in separately, at a different call site, not as a
  4th aggregator condition.
**Do NOT touch:** `check_migration_complete`, `check_ticket_finalized`,
`check_working_log_exactly_one_row`, `run_finalize_selfcheck`'s existing 3-condition tuple, Part A
(`run_static_precheck` and its 5 checks), `classify_checklist_failure`.
**Verify:** `test_check_monitoring_write_recorded_fails_when_run_missing`,
`test_check_monitoring_write_recorded_fails_when_events_missing`,
`test_check_monitoring_write_recorded_passes_when_both_present` (Step 2).

### Step 2 — Unit tests for the new check function
**Files:** `tests/tools/test_done_checker_static.py`
**Change:** Add 4 new tests, using `tmp_path`-style fixtures consistent with this file's existing
style (do not introduce a new fixture pattern):
1. `test_check_monitoring_write_recorded_fails_when_run_missing` — empty/no `runs.jsonl` (or one with
   rows for a *different* `run_id`) → `("FAIL", ...)`.
2. `test_check_monitoring_write_recorded_fails_when_events_missing` — `runs.jsonl` has a matching row,
   `events.jsonl` has zero matching rows → `("FAIL", ...)`.
3. `test_check_monitoring_write_recorded_passes_when_both_present` — both files have ≥1 matching row →
   `("PASS", ...)`. This is the AC's required false-positive guard.
4. `test_check_monitoring_write_recorded_applies_under_hotfix_tier` — call the function with the same
   fixture data used in a hotfix-tier ticket scenario and confirm it still returns `PASS`/`FAIL`
   (never `NA`) — the function takes no `tier` argument at all, so this test documents and locks in
   that it cannot special-case hotfix, satisfying the anti-drift guard from test_plan.md ("do not let
   this be an untested implicit fallthrough").
**Do NOT touch:** Any existing test in this file (confirmed actual current count: 41 tests — must keep
passing unmodified, per test_plan.md; the plan's own earlier "38" baseline was stale, flagged by
architecture-review as a non-blocking note — verify actual count via
`grep -c '^def test_' tests/tools/test_done_checker_static.py` rather than trusting either figure).
**Verify:** `pytest tests/tools/test_done_checker_static.py -v` — all pass (41 existing + 4 new = 45
expected; confirm the real number rather than asserting it blindly).

### Step 3 (REVISED post-review) — Wire case (a) into Finalize as a non-blocking warning
**Files:** `.claude/workflows/implement-ticket.js` (Finalize phase, current lines ~1096-1110)
**Change:** Insert the new check between the existing `await writeMonitoring('DONE')` call and the
final `return { status: 'DONE', ... }`. Current code:
```js
pushEvent('Finalize', 'finalizer', 'ok', 'Ticket ' + tid + ' finalized and moved to done')
await writeMonitoring('DONE')

return {
  status: 'DONE',
  ...
}
```
New code:
```js
pushEvent('Finalize', 'finalizer', 'ok', 'Ticket ' + tid + ' finalized and moved to done')
await writeMonitoring('DONE')

// Verifies the write just above actually landed (tools/gate_checks/done_checker_static.py::
// check_monitoring_write_recorded). Deliberately non-blocking: CLAUDE.md's Hard Rule ("monitoring
// write failure must never fail the workflow") governs the OUTCOME here, not just the write
// ATTEMPT — so a FAIL result must not change `status` away from 'DONE'. This is a loud warning
// surfaced in the return message, not a gate. (Revised from an earlier hard-block design that was
// rejected at architecture-review for silently reversing the Hard Rule — see plan.md Design
// Decision 2.)
const monitoringCheckOutput = await bash(
  `python3 -c "
import sys, json
sys.path.insert(0, 'tools')
from gate_checks.done_checker_static import check_monitoring_write_recorded
status, evidence = check_monitoring_write_recorded(sys.argv[1])
print('MONITORING_CHECK_JSON:' + json.dumps({'status': status, 'evidence': evidence}))
" "${tid}"`
)
let monitoringCheck = null
const monitoringMarkerIndex = monitoringCheckOutput.indexOf('MONITORING_CHECK_JSON:')
if (monitoringMarkerIndex !== -1) {
  try {
    monitoringCheck = JSON.parse(monitoringCheckOutput.slice(monitoringMarkerIndex + 'MONITORING_CHECK_JSON:'.length).trim())
  } catch (e) { monitoringCheck = null }
}
let monitoringWarning = null
if (monitoringCheck === null || monitoringCheck.status === 'FAIL') {
  monitoringWarning = monitoringCheck === null ? 'monitoring-write self-check output unparseable' : monitoringCheck.evidence
  pushEvent('Finalize', 'finalizer', 'failed', ('monitoring_write_recorded: ' + monitoringWarning).slice(0, 200))
  log(`WARNING: agent-monitoring write for ${tid} could not be verified — ${monitoringWarning}`)
}

return {
  status: 'DONE',
  ...
  message: monitoringWarning
    ? `WARNING: agent-monitoring write for this run could not be verified (${monitoringWarning}). Ticket is otherwise complete — investigate agent-monitoring/runs.jsonl and events.jsonl manually.`
    : undefined,
}
```
Note: do **not** call `writeMonitoring` again in this branch — the write was already attempted (and,
per this branch's own trigger condition, did not land), so a second call here would either also fail
silently or misleadingly appear to "fix" the very gap just detected. Leave `agent-monitoring/`
untouched in this branch. `status` is unconditionally `'DONE'` — the `monitoringWarning` value only
ever affects the `message` field and the pushed event, never the status string.
**Do NOT touch:** The two existing `FINALIZE_INCOMPLETE` early-return branches
(`finalizeResults === null` and `finalizeFailures.length > 0`, lines ~1077-1096) — both are unrelated
to this check, remain real hard blocks, and must remain exactly as they are. `FINALIZE_INCOMPLETE` is
not introduced or referenced anywhere in this revised step. Do not add `check_monitoring_write_recorded`
as a 4th condition inside `run_finalize_selfcheck` itself (the ordering rationale in Design Decision 2
still holds even though this is no longer a hard block — checking there would always FAIL for the same
structural reason).
**Verify:** Manual/structural review only (no JS test harness exists, per test_plan.md) — confirm
bracket/quote balance, confirm the two existing FINALIZE_INCOMPLETE branches are byte-for-byte
unchanged, confirm `status` is unconditionally `'DONE'` in every path through this step (no branch may
set it to anything else), confirm `check_monitoring_write_recorded`'s Python-side behavior is exercised
via Step 2's tests (the JS wiring itself calls the already-unit-tested function, so no new Python test
is needed here).

### Step 4 — Wire case (b) hard block into the Parity phase
**Files:** `.claude/workflows/implement-ticket.js` (Parity phase, current lines ~849-854, inside the
`else` / full-call branch — i.e. `paritySkipEligible && !parityForceFullRun` is false)
**Change:** Current code:
```js
const parityEvidence = (parityCrossRef === null || parityCrossRefFailures.length > 0)
  ? (parity.summary || 'Parity ledger updated').slice(0, 150) + ' | cross-ref: ' + (parityCrossRef === null
      ? 'unparseable'
      : parityCrossRefFailures.map(f => f.file + ': ' + f.evidence).join('; ')).slice(0, 200)
  : (parity.summary || 'Parity ledger updated')
pushEvent('Parity', 'parity-updater', 'ok', parityEvidence, parity.ts)
```
New code:
```js
// Reverses TCK-20260705-GATE-DET-PARITY-UPDATER's explicit "visibility-only, no new blocking
// status" decision (stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/plan.md lines 222-227) —
// this ticket's own ACs ask for exactly the gate that decision declined to add. Only a genuine
// FAIL (a src/ file mapped to a ledger subsystem with no matching ledger touch) hard-blocks; an
// unparseable cross-ref result (parityCrossRef === null) stays non-blocking, unchanged from today.
if (parityCrossRefFailures.length > 0) {
  const evidence = parityCrossRefFailures.map(f => f.file + ': ' + f.evidence).join('; ').slice(0, 200)
  pushEvent('Parity', 'parity-updater', 'failed', evidence, parity.ts)
  await writeMonitoring('PARITY_INCOMPLETE')
  return {
    status: 'PARITY_INCOMPLETE',
    ticket_id: tid,
    failing_items: parityCrossRefFailures.map(f => f.file + ': ' + f.evidence),
    message: 'A src/ file mapped to a parity-ledger subsystem had no corresponding docs/parity_ledger/*.yaml entry touched in this diff — see failing_items.',
  }
}

const parityEvidence = parityCrossRef === null
  ? (parity.summary || 'Parity ledger updated').slice(0, 150) + ' | cross-ref: unparseable'
  : (parity.summary || 'Parity ledger updated')
pushEvent('Parity', 'parity-updater', 'ok', parityEvidence, parity.ts)
```
**Do NOT touch:** The `paritySkipEligible && !parityForceFullRun` branch (`if` side, ~line 771) — it
must continue to call neither the `parity-updater` agent nor this new block at all. Do not touch
`tools/gate_checks/parity_updater_static.py` itself (explicitly out of scope) — this step only acts on
`cross_reference_touched`'s existing return value. Do not change the `parityCrossRef === null`
(unparseable) branch's non-blocking treatment.
**Verify:** Manual/structural review (no JS harness) confirming: (a) the block only triggers on
`parityCrossRefFailures.length > 0`, (b) it is unreachable from the skip-eligible branch, (c) the
existing `test_flags_untouched_mapped_subsystem` / `test_does_not_flag_when_mapped_subsystem_touched`
/ `test_any_of_candidate_subsystems_touched_clears_flag` in `tests/tools/test_parity_updater_static.py`
all still pass unmodified (`cross_reference_touched`'s own semantics are untouched by this step).

### Step 5 — Confirm `implement-epic.js` batch-stop compatibility
**Files:** none (verification-only; no code expected to change)
**Change:** Read `.claude/workflows/implement-epic.js`'s stop condition
(`if (result.status !== 'DONE') { batchStatus = result.status; ... }`, confirmed at line 203) and
confirm it is string-agnostic — it already catches any status other than the literal `'DONE'`, so both
`PARITY_INCOMPLETE` (new) and the existing `FINALIZE_INCOMPLETE` reused for case (a) are caught with
zero code changes. Record this confirmation in the ticket's Implementation Notes rather than silently
assuming it (per test_plan.md's explicit ask — this reconfirms for a *different* status string than the
prior ticket verified).
**Do NOT touch:** `implement-epic.js` itself — no change is needed or in scope.
**Verify:** Manual read-through; no automated test (the condition's string-agnostic nature is provable
by inspection, not by a new test fixture).

### Step 6 — Document `lane-architecture`'s coverage boundary and update `implement-ticket`'s phase/return-value tables
**Files:** `docs/ai/workflows.md`
**Change:**
1. Add a new subsection (e.g. directly under the `implement-ticket` section, after its "Artifacts
   produced" list, or as a new top-level subsection before `## Simulation Workflows` — either location
   is acceptable; keep it near the `implement-ticket` phase table since that's where a reader will look
   for it) stating the coverage boundary, transcribed from investigation.md's already-confirmed finding
   (no new investigation needed):
   > `make lane-architecture` (`pytest tests/ -m "architecture"`) is a `src/`-simulation-code guard
   > lane only — durable-state mutation discipline, cross-domain import bans, unstable-sort detection.
   > It has **zero overlap** with the 4 gate-checker modules in `tools/gate_checks/`
   > (`done_checker_static.py`, `parity_updater_static.py`, `mechanics_auditor_static.py`,
   > `architecture_reviewer_static.py`): none of `tests/tools/test_*_static.py` carry
   > `@pytest.mark.architecture`, by deliberate design
   > (`tickets/done/gate-determinism-followups/SEQUENCE.md` decision 1) — these are agent-workflow
   > hygiene checks, not simulation-code architecture guards, and are intentionally not folded into
   > `lane-architecture`. Whether `lane-architecture` itself is wired into CI is a separate, already-
   > resolved question (audit finding D18 F3); this note is strictly about content-coverage boundary.
2. Update the Parity row of the phase table: change "...surfacing any untouched-mapped-subsystem miss
   via the pushed event (non-blocking)" to "...surfacing any untouched-mapped-subsystem miss; a genuine
   miss now hard-blocks the phase (returns `PARITY_INCOMPLETE`); an unparseable cross-ref result
   remains non-blocking."
3. Update the Finalize row's parenthetical to add the 4th post-migration condition: "...or the
   agent-monitoring write (`runs.jsonl`/`events.jsonl`) for this run could not be verified."
4. Add one new row to the Return Values table:
   `PARITY_INCOMPLETE | A src/ file mapped to a parity-ledger subsystem had no corresponding ledger entry touched in this diff (tools/gate_checks/parity_updater_static.py::cross_reference_touched) | Read failing_items, update the missing docs/parity_ledger/*.yaml entry, re-run with ticket_id`
**Do NOT touch:** Any other workflow's section in this file (`implement-epic`, `generate-simulation-setup`, etc.).
**Verify:** Manual review only — no doc-content test harness exists (per test_plan.md item 4).

### Step 7 — Update `idea_agent_gate_determinism.md`
**Files:** `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`
**Change:**
1. Extend the existing maturity banner at the top: note that the "Enforcement: nudge vs. block"
   section is now also shipped, citing this ticket ID, alongside the existing static-verifier pointer.
2. In "Open Questions," resolve the first bullet ("Do static verifier failures hard-block immediately,
   or downgrade...") — replace with a short resolved-note: hard-block, reusing existing vocabulary
   where one exists (case a: `FINALIZE_INCOMPLETE`) and introducing exactly one new phase-specific
   status where none existed (case b: `PARITY_INCOMPLETE`), per this ticket's Design Decisions 1–2.
   Leave the other 3 "Open Questions" bullets (module location, static-layer self-honesty test,
   token/cost telemetry) as-is — none are in this ticket's scope.
3. Correct the "Natural Integration Points" table's `agent-monitoring/tools.jsonl / hooks` row, which
   currently states "The hard-block escalation is a `PreToolUse`/`PostToolUse` hook change" — this is
   now known to be factually wrong (investigation found zero hook-blocking precedent in this harness).
   Replace with: "The hard-block escalation lives in `implement-ticket.js`'s own control flow (early
   `return {status: ...}`), the same mechanism every other gate in this pipeline already uses — not a
   `.claude/settings.json` hook change; hooks in this harness can only inject `additionalContext`, never
   block a tool call (confirmed by TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING's investigation)."
**Do NOT touch:** The "Idea," "Where it helps," or "Verdict provenance" sections — already correctly
marked shipped by the prior tickets' work; not this ticket's concern.
**Verify:** Manual review only.

### Step 8 — Update `agent_infrastructure_audit.md`
**Files:** `docs/ai/agent_infrastructure_audit.md`
**Change:** In the "Recommendations" list:
1. Recommendation #1 ("Log hook near-misses, not just hook fires") — mark closed, but be precise about
   *how* it was closed: this ticket did not literally add near-miss logging; it resolved the underlying
   concern via a stronger mechanism (hard-blocking the two specific cases the idea doc's own
   "Enforcement: nudge vs. block" section named as unambiguous and cheap to check), superseding the
   originally-proposed near-miss-logging approach. State this accurately rather than implying the
   literal recommendation text was implemented verbatim — append: *"(Closed by
   TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING — resolved via hard-blocking the two named cases
   directly rather than near-miss logging; see `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`'s
   "Enforcement: nudge vs. block" section.)"*
2. Recommendation #3 ("Write down what `lane-architecture` actually covers") — mark closed with a
   pointer: *"(Closed by TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING — see
   `docs/ai/workflows.md`'s lane-architecture coverage-boundary note.)"*
**Do NOT touch:** Recommendations #2 (cost telemetry — explicitly out of scope, separate child
ticket), #4 (skill catalog pruning), #5 (already closed by a different, unrelated prior ticket per the
existing footnote) — do not alter their existing text or closure status.
**Verify:** Manual review only.

## Scope Guards

- Do not modify any of the 4 static verifier modules' existing check functions/logic:
  `done_checker_static.py`'s `check_staging_artifacts_complete`, `check_data_runs_clean`,
  `clean_data_runs_early`, `check_ticket_location`, `check_working_log_no_row_yet`,
  `check_frontmatter_valid`, `run_static_precheck`, `classify_checklist_failure`,
  `check_migration_complete`, `check_ticket_finalized`, `check_working_log_exactly_one_row`,
  `run_finalize_selfcheck` (only additive: one new function, Step 1); `parity_updater_static.py`
  (`derive_mapping`, `expected_subsystems_for_files`, `cross_reference_touched`) — untouched, zero
  lines changed; `mechanics_auditor_static.py`; `architecture_reviewer_static.py`.
- Do not touch the context-scan grep/find advisory hook or the Agent investigation-keyword advisory
  hook in `.claude/settings.json` — explicitly Out of Scope per the ticket, and the idea doc explicitly
  keeps the former advisory.
- Do not implement either hard block as a `.claude/settings.json` `PreToolUse`/`PostToolUse` hook —
  both live entirely in `implement-ticket.js`'s control flow (Design Decision 3).
- Do not add a check for manual/out-of-workflow actions (raw `git commit`, manual `mv` to
  `tickets/done/`) — out of scope per Design Decision 3; no existing gate in this repo does this
  either.
- Do not add `check_monitoring_write_recorded` as a 4th condition inside `run_finalize_selfcheck`'s
  aggregator — it would always FAIL (Design Decision 2); it is wired in at a different call site
  (Step 3).
- Do not touch the `paritySkipEligible && !parityForceFullRun` skip-eligible branch in the Parity
  phase — the new hard block only lives in the `else` (full-call) branch, at the exact point
  `cross_reference_touched` is already computed today.
- Do not add cost/token telemetry (Recommendation #2) — separate child ticket in this epic.
- Do not backfill or retroactively audit past `DONE` runs' monitoring-write completeness — this ticket
  changes future enforcement only.
- Do not alter `docs/parity_ledger/*.yaml` — investigation confirmed no entry needs updating and none
  should be added (agent-tooling scope, not simulation mechanics).
- Do not conflate D18 F3 (CI wiring of `lane-architecture`) with this ticket's Step 6 coverage-boundary
  documentation — they answer different questions; do not cite D18 F3 as satisfying AC #4.
- Do not alter Recommendations #2, #4, or #5 in `agent_infrastructure_audit.md`.

## Dependency Map

- Step 1 → Step 2 (tests require the function to exist).
- Step 1 → Step 3 (Step 3's `bash()` call invokes `check_monitoring_write_recorded`, which must exist
  first).
- Step 4 is independent of Steps 1–3 (different phase, different file region) — can be implemented in
  parallel/either order.
- Step 5 depends on Step 3 and Step 4 both landing (it confirms the batch-stop condition catches both
  final status strings, `FINALIZE_INCOMPLETE`-via-Step-3 and `PARITY_INCOMPLETE`-via-Step-4) — but
  requires no code change itself, only a read-through once both exist.
- Step 6 depends on Steps 3 and 4 (documents their exact resulting behavior) but its lane-architecture
  coverage-boundary content (item 1 in Step 6) has no code dependency and could be drafted first.
- Step 7 depends on Steps 3, 4, and 6 (references the final decisions and the doc landing in Step 6).
- Step 8 depends on Step 6 (points to it) and Step 7 (both doc-sync updates should land together for a
  consistent final state, though Step 8 does not technically require Step 7's content).
- All steps are otherwise independent of each other's internals — no step requires re-reading another
  step's diff to implement correctly, only to know it landed.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A ticket finalize step with no matching agent-monitoring write is loud but non-blocking (failed-status event + WARNING message, status stays DONE) | Steps 1, 2, 3 (revised) | `test_check_monitoring_write_recorded_fails_when_run_missing`, `..._fails_when_events_missing`, `..._passes_when_both_present`, `..._applies_under_hotfix_tier` (Step 2, unchanged Python-level tests) + manual review of Step 3's revised JS wiring confirming `status` is unconditionally `'DONE'` |
| A commit touching a parity-ledger-mapped src/ path with no matching ledger touch is hard-blocked, not just nudged | Step 4 | Existing `test_flags_untouched_mapped_subsystem` etc. in `test_parity_updater_static.py` (unmodified, confirm semantics preserved) + manual review of Step 4's JS wiring |
| The one new hard block (case b) introduces exactly one new status string (`PARITY_INCOMPLETE`) | Design Decisions 1, 2 (revised); realized in Step 4 only — Step 3 no longer introduces or reuses any status string for case (a) | No automated test — design-decision documentation is the artifact; manual review confirms code matches stated decision |
| `docs/ai/workflows.md` or a new doc explicitly states `lane-architecture`'s coverage boundary against the 4 gate-checker modules | Step 6 | Manual review only |
| `idea_agent_gate_determinism.md` and `agent_infrastructure_audit.md` both reflect current reality | Steps 7, 8 | Manual review only |
| Tests cover the case (b) hard-block trigger condition, the case (a) warning-but-DONE behavior, and confirm no false-positive block on a normal compliant run | Step 2 (case a: all 4 new tests, unchanged) + existing `test_parity_updater_static.py` suite (case b, unmodified, already covers this) + Step 3's manual review (case a's DONE-status invariant has no Python-level test since it's JS control flow) | `pytest tests/tools/test_done_checker_static.py -v`, `pytest tests/tools/test_parity_updater_static.py -v` |

## Anti-Drift Notes

- **Do not re-derive `cross_reference_touched`'s semantics.** Step 4 must call the existing function
  as-is; a stricter/looser reimplementation would silently regress the ANY-of-candidates matching
  semantics already tested by `test_any_of_candidate_subsystems_touched_clears_flag`.
- **The unparseable (`null`) cross-ref result stays non-blocking in both Steps 3 and 4.** Only a
  parsed, non-empty FAIL list triggers a hard block. This is a deliberate, narrower scope than
  Finalize's own unparseable-output handling (which treats unparseable as `FINALIZE_INCOMPLETE`) — the
  two phases are allowed to differ here because the ticket's own investigation explicitly scoped
  case (b)'s trigger condition to `parityCrossRefFailures.length > 0`, not to plumbing/parse failures.
- **`writeMonitoring` itself must never become fail-fast.** Only Step 4 (Parity, case b) may hard-block;
  the write *attempt* inside `writeMonitoring` keeps its existing non-fatal `WARNING ... (non-fatal)`
  behavior untouched, per CLAUDE.md's Hard Rule.
- **Step 3 (revised) must never set `status` to anything other than `'DONE'`.** This is the entire
  point of the post-review revision — a FAIL from `check_monitoring_write_recorded` may only add a
  `failed`-status event and a `WARNING` in the `message` field; if a future edit reintroduces a
  status-changing branch here, that silently reverses CLAUDE.md's Hard Rule again, exactly what
  architecture-review caught this round.
- **Step 3's warning branch does not call `writeMonitoring` a second time.** The monitoring write was
  already attempted by the preceding `await writeMonitoring('DONE')`; a second call here would either
  also fail silently or misleadingly appear to "fix" the very gap just detected.
- **Resumed-ticket false-negative risk (Design Decision 2) is accepted, not fixed.** Do not attempt to
  add run-attempt/session partitioning to `check_monitoring_write_recorded` as part of this ticket —
  that would be new scope beyond what the ACs ask for.
- **D18 F3 (CI wiring) and this ticket's Step 6 (content coverage boundary) answer different
  questions** — Step 6's doc text must not cite D18 F3 as if it already satisfied AC #4.
- **No `src/` file, Mechanics Bible chapter, engine contract, or parity ledger entry is touched by any
  step** — confirmed by investigation; if implementation drifts into any of those, that is out of
  scope for this ticket and should stop.

## Unresolved Questions

None, after one review round-trip. Investigation flagged three open questions (failure vocabulary for
case (b); case (a)'s ordering constraint; whether hooks must catch manual/out-of-workflow actions).
This plan's first version resolved all three on planner authority (Design Decisions 1–3), but
architecture-review returned `NEEDS_CHANGES` on Design Decision 2: reusing `FINALIZE_INCOMPLETE` to
hard-block case (a) was an undisclosed reversal of CLAUDE.md's Hard Rule ("monitoring write failure
must never fail the workflow"), unlike Design Decision 1's reversal of the Parity precedent, which was
explicitly disclosed and justified. This was exactly the kind of conflict the Clarification Rule
reserves for a human — not a planner implementation-detail call — so it was surfaced to the user
directly rather than re-decided unilaterally. The user chose to keep CLAUDE.md's rule intact and
redesign case (a) as loud-but-non-blocking (Design Decision 2, revised, above). Design Decisions 1 and
3 were not in question and are unchanged. The plan now proceeds on the revised basis with no open
questions remaining.

## Deviations

- **Step 6, item 3 wording corrected during Implement.** This plan's Step 6 item 3 literally reads:
  *"Update the Finalize row's parenthetical to add the 4th post-migration condition: '...or the
  agent-monitoring write (`runs.jsonl`/`events.jsonl`) for this run could not be verified.'"* Read
  literally and appended directly after the existing "...returns `FINALIZE_INCOMPLETE` instead of
  `DONE` if a discrepancy is found" text, this phrasing reads as though the monitoring-write check
  also triggers `FINALIZE_INCOMPLETE` — which contradicts Design Decision 2 (revised), the actual
  implemented behavior (non-blocking warning, `status` stays `DONE`), and this plan's own explicit
  Anti-Drift Note ("Step 3 (revised) must never set `status` to anything other than `'DONE'`"). This
  is stale wording carried over from the pre-review draft of Step 6 that was not re-synced when
  Design Decision 2 was revised. Implement wrote the Finalize row instead as: "...returns
  `FINALIZE_INCOMPLETE` instead of `DONE` if a discrepancy is found; separately, after
  `writeMonitoring('DONE')`, runs `check_monitoring_write_recorded` to confirm the agent-monitoring
  write ... landed — a FAIL here is loud but non-blocking (a `failed`-status event plus a `WARNING`
  in the returned `message`), `status` stays `DONE` ..." — accurately describing the actual shipped
  behavior rather than the plan's literal (stale) text. No code behavior was changed by this
  deviation; only the doc wording in `docs/ai/workflows.md` differs from the plan's literal Step 6
  instruction.
