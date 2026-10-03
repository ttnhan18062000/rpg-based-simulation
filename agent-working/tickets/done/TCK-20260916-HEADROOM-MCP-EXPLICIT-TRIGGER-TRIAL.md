---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL
phase: done
date: 2026-09-16
tags: [ai, mcp, process-improvement, optimization]
---

# TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL

## Title
Run the trial in MCP mode only — explicit `headroom_compress` on JSON/JSONL payloads, nothing
intercepted, because Claude Code + proxy offers no observe-only mode

## Status
DONE

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
- [x] Compression is exercised on at least three real payloads of different shapes, each with a
      recorded original-versus-compressed figure on identical input. **4 real payloads exercised**
      (`docs/REGISTRY.yaml`, a real junit XML, a real `agent-monitoring/data/2026-W36/tools.jsonl`
      shard, `graphify-out/graph.json`) — see Completion Summary for the exact numbers.
- [x] A `headroom_retrieve` round-trip is demonstrated recovering full original content. On
      `docs/REGISTRY.yaml`: `original_content == payload` confirmed via direct Python comparison,
      byte-for-byte.
- [x] The trial session's state is confined to the isolated directory from the first child, verified
      rather than assumed. Confirmed after the full trial: `~/.headroom` absent (`ls` returns "No
      such file or directory"); all new/updated state files (`ccr_store.db`, `session_stats.jsonl`,
      `savings_events.jsonl`, `config/install_id`) present under `HEADROOM_WORKSPACE_DIR`.
- [x] No repository file is modified by the compression itself. Every payload was **copied to a
      temp directory** before compression, never compressed in place — confirmed by `git status
      --porcelain` on the relevant repo paths before/after, no content diff attributable to the
      trial (the 2 unrelated diffs present — a hook-written monitoring shard and a REGISTRY.yaml
      timestamp — predate and are independent of this trial's own work).
- [x] Trial activity is attributable in `tools.jsonl` (via `session_id`) so the verdict ticket can
      separate it from concurrent sessions. The trial itself ran as `Bash` tool calls from this
      session, each carrying this session's own `session_id` per the normal `post_tool_hook.py`
      path — confirmed 100% reliable across the corpus by the sibling baseline ticket
      (`TCK-20260916-HEADROOM-HARM-CHECK-BASELINE`).
- [x] If measured savings on JSON/JSONL are materially below the claimed 60–95%, that is recorded as
      the finding — **not** retried with tuned settings until the number improves. **Recorded
      exactly as measured**: 0% on the real `tools.jsonl` shard and 0% on `graph.json` (JSON), for
      two different, real, diagnosed reasons — see Completion Summary. Payload selection was the
      ticket's own named list, not tuned to clear any bar.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` — blocks this
- `TCK-20260916-HEADROOM-HARM-CHECK-BASELINE` — provides the comparison point

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL/investigation.md`
- `stored_artifacts/TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL/plan.md`
- `stored_artifacts/TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL/test_plan.md`

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

## Systematic paired measurement (2026-09-20, this ticket's own real substance)

Ran against the **default install, no `[ml]`** — the working decision: let the trial conclude
honestly on what the base package delivers, since 7.5% (the smoke test's own large-payload figure)
is what anyone gets without extras. `[ml]` was never installed. Every occurrence of
`"Kompress model not ready"` below is recorded as a stated limitation of these numbers, not
elided — a reader must not mistake "the default install doesn't compress this" for "compression
doesn't work."

**Methodology**: each of the 4 payloads the ticket itself names was **copied to a temp directory**
(never compressed in place), then read and passed to a real MCP client's own `headroom_compress`
call (the `mcp` Python SDK's `stdio_client`/`ClientSession`, the same protocol Claude Code itself
speaks — not a bypass of it, and the same mechanism already used for the prior smoke test).
Nothing here started a proxy, set `ANTHROPIC_BASE_URL`, or ran `headroom learn`.

| Payload | Original bytes | Original tokens | Compressed tokens | Savings | Transform |
|---|---:|---:|---:|---:|---|
| `docs/REGISTRY.yaml` | 1,594,098 | 454,943 | 2,463 | **99.5%** | `router:mixed:0.01` |
| real junit XML (`pytest tests/tools/ ... --junit-xml`, 2767 real test results) | 427,185 | 122,024 | 122,024 | 0% | `router:noop` |
| real `agent-monitoring/data/2026-W36/tools.jsonl` shard | 14,993,340 | 4,283,819 | 4,283,819 | 0% | `inflation_guard:reverted` |
| `graphify-out/graph.json` | 54,306,933 | 15,516,275 | 15,516,275 | 0% | `router:noop` (see below) |

**Three genuinely different reasons for 0%, not one repeated failure — worth distinguishing:**

- **junit XML → `router:noop`**: the content router simply didn't classify this as a compressible
  shape under the degraded (non-ONNX) pure-Python detector.
- **The real `tools.jsonl` shard → `inflation_guard:reverted`, a new transform not seen in the
  smoke test.** The real log line: `"Optimization inflated tokens (4283819 -> 4293204); reverting
  to original messages"` — Headroom's own internal safety mechanism detected that its attempted
  transform would have made the payload **larger**, not smaller, and automatically reverted rather
  than applying a net-harmful "optimization." This is a genuinely positive finding about the
  library's own design (it isn't force-fitting a bad compression), but it also means **this
  ticket's own named #1 target payload type — real `agent-monitoring/*.jsonl` shards — got zero
  measured benefit** under the current install.
