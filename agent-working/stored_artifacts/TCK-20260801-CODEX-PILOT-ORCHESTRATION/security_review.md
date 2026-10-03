---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-PILOT-ORCHESTRATION
artifact_type: investigation
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Security review — TCK-20260801-CODEX-PILOT-ORCHESTRATION

## Verdict

APPROVED.

## Findings

- Config targeting is factory-derived from typed real-root preflight evidence; no
  caller can supply a config path, fragment, command, root, prompt, or options.
- The factory rejects ordinary evidence, mismatched roots, a missing config, and
  symlinked config targets before capture/write.
- `enable()` performs the existing exact dual-consent check as its literal first
  operation and verifies baseline bytes immediately before the fixed hook write.
- `restore()` is identity-bound and deliberately consent-independent, preventing a
  changed consent environment from stranding an enabled hook. It restores only the
  captured bytes and rejects an external change before enablement.
- The orchestration verifies exact approved enabled bytes after transport, requires
  the transient config path in the immutable policy, delegates existing post-run
  proof, and preserves both primary and cleanup failures explicitly.
- Source-level tests reject duplicate production constructors, raw public inputs,
  direct process/monitoring writers, and all tests use temporary/synthetic evidence.

## Non-activation boundary

No real config write, hook registration, Codex invocation, candidate/parent-ticket
change, or provider-attributed monitoring record occurred in this ticket.
