---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT
phase: done
date: 2026-07-10
tags: []
---

# TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT

## Title
Add orchestrator-side enforcement for verified_by provenance Step 0 compliance, starting with mechanics-auditor

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
The `verified_by` field should stop relying purely on an agent honestly self-reporting that it ran its Step 0 static check before rendering a verdict. This ticket implements the concern raised in `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`, which names mechanics-auditor as the weakest instance of this problem: `docs/ai/agents.md` explicitly admits it "has no orchestrator-side enforcement... compliance depends entirely on the agent actually running the script and citing it honestly." This concern asks for orchestrator-side enforcement of `verified_by` provenance, starting with mechanics-auditor, mirroring the `bash()`-runs-static-check-before-`agent()` pattern already used for Architecture-Verify.

## Scope
- Resolve, explicitly and in writing (not implicitly), whether mechanics-auditor gets a new orchestrator call site (e.g. a standalone wrapper script, since it has no JS workflow host today — it is invoked ad hoc via `Agent(subagent_type: "mechanics-auditor")` outside any pipeline), or whether enforcement takes a different form (e.g. a post-hoc audit of past `verified_by` claims against the static check's own output).
- This must directly address that TCK-20260705-GATE-DET-MECHANICS-AUDITOR's own Implementation Notes explicitly ruled out adding an `Agent(subagent_type: mechanics-auditor)` call site to `implement-ticket.js` as "out of scope per the plan and ticket" — this ticket must either justify overturning that prior explicit scope decision (with Architecture-Review sign-off) or design a non-call-site enforcement mechanism instead.
- If a call site/wrapper is added, the static check result (`tools/gate_checks/mechanics_auditor_static.py`) must be computed before the agent renders its verdict and injected as context, mirroring `implement-ticket.js`'s Architecture-Verify phase pattern (lines 560-613).
- The agent's `verified_by` self-report must then be cross-checked post-hoc against the orchestrator-computed static result.

## Out of Scope
- C1 (tool_call_count/cost_proxy_score sidecar registration) — separate ticket TCK-20260710-CURRENT-RUN-SIDECAR-BASH, different field, different files.
- C2 (per-phase ts capture) — separate ticket TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH, different field.
- Extending this same enforcement mechanism to the other three verified_by-producing gates (done-checker, architecture-reviewer, parity-updater) beyond what's needed to design a reusable pattern — mechanics-auditor is the explicit starting instance; broader rollout is a follow-up.
- The 4 "related, smaller ideas" from `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`: (1) asymmetric gate coverage beyond the security tag, (2) cross-retro trend detection, (3) duplicated tag-to-skill mapping logic consolidation, (4) working_log.csv malformed-row normalization backfill.
- Reopening or modifying the scope of TCK-20260705-GATE-DET-MECHANICS-AUDITOR itself — this ticket supersedes/extends its explicit "out of scope" ruling for a new call site, it does not amend that ticket's own closed record.

## Acceptance Criteria
- [ ] The ticket explicitly resolves whether mechanics-auditor gets a new orchestrator call site (e.g. a standalone wrapper script) or whether enforcement takes a different form (e.g. post-hoc audit of past verified_by claims) — documented, not left implicit, given TCK-20260705-GATE-DET-MECHANICS-AUDITOR's prior explicit "out of scope" ruling.
- [ ] If a call site/wrapper is added, the static check result is computed before the agent renders its verdict and injected as context.
- [ ] The agent's verified_by self-report is cross-checked post-hoc against the orchestrator-computed static result.
- [ ] A new test demonstrates the enforcement mechanism actually detects a case where Step 0 was skipped or falsely cited.

## Related Tickets
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC
- TCK-20260705-GATE-DET-MECHANICS-AUDITOR
- TCK-20260705-GATE-DET-DONE-CHECKER
- TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER
- TCK-20260705-GATE-DET-PARITY-UPDATER
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH (sibling)
- TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH (sibling)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md
- docs/ai/agents.md
- docs/ai/ticket-lifecycle.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/agents/mechanics-auditor.md
- tools/gate_checks/mechanics_auditor_static.py
- tools/gate_checks/done_checker_static.py
- tools/gate_checks/parity_updater_static.py
- tools/gate_checks/architecture_reviewer_static.py
- .claude/workflows/implement-ticket.js
- docs/ai/agents.md
- docs/ai/skills.md
- docs/ai/workflows.md
- docs/ai/system_overview.md
- docs/ai/ticket-lifecycle.md
- tests/tools/test_mechanics_auditor_static.py

## Assumptions / Open Questions
- mechanics-auditor has zero pipeline call sites anywhere (confirmed across 4 docs) — it's invoked ad hoc via `Agent(subagent_type: "mechanics-auditor")` directly, so the standard `bash()`-before-`agent()` pattern used elsewhere has no natural host location; this must be designed, not assumed to be a direct port.
- Adding a new call site would reverse TCK-20260705-GATE-DET-MECHANICS-AUDITOR's explicit prior scope decision — requires Architecture-Review sign-off before implementation, not just implementer discretion.
- Open question left to Scope/Plan phase: whether the eventual mechanism generalizes cleanly to the other three verified_by-producing gates or is mechanics-auditor-specific due to its lack of a JS workflow host.

## Implementation Notes

1. **Design (b) was chosen and implemented.** Added `audit_verified_by_claims(rows, ledger_dir,
   base_dir) -> list[dict]` to `tools/gate_checks/mechanics_auditor_static.py`. No
   `Agent(subagent_type: "mechanics-auditor")` call site was added to `implement-ticket.js`
   (confirmed zero matches for `mechanics-auditor|mechanics_auditor` in that file both before and
   after this ticket, via `grep`; `implement-ticket.js` was not edited by this ticket at all — its
   working-tree modifications, present at session start, come from sibling tickets in this same
   epic and were left untouched).

2. **Why this does not reopen or amend `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s closed record:**
   that ticket's ruling was scoped narrowly and explicitly to "no new call site in
   `implement-ticket.js`" (its plan.md Summary and Implementation Notes, quoted verbatim in this
   ticket's own `investigation.md`, Prior Work section). Design (b) adds zero call sites anywhere —
   it is a new, independent function in a module that ticket already built, addressing a question
   (post-hoc honesty cross-check of an agent's own self-report) that ticket never posed or ruled on.
   The prior ruling remains correct and untouched; this ticket does not amend, supersede in
   substance, or require Architecture-Review sign-off to overturn it, because nothing about "no call
   site" was reversed. `tickets/done/TCK-20260705-GATE-DET-MECHANICS-AUDITOR.md` and its
   `stored_artifacts/` were not touched by this ticket (confirmed via `git status`).

3. **AC #2** ("if a call site/wrapper is added, the static check result is computed before the agent
   renders its verdict and injected as context") is satisfied **vacuously** — no call site/wrapper
   was added, so its precondition never triggers. The closest functional analogue — a static result
   computed and made available for comparison — is delivered by `audit_verified_by_claims`'s internal
   recompute-and-compare step, just without an agent-prompt injection point, since no agent-prompt
   call site exists to inject into.

4. **AC #3** ("the agent's verified_by self-report is cross-checked post-hoc against the
   orchestrator-computed static result") is satisfied directly: `audit_verified_by_claims` takes the
   agent's self-reported rows and independently recomputes the static result (`verify_entry_test_path`)
   for comparison, flagging a "Step 0 skipped" row (no static tag cited) or a "falsely cited" row
   (static PASS claimed but a fresh recompute disagrees with no disclosed FAIL caveat).

5. **Disclosed residual invocation gap (per plan.md Decision 2, not silently left implicit):** this
   ticket closes the **detection** gap — a deterministic, independently-tested function now exists
   that can catch a false or omitted `verified_by` claim, given the agent's own output rows — but does
   **not** close the **invocation** gap. Nothing calls `audit_verified_by_claims` automatically today;
   it requires a human reviewer or a future ticket to supply a `mechanics-auditor` session's output
   rows explicitly. Closing that gap would require a durable-capture mechanism for ad hoc agent
   output (e.g. a sidecar or JSON log of a session's Markdown table) that does not exist yet and is
   out of this ticket's scope. A future reader must not read this ticket's Title ("Add
   orchestrator-side enforcement...") as meaning the check now runs automatically in the pipeline —
   it does not; see `docs/ai/agents.md`'s `mechanics-auditor` section for the same disclosed-limitation
   paragraph, and this ticket's own Completion Summary below for the same caveat stated plainly.

6. **Output field naming.** The function's return dicts use `entry_id` / `honesty_status` / `evidence`
   only — never a key named `status` or `Status` — per plan.md Decision 3, to avoid repeating the
   exact non-override mistake `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s architecture review round 1
   already caught once. Locked in by `test_audit_never_overrides_agent_status_classification`.

## Test Summary

Added 6 tests to `tests/tools/test_mechanics_auditor_static.py`:
`test_audit_passes_honest_static_pass_claim`,
`test_audit_detects_step_0_skipped_on_verified_status_entry`,
`test_audit_detects_falsely_cited_static_pass`,
`test_audit_passes_honest_llm_only_claim_on_non_verified_status_entry`,
`test_audit_scoped_by_row_not_whole_ledger`,
`test_audit_never_overrides_agent_status_classification`.

`python3 -m pytest tests/tools/test_mechanics_auditor_static.py -v` — 17 passed (11 pre-existing + 6
new; note: plan.md's Step 9 anticipated a baseline of 16 pre-existing tests / 22 total — the actual
pre-existing count in this file at implementation time was 11, so the actual total is 17; see
plan.md's Deviations section).

`python3 -m pytest tests/tools/test_mechanics_auditor_static.py tests/tools/test_parity_updater_static.py tests/tools/test_done_checker_static.py -v`
— 79 passed, no regressions in the two sibling gate-check modules.

Negative-control greps (Step 9): `grep -n "mechanics-auditor\|mechanics_auditor" .claude/workflows/implement-ticket.js`
returned zero matches; no `Agent(subagent_type: "mechanics-auditor")` call site exists anywhere in
the repo; `git diff --stat` for `tools/gate_checks/parity_updater_static.py`,
`tools/gate_checks/done_checker_static.py`, and `.claude/agents/mechanics-auditor.md` shows no
changes from this ticket.

## Files Changed
- `tools/gate_checks/mechanics_auditor_static.py` — added `audit_verified_by_claims(rows, ledger_dir, base_dir) -> list[dict]`.
- `tests/tools/test_mechanics_auditor_static.py` — added 6 new tests covering the function's honest-pass, skip-detection, false-citation-detection, non-verified-status-skip, per-row scoping, and never-overrides-agent-status behaviors.
- `docs/ai/agents.md` — documented the new post-hoc audit function in the `mechanics-auditor` section, alongside the disclosed invocation-gap limitation.
- No changes to `.claude/workflows/implement-ticket.js`, `.claude/agents/mechanics-auditor.md`, `tools/gate_checks/parity_updater_static.py`, or `tools/gate_checks/done_checker_static.py` (confirmed via `git diff --stat` and negative-control greps in Test Summary above).

## Completion Summary
Implemented a **callable, on-demand post-hoc DETECTION capability**, not automatic pipeline
enforcement. `audit_verified_by_claims` (new function in `tools/gate_checks/mechanics_auditor_static.py`)
takes a `mechanics-auditor` session's self-reported output rows and independently recomputes each
`verified`-status ledger entry's Step 0 static-check result, flagging rows where `verified_by` omits
the static-check tag ("Step 0 skipped") or where a claimed static PASS contradicts a fresh recompute
with no disclosed FAIL caveat ("falsely cited"). It returns `entry_id` / `honesty_status` (`PASS`/
`FAIL`) / `evidence` per row — deliberately never a field named `status`/`Status`, so it can never be
mistaken for or override the agent's own PARITY/DIVERGENT/MISSING/UNDOCUMENTED classification.

No `Agent(subagent_type: "mechanics-auditor")` call site was added anywhere in the codebase, and
`.claude/workflows/implement-ticket.js` was not edited by this ticket at all — `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s
prior explicit "out of scope" ruling against a new pipeline call site stands untouched and is not
reopened or amended by this work.

**Plainly stated per architecture-review's non-blocking recommendation (confirmed followed by
done-checker):** nothing currently calls `audit_verified_by_claims` automatically. It is not wired
into `implement-ticket.js`, any hook, or any other orchestrator control flow. A human reviewer or a
future ticket must invoke it explicitly, supplying a `mechanics-auditor` session's output rows by
hand. This ticket's Title ("Add orchestrator-side enforcement...") should be read narrowly: it adds
the *mechanism* that makes such enforcement possible on demand, not an automatic gate that runs on
every mechanics-auditor invocation. Closing the remaining invocation gap (durably capturing an ad hoc
agent session's output rows so this function could be wired in automatically) is out of this
ticket's scope and is called out as a residual gap in Implementation Notes item 5 above.

Tests: 6 new tests added to `tests/tools/test_mechanics_auditor_static.py` (17 total in that file, all
passing); no regressions in `test_parity_updater_static.py` / `test_done_checker_static.py` (79 tests
total across the three files, all passing).
