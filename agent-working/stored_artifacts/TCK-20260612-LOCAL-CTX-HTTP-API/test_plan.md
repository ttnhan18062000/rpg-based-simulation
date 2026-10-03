# Test Plan — TCK-20260612-LOCAL-CTX-HTTP-API
## Local FastAPI Search Server for Agent Tool Use (`POST /api/search`)

PHASE_TS: 2026-06-12T15:05:32Z

---

## 1. Regression Surface (Existing Tests That Must Pass)

These tests must remain green after this ticket's changes. None of them should require modification.

| Test file | What it covers | Run command |
|---|---|---|
| `tests/tools/test_knowledge_search.py` | All knowledge_search.py behavior (build, query, hybrid scoring, BM25 modes, corpus guards) | `pytest tests/tools/test_knowledge_search.py -v --tb=short` |
| `tests/tools/test_validate_frontmatter.py` | Frontmatter validator (unrelated tooling — guards against stray edits) | `pytest tests/tools/test_validate_frontmatter.py -v --tb=short` |

No simulation engine tests are in scope — `search_server.py` has zero simulation dependencies.

---

## 2. New Tests Required

**New file:** `tests/tools/test_search_server.py`

All tests use `fastapi.testclient.TestClient` (synchronous ASGI test client backed by `httpx`). The test client exercises the full FastAPI app in-process — no subprocess, no live uvicorn port.

Because `knowledge_search.py` has expensive optional deps (`sentence-transformers`, `sqlite-vec`), all tests that exercise the query path must either:
- Use a **pre-built mock index** (a real sqlite-vec `.db` + a real `bm25.pkl` created during test setup), or
- **Monkeypatch the model loading and DB access** at the `search_server` module level to inject deterministic fake results.

The recommended approach is monkeypatching at the app startup level (override `_load_app_state()` or equivalent lifespan initialization) so that the test environment never loads the actual 22 MB model. This mirrors the pattern in `tests/tools/test_knowledge_search.py` which uses stub modules for `sentence_transformers` and `sqlite_vec`.

### 2.1 Module-level setup

```python
# Fixture: fake_app_state
# Returns a TestClient bound to the search_server FastAPI app with
# all model/index dependencies replaced by deterministic stubs.
```

The fake state should contain at minimum 5 synthetic result dicts with:
- Distinct `doc_id` values across sections: `mechanics/...`, `engine/...`, `core/...`
- Deterministic `score`, `semantic_score`, `keyword_score` values
- Non-empty `excerpt` strings
- Non-empty `text` strings (for include_text tests)

---

### 2.2 Test Cases (per AC)

#### Group 1: Health endpoint (AC: `GET /api/health`)

**T-HEALTH-01** — `test_health_returns_ok`
- Request: `GET /api/health`
- Assert: status 200, `response.json()["status"] == "ok"`
- Assert: response contains keys `index_version`, `documents`, `chunks`, `model`
- AC: health check AC

**T-HEALTH-02** — `test_health_model_name_matches_knowledge_search`
- Assert: `response.json()["model"] == "all-MiniLM-L6-v2"` (matches `_MODEL_NAME` from `knowledge_search.py`)
- Anti-drift: model name must not be hardcoded separately in `search_server.py`

**T-HEALTH-03** — `test_health_chunk_count_is_positive`
- Assert: `response.json()["chunks"] > 0`
- With the fake state fixture this confirms the count comes from the stubbed index, not zero.

---

#### Group 2: Search endpoint — normal flow (AC: `POST /api/search`)

**T-SEARCH-01** — `test_search_returns_valid_structure`
- Request: `POST /api/search` with `{"query": "damage formula", "top_k": 5}`
- Assert: status 200
- Assert: `response.json()` matches schema: has `query`, `top_k`, `results` keys
- Assert: `len(results) == 5`
- Assert: each result has `doc_id`, `source_path`, `score`, `excerpt` keys
- AC: basic search AC

**T-SEARCH-02** — `test_search_top_k_respected`
- Request: `{"query": "anything", "top_k": 3}`
- Assert: `len(results) <= 3`
- AC: `top_k` parameter honored

