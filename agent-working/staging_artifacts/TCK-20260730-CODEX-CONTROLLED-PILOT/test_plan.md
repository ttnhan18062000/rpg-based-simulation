---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260730-CODEX-CONTROLLED-PILOT
artifact_type: test_plan
---

# Test Plan — TCK-20260730-CODEX-CONTROLLED-PILOT

## Regression Surface

- `tests/agent_codex_pilot_guardrails/` — manifest, sign-off, enabled-surface, baseline, config
  toggle, and no-live-execution invariants.
- `tests/agent_codex_posttool_adapter/` — payload validation/redaction, gated append, and no-live
  wiring/subprocess invariants.
- `tests/agent_codex_runtime_shadow/` and `tests/agent_replay_codex/` — shadow/replay containment.
- `tests/tools/test_agent_ops_dashboard_ingest.py` — provider/execution identity reader behavior.

## New Tests Required

No new production test is authorized in this ticket before the missing executor has its own
approved ticket. That future ticket must add:

1. Read-only preflight tests for absent/malformed candidate, stale predecessor, corpus claim,
   policy widening, hook-bearing baseline, and missing sign-off; every refusal occurs before any
   config/write/subprocess action.
2. Disposable-repository integration tests for exact config syntax, adapter stdin/payload behavior,
   fail-open timeout/error behavior, redaction, and out-of-band diagnostics.
3. Prefix-preservation and rollback tests that distinguish intentional pilot appends from forbidden
   historical changes/deletions.
4. Temporary-corpus reader tests proving a coherent Codex run/events/tools lifecycle and proving a
   tool row alone cannot establish dashboard run visibility.
5. Structural tests keeping live invocation isolated to the new executor and forbidden from the
   existing guardrail/adapter/shadow packages.

## Scoped Pytest Commands

Read-only readiness verification, if rerun during planning:

```bash
.venv/bin/python -m pytest -q tests/agent_codex_pilot_guardrails tests/agent_codex_posttool_adapter tests/agent_codex_runtime_shadow tests/agent_replay_codex tests/tools/test_agent_ops_dashboard_ingest.py
```

The final live test is deliberately absent from ordinary pytest/CI and must remain refused without
fresh human authorization.

## Anti-Drift Test Guards

- No test may set live consent/sign-off/append variables against the real repository.
- No test may target the committed `.codex/config.toml` or append to real monitoring JSONL.
- Baseline failures unrelated to this ticket must be recorded, not normalized away.

