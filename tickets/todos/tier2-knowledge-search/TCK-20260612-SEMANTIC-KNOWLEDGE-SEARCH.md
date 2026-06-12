---
status: active
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH
phase: open
date: 2026-06-12
tags: [tooling, workflow, rag, knowledge-search]
---

# TCK-20260612-SEMANTIC-KNOWLEDGE-SEARCH

## Title
Semantic Knowledge Search for Ticket and Investigation History (Tier 2)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The `create-tickets` Investigate phase now uses REGISTRY.yaml, graphify, and working_log.csv (Tier 1) for structured lookups. However, structured keyword search fails when a proposal uses different vocabulary than the code or prior tickets — e.g., "player fatigue" vs `stamina_pressure`, or "region control" vs "Sovereignty Enforcement". With 660 done tickets and 382 stored investigations growing every sprint, the probability of relevant prior work being missed due to terminology mismatch is high and increasing. This ticket adds a lightweight local semantic search tool (`tools/knowledge_search.py`) that the Investigate phase can query with a natural-language description to surface the most relevant prior tickets and investigations regardless of exact wording.

## Scope
- Implement `tools/knowledge_search.py` with two subcommands:
  - `build` — embed the corpus and write a local vector index to `knowledge-index/` (gitignored)
  - `query "<text>" --top-k N` — return top-N nearest neighbors with ticket ID, path, and summary snippet
- Corpus to embed (targeted, not full codebase):
  - `tickets/working_log.csv` → embed `title + summary` per row
  - `stored_artifacts/*/investigation.md` → embed first 500 characters per file
  - `tickets/done/TCK-*.md` → embed the `## Request Summary` section only
- Embedding model: `all-MiniLM-L6-v2` via `sentence-transformers` (local, ~22MB, no API calls)
- Vector store: `sqlite-vec` (single `.db` file, zero-config, no server required)
- Add `knowledge-index/` to `.gitignore`
- Add `make knowledge-index` target to the Makefile that calls `python3 tools/knowledge_search.py build`
- Update `create-tickets.js` Investigate phase: prepend a Step 0 that calls `python3 tools/knowledge_search.py query "<concern title and description>" --top-k 5` and uses the results to warm-start steps 2 and 3

## Out of Scope
- Embedding source code (graphify handles code structure)
- Online or API-based embedding models
- A query UI or web interface
- Indexing docs other than tickets and investigations (REGISTRY.yaml covers those)
- Auto-reindex on file save (manual `make knowledge-index` after tickets close is sufficient)
- Full codebase RAG

## Acceptance Criteria
- [ ] `python3 tools/knowledge_search.py build` completes without error, produces `knowledge-index/knowledge.db`, and prints a summary: N documents embedded
- [ ] `python3 tools/knowledge_search.py query "player fatigue during extended combat" --top-k 5` returns 5 results in under 2 seconds on the full current corpus
- [ ] Results include ticket ID, file path, and a one-line snippet from the matched document
- [ ] If `knowledge-index/` does not exist, `query` prints a warning ("knowledge index not found — run make knowledge-index") and exits 0 without blocking the caller
- [ ] `make knowledge-index` runs `build` successfully from a clean checkout (after `pip install` of new deps)
- [ ] `create-tickets.js` Investigate phase Step 0 calls the tool and incorporates returned ticket IDs into step 3 (prior ticket cross-reference)
- [ ] The tool degrades gracefully (warns and continues) if `sentence-transformers` or `sqlite-vec` is not installed
- [ ] `knowledge-index/` is listed in `.gitignore`

## Related Tickets
- None.

## Related Docs
- docs/plans/tier2-knowledge-search.md

## Related Stored Artifacts
- None.

## Related Code Areas
- expected: tools/knowledge_search.py (new file)
- expected: .claude/workflows/create-tickets.js (Investigate phase Step 0 integration)
- expected: Makefile (knowledge-index target)
- expected: .gitignore (knowledge-index/ entry)
- expected: requirements.txt or pyproject.toml (sentence-transformers, sqlite-vec deps)

## Assumptions / Open Questions
- `sqlite-vec` may require a minimum SQLite version — check against the project's current SQLite and document in the tool's README block if it requires an upgrade
- `sentence-transformers` first run downloads the model (~22MB) — the `build` command should print a clear message so the wait is not surprising
- Incremental update (add one ticket without full rebuild) is desirable but out of scope for this ticket; can be a follow-up

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
