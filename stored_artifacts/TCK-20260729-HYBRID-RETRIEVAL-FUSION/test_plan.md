---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-HYBRID-RETRIEVAL-FUSION
artifact_type: test_plan
tags: [ai, debugging, testing]
---

# Test Plan — TCK-20260729-HYBRID-RETRIEVAL-FUSION

## Regression Surface

All existing tests below must keep passing unmodified — the ticket's Scope
explicitly requires `--mode vector` / `--mode keyword` paths and their tests
to continue passing, and the fix must not change `_hybrid_score()`'s existing
formula/signature (still used by `--mode vector`/`--mode keyword` and by
`search_server.py`, out of scope).

**Unit (fast, non-`slow`):**
- `tests/tools/test_knowledge_search.py::TestTokenize` — `_tokenize()` unchanged.
- `tests/tools/test_knowledge_search.py::TestBm25BuildLoad` — `_build_bm25_index()`/`_load_bm25()` unchanged.
- `tests/tools/test_knowledge_search.py::TestHybridScore` — `_hybrid_score()` formula/weights unchanged (still used by vector/keyword modes).
- `tests/tools/test_knowledge_search.py::TestComputeBoosts` — `_compute_boosts()` unchanged.
- `tests/tools/test_knowledge_search.py::TestCollectCorpus`, `TestDocsChunkExtraction`, `TestDocsCorpusScopeGuard`, `TestExtractRequestSummary`, `TestExtractWorkingLogRows`, `TestManifestHelpers` — corpus collection untouched by this ticket.
- `tests/tools/test_knowledge_search.py::TestPyprojectDeps`, `TestPyprojectRankBm25` — dependency declarations untouched.
- `tests/tools/test_search_mcp.py::TestMcpJson`, `TestRunSearchMissingIndex`, `TestRunHealth`, `TestPyprojectDeps`, `TestMakefileTargets` — MCP registration/health untouched.
- `tests/tools/test_eval_search.py::TestReciprocalRank`, `TestStripAnchor`, `TestHit`, `TestDuplicateRate`, `TestRunQuery`, `TestEvaluateExitCode`, `TestMainNoIndex`, `TestQueriesJson` — `eval_search.py` is explicitly not in this ticket's Scope; `_reciprocal_rank()`'s MRR@10 semantics must be untouched (see naming-collision guard below).

**Integration / slow (require `sentence-transformers`/`sqlite-vec`/`rank-bm25`, or a live index — run when deps/index are available):**
- `tests/tools/test_knowledge_search.py::TestBuildHappyPath`, `TestQueryHappyPath`, `TestGracefulDegradation`, `TestBuildProducesBm25`, `TestQueryModeRouting`, `TestQueryScoreFields`, `TestMissingBm25Fallback`, `TestDocsBuildSummary`, `TestLiveQueryDocsMechanics` — cover build/query CLI behavior for hybrid/vector/keyword modes; `TestQueryModeRouting::test_query_mode_vector_skips_bm25` and `test_query_mode_keyword_skips_embedding` are the direct regression guard that this ticket's fusion helper must not be force-invoked by those two modes.
- `tests/tools/test_search_mcp.py::TestRunSearch` — `_run_search()`'s existing return-shape contract (`doc_id, title, heading, source_path, section, score, semantic_score, keyword_score, excerpt`) must be preserved for any caller not opting into the new fusion path (or, if `_run_search()` itself is routed through the new helper per ticket Scope, its external return shape must remain identical even though its internals change).

**Arena-combat:** None — this ticket touches no `src/` simulation code; no
arena-combat regression surface applies.

## New Tests Required

Per acceptance criteria (ticket lines 47-50):

