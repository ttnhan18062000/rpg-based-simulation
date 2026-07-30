---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260730-CODEX-RUNTIME-SHADOW
phase: open
date: 2026-07-30
tags: [ai, workflows, testing, process-improvement]
---

# TCK-20260730-CODEX-RUNTIME-SHADOW

## Title
Implement the minimal Codex ticket runtime and contained shadow parity

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Create a narrow, machine-checkable Codex `implement-ticket` runtime adapter and prove it in scratch/shadow mode. The existing Codex replay adapter is deterministic Scope-to-Review fixture replay only; it must not be relabeled as a live ticket runtime. This ticket establishes exactly which phases and tiers the first runtime supports, rejects everything else, and produces parity evidence before any pilot can be considered.

## Scope
- Define a dedicated runtime adapter package from `agent-orchestration/workflows/implement-ticket.yaml`, separate from the replay and pilot-guardrail packages.
- Support only a deliberately selected initial phase/tier slice; reject unsupported phases, tiers, and contract versions clearly rather than implying full Claude parity.
- Map a real ticket-shaped input through machine-checkable phase transition, gate, and required-artifact records in a scratch/shadow environment.
- Compare Codex output against the canonical fixture/runner for phase order, final status, gate result, and required artifacts. A mismatch requires a ratified intentional divergence before it is accepted.
- Add containment checks proving the shadow path creates no repository ticket/config mutation and no `provider=codex` monitoring corpus record.
- Preserve Claude as the default production executor and leave committed `.codex/config.toml` hook-free.

## Out of Scope
- A live ticket implementation, ticket ownership/finalization, autonomous execution, or a production cutover.
- Treating the existing Scope-to-Review replay result as evidence of complete runtime parity.
- A real hook registration, paid Codex invocation, or production monitoring write.
- Weakening current replay containment or pilot guardrail protections.

## Acceptance Criteria
- [ ] The adapter has an explicit supported phase/tier matrix and deterministically rejects unsupported input.
- [ ] Contract-version, phase-order, required-gate, and required-artifact validation are machine-checkable and covered by tests.
- [ ] Scratch/shadow comparison validates phase order, final status, gate result, and artifacts against canonical fixture evidence; mismatches fail unless a matching RATIFIED divergence exists.
- [ ] Process-level containment tests prove no unexpected ticket, monitoring, or committed config mutation and no real `provider=codex` corpus record.
- [ ] Existing replay and pilot suites remain green, with consent-gated skips still classified as authorization gates rather than successful live runtime evidence.

## Related Tickets
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (parent)
- TCK-20260730-PROVIDER-HOOK-POLICY (must complete first)
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY (must complete first)
- TCK-20260730-CODEX-POSTTOOL-ADAPTER (must complete first)
- TCK-20260721-CODEX-REPLAY-PARITY (DONE; limited replay predecessor)

## Related Docs
- docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md
- agent-orchestration/workflows/implement-ticket.yaml
- agent-orchestration/intentional-divergences.md
- docs/ai/replay_fixture_spec.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- agent-orchestration/workflows/implement-ticket.yaml
- tools/agent_replay_codex/
- tools/agent_codex_pilot_guardrails/
- tests/agent_replay_codex/
- tests/fixtures/agent_replay/
- .codex/config.toml

## Assumptions / Open Questions
- Investigate must select the smallest useful phase/tier slice and document every intentionally unsupported lifecycle feature.
- The adapter package name is provisional; it must remain clearly distinct from `tools/agent_replay_codex/` and `tools/agent_codex_pilot_guardrails/`.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
