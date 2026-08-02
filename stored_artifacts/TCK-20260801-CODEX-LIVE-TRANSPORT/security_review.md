---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-LIVE-TRANSPORT
artifact_type: investigation
tags: [ai, security, testing]
---

# Security review — TCK-20260801-CODEX-LIVE-TRANSPORT

## Verdict

APPROVED.

## Reviewed boundary

The new transport is capability-only. It does not invoke Codex in this ticket;
default tests use synthetic evidence and the unrequested live fixture skips.

- `invoke_live_transport()` re-checks both existing exact-value consent gates as
  its literal first operation, before authority/preflight validation or subprocess
  construction.
- The API accepts only typed authority and a `LivePreflightResult`; it accepts no
  raw root, prompt/text, arbitrary options, executable, or runner argument.
- The sole real-root capability constructor is the private live-preflight factory;
  AST coverage rejects any second construction path.
- The command is a fixed argv list and specifies `shell=False`; structural tests
  reject dangerous Codex sandbox/hook bypass flags.
- Instruction evidence is serialized with `json.dumps`, so newlines and other
  control characters in validated strings cannot forge additional instruction
  lines.
- The transport delegates root admission to the existing harness boundary and
  introduces no duplicate containment, expected-write proof, or rollback code.

## Non-activation verification

The scoped diff contains no hook registration, `.codex/config.toml` change,
reserved-candidate change, blocked-parent-ticket change, live invocation, or
`provider="codex"` monitoring record. A future pilot remains independently gated.
