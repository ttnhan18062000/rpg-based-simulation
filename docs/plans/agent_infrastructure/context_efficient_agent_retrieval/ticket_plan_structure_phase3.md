---
status: active
layer: ai
authority: P2
audience: developer
date: 2026-07-29
tags: [ai, workflows, process-improvement]
---

# Ticket Plan Structure — Context-Efficient Agent Retrieval, Phase 3

Guide for `/create-tickets`'s Comprehend/Structure phases when parsing
`idea_context_efficient_agent_retrieval_observability.md`'s Phase 3 only.

This supersedes `ticket_plan_structure_phase2.md` for this batch — Phase 2 is now
`DONE` (`TCK-20260728-CONTEXT-PACKET-SCHEMA`, `TCK-20260728-CODE-TEST-INDEX-BOUNDARIES`,
`TCK-20260728-DEFAULT-PACKET-CRITERIA`, `TCK-20260728-RETRIEVAL-RETENTION-REDACTION`),
resolving Open Decisions 1-4 and unblocking this phase.

## Scope this batch to Phase 3 of the source doc's "Sequenced Future Epic" only

Phase 3 is **"Read-only hybrid retrieval and cache proof — build local docs/code/test
retrieval plus cache invalidation tests; no mandatory invocation."** This is the FIRST
phase in the sequence that ships working code, not a decision document — treat it with
correspondingly more scrutiny. The Maturity banner still applies in full: this batch
does not authorize a new mandatory workflow gate, a production monitoring writer change,
or a new external retrieval service. Nothing built in this phase may be wired into any
`.claude/workflows/*.js` file or invoked automatically by any existing pipeline — it is
a standalone, directly-testable proof, callable manually (a script/module with its own
tests), exactly as "no mandatory invocation" states.

**Ground every ticket in this batch in the 4 just-resolved Phase 2 decision docs — do
not re-derive their answers:**
- `docs/engine/contracts/context_packet_contract.md` — the `ContextPacket`/`ContextRequest`
  field schema this phase's retrieval output must conform to.
- `docs/ai/code_test_index_boundaries_decision.md` — which code/test relationships
  (graphify's deterministic AST/tree-sitter edges) are safe to build on now; explicitly
  do NOT build a new semantic/LLM code model, since that decision ruled it out for now.
- `docs/observability/retrieval_retention_redaction_policy.md` — the 3-cache-level
  category names (`retrieval_index_cache`, `retrieval_query_cache`,
  `retrieval_packet_cache`) and MAY/PROHIBITED field list this phase's cache
  implementation must follow exactly (same names, same field restrictions — do not
  invent new cache-level names or store prohibited fields).
- `docs/ai/default_packet_scenarios_decision.md` — which scenarios are in-scope for a
  default packet (informs but does not require implementing scenario routing yet).

**This batch should produce standard-tier ticket(s) whose deliverable is working,
tested, read-only code** (a query router / hybrid retrieval module, a SQLite-backed
cache layer with invalidation tests) — following this repo's existing patterns:
`tools/knowledge_search.py`'s SQLite/sqlite-vec precedent for the vector-store shape,
`tools/agent-monitoring/build_index.py`'s SQLite index precedent for a second, independent
SQLite-backed store, and `docs/testing/test_taxonomy.md`/`.claude/agents/test-scoper.md`
for how symbol/test relationships are already named. Acceptance criteria must be
concrete and code-testable — "hybrid retrieval returns X when queried with Y, unit-tested
in `tests/tools/test_X.py`" — not prose claims.

**Cover these source-doc items, each traceable to a concrete deliverable:**

1. **Hybrid hybrid retrieval fusion** — a query router that retrieves a bounded candidate
   set independently from dense (existing `tools/knowledge_search.py` embeddings) and
   lexical (BM25 or equivalent) channels, unions them, and applies reciprocal-rank
   fusion — per the doc's "Retrieval layers" section 2. Must apply metadata filters
   (source kind, authority, freshness) before assembly, using the resolved Decision 3
   contract fields.
2. **Code/test symbol index, deterministic-only** — extend retrieval to cover code/test
   symbols (module, symbol, docstring/summary, imports/calls, owned component,
   associated tests) using ONLY the relationship types the Phase 2 Decision 2 doc
   confirmed are deterministic today (graphify's Part A AST edges) — no new semantic
   code model, per that decision's explicit ruling.
3. **3-level cache with invalidation tests** — implement the embedding/index cache,
   query-result cache, and context-packet cache exactly as keyed/invalidated in the
   idea doc's "Cache design" table (section 3), using the category names and
   MAY/PROHIBITED fields the Phase 2 Decision 4 doc already fixed. Each cache level
   needs its own invalidation test proving a source/model/corpus-generation change
   correctly evicts/rejects stale entries — this is the ticket's core testable claim.
4. **ContextPacket assembly** — assemble a real `ContextPacket` (per the Decision 3
   schema) from the fused/cached retrieval results, with real `included[]`/
   `excluded_summary[]` population — proving the schema is buildable from real data,
   not just documented.

**Do NOT ticket in this batch** (still gated behind this phase's own evidence, per the
doc's Sequenced Future Epic):
- Retrieval observability events, dashboard views, or any shared-writer change (Phase 4)
  — do not add any new `agent-monitoring/*.jsonl` event type in this batch.
- Shadow context packets, workflow adoption, or wiring into any `.claude/workflows/*.js`
  file (Phase 5-6).
- Any external vector/graph database (Qdrant, Postgres/pgvector, Neo4j) or hosted RAG
  service — the idea doc explicitly forbids this before measured need; SQLite only.
- A lightweight re-ranker beyond fusion+metadata filtering — the doc states this is "a
  later option only if evaluation proves...insufficient," and no evaluation has run yet.
- Open Decisions 5 (promotion sample-size/thresholds) and 6 (MCP tool vs. adapter-library
  exposure) — both still explicitly deferred; do not force-resolve either just because
  this phase touches adjacent code.

If investigation reveals Phase 3 cannot be meaningfully scoped without first resolving
something Phase 2 should have settled but didn't, say so plainly as a risk/open-question
in the ticket rather than silently guessing or re-litigating an already-closed decision.
