---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION
artifact_type: test_plan
tags: [ai, bug]
---

# Test Plan — TCK-20260815-HOTFIX-DOC-ID-NESTED-PATH-TRUNCATION

## Regression Surface

Existing tests that must keep passing, by file path (all read/counted directly, not estimated):

**Unit — corpus builder / doc_id derivation**
- `tests/tools/test_knowledge_search.py` (104 tests total; none currently assert an exact `doc_id`
  string value or use a nested (>1 level) docs path — confirmed by grep — so none are expected to
  break from the fix itself, but all must still pass since this file's chunking/BM25/query logic
  is adjacent code in the same module). In particular the `TestCollectDocsChunks*` class
  (L734–889) and `TestCollectCorpus*` (L515–970).

**Unit — eval harness**
- `tests/tools/test_eval_search.py` (36 tests, includes the `TestStripAnchor` class added by
  `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`) — `_strip_anchor()` only touches `#anchor`, not
  `/`-nesting, so unaffected by this fix; must still pass unchanged.

**Integration — downstream doc_id consumers (the ticket's 3 named consumers)**
- `tests/tools/test_context_packet_assembler.py` (16 tests) — `source_id=result.doc_id` passthrough.
- `tests/tools/test_search_server.py` (15 tests) — `doc_ids.index(doc_id)` lookup, `_derive_title()`.
- `tests/tools/test_search_mcp.py` (16 tests) — response `doc_id`/`_derive_title()`.
- `tests/tools/test_hybrid_retrieval.py` (16 tests) — `HybridResult.doc_id`, `resolve_metadata()`
  (path-keyed, not doc_id-keyed — should be unaffected) — not named in the ticket but is the real
  query-time consumer wired into `cmd_query()`'s hybrid path; include in regression surface.

**Integration — Knowledge Gateway MCP Phase 1 (insulated, but verify)**
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py` — specifically
  `test_zero_mutation_of_real_agent_monitoring_corpus_from_comparison_runner`, which is the one
  test in this suite that exercises the full live-call path (`run_corpus()` against the real
  gateway). Confirmed `_normalize_phase1_source_id()` never reads `doc_id` (only Phase 1's own
  `source_path`-derived `evidence_id`) — this test is not expected to change behavior, but must
  still pass as a belt-and-suspenders check that the fix didn't have an unforeseen live-call
  side effect.
- `tests/tools/test_kgmcp_measurement_baseline.py` — same rationale, run for completeness since it
  shares fixtures with the above.

## New Tests Required

1. **Test name**: `test_collect_docs_chunks_preserves_full_nested_path`
   **Category**: unit
   **What it verifies**: for a doc under a synthetic multi-level nested directory (e.g.
   `docs/engine/contracts/knowledge_gateway_mcp/foo.md`, mirroring the real corpus example),
   `_collect_docs_chunks()`'s returned `doc_id` field equals `"engine/contracts/knowledge_gateway_mcp/foo"`
   — the full path minus the `docs/` prefix and `.md` suffix — not the truncated
   `"engine/foo"`. Must fail against pre-fix code (assert the OLD behavior would have produced
   `"engine/foo"` in a comment or a paired negative assertion, to prove this test actually exercises
   the bug).
   **Where**: `tests/tools/test_knowledge_search.py`, alongside `TestCollectDocsChunks*`.

2. **Test name**: `test_collect_docs_chunks_no_collision_same_stem_different_subdir`
   **Category**: unit
   **What it verifies**: two synthetic docs with the same stem but different nested subdirectories
   under the same top-level section — e.g. `docs/engine/a/foo.md` and `docs/engine/b/foo.md` (the
   ticket's own example) — produce two **distinct** `doc_id` values
   (`"engine/a/foo"` vs `"engine/b/foo"`), not both collapsing to `"engine/foo"`.
   **Where**: `tests/tools/test_knowledge_search.py`.

3. **Test name**: `test_collect_docs_chunks_single_level_path_unchanged`
   **Category**: unit (anti-drift guard)
   **What it verifies**: a depth-1 doc (`docs/mechanics/02_combat_laws.md`, the existing shape all
   current tests use) still produces `doc_id = "mechanics/02_combat_laws"` — i.e. the fix must be a
   strict generalization, not a behavior change for the common (non-nested) case that 218/338 real
   docs are in.
   **Where**: `tests/tools/test_knowledge_search.py` (may already be implicitly covered by
   `test_collect_docs_chunks_basic` — add an explicit `doc_id` value assertion there if not, since
   no current test asserts the exact `doc_id` string).

4. **Test name**: `test_chunk_id_anchor_suffix_unaffected_by_nesting_fix`
   **Category**: unit (anti-drift guard — protects the `TCK-20260711` precedent)
   **What it verifies**: for a nested doc with an H2 heading, the chunk-level `id` field is still
   `f"{new_doc_id}#{heading_slug}-{seq:03d}"` — i.e. anchor derivation (`_heading_slug()`, `#`
   separator, zero-padded sequence) is untouched; only the pre-`#` portion changes shape.
   **Where**: `tests/tools/test_knowledge_search.py`.

