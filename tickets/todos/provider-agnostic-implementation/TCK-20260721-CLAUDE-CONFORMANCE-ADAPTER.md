---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER
phase: open
date: 2026-07-21
tags: []
---

# TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER

## Title
Claude contract conformance adapter and tests, with no behavior change

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Generate a read-only Claude adapter representation from the canonical contract and diff it against the existing live .claude/workflows/implement-ticket.js behavior; any mismatch must be logged as an intentional divergence and human-approved, while the live Claude pipeline stays authoritative and unchanged until shadow parity is proven. This matters because the Provider-Adapter Boundary bars adapters from redefining phases/statuses/gates/artifacts, and Phase 1's exit criteria requires every divergence to be intentional and reviewed with no live workflow behavior change.

## Scope
- Build a read-only generator that renders a Claude adapter representation from the canonical contract (from the orchestration-contract-core ticket)
- Build a conformance test extracting the LIVE phase order from .claude/workflows/implement-ticket.js's meta.phases block (reusing workflow_meta_conformance.py's extraction approach) and asserting it is byte-identical to the rendered representation
- Build a conformance test extracting the LIVE terminal-status vocabulary (every writeMonitoring('STATUS') literal, ~13 call sites + 2 verdict-derived) and asserting full representation against the contract
- Define an operational meaning of "human-approved" divergence (e.g. required reviewer/date field format) enforced by the conformance test
- Create agent-orchestration/intentional-divergences.md (new file, distinct from docs/guidelines/intentional_divergences.md) to log any mismatch with an explicit human-approval marker
- Add an AST-based test asserting zero write-mode file opens / subprocess calls against implement-ticket.js by the generator/conformance tooling

## Out of Scope
- Does not modify .claude/workflows/implement-ticket.js or change any live Claude pipeline behavior
- Does not write to docs/guidelines/intentional_divergences.md (the existing mechanics-bible log) — divergences from this ticket go only in the new agent-orchestration/intentional-divergences.md
- Does not implement the Codex-side adapter (owned by the Codex guidance/fixture-capture and Codex replay tickets)

## Acceptance Criteria
- [ ] Read-only generator renders a Claude adapter representation from the contract; running it produces zero git diff under .claude/ before/after
- [ ] Conformance test extracts the LIVE phase order from implement-ticket.js's meta.phases block and asserts byte-identical match to the rendered representation
- [ ] Conformance test extracts the LIVE terminal-status vocabulary (all writeMonitoring('STATUS') call sites, ~13 literal + 2 verdict-derived) and asserts full match to the contract's status representation
- [ ] Any mismatch between live behavior and the rendered representation fails the test UNLESS a matching entry exists in agent-orchestration/intentional-divergences.md (the new file, explicitly distinguished from docs/guidelines/intentional_divergences.md) carrying an explicit human-approval marker (e.g. reviewer + date field) parsed and enforced by the test
- [ ] AST-based test asserts zero write-mode file opens and zero subprocess calls against implement-ticket.js by any tool built in this ticket
- [ ] Every divergence found during this ticket's own build is intentional and reviewed before the ticket closes

## Related Tickets
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK
- TCK-20260720-GATE-CHECK-WIRING-DECISIONS

## Related Docs
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/replay_fixture_spec.md
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/replay_fixture_spec.md
- docs/guidelines/intentional_divergences.md
- tools/agent_replay/runner.py
- tools/agent_replay/fixture_envelope.py
- tools/gate_checks/workflow_meta_conformance.py
- tests/agent_replay/test_runner_no_forbidden_calls.py
- tests/agent_replay/test_no_mutation_snapshot.py
- tests/tools/test_workflow_meta_conformance.py

## Assumptions / Open Questions
- Hard dependency on the orchestration-contract-core ticket delivering agent-orchestration/ first — this ticket cannot start meaningfully until that lands
- "Human-approved" enforcement mechanism (reviewer/date field format, where it's recorded) is not yet defined anywhere in the repo — this ticket's Plan phase must define it, not assume an existing convention
- Terminal-status vocabulary extraction reliability (~13 scattered string literals) is flagged as the largest implementation risk; exact extraction technique to be resolved during Investigate/Plan
- `layer: ai` used per docs/guidelines/layer_registry.jsonl ("Claude agent/orchestration tooling") since this ticket builds Claude-adapter/conformance tooling, not gameplay cognition

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