**T-SEARCH-03** — `test_search_default_top_k_is_8`
- Request: `{"query": "anything"}` (no `top_k`)
- Assert: `top_k` field in response is `8`
- AC: default top_k=8

**T-SEARCH-04** — `test_search_include_text_false_omits_text_field`
- Request: `{"query": "anything", "include_text": false}`
- Assert: each result dict does NOT have a `"text"` key (or has `text: null`)
- AC: `include_text: false` omits full text

**T-SEARCH-05** — `test_search_include_text_true_includes_text_field`
- Request: `{"query": "anything", "include_text": true}`
- Assert: each result has `"text"` key with non-empty string
- AC: `include_text: true` includes full chunk text

**T-SEARCH-06** — `test_search_result_has_score_fields`
- Assert: each result has `score`, `semantic_score`, `keyword_score` as floats in [0.0, 1.0]
- AC: result schema correctness

**T-SEARCH-07** — `test_search_result_has_excerpt`
- Assert: each result `excerpt` is a non-empty string with len <= 200 chars (or 200-char limit per spec)
- AC: excerpt is first 200 chars of chunk text

---

#### Group 3: Section filter (AC: section filter)

**T-FILTER-01** — `test_search_section_filter_mechanics`
- Request: `{"query": "damage formula", "top_k": 5, "filters": {"section": "mechanics"}}`
- Assert: all results have `source_path` starting with `docs/mechanics/`
- AC: section filter restricts results to mechanics subsection

**T-FILTER-02** — `test_search_section_filter_engine`
- Request: `{"query": "authoritative pipeline", "top_k": 5, "filters": {"section": "engine"}}`
- Assert: all results have `source_path` starting with `docs/engine/`
- AC: section filter works for engine section

**T-FILTER-03** — `test_search_section_filter_unknown_returns_empty_or_partial`
- Request: `{"query": "anything", "filters": {"section": "nonexistent_section_xyz"}}`
- Assert: status 200, `results` is an empty list (no crash)
- AC: unknown section does not crash the server

---

#### Group 4: Search mode filter

**T-MODE-01** — `test_search_mode_vector`
- Request: `{"query": "test", "filters": {"mode": "vector"}}`
- Assert: status 200, results returned
- Coverage: mode routing

**T-MODE-02** — `test_search_mode_keyword`
- Request: `{"query": "test", "filters": {"mode": "keyword"}}`
- Assert: status 200, results returned

**T-MODE-03** — `test_search_mode_hybrid_is_default`
- Request: `{"query": "test"}` (no mode)
- Assert: status 200 (default mode handled without error)

---

#### Group 5: Input validation

**T-VALIDATE-01** — `test_search_missing_query_returns_422`
- Request: `POST /api/search` with `{}` (no `query` field)
- Assert: status 422 (FastAPI validation error)
- AC: `query` is required

**T-VALIDATE-02** — `test_search_empty_query_returns_results_or_422`
- Request: `{"query": ""}` (empty string)
- Assert: status 422 OR status 200 with empty results (either is acceptable; document the choice)
- Coverage: edge case

**T-VALIDATE-03** — `test_search_invalid_top_k_type_returns_422`
- Request: `{"query": "test", "top_k": "not_a_number"}`
- Assert: status 422
- Coverage: Pydantic type coercion

---

#### Group 6: Missing index fast-fail (AC: missing index exits with error)

**T-MISSING-01** — `test_server_startup_fails_fast_when_index_missing`
- Set up an app instance pointed at a nonexistent index path
- Assert: `SystemExit` is raised during startup (or `RuntimeError` with the expected message)
- Assert: error message contains `"knowledge index not found"`
- AC: startup fails fast with actionable error when index is missing

---

#### Group 7: CORS (AC: CORS rejects non-localhost origins)

**T-CORS-01** — `test_cors_allows_localhost_origin`
- Send `OPTIONS` preflight with `Origin: http://localhost:3000`
- Assert: response includes `Access-Control-Allow-Origin` header with localhost value
- AC: CORS allows localhost

