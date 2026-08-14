---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND
artifact_type: investigation
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Investigation

## Current Behavior

`tools/agent_codex_posttool_adapter/adapter.py::process_post_tool_use` is the sole reviewed
adapter composition point. It parses a dictionary, validates supplied identity, requires its own
strict `CODEX_POSTTOOL_ADAPTER_LIVE_APPEND=1` gate before any write, builds a redacted 13-field
record, and delegates to the shared writer bridge. Every failure returns `False`.

There is no runnable boundary for it: the package has neither `__main__.py` nor a callable command
entrypoint. The only registered fragment in
`docs/ai/codex_posttool_adapter_activation_fragment.md` remains `command = "true"`, which reads
no stdin and never invokes the adapter.

`tools/agent_codex_live_transport/invoker.py::invoke_live_transport` uses a fixed argv and a
fresh dual-consent recheck, but does not pass `env=` to `subprocess.run`. Consequently a future
hook descendant cannot receive the current `execution_id` or candidate ticket identity from the
transport boundary.

`tools/agent_codex_pilot_entrypoint/preparation.py::prepare_policy` intentionally emits empty
`tools.jsonl` suffixes because the current hook is a no-op. `proofs.py::_assert_suffixes` already
requires an exact ordered JSONL suffix once a policy contains rows, so the required proof primitive
exists and must be reused rather than duplicated.

## Constraints

- `agent-orchestration/hook-surface-policy.yaml` permits only candidate event `PostToolUse` and
  writers `write_line`/`write_lines`; no registration is currently enabled.
- Hook input is untrusted. The direct-experiment fixture proves available payload fields but does
  not provide the controlled-pilot execution identity. Payload-derived identity must be prohibited.
- Adapter failure must fail open: neither malformed JSON nor any adapter/write/gate refusal may
  cause a nonzero hook process exit.
- Existing `CODEX_POSTTOOL_ADAPTER_LIVE_APPEND` is a deliberately independent gate. The design
  may thread it only as fixed, explicit evidence alongside existing fresh primary consents; it may
  not delete, coerce, or replace it.
- The policy proof compares exact JSON-serialized rows. A future expected tool row must therefore
  be deterministic: timestamp-free or supplied from a bounded, reviewed source. The adapter's
  default clock cannot be predicted before the hook executes.

## Prior Work

- The completed adapter ticket already supplies parsing, validation, redaction, writer bridging,
  a strict live append gate, and failure-injection tests.
- The completed live-transport ticket provides only a fixed argv, real-root admission, and two
  fresh consent gates; it deliberately never ran a subprocess in tests without mocks.
- The completed entrypoint ticket solved policy-baseline staleness with a self-excluded policy
  file, but correctly records no tool suffix while the command is unavailable.

## Architecture Decisions

1. **Bounded live-hook proof:** Preserve `proofs.py::_assert_suffixes` unchanged for all existing
   pre-declarable monitoring rows. Add a separately named tools-only proof for live PostToolUse
   output. For every appended row it requires exact `execution_id`, `ticket_id`, `provider`, and
   `run_id`; sequence starts at one and has no gaps/repeats; count is from zero through a reviewed
   policy `max_tool_calls`; and timestamps lie within wall-clock bounds captured immediately around
   transport. Exceeding any bound fails closed. This is a narrow additive mechanism, never a
   wildcard substitute.
2. **Three independent human gates:** `CODEX_LIVE_PILOT_HUMAN_SIGNOFF`,
   `CODEX_REALREPO_PILOT_LIVE_CONSENT`, and `CODEX_POSTTOOL_ADAPTER_LIVE_APPEND` remain direct,
   strict human shell grants. Transport copies the ambient environment and adds only internally
   derived identity metadata. It must never calculate, add, or alter any consent value.
3. **Auditable command form:** A later human-reviewed config diff must use the absolute repository
   `.venv/bin/python3` path and absolute `hook_entry.py` path. Ambient `PATH` lookup is prohibited.
   This deliberately couples the reviewed config to the current venv location; a moved venv requires
   a new config-diff review.

## Anti-Drift Hazards

- No test may write the real `agent-monitoring/tools.jsonl`, mutate `.codex/config.toml`, or call
  `codex`.
- Do not change the reserved candidate, blocked parent tickets, or the no-op activation fragment.
- Do not make a hook command infer ticket identity from `cwd`, stdin, filenames, or process args.
- Do not represent unknown future tool calls as fabricated monitoring rows merely to satisfy a
  static suffix proof.
- Do not expand the bounded tool-only proof into a general replacement for exact suffix checking.
