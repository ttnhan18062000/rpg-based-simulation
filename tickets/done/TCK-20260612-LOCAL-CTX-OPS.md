---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-LOCAL-CTX-OPS
phase: open
date: 2026-06-12
tags: [tooling, rag, knowledge-search, docker, ops, workflow]
---

# TCK-20260612-LOCAL-CTX-OPS

## Title
Knowledge Search Ops: Docker Deployment, Incremental Reindex, and Skill/Workflow Integration

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The core search tickets (DOCS-CORPUS, HYBRID-SEARCH, HTTP-API) leave four operational gaps: (1) the server dies when the terminal closes — Docker is the primary deployment method (`make search-server-docker`); `make search-server` is kept as a no-Docker fallback only; (2) full rebuild from scratch is the only reindex path — incremental update based on file mtimes is needed for day-to-day use; (3) agent skills and workflows (`implement-ticket`, `create-tickets`, CLAUDE.md After Work step) need to be wired to query and maintain the index automatically; (4) there is no written guide for setting up and operating the search environment — agents and developers starting fresh need a single reference doc.

## Scope

### 1. Docker Deployment

- New file: `tools/search/Dockerfile`
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  # Pre-download the embedding model so container start is fast
  RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
  COPY tools/ tools/
  EXPOSE 8765
  HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8765/api/health || exit 1
  CMD ["uvicorn", "tools.search_server:app", "--host", "0.0.0.0", "--port", "8765"]
  ```
- New file: `tools/search/docker-compose.yml`
  ```yaml
  services:
    search:
      build:
        context: ../..
        dockerfile: tools/search/Dockerfile
      ports:
        - "8765:8765"
      volumes:
        - ../../knowledge-index:/app/knowledge-index:ro
      restart: unless-stopped
  ```
  The `knowledge-index/` is **read-only** in the container — rebuilds happen on the host via `make knowledge-index` or `make knowledge-index-update`, then the running container picks up the new index on its next request (sqlite-vec opens the db per-request, not at startup, so no restart is needed after a rebuild).
- New Makefile targets:
  ```makefile
  search-server-docker: ## Start knowledge search server in Docker (persistent)
      docker compose -f tools/search/docker-compose.yml up -d

  search-server-stop: ## Stop knowledge search Docker container
      docker compose -f tools/search/docker-compose.yml down

  search-server-logs: ## Tail knowledge search server logs
      docker compose -f tools/search/docker-compose.yml logs -f
  ```
- `make search-server-docker` is the **primary** way to run the server. Update its Makefile comment to say "primary — persistent, survives terminal close".
- `make search-server` is kept as a **fallback** for environments without Docker. Update its Makefile comment to say "fallback only — exits when terminal closes; use search-server-docker instead".

### 2. Incremental Reindex

- Add `build --incremental` flag to `tools/knowledge_search.py`:
  - Load the existing `knowledge-index/manifest.json` (written by full `build`): maps `source_path → {mtime, chunk_ids[]}`
  - Compare current file mtimes against manifest
  - For changed or new files: delete their existing chunk vectors from sqlite-vec and bm25.pkl, re-embed and re-insert
  - For deleted files: remove their chunk vectors
  - For unchanged files: skip entirely
  - Write updated manifest
  - Print: `Incremental update: N files changed, M chunks updated, K files skipped`
- New file: `knowledge-index/manifest.json` (written by both full `build` and `--incremental`; gitignored)
- New Makefile target:
  ```makefile
  knowledge-index-update: ## Incremental reindex (only changed files; faster than full rebuild)
      python3 tools/knowledge_search.py build --incremental
  ```
  Full `make knowledge-index` remains available for clean rebuilds (e.g., after embedding model change).

### 3. Git Post-Commit Hook

- New file: `tools/hooks/post-commit-reindex.sh`
  ```bash
  #!/usr/bin/env bash
  # Auto-trigger incremental reindex when docs/ or tickets/done/ changed in the last commit
  changed=$(git diff --name-only HEAD~1 HEAD 2>/dev/null)
  if echo "$changed" | grep -qE '^(docs/|tickets/done/)'; then
    if [ -f knowledge-index/knowledge.db ]; then
      echo "[knowledge-search] Relevant files changed — running incremental reindex..."
      python3 tools/knowledge_search.py build --incremental
    fi
  fi
  ```
- New Makefile target:
  ```makefile
  install-hooks: ## Install git hooks (post-commit reindex)
      cp tools/hooks/post-commit-reindex.sh .git/hooks/post-commit
      chmod +x .git/hooks/post-commit
  ```
  Hook installation is **opt-in** (`make install-hooks`), not automatic on checkout. Add to `README` or `CONTRIBUTING` as a recommended setup step.
- Hook is a no-op if `knowledge-index/` doesn't exist yet — does not block commits.

### 4. Skill and Workflow Integration

#### `implement-ticket` skill — add Step 0 context search

Before Phase 1 (Scope) of the implement-ticket pipeline, add:

```
Step 0: Context search (if knowledge index exists)
  Run: python3 tools/knowledge_search.py query "<ticket title + request summary>" --top-k 5
  OR:  curl -s -X POST http://localhost:8765/api/search -d '{"query": "...", "top_k": 5}'
       (prefer HTTP if server is running; fall back to CLI if not)
  For each result: note source_path and excerpt — use as warm-start context for investigation.
  If knowledge-index/ does not exist: skip silently.