- **`graph.json` (54MB) → `router:noop`, but for an operational reason, not a classification
  one.** The real log line: `"ContentRouter single-cache-miss compression exceeded 20.0s; failing
  open via PASSTHROUGH"` — there is an internal ~20-second timeout on content analysis, and this
  payload's sheer size exceeded it, so the router failed open (passthrough, unmodified) rather
  than hang or error. A real, previously-undocumented operational limit for large local files,
  discovered by exercising a real 54MB payload, not a synthetic one.

**Only `docs/REGISTRY.yaml` shows the kind of savings the plan's decision criteria are looking
for**, and by a wide margin (99.5%) — plausibly because it's an extremely repetitive, structurally
uniform generated file (2585+ near-identical entries), the single most compression-friendly shape
among the 4 real payloads tried. **This is not cherry-picked**: all 4 payloads are exactly the
ticket's own named target list, tried once each, reported exactly as measured — the other 3
genuinely read 0%, for 3 different diagnosed reasons, none of them tuning.

**`headroom_retrieve` round-trip**: performed on `docs/REGISTRY.yaml` (the one real compression
that actually happened) — `original_content == payload` confirmed via direct Python string
comparison, byte-for-byte, not eyeballed.

**A clarification about `headroom_stats`' own aggregate view, checked directly rather than
assumed**: the `headroom_stats` tool call after this trial reported `combined.total_compressions:
7`, not 4 — initially looked like evidence of a concurrent session sharing the same isolated
store. Checked `session_stats.jsonl` directly: the extra 3 compress+retrieve pairs carry PIDs from
this *same* ticket's own earlier smoke-test runs (different subprocess PIDs from separate script
invocations, all mine, all earlier in this same day). `headroom_stats` is a **cumulative view over
the isolated store's full history**, not a per-invocation report — a real, useful clarification of
the tool's own behavior for whoever reads a `headroom_stats` call later and assumes it reflects
only their own immediately-preceding activity. The per-payload `results` this trial itself
recorded (the table above) are the authoritative paired measurement, not the aggregate.

**State isolation reconfirmed after the full trial**: `~/.headroom` absent (`ls` → "No such file or
directory"); `ccr_store.db`, `session_stats.jsonl`, `savings_events.jsonl`, `config/install_id` all
present under the isolated `HEADROOM_WORKSPACE_DIR`.

## Test Summary
No pytest suite applies — this is agent-tooling/measurement, verified by real execution against
the actual installed CLI and a real MCP client, not by unit tests. Full record: the prior smoke
test (3 synthetic payloads, 3 tools, 2 confirmed byte-exact round-trips) plus this ticket's own
systematic trial (4 real payloads, 1 confirmed byte-exact round-trip, 2 previously-undocumented
real transforms discovered — `inflation_guard:reverted` and the 20s content-router timeout).
`git status --porcelain` confirmed no repository file was modified by the compression itself
(every payload copied to `/tmp` first).

## Files Changed
- (via cherry-pick of `967f1efa4`, folded into PR #228, not a new commit on this ticket's own
  branch) `.mcp.json`, `tools/start_headroom_mcp.sh`, `requirements-knowledge.txt`, `.gitignore`.
- This ticket file — recorded the early-completed registration step, the smoke-test findings, and
  the systematic paired-measurement trial's own real results.
- No other repository file changed — every payload measured was a temp copy, never compressed in
  place.

## Completion Summary
Ran the systematic paired measurement this ticket exists for, on the default install (no `[ml]`,
per the working decision), against the 4 real payload types the ticket itself names — nothing
tuned to clear the plan's own decision bar. Result, reported honestly rather than smoothed into a
single misleading average: **3 of 4 real payloads measured 0% savings**, each for a different,
diagnosed reason (`router:noop` content-classification miss on the junit XML; a real, previously
undocumented `inflation_guard:reverted` safety transform on the real `tools.jsonl` shard — the
library's own protection against a net-harmful "optimization," discovered on this ticket's own
named #1 target payload type; and a real, previously undocumented ~20-second content-analysis
timeout failing open to passthrough on the 54MB `graph.json`). **1 of 4 — `docs/REGISTRY.yaml`, an
extremely repetitive generated file — measured 99.5% savings**, confirmed recoverable byte-for-
byte via a real `headroom_retrieve` round-trip. State isolation held under real, large-scale
functional use (`~/.headroom` absent throughout); no repository file was modified (every payload
copied to `/tmp` first); a real clarification about `headroom_stats`'s own cumulative-not-
per-invocation aggregate view is recorded so it isn't misread by whoever runs it next. This
ticket's own honest number — a wide spread from 0% to 99.5%, with the two largest and most
central target shapes (real monitoring JSONL, a large JSON graph) landing at 0% — is exactly the
kind of result the verdict ticket (child 4) needs to weigh against the plan's own ≥30% JSON/JSONL
bar; not chased further or re-run with different settings to see if the number improves.
