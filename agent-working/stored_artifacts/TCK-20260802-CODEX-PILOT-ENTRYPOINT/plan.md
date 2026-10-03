---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-CODEX-PILOT-ENTRYPOINT
artifact_type: plan
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Plan

## Proposed policy design

Implement a context/policy preparation API plus a command-line wrapper that defaults
to preparation/evidence output only. It accepts no caller-selected candidate or hook
fragment. It generates one identity, writes a contained provisional policy, captures
the policy-excluded baseline, atomically replaces policy bytes with final hashes and
exact suffix rows, then constructs `PilotHarnessContext`. Any drift before later
preflight fails closed; the policy is not reused across attempts.

## Unresolved architecture gate

Architecture Review resolved this by splitting the work: implement only an output-only
preparation entrypoint here. A future ticket must build/review a real adapter-invoking
hook command plus exact config-diff and trust evidence. This ticket must not claim
that it can run a pilot or generate genuine `provider="codex"` monitoring evidence.

## Scope guards

No real-root execution in tests, no hook/config/monitoring write, no candidate or
parent-ticket change, and no reimplementation of reviewed invocation/preflight/proof
logic.
