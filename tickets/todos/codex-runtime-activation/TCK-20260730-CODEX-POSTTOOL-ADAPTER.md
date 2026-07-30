---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260730-CODEX-POSTTOOL-ADAPTER
phase: open
date: 2026-07-30
tags: [ai, hooks, agent-monitoring, observability, testing]
---

# TCK-20260730-CODEX-POSTTOOL-ADAPTER

## Title
Build the isolated Codex PostToolUse monitoring adapter

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement and test the smallest Codex-specific boundary that can normalize the captured `PostToolUse` payload into the shared monitoring writer and execution identity model. This is isolated activation evidence only: it must not enable a project hook or create real Codex traffic in the repository corpus.

## Scope
- Consume the hook-surface policy and the approved Claude identity conventions to define a Codex `PostToolUse` adapter input/output contract.
- Build a testable adapter/harness using captured payload fixtures, explicit injected paths, bounded timeout/failure behavior, and redacted summaries; do not route raw tool input/output into monitoring.
- Require an explicit `provider="codex"`, validated execution identity, and known ticket ID before an adapter is permitted to append a record in an approved later runtime path.
- Keep default/scratch verification non-writing against the repository monitoring corpus and committed config; use temporary directories and test doubles for writer behavior.
- Add failure-injection coverage proving malformed payloads, writer failures, timeouts, and diagnostic failures cannot block a Codex tool workflow.
- Produce a reviewable proposed hook command/config fragment, but leave `.codex/config.toml` byte-identical and hook-free.

## Out of Scope
- Enabling the proposed hook command in project configuration.
- Running Codex or writing `provider=codex` into real `agent-monitoring/*.jsonl` during ordinary implementation/test execution.
- Reusing Claude's `post_tool_hook.py` by assumption without validating the Codex payload boundary.
- Implementing the full `implement-ticket` runtime or selecting/executing a pilot.

## Acceptance Criteria
- [ ] Captured Codex `PostToolUse` fixtures validate against the adapter's documented input model, and unsupported/malformed payloads fail safely without a repository write.
- [ ] The adapter emits only redacted/minimal monitoring fields and uses the shared append writer interface rather than a new append mechanism.
- [ ] Adapter tests prove non-blocking behavior for writer, parse, timeout, and diagnostic failure cases.
- [ ] A project-config guard proves committed `.codex/config.toml` remains byte-identical/hook-free throughout the test suite.
- [ ] The proposed activation fragment enables only `PostToolUse` and only after the policy's explicit human-approval gate; no test or normal run invokes it.

## Related Tickets
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (parent)
- TCK-20260730-PROVIDER-HOOK-POLICY (must complete first)
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY (must complete first; establishes new-record identity convention)
- TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE (DONE; source fixture)

## Related Docs
- docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md
- docs/ai/codex_capability_matrix.md
- agent-orchestration/monitoring-schema.yaml

## Related Stored Artifacts
- stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/

## Related Code Areas
- tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json
- tools/agent-monitoring/writer.py
- tools/agent-monitoring/post_tool_hook.py
- tools/agent_codex_pilot_guardrails/enabled_surface.py
- tools/agent_codex_pilot_guardrails/config_toggle.py
- .codex/config.toml
- tests/tools/test_codex_hook_payload_fixture.py
- tests/agent_codex_pilot_guardrails/test_enabled_surface.py

## Assumptions / Open Questions
- Investigate must choose a dedicated Codex adapter location that does not blur replay tooling, pilot guardrails, and a live writer boundary.
- Any later live hook command must be explicitly reviewed for project trust and hook trust in addition to this ticket's implementation evidence.

## Implementation Notes
(pending — Investigate phase)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
