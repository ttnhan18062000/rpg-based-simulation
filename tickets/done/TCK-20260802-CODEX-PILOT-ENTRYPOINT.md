---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-CODEX-PILOT-ENTRYPOINT
phase: done
date: 2026-08-02
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# TCK-20260802-CODEX-PILOT-ENTRYPOINT

## Title

Build the non-live controlled-pilot invocation entrypoint and just-in-time policy builder

## Status

DONE

## Tier

standard

## Type

feature

## Priority

P1

## Request Summary

Add the final non-live entrypoint capable of preparing the actual stale-status
candidate's typed context and immutable expected-write policy immediately before a
future pilot attempt. It must solve full-tree baseline freshness and bind a single
fresh execution identity into the generated policy/context. It does not authorize
or perform a live invocation, config change, hook registration, or monitoring write.

## Scope

- Add a narrow runnable entrypoint for the actual in-progress candidate only.
- Build the candidate policy just in time, with contained temporary/persisted policy
  evidence and a fresh execution identity shared by context and policy suffixes.
- Reuse reviewed preflight, transport, orchestration, proof, and authority primitives.
- Test only against injected scratch roots and synthetic data.

## Out of Scope

- Running the entrypoint against the real repository or invoking Codex.
- Editing `.codex/config.toml`, the candidate, either blocked parent ticket, or real monitoring.
- Replacing the approved hook fragment or broadening hook/writer surface without separate review.

## Acceptance Criteria

- [x] Entry preparation binds only `TCK-20260801-MONITORING-WRITER-STATUS-STALE`, its real
      request, exact target transitions, approved surface, and canonical paths.
- [x] Policy construction is deterministic for fixed injected bytes and detects baseline/request
      drift before any invocation boundary is reached.
- [x] A fresh execution identity is generated once per preparation and consistently represented
      wherever policy/context requires it.
- [x] Tests prove no real-root/config/Codex/monitoring mutation and reject traversal, stale policy,
      mismatched candidate, altered request, and missing required policy paths.
- [x] Architecture Review resolves how live hook output can satisfy the controlled-pilot monitoring
      evidence requirement before implementation proceeds.

## Related Tickets

- TCK-20260801-CODEX-PILOT-ORCHESTRATION (DONE)
- TCK-20260801-CODEX-LIVE-TRANSPORT (DONE)
- TCK-20260801-MONITORING-WRITER-STATUS-STALE (reserved candidate)
- TCK-20260730-CODEX-CONTROLLED-PILOT (BLOCKED; untouched)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (BLOCKED; untouched)

## Related Docs

- docs/plans/agent_infrastructure/codex_pilot_invocation_entrypoint_authorization_claude.md
- docs/ai/codex_posttool_adapter_activation_fragment.md
- agent-orchestration/hook-surface-policy.yaml

## Related Stored Artifacts

- stored_artifacts/TCK-20260801-CODEX-PILOT-ORCHESTRATION/

## Related Code Areas

- tools/agent_codex_pilot_orchestration/orchestrator.py
- tools/agent_codex_realrepo_pilot_harness/{preflight.py,policy.py,proofs.py}
- tools/agent_codex_pilot_guardrails/config_toggle.py
- tools/agent_codex_posttool_adapter/
- pilot_requests/TCK-20260801-MONITORING-WRITER-STATUS-STALE.yaml

## Assumptions / Open Questions

- Architecture Review resolved the no-op hook fragment versus required live monitoring evidence:
  this ticket is preparation/output-only. A separate, not-yet-scoped and independently reviewed
  ticket must build a real adapter-invoking hook command and exact config-diff/trust evidence.
  Until then, no real pilot can produce genuine `provider="codex"` monitoring evidence, even if
  this ticket closes.

## Implementation Notes

- Added `tools/agent_codex_pilot_entrypoint/preparation.py`. It creates a fixed-candidate,
  just-in-time policy through provisional-write/baseline-capture/final-rewrite and returns the
  matching typed context. `python -m tools.agent_codex_pilot_entrypoint` is explicitly
  prepare-only. The policy includes the candidate lifecycle, working-log, registry, target,
  and transient config paths; it has no invocation, config, hook, or monitoring write path.

## Test Summary

- `tests/agent_codex_pilot_orchestration/test_entrypoint.py` plus existing orchestration tests:
  **19 passed** (`tests/agent_codex_pilot_orchestration --import-mode=importlib -q`).

## Files Changed

- tools/agent_codex_pilot_entrypoint/{__init__.py,preparation.py}
- tests/agent_codex_pilot_orchestration/test_entrypoint.py

## Completion Summary

Completed the prepare-only fixed-candidate policy/context entrypoint. It does not
authorize or execute a pilot; the real hook-command and provider-monitoring gap remains deferred.
