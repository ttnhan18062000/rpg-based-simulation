---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260714-DATA-RUNS-VERIFY-REGEN
phase: done
date: 2026-07-14
tags: [ai, workflows, process-improvement]
---

# TCK-20260714-DATA-RUNS-VERIFY-REGEN

## Title
Post-Test `data/runs/` cleanup checkpoint doesn't cover artifacts regenerated during Parity/Verify — `done-checker` still blocks on the same failure it was fixed to prevent

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`TCK-20260708-DATA-RUNS-CLEANUP-TIMING` (done, 2026-07-08) added a one-time `clean_data_runs_early()`
checkpoint to `.claude/workflows/implement-ticket.js`, running immediately after the Test phase and
before Parity, specifically to stop `done-checker` (Verify phase) from blocking on leftover
`data/runs/*` / `reports/release_proof/*` artifacts. Its stated acceptance criterion was "the next 5
completed `implement-ticket` runs show zero Verify-phase failures citing uncleaned `data/runs/`."

Per `agent-monitoring/retro/RETRO-2026-W29.md` (2026-07-14 retro, Notes section 1), that criterion has
not held. Three `done-checker` BLOCKED events cite uncleaned `data/runs/` *after* the fix landed:

- `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` (event seq 11, 2026-07-14T04:19:32Z) — "leftover data/runs
  artifacts". Sequence: Test (04:03:34, includes an `evaluate_simq` dry-run) → cleanup checkpoint (silent,
  runs immediately after) → Parity (`parity-updater`, ok, 04:10:37) → Verify BLOCKED (04:19:32) → re-run
  Verify OK after manual cleanup (04:25:07).
- `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` (event seq 9, 2026-07-14T07:38:42Z) — "3 items:
  ...data/runs uncleaned". Sequence: Test (07:15:53) → cleanup checkpoint → Parity *skipped* (no src/
  change) → Verify BLOCKED (07:38:42, 23 min later) — no phase but `done-checker` itself ran in that
  window.
- `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` (event seq 9, 2026-07-14T11:44:28Z) — "36 leftover
  data/runs dirs contradicting ticket's own cleanup claim". Sequence: Test (09:57:23) → cleanup checkpoint
  → Parity (`parity-updater`, ok, 11:40:10, 1h43m elapsed) → Verify BLOCKED (11:44:28).

