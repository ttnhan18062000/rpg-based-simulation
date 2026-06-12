---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [planning, rag, knowledge-search]
---

# Proposal: Semantic Knowledge Search for Ticket and Investigation History (Tier 2)

**Author:** Engineering  
**Date:** 2026-06-12  
**Context:** Follow-up to the `create-tickets` workflow redesign (Tier 1)

---

## Background

The `create-tickets` Investigate phase now uses REGISTRY.yaml, graphify, and working_log.csv
(Tier 1) instead of raw grep. This handles structured lookups well.

However, there is a class of retrieval that structured tools cannot solve: **terminology mismatch**.
When a proposal uses different vocabulary than the code or prior tickets, keyword-based search misses
relevant history. Examples from this project:

- A proposal says "player fatigue" but the code uses `stamina_pressure`
- A proposal says "region control" but the relevant ticket was titled "Sovereignty Enforcement"
- A BA describes "resource depletion over time" but the prior investigation used "node decay rate"

With 660 done tickets, 382 stored investigations, and 580 working log rows, the probability
of a relevant prior artifact using different terminology is high and growing.

---

## What We Want

A lightweight semantic search layer that the Investigate phase can query with a natural-language
description and get back the most relevant prior tickets and investigation reports — even when
the vocabulary doesn't match.

This is NOT full codebase RAG. Graphify already handles code structure. The gap is specifically:
- `tickets/done/*.md` — 660 ticket files
- `stored_artifacts/*/investigation.md` — 382 investigation reports
- `tickets/working_log.csv` — 580 summary rows

---

## Desired Behavior

The Investigate agent should be able to run something like:

```bash
python3 tools/knowledge_search.py query "player fatigue during extended combat" --top-k 5
```

And get back the 5 most semantically similar prior tickets/investigations with their paths and
summary snippets — regardless of exact wording used in those documents.

---

## Constraints

- Must work locally with no external API calls during the Investigate phase (low latency, no cost per query)
- Index must be rebuildable deterministically: `make knowledge-index`
- Index must support incremental updates when new tickets close (one new item, not full rebuild)
- Storage should be in `knowledge-index/` at the project root (gitignored)
- The embedding model must be local (e.g., sentence-transformers via `sentence-transformers` Python package)
- Query time should be under 2 seconds for top-k retrieval across the full corpus
- The tool must degrade gracefully if the index doesn't exist yet (warn and continue, don't block)

---

## Suggested Approach

A single Python tool `tools/knowledge_search.py` with two subcommands:

- `build` — embed all ticket summaries and investigation first-paragraphs, store in a local
  vector index (sqlite-vec or FAISS). Run via `make knowledge-index`.
- `query "<text>" --top-k N` — embed the query and return top-N nearest neighbors with paths
  and snippets.

The corpus for embedding (keep it small and targeted):
1. Each row of `tickets/working_log.csv` → embed `title + summary`
2. Each `stored_artifacts/*/investigation.md` → embed first 500 chars (the "Current Behavior" section)
3. Each `tickets/done/TCK-*.md` → embed the `## Request Summary` section only

Embedding model: `all-MiniLM-L6-v2` from sentence-transformers (22MB, fast, good enough for this corpus size).
Vector store: `sqlite-vec` (single file, zero-config, no server required).

---

## Integration Point

In `create-tickets.js` Investigate phase, add a Step 0 before the existing steps:

```
Step 0: Semantic prior-work retrieval (if knowledge index exists)
  Run: python3 tools/knowledge_search.py query "<concern title and description>" --top-k 5
  If the tool errors or the index doesn't exist, skip and continue.
  For each result returned: note the ticket ID and path for steps 3 and 4.
```

This surfaces the most relevant prior work before any structured lookup, giving the agent
warm starting context even when vocabulary differs.

---

## Out of Scope

- Embedding source code (graphify handles code structure)
- Online/API-based embedding models
- A query UI or web interface
- Indexing docs other than tickets and investigations (REGISTRY.yaml covers those)
- Auto-reindex on file save (just `make knowledge-index` after tickets close)
