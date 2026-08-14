---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-REALREPO-PILOT-HARNESS
artifact_type: investigation
---

# Parity disposition — TCK-20260801-CODEX-REALREPO-PILOT-HARNESS

**Recorded as `INFRA-310`.** The harness is durable, reusable agent-orchestration
developer tooling comparable to INFRA-306 through INFRA-309. It adds scratch-only
immutable preflight, policy-bound expected-write proof, dual-authority invoker
ordering, traversal/symlink containment, and adapter-owned scratch rollback.

The support boundary remains explicit: it changes no simulation behavior,
authoritative pipeline behavior, Mechanics Bible contract, live Codex invocation,
hook registration, project config, or provider-attributed project monitoring data.
Its tests use injected scratch roots only.
