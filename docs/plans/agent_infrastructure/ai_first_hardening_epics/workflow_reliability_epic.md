---
status: active
layer: ai
authority: P1
audience: agent
date: 2026-09-04
tags: [ai, agent-monitoring, hooks]
---

# Epic Plan — Workflow Reliability

**Tracking ticket**: not yet created (planning stage — detail plan and milestones only).
**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3, Bucket A / Horizon 1 item
"Migrate the 2 remaining sidecar stragglers" (quoted verbatim from the frozen proposal; corrected
during the 2026-09-04 `create-tickets` investigation pass to 1 remaining straggler, then shipped
the same day by `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` — see the Problem section below),
plus two Bucket-B members of the same epic grouping ("Ticket-claim DETECTION logging",
"Phase-level workflow resume (design phase)").
**Roadmap**: `roadmap.md` — Horizon 1. M1 has **no dependency** on the Horizon-0 exit gate
(`governance_capability_policy_epic.md`/`guardrail_enforcement_epic.md`) and may start in parallel
with Horizon 0, capacity allowing — the horizon label reflects strategic staging, not a hard
execution-order constraint. The one real coordination point with Horizon-0 work is file-level, not
architectural: M1 and Epic G's M4 may both touch `.claude/settings.json`'s `hooks` block, resolved
by a normal rebase at merge time (see `roadmap.md`'s Git &amp; delivery process section), not by
sequencing M1 after Epic G.
**Priority**: P1 — the sidecar member is Bucket A (committed); the other two are Bucket B
(experiment/design), correctly not committed to a ticket yet per the freeze verdict.

## Problem

Three related run-state reliability gaps, all touching the same mechanism — the
`.claude/current_run` sidecar and the ticket-lifecycle state it represents:

1. **The cross-session sidecar fix is real but only partially shipped.** *(Fully shipped as of
   2026-09-04 — see the M1 status note below; left in past tense as the historical record of the
   gap this epic tracked.)*
   `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` added a session-scoped
   `.claude/current_run.<SESSION_ID>` variant specifically because the old unscoped file was
   "silently overwritten by every concurrent session's own `writeSidecar()` call, misattributing
   `tools.jsonl` rows across sessions" (comment at `implement-ticket.js:264-272`). Two known
   consumers were originally left reading the old, racy unscoped file: `tools/retrieval_cache.py`
   (`_CURRENT_RUN_SIDECAR_PATH = Path(".claude/current_run")`, feeding `read_current_run_sidecar()`)
   and the inline `PreToolUse` sidecar-check hook in `.claude/settings.json` (line 88, reads
   `.claude/current_run` directly via a `python3 -c` one-liner). **Revised during the 2026-09-04
   `create-tickets` investigation pass (PR #124)**: `tools/retrieval_cache.py`'s
   `read_current_run_sidecar()` was already migrated to the scoped-then-unscoped-fallback pattern
   by `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY` (closed the same day, 2026-08-24) — confirmed by
   direct read of the current source, which already prefers `.claude/current_run.<CLAUDE_CODE_SESSION_ID>`
   when it exists. Only one straggler genuinely remained: the `.claude/settings.json` inline hook —
   migrated the same day by `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE`, closing this gap
   entirely.
2. **No repo-level protection exists against two sessions claiming the same ticket.**
   `tickets/inprogress/` is a plain directory with no claim/reservation record. 5 worktrees were
   live at review time, all coordinated by convention only (CLAUDE.md's Worktree & Branch
   Isolation section), not by any mechanism that would actually stop a double-claim.
3. **A crash mid-phase has no automatic resume — a human must manually re-diagnose.**
   `implement-ticket.js`'s resume today is ticket-ID re-invocation from Scope, not phase-level
   state restoration, even though the sidecar already records enough (`run_id/seq/phase/agent/
   execution_id/provider`) to know which phase a crashed run was in.

## Scope

### M1 — Migrate the 1 remaining sidecar straggler (gated on nothing; Bucket A, committed) — **SHIPPED** (`TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE`, 2026-09-04)

Moved the one genuinely remaining consumer from the unscoped `.claude/current_run` to the
session-scoped `.claude/current_run.<SESSION_ID>` path, finishing the fix
`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` left partial:
- The inline `PreToolUse` Edit|Write-matcher hook in `.claude/settings.json` (line 88) — its
  embedded `python3 -c` snippet now resolves the session-scoped path (`CLAUDE_CODE_SESSION_ID` env
  var, via `os.environ.get`) the same way `implement-ticket.js` and `tools/retrieval_cache.py`
  already do, falling back to the unscoped file when the scoped one doesn't exist, rather than
  reading the shared unscoped file directly.

`tools/retrieval_cache.py`'s `read_current_run_sidecar()` / `_CURRENT_RUN_SIDECAR_PATH` is **not**
in scope — confirmed already migrated by `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY` (see the
Problem section above). Re-touching it would be duplicate effort against already-correct code.

This is the only Bucket-A (committed) member of this epic — the other two milestones below are
design/measurement work, not implementation, and are explicitly **not** committed to a ticket at
this stage.

### M2 — Ticket-claim detection logging (Bucket B — experiment/measurement) — **INSTRUMENTATION SHIPPED** (`TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING`, 2026-09-07); 30-day/quarter decision gate still open

Per the freeze verdict's §77 "detect before prevent" principle and the frozen proposal's own kill
criteria: add **log-only** instrumentation that flags when two sessions touch the same ticket ID
within a short window — no blocking, no lock file, just a detection signal. Decision gate,
explicit: build an actual claim lock only if real double-claim incidents are observed within 30
days of this instrumentation going live. If zero incidents surface after a full quarter, downgrade
this from "build a lock" to "keep as documented convention" rather than shipping unused
infrastructure (frozen proposal, kill criteria).

This became an Experiment Specification (Hypothesis/Baseline/Method/Metrics/Exit/Kill Criteria)
before any ticket was written, per the freeze verdict's Bucket-B handoff boundary — see
`ticket_claim_detection_experiment.md`. `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING` then
converted that spec directly into a ticket that both wrote the spec and shipped the described
log-only instrumentation (`tools/agent-monitoring/ticket_claim_detection.py`, wired into
`implement-ticket.js`'s Scope phase): reading the real
`.claude/current_run.<CLAUDE_CODE_SESSION_ID>` sidecar signal named above, writing detections to
`agent-monitoring/data/YYYY-Www/claim_detections.jsonl`, never blocking. Only the 30-day/quarter
observation window and the resulting lock-vs-convention decision remain open — that decision is
explicitly out of scope for the shipping ticket itself.

**Ownership/lifecycle row:** see docs/guidelines/subsystem_ownership_lifecycle.md for this
subsystem's accountable role, update trigger, staleness signal, and removal condition — not
restated here.

### M3 — Phase-level workflow resume: design/validation-rule resolution (Bucket B — design work, not a committed ticket) — **RESOLVED** (`TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN`, 2026-09-07)

Before any resume logic is written, resolve the resume-semantics validation rule the freeze pass
required (§76): a checkpoint is reusable only if `workflow_version` matches, the input a phase
consumed is unchanged (`input_hash`), and every artifact that phase produced still exists on disk
— prefer this minimum sufficient set; add `source_revision`/`phase_version` only if this design
work finds them materially necessary. Invariant to hold once implemented: `checkpoint exists +
checkpoint still valid = safe to reuse` — never `checkpoint exists = skip phase`.

This is design-resolution work, not implementation — it produces the validation rule
`implement-ticket.js` would need, not the resume code itself.

**Resolved by `docs/ai/phase_resume_validation_rule_decision.md`**: confirms today's baseline is
ticket-ID re-invocation from Scope with no phase-level checkpoint anywhere (direct read of
`implement-ticket.js`/`SKILL.md`); confirms the epic's proposed minimum field set
(`workflow_version` + `input_hash` + per-phase-artifact-existence) is sufficient and that
`source_revision`/`phase_version` are **not** materially necessary; confirms
`agent-orchestration/workflows/implement-ticket.yaml`'s existing `workflow_version` field can be
reused as-is (same consumer pattern as `tools/agent_codex_runtime_shadow/matrix.py`'s own
staleness check) rather than forking a distinct field; identifies that `workflow_version` and
`input_hash` both need new `runs.jsonl`/`events.jsonl` fields (neither is recorded today, per
`docs/agent-monitoring/schema.md`), while artifact-existence needs no new recorded field (a live
filesystem check suffices); states the earliest-invalidated-phase restart fallback; and states the
audit-trail requirement (a new closed-vocabulary `reason_code`-family value distinguishing
checkpoint-reused from each invalidation cause) as a requirement for the future implementation
ticket to build, not something this design work builds itself.

**M3 is now eligible to move from Bucket B into a future Bucket-A ticket** — the design/validation-
rule resolution this milestone required is complete, but the phase-level resume implementation
itself is still future work, not scoped by this resolution.

## Out of scope

- Building an actual ticket-claim lock now — M2 explicitly ships detection only; the lock itself
  is contingent on real incident evidence M2 has not yet produced.
- Writing the phase-resume implementation itself — M3 resolves the design question only.
- Any change to how `.claude/current_run` sidecars are *written* (only which path M1's two
  consumers *read* changes) — the write-side session-scoping already shipped under
  `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`.

## Acceptance signal for this epic

- M1: **met.** The `.claude/settings.json` inline hook reads from the session-scoped sidecar path
  (matching `tools/retrieval_cache.py`'s already-shipped behavior); a synthetic two-session
  scenario (`tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py::test_two_concurrent_sessions_resolve_to_their_own_run_id`)
  confirms it no longer shows cross-session attribution bleed in `tools.jsonl` for this consumer.
- M2: **instrumentation met, decision gate open.** Detection logging is live
  (`TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING`); after 30 days/a full quarter, either a real
  incident triggered the lock-build decision, or zero incidents confirm the convention-only
  approach stands.
- M3: **met.** A written resume-semantics validation rule exists
  (`docs/ai/phase_resume_validation_rule_decision.md`), ready to hand to a future implementation
  ticket — not yet that ticket itself.

## References

- `roadmap.md` — Horizon-1 placement and relationship to the Horizon-0 exit gate.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` — §"Change coupling & epic boundaries" (this
  epic's grouping is named directly there, matching the addendum's own worked example), §"Resume
  semantics, not just resume mechanics", Automation boundary analysis (phase resume row).
- `implement-ticket.js:264-292` — the partial sidecar fix this epic's M1 finishes.
- `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY` (done, 2026-08-24) — already migrated
  `tools/retrieval_cache.py`'s consumer; confirms M1 had only one real remaining target.
- `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` (done, 2026-09-04) — shipped M1, migrating the
  `.claude/settings.json` inline hook and closing this epic's sidecar-straggler gap entirely.
- `.claude/settings.json:88` — the one remaining straggler consumer (inline hook).
- `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` — the ticket this milestone was scoped into during
  the 2026-09-04 `create-tickets` pass, reflecting the single-consumer correction above.
- `tickets/inprogress/` — the plain directory M2's detection logging instruments.
- `docs/ai/phase_resume_validation_rule_decision.md` — M3's resolved design/validation-rule
  decision doc (`TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN`, 2026-09-07).
- `ticket_claim_detection_experiment.md` — M2's Experiment Specification, and
  `TCK-20260907-TICKET-CLAIM-DETECTION-LOGGING` (done, 2026-09-07) — shipped M2's log-only
  instrumentation (`tools/agent-monitoring/ticket_claim_detection.py`), leaving only the 30-day/
  quarter decision gate open.
