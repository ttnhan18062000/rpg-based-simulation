---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260730-CODEX-CONTROLLED-PILOT
phase: blocked
date: 2026-07-30
tags: [ai, workflows, hooks, agent-monitoring, observability, rollback, testing]
---

# TCK-20260730-CODEX-CONTROLLED-PILOT

## Title
Conduct one human-approved, controlled Codex pilot

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Use the completed guardrails and the prior activation tickets to conduct at most one low-risk Codex pilot. The operational execution is not routine ticket automation: it is a final, explicitly human-authorized step that may use paid/live Codex and enable the minimal hook surface only after every preflight gate passes.

## Scope
- Reuse the existing pilot request, sign-off, candidate-selection, enabled-surface, baseline-manifest, and scratch rollback guardrails; do not rebuild or weaken them.
- Require all predecessor tickets to be DONE with reviewed shadow evidence, a real identity-bearing writer route, a hook policy, and a clean baseline before a candidate is eligible.
- Require a specific low-risk `pilot_requests/<ticket_id>.yaml` with human owner and rollback plan, no concurrent provider claim, and a fresh independent sign-off.
- Permit only the policy-approved enabled surface: `PostToolUse` and shared writer functions `write_line`/`write_lines`.
- Treat actual live invocation/config enablement as a named final operation requiring contemporaneous user approval; the ordinary implementation workflow must stop before it if approval is absent.
- Before and after that operation, prove monitoring prefix preservation, provider-attributed visibility in readers/dashboard, and a tested one-action rollback restoring hook-free config with no unintended ticket or monitoring changes.

## Out of Scope
- More than one pilot, a broad rollout, or activation of any other workflow.
- Any live action before the human owner supplies a candidate, rollback plan, and current sign-off.
- Setting `CODEX_REPLAY_PARITY_LIVE_CONSENT=1`, setting `CODEX_LIVE_PILOT_HUMAN_SIGNOFF=1`, creating a production hook-bearing config, or invoking Codex as part of planning, test, or ordinary implementation without that contemporaneous approval.
- Altering the no-live-execution-path invariant inside `tools/agent_codex_pilot_guardrails/`; a narrowly scoped executor boundary must be separate and reviewable.
- Historic monitoring data migration/backfill.

## Acceptance Criteria
- [ ] Preflight rejects a missing/invalid human owner, rollback plan, sign-off, eligible candidate, identity-bearing evidence, or concurrent-claim check.
- [ ] The only permitted enabled surface is exactly `PostToolUse` plus `write_line`/`write_lines`; every broader surface is rejected.
- [ ] Without explicit contemporaneous approval, no live Codex invocation or hook-bearing project config is created and the ticket remains safely blocked at the final operation.
- [ ] If approval is supplied and the pilot is run, pre/post evidence proves legacy monitoring prefix preservation, a coherent provider-attributed run, reader/dashboard visibility, and a successful one-action rollback with zero unintended ticket/config/monitoring changes.
- [ ] The pilot result and rollback evidence are reviewed before any scope expansion decision.

## Related Tickets
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (parent)
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY (must complete first)
- TCK-20260730-PROVIDER-HOOK-POLICY (must complete first)
- TCK-20260730-CODEX-POSTTOOL-ADAPTER (must complete first)
- TCK-20260730-CODEX-RUNTIME-SHADOW (must complete first)
- TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS (DONE; guardrail predecessor)

## Related Docs
- docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md
- docs/ai/monitoring_writer_decision.md
- agent-orchestration/monitoring-schema.yaml

## Related Stored Artifacts
None yet.

## Related Code Areas
- pilot_requests/
- tools/agent_codex_pilot_guardrails/
- tools/agent_replay_codex/
- tools/agent-monitoring/writer.py
- agent-monitoring/*.jsonl
- .codex/config.toml
- tests/agent_codex_pilot_guardrails/
- tests/agent_replay_codex/

## Assumptions / Open Questions
- A separate human decision is required to authorize the actual live operation even after this ticket's plan and code are approved.
- BLOCKED pending a named candidate request, human owner, rollback plan, contemporaneous sign-off, and passing preflight; it may return to INPROGRESS when those inputs are supplied.
- A later executor package may be needed, but it must not be added by weakening the guardrail package's static no-execution tests.
- 2026-08-02 decision: temporarily defer the actual pilot. The complete non-live capability chain
  is verified, but no human approval, trust review, exact config-diff sign-off, or fresh consent
  was supplied. Remain BLOCKED; the reserved candidate stays unimplemented until the owner either
  resumes a pilot decision or explicitly releases it for ordinary hotfix implementation.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
