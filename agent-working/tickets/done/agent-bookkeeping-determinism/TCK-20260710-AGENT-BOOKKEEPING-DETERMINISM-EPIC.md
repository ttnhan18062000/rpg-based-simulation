---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC
phase: done
date: 2026-07-10
tags: [ai, agent-monitoring, determinism, data-quality]
---

# TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC

## Title
Move agent-prompt "remember to do this mechanical thing" bookkeeping to orchestrator-side determinism — epic tracking 3 child tickets

## Status
OPEN

## Tier
epic

## Type
chore

## Priority
P2

## Request Summary
This epic implements `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md` (raised
2026-07-10, maturity "IDEA — not scheduled"). The idea doc's Problem section documents that
`TCK-20260709-AGENT-MONITORING-DURATION` diagnosed and fixed one instance of a general failure mode —
`duration_s` was documented as a required run-record field but was never actually computed, because
every caller was expected to compute and pass it and none did; the fix moved computation into
`record_run.py` itself, at write time, removing the dependency on caller correctness. The idea doc
argues the same failure mode still exists, unfixed, one layer up: `tool_call_count`/`cost_proxy_score`
attribution depends on every agent prompt's "Step 0b" sidecar-write instruction
(`.claude/current_run` registration) being executed literally, verbatim, by the agent itself as its
first action — and this was reproduced live in the same session while manually orchestrating
`TCK-20260710-SECURITY-REVIEWER-AGENT-DOC`: the Step 0b instruction was omitted from all 5 agent
prompts issued, and every event for that run silently wrote `tool_call_count: 0, cost_proxy_score: 0.0`
— indistinguishable from a genuine zero-tool-call event, with no error or warning anywhere in the
pipeline. The idea doc's "Where this pattern already shows up" table names three further instances of
the same anti-pattern (agent-prompt text carrying a purely mechanical instruction whose correctness
depends on the agent reproducing it) beyond the already-fixed `duration_s` case; this epic tracks one
child ticket per remaining instance. This epic itself performs no direct implementation — per
CLAUDE.md's Tier Routing table, `epic` tier is Scope only, tracking child tickets created separately
via the create-tickets workflow.

## Scope
Track the following 3 child tickets, to be created next via the create-tickets workflow, each
implementing one row of the idea doc's "Where this pattern already shows up" table:

1. **Sidecar registration determinism.** Move `.claude/current_run` sidecar registration
   (`tool_call_count`/`cost_proxy_score` attribution) from agent-prompt "Step 0b" instructions to
   orchestrator-side `bash()` calls in `.claude/workflows/implement-ticket.js` (confirmed ~9 Step 0b
   sites at lines 350, 393, 455, 526, 597, 660, 811, 905, 970, plus a variant at line 1025) —
   mirroring the existing orchestrator-side `bash()` pattern already used ahead of the Parity phase's
   `p0ScanOutput` and Architecture-Verify's static pre-check. Also check
   `.claude/workflows/implement-epic.js` (confirmed: 3 Step 0 sites at lines 66, 99, 124, none of
   which register a `.claude/current_run` sidecar at all today) and
   `.claude/workflows/create-tickets.js` (confirmed: 1 Step 0 site at line 157, no sidecar
   registration — `docs/agent-monitoring/schema.md:185` already documents `tool_call_count` as always
   `null` there) for the same gap, and decide/document whether that's an intentional scope boundary
   or the same unfixed gap.
2. **Per-phase timestamp capture determinism.** Same treatment for per-phase `ts` capture
   (agent-prompt "Step 0" `date -u ...` instructions, agent must echo it back as the first line of its
   response) — move to orchestrator-side capture where feasible. Lower stakes than (1) today per the
   idea doc (`generate_retro.py`'s Slow Runs/Avg Duration sections read `runs.jsonl`'s `duration_s`,
   not per-phase `ts`), but the same class of bug.
