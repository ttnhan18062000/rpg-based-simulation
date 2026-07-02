---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [setup, tooling, knowledge-search, docker, rag]
---

# Agent Working Environment Setup

This document is the single reference for setting up and operating the local context search environment. Read it once before your first search call. It covers first-time setup, daily workflow, all commands, and troubleshooting.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker Engine | 24+ | Required for `make search-server-docker` (primary) |
| Python | 3.11+ | For index build and CLI fallback |
| `pip install -r requirements.txt` | — | Core app deps: `fastapi`, `uvicorn`, etc. Installed by CI too. |
| `pip install -r requirements-knowledge.txt` | — | Knowledge-search stack: `torch`, `sentence-transformers`, `sqlite-vec`, `rank_bm25`. Local agent tooling only — CI never installs this. |

First-time model download: `all-MiniLM-L6-v2` (~22 MB) is downloaded automatically on first `make knowledge-index`. Subsequent builds use the local cache.

---

## First-Time Setup

Run these once after cloning or after a clean checkout.

```bash
# 1. Install core Python dependencies
pip install -r requirements.txt

# 1b. Install the knowledge-search stack (torch must come from the CPU wheel index)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-knowledge.txt

# 2. Build the full knowledge index (tickets + investigations + docs/)
#    Expected: ~3,000–4,000 chunks; takes 3–5 minutes on first run (model download included)
make knowledge-index

# 3. Start the search server (Docker — primary)
make search-server-docker

# 4. Verify the server is healthy
curl -s http://localhost:8765/api/health
# Expected: {"status": "ok", "chunks": <N>, "model": "sentence-transformers/all-MiniLM-L6-v2", ...}
```

The Docker container runs with `restart: unless-stopped` — it will come back automatically after system restarts as long as Docker Engine is running.

---

## Daily Workflow

The server is already running from first-time setup. Normal working sessions need no action unless docs change.

### After modifying or adding a file under `docs/`

The CLAUDE.md After Work rule also covers this — it is repeated here for completeness.

```bash
# Incremental reindex: only re-embeds changed files (~10–60 seconds)
make knowledge-index-update
```

The running Docker container picks up the new index on its next query — no restart needed.

### After closing a ticket (ticket moved to `tickets/done/`)

```bash
make knowledge-index-update
```

Same command. The incremental build detects the new file in `tickets/done/` and adds it.

### Automatic reindex on commit (optional but recommended)

```bash
# Install git post-commit hook — runs make knowledge-index-update automatically
# when a commit touches docs/ or tickets/done/
make install-hooks
```

Once installed, the hook is silent on unrelated commits and self-skips if `knowledge-index/` does not exist.

---

## Command Reference

| Command | What it does |
|---|---|
| `make knowledge-index` | Full rebuild — embeds all docs, tickets, investigations from scratch. Use after model change or first setup. |
| `make knowledge-index-update` | Incremental rebuild — re-embeds only changed/new/deleted files. Use after normal doc or ticket changes. |
| `make search-server-docker` | **Primary.** Start the search server in Docker (persistent, survives terminal close and system restart). |
| `make search-server-stop` | Stop the Docker container. |
| `make search-server-logs` | Tail the Docker container logs. |
| `make search-server` | **Fallback only** (no Docker). Starts uvicorn directly; exits when the terminal closes. |
| `make install-hooks` | Install git post-commit hook for automatic incremental reindex. |
| `make eval-search` | Run the curated 40-query evaluation set; reports Recall@5 and MRR@10. |

---

## Verifying Search Works

### HTTP (primary — requires Docker server running)

```bash
# Natural-language query
curl -s -X POST http://localhost:8765/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how does the damage formula work", "top_k": 5}' \
  | python3 -m json.tool

# Exact-term query
curl -s -X POST http://localhost:8765/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "WorldRepository", "top_k": 3}'

# Filter by section
curl -s -X POST http://localhost:8765/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authoritative mutation phases", "top_k": 5, "filters": {"section": "engine"}}'
```

Expected response shape:

```json
{
  "query": "how does the damage formula work",
  "top_k": 5,
  "results": [
    {
      "doc_id": "mechanics/02_combat_laws#h2-damage-formula-001",
      "title": "Combat Laws",
      "heading": "Damage Formula",
      "source_path": "docs/mechanics/02_combat_laws.md",
      "section": "mechanics",
      "score": 0.84,
      "semantic_score": 0.79,
      "keyword_score": 0.62,
      "excerpt": "..."
    }
  ]
}
```

### CLI (fallback — no server required)

```bash
python3 tools/knowledge_search.py query "how does the damage formula work" --top-k 5
python3 tools/knowledge_search.py query "WorldRepository" --top-k 3 --mode keyword
python3 tools/knowledge_search.py query "stamina pressure combat" --top-k 5 --mode hybrid
```

---