```

Update `.claude/skills/implement-ticket/SKILL.md` (or equivalent) to include this step.

#### `create-tickets` workflow — confirm Step 0 is wired

`TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH` already specifies adding Step 0 to `create-tickets.js`. This ticket verifies it is implemented and working end-to-end (not just specified).

#### CLAUDE.md — After Work step addition

Add to the **After Work** section of `CLAUDE.md`:

```
- If any files under `docs/` were created or modified: run `make knowledge-index-update`
  to keep the agent context search index current.
```

This ensures the index never drifts more than one session behind the docs.

#### CLAUDE.md — Proactive Tool Use table addition (backup entry)

Add a CLI fallback entry to the Proactive Tool Use table for when the HTTP server is not running:

```
| Answering project-specific mechanics/architecture questions + server not on :8765 |
  python3 tools/knowledge_search.py query "<question>" --top-k 5
```

### 5. Agent Working Environment Setup Documentation

- New file: `docs/guidelines/agent_working_environment.md`
- Covers the full lifecycle an agent or developer needs to operate the context search environment:
  1. **Prerequisites** — Docker Engine, Python 3.11+, `pip install -r requirements.txt`
  2. **First-time setup** — build the index, start the Docker server, verify health
  3. **Daily workflow** — server is already running; what to do when docs change
  4. **Index update rules** — when to use `make knowledge-index-update` vs `make knowledge-index` (full rebuild)
  5. **Command reference** — all `make` targets with one-line descriptions
  6. **Verifying search** — example CLI and HTTP queries with expected output shape
  7. **Fallback mode** — `make search-server` when Docker is unavailable
  8. **Git hook setup** — `make install-hooks` for automatic reindex on commit
  9. **Troubleshooting** — server not responding, index stale, model download slow, first-commit hook guard
- This doc is the **single reference** linked from CLAUDE.md. Agents starting fresh in this repo read it before their first context search call.
- Add a link to it in the CLAUDE.md Graphify Integration section alongside the existing `graphify-out/GRAPH_REPORT.md` reference.

## Out of Scope
- CI/CD deployment (this is a local developer tool only)
- Remote or cloud hosting
- Authentication on the Docker container (localhost only)
- Auto-start on system boot (launchd/systemd; use `make search-server-docker` with `restart: unless-stopped` instead)
- Kubernetes or multi-replica setup

## Acceptance Criteria

### Docker
- [ ] `make search-server-docker` starts the container; `curl http://localhost:8765/api/health` returns `{"status": "ok", ...}`
- [ ] Container survives terminal close and system restart (`restart: unless-stopped`)
- [ ] After running `make knowledge-index-update` on the host, the next query to the running container returns results from the newly indexed content (no container restart required)
- [ ] `make search-server-stop` cleanly stops the container
- [ ] Container healthcheck is configured and visible in `docker ps`

### Incremental Reindex
- [ ] `make knowledge-index-update` completes in under 60 seconds when fewer than 10 files changed
- [ ] A file that was not modified does not have its vectors deleted and re-inserted (verify via manifest mtime comparison)
- [ ] Deleting a doc from `docs/` and running `--incremental` removes its chunks from the index
- [ ] `manifest.json` is created/updated by both `build` and `build --incremental`
- [ ] `make knowledge-index` (full rebuild) still works correctly after incremental runs

### Git Hook
- [ ] `make install-hooks` copies and chmods the hook
- [ ] After a commit that touches `docs/`, the hook triggers `build --incremental` automatically
- [ ] After a commit that touches only `src/`, the hook exits silently without reindexing
- [ ] If `knowledge-index/` does not exist, the hook exits without error

### Skill/Workflow Integration
- [ ] `implement-ticket` skill documentation includes Step 0 context search with both HTTP and CLI invocation paths
- [ ] `CLAUDE.md` After Work section includes `make knowledge-index-update` trigger for doc changes
- [ ] `CLAUDE.md` Proactive Tool Use table includes both HTTP (`localhost:8765`) and CLI fallback paths

