---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, hooks, agent-monitoring, observability, testing]
---

# Codex PostToolUse Adapter — Proposed Activation Fragment (TCK-20260730-CODEX-POSTTOOL-ADAPTER)

This document is **for human review only**. Nothing in this repository parses it as TOML, and
nothing in `.codex/config.toml` references it. It exists to make the adapter's proposed hook
registration reviewable before any future activation ticket considers enabling it.

## Proposed fragment

The exact bytes of `tools.agent_codex_posttool_adapter.activation_fragment.PROPOSED_HOOK_BLOCK`:

```toml
[[hooks.PostToolUse]]
matcher = "*"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "true"
```

`command = "true"` is a deliberate no-op placeholder — the same discipline
`tools/agent_codex_pilot_guardrails/config_toggle.py::_HOOK_BLOCK` already uses for its own
proposed pilot fragment. It registers only the `PostToolUse` hook event; no other event is
proposed by this ticket.

## Activation prerequisites (per `agent-orchestration/hook-surface-policy.yaml`)

All nine of the policy's `activation_prerequisites` remain unmet by this ticket. None of the
boxes below may be checked by this document or by any code in
`tools/agent_codex_posttool_adapter/` — checking one requires a separate, later activation
ticket with its own explicit human review.

- [ ] `human_approval` — Contemporaneous human sign-off recorded before any Codex hook is enabled.
- [ ] `scratch_first_verification` — Payload/schema verified in a scratch environment before any
      committed config change.
- [ ] `project_trust_review` — Project-level trust reviewed and recorded independently of hook
      trust.
- [ ] `hook_trust_review` — Hook-level trust reviewed and recorded independently of project trust.
- [ ] `failure_timeout_fail_open` — Hook failure or timeout must fail open, never block the run.
- [ ] `redacted_output` — Hook output must be redacted before storage or display.
- [ ] `out_of_band_diagnostics` — Diagnostics for a live hook must be captured out-of-band from
      the run's own state.
- [ ] `reviewed_config_diff` — The exact config diff enabling the hook must be reviewed before
      commit.
- [ ] `one_action_rollback` — A single action must fully roll back the enabled hook to the
      pre-activation state.

## What this ticket already built toward these prerequisites

`failure_timeout_fail_open` and `redacted_output` are satisfied at the *adapter code* level by
`tools/agent_codex_posttool_adapter/adapter.py` (fail-open on any parse/validation/write
exception) and `tools/agent_codex_posttool_adapter/redaction.py` (tool_response content never
persisted, only a derived status flag). `out_of_band_diagnostics` is satisfied by delegating to
`tools/agent-monitoring/writer.py`'s existing `.writer_health.jsonl` sidecar. None of this
constitutes `human_approval`, `project_trust_review`, `hook_trust_review`,
`scratch_first_verification`, `reviewed_config_diff`, or `one_action_rollback` — those remain
entirely for a future activation ticket to satisfy and record.

## Related

- `tools/agent_codex_posttool_adapter/activation_fragment.py` — the code this document quotes.
- `agent-orchestration/hook-surface-policy.yaml` — the source of the prerequisite checklist above.
- `tools/agent_codex_pilot_guardrails/config_toggle.py` — the closest sibling precedent for a
  scratch-only, never-applied config toggle mechanism.
