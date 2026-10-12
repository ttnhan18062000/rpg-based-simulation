---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-MODEL
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20261012-SEARCH-MCP-SHARED-MODEL (Refs #520)

Host: `ubuntu` (6 vCPU, 9.9 GB). Unstaffed-seat exception: `tools/**` is agent-working's; codebase investigates at the planner's request. Measured 2026-10-12 against main `5951fdb71`, the main checkout's index (`agent-working/.index/knowledge-index/knowledge.db`), model `_ks._MODEL_NAME`, venv `.venv-knowledge` (Python 3.13.7). Scripts: scratchpad `measure.py` (not committed; recipe in `test_plan.md`).

## 1. Baseline memory (question 1)

Live `tools/search_mcp.py` processes, one per Claude session (`ps`, RSS):

| state | processes | RSS each |
|---|---|---|
| model loaded (the session has queried) | 5 | about 645 MB |
| not yet queried | 3 | about 58-62 MB |
| **total** | **8** | **about 3.2 GB of the 9.9 GB host** |

One process, scripted (`_search` on the real index):

| step | RSS | time |
|---|---|---|
| after importing `search_mcp` | 18 MB (a live idle process is about 60 MB with the MCP runtime) | 0.06 s |
| after the **first** query (loads `SentenceTransformer` and BM25) | **606 MB** | **6.05 s** |
| after five more queries | 607 MB (no growth) | 1.24 s for five |

So the loaded model is about 545 MB of pure overhead per session, and nothing frees it. `_ensure_loaded()` is already lazy, but `CLAUDE.md` makes `search_docs` the first call of any investigation, so in practice every active session pays it.

## 2. Result parity, server path against in-process path (question 2)

`tools/search_server.py` `/api/search` (lines 167-230) and `search_mcp._search` use different pipelines. The server runs one vector `MATCH` query with `k = min(top_k*4, 50)`, adds a BM25 score by `doc_ids.index`, and scores with `_ks._hybrid_score`. The MCP path calls `hybrid_retrieval.hybrid_fuse_and_filter` (reciprocal-rank fusion, authority and freshness filters). The server's own code has no `mode` and no staleness warning.

Measured on the same loaded model, five queries, top 5 each (the server path reproduced line for line, because `fastapi` is not in `.venv-knowledge`, see section 3):

| query | overlap of the 5 doc ids | same order | same scores |
|---|---|---|---|
| damage formula | 3 | no | no |
| how does goal interruption work | 2 | no | no |
| import linter contracts | 4 | no | no |
| working log append helper | 3 | no | no |
| regional trauma ecology | 4 | no | no |

**All five differ**, in set, order and scores. A proxy to the existing server would silently change what `search_docs` returns, so the existing `/api/search` cannot be the shared backend.

## 3. Server availability on this VM (question 3)

- Nothing listens on :8765 (`ss -ltn`). Docker runs, but there is no search image here, and `agent_working_environment.md` records the image build as unverified. I did not build one (docker builds are not bounded by the memory cap).
- `.venv-knowledge` has `uvicorn`, `starlette`, `pydantic`, `mcp`, `httpx`, `anyio`, `sentence_transformers`, `sqlite_vec`, **but not `fastapi`**. `make search-server` (`uvicorn tools.search_server:app`) therefore cannot start under the knowledge venv today; it needs `.venv`, which has no `sentence_transformers`.
- Consequence for the plan: a shared server for this fleet must not depend on `fastapi`. The stdlib `http.server` needs no dependency at all.
- Index and worktrees: `search_mcp._resolve_index_dir` already reads the main checkout's index when a worktree has none; `search_server.py` does not (it uses `_ks._DEFAULT_DB` relative to its own checkout).

## 4. Who starts and keeps the server alive (question 4)

Today nobody: the Docker server is owner-started and unused (nothing on :8765). Candidate owners:

| owner | for | against |
|---|---|---|
| owner-run Docker | already documented | unverified image, needs the owner, wrong venv, different results |
| systemd user unit | survives anything | per-host setup, outside the repo, easy to forget on a new host |
| auto-spawn by the first session's launcher | no setup, same on every host | needs a lock, stale-state and idle-exit rules |

`$XDG_RUNTIME_DIR` (`/run/user/1000`, mode 0700, tmpfs, cleared on logout or reboot) exists here and is per user and outside the repo, which suits a lock, pid and port record.

## 5. Findings that shape the plan

1. The saving is real and large: 5 loaded sessions hold about 3.1 GB; one shared model would hold about 0.6 GB plus about 60 MB per session.
2. Identical results must come from one core search function, not from reconciling two (section 2).
3. The server cannot be `search_server.py` as it is: different results, `fastapi` missing in the knowledge venv.
4. The staleness warning needs only the manifest, not the model (`_ks.index_staleness`), so it can stay client-side and keep working with the server down.
5. A fixed port (8765) invites collisions with foreign processes; an OS-assigned port recorded in a state file removes that class.