In all three cases the only phases between the post-Test checkpoint and the Verify failure are Parity
(`parity-updater`) and/or Verify (`done-checker`) itself — both LLM agents with full Bash/tool access,
and both operating in a pipeline culture that explicitly rewards "independently confirming" claims by
re-running things (`test-scoper` re-runs via `git stash`; `architecture-reviewer` "independently
confirmed zero diff" is a recurring pattern in this week's `agent-monitoring/events.jsonl`). Several
integration tests write directly into `data/runs/` (`tests/integration/lab/test_lab_observatory_integration.py`,
`tests/integration/observability/test_cognition_snapshot_artifact.py`,
`tests/integration/observability/test_metric_windows_flow.py`,
`tests/integration/observability/test_balance_envelope_comparison.py`, others). If Parity or Verify
re-runs any of these to verify a claim, it regenerates `data/runs/` artifacts *after* the one-time
checkpoint already ran — `done-checker`'s static precheck (mtime-based) then correctly flags them as
"this session's, uncleaned," but the underlying assumption that no phase after Test creates new
artifacts is false for this codebase.

The prior ticket's own "Residual risk, accepted and unresolved" section anticipated only a *concurrent
second session* colliding with the checkpoint's mtime-lower-bound logic — it did not anticipate later
phases in the *same* session regenerating artifacts after the checkpoint ran. This is a genuine gap in
that fix, not a previously-accepted tradeoff.

## Scope
- Investigate exactly which phase(s)/agent(s) are producing the post-checkpoint `data/runs/` artifacts
  in the three cited runs (or confirm the mechanism via a reproduction) before choosing a fix — do not
  assume without verifying, per the Uncertainty Rule.
- Move or duplicate the `clean_data_runs_early()` sweep (or an equivalent) so it also runs immediately
  before `done-checker`'s DoD check in the Verify phase (`.claude/workflows/implement-ticket.js`,
  currently around line 1072's Phase 8 boundary), not only once after Test — so it sweeps up whatever
  Parity/Verify's own verification work created, rather than relying on `done-checker` to detect-and-block
  on it.
- Preserve `check_data_runs_clean` / `run_static_precheck`'s existing Verify-phase backstop role (per the
  prior ticket's own constraint) — this ticket is about closing the *timing* gap between the last cleanup
  sweep and the Verify check, not removing the backstop.
- Consider (Investigate to confirm feasibility, not prescribed here) whether Parity's/Verify's own
  agent-run verification commands should be constrained to avoid regenerating `data/runs/` artifacts in
  the first place (e.g. steering agents toward `pytest --collect-only`-style dry verification or an
  existing result cache instead of re-executing artifact-producing integration tests) as a complementary,
  not alternative, fix.
- Update `docs/ai/ticket-lifecycle.md`'s Verify/Finalize phase documentation and the `data_runs_clean`
  condition's backstop note to reflect the corrected timing.
- Add/update tests demonstrating that artifacts created during Parity/Verify (not just Test) are caught
  before the Verify agent judges cleanliness.

## Out of Scope
- Changing `check_data_runs_clean`'s mtime-lower-bound definition of "this session's own file" — same
  out-of-scope boundary the prior ticket set; not the mechanism being fixed here.
- The concurrent-session-overlap residual risk already accepted in
  `stored_artifacts/TCK-20260708-DATA-RUNS-CLEANUP-TIMING/plan.md` — unrelated failure mode, not
  reopened by this ticket.
- The second retro-flagged failure category (empty Completion Summary / Files Changed / Test Summary
  sections at Verify) — a separate concern with its own fix path, not addressed here.
- Any change to what Parity/Verify agents are asked to verify, beyond constraining *how* they verify it
  (see Scope) — their verification mandate itself is out of scope.

## Acceptance Criteria
- Root cause confirmed (which phase/agent/command actually regenerates `data/runs/` artifacts in at
  least one of the three cited runs, or a reproduced equivalent) before the fix is designed.
- A cleanup sweep runs at a point in the pipeline after which no further `data/runs/`-writing agent work
  occurs before Verify's DoD check reads its result — verifiable by diffing
  `.claude/workflows/implement-ticket.js`'s phase ordering before/after.
- `check_data_runs_clean` / `run_static_precheck` still exist and still run at Verify as a backstop —
  unchanged in role.
- A new or updated test demonstrates that artifacts created during a simulated Parity/Verify step (not
  just Test) are cleaned or fail-fast before the Verify DoD check judges cleanliness.
- `docs/ai/ticket-lifecycle.md` updated to reflect the corrected checkpoint timing.
- Scoped pytest run against the changed test file(s) passes.
- The next 5 completed `implement-ticket` runs (standard tier) show zero Verify-phase failures citing
  uncleaned `data/runs/` — noted as a follow-up verification signal for the next weekly retro, not a hard
  gate on this ticket's own closure.

## Related Tickets
- TCK-20260708-DATA-RUNS-CLEANUP-TIMING (done) — introduced the post-Test checkpoint and
  `clean_data_runs_early()` this ticket is closing a timing gap in; must not be reverted or weakened.
- TCK-20260705-GATE-DET-DONE-CHECKER (done) — built `done_checker_static.py`, including
  `check_data_runs_clean`, the backstop this ticket must preserve.

## Related Docs
- `CLAUDE.md` — Workflow Rule > After Work; Definition of Done ("Temporary run data cleaned").
- `docs/ai/ticket-lifecycle.md` — Test section (post-Test cleanup checkpoint paragraph), DoD condition
  10's backstop note, Finalize step 5, Failure Recovery Reference table (`DATA_RUNS_CLEAN_FAILED` row).
- `agent-monitoring/retro/RETRO-2026-W29.md` — Notes section 1, source of the evidence motivating this
  ticket.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260708-DATA-RUNS-CLEANUP-TIMING/` (investigation.md, plan.md, test_plan.md) —
  prior design for the checkpoint this ticket extends; read before planning the fix.

## Related Code Areas
- `.claude/workflows/implement-ticket.js` — post-Test cleanup checkpoint (~line 757-799), Parity phase
  (~line 802-936), Verify phase (~line 993-1071).
- `tools/gate_checks/done_checker_static.py` — `clean_data_runs_early` (~line 165+),
  `check_data_runs_clean`, `run_static_precheck` — reuse, do not duplicate logic.
- `tests/tools/test_done_checker_static.py` — home for new tests, alongside the 5 added by the prior
  ticket.

## Assumptions / Open Questions
- Assumes the regenerating agent is `parity-updater` and/or `done-checker` itself, based on phase-timing
  correlation across all three cited runs — not yet confirmed by direct evidence (e.g. a transcript or
  bash-history trace showing which command wrote the artifacts). Investigate must confirm or correct this
  before the fix is designed, per the Uncertainty Rule ("vague leads stay vague until evidence narrows
  them").
- Open question for Investigate: should the second sweep run unconditionally right before Verify's agent
  call, or only when Parity actually ran (non-skipped) — the `TCK-...-LOOPDET-NONDETERMINISM` case shows
  regeneration can happen even with Parity skipped, suggesting `done-checker` itself is a plausible source
  and an unconditional pre-Verify sweep is likely necessary regardless of Parity's skip state.
- Assumes `layer: ai` / no Mechanics Bible or parity ledger overlap — same rationale as the prior ticket
  (this is Claude agent workflow tooling, not gameplay simulation code).

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260714-DATA-RUNS-VERIFY-REGEN/plan.md` Steps 1-4, exactly as
specified, with no deviations:

1. `.claude/agents/done-checker.md` — replaced the single-part `## Step 0 — Run the Static Pre-Check
   Script First` section with a two-part `## Step 0 — Sweep data/runs/, Then Run the Static Pre-Check
   Script` section. **Step 0a** runs `clean_data_runs_early(start_ts)` unconditionally before anything
   else, folding its PASS/CLEANED/FAIL result into condition 10's evidence (never a separate checklist
   item); a Step 0a `FAIL` short-circuits condition 10 without waiting on Step 0b. **Step 0b** is the
   renamed, otherwise-unchanged original `run_static_precheck` call, now explicitly deferring to Step
   0a's result for condition 10 if it already failed. Condition 10's checklist line gained a
   parenthetical pointing back to Step 0. Conditions 1-9, 11, 13, the Tier-Aware Checking section, and
   the Output section are byte-identical to before (confirmed via `git diff` review after edit).
