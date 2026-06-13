---
status: active
layer: misc
authority: P1
audience: agent
tags: [planning, rag, knowledge-search, tooling]
---

# Plan: Local Agent Context Search

**Source:** `context_search_feature.md`  
**Date:** 2026-06-12  
**Scope note:** Docusaurus frontend and cloud deployment are explicitly out of scope. This plan builds a local semantic retrieval layer so AI agents can query the project's `docs/` during implementation work.

---

## What Already Exists

`TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH` (in `tickets/todos/tier2-knowledge-search/`) builds the foundation:
- `tools/knowledge_search.py` — CLI tool with `build` and `query` subcommands
- `knowledge-index/knowledge.db` — sqlite-vec vector store
- Corpus: `tickets/done/`, `stored_artifacts/*/investigation.md`, `tickets/working_log.csv`
- Model: `all-MiniLM-L6-v2` (22MB, CPU, no API calls)

That ticket must be implemented **first**. The tickets below extend it.

---

## What This Plan Adds

| Ticket | Adds | Depends On |
|---|---|---|
| TCK-20260612-LOCAL-CTX-DOCS-CORPUS | Index `docs/` (545 md files) with heading-aware chunking | SEMANTIC-KNOWLEDGE-SEARCH |
| TCK-20260612-LOCAL-CTX-HYBRID-SEARCH | BM25 keyword index + hybrid score merging | SEMANTIC-KNOWLEDGE-SEARCH |
| TCK-20260612-LOCAL-CTX-HTTP-API | Local FastAPI `POST /api/search` for agent tool calls | DOCS-CORPUS + HYBRID-SEARCH |
| TCK-20260612-LOCAL-CTX-EVAL | Curated query set, Recall@5 / MRR@10 measurement | DOCS-CORPUS + HYBRID-SEARCH |
| TCK-20260612-LOCAL-CTX-OPS | Docker container, incremental reindex (`--incremental` + manifest.json), git post-commit hook, implement-ticket Step 0, CLAUDE.md After Work rule | HTTP-API |
| TCK-20260612-LOCAL-CTX-MCP | MCP server (`tools/search_mcp.py`), `search_docs` native tool, `.claude/settings.json` registration, supersedes curl wiring from OPS | DOCS-CORPUS + HYBRID-SEARCH |

---

## Implementation Order

```
TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH   ← implement first (foundation)
        |
        +-- TCK-20260612-LOCAL-CTX-DOCS-CORPUS    ─┐
        +-- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH   ─┤ parallel
                |                                  ─┘
                +-- TCK-20260612-LOCAL-CTX-HTTP-API   ─┐
                +-- TCK-20260612-LOCAL-CTX-EVAL        ─┘ parallel
                        |
                        +-- TCK-20260612-LOCAL-CTX-OPS   ─┐ parallel
                        +-- TCK-20260612-LOCAL-CTX-MCP   ─┘ MCP supersedes OPS curl wiring
```

---

## End State for Agent Use

Once all tickets are done, an agent can:

```bash
# CLI lookup (fast, no server)
python3 tools/knowledge_search.py query "how does regional trauma accumulate" --top-k 5

# HTTP lookup (via local server or make search-server)
curl -s -X POST http://localhost:8765/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how does regional trauma accumulate", "top_k": 5}'
```

The HTTP API is also registered as a CLAUDE.md Proactive Tool Use entry so future agents auto-invoke it before answering architecture questions.

---

## Non-Goals (from feature doc, confirmed dropped)

- Docusaurus frontend search component
- Cloud/remote deployment of any kind
- Browser-side embedding
- Algolia or any external search service
- Full chatbot or LLM-generated answers
- Multi-tenant or permission-gated search
