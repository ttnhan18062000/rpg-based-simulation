---
status: active
layer: ai
authority: P1
audience: developer
date: 2026-07-30
tags: [ai, codex, workflows, hooks, agent-monitoring]
---

# Claude Review Request — Codex Runtime Activation Ticket Batch

## Requested review

Please review the ticket batch in `tickets/todos/codex-runtime-activation/`, created from
`current_codex_runtime_status_and_activation_plan.md` using the create-tickets workflow.

The proposed sequence is intentionally gated:

1. Add real Claude execution identity for future records only.
2. Record and validate available/normalized/enabled provider hook semantics.
3. Build an isolated Codex `PostToolUse` adapter without enabling it.
4. Build a contained, partial Codex ticket runtime/shadow adapter.
5. Consider one human-approved pilot as a separately gated operation.

## Review focus

- Is the split sufficient to prevent the existing Scope-to-Review replay proof from being misrepresented as a live runtime?
- Do the identity ticket's `provider="claude"` decision and legacy `claude-code` compatibility boundary avoid ambiguous new writes?
- Does the hook policy prevent capability-only Codex events from being treated as normalized/enabled support?
- Do the runtime and pilot tickets retain the current no-live-execution and hook-free-config protections until explicit approval?
- Are any dependencies, implementation paths, acceptance criteria, or historical-data safeguards missing?

## Explicit non-authorization

This review request does not approve a hook registration, a paid/live Codex invocation, or a
pilot candidate. Those remain scoped to the final ticket and require contemporaneous human
authorization.
