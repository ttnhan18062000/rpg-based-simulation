---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL
phase: open
date: 2026-09-16
tags: [ai, mcp, process-improvement, optimization]
---

# TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL

## Title
Run the trial in MCP mode only — explicit `headroom_compress` on JSON/JSONL payloads, nothing
intercepted, because Claude Code + proxy offers no observe-only mode

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Third child of `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`. Requires
`TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` (safety) and
`TCK-20260916-HEADROOM-HARM-CHECK-BASELINE` (comparison point) to be closed first.

**Why MCP rather than proxy, stated as a constraint rather than a preference.** Claude Code can set
only `ANTHROPIC_BASE_URL`; it cannot send request headers or per-request parameters. Consequently:

- `headroom_mode="audit"` and per-tool `skip_compression` profiles are **SDK-only** and unreachable
  from Claude Code;
- `headroom proxy --mode` accepts only `cache` and `token` — there is **no proxy-level audit or
  observe-only mode**;
- `x-headroom-bypass` applies only to the `/v1/compress` endpoint, not `/v1/messages`.

So proxy mode is all-or-nothing per session, fixed at proxy startup, and the "observe first, commit
later" rollout normally used for a change like this **is not available by that route**. MCP mode —
where the agent explicitly invokes `headroom_compress` on a chosen payload and nothing else is
touched — is the only way to obtain a measured result with zero exposure.

## Scope
- Register Headroom's MCP server for the trial session only, using the isolation established by the
  first child.
- Exercise `headroom_compress` / `headroom_retrieve` / `headroom_stats` against real repository
  payloads of the shape where compression is claimed to pay:
  - `agent-monitoring/data/**/*.jsonl` shards
  - `graphify-out/graph.json` (local-only, ~50MB)
  - `docs/REGISTRY.yaml`, junit XML under `reports/junit/`
- For each payload, record the paired measurement: original size/tokens versus compressed, on
  identical input.
- Record at least one `headroom_retrieve` round-trip, confirming that compressed content can
  actually be recovered in practice rather than only in principle.

## Out of Scope
- **Proxy mode, and wrapping any session.** Phase 2, separately BLOCKED.
- **Any compression in gate, CI, or review verification work.** The lossy compressors keep anomalies
  and drop normality, while verification evidence *is* the absence of anomaly (`273 passed, 0
  failed`; an empty `uniq -d`; an identical `diff`). Hard boundary for this ticket.
- `headroom learn` — off; it auto-writes to `CLAUDE.md`.
- Cross-ticket cost comparison as evidence of anything. Ticket scale varies by orders of magnitude;
  only paired same-payload measurements count.
- Making any of this a default, or changing any agent's standing instructions.

## Acceptance Criteria
- [ ] Compression is exercised on at least three real payloads of different shapes, each with a
      recorded original-versus-compressed figure on identical input.
- [ ] A `headroom_retrieve` round-trip is demonstrated recovering full original content.
- [ ] The trial session's state is confined to the isolated directory from the first child, verified
      rather than assumed.
- [ ] No repository file is modified by the compression itself.
- [ ] Trial activity is attributable in `tools.jsonl` (via `session_id`) so the verdict ticket can
      separate it from concurrent sessions.
- [ ] If measured savings on JSON/JSONL are materially below the claimed 60–95%, that is recorded as
      the finding — **not** retried with tuned settings until the number improves.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` — blocks this
- `TCK-20260916-HEADROOM-HARM-CHECK-BASELINE` — provides the comparison point

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.mcp.json`
- `agent-monitoring/data/YYYY-Www/tools.jsonl` (trial attribution via `session_id`)

## Assumptions / Open Questions
- Assumed the MCP server can be registered for one session without becoming globally active for
  every session on this machine. If registration turns out to be global, **stop and report** — that
  changes the trial's risk profile rather than merely its mechanics.
- The 20% coding-agent figure is not expected to apply: code is passthrough by design
  ("Compressing function bodies would remove exactly what they need"). Savings should concentrate in
  JSON/JSONL, and a low figure on code is the expected, correct result.

## Implementation Notes
Measure on identical input, always. The whole point of the MCP approach is that the paired
measurement makes ticket scale irrelevant.

Verify upstream behaviour from source or `--help` rather than from docs or from this ticket.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
