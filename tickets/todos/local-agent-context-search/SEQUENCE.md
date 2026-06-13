# Implementation Sequence

These tickets have intra-batch dependencies. Implement in the order below.

## Phase 0 — Foundation (separate folder, implement first)

```
tickets/todos/tier2-knowledge-search/TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH
```

This ticket creates `tools/knowledge_search.py`, `knowledge-index/knowledge.db`, and the `make knowledge-index` target. All tickets below import from or extend it.

## Phase 1 — Corpus + Search (implement in parallel after Phase 0)

```
TCK-20260612-LOCAL-CTX-DOCS-CORPUS       (extends corpus to include docs/)
TCK-20260612-LOCAL-CTX-HYBRID-SEARCH     (adds BM25 + hybrid score merging)
```

These two tickets both modify `tools/knowledge_search.py` in different areas (corpus loading vs. query pipeline). If implemented together in one session, write DOCS-CORPUS changes first (new `build` data source), then HYBRID-SEARCH changes (new `query` scoring path) to minimize merge conflicts.

## Phase 2 — API + Evaluation (implement in parallel after Phase 1)

```
TCK-20260612-LOCAL-CTX-HTTP-API          (FastAPI server, CLAUDE.md update)
TCK-20260612-LOCAL-CTX-EVAL             (evaluation set + measurement script)
```

Both depend on the full index (docs + hybrid) being available. No dependency between them; implement in either order or in parallel.

## Phase 3 — Ops + MCP (implement after HTTP-API; OPS and MCP can run in parallel)

```
TCK-20260612-LOCAL-CTX-OPS              (Docker, incremental reindex, git hook, skill wiring)
TCK-20260612-LOCAL-CTX-MCP             (MCP server, native tool call, settings.json registration)
```

OPS containerizes the HTTP server and wires CLAUDE.md with curl-based calls.
MCP supersedes the curl wiring in CLAUDE.md — implement MCP after or alongside OPS, then update CLAUDE.md once to the MCP form. If both are implemented in the same session, skip the curl CLAUDE.md edits in OPS and go straight to the MCP wiring.