3. **`verified_by` orchestrator-side enforcement for mechanics-auditor.** Add orchestrator-side
   enforcement for mechanics-auditor's Step 0 `verified_by` self-report compliance. Per
   `.claude/agents/mechanics-auditor.md:53-54`, this Step 0 "has no orchestrator-side enforcement...
   compliance depends entirely on the agent actually running the script and citing it honestly" —
   unlike done-checker/parity-updater/architecture-reviewer's static pre-checks, which the
   orchestrator runs and independently verifies (per `TCK-20260705-GATE-DET-MECHANICS-AUDITOR`'s own
   Implementation Notes: "no `Agent(subagent_type: "mechanics-auditor")` call site was added to
   `implement-ticket.js`... adding one is explicitly out of scope"). This child ticket must confirm
   whether mechanics-auditor has any pipeline call site to enforce against, or whether enforcement
   means something else (e.g. a standalone post-hoc audit) given it's invoked ad hoc, not from within
   `implement-ticket.js`.

## Out of Scope
The idea doc's 4 "Related, smaller ideas raised in the same review" are explicitly NOT part of this
epic, per the user's decision. They remain named-but-not-ticketed follow-ups in
`docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`'s "Related, smaller ideas"
section, each requiring its own investigation before becoming a ticket:
1. Asymmetric gate coverage (only `security` tag has an enforced pipeline gate; `api-design`,
   `debugging`, `performance` map to `suggested_skills` with no compliance check).
2. Cross-retro trend detection (no automated comparison across consecutive `RETRO-<week>.md` reports).
3. Duplicated tag→skill mapping logic (independently re-implemented in at least 4 places in
   `implement-ticket.js`).
4. `working_log.csv` malformed-row normalization (83 non-canonical rows, permanently excluded via
   documented allowlists rather than cleaned up).

Also out of scope for this epic itself (belongs to its child tickets, not here): any direct code
change to `.claude/workflows/*.js`, `.claude/agents/mechanics-auditor.md`, or
`tools/gate_checks/mechanics_auditor_static.py`; any change to `tools/agent-monitoring/record_events.py`
(the idea doc confirms no change is needed there — the fix is entirely about how reliably the
orchestrator computes correct values before calling it, not the write-path itself).

## Acceptance Criteria
- All 3 child tickets listed in Scope exist and are moved to `tickets/done/` (or
  `tickets/done/agent-bookkeeping-determinism/` per this folder's own convention once complete).
- `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`'s maturity banner is updated
  from "IDEA — not scheduled" to reflect this epic, once the child tickets are created (e.g.
  "SCHEDULED" or "IN PROGRESS", linking this epic's ticket ID), consistent with how sibling idea docs
  (`idea_agent_gate_determinism.md`, `idea_agent_monitoring_schema_enforcement.md`) were updated when
  their tracking epics/tickets were created.
- No child ticket introduces a change to `tools/agent-monitoring/record_events.py`'s accepted-field
  contract (per the idea doc's own "no change needed" note) unless a child ticket's own investigation
  finds and documents a specific reason to deviate.

## Related Tickets
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH
- TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH
- TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT

## Related Docs
- `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md` — the source idea doc this
  epic implements
- `docs/agent-monitoring/schema.md`
- `docs/ai/ticket-lifecycle.md`
- `docs/ai/agents.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `.claude/workflows/implement-ticket.js`
- `.claude/workflows/implement-epic.js`
- `.claude/workflows/create-tickets.js`
- `tools/gate_checks/mechanics_auditor_static.py`

## Assumptions / Open Questions
Carried forward verbatim from the idea doc's own Open Questions section, each noted with the child
ticket it maps to:
- "Is there any Step 0/0b content that genuinely needs the *agent's own* timestamp (e.g. capturing the
  moment the agent actually began reasoning, not just when the orchestrator dispatched the call) — or
  can every current instance be replaced by an orchestrator-side capture without losing meaning?" —
  maps to child ticket 2 (per-phase timestamp capture determinism).
- "For `create-tickets.js`'s already-`null` `tool_call_count`: is that a deliberate scope decision
  (documented as such in `schema.md`) or simply the same gap this idea describes, never fixed there
  because no one hit it the way this session hit the `implement-ticket` case?" — maps to child ticket
  1 (sidecar registration determinism).
- "Should the four 'related, smaller ideas' above be split into their own `idea_*.md` files before any
  of them is scheduled, following this folder's one-idea-per-file convention — or is a single combined
  follow-up ticket sufficient given none of them, on its own, is large?" — not mapped to any child
  ticket in this epic; these 4 ideas are explicitly Out of Scope here (see above) and remain
  unresolved in the idea doc pending a future, separate decision.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
