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
during the 2026-09-04 `create-tickets` investigation pass to 1 remaining straggler — see the
Problem section below), plus two Bucket-B members of the same epic grouping ("Ticket-claim
DETECTION logging", "Phase-level workflow resume (design phase)").
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

1. **The cross-session sidecar fix is real but only partially shipped.**
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
   when it exists. Only one straggler genuinely remains: the `.claude/settings.json` inline hook.
2. **No repo-level protection exists against two sessions claiming the same ticket.**
   `tickets/inprogress/` is a plain directory with no claim/reservation record. 5 worktrees were
   live at review time, all coordinated by convention only (CLAUDE.md's Worktree & Branch
   Isolation section), not by any mechanism that would actually stop a double-claim.
3. **A crash mid-phase has no automatic resume — a human must manually re-diagnose.**
   `implement-ticket.js`'s resume today is ticket-ID re-invocation from Scope, not phase-level
   state restoration, even though the sidecar already records enough (`run_id/seq/phase/agent/
   execution_id/provider`) to know which phase a crashed run was in.

## Scope

### M1 — Migrate the 1 remaining sidecar straggler (gated on nothing; Bucket A, committed)

Move the one genuinely remaining consumer from the unscoped `.claude/current_run` to the
session-scoped `.claude/current_run.<SESSION_ID>` path, finishing the fix
`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` left partial:
- The inline `PreToolUse` Edit|Write-matcher hook in `.claude/settings.json` (line 88) — update its
  embedded `python3 -c` snippet to resolve the session-scoped path (`CLAUDE_CODE_SESSION_ID` env
  var) the same way `implement-ticket.js` and `tools/retrieval_cache.py` already do, rather than
  reading the shared file directly.

`tools/retrieval_cache.py`'s `read_current_run_sidecar()` / `_CURRENT_RUN_SIDECAR_PATH` is **not**
in scope — confirmed already migrated by `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY` (see the
Problem section above). Re-touching it would be duplicate effort against already-correct code.

This is the only Bucket-A (committed) member of this epic — the other two milestones below are
design/measurement work, not implementation, and are explicitly **not** committed to a ticket at
this stage.

### M2 — Ticket-claim detection logging (Bucket B — experiment/measurement, not a committed ticket)

Per the freeze verdict's §77 "detect before prevent" principle and the frozen proposal's own kill
criteria: add **log-only** instrumentation that flags when two sessions touch the same ticket ID
within a short window — no blocking, no lock file, just a detection signal. Decision gate,
explicit: build an actual claim lock only if real double-claim incidents are observed within 30
days of this instrumentation going live. If zero incidents surface after a full quarter, downgrade
this from "build a lock" to "keep as documented convention" rather than shipping unused
infrastructure (frozen proposal, kill criteria).

This becomes an Experiment Specification (Hypothesis/Baseline/Method/Metrics/Exit/Kill Criteria)
before any ticket is written — not sketched further here; see the freeze verdict's Bucket-B
handoff boundary.

### M3 — Phase-level workflow resume: design/validation-rule resolution (Bucket B — design work, not a committed ticket)

Before any resume logic is written, resolve the resume-semantics validation rule the freeze pass
required (§76): a checkpoint is reusable only if `workflow_version` matches, the input a phase
consumed is unchanged (`input_hash`), and every artifact that phase produced still exists on disk
— prefer this minimum sufficient set; add `source_revision`/`phase_version` only if this design
work finds them materially necessary. Invariant to hold once implemented: `checkpoint exists +
checkpoint still valid = safe to reuse` — never `checkpoint exists = skip phase`.

This is design-resolution work, not implementation — it produces the validation rule
`implement-ticket.js` would need, not the resume code itself. Once resolved, it becomes eligible
to move from Bucket B into a future Bucket-A ticket; it is not there yet.

## Out of scope

- Building an actual ticket-claim lock now — M2 explicitly ships detection only; the lock itself
  is contingent on real incident evidence M2 has not yet produced.
- Writing the phase-resume implementation itself — M3 resolves the design question only.
- Any change to how `.claude/current_run` sidecars are *written* (only which path M1's two
  consumers *read* changes) — the write-side session-scoping already shipped under
  `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`.

## Acceptance signal for this epic

- M1: the `.claude/settings.json` inline hook reads from the session-scoped sidecar path (matching
  `tools/retrieval_cache.py`'s already-shipped behavior); a synthetic two-session scenario no
  longer shows cross-session attribution bleed in `tools.jsonl` for this consumer.
- M2: detection logging is live; after 30 days, either a real incident triggered the lock-build
  decision, or zero incidents confirm the convention-only approach stands.
- M3: a written resume-semantics validation rule exists, reviewed, ready to hand to a future
  implementation ticket — not yet that ticket itself.

## References

- `roadmap.md` — Horizon-1 placement and relationship to the Horizon-0 exit gate.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` — §"Change coupling & epic boundaries" (this
  epic's grouping is named directly there, matching the addendum's own worked example), §"Resume
  semantics, not just resume mechanics", Automation boundary analysis (phase resume row).
- `implement-ticket.js:264-292` — the partial sidecar fix this epic's M1 finishes.
- `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY` (done, 2026-08-24) — already migrated
  `tools/retrieval_cache.py`'s consumer; confirms M1 has only one real remaining target.
- `.claude/settings.json:88` — the one remaining straggler consumer (inline hook).
- `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` — the ticket this milestone was scoped into during
  the 2026-09-04 `create-tickets` pass, reflecting the single-consumer correction above.
- `tickets/inprogress/` — the plain directory M2's detection logging instruments.
