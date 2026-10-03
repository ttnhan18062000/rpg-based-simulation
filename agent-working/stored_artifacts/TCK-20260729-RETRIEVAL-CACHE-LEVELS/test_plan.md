---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-CACHE-LEVELS
artifact_type: test_plan
tags: [ai, observability]
---

# Test Plan — TCK-20260729-RETRIEVAL-CACHE-LEVELS

## Regression Surface

Files that must remain passing **unmodified**, proving the new module is genuinely additive and
never touches out-of-scope code:

**Unit — out-of-scope siblings (must not be touched by this ticket's diff):**
- `tests/unit/observability/test_retention_manager.py` (3 tests — `RetentionPolicy`/`RetentionManager`)
- `tests/unit/core/test_retention.py` (3 tests — `BoundedBuffer`/`OverflowPolicy`)
- `tests/unit/optimization/test_cache_invalidation_policy.py` (7 tests — `world_index.py`'s
  unrelated `CacheInvalidationPolicy`; also serves as the naming-collision regression guard)

**Unit/tools — retrieval-tooling regression surface:**
- `tests/tools/test_knowledge_search.py` (manifest schema, corpus scope guard, build/query paths —
  scoped with `-m "not slow"` for fast local iteration; this ticket does not modify
  `knowledge_search.py`, but if the `corpus_generation` decision reads `manifest.json`, this suite
  is the proof that read is non-mutating and the existing build/query contract is unaffected)
- `tests/tools/test_hybrid_retrieval.py` (16 tests — sibling `TCK-20260729-HYBRID-RETRIEVAL-FUSION`
  fusion module; regression guard that this ticket does not disturb it)
- `tests/tools/test_code_test_index.py` (11 tests — sibling `TCK-20260729-DETERMINISTIC-CODE-INDEX`;
  regression guard, same directory)

**Arena-combat:** none — this ticket has no combat/simulation surface.

## New Tests Required

All new tests live in `tests/tools/test_retrieval_cache.py` and must be runnable without live ML
dependencies (sentence-transformers/sqlite-vec/rank-bm25) — cache read/write/invalidation logic
has no ML dependency itself, following the dependency-free-by-default pattern established by
`tests/tools/test_hybrid_retrieval.py`.

**AC1 — Embedding/index cache: hit on unchanged hash+version, recompute+evict on either change**
- `test_index_cache_hit_on_unchanged_content_hash_and_chunking_version` — unit. Verifies a
  rebuild request with identical content hash + embedding/chunking version returns a hit (no
  recompute signaled).
- `test_index_cache_recompute_on_content_hash_change` — unit. Changing the content hash with the
  version unchanged forces recompute; verifies the stale row is evicted.
- `test_index_cache_recompute_on_chunking_version_change` — unit. Changing the
  embedding/chunking version with the content hash unchanged forces recompute; verifies the stale
  row is evicted.
- `test_index_cache_category_name_is_retrieval_index_cache` — unit. Asserts the literal category
  string stored/used is `retrieval_index_cache`, not an invented name.

**AC2 — Query-result cache: stale-reject on corpus_generation/retrieval_version change**
- `test_query_cache_hit_on_identical_query_filters_and_versions` — unit. Same normalized query +
  filters + `corpus_generation` + `retrieval_version` returns a hit.
- `test_query_cache_stale_reject_on_corpus_generation_change` — unit. Identical query+filters but
  changed `corpus_generation` is rejected as stale even though the query text is unchanged;
  asserts the returned/logged reason code is a stale-reject code, not a plain miss.
- `test_query_cache_stale_reject_on_retrieval_version_change` — unit. Same as above but for
  `retrieval_version` specifically (distinct field, must be tested independently per the idea
  doc's key definition: "normalized query + filters + corpus generation + retrieval version").
- `test_query_cache_miss_reason_code_distinct_from_stale_reject_reason_code` — unit. A genuinely
  new (never-cached) query key produces a `miss` reason code, distinguishable from a
  `stale-rejected` reason code for a key that exists but failed version validation — the idea
  doc's "Cache level/status" MAY-field explicitly lists `hit`/`miss`/`stale-rejected` as three
  distinct values, not two.
- `test_query_cache_category_name_is_retrieval_query_cache` — unit. Literal string check.

**AC3 — Context-packet cache: invalidated on cited-hash mismatch or corpus_generation/policy version change**
- `test_packet_cache_hit_when_all_cited_hashes_and_versions_match` — unit.
- `test_packet_cache_invalidated_on_single_cited_source_hash_mismatch` — unit. Only one of
  multiple cited-source hashes changing is sufficient to invalidate the whole packet entry.
- `test_packet_cache_invalidated_on_corpus_generation_change` — unit.
- `test_packet_cache_invalidated_on_policy_version_change` — unit. Tested independently from
  `corpus_generation` since the idea doc's key/invalidation columns list them as separate
  triggers ("Any cited source hash, corpus generation, policy, or budget change").
- `test_packet_cache_category_name_is_retrieval_packet_cache` — unit. Literal string check.

**AC4 — MAY-list only, no raw text, ever**
- `test_all_three_cache_tables_expose_only_may_list_columns` — architecture guard. Introspects
  each table's schema (`PRAGMA table_info` or equivalent) and asserts every column name is drawn
  from an explicit MAY-list allowlist constant defined in the new module (hashes, IDs, counts,
  reason codes, scores, latency, version numbers, cache-status) — fails loudly if a new column is
  ever added without updating the allowlist.
- `test_no_stored_row_contains_raw_prompt_or_chunk_text` — unit/architecture guard. Writes a
  realistic long excerpt/prompt string through the cache's normal write path, then asserts no
  column value in the resulting row equals or contains that literal text — only its hash may be
  stored.
- `test_write_path_rejects_a_prohibited_field_if_offered` — unit. If the cache write function
  accepts a dict/kwargs, verify passing a `raw_text`/`prompt`/`chunk_text`-shaped key either
  raises or is silently dropped, never persisted — a defensive guard against a future caller
  accidentally leaking prohibited content through the write path.

## Scoped Pytest Commands

```
# New module's own test suite
pytest tests/tools/test_retrieval_cache.py -v

# Regression: out-of-scope siblings must remain green and untouched
pytest tests/unit/observability/test_retention_manager.py tests/unit/core/test_retention.py \
       tests/unit/optimization/test_cache_invalidation_policy.py -v

# Regression: retrieval-tooling scope, fast subset (skip slow ML-dependent tests)
pytest tests/tools/test_knowledge_search.py tests/tools/test_hybrid_retrieval.py \
       tests/tools/test_code_test_index.py -m "not slow" -q
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **Naming-collision guard**: a static/introspection test asserting no class named
  `CacheInvalidationPolicy` (or a near-identical name) is defined anywhere in the new
  `tools/retrieval_cache.py` module — catches accidental reuse of `world_index.py`'s unrelated
  class name.
- **No-import-from-out-of-scope-modules guard**: a static test asserting
  `tools/retrieval_cache.py` never imports from `src.observability.reporting.retention`,
  `src.core.retention`, or `src.engine.world_index` — catches accidental coupling to the
  explicitly out-of-scope modules.
- **Category-name-literal guards**: the three `test_*_category_name_is_*` tests above (one per
  cache level) pin the exact strings `retrieval_index_cache`/`retrieval_query_cache`/
  `retrieval_packet_cache` — catches silent renaming drift away from the policy doc's fixed
  vocabulary.
- **Duration-is-not-behavior guard**: no test in the new suite may assert that a row is evicted
  strictly because 30/7/14 days elapsed — every invalidation test must construct its stale
  condition via a hash/version mismatch, never a manipulated clock/duration boundary. (Meta-check
  for code review, not a runnable assertion — but the test file's docstring should say this
  explicitly, matching the ticket's own Out of Scope wording, so a future contributor does not
  add a duration-based test by mistake.)
- **MAY-list allowlist guard** (`test_all_three_cache_tables_expose_only_may_list_columns` above)
  doubles as an anti-drift guard against future scope creep: any future column addition to any of
  the three tables fails this test until the allowlist constant is explicitly updated, forcing a
  conscious MAY/PROHIBITED review rather than a silent schema change.
- **File-isolation guard** (if Planning selects the separate-`.db`-file approach flagged in
  investigation.md Risk 2): a test asserting the cache module's db path is never equal to
  `knowledge-index/knowledge.db`'s path — guards against a future edit accidentally pointing the
  cache at the file `knowledge_search.py::cmd_build()` unconditionally `unlink()`s on every
  rebuild, which would silently destroy all cached rows.
- **Parity ledger drift guard**: confirm `docs/parity_ledger/infrastructure.yaml` still parses
  (`python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`)
  after appending the new `INFRA-295` entry, matching the verification step both sibling tickets
  (`INFRA-293`/`INFRA-294`) performed.
