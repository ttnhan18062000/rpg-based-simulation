---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260730-PROVIDER-HOOK-POLICY
phase: open
date: 2026-07-30
tags: [ai, hooks, workflows, documentation, testing]
---

# TCK-20260730-PROVIDER-HOOK-POLICY

## Title
Define the provider hook-surface policy and Codex activation boundary

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Make hook terminology precise before Codex hooks can be activated. Codex exposes more lifecycle events than the shared contract normalizes, while only `PostToolUse` has direct payload-capture evidence. The contract needs an enforceable distinction between a provider capability being available, a shared event being normalized, and an event actually being enabled in project configuration.

## Scope
- Add a contract-owned, validator-covered provider hook-surface policy that separately represents `available`, `normalized`, and `enabled` events.
- Record the current truth: Claude enables `PreToolUse` and `PostToolUse`; Codex has ten documented available events; the committed Codex project configuration enables zero hooks.
- Keep Codex's other eight events out of normalized/enabled status. `PreToolUse` remains schema-valid but is not an evidenced first Codex activation candidate.
- Declare `PostToolUse` as the sole possible first Codex enabled event, constrained to the existing evidenced writer functions `write_line` and `write_lines`.
- Define later activation prerequisites: contemporaneous human approval, scratch-first payload/schema verification, project and hook trust review, failure/timeout fail-open behavior, redacted output, out-of-band diagnostics, reviewed config diff, and one-action rollback.
- Add tests that reject conflating availability with support or enabled configuration and retain proof that committed `.codex/config.toml` is hook-free.

## Out of Scope
- Registering any actual Codex hook or changing committed `.codex/config.toml` into a hook-bearing configuration.
- Invoking Codex, running a paid/live pilot, or adding a subprocess execution path to guardrail tooling.
- Expanding normalized hook vocabulary merely because a provider documents an event.
- Replacing existing pilot guardrails or their no-live-execution-path tests.

## Acceptance Criteria
- [ ] Contract validation independently checks available, normalized, and enabled hook status or another equally machine-checkable representation.
- [ ] The policy accurately represents Claude's two enabled events, Codex's ten available events, Codex's zero enabled events, and the shared normalized vocabulary without falsely claiming broader Codex support.
- [ ] Only Codex `PostToolUse` is approved as a future initial activation candidate; its evidenced writer subset is explicitly bound to `write_line`/`write_lines`.
- [ ] Tests prove a committed Codex config remains hook-free and guardrail code retains no live Codex invocation path.
- [ ] Future activation requirements are explicit enough for a later ticket to consume without reinterpreting consent, rollback, redaction, or failure behavior.

## Related Tickets
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (parent)
- TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE (DONE; payload evidence)
- TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS (DONE; enabled-surface and rollback mechanisms)

## Related Docs
- docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md
- docs/ai/codex_capability_matrix.md
- agent-orchestration/hook-events.yaml
- agent-orchestration/intentional-divergences.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/

## Related Code Areas
- agent-orchestration/hook-events.yaml
- agent-orchestration/contract.yaml
- agent-orchestration/README.md
- .claude/settings.json
- .codex/config.toml
- tools/agent_codex_pilot_guardrails/enabled_surface.py
- tools/agent_replay_codex/codex_config_guard.py
- tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py
- tests/agent_codex_pilot_guardrails/test_enabled_surface.py
- tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py
- tests/tools/test_codex_hook_payload_fixture.py

## Assumptions / Open Questions
- The policy structure may be a new contract file rather than an overloaded extension of `hook-events.yaml`; Investigate must choose the smallest validated shape.
- Project trust and hook trust remain distinct checks and must not be assumed satisfied by a committed config alone.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