1. **AC1 — Exact-term query outside dense candidate_k now surfaces via the
   lexical channel (the confirmed bug's regression test).**
   - Test name: `test_lexical_only_match_outside_dense_cut_is_surfaced`
   - Category: integration (regression)
   - Verifies: construct a small fixture corpus where one document contains an
     exact rare token (e.g. a made-up identifier like `zzqfrobnicate_widget`)
     but is semantically dissimilar to the query embedding, such that it would
     rank outside `top_k * 3` (or whichever bound the new module uses) on the
     dense channel alone. Query for that exact token via the new fusion
     module/CLI path and assert the document IS present in the final result
     set — this is the direct regression test for the confirmed bug at
     `knowledge_search.py:992-1038` / `search_mcp.py:73-146`.
   - Location: `tests/tools/test_hybrid_retrieval.py`

2. **AC2 — Dense and lexical channels independently retrieve bounded top-N,
   unioned by doc/chunk id, ranked via RRF (`score = sum of 1/(k+rank)`), not
   the current linear-weighted formula.**
   - Test name: `test_rrf_score_matches_formula_for_known_ranks`
   - Category: unit
   - Verifies: given two synthetic ranked lists (dense ranks, lexical ranks)
     for a small set of doc_ids, the fusion function's output score for a
     doc_id equals the literal `1/(k+rank_dense) + 1/(k+rank_lexical)` formula
     (or `0` contribution from a channel where the doc_id is absent) — locks
     in the exact RRF definition, not just "some fused ordering."
   - Location: `tests/tools/test_hybrid_retrieval.py`
   - Test name: `test_union_by_doc_id_includes_single_channel_hits`
   - Category: unit
   - Verifies: a doc_id present in only the dense channel's candidate list (not
     the lexical list) and vice versa both appear in the unioned candidate set
     before ranking — proves union, not intersection.
   - Location: `tests/tools/test_hybrid_retrieval.py`
   - Test name: `test_fusion_function_name_distinct_from_eval_search_reciprocal_rank`
   - Category: architecture guard (anti-drift, naming collision)
   - Verifies: the new module's fusion function is not named `_reciprocal_rank`
     and is not merely a re-export/alias of `eval_search.py::_reciprocal_rank`
     — import both and assert they are different callables with different
     signatures (RRF takes multiple ranked lists; MRR's `_reciprocal_rank`
     takes one list + one expected set).
   - Location: `tests/tools/test_hybrid_retrieval.py`

3. **AC3 — Metadata filter excludes non-matching candidates before RRF
   ranking.**
   - Test name: `test_metadata_filter_excludes_before_fusion`
   - Category: unit
   - Verifies: given dense/lexical candidate lists containing a doc_id whose
     resolved metadata (`authority`/`freshness`/`kind`, per the plan's chosen
     join mechanism) fails a supplied filter predicate, that doc_id is absent
     from the RRF input entirely (not merely down-ranked or excluded post-hoc)
     — proves exclusion happens before fusion, matching the AC's literal
     ordering requirement.
   - Location: `tests/tools/test_hybrid_retrieval.py`
   - Test name: `test_non_registry_backed_rows_get_sentinel_not_fabricated_value`
   - Category: unit (anti-drift, grounded in `context_packet_contract.md` §3)
   - Verifies: a `knowledge_docs` row whose `source_type` is `ticket`,
     `investigation`, or `working_log` (no `docs/REGISTRY.yaml` entry to join
     against) resolves to the fallback sentinel for authority/freshness, not a
     fabricated `P2`/`historical`-looking default — regression guard for the
     open question flagged in investigation.md.
   - Location: `tests/tools/test_hybrid_retrieval.py`

4. **AC4 — Existing `--mode vector`/`--mode keyword` paths and their tests
   continue passing unmodified.**
   - Test name: (no new test — covered by the existing Regression Surface
     tests above, specifically `TestQueryModeRouting` and
     `TestMissingBm25Fallback`); add one new explicit guard:
   - Test name: `test_vector_and_keyword_modes_do_not_import_fusion_module`
   - Category: architecture guard (anti-drift)
   - Verifies: `cmd_query()` with `mode="vector"` or `mode="keyword"` never
     calls into the new fusion module (patch/spy on the fusion entry point and
     assert zero calls) — proves the new code path is additive, not a
     refactor that silently reroutes the preserved modes.
   - Location: `tests/tools/test_knowledge_search.py` (extends
     `TestQueryModeRouting`) or `tests/tools/test_hybrid_retrieval.py`,
     implementer's choice.