**T-CORS-02** — `test_cors_rejects_external_origin`
- Send `OPTIONS` preflight with `Origin: https://external-site.com`
- Assert: response does NOT include `Access-Control-Allow-Origin: https://external-site.com`
- AC: CORS rejects non-localhost

---

#### Group 8: Anti-drift guards

**T-DRIFT-01** — `test_search_server_imports_knowledge_search_not_copy`
- Load `search_server` module, inspect its namespace for `_hybrid_score`, `_tokenize`, etc.
- Assert: the functions are the same objects as those in `knowledge_search` module (identity check via `is`)
- Anti-drift: prevents future copy-paste of scoring logic

**T-DRIFT-02** — `test_fastapi_uvicorn_in_core_deps_not_knowledge`
- Read `pyproject.toml`, parse `[project.dependencies]`
- Assert: `fastapi` appears in core deps, NOT in `[knowledge]` optional group
- Assert: `uvicorn` appears in core deps, NOT in `[knowledge]` optional group
- Anti-drift: fastapi/uvicorn must stay as core deps, not drift to optional

**T-DRIFT-03** — `test_makefile_has_search_server_target`
- Read `Makefile`, assert it contains `search-server:` target definition
- Assert: target body contains `uvicorn tools.search_server:app --port 8765`
- Anti-drift: make target must be present and correct

**T-DRIFT-04** — `test_claude_md_has_search_server_proactive_entry`
- Read `CLAUDE.md`, assert it contains `tools/search_server.py` or `localhost:8765` within the `### Always auto-invoke` section
- Anti-drift: CLAUDE.md must be updated as part of this ticket

**T-DRIFT-05** — `test_default_port_is_8765`
- Inspect `search_server` module or its source for the port constant
- Assert: port 8765 is the documented default
- Anti-drift: port must not silently drift

---

## 3. Scoped Pytest Commands

```bash
# Run only the new search server tests (during implementation)
pytest tests/tools/test_search_server.py -v --tb=short

# Run all tooling tests (regression + new)
pytest tests/tools/ -v --tb=short

# Run with architecture marker (guards only, fast)
pytest tests/tools/ -m "architecture" -v --tb=short

# Full fast suite (no slow/strict_matrix)
pytest tests/ -m "not slow and not extra_slow and not strict_matrix" -v --tb=short
```

Do NOT run `pytest tests_v2/` or `pytest tests/` (full suite) — out of scope for tooling-only work.

---

## 4. Anti-Drift Test Guards Summary

| Guard | Test | What it prevents |
|---|---|---|
| No logic duplication | T-DRIFT-01 | Copy-paste of `_hybrid_score` / `_tokenize` into search_server.py |
| fastapi stays core dep | T-DRIFT-02 | Accidental move of fastapi to optional-deps |
| make target present | T-DRIFT-03 | make target deletion or rename |
| CLAUDE.md updated | T-DRIFT-04 | CLAUDE.md update being skipped |
| Port constant | T-DRIFT-05 | Silent port change |
| Model name matches | T-HEALTH-02 | Model name hardcoded separately in server |
| Missing index message | T-MISSING-01 | Error message wording drift |

---

## 5. Test Infrastructure Notes

- **TestClient**: `from fastapi.testclient import TestClient` — synchronous, no live server needed
- **httpx**: already in `[dev]` optional-deps (`pyproject.toml` line 30); TestClient uses it internally
- **No live index required**: all path-dependent tests use monkeypatching / tmp_path fixtures with synthetic data
- **Fixture strategy**: a `@pytest.fixture` that patches `search_server._APP_STATE` (or equivalent module-level state holder) with a deterministic `AppState` object containing stub results and metadata
- **Model stub**: mock the `SentenceTransformer` to return a fixed 384-dim zero vector; stub the sqlite-vec connection to return deterministic rows from a real or in-memory SQLite DB
- **Isolation**: each test that modifies module state must use `monkeypatch` to restore it (pytest monkeypatch fixture handles teardown automatically)
