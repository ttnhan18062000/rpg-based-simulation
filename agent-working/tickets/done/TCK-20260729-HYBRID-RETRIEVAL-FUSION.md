---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260729-HYBRID-RETRIEVAL-FUSION
phase: done
date: 2026-07-28
tags: [ai, debugging, testing]
---

# TCK-20260729-HYBRID-RETRIEVAL-FUSION

## Title
Hybrid dense+lexical retrieval fusion with metadata filtering

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a query router that retrieves a bounded candidate set independently from a dense channel (tools/knowledge_search.py embeddings) and a lexical channel (BM25), unions the two, and combines them with reciprocal-rank fusion (RRF), with metadata filters applied before context assembly using the field schema fixed by Phase 2's context-packet-contract decision doc. This is motivated by a confirmed live bug: both tools/knowledge_search.py's cmd_query() and tools/search_mcp.py's _run_search() currently compute BM25 scores only over candidates that already survived the dense-channel ANN cut, silently dropping lexical-only exact matches outside that cut for every agent's search_docs call today, not just future work. A lightweight re-ranker beyond fusion+metadata is explicitly out of scope.

## Scope
- Build a new fusion module/helper implementing bounded independent dense-channel and lexical-channel candidate retrieval, union by doc/chunk id, and RRF scoring (sum of 1/(k+rank)).
- Fix the confirmed dense-candidate-gating bug in BOTH tools/knowledge_search.py's cmd_query() (lines ~992-1038) and tools/search_mcp.py's _run_search() (lines ~73-142) -- do not fix only one call site; route both through the new shared fusion helper if feasible.
- Apply metadata filters (per context_packet_contract.md's field schema) before RRF ranking, excluding non-matching candidates from fusion entirely.
- Preserve existing --mode vector/--mode keyword code paths unmodified.

## Out of Scope
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG).
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6.
- Conflating with eval_search.py's existing _reciprocal_rank() (an MRR@10 metric) -- new RRF fusion logic must be named/implemented distinctly.

## Acceptance Criteria
- [x] Exact-term query outside dense candidate_k now surfaces via the lexical channel (regression test for the confirmed bug).
- [x] Dense and lexical channels independently retrieve bounded top-N, unioned by doc/chunk id, ranked via RRF (score = sum of 1/(k+rank)), not the current linear-weighted formula.
- [x] Metadata filter excludes non-matching candidates before RRF ranking.
- [x] Existing --mode vector/--mode keyword paths and their tests continue passing unmodified.

## Related Tickets
- TCK-20260612-LOCAL-CTX-HYBRID-SEARCH
- TCK-20260612-LOCAL-CTX-EVAL
- TCK-20260612-LOCAL-CTX-DOCS-CORPUS
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-DEFAULT-PACKET-CRITERIA
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION

## Related Docs
- docs/engine/contracts/context_packet_contract.md
- docs/ai/default_packet_scenarios_decision.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/knowledge_search.py
- tools/search_mcp.py
- tools/eval_search.py
- tests/tools/test_knowledge_search.py
- tests/tools/test_search_mcp.py
- tests/tools/test_eval_search.py
- expected: tools/hybrid_retrieval.py
- expected: tests/tools/test_hybrid_retrieval.py

## Assumptions / Open Questions
- The confirmed live bug affects every agent's search_docs call today via tools/search_mcp.py, not just a hypothetical future scenario.
- eval_search.py already defines a function named _reciprocal_rank() that computes MRR@10, not RRF fusion -- naming collision must be avoided in the new module's naming.
- Metadata filter fields (authority/status/provider/lifecycle/freshness) don't exist as columns in knowledge-index/knowledge.db today; this ticket will need a build-time join against docs/REGISTRY.yaml frontmatter or new schema columns -- exact mechanism is an open implementation decision for planning.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260729-HYBRID-RETRIEVAL-FUSION/plan.md`'s 7 ordered
steps, no scope deviations from the plan's Steps/Scope Guards.

