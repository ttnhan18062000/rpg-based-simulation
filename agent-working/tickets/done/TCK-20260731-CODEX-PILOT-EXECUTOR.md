---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-CODEX-PILOT-EXECUTOR
phase: done
date: 2026-07-31
tags: [ai, workflows, hooks, agent-monitoring, observability, rollback, testing]
---

# TCK-20260731-CODEX-PILOT-EXECUTOR

## Title
Build the non-live Codex pilot executor boundary

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build the smallest deterministic, scratch-only executor boundary that composes the existing Codex
guardrails, PostToolUse adapter, shared monitoring writer, identity model, and dashboard ingest.
It must prove a future pilot can be attributable, observable, refused safely, and recovered
without enabling configuration, invoking Codex, selecting a candidate, or writing real data.

## Scope
- Add a dedicated scratch-only executor package that reuses existing guardrail, adapter, writer,
  manifest, identity, and dashboard components rather than duplicating their logic.
- Implement ordered, deterministic preflight and atomic exclusive unfinished-ticket claims. Reject
  any unfinished claim for the same ticket regardless of provider; test recovery after terminal or
  injected-failure outcomes.
- Produce a synthetic coherent Codex run, ordered events, and one redacted tool row with matching
  execution_id, ticket_id, and run_id; prove existing dashboard ingestion sees it.
- Prove original bytes of each scratch JSONL are preserved as a prefix and only declared ordered
  simulated-pilot records are appended.
- Update `docs/ai/monitoring_writer_decision.md` with identity-less pre-pilot logging, executor
  lifecycle/claim semantics, and the continuing separate human-approval gate.

## Out of Scope
- Any `.codex/config.toml` change, hook registration, live consent/sign-off/append environment
  variable, paid/live Codex invocation, real pilot request, or candidate selection.
- Real `agent-monitoring/*.jsonl` writes, a parallel writer, replay-invoker changes, dashboard
  redesign, historic migration/backfill, or broad workflow activation.

## Acceptance Criteria
- [x] The executor is structurally scratch-only, has no subprocess/live execution/config-toggle
      path, and reuses existing components rather than copying policy, payload, append, or IDs.
- [x] Invalid preflight inputs refuse deterministically before config/write activity, with a
      gate-specific reason and no real monitoring mutation.
- [x] A second unfinished claim for the same ticket is atomically rejected regardless of provider;
      terminal and injected-failure recovery leaves no ambiguous active claim.
- [x] Scratch execution creates one internally coherent `provider=codex` run/event/tool lifecycle
      that existing dashboard readers surface; all identity fields agree across records.
- [x] Prefix verification rejects altered/reordered/deleted history and accepts only declared,
      ordered scratch appends; write failures remain explainable and recoverable.
- [x] Documentation records the identity-less pre-pilot policy and preserves separate human
      authorization for any real pilot.

## Related Tickets
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC
- TCK-20260730-CODEX-CONTROLLED-PILOT
- TCK-20260730-CODEX-POSTTOOL-ADAPTER
- TCK-20260730-PROVIDER-HOOK-POLICY
- TCK-20260730-CLAUDE-EXECUTION-IDENTITY
- TCK-20260730-CODEX-RUNTIME-SHADOW
- TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS

## Related Docs
- docs/plans/agent_infrastructure/codex_controlled_pilot_plan_response_codex.md
- docs/plans/agent_infrastructure/codex_controlled_pilot_monitoring_policy_decision_codex.md
- docs/ai/monitoring_writer_decision.md
- agent-orchestration/hook-surface-policy.yaml
- agent-orchestration/monitoring-schema.yaml

## Related Stored Artifacts
- staging_artifacts/TCK-20260730-CODEX-CONTROLLED-PILOT/
- stored_artifacts/TCK-20260731-CODEX-PILOT-EXECUTOR/

## Related Code Areas
- expected: tools/agent_codex_pilot_executor/
- expected: tests/agent_codex_pilot_executor/
- tools/agent_codex_pilot_guardrails/ticket_selection.py
- tools/agent_codex_pilot_guardrails/enabled_surface.py
- tools/agent_codex_pilot_guardrails/baseline_manifest_gate.py
- tools/agent_codex_posttool_adapter/adapter.py
- tools/agent_codex_posttool_adapter/writer_bridge.py
- tools/agent-monitoring/writer.py
- tools/agent-monitoring/record_run.py
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/manifest.py
- tools/agent_replay_codex/invoker.py
- src/api/agent_ops_dashboard/ingest.py

## Assumptions / Open Questions
- Linux is the approved development/CI platform for the exclusive-claim mechanism.
- Scratch `provider=codex` fixtures do not violate the corpus invariant; the first real corpus
  value remains reserved for the separately authorized live pilot.

## Implementation Notes
Added the additive `tools/agent_codex_pilot_executor/` library and focused scratch-only tests.
It validates containment and preflight before any write, uses `fcntl.flock` over claim marker
transitions, produces only disposable synthetic monitoring records, and proves the shared
dashboard reader can ingest them. No live Codex path, config/hook change, or real monitoring
write was introduced.

## Test Summary
`.venv/bin/python -m pytest -q tests/agent_codex_pilot_executor tests/agent_codex_pilot_guardrails
tests/agent_codex_posttool_adapter tests/agent_codex_runtime_shadow tests/agent_replay_codex
tests/tools/test_monitoring_writer.py tests/tools/test_agent_monitoring_manifest.py
tests/tools/test_agent_ops_dashboard_ingest.py` → **221 passed, 5 skipped** (expected existing
consent-gated tests). The stale real-corpus provider-coverage assertion was corrected and closed
separately in `TCK-20260801-PROVIDER-COVERAGE-TEST-STALE`.

## Files Changed
- `tools/agent_codex_pilot_executor/{__init__.py,claims.py,dependencies.py,errors.py,models.py,paths.py,preflight.py,simulation.py}`
- `tests/agent_codex_pilot_executor/{conftest.py,test_claims.py,test_preflight.py,test_simulation.py,test_structure.py}`
- `docs/ai/monitoring_writer_decision.md`
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-308`)
- `staging_artifacts/TCK-20260731-CODEX-PILOT-EXECUTOR/{plan.md,test_plan.md}`

## Completion Summary
Implemented a contained, scratch-only Codex pilot executor with deterministic preflight refusal,
Linux advisory claim locking and recovery, exact monitoring-suffix proof, and existing-dashboard
ingest verification. The full targeted regression suite passed (221 passed, 5 expected skips);
all `provider=codex` records remain disposable test fixtures and a real pilot remains human-gated.