2. `tests/tools/test_done_checker_static.py` — added
   `test_data_runs_clean_pre_verify_sweep_documented_in_done_checker_prompt` immediately after
   `test_data_runs_clean_status_appears_in_failure_recovery_reference_table`, asserting
   `"clean_data_runs_early"` and `"Step 0a"` both appear in `.claude/agents/done-checker.md`. This is a
   static string-presence check only (per plan.md's Anti-Drift guard) — it proves the instruction text
   exists in the file the agent is built from, not that a live agent turn executes it. No existing test
   body was touched.
3. `docs/ai/ticket-lifecycle.md` — three edits exactly as specified in plan.md Step 3: (a) appended a
   "Reliability caveat" paragraph after the Post-Test cleanup checkpoint paragraph in the Test section,
   documenting that this checkpoint's `bash()` call has never been observed to execute (per
   investigation.md's `tools.jsonl` evidence) and that it is now defense-in-depth documentation only;
   (b) replaced the Verify section's single Step 0 prose paragraph with Step 0a (the new
   `clean_data_runs_early` sweep, folding deletion errors into condition 10) and Step 0b (the renamed,
   unchanged `run_static_precheck` call, now noting it defers to Step 0a for condition 10 if already
   failed); (c) replaced the 13-condition table's row 10 to point at Step 0a as the primary cleanup
   mechanism and describe `run_static_precheck`'s `data_runs_clean` check as the backstop. The Failure
   Recovery Reference table (`DATA_RUNS_CLEAN_FAILED` row), the Parity section, the Architecture-Verify
   section, and the Finalize section were not touched.
4. Ran `pytest tests/tools/test_done_checker_static.py -v` — 53 passed (52 existing + 1 new), zero
   modified existing test bodies (confirmed via `git diff --stat` showing only a 7-line addition to the
   test file).