5. **Bug-fix verification for both named call sites (ticket Scope, not a
   separate numbered AC but explicitly required: "do not fix only one call
   site").**
   - Test name: `test_knowledge_search_cmd_query_uses_fusion_helper`
   - Category: integration
   - Verifies: `cmd_query()` in `hybrid` mode routes through the new shared
     fusion helper (not the old ANN-then-BM25-lookup-on-ANN-rows sequence) —
     assert via the AC1-style lexical-outside-dense-cut fixture run through
     the actual `knowledge_search.py query` CLI subprocess path (mirrors the
     existing `TestQueryHappyPath` subprocess pattern).
   - Location: `tests/tools/test_knowledge_search.py`
   - Test name: `test_search_mcp_run_search_uses_fusion_helper`
   - Category: integration
   - Verifies: same proof for `search_mcp.py::_run_search()` — the exact tool
     `search_docs` (the MCP tool every agent calls) exposes; run the same
     lexical-outside-dense-cut fixture through `_run_search()` directly (or
     via `--test` stdin mode, mirroring existing `test_search_mcp.py` patterns)
     and assert the previously-unreachable doc_id is now present.
   - Location: `tests/tools/test_search_mcp.py`

## Scoped Pytest Commands

```bash
# Fast unit/architecture-guard tests for the new module (primary gate)
pytest tests/tools/test_hybrid_retrieval.py -v

# Regression: existing knowledge_search.py / search_mcp.py / eval_search.py suites
pytest tests/tools/test_knowledge_search.py tests/tools/test_search_mcp.py tests/tools/test_eval_search.py -v -m "not slow"

# Full regression including slow/live-index tests (requires sentence-transformers,
# sqlite-vec, rank-bm25 installed and knowledge-index/knowledge.db built)
pytest tests/tools/test_knowledge_search.py tests/tools/test_search_mcp.py tests/tools/test_eval_search.py tests/tools/test_hybrid_retrieval.py -v
```

Never `pytest tests/` — scope stays to `tests/tools/` for this ticket's
domain (agent-orchestration/retrieval tooling), consistent with this being
non-simulation code with no `src/` or arena-combat surface.

## Anti-Drift Test Guards

- `test_fusion_function_name_distinct_from_eval_search_reciprocal_rank` (above)
  — directly guards against the ticket's flagged naming-collision risk with
  `eval_search.py::_reciprocal_rank()` (MRR@10, not RRF).
- `test_vector_and_keyword_modes_do_not_import_fusion_module` (above) — guards
  against a well-intentioned refactor silently rerouting the two modes the
  ticket requires to stay untouched.
- A test asserting `tools/search_server.py` is **not** imported/modified by
  this ticket's diff (e.g. a `git diff --name-only` check in CI, or simply
  the done-checker's Files Changed review) — guards against silently
  "helpfully" fixing the third call site (`search_server.py`) that shares the
  same bug pattern but is out of this ticket's scope; a scope-creep fix there
  without its own ticket/tests would violate the traceability rule.
- A test on the metadata-filter join mechanism (whichever the plan chooses —
  build-time column vs. query-time `docs/REGISTRY.yaml` join) asserting that
  `docs/REGISTRY.yaml`'s existing schema/enum values
  (`STATUS_VALUES`/`AUTHORITY_VALUES` in `tools/validate_frontmatter.py`) are
  read, not reinvented — guards against inventing a parallel authority/
  freshness vocabulary that drifts from the one `context_packet_contract.md`
  §3 already fixed.
- `test_metadata_filter_excludes_before_fusion` (above) — guards against a
  cheaper-to-implement-but-wrong "filter after ranking" shortcut that would
  violate the AC's literal ordering requirement and could let a low-authority/
  stale source's score influence which documents get displaced from a bounded
  result set before it's excluded.
