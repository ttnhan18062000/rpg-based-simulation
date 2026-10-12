---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-MODEL
artifact_type: report
tags: [ai, mcp]
---

# Measurement and parity scripts — TCK-20261012-SEARCH-MCP-SHARED-MODEL

Re-run the acceptance gate (same top-k from the shared server and in-process, and the memory table in `../plan.md`).

- `sessions.py`: N stdio MCP sessions, `after` (shared server) or `before` (in-process); writes `sessions_<mode>_<n>.json`
  with per-session and server RSS/PSS, totals, MemAvailable, in-process fallback count, first-query latency and the
  answers to five fixed queries. Parity = `parity_answers` of an `after` run equals that of a `before` run.
- `measure.py`: one process, RSS idle / after first query / warm, and the old FastAPI server's SQL path against
  `search_mcp._search` (the five queries differed: why `search_server.py` could not be the shared backend).

Run under `systemd-run --user --scope -p MemoryMax=2500M -p MemorySwapMax=0`, one at a time, with the knowledge venv
(`.venv-knowledge`) from a checkout that has `agent-working/.index/knowledge-index/`. Nine in-process sessions need about
5.7 GB; measure 2 and extrapolate on a small host.

Results of the 2026-10-12 run on host `ubuntu` are in `../plan.md` ("Measured result"): 5 of 5 queries byte-identical,
1,220 MB RSS for 9 shared sessions against about 5.7 GB in-process.
