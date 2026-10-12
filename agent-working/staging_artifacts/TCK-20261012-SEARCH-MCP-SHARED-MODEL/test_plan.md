---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-MODEL
artifact_type: test_plan
tags: [ai, mcp]
---

# Test plan — TCK-20261012-SEARCH-MCP-SHARED-MODEL

## Proof Plan
| criterion | proof |
|---|---|
| Identical results proxy vs in-process | parity test: fake embedding model, small fixture index, same `search_core.search`, direct vs over HTTP, equal lists and scores |
| Fallback never breaks search | tests: no state file, stale pid, refused port, wrong token, slow server (timeout), garbage JSON: each returns the in-process result |
| Two sessions start at once | test: N threads call ensure on one state dir; exactly one server pid, all attach |
| Stale pidfile / foreign port | tests: dead pid and a foreign listener on the recorded port are replaced |
| Idle shutdown | test with a 1 s idle limit: process exits and state files are removed |
| Worktree key | test: worktree and main checkout resolve to one key |
| Staleness warning with the server down | existing staleness tests stay green |
| Memory and latency | scripted 9-session run (plan.md), numbers into the ticket |

Run `tests/static`, `tests/tools` (the whole directory) before any push.

## Recipe used for the investigation numbers
`measure.py` imported `tools/search_mcp.py` by path under `systemd-run --user --scope -p MemoryMax=3G` with `.venv-knowledge`, read `VmRSS` after import, after the first `_search`, and after five more; then ran the server's SQL path line for line (`search_server.py` 167-230) and compared top-5 doc ids and scores.