**Deliberate divergence from this ticket's original Related Code Areas / AC #2 wording (already flagged
and accepted at Plan/Review, per plan.md Design Decision 1):** `.claude/workflows/implement-ticket.js`
is **not modified** by this ticket, despite being named in Related Code Areas and despite AC #2's
originally-stated verification method ("diffing `implement-ticket.js`'s phase ordering before/after").
Investigation found the existing post-Test checkpoint in that file has never actually executed in any
observed run (zero real invocations across 5+ weeks of `agent-monitoring/tools.jsonl`), because it is a
bare, non-`phase()`-anchored `bash()` block with no row in `SKILL.md`'s fixed six-shape translation
table and no per-phase prose narrating it — the exact failure mode this ticket exists to fix. Adding a
second checkpoint in the same shape inside `implement-ticket.js` would carry the identical risk.
Instead, the sweep was added as `done-checker`'s own Step 0a, mirroring `run_static_precheck`'s Step 0,
the one call-shape in this codebase with a directly-evidenced reliable execution record (confirmed
firing in all three cited runs' `tools.jsonl` slices) because it is embedded in the agent's own prompt
definition rather than orchestrator pseudocode a separate LLM turn must remember to transcribe. AC #2's
verification method was correspondingly refined in plan.md's Acceptance Criteria Map to "diffing
`done-checker.md`'s Step 0 section" — satisfied above. `.claude/skills/implement-ticket/SKILL.md` was
also confirmed unnecessary to touch (it has no per-phase prose structure at all to extend) and was not
modified, consistent with plan.md Design Decision 2.

`tools/gate_checks/done_checker_static.py` was not modified — `clean_data_runs_early` and
`check_data_runs_clean` are reused exactly as they exist today; only a new call site was added inside
`done-checker.md`. `run_static_precheck`'s 5-check aggregation tuple did not grow to 6 (confirmed by
`test_run_static_precheck_all_pass_eligible` and `test_run_static_precheck_surfaces_fail_not_masked`
passing unmodified). The post-Test checkpoint's code, its `DATA_RUNS_CLEAN_FAILED` status, and its
original doc paragraph remain exactly as they were — only a caveat paragraph was appended, per plan.md
Design Decision 3.

## Test Summary
`pytest tests/tools/test_done_checker_static.py -v` — 53 passed (52 pre-existing + 1 new:
`test_data_runs_clean_pre_verify_sweep_documented_in_done_checker_prompt`), 0 failed, 0 modified
existing test bodies. Command and full pass list captured in this session's implementer transcript.
No other test files were touched by this ticket (workflow tooling / agent-prompt change only, no `src/`
or simulation-logic files modified).

## Files Changed
- `.claude/agents/done-checker.md` — Step 0 section split into Step 0a (new pre-Verify
  `clean_data_runs_early` sweep) / Step 0b (renamed, unchanged `run_static_precheck` call); condition
  10 checklist line gained a parenthetical pointer to Step 0.
- `tests/tools/test_done_checker_static.py` — added
  `test_data_runs_clean_pre_verify_sweep_documented_in_done_checker_prompt` (doc-guard test).
- `docs/ai/ticket-lifecycle.md` — Test-section Reliability caveat paragraph; Verify-section Step 0
  prose split into Step 0a/0b; 13-condition table row 10 rewritten to point at Step 0a.

## Completion Summary
Closed the timing gap between the (non-executing) post-Test `data/runs/` cleanup checkpoint and
Verify's DoD check by adding an unconditional pre-Verify cleanup sweep as `done-checker`'s own Step 0a,
immediately before the existing Step 0b static pre-check — reusing `clean_data_runs_early` exactly as
it exists today, with no changes to its cleaning logic or mtime definition. This mirrors the one
call-shape in this codebase with direct evidence of reliable execution (`run_static_precheck`'s
agent-prompt Step 0), rather than adding a second orchestrator-`.js` block in the same failure-prone
shape as the checkpoint whose total non-execution this ticket's investigation confirmed. Root cause
(investigation.md) and design rationale (plan.md Design Decisions 1-3) are both recorded in
`staging_artifacts/TCK-20260714-DATA-RUNS-VERIFY-REGEN/`. `implement-ticket.js` and `SKILL.md` were
deliberately not modified — see Implementation Notes' divergence callout, accepted at Plan/Review. No
material gaps: AC7 (5-run zero-Verify-failure follow-up signal) is explicitly a post-closure retro
tracking item per the ticket's own wording, not a closure gate. Candidate future tickets (repairing the
post-Test checkpoint's own execution; constraining Parity/Verify re-verification commands to avoid
regenerating `data/runs/` artifacts) were identified but explicitly not undertaken, per plan.md Design
Decision 3 and the Anti-Drift Notes.
