---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS
phase: open
date: 2026-07-21
tags: []
---

# TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS

## Title
Isolated live Codex pilot with rollback guardrails

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Once replay/shadow evidence is clean, permit exactly one recoverable, low-risk live Codex ticket run: a human-owned ticket with a rollback plan and no concurrent same-work execution by both providers, only the hooks/writer already proven safe in earlier phases enabled, pre/post snapshots of the ticket and monitoring corpus required alongside normal gates, and disabling Codex afterward limited to a configuration rollback — never a data repair. This matters because this is the only concern touching genuinely irreversible-risk territory, and it is doubly blocked: on all prior phases landing, and separately on the documented .agents/skills quarantine gate.

## Scope
- Design and build a ticket-selection step that programmatically rejects candidates lacking a recorded human owner + rollback plan, or where the same ticket is concurrently claimed by both providers
- Build a rollback mechanism achievable via a single config/flag flip (Codex-adapter disable), verified by a test that performs the rollback and asserts zero bytes differ across agent-monitoring/*.jsonl and the pilot ticket file
- Build pre/post baseline-manifest capture and diff tooling for the pilot (consuming the baseline-monitoring-manifest ticket's tooling rather than rebuilding it), failing closed if any pre-existing line's hash changes
- Build an explicit, programmatically-checked human sign-off gate immediately before live pilot execution itself (not just before ticket designation) that the pilot workflow refuses to proceed without
- Restrict the enabled hook/writer set for the pilot to only what the Codex-guidance and monitoring-writer-unification tickets' evidence has proven safe, with a test enumerating the enabled set as a subset of that evidence

## Out of Scope
- Does not begin actual live pilot execution until the orchestration-contract-core, Claude-conformance-adapter, Codex-guidance-fixture-capture, monitoring-writer-unification, and Codex-replay-parity tickets have all landed and passed their own exit criteria, AND the separate legacy .agents/skills/ quarantine gate (owned by the Codex-guidance-fixture-capture ticket) is independently satisfied — this ticket's scope is limited to designing and building the guardrail/rollback/sign-off mechanisms; live execution itself remains blocked pending those preconditions
- Rollback logic never deletes output or modifies historic JSONL records — only additive quarantine or reader-side exclusion; no data-repair-via-deletion mechanism is built
- Does not re-implement baseline-manifest tooling already delivered by the baseline-monitoring-manifest ticket — this ticket consumes it

## Acceptance Criteria
- [ ] Ticket-selection step programmatically rejects candidates lacking a recorded human owner and rollback plan, verified against actual ticket/run state (not just doc convention)
- [ ] Ticket-selection step programmatically rejects a candidate that is concurrently claimed by both providers for the same work
- [ ] Only Phase-2/Phase-3-evidenced hook events are registered as enabled for the pilot; a test enumerates the enabled set as a subset of that evidence
- [ ] Pre/post baseline manifests are captured and diffed for the pilot; the pilot workflow fails closed if any pre-existing line's hash changes
- [ ] Codex-adapter disable is achievable via a single config/flag flip; a test performs the rollback and asserts zero bytes differ across agent-monitoring/*.jsonl and the pilot ticket file
- [ ] An explicit, programmatically-checked human sign-off gate exists immediately before live pilot execution (distinct from and later than ticket designation); the pilot workflow refuses to proceed without it
- [ ] This ticket's own scope explicitly states that live pilot execution is blocked pending the prior 5 tickets AND the .agents/skills quarantine gate, and that only guardrail/rollback/sign-off design-and-build work is in scope now

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-CODEX-CAPABILITY-MATRIX
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-AGENTS-DIR-DISPOSITION
- TCK-20260721-AGENTS-DISPOSITION-FIX
- TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX

## Related Docs
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/ai/agents_dir_disposition.md
- docs/ai/monitoring_writer_decision.md
- docs/ai/codex_capability_matrix.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/replay_fixture_spec.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/ai/agents_dir_disposition.md
- docs/ai/monitoring_writer_decision.md
- docs/ai/codex_capability_matrix.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/replay_fixture_spec.md
- tools/agent-monitoring/post_tool_hook.py
- tests/tools/test_monitoring_writer_lockfile_candidate.py
- tests/agent_replay/test_runner_no_forbidden_calls.py
- tests/agent_replay/test_no_mutation_snapshot.py

## Assumptions / Open Questions
- No rollback/feature-flag mechanism exists yet for agent-orchestration/Codex-adapter enablement; the only existing feature_flag precedent (src/domains/optimization/feature_flags.py) is an unrelated simulation-engine per-tick mechanism and cannot be reused as-is
- Doubly blocked: hard sequencing dependency on the 5 prior tickets all landing, plus a separate independent precondition (legacy .agents/skills/ quarantine, owned by the Codex-guidance-fixture-capture ticket) — both must be satisfied before live execution, not just this ticket's own build work
- Assumes the baseline-monitoring-manifest ticket delivers reusable baseline-manifest tooling this ticket should consume rather than rebuild

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
