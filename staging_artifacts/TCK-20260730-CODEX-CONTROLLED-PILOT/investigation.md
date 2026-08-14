---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260730-CODEX-CONTROLLED-PILOT
artifact_type: investigation
---

# Investigation — TCK-20260730-CODEX-CONTROLLED-PILOT

## Current Behavior

- The ticket permits at most one live operation, and only after a named candidate, rollback
  plan, fresh sign-off, and preflight evidence. It forbids live invocation/config enablement in
  ordinary implementation (`tickets/inprogress/TCK-20260730-CODEX-CONTROLLED-PILOT.md`).
- Codex has no enabled events. The policy designates only `PostToolUse` with
  `write_line`/`write_lines` as a future candidate (`agent-orchestration/hook-surface-policy.yaml`).
  The committed `.codex/config.toml` is hook-free.
- `pilot_requests/` contains only its README: no candidate is registered. Candidate parsing,
  concurrent-provider detection, sign-off, baseline, enabled-surface, and rollback functions are
  separately implemented in `tools/agent_codex_pilot_guardrails/`, but no production preflight
  orchestration composes them.
- The adapter is callable but inert: it parses/redacts a captured `PostToolUse` payload and,
  only behind `CODEX_POSTTOOL_ADAPTER_LIVE_APPEND=1`, appends a `tools.jsonl`-shaped record through
  the shared writer (`tools/agent_codex_posttool_adapter/adapter.py`). Its proposed config block is
  deliberately `command = "true"`, never an adapter invocation.
- `tools/agent_replay_codex/invoker.py` is the sole `codex exec` boundary. It is an isolated replay:
  it runs in scratch and asserts no ticket/config/monitoring corpus change. It therefore cannot
  satisfy this ticket's required provider-attributed monitoring evidence or hook enable/rollback.
- Dashboard readers already expose `provider`, `execution_id`, and `ticket_id` when a valid run
  record exists (`src/api/agent_ops_dashboard/ingest.py`); a tool row alone is insufficient.

## Mechanics / Engine Constraints

This is agent tooling only. It must not mutate simulation state, bypass the authoritative mutation
pipeline, or claim Mechanics Bible parity. YAML parity work is not implicated by the planned
read-only ticket artifacts.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml` has the established agent-tooling boundary entries
`INFRA-305` through `INFRA-307`. No source behavior changes occur in this run, so no ledger update
is currently justified. A separately approved executor ticket must reassess whether a new INFRA
entry is required when it changes a real activation boundary.

## Prior Work

- `TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS`: scratch-only config/rollback and candidate primitives.
- `TCK-20260730-CLAUDE-EXECUTION-IDENTITY`: real Claude provider/execution identity writes.
- `TCK-20260730-PROVIDER-HOOK-POLICY`: machine-checkable candidate surface; no enablement.
- `TCK-20260730-CODEX-POSTTOOL-ADAPTER`: redacted, gated tools-row adapter; no wiring.
- `TCK-20260730-CODEX-RUNTIME-SHADOW`: non-live in-process outcome comparison.

## Risks and Open Questions

1. **Hard final-operation blocker:** no separately reviewed executor can both perform an actual
   trusted hook activation and produce the required run/events/tools lifecycle. The existing replay
   invoker is intentionally incompatible with those effects. This is not permission to weaken any
   guardrail or add the executor to this ticket.
2. A future executor must order independent candidate, corpus-claim, policy, trust, baseline,
   config-diff, adapter-append, replay-consent, and pilot-sign-off gates without conflation.
3. The successful-pilot prefix-preservation proof must retain legitimate appended pilot records;
   the existing rollback drill's whole-file-equality proof is appropriate only where no pilot ran.
4. The adapter creates a tool record, not a coherent run/events lifecycle. The future design must
   specify and test exact new records and reader visibility.
5. `assert_no_concurrent_claim` is not wired to the real corpus and only detects multiple distinct
   providers. The future policy must define an existing single-provider active-claim outcome.
6. A current guardrail test's historical provider-coverage expectation predates the now-real Claude
   identity record. Treat any resulting failure as an explicit baseline issue; do not rewrite it to
   make this pilot ticket pass.

## Anti-Drift Hazards

- Never set `CODEX_REPLAY_PARITY_LIVE_CONSENT`, `CODEX_LIVE_PILOT_HUMAN_SIGNOFF`, or
  `CODEX_POSTTOOL_ADAPTER_LIVE_APPEND` during this ticket's ordinary workflow.
- Preserve hook-free `.codex/config.toml` byte-for-byte and the no-subprocess/no-live-path AST
  tests in guardrail, adapter, and shadow packages.
- Do not treat a synthetic adapter write, a scratch replay, or a policy declaration as a live
  Codex pilot.
- Keep unrelated working-tree changes and the parity-index initiative outside this ticket.

