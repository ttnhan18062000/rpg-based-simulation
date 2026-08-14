"""Minimal Codex `implement-ticket` phase/tier runtime contract + shadow parity
(TCK-20260730-CODEX-RUNTIME-SHADOW).

Defines the minimal `implement-ticket` phase/tier support matrix (`standard` tier,
`Scope->Investigate->Plan->Review` only) read from
`agent-orchestration/workflows/implement-ticket.yaml`, validates a ticket-shaped input against it
(rejecting any unsupported phase or tier with a typed error rather than silently accepting it),
and produces a machine-checkable phase-transition/gate/required-artifact record for that input
entirely in-process — never invoking a real `codex exec` subprocess. Shadow-compares its own
record against `tools/agent_replay`'s canonical fixture/runner output; a mismatch fails unless a
matching RATIFIED entry exists in `agent-orchestration/intentional-divergences.md`.

Distinct from `tools/agent_replay_codex/`: that package's job is proving a real, authenticated
`codex exec` process can execute the identical Python replay functions — an execution-*environment*
proof, consent-gated, costing real account usage. This package's job is defining and enforcing the
phase/tier *contract* a Codex-driven execution would have to satisfy, and validating a
ticket-shaped input against it without ever spending a real invocation — a contract-*shape* proof
that runs unconditionally, with no consent gate needed because it never shells out.

Distinct from `tools/agent_codex_pilot_guardrails/`: that package governs human sign-off,
rollback, and enabled-surface restriction for a future live pilot run of a specific ticket — it
has no phase/gate/artifact validation logic at all. No overlap.
"""