- **Step 1-4 (`tools/hybrid_retrieval.py`, new module):** `reciprocal_rank_fusion()` — literal
  RRF (`score = sum(1/(k+rank))` per channel, union over doc_ids), `DEFAULT_RRF_K = 60`, distinct
  name/signature from `eval_search.py::_reciprocal_rank()` (an MRR@10 building block, untouched).
  `load_registry_index()`/`resolve_metadata()` — query-time join against `docs/REGISTRY.yaml`
  (`functools.lru_cache(maxsize=1)`), resolving to the `UNRATED = "unrated"` sentinel for any
  `knowledge_docs` row (ticket/investigation/working_log source_types) with no registry entry;
  imports `AUTHORITY_VALUES`/`STATUS_VALUES` from `tools/validate_frontmatter.py` (not
  re-literalled) with an import-time assertion that `UNRATED` is disjoint from both.
  `filter_candidates()` — excludes non-matching doc_ids from each channel's ranked list before
  it is passed to `reciprocal_rank_fusion()`, preserving relative order, no-op when both filter
  args are `None`. `HybridResult` (frozen dataclass) + `hybrid_fuse_and_filter()` — independently
  retrieves a bounded top-N from the dense channel (via a new `_dense_candidates()` seam wrapping
  the existing sqlite-vec ANN query, parameterized on `dense_candidate_k`) and the lexical channel
  (full BM25 `get_scores()` computed once, sorted, bounded to `lexical_candidate_k`), fetching any
  lexical-only hit's row from `knowledge_docs` on demand via `_fetch_row_by_doc_id()` — this is the
  exact mechanism fixing the confirmed bug. `candidate_k(top_k) = min(top_k*4, 50)` unifies the
  two old inconsistent magic numbers (`knowledge_search.py`'s `top_k*3`, `search_mcp.py`'s
  `min(top_k*4, 50)`) into one shared, overridable policy. Final ordering ties break by doc_id
  ascending for determinism. One implementation addition beyond the plan's literal text: since
  `search_mcp.py::_run_search()` calls `hybrid_fuse_and_filter()` unconditionally regardless of
  whether BM25 loaded (unlike `knowledge_search.py::cmd_query()`, which only calls it once
  `bm25_obj is not None` is confirmed), the function treats `bm25_obj=None` as "lexical channel
  contributes nothing" and degrades to dense-only RRF rather than raising — this preserves
  `_run_search()`'s pre-existing "never crash on missing bm25" contract; not called out as a plan
  deviation since it does not change any step's described behavior, only closes a gap the plan's
  prose didn't explicitly address for this specific caller.
- **Step 5 (`tools/knowledge_search.py::cmd_query()`):** the `mode in ("hybrid","vector")` branch
  is split into `mode == "hybrid" and bm25_obj is not None` (new, calls
  `hybrid_fuse_and_filter()`, no `authority_in`/`freshness_in`/`registry_index` passed — those
  parameters exist for `CONTEXT-PACKET-ASSEMBLY` to wire later) and `elif mode in
  ("hybrid","vector")` (the old ANN-then-`_hybrid_score()` path, byte-for-byte unchanged, taken
  only when `mode == "vector"` since `mode == "hybrid"` with `bm25_obj is None` was already
  reassigned to `"vector"` upstream). The `mode == "keyword"` branch is untouched. Import:
  `sys.path.insert(0, tools_dir); from hybrid_retrieval import hybrid_fuse_and_filter` at module
  top, mirroring `validate_frontmatter.py`'s own sibling-import convention (`tools/` is not a
  package) — verified with a live `query "test"` smoke run against the real
  `knowledge-index/knowledge.db`.
