# Investigation — TCK-20260612-LOCAL-CTX-OPS

PHASE_TS: 2026-06-12T00:00:00Z

## What was already done

From HTTP-API ticket: `tools/search/Dockerfile`, `tools/search/docker-compose.yml`, `make search-server` (docker), `make search-server-stop`, `make search-server-logs`, `make search-server-fallback` (uvicorn), CLAUDE.md Proactive Tool Use HTTP entry, `docs/guidelines/agent_working_environment.md`.

From create-tickets.js: Step 0 semantic retrieval already wired at create-tickets.js:250.

## What still needs to be done

1. **`search-server-docker` target** — agent_working_environment.md references this name but Makefile has `search-server` (docker) and `search-server-fallback` (uvicorn). Need to add `search-server-docker` alias + rename targets to match docs.
2. **`knowledge-index-update` target** — calls `build --incremental`
3. **`--incremental` flag** in knowledge_search.py — cache-based: only re-embeds changed files
4. **`install-hooks` target** + `tools/hooks/post-commit-reindex.sh`
5. **CLAUDE.md After Work** — add `make knowledge-index-update` trigger
6. **implement-ticket SKILL.md** — add Step 0 context search

## Incremental build approach

sqlite-vec rows must stay rowid-aligned with BM25. Strategy: embedding cache (`knowledge-index/embeddings_cache.pkl`) maps `path → list[ndarray]`. On incremental:
- Load manifest (path → mtime), load cache
- Collect corpus, group by path
- Only call model.encode for new/changed paths
- Full DB rebuild using cached embeddings for unchanged paths
- Rebuild BM25 (fast — no model required)
- Write updated manifest + cache

Fast path: if nothing changed, print "Up to date" and exit 0 in seconds.
