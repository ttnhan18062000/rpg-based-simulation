# Test Plan — TCK-20260612-LOCAL-CTX-HYBRID-SEARCH
## Add BM25 Keyword Index and Hybrid Score Merging to Knowledge Search

---

## Test Strategy

All tests are in `tests/tools/test_knowledge_search.py`. Grouped by function. Slow integration tests (subprocess + real embeddings) are marked `@pytest.mark.slow`. Unit tests run without deps. No full test suite run — scope to `pytest tests/tools/test_knowledge_search.py -m "not slow"` for fast gate, `pytest tests/tools/test_knowledge_search.py` for full coverage.

---

## Group A — Unit: `_tokenize()` (new, non-slow)

| Test | What it checks | AC |
|---|---|---|
| `test_tokenize_basic_whitespace` | Splits on spaces, lowercases | — |
| `test_tokenize_punctuation` | Splits on punctuation, no empty tokens | — |
| `test_tokenize_underscore_preserved` | `authoritative_pipeline` stays as one token | Scope |
| `test_tokenize_camelcase_not_split` | `WorldRepository` → `worldrepository` (no camelCase split in scope) | Scope |
| `test_tokenize_empty_string` | Returns `[]` | — |

---

## Group B — Unit: `_build_bm25_index()` / `_load_bm25()` (new, non-slow)

| Test | What it checks | AC |
|---|---|---|
| `test_build_bm25_creates_pkl` | Calling `_build_bm25_index(corpus, path)` creates `bm25.pkl` | AC1 |
| `test_load_bm25_returns_obj_and_ids` | `_load_bm25(path)` returns `(BM25Okapi, list)` where list length == corpus length | — |
| `test_load_bm25_missing_file_warns_and_returns_none` | Missing pkl → prints warning to stderr, returns `(None, [])`, no exception | AC5 |
| `test_load_bm25_corrupt_file_returns_none` | Corrupt pkl → prints warning, returns `(None, [])`, no exception | AC5 |
| `test_bm25_scores_nonzero_for_matching_query` | `bm25.get_scores(tokens)` > 0 for a document containing the query term | — |

---

## Group C — Unit: `_hybrid_score()` (new, non-slow)

| Test | What it checks | AC |
|---|---|---|
| `test_hybrid_score_formula` | `final = 0.55*sem + 0.25*kw + 0.10*title + 0.05*head + 0.05*code` | AC6 |
| `test_hybrid_score_all_zero_inputs` | Returns 0.0 without error | — |
| `test_hybrid_score_all_one_inputs` | Returns 1.0 (0.55+0.25+0.10+0.05+0.05 = 1.0) | AC6 |
| `test_title_boost_on_query_token_in_doc_id` | `title_boost=1.0` when query token appears in `doc_id` | AC6 |
| `test_heading_boost_on_query_token_in_heading` | `heading_boost=1.0` when query token appears in `heading` | AC6 |
| `test_code_boost_on_backtick_match` | `code_boost=1.0` when backtick-quoted token in text matches query token | AC6 |
| `test_code_boost_absent_when_no_backtick` | `code_boost=0.0` when no backtick tokens present | AC6 |

---

## Group D — Integration: `cmd_build()` produces both artifacts (slow)

| Test | What it checks | AC |
|---|---|---|
| `test_build_produces_db_and_bm25_pkl` | Both `knowledge.db` and `bm25.pkl` exist after build | AC1 |
| `test_build_bm25_pkl_is_valid_pickle` | `bm25.pkl` can be unpickled without error | AC1 |
| `test_build_prints_bm25_index_line` | stdout/stderr contains a line mentioning `bm25.pkl` | AC1 |
| `test_build_idempotent_overwrites_bm25` | Running build twice overwrites `bm25.pkl` without error | AC1 |

---

## Group E — Integration: `cmd_query()` mode routing (slow)

| Test | What it checks | AC |
|---|---|---|
| `test_query_mode_hybrid_default` | `--mode hybrid` (and no `--mode`) returns results with score fields | AC4, AC6 |
| `test_query_mode_vector_skips_bm25` | `--mode vector` completes without reading `bm25.pkl`; score fields present with `keyword_score=0.0` | AC4 |
| `test_query_mode_keyword_skips_embedding` | `--mode keyword` completes; `semantic_score=0.0` in output | AC4 |
| `test_query_mode_unknown_rejected_by_parser` | Passing `--mode invalid` causes argparse error (exit != 0) | — |

---

## Group F — Integration: score fields in output (slow)

| Test | What it checks | AC |
|---|---|---|
| `test_query_output_has_8_fields` | Each result line has exactly 8 tab-separated fields | AC6 |
| `test_query_output_score_fields_are_floats` | Fields 5, 6, 7 (0-indexed: 4, 5, 6) are parseable as float | AC6 |
| `test_query_hybrid_final_score_in_range` | `final_score` ∈ [0.0, 1.0] for all results | AC6 |
| `test_query_semantic_score_nonzero_in_hybrid` | At least one result has `semantic_score > 0` in hybrid mode | AC6 |

---

## Group G — Integration: graceful fallback (slow)

| Test | What it checks | AC |
|---|---|---|
| `test_query_missing_bm25_fallback_vector_only` | When `bm25.pkl` absent, `query` runs, warns once to stderr, returns results | AC5 |
| `test_query_missing_bm25_no_exception` | Absence of `bm25.pkl` does not raise exception | AC5 |
| `test_query_missing_bm25_warning_text` | Warning message contains "bm25" or "fallback" | AC5 |

---

## Group H — Integration: recall quality (slow, live DB)

| Test | What it checks | AC |
|---|---|---|
| `test_query_exact_term_worldrepository` | `query "WorldRepository" --top-k 5` returns at least one result from `docs/architecture/` or `docs/worldassembly/` | AC2 |
| `test_query_semantic_turn_order` | `query "how does the engine decide turn order"` returns at least one result from `docs/engine/` | AC3 |

---

## Group I — pyproject.toml anti-drift (non-slow)

| Test | What it checks | AC |
|---|---|---|
| `test_knowledge_group_contains_rank_bm25` | `rank-bm25` (or `rank_bm25`) in `[project.optional-dependencies.knowledge]` | AC1 |
| `test_rank_bm25_not_in_core_deps` | `rank-bm25` NOT in `[project.dependencies]` | — |

---

## Updated Existing Tests

| Existing Test | Change Required |
|---|---|
| `test_query_result_format_tab_separated` (line 291) | Update `len(parts) == 5` to `len(parts) == 8`; update destructuring |
| `test_query_result_has_five_fields` (Group 10, line 1097) | Same: `len(parts) == 5` → `len(parts) == 8` |

---

## Run Commands

Fast (non-slow, no deps required):
```
pytest tests/tools/test_knowledge_search.py -m "not slow" -v
```

Full (requires sentence-transformers + sqlite-vec + rank-bm25):
```
pytest tests/tools/test_knowledge_search.py -v
```

Scope to new BM25 groups only:
```
pytest tests/tools/test_knowledge_search.py -k "bm25 or hybrid or tokenize or mode" -v
```
