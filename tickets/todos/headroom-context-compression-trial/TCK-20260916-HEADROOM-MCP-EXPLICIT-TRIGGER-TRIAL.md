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
- ~~Assumed the MCP server can be registered for one session without becoming globally active for
  every session on this machine~~ — **resolved by `TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-
  REVERT`**: registration via this repo's own `.mcp.json` is genuinely repo-scoped, demonstrated
  (not inferred) via `claude mcp list` run from inside this repo versus from a directory with no
  `.mcp.json`. No longer an open question.
- The 20% coding-agent figure is not expected to apply: code is passthrough by design
  ("Compressing function bodies would remove exactly what they need"). Savings should concentrate in
  JSON/JSONL, and a low figure on code is the expected, correct result.

## Implementation Notes
Measure on identical input, always. The whole point of the MCP approach is that the paired
measurement makes ticket scale irrelevant.

Verify upstream behaviour from source or `--help` rather than from docs or from this ticket.

**Registration is already permanent on `main` (2026-09-20) — the earlier "cherry-pick 967f1efa4"
note is spent and no future session needs it.** `.mcp.json`'s `headroom` entry and
`tools/start_headroom_mcp.sh` landed on `main` via PR #228 and are there unconditionally now, not
something any session needs to reapply. The only thing that remains machine-level rather than
repo-level is the package install itself: if this machine's `.venv` or pip cache is ever cleared,
`headroom-ai` would need to be reinstalled — that step still needs the user's own shell (this
sandbox's own `files.pythonhosted.org` block is confirmed, not worked around), never
`headroom mcp install`/`headroom wrap` as a shortcut (both write to every detected agent's
user-scope config, confirmed from the real CLI's own `--help`).

**Registration was completed early, 2026-09-20 (PR #228), with a real functional smoke test —
this ticket's own step 1 is done, do not redo it.** After the user's second install attempt
actually landed `headroom-ai==0.37.0` in `.venv`, `967f1efa4` was cherry-picked onto the batch
branch and verified with the same real-evidence discipline as the isolation ticket: `claude mcp
list` connects from inside this repo and shows nothing from a directory with no `.mcp.json`;
`~/.claude.json` stayed structurally clean (no `mcpServers` key added anywhere); this worktree
still has no `.venv` of its own, so the launcher's absolute-path resolution is still doing real
work.

**Beyond registration, a real MCP client (the `mcp` Python SDK's `stdio_client`/`ClientSession`,
speaking the actual protocol Claude Code would use — not a bypass of it) called all three tools
against synthetic, non-sensitive payloads. Load-bearing findings for this ticket's own upcoming
systematic measurement, found here so they don't surprise whoever runs it next:**

- **All three tools work at the protocol level.** `headroom_compress`, `headroom_retrieve`, and
  `headroom_stats` all returned valid, well-formed responses across 3 calls each — no MCP-level
  errors. A `headroom_retrieve` round-trip on both a small (2536-byte) and a large (66500-byte)
  synthetic JSONL payload returned the exact original content, byte-for-byte
  (`original_content == payload` confirmed via direct Python comparison, not eyeballed).
- **The base (no-`[ml]`-extra) install measurably degrades compression, not just disables an
  unrelated feature.** Every compress call printed: `"Native content detection requires ONNX
  Runtime 1.24+; using pure-Python detection for this process."` A small (~700-token), pure-JSON,
  anomaly-free payload got `transforms: ["router:noop"]` — 0% savings, no compression attempted at
  all — plus an explicit second warning: `"Kompress model not ready; requests will not be
  compressed. Check HuggingFace connectivity or pre-download: headroom-ai[ml] + first-run
  warmup."` A payload containing one `ERROR`-level line got `"router:protected:error_output"` —
  also 0%, but that one is *correct*, expected behavior (the plan doc's own "keeps failures, drops
  passing noise" design). A larger (~19000-token) clean JSONL payload got `"router:mixed:0.93"` —
  **7.5% savings**, real but far below the claimed 60–95% for JSON specifically, plausibly because
  the degraded pure-Python content detector isn't confidently classifying repetitive JSONL as
  `json` (a confident classification would presumably route to `SmartCrusher`, not a generic
  `mixed` bucket) — **this specific causal chain is a hypothesis, not confirmed**, and is exactly
  the kind of question this ticket's own systematic measurement should resolve deliberately rather
  than have surface as a surprise mid-trial.
- **Practical consequence for this ticket's own Acceptance Criteria**: AC1's "materially below the
  claimed 60–95%" framing may already be the expected outcome under the current install profile,
  not a negative trial result — measure it and record it as such, but the possible confound (no
  `[ml]` extra, degraded content detection) should be named alongside the number, not omitted.
  Installing `[ml]` is a real, separate, larger decision (pulls `onnxruntime` + `transformers`,
  the exact memory-pressure risk the base-only install was chosen to avoid) — **do not install it
  without asking first**, the same discipline the isolation ticket applied to the base install.
- **State isolation held under real functional use, not just at rest.** All new files this smoke
  test produced (`ccr_store.db`, `session_stats.jsonl`, `savings_events.jsonl`,
  `config/install_id`) landed under the isolated `HEADROOM_WORKSPACE_DIR`; `~/.headroom` stayed
  absent throughout.

## Test Summary
No pytest suite applies — this is agent-tooling/config, verified by real execution against the
actual installed CLI and a real MCP client, not by unit tests. See the Implementation Notes above
for the full smoke-test record (3 payloads, 3 tools, 2 confirmed byte-exact round-trips).

## Files Changed
- (via cherry-pick of `967f1efa4`, folded into PR #228, not a new commit on this ticket's own
  branch) `.mcp.json`, `tools/start_headroom_mcp.sh`, `requirements-knowledge.txt`, `.gitignore`.
- This ticket file — recorded the early-completed registration step and the smoke-test findings.

## Completion Summary
_Still open — registration (this ticket's own step 1) is done; the systematic paired measurement
across real payload types (the ticket's actual substance) has not started._
