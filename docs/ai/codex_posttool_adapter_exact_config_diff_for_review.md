---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, hooks, agent-monitoring, observability, testing]
---

# Exact `.codex/config.toml` diff — for owner review only

This document is **for human review only**. It is not applied. Nothing in this
repository parses it as TOML, and the committed `.codex/config.toml` remains
byte-identical to its current hook-free state. It exists so the owner has the
literal, exact diff to review — not a description of one — ahead of the
`reviewed_config_diff` prerequisite.

## Current committed file (unchanged)

```toml
# .codex/config.toml — TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE
#
# Minimal project marker, committed only after the isolated scratch-directory fixture-capture
# experiment (Step 11 of this ticket's plan.md; captured payload at
# tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json) confirmed real
# PostToolUse hook stdin-payload behavior and the project-trust/hook-registration mechanics.
#
# This file deliberately contains ZERO hook registrations — no [hooks] table, no per-event
# hook arrays, at any nesting level. This ticket's scope explicitly forbids enabling any
# production hook. A future, separate ticket (live-Codex-pilot-guardrails, out of this
# ticket's scope) owns actually wiring a production hook, using the registration syntax this
# ticket's Step 11 discovered and recorded in this ticket's Implementation Notes.
```

## Proposed addition, rendered from the actual reviewed code, on this machine, right now

Computed by calling `tools/agent_codex_posttool_adapter/command.py::render_review_command`
against this repository's real root — not typed by hand:

```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 /home/u24desktop/Working/rpg-based-simulation/tools/agent_codex_posttool_adapter/hook_entry.py
```

The exact bytes that would be appended:

```toml
[[hooks.PostToolUse]]
matcher = "*"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 /home/u24desktop/Working/rpg-based-simulation/tools/agent_codex_posttool_adapter/hook_entry.py"
```

This differs from the currently-approved placeholder fragment in exactly one way:
`command = "true"` → the real absolute interpreter + script path. Nothing else in
the fragment changes — same `matcher = "*"`, same single `PostToolUse` event, same
shape reviewed throughout this whole exchange.

## What this command does when actually invoked

`hook_entry.py` reads one JSON object from stdin, reads identity *only* from
six `CODEX_HOOK_*` environment variables (never from the payload), calls the
already-reviewed `process_post_tool_use`, and always exits `0` — malformed input,
missing identity, the adapter's own `CODEX_POSTTOOL_ADAPTER_LIVE_APPEND` gate
refusing, or a write failure all fail open silently. It cannot be invoked with
different behavior — no arguments, no flags, nothing caller-controlled.

## What is NOT decided by this document

This is the artifact for the `reviewed_config_diff` prerequisite — nothing more.
Still entirely separate, entirely yours:

- **`project_trust_review`** — do you trust this project/repository enough for
  Codex to register any hook in it at all, independent of what the hook does.
- **`hook_trust_review`** — do you trust *this specific command* (shown above,
  exactly) enough to let Codex's CLI execute it once per tool call during a real
  run.
- **`human_approval`** — a contemporaneous decision, recorded at the moment you
  actually decide to proceed, not inferred from anything earlier in this exchange.
- **Fresh three-factor consent at execution time** — `CODEX_LIVE_PILOT_HUMAN_SIGNOFF=1`,
  `CODEX_REALREPO_PILOT_LIVE_CONSENT=1`, `CODEX_POSTTOOL_ADAPTER_LIVE_APPEND=1`, all
  three set fresh, immediately before the actual attempt — not now, not in advance.

If you approve this exact diff, the mechanical next step is genuinely small: edit
`.codex/config.toml` to add the block above, byte for byte. I won't do that without
you explicitly saying so after you've seen this — editing the real committed config
is the one action in this entire exchange that was never authorized for either of
us to take unilaterally.
