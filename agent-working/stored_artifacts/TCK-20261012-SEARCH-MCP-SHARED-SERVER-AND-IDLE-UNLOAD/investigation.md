---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD
artifact_type: investigation
tags: [ai, mcp, process-improvement]
---

# investigation — TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD

## Findings
- `search_mcp._search` fuses with `hybrid_retrieval.hybrid_fuse_and_filter`; `search_server` used a vector top-k with `_hybrid_score`, no staleness, only its own checkout's index. A bare proxy would have changed results.
- `index_staleness` is stat-only and anchored to the calling checkout's corpus, so the session must compute it, not the server.
- Model weights are not the whole footprint: sentence_transformers/torch are imported lazily on the first query and stay resident after the model is dropped.

## Measurements (u24desktop-Virtual-Machine, .venv-knowledge 3.12, 2026-10-12, this worktree's 48 MB index)
| state | RSS |
|---|---|
| `search_mcp` imported, no query | 24 MB |
| after first in-process query (model loaded) | 598 MB |
| after idle unload (5 s test setting) | 434 MB (-164 MB; torch libraries remain) |
| after the next query (reload) | 611 MB |
| shared-server path after a query (`model_loaded` false) | 30 MB |
| the `uvicorn tools.search_server:app` process itself | 622 MB |
Top 3 doc ids were identical on the in-process and shared-server paths for the same query. The server was run with `python -m uvicorn tools.search_server:app --host 127.0.0.1 --port 8765` (the `make search-server` command without `--reload`; Docker is TLS-blocked on this host). Not measured: a live index-mismatch (covered by unit tests), the Docker image.