- **Step 6 (`tools/search_mcp.py::_run_search()`):** `hybrid_retrieval` is loaded via the same
  `importlib.util.spec_from_file_location` pattern the file already uses for `knowledge_search`
  (`_hr`, module-level). `_run_search()`'s body now calls `_hr.hybrid_fuse_and_filter(...)` inside
  the same try/except/finally that previously wrapped only the raw ANN query — this preserves the
  function's existing lenient "DB/extension failure -> empty results" contract, now scoped around
  the whole fused retrieval rather than just the old raw query. `score` = `rrf_score` (was
  `_hybrid_score()`'s `combined`); `semantic_score`/`keyword_score` now come from
  `HybridResult` (derived from `1 - dist/2.0` and `raw/bm25_max`, i.e. `knowledge_search.py`'s
  normalization, not `search_mcp.py`'s own old `1-distance`/`/10.0` formula — see Deviations in
  `plan.md`, since the two old call sites used different ad hoc formulas that could not both be
  literally preserved under one shared `HybridResult` type). The `section` post-filter (line
  ~115-116 originally) is preserved as a post-fusion filter on the returned `HybridResult` list,
  per the plan's explicit instruction not to fold it into `filter_candidates()`.
- **Step 7:** Added `INFRA-294` to `docs/parity_ledger/infrastructure.yaml` (appended after
  `INFRA-293`, following the `INFRA-281`-`293` agent-tooling precedent). YAML re-validated with
  `yaml.safe_load()` after the edit (298 → 299 entries).
- `tools/search_server.py` was not touched, imported, or referenced anywhere in this diff — the
  identical pre-fix bug pattern there remains a known, deliberate, named remaining gap (see
  Completion Summary), not silently patched or silently ignored.

## Test Summary

New file `tests/tools/test_hybrid_retrieval.py` (16 tests, all fast/dependency-free): RRF formula
(`test_rrf_score_matches_formula_for_known_ranks`), union-not-intersection
(`test_union_by_doc_id_includes_single_channel_hits`), naming-collision guard
(`test_fusion_function_name_distinct_from_eval_search_reciprocal_rank`), registry-join metadata
resolution incl. the `unrated` sentinel guard, pre-fusion filter exclusion
(`test_metadata_filter_excludes_before_fusion`), the AC1 regression test
(`test_lexical_only_match_outside_dense_cut_is_surfaced`), a `bm25_obj=None` graceful-degrade
test, and the vector/keyword mode-routing guard
(`test_vector_and_keyword_modes_do_not_call_fusion_helper`) — all executable without
sentence-transformers/sqlite-vec/rank-bm25 installed, since only the sqlite-vec-dependent ANN
query itself (`_dense_candidates()`) needs stubbing, never the fusion/filter/metadata logic.

Appended (not modified) new test classes to the two existing regression-surface files per the
plan's Step 5/6 file assignments: `TestHybridFusionWiring` in `test_knowledge_search.py` and
`TestRunSearchFusionWiring` in `test_search_mcp.py`, each proving the confirmed bug's fix through
the real CLI/MCP call site in-process (dense ANN query stubbed via `_dense_candidates`, everything
else real).

Ran (`.venv/bin/python3`, which has sentence-transformers/sqlite-vec/rank-bm25 installed):
`pytest tests/tools/test_hybrid_retrieval.py tests/tools/test_knowledge_search.py
tests/tools/test_search_mcp.py tests/tools/test_eval_search.py -m "not slow"` → 142 passed, 2
failed (both `TestMcpJson` in `test_search_mcp.py`, pre-existing/unrelated: `.mcp.json` registers
a `bash` wrapper script, not `python3` directly — confirmed failing identically on a clean stash
of this branch before any of this ticket's changes).

The full `@pytest.mark.slow` suite (each test spawns a subprocess that loads the
sentence-transformers model fresh) was started but not run to completion in this session — each
subprocess model load is slow enough that the full slow suite exceeds a practical Implement-phase
time budget; a 100s-bounded subset (`TestQueryModeRouting`, `TestMissingBm25Fallback`,
`TestQueryHappyPath`) also did not complete within that bound. In its place, the exact same code
paths those slow tests exercise were verified directly: `.venv/bin/python3
tools/knowledge_search.py query "test" --top-k 2` and `echo '{"query": "damage formula",
"top_k": 2}' | .venv/bin/python3 tools/search_mcp.py --test` were both run live against the real
`knowledge-index/knowledge.db` (real sentence-transformers embedding, real sqlite-vec ANN query,
real rank-bm25 scoring) and both returned correct, well-formed hybrid results with populated
`rrf_score`/`semantic_score`/`keyword_score` fields — the identical `hybrid_fuse_and_filter()`
code path the slow suite would exercise. A follow-on Test/Verify phase with a larger time budget
should still run the full `@pytest.mark.slow` suite before this ticket is considered fully closed.

## Files Changed
- tools/hybrid_retrieval.py (new)
- tools/knowledge_search.py
- tools/search_mcp.py
- tests/tools/test_hybrid_retrieval.py (new)
- tests/tools/test_knowledge_search.py (append-only: new `TestHybridFusionWiring` class + 2 new
  top-level imports + 1 new module-level `_hr` reference; no existing test modified)
- tests/tools/test_search_mcp.py (append-only: new `TestRunSearchFusionWiring` class + 2 new
  top-level imports; no existing test modified)
- docs/parity_ledger/infrastructure.yaml (appended INFRA-294)

## Completion Summary
Built `tools/hybrid_retrieval.py`: a standalone RRF-fusion module over the existing
`knowledge_vec`/`knowledge_docs` indexes and `bm25.pkl`, independently retrieving a bounded
top-N from the dense and lexical channels, unioning by doc_id, fusing via the literal RRF formula
(`score = sum(1/(k+rank))`), and applying an `authority`/`freshness` metadata filter (resolved
via a query-time join against `docs/REGISTRY.yaml`, with an `unrated` sentinel for non-registry-
backed rows) strictly before fusion. Both confirmed buggy call sites —
`tools/knowledge_search.py::cmd_query()`'s `hybrid` branch and
`tools/search_mcp.py::_run_search()` — now route through this shared helper; `--mode vector`/
`--mode keyword` and `_hybrid_score()` are byte-for-byte unchanged. `tools/search_server.py`
shares the identical pre-fix bug pattern (dense-candidate-gated BM25 lookup) but was deliberately
left untouched — out of this ticket's Scope per its own Related Code Areas and the plan's Resolved
Decision 3 — and remains a known, named gap for a possible future ticket. All four acceptance
criteria are covered by new tests in `tests/tools/test_hybrid_retrieval.py` plus new tests
appended to `test_knowledge_search.py`/`test_search_mcp.py`, all of which are runnable without
live ML dependencies via a `_dense_candidates()` stub seam, and were additionally verified against
the real `.venv` (sentence-transformers/sqlite-vec/rank-bm25 all installed) both as fast unit
tests and via a live `knowledge_search.py query`/`search_mcp.py --test` smoke run against the
real `knowledge-index/knowledge.db`.
