---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-PILOT-ORCHESTRATION
phase: done
date: 2026-08-01
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# TCK-20260801-CODEX-PILOT-ORCHESTRATION

## Title

Build the non-exercised controlled-pilot orchestration and real-config capability

## Status

DONE

## Tier

standard

## Type

feature

## Priority

P1

## Request Summary

Build the final capability required to make one controlled Codex pilot technically
possible, without running it. Unlike the completed harness and transport tickets,
this capability will be structurally capable of targeting the real project config
when a future caller supplies the already-required live preflight and fresh dual
consent. It must therefore fail closed, compose reviewed primitives instead of
duplicating them, and be tested only with injected temporary config files. This
ticket does not authorize a live invocation, hook activation, candidate execution,
or any change to the actual `.codex/config.toml`.

## Scope

- Add a narrow orchestration entry point that sequences reviewed live preflight,
  authority issuance, transport invocation, post-run policy proof, and config
  rollback verification.
- Add a separate production-config-toggle capability, distinct from the protected
  scratch adapter, for the exact `.codex/config.toml` path only.
- Require a fresh re-check of both existing exact-value live-consent gates at the
  literal point of every real-config write; do not introduce a third environment
  variable or treat a prior authority object as sufficient.
- Use only the policy-approved `PostToolUse` hook surface and existing
  `write_line`/`write_lines` writer boundary.
- Test all enable/restore/verification behavior through injected temporary config
  files and synthetic preflight/authority doubles, never the real config or Codex.

## Out of Scope

- Any actual Codex invocation, hook enablement, live monitoring write, or edit to
  the committed `.codex/config.toml`.
- Implementing or unblocking `TCK-20260801-MONITORING-WRITER-STATUS-STALE`.
- Modifying `TCK-20260730-CODEX-CONTROLLED-PILOT` or
  `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`.
- Weakening/replacing `ScratchConfigAdapter`, ordinary scratch-root refusal, or
  existing preflight/transport/proof/rollback validation.
- Broad hook support, arbitrary commands, retries, rollout, or a new consent gate.

## Acceptance Criteria

- [x] A single orchestration entry composes reviewed live preflight, authority,
      transport, post-run proof, and rollback verification in the approved order,
      without reimplementing their validation logic.
- [x] A separately scoped production-config adapter can target only the canonical
      `.codex/config.toml`, only with typed live-preflight/authority evidence, and
      re-checks both exact consent values immediately before each write.
- [x] Enablement adds only the approved `PostToolUse` fragment; captured baseline
      bytes are restored exactly by an ownership-bound one-action rollback and
      verification rejects any mismatch.
- [x] Tests prove refusal of raw roots, ordinary/scratch preflight, wrong config
      paths, forged/mismatched evidence, missing or stale consent, symlink escape,
      broadened hook surfaces, and transport/proof failure paths without touching
      the real repository/config or calling Codex.
- [x] Tests prove the no-live default: no real config write, no hook registration,
      no provider-attributed monitoring write, and no candidate/blocked-ticket
      mutation.
- [x] Architecture Review independently approves both the plan and actual diff
      before Verify/Finalize.

## Related Tickets

- TCK-20260801-CODEX-LIVE-TRANSPORT (DONE)
- TCK-20260801-CODEX-REALREPO-PILOT-HARNESS (DONE)
- TCK-20260801-MONITORING-WRITER-STATUS-STALE (reserved pilot candidate; untouched)
- TCK-20260730-CODEX-CONTROLLED-PILOT (BLOCKED; untouched)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (BLOCKED; untouched)
- TCK-20260730-PROVIDER-HOOK-POLICY (DONE)
- TCK-20260730-CODEX-POSTTOOL-ADAPTER (DONE)

## Related Docs

- docs/plans/agent_infrastructure/codex_pilot_orchestration_ticket_authorization_claude.md
- docs/ai/codex_posttool_adapter_activation_fragment.md
- agent-orchestration/hook-surface-policy.yaml
- docs/engine/authoritative_pipeline.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260801-CODEX-LIVE-TRANSPORT/
- stored_artifacts/TCK-20260801-CODEX-REALREPO-PILOT-HARNESS/
- stored_artifacts/TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS/

## Related Code Areas

- tools/agent_codex_realrepo_pilot_harness/authority.py
- tools/agent_codex_realrepo_pilot_harness/live_preflight.py
- tools/agent_codex_realrepo_pilot_harness/boundary.py
- tools/agent_codex_realrepo_pilot_harness/proofs.py
- tools/agent_codex_realrepo_pilot_harness/rollback.py
- tools/agent_codex_live_transport/invoker.py
- tools/agent_codex_pilot_guardrails/config_toggle.py
- tools/agent_codex_pilot_guardrails/enabled_surface.py
- tests/agent_codex_realrepo_pilot_harness/
- tests/agent_codex_live_transport/

## Assumptions / Open Questions

- The actual live pilot remains a separate explicit decision after this ticket
  closes; this capability must not be exercised during the ordinary workflow.
- Architecture Review must confirm the proposed production-adapter constructor and
  orchestration failure/rollback ordering before any implementation begins.
- Closing this capability ticket cannot satisfy the non-code hook prerequisites:
  contemporaneous recorded approval, project/hook trust reviews, exact config-diff
  review, and reviewed real-run rollback evidence remain future pilot-decision work.

## Implementation Notes

- Added `tools/agent_codex_pilot_orchestration/` with a private, canonical-root
  production-config capability and a single context-only orchestration entry point.
- Enablement rechecks the two existing exact consent gates; owner-bound restore is
  consent-independent, exact-byte, and safe as a repeated no-op after success.
- The orchestration requires the captured policy to name `.codex/config.toml` as
  its transient path, verifies its exact approved hook bytes after transport, then
  delegates post-run proof and always restores/verifies in `finally`.
- If the operation and rollback both fail, `PilotExecutionCleanupError` preserves
  both errors in its message and explicit `primary_error`/`cleanup_error` fields;
  cleanup can no longer silently mask the operational failure.
- All tests use temporary config files or synthetic private evidence; no live entry
  point was invoked and the actual project config remains untouched.

## Test Summary

- `.venv/bin/python -m pytest tests/agent_codex_pilot_orchestration
  tests/agent_codex_realrepo_pilot_harness tests/agent_codex_live_transport
  tests/agent_codex_pilot_guardrails tests/agent_codex_posttool_adapter
  --import-mode=importlib -q`: **136 passed**.
- Wider protected scope: **270 passed, 5 skipped, 4 failed**. The four failures
  are the known unrelated runtime-shadow workflow-version fixture mismatch; no new
  pilot-orchestration, harness, transport, guardrail, adapter, or monitoring failure
  occurred.

## Files Changed

- tools/agent_codex_pilot_orchestration/__init__.py
- tools/agent_codex_pilot_orchestration/production_config.py
- tools/agent_codex_pilot_orchestration/orchestrator.py
- tests/agent_codex_pilot_orchestration/
- staging_artifacts/TCK-20260801-CODEX-PILOT-ORCHESTRATION/{investigation.md,plan.md,test_plan.md}
- docs/parity_ledger/infrastructure.yaml (INFRA-312)

## Completion Summary

Completed the non-exercised controlled-pilot orchestration and canonical-config
capability with exact rollback, policy-bound post-run proof, and explicit
dual-failure reporting. No actual pilot, config activation, hook registration,
candidate implementation, or provider-attributed monitoring write occurred; the
remaining human trust/approval prerequisites are still required for any future run.