5. **Test name**: `test_derive_title_agnostic_to_nesting_depth`
   **Category**: unit (anti-drift guard)
   **What it verifies**: `_derive_title()` (both copies — `search_server.py` and `search_mcp.py`)
   produces the same title string for `"engine/measurement_baseline_contract"` (old-scheme input)
   and `"engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract"` (new-scheme input)
   — i.e. `.split("/")[-1]` correctly ignores added nesting. Confirms Investigation's claim that
   this function needs no code change.
   **Where**: `tests/tools/test_search_server.py` and `tests/tools/test_search_mcp.py` (one case
   each, or a shared parametrized case if the test files already share fixtures).

6. **Test name**: `test_build_incremental_noop_leaves_stale_doc_id_documented` (or equivalent
   named to reflect it's asserting current, now-understood behavior rather than a bug being fixed)
   **Category**: architecture guard / integration
   **What it verifies**: calling `cmd_build_incremental()` when no corpus-tracked file's mtime has
   changed (only in-process derivation logic differs) returns 0 and does **not** rewrite
   `knowledge.db` — i.e. locks in the Investigation finding that `make knowledge-index-update`
   alone is insufficient for an ID-scheme change, so a future regression (someone "optimizing" the
   rebuild step to always use `--incremental`) is caught. Not a fix to this no-op behavior (that
   would be a larger, out-of-scope change to add scheme-versioning to the manifest) — a guard that
   documents and freezes the current, now-understood contract.
   **Where**: `tests/tools/test_knowledge_search.py`, near the existing `TestCmdBuildIncremental`-
   style tests (confirm exact existing class name during Implement; not verified here since this
   is new coverage, not existing).

7. **Test name**: `test_queries_json_expected_doc_ids_match_current_scheme` (fixture-integrity
   guard)
   **Category**: unit / fixture guard
   **What it verifies**: every `expected_doc_ids` entry in `tools/eval/queries.json` that refers to
   a real `docs/` file (as opposed to a `tickets/done/` ticket ID) matches that file's actual
   `doc_id` under the current (post-fix) derivation scheme — i.e. programmatically re-derive
   `doc_id` for every real file and assert no `expected_doc_ids` entry is stale. This directly
   locks in the 9-query fixture update Investigation found is required, and prevents silent
   fixture drift on any future `doc_id`-scheme change.
   **Where**: `tests/tools/test_eval_search.py` (new test class, e.g. `TestQueriesFixtureIntegrity`).

## Scoped Pytest Commands

```
pytest tests/tools/test_knowledge_search.py tests/tools/test_eval_search.py \
       tests/tools/test_context_packet_assembler.py tests/tools/test_search_server.py \
       tests/tools/test_search_mcp.py tests/tools/test_hybrid_retrieval.py \
       tests/tools/test_kgmcp_phase1_baseline_comparison.py \
       tests/tools/test_kgmcp_measurement_baseline.py -v
```

Never `pytest tests/` — scoped to the `tools/` search-index subsystem and its direct/insulated
consumers, per project Testing Rule.

## Anti-Drift Test Guards

- **Anchor-suffix guard** (test 4 above): fails if a future edit collapses the `/`-nesting fix and
  the `#anchor` fix into one change, or accidentally alters `_heading_slug()`/seq-numbering while
  touching the adjacent `doc_id` line — protects the `TCK-20260711-EVAL-SEARCH-DOCID-ANCHOR-FIX`
  guarantee.
- **`_derive_title()` nesting-agnosticism guard** (test 5): fails if a future refactor of
  `_derive_title()` assumes a fixed 2-segment shape (e.g. `doc_id.split("/", 1)` instead of
  `.split("/")[-1]`), which would silently break titles for every nested doc.
- **Incremental-noop guard** (test 6): fails if someone "fixes" the incremental no-op by changing
  its early-return behavior without this being a deliberately scoped, tested change — surfaces any
  accidental behavior change in either direction (silently starts writing on 0-diff, or continues
  to silently no-op after a real scheme change with no manifest-version signal added).
  Also directly enforces this ticket's own AC #3 process requirement: implementers must run a full
  `make knowledge-index` rebuild, not rely on `--incremental`.
- **Fixture-integrity guard** (test 7): fails immediately if `tools/eval/queries.json` is not
  updated for the 9 affected queries in the same change — turns the "AC #5: no regression to
  eval_search's recall/MRR metrics" acceptance criterion into a fast, deterministic unit-test
  check instead of relying solely on a full `make eval-search` run (which is also required, but
  slower and non-deterministic-adjacent due to embedding model behavior).
- **No-collision guard** (test 2): protects against the exact collision shape the ticket's own
  Request Summary describes (`docs/engine/a/foo.md` vs `docs/engine/b/foo.md`) — ensures the fix
  actually eliminates the theoretical collision risk, not just changes the string format.
- Post-fix, re-run the real-corpus collision-count script from Investigation
  (`doc_id = path minus "docs/" prefix and ".md" suffix` for all 338 real files) as a manual
  Verify-phase sanity check — expect 338 distinct `doc_id`s under the new scheme too (a stricter
  guarantee than before, since full-path uniqueness is filesystem-guaranteed while
  section/stem uniqueness was not). Not added as an automated test since it duplicates what test 2
  already guards structurally, but worth one manual confirmation run against the live corpus
  during Verify.
