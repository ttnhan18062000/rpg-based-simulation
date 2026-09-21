# Test Plan — TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL

No pytest suite applies — this ticket measures a third-party tool's real behavior against real
repo payloads, not repository code.

| Case | Verification |
|---|---|
| At least 3 real payloads of different shapes, paired measurement | 4 real payloads measured: `docs/REGISTRY.yaml`, a real junit XML, a real `tools.jsonl` shard, `graph.json` — each compressed once on identical (unmodified) input |
| `headroom_retrieve` round-trip recovers full original content | `docs/REGISTRY.yaml`: `original_content == payload` confirmed via direct Python string comparison |
| No repository file modified by compression | `git status --porcelain` on `docs/`, `agent-monitoring/`, `graphify-out/` before/after — no diff attributable to the trial (2 pre-existing, unrelated diffs identified and ruled out) |
| Trial activity attributable via `session_id` | Trial ran as this session's own `Bash` tool calls, `session_id` populated per the normal hook path (100% reliability already confirmed by the sibling baseline ticket) |
| State confined to the isolated directory | `~/.headroom` absent (`ls` → not found) both before and after; `ccr_store.db`/`session_stats.jsonl`/`savings_events.jsonl`/`config/install_id` all present under `HEADROOM_WORKSPACE_DIR` |
| Low savings recorded honestly, not retried to improve | 3 of 4 payloads read 0%, each with a different diagnosed real cause (`router:noop`, `inflation_guard:reverted`, a 20s content-analysis timeout); recorded as-is |
| `headroom_stats` aggregate discrepancy explained, not assumed | `session_stats.jsonl` read directly; extra compress/retrieve pairs traced to this same session's own earlier smoke-test PIDs, not a concurrent session |
| Default install only, no `[ml]` | Confirmed: no install command run during this pass; the "Kompress model not ready" warning is present in every compress call's own stderr output |

Executed: 4 real `headroom_compress` calls (one per payload) plus 1 `headroom_retrieve` call and 1
`headroom_stats` call, all via a real MCP client script (`mcp` SDK's `stdio_client`/
`ClientSession`) launched through `tools/start_headroom_mcp.sh`, the same launcher a real Claude
Code session uses. Full raw JSON output recorded in the ticket's own Implementation Notes.