### Setup Documentation
- [ ] `docs/guidelines/agent_working_environment.md` exists and covers all 9 sections listed in Scope §5
- [ ] First-time setup section walks through: `pip install`, `make knowledge-index`, `make search-server-docker`, health check verification
- [ ] Command reference table is complete and matches the actual Makefile targets
- [ ] Fallback mode section documents `make search-server` with a clear "Docker not available" framing
- [ ] CLAUDE.md links to the doc from the Graphify Integration section

## Related Tickets
- TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH (foundation)
- TCK-20260612-LOCAL-CTX-DOCS-CORPUS (must be done — provides docs/ chunks)
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH (must be done — hybrid scoring)
- TCK-20260612-LOCAL-CTX-HTTP-API (must be done — server being containerized)
- TCK-20260612-LOCAL-CTX-EVAL (independent)

## Related Docs
- context_search_feature.md §12 (Deployment Model), §14 (Observability)
- CLAUDE.md §Workflow Rule After Work, §Proactive Tool Use, §Graphify Integration
- .claude/skills/implement-ticket/SKILL.md
- docs/guidelines/agent_working_environment.md (deliverable of this ticket)

## Related Stored Artifacts
- None.

## Related Code Areas
- `tools/search/Dockerfile` (new)
- `tools/search/docker-compose.yml` (new)
- `tools/hooks/post-commit-reindex.sh` (new)
- `tools/knowledge_search.py` (extend: `--incremental` flag, manifest.json write)
- `knowledge-index/manifest.json` (new artifact, gitignored)
- `Makefile` (new targets: `search-server-docker`, `search-server-stop`, `search-server-logs`, `knowledge-index-update`, `install-hooks`)
- `CLAUDE.md` (After Work step, Proactive Tool Use table, link to setup doc)
- `.claude/skills/implement-ticket/SKILL.md` (Step 0 addition)
- `docs/guidelines/agent_working_environment.md` (new — agent setup reference)

## Assumptions / Open Questions
- sqlite-vec opens the db file per-query, not at server startup — verify this before claiming the "no restart needed after reindex" behavior; if it caches at startup, add a `POST /api/reload` endpoint or use file-watch reload
- `restart: unless-stopped` in docker-compose requires Docker Desktop or Docker Engine to be running; document this prerequisite in `make search-server-docker` help text
- `git diff HEAD~1 HEAD` in the post-commit hook fails on the very first commit (no HEAD~1); add a guard: `git rev-parse HEAD~1 2>/dev/null || exit 0`

## Implementation Notes

- Docker assets (Dockerfile, docker-compose.yml, `make search-server`/stop/logs targets) were already done in HTTP-API ticket; this ticket adds `search-server-docker` as the primary named target and renames `search-server` to the uvicorn fallback, matching agent_working_environment.md naming
- Incremental build moves dep import AFTER the "nothing changed" early-exit so the fast path (manifest unchanged) works without sentence-transformers installed
- `embeddings_cache.pkl` stores `{path: [embedding_list, ...]}` in the index dir; cache is updated per changed file and persisted after each incremental run
- `create-tickets.js` Step 0 was already wired (line 250) — verified, no change needed
- implement-ticket SKILL.md had no Step 0 — added it before the Scope phase entry

## Test Summary

- 6 new tests in `TestManifestHelpers` class in `test_knowledge_search.py`; all pass
- Full tools suite: 403 passed, 28 skipped; no regressions

## Files Changed

- `tools/knowledge_search.py` (added `_write_manifest`, `_load_manifest`, `_load_embedding_cache`, `_save_embedding_cache`, `cmd_build_incremental`; extended `cmd_build` to write manifest/cache; added `--incremental` flag)
- `tools/hooks/post-commit-reindex.sh` (new git hook)
- `Makefile` (added `search-server-docker`, `knowledge-index-update`, `install-hooks`; renamed targets to match docs)
- `CLAUDE.md` (After Work: added `make knowledge-index-update` step)
- `.claude/skills/implement-ticket/SKILL.md` (added Step 0 context search)
- `tests/tools/test_knowledge_search.py` (added `TestManifestHelpers` group, 6 tests)

## Completion Summary

Incremental reindex implemented with embedding cache; `make knowledge-index-update` fast-paths when nothing changed and only re-embeds changed files. Git hook auto-triggers on relevant commits. All Makefile target names now match agent_working_environment.md. implement-ticket skill wired with Step 0 context search. 403 tests passing.
