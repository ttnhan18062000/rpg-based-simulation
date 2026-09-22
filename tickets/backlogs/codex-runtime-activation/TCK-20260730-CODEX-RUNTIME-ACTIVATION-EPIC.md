---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC
phase: backlog
date: 2026-07-30
tags: [ai, workflows, hooks, agent-monitoring, process-improvement]
---

# TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC

> **Physically moved to `tickets/backlogs/codex-runtime-activation/`, 2026-09-22** — the
> `tickets/todos/` copy of this epic and its own `TCK-20260730-CODEX-CONTROLLED-PILOT.md` +
> `SEQUENCE.md` folder duplicate were superseded by that folder's own already-stale copy, so both
> now live together under `tickets/backlogs/`, matching the 2026-09-20 lifecycle decision below.

> **Moved back to the backlog, 2026-09-20, at the user's direct instruction.** This is a
> **lifecycle correction only** — the ticket had sat in `tickets/inprogress/` with no further
> activity since at least 2026-08-14 (its own last recorded content change, per `git log`; its
> own body's last dated note is 2026-08-02), and its presence there (along with several other
> stale `tickets/inprogress/` entries) was firing this repo's sidecar-check hook on every
> `Edit`/`Write` in every concurrent session on this machine. **Nothing about the ticket's own
> substance was investigated, debugged, or re-scoped as part of this move** — its Scope,
> Acceptance Criteria, and Assumptions below are exactly as they were. Anyone picking this up
> should treat it as **unstarted backlog work** and re-validate its premises first: it predates a
> large amount of change in this repo, and nothing here has been checked against the current
> state of any of that.

## Title
Controlled Codex runtime activation epic

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Turn the completed provider-agnostic foundation into a deliberately limited, auditable Codex `implement-ticket` runtime. The existing replay proof, contract, guidance, monitoring writer, and pilot guardrails are readiness mechanisms, not authorization for a live workflow. This epic sequences the missing activation work without weakening the active Claude baseline, rewriting historic monitoring records, or silently enabling a Codex hook.

## Scope
- Scope-only epic: track and sequence the five child tickets in this folder; do not implement provider runtime behavior in the parent.
- Carry forward the canonical `agent-orchestration/` contract as the semantic authority. Provider-local behavior must extend the contract before it becomes active.
- Preserve the committed `.codex/config.toml` as hook-free until the final, explicitly human-authorized pilot operation.
- Preserve historical `agent-monitoring/*.jsonl` bytes and ordering; identity fields are additive for new records only.
- Retain Claude as the default production executor until the runtime/shadow ticket has passed its contained parity evidence and the pilot has been reviewed.
- Require a distinct human decision before any paid/live Codex invocation, production hook registration, or `provider=codex` monitoring write.

## Out of Scope
- Broad Codex rollout, autonomous dispatch, or activation of workflows other than `implement-ticket`.
- Backfilling, rewriting, reordering, compacting, or deleting historical monitoring records.
- Enabling a hook, invoking Codex, or selecting a pilot candidate as part of this epic ticket itself.
- Weakening `tools/agent_codex_pilot_guardrails/`' no-live-execution-path protections.

## Acceptance Criteria
- [ ] All five child tickets are reviewed, dependency ordered, and linked below.
- [ ] Each child preserves the hook-free committed Codex configuration and historic monitoring corpus unless a later human-authorized pilot explicitly permits its narrowly defined operation.
- [ ] The implementation sequence requires policy and Claude execution identity before Codex runtime activation, and a fresh human sign-off before the pilot operation.
- [ ] The epic is not closed merely because readiness code exists; it requires reviewed evidence for every child and an explicit decision on whether to execute the final pilot.

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC (DONE; foundation predecessor)
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION (DONE; readiness confirmation)
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY
- TCK-20260730-PROVIDER-HOOK-POLICY
- TCK-20260730-CODEX-POSTTOOL-ADAPTER
- TCK-20260730-CODEX-RUNTIME-SHADOW
- TCK-20260730-CODEX-CONTROLLED-PILOT
- TCK-20260731-CODEX-PILOT-EXECUTOR (non-live prerequisite for controlled-pilot final operation)

## Related Docs
- docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md
- agent-orchestration/README.md
- agent-orchestration/intentional-divergences.md
- docs/ai/codex_capability_matrix.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- agent-orchestration/
- .claude/workflows/implement-ticket.js
- .codex/config.toml
- tools/agent_replay_codex/
- tools/agent_codex_pilot_guardrails/
- agent-monitoring/*.jsonl

## Assumptions / Open Questions
- A future live pilot remains an operational decision, not an automatic consequence of completing readiness code.
- BLOCKED pending the owner's explicit decision to run or defer the controlled pilot; it may return to INPROGRESS when that decision and any required pilot inputs are supplied.
- Linux remains the only approved platform for shared monitoring writes.
- The known unrelated stale-path test failure (`TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH`) must remain classified separately from activation regressions.
- 2026-08-02 decision: temporarily defer live Codex activation after completing and independently
  reviewing the five-ticket non-live capability chain (harness, transport, orchestration,
  entrypoint, hook command). This epic remains BLOCKED rather than closing as readiness-only;
  resumption requires a new explicit owner decision and the governed human prerequisites.

## Implementation Notes
(pending — scope-only epic)

## Test Summary
(pending — no direct tests)

## Files Changed
(pending)

## Completion Summary
(pending)
