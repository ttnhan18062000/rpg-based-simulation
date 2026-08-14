---
status: active
layer: ai
authority: P2
audience: agent
tags: [ai, hooks, agent-monitoring, observability, testing]
---

# Codex PostToolUse Adapter — Proposed Real Command (Draft for Human Review)

This document is **for human review only**. Nothing in this repository parses it as
TOML, nothing in `.codex/config.toml` references it, and no code in this repository
implements or executes what it describes. It exists so the owner has a concrete,
reviewable proposal to evaluate — not something already built or activated. It
extends `docs/ai/codex_posttool_adapter_activation_fragment.md`'s own established
"for human review only" framing to the one thing that document deliberately left
unresolved: what the hook's `command` field would actually need to *do*.

## Why `command = "true"` cannot work

Confirmed directly against the real code: `command = "true"` is a no-op shell
command. It ignores its stdin payload entirely and exits immediately. For the
`PostToolUse` hook to produce genuine monitoring evidence, `command` needs to
invoke something that actually reads the payload and calls
`tools/agent_codex_posttool_adapter/adapter.py::process_post_tool_use`. Nothing in
this repository does that today — there is no `__main__.py`, no `main()`, no
runnable script anywhere in `tools/agent_codex_posttool_adapter/`.

## A real gap this proposal surfaces, not previously named

`process_post_tool_use` requires `execution_id`, `ticket_id`, and optionally
`run_id`/`seq`/`phase`/`agent` as explicit keyword arguments — none of which a hook
process can know from its own stdin payload alone. Checked directly:
`tools/agent_codex_live_transport/invoker.py`'s `subprocess.run(...)` call for the
`codex exec` invocation passes no `env=` argument, meaning the child process only
inherits whatever's already in the parent's environment — and nothing currently
exports `execution_id`/`ticket_id`/`run_id` as environment variables anywhere in this
codebase. A hook invoked as a grandchild of that subprocess would have no way to
attribute its own write to the correct execution.

There is also a **third**, previously easy-to-miss gate:
`tools/agent_codex_posttool_adapter/live_gate.py::require_live_append` checks
`CODEX_POSTTOOL_ADAPTER_LIVE_APPEND == "1"` — structurally distinct from
`CODEX_LIVE_PILOT_HUMAN_SIGNOFF` and `CODEX_REALREPO_PILOT_LIVE_CONSENT`, by
deliberate original design (the adapter's own docstring explains why it's a
re-implementation, not an import, of the same strict-equality pattern). A real
attempt would need **three** env vars satisfied, not two — the two already tracked
throughout this exchange, plus this one, which nothing built so far threads through
to a hook's actual execution environment.

## Proposed shape (not implemented, not reviewed for trust, not activated)

1. **A new wrapper script** — e.g.
   `tools/agent_codex_posttool_adapter/hook_entry.py` — that: reads the raw JSON
   payload from stdin; reads `execution_id`/`ticket_id`/`run_id`/`seq`/`phase`/`agent`
   from environment variables (names to be decided under review, not invented here);
   calls `process_post_tool_use(..., target_path=<repo>/agent-monitoring/tools.jsonl)`;
   exits `0` unconditionally, regardless of the call's own return value — the
   adapter's own fail-open contract must extend all the way to the hook process
   itself, since a non-zero exit from a hook could visibly disrupt Codex's own run,
   which is exactly the failure mode `failure_timeout_fail_open` exists to prevent.
2. **A corresponding change to `tools/agent_codex_live_transport/invoker.py`'s**
   subprocess construction — passing an explicit `env=` that includes the pilot's own
   `execution_id`/`ticket_id`/`run_id` alongside the inherited environment, so the
   hook process (a descendant of that subprocess) can read them. This is itself a
   real, reviewable change to already-approved code, not something to slip in
   silently.
3. **The resulting `command` string** would be something like
   `command = "python3 <absolute-repo-path>/tools/agent_codex_posttool_adapter/hook_entry.py"`
   — fixed, no shell interpolation, no caller-suppliable arguments, matching every
   other fixed-command precedent in this exchange.

## What this document does not do

- It does not implement any of the above. `hook_entry.py` does not exist.
- It does not change `invoker.py`, `.codex/config.toml`, or any hook registration.
- It does not satisfy `human_approval`, `project_trust_review`, `hook_trust_review`,
  or `reviewed_config_diff` from `agent-orchestration/hook-surface-policy.yaml`'s
  own governed checklist — those remain exactly what they've always been: human
  decisions this document can inform but not stand in for.

## If the owner wants to proceed

The next concrete step would be scoping this as its own standard-tier ticket —
`hook_entry.py`'s implementation, the `invoker.py` env-threading change, and the
exact resulting config diff — through the same plan-review and actual-diff-review
process as every prior ticket in this exchange, with the config diff itself
presented for explicit sign-off before any real activation, exactly as
`reviewed_config_diff` requires. Nothing here authorizes skipping that.
