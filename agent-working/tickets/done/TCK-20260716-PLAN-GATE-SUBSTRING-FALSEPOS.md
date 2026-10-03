---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS
phase: done
date: 2026-07-16
tags: [ai, workflows, bug]
---

# TCK-20260716-PLAN-GATE-SUBSTRING-FALSEPOS

## Title
Fix Plan-phase "unresolved question" gate false-positive in implement-ticket.js

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`.claude/workflows/implement-ticket.js` line 487 gates the Plan phase with
`planText.toLowerCase().includes('unresolved question')`, run against the
planner agent's free-text return summary. This is a naive substring match: it
false-triggers whenever the planner's prose summary contains the phrase "No
unresolved questions" (the plural "questions" contains "question" as a
substring), incorrectly returning `NEEDS_HUMAN_INPUT` even when the plan has
no genuine `## Unresolved Questions` section. This was hit directly on
TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP: the planner had resolved
both open items in a documented "Decision" section of `plan.md`, but its
return-text summary ("No unresolved questions: both open items were decided
in the plan's Decision section...") still matched the gate. Caught only by
manually reading `plan.md` and confirming no `## Unresolved Questions`
heading existed in the file, then proceeding past the false positive.

Fix: change the gate to check for a real `## Unresolved Questions` markdown
heading in the actual generated `staging_artifacts/{tid}/plan.md` file
(orchestrator-run `bash()` read of durable file state), instead of
substring-matching the agent's prose return value. This mirrors this same
file's existing pattern of orchestrator-run static checks reading real state
(e.g. `tagCheckOutput`, `archCheckOutput`) rather than trusting agent
self-report.

## Scope
- `.claude/workflows/implement-ticket.js`: replace the
  `planText.toLowerCase().includes('unresolved question')` check at line 487
  with an orchestrator-run read of the generated
  `staging_artifacts/${tid}/plan.md` file, testing for a genuine
  `## Unresolved Questions` markdown heading (not a substring of arbitrary
  prose).
- Preserve existing gate behavior/outputs when a real `## Unresolved
  Questions` section IS present: same `NEEDS_HUMAN_INPUT` status, same
  `pushEvent('Plan', 'planner', 'blocked', ...)` call, same monitoring write,
  same returned message pointing at `staging_artifacts/{tid}/plan.md`.
- Keep the `planTs`/`writeSidecar`/`plan = await agent(...)` adjacency block
  (lines ~459-483) structurally intact — `tests/tools/test_step0_ts_orchestrator.py`
  raw-source-text-parses this exact adjacency string and must continue to pass
  unmodified.
- Update `docs/ai/workflows.md` (line 85: "Plan | `planner` | Stops if
  unresolved questions in plan") only if its wording becomes materially
  inaccurate after the fix — current wording is already consistent with the
  corrected (file-based) behavior, so likely no change needed; confirm during
  implementation.

## Out of Scope
- Any change to the planner agent's prompt text or its instructions to flag
  unresolved questions under a "Unresolved Questions" heading
  (`.claude/agents/planner.md` lines 81/88) — those already describe the
  correct heading-based convention; only the orchestrator's *detection* of it
  is broken.
- Any change to other Plan-phase behavior (Review gate, Architecture-Verify
  gate, or any other phase's gate logic) — this ticket is scoped to the single
  Plan-phase check at line 487.
- Any change to `docs/ai/ticket-lifecycle.md` line 206 ("Gate: If plan.md
  contains an 'Unresolved Questions' section...") — this doc text already
  describes the file-based, heading-based behavior this fix implements; no
  update needed unless implementation reveals a wording gap.
- Retroactively re-checking or re-running TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP
  or any other already-completed ticket that may have been affected by this
  bug in the past — this ticket only fixes the gate going forward.
- Building a general "structured agent return schema" for the planner (e.g.
  JSON with an explicit `unresolved_questions: []` field) instead of a file
  heading check — out of scope; the file-based heading check is the
  narrowly-scoped fix requested.

## Acceptance Criteria
- [ ] Line 487's `planText.toLowerCase().includes('unresolved question')`
  check is replaced with a read of the actual `staging_artifacts/{tid}/plan.md`
  file content, testing for a genuine `## Unresolved Questions` markdown
  heading.
- [ ] A plan.md containing a planner return-summary sentence like "No
  unresolved questions: ..." but with NO `## Unresolved Questions` heading in
  the file itself does NOT trigger `NEEDS_HUMAN_INPUT` (regression test
  reproducing the exact false-positive scenario from
  TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP).
- [ ] A plan.md that DOES contain a genuine `## Unresolved Questions` heading
  still triggers `NEEDS_HUMAN_INPUT`, with the same `pushEvent`/monitoring/
  return-message behavior as before the fix (no regression on the true-positive
  path).
- [ ] `tests/tools/test_step0_ts_orchestrator.py` continues to pass unmodified
  (the `planTs`/`writeSidecar`/`plan = await agent(...)` adjacency string it
  parses is untouched by this fix).
- [ ] No other existing test in `tests/` that references "unresolved
  question" (confirmed via grep: none exist outside this line) regresses.

## Related Tickets
- TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP (done) — the ticket
  during which this false positive was hit and manually worked around; no
  code fix was made there, this ticket is the follow-up fix.
- TCK-20260705-WORKFLOW-SECURITY-GATE (done) — precedent for adding/fixing a
  gate in `implement-ticket.js`; same file, same `layer: ai` /
  `tags: [..., workflows]` pattern.
- TCK-20260708-SKILL-IMPLEMENT-TICKET-PHASE-DRIFT (done) — prior fix to
  `implement-ticket.js`/`SKILL.md` phase-description drift; same file, same
  tagging pattern (`[ai, documentation, workflows, skills]`).
- TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH (done) — introduced the
  `tests/tools/test_step0_ts_orchestrator.py` static parsing tests against
  `implement-ticket.js` that this ticket's fix must not break.
- TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME (backlogs) — a much larger,
  deliberately-deprioritized proposal to port `implement-ticket.js` off its
  current agent-prompt-based execution model entirely. Flagged as a
  conflict/duplicate candidate only in the broad sense that it touches the
  same file; it does not cover this specific gate bug and this hotfix should
  proceed independently rather than being folded into that backlog item.

## Related Docs
- `docs/ai/workflows.md` (line 85, table row: "Plan | `planner` | Stops if
  unresolved questions in plan") — describes the gate at a summary level;
  verify still accurate after the fix, update if wording needs tightening.
- `docs/ai/ticket-lifecycle.md` (line 206: "Gate: If plan.md contains an
  'Unresolved Questions' section, the workflow returns `NEEDS_HUMAN_INPUT`.")
  — already describes the intended (file/heading-based) behavior; the code is
  currently divergent from this doc, so this fix brings code into line with
  existing documentation rather than requiring a doc change.
- `docs/agent-monitoring/schema.md` (line 60: `NEEDS_HUMAN_INPUT` status
  description) — no change expected, confirms the status semantics are
  unaffected by this fix.
- `.claude/agents/planner.md` (lines 81, 88) — defines the planner's
  contract to flag unresolved questions under a "Unresolved Questions"
  heading in `plan.md`; this fix relies on that contract already being
  correct and unchanged.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH/investigation.md`
  and `plan.md` — document the exact adjacency-string structure around the
  Plan phase's `captureTs()`/`writeSidecar()`/`agent()` call sequence that
  must remain intact.
- `stored_artifacts/TCK-20260705-WORKFLOW-SECURITY-GATE/investigation.md` and
  `plan.md` — precedent investigation/plan for adding a gate to
  `implement-ticket.js`, useful as a structural reference for how gates are
  wired (pushEvent + monitoring write + structured return).

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (lines 455-499, Phase 3: Plan) —
  primary fix location, specifically line 487.
- `tests/tools/test_step0_ts_orchestrator.py` — static regression test file
  that raw-source-text-parses `implement-ticket.js`; must continue passing
  unmodified.
- `.claude/agents/planner.md` — defines planner's contract to write
  `staging_artifacts/{ticket_id}/plan.md` with an "Unresolved Questions"
  heading when applicable; read-only reference, not modified by this ticket.

## Assumptions / Open Questions
- Assumes `staging_artifacts/${tid}/plan.md` is guaranteed to exist and be
  readable by the time the gate check runs (the planner agent call at line
  461-483 writes it before returning) — if the planner fails to write the
  file, the orchestrator's `bash()` read needs a defined failure mode
  (treat as no unresolved questions vs. hard error); implementer should
  confirm which existing orchestrator-run checks (e.g. `tagCheckOutput`,
  `archCheckOutput`) do on a missing-file case and mirror that convention.
- Assumes a case-insensitive, heading-level match on `## Unresolved
  Questions` (allowing for markdown heading level variance, e.g. `###`) is
  sufficient — if the planner ever emits the heading at an unexpected level
  or with different casing, the fix should still catch it; implementer should
  decide the exact matching regex/normalization during implementation.
- Assumes no other call site in `implement-ticket.js` or `implement-epic.js`
  performs the same naive `planText`/prose substring check pattern elsewhere
  (grep during investigation confirmed no other "unresolved question" string
  matches in `tests/` or `.claude/`, but this doesn't rule out a differently-
  worded prose check for other gates — out of scope for this ticket if found,
  should be flagged as a separate follow-up ticket).
- If wrong, i.e. if `staging_artifacts/${tid}/plan.md` is NOT reliably present
  at the gate-check point, this scope is invalid and needs re-investigation
  of the write-then-read timing/ordering guarantee.

## Implementation Notes
Replaced the `planText.toLowerCase().includes('unresolved question')` condition
in `.claude/workflows/implement-ticket.js` (Phase 3: Plan) with an
orchestrator-run `bash()` check that reads the real
`staging_artifacts/${tid}/plan.md` file and tests for a genuine
`^##\s+Unresolved Questions\s*$` heading (MULTILINE mode, `re.search`),
matching the exact regex specified in the ticket. The plan.md path is passed
as a quoted `sys.argv[1]` element (mirrors `archCheckOutput`'s convention of
passing files as individually-quoted argv rather than interpolating untrusted
content into the Python source body). The result is printed with an
`UNRESOLVED_CHECK_JSON:` marker prefix and parsed via `indexOf` +
`JSON.parse`, mirroring the `tagCheckOutput`/`archCheckOutput` marker-prefix
convention already used elsewhere in this file. Only the *condition* changed —
the `pushEvent`, `log`, `writeMonitoring`, and `return` statements inside the
`if` block are untouched and still reference `planText` for the
summary/message fields, as required by scope.

**Revision within this same ticket/session:** the first pass inlined the regex
directly in the `python3 -c` string, which is untestable in isolation and
diverges from how `tagCheckOutput`/`archCheckOutput` are actually built (both
call a real importable function from `tools/`, not inline logic). Extracted
the check into `tools/gate_checks/plan_gate_static.py::
plan_has_unresolved_questions_heading()` and updated the `bash()` call to
import and call it, matching the established pattern exactly. Added
`tests/tools/test_plan_gate_static.py` (6 tests) as dedicated regression
coverage — including the exact false-positive prose case that motivated this
ticket — closing the test gap flagged during this ticket's own Parity phase
(the parity-updater agent correctly identified that manual `python3 -c`
verification alone was not durable regression coverage). `docs/parity_ledger/
infrastructure.yaml::INFRA-274`'s `v2_evidence`/`test_path` were updated in
place (same entry, not append-only — this ledger entry was created and
corrected within the same ticket/session, not across sessions) to point at
the real module and test file.

The `planTs` / `writeSidecar` / `plan = await agent(...)` /
`planText = plan.toString().trim()` adjacency block that
`tests/tools/test_step0_ts_orchestrator.py` raw-source-text-parses was left
structurally intact — confirmed by re-running that test suite (6/6 pass).

Verified the exact regex against three cases via direct `python3 -c`
invocation before writing it into the workflow file: a plan.md with prose
"No unresolved questions: ..." but no heading (correctly `false`, reproducing
and fixing the exact false-positive from
TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP), a plan.md with a real
`## Unresolved Questions` heading (correctly `true`), and a plan.md with a
`### Unresolved Questions` (H3) heading (correctly `false` — the ticket's
specified regex is H2-anchored via `^##\s+`, consistent with `planner.md`'s
contract which always emits `##`-level section headings).

`docs/ai/workflows.md` (line 85) and `docs/ai/ticket-lifecycle.md` (line 206)
were read and left unmodified — both already describe the gate generically
("if plan.md contains an 'Unresolved Questions' section") or at a summary
level ("stops if unresolved questions in plan"), which remains accurate after
this fix; neither described the old substring-matching implementation detail,
so there was no stale claim to correct. `.claude/agents/planner.md` was read
and left unmodified per Out of Scope — its existing contract (flag unresolved
items under a "Unresolved Questions" heading) is exactly what this fix now
checks for in the real file.

## Test Summary
- `pytest tests/tools/test_plan_gate_static.py -v` — 6 passed: true-positive
  genuine heading; the exact false-positive prose ("No unresolved questions:
  ...") that motivated this ticket; no heading at all; H3 heading does not
  match the H2-only contract; heading with trailing whitespace still matches;
  missing file returns `False` rather than raising.
- `pytest tests/tools/test_step0_ts_orchestrator.py tests/tools/
  test_current_run_sidecar_orchestrator.py tests/tools/
  test_tag_skill_mapping_check.py tests/tools/test_doc_staleness_check.py
  tests/tools/test_scope_orphan_fix.py tests/tools/
  test_workflow_meta_conformance.py tests/tools/test_plan_gate_static.py -v`
  — 64 passed, 1 xfailed (pre-existing, unrelated) — full static
  structural/adjacency surface for `implement-ticket.js` remains intact.
- `grep -rn "unresolved question" tests/` — no matches to the old
  substring-based behavior remain outside this ticket's own new test file.

## Files Changed
- `.claude/workflows/implement-ticket.js`
- `tools/gate_checks/plan_gate_static.py` (new)
- `tests/tools/test_plan_gate_static.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (INFRA-274)

## Completion Summary
Fixed the Plan-phase gate in `.claude/workflows/implement-ticket.js` to check
for a genuine `## Unresolved Questions` markdown heading in the real
generated `plan.md` file (via an orchestrator-run `bash()`/`python3` regex
check) instead of substring-matching the planner agent's free-text return
summary. This eliminates the false-positive where a planner's prose summary
sentence like "No unresolved questions: ..." incorrectly triggered
`NEEDS_HUMAN_INPUT` even when no genuine unresolved-questions section existed
in the plan, as previously hit and manually worked around on
TCK-20260716-SIMQ-URBAN-POLITICAL-FULL-PILLAR-SWEEP. The true-positive path
(a real `## Unresolved Questions` heading) still triggers the same
`NEEDS_HUMAN_INPUT` status, `pushEvent`, monitoring write, and return message
as before. No other phase, gate, or agent prompt in the file was touched;
`tests/tools/test_step0_ts_orchestrator.py` continues to pass unmodified;
`docs/ai/workflows.md` and `docs/ai/ticket-lifecycle.md` were confirmed
already accurate and left untouched.