## MCP Setup (Agent-Native Tool — Recommended)

`search_docs` is a native Claude Code MCP tool — no curl or bash needed.

### Registration

`.mcp.json` (project root) contains:

```json
{
  "mcpServers": {
    "knowledge-search": {
      "command": "python3",
      "args": ["tools/search_mcp.py"],
      "description": "Local semantic search over project docs, tickets, and investigations"
    }
  }
}
```

Claude Code spawns `tools/search_mcp.py` on startup. The MCP server loads the index once and stays resident — it does **not** require the Docker HTTP server to be running.

### Verify MCP is working

```bash
make mcp-server-test
```

Or restart Claude Code and confirm `search_docs` appears in `/tools`.

### Using the MCP tool (agent calls this natively)

```
search_docs(query="how does the damage formula work", top_k=5)
search_docs(query="WorldRepository", top_k=3, mode="keyword")
search_docs(query="authoritative mutation phases", top_k=5, section="engine")
search_health()
```

No curl. No bash. Results arrive as a structured tool response directly in context.

### Priority order for agents

| Priority | Method | When |
|---|---|---|
| 1 | `search_docs` MCP tool | MCP server registered (normal case) |
| 2 | `curl POST http://localhost:8765/api/search` | Docker HTTP server running, MCP not registered |
| 3 | `python3 tools/knowledge_search.py query "..." --top-k 5` | No server, no MCP — CLI fallback |

---

## Agent Usage Pattern

In skill or workflow code, the agent calls the MCP tool natively. If MCP is not available, fall back to HTTP, then CLI:

```
# 1. MCP tool (preferred — native, no bash)
search_docs(query=QUERY, top_k=5)

# 2. HTTP fallback (if MCP not registered)
if curl -sf http://localhost:8765/api/health > /dev/null 2>&1; then
  curl -s -X POST http://localhost:8765/api/search \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$QUERY\", \"top_k\": 5}"

# 3. CLI fallback (no server at all)
else
  python3 tools/knowledge_search.py query "$QUERY" --top-k 5
fi
```

If none of the above is available, skip the search step silently and continue — do not block the workflow.

---

## Fallback Mode (No Docker)

If Docker is not available in your environment:

```bash
# Start the server directly (exits when terminal closes)
make search-server

# Keep it running in the background
nohup make search-server &> /tmp/search-server.log &

# Or use a separate terminal window
```

All HTTP queries work identically. The only difference is the server does not auto-restart.

---

## Index Lifecycle Rules

| Situation | Command |
|---|---|
| First setup or after changing embedding model | `make knowledge-index` (full) |
| After adding/editing a doc in `docs/` | `make knowledge-index-update` |
| After closing a ticket (new file in `tickets/done/`) | `make knowledge-index-update` |
| After deleting a doc | `make knowledge-index-update` |
| Index seems stale or returning wrong results | `make knowledge-index` (full rebuild) |
| Switching to a different embedding model | `make knowledge-index` (full rebuild) |

---

## Troubleshooting

**Server not responding (`connection refused` on :8765)**
```bash
make search-server-logs        # check container logs
docker ps                      # verify container is running
make search-server-docker      # restart if stopped
```

**Index stale after doc changes**
```bash
make knowledge-index-update    # incremental reindex
# verify with: curl http://localhost:8765/api/health  (check "chunks" count increased)
```

**Model download is slow on first build**

`all-MiniLM-L6-v2` is ~22 MB. It downloads once to the sentence-transformers cache and is baked into the Docker image at build time. If `make knowledge-index` hangs on the first run, wait — it is downloading. Subsequent runs use the cache.

**Git hook failing on first commit (no `HEAD~1`)**

The hook guards against this: `git rev-parse HEAD~1 2>/dev/null || exit 0`. If you see an error, verify the hook file was installed correctly: `cat .git/hooks/post-commit`.

**`sqlite-vec` version mismatch**

If `make knowledge-index` fails with a sqlite-vec error, check: `python3 -c "import sqlite_vec; print(sqlite_vec.__version__)"`. The required minimum version is listed in `requirements.txt`.

**Search returns no results for a doc that exists**

Run `make knowledge-index-update`. The file may have been added after the last build. If the problem persists after update, run `make knowledge-index` (full rebuild) and re-check.

---

## Related Tickets

- `TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH` — CLI tool foundation
- `TCK-20260612-LOCAL-CTX-DOCS-CORPUS` — docs/ corpus expansion
- `TCK-20260612-LOCAL-CTX-HYBRID-SEARCH` — BM25 + hybrid scoring
- `TCK-20260612-LOCAL-CTX-HTTP-API` — FastAPI server
- `TCK-20260612-LOCAL-CTX-OPS` — Docker, incremental reindex, git hook, skill wiring
- `TCK-20260612-LOCAL-CTX-MCP` — MCP server, `search_docs` native tool, settings.json registration
