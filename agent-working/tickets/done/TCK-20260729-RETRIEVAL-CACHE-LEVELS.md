---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-CACHE-LEVELS
phase: done
date: 2026-07-29
tags: [ai, observability]
---

# TCK-20260729-RETRIEVAL-CACHE-LEVELS

## Title
3-level SQLite retrieval cache with invalidation tests

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement 3 independently invalidatable caches (embedding/index, query-result, context-packet) per the idea doc's Cache design table, using SQLite, following the already-resolved retention/redaction policy's category names (retrieval_index_cache/retrieval_query_cache/retrieval_packet_cache) and MAY/PROHIBITED field list. This is genuinely new code -- no cache implementation exists anywhere in the repo today -- and must not be built as an extension of src/observability/reporting/retention.py or src/core/retention.py, both of which are out of scope for this subsystem per the policy doc's own Out of Scope section.

## Scope
- Build 3 new SQLite cache tables -- retrieval_index_cache (~30d), retrieval_query_cache (~7d), retrieval_packet_cache (~14d) -- as a genuinely new module, not an extension of any existing retention code.
- Implement each cache's key/value/invalidation trigger per the idea doc's Cache design table (content hash + embedding/chunking version for index cache; query+filters+corpus_generation/retrieval_version for query cache; cited-source content hashes + corpus_generation/policy version for packet cache).
- Restrict every stored row to MAY-list fields only (hashes, IDs, counts, reason codes, scores, latency, version numbers, cache-status); never store raw prompt/chunk/source text.
- Introduce the corpus_generation/retrieval_version concept (new counter or derived from knowledge_search.py's manifest.json) since this ticket is first to need it -- decide and document the source as part of scope.

## Out of Scope
- Touching src/observability/reporting/retention.py, src/core/retention.py, or any tools/agent-monitoring/*.py writer.
- Any new agent-monitoring/*.jsonl event type (Phase 4).
- Shadow packets, workflow adoption, or any .claude/workflows/*.js wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG) -- SQLite only.
- Any lightweight re-ranker beyond fusion+metadata filtering.
- Force-resolving Open Decisions 5 or 6.
- Treating the idea doc's 30d/7d/14d durations as load-bearing values -- tests assert invalidation-trigger correctness (hash/version mismatch), not duration enforcement.

## Acceptance Criteria
- [x] Rebuilding the embedding/index cache with unchanged content hash + embedding/chunking version returns a hit (no re-embed); changing either causes recompute and stale-row eviction.
- [x] Query-result cache entry is rejected as stale when corpus_generation/retrieval_version changes even with identical query+filters; rejection is observable via a stale-reject/miss reason code.
- [x] Context-packet cache entry is invalidated when any cited source's content hash no longer matches, or corpus_generation/policy version changes.
- [x] Every stored row is inspectable and contains ONLY MAY-list fields; tested by asserting no row contains raw prompt/chunk text.

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION
- TCK-20260728-CONTEXT-PACKET-SCHEMA

## Related Docs
- docs/observability/retrieval_retention_redaction_policy.md
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase3.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/reporting/retention.py
- src/core/retention.py
- src/engine/world_index.py
- tools/knowledge_search.py
- tests/unit/observability/test_retention_manager.py
- tests/unit/core/test_retention.py
- tests/tools/test_knowledge_search.py
- expected: tools/retrieval_cache.py
- expected: tests/tools/test_retrieval_cache.py

## Assumptions / Open Questions
- src/engine/world_index.py already defines an unrelated class literally named CacheInvalidationPolicy for simulation-tick spatial/entity/resource indexes tied to DirtySet -- must not be confused with or reused for this retrieval-cache work; new module needs distinct naming.
- The idea doc's 30d/7d/14d durations are explicitly labeled placeholders, not measured values.
- No corpus_generation/retrieval_version concept exists in code anywhere yet; whether it's a new counter or derived from knowledge_search.py's manifest.json is an open implementation decision for planning.
- Exact file path for the new cache module is not fixed by any doc -- a scoping decision for this ticket (suggested: tools/retrieval_cache.py, following tools/knowledge_search.py's precedent).

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260729-RETRIEVAL-CACHE-LEVELS/plan.md`'s revised
(post-architecture-review) 9-step plan, followed exactly, no scope deviations.

- **Step 1 (skeleton)**: `tools/retrieval_cache.py` created. `RETRIEVAL_VERSION = 1` module
  constant; `_NO_MANIFEST = "no_manifest"` sentinel; `CACHE_DB_PATH =
  Path("knowledge-index/retrieval_cache.db")`, resolved relative to cwd exactly like sibling
  tools (`tools/knowledge_search.py::_DEFAULT_DB`), never equal to `knowledge.db`;
  `MAY_LIST_COLUMNS` trimmed to exactly the 16 columns the three tables actually carry (the
  plan's "as applicable per table" language for ID columns like `entity_id`/`ticket_id`/`run_id`
  — none of the three schemas needed them, so they were left out of the allowlist rather than
  added speculatively); `_get_connection()`/`_init_schema()` use `CREATE TABLE IF NOT EXISTS`,
  never `DROP TABLE`/`unlink()`.
- **Step 2 (index cache, AC1)**: `check_index_cache()`/`write_index_cache()`. Stale-row eviction
  is scoped exactly as the plan specifies — same `content_hash`, differing
  `embedding_version`/`chunking_version` — via one `DELETE ... WHERE content_hash = ? AND
  (embedding_version != ? OR chunking_version != ?)` before insert. A `content_hash` change
  itself is a different composite key (the hash *is* the content's identity), so the old hash's
  row is not evicted — it remains a legitimately valid entry for that old content. This is the
  plan's literal Step 2 semantics, not a deviation; my first draft test asserted the wrong thing
  here and was corrected before this ticket closed (see Test Summary).
- **Step 3 (query cache, AC2)**: `check_query_cache()`/`write_query_cache()`.
  `_corpus_generation()` reads `knowledge-index/manifest.json`'s `built_at` field directly,
  read-only, falling back to `_NO_MANIFEST` when absent. Lookup is two-phase: first by
  `(query_hash, filters_hash)` alone (no match → `MISS`), then by the full 4-column key (match →
  `HIT`); a `(query_hash, filters_hash)` match with a different `corpus_generation` or
  `retrieval_version` → `STALE_REJECTED` with a distinct reason code per field. No stale-row
  eviction on write (the plan does not require it for this table, unlike Step 2 — rows for
  superseded generations are left for the `prune` backstop).
- **Step 4 (packet cache, AC3)**: `check_packet_cache()`/`write_packet_cache()` take raw fields
  only (`packet_key_hash`, `cited_hashes`, `corpus_generation`, `policy_version`) — no
  `ContextPacket` import anywhere, matching investigation Risk 4. Cited-hash comparison is
  set-based, so a single-hash mismatch among several is caught.
- **Step 5 (MAY-list guard, AC4)**: one shared `_validate_may_list_kwargs()` used by all three
  `write_*_cache()` functions; raises `ValueError` on any kwarg outside `MAY_LIST_COLUMNS` or on
  a caller-supplied `created_at` (which is always stamped internally via `time.time()`).
- **Step 6 (static guards)**: verified via new AST-based tests — no `CacheInvalidationPolicy`
  class defined, no import from the three out-of-scope modules, `CACHE_DB_PATH !=
  tools.knowledge_search._DEFAULT_DB`.
- **Step 7 (CLI + prune)**: `argparse` subcommands `stats`/`check-index`/`check-query`/
  `check-packet`/`prune`, mirroring `tools/hybrid_retrieval.py`/`tools/knowledge_search.py`'s
  shape. `prune(older_than_days, table="all")` does a plain per-table `DELETE ... WHERE
  created_at < ?`; confirmed (by a dedicated static test reading `inspect.getsource()` of all six
  `check_*`/`write_*` functions) that none of them reference `prune`. Manual CLI smoke-tested
  (`stats`, `check-index`, `check-query`, `check-packet`, `prune --older-than-days 30`) against a
  freshly created DB — all exit 0.
- **Step 8 (parity ledger)**: appended `INFRA-295` to `docs/parity_ledger/infrastructure.yaml`
  following the `INFRA-292`–`294` shape exactly (`status: verified`, `priority: P2`,
  `support_boundary` wording matching the established agent-tooling posture). Confirmed the file
  still parses as a flat YAML list of 300 entries with `INFRA-295` as the final one, matching the
  schema's `required: [id, text, status, priority]` plus `v2_evidence`/`test_path` (required
  since `status: verified`).
- **Step 9 (regression)**: ran all three scoped pytest commands from `test_plan.md` — see Test
  Summary. `.gitignore` line 264 (`knowledge-index/`) already covers the new
  `retrieval_cache.db`; confirmed via `git check-ignore -v knowledge-index/retrieval_cache.db` —
  no `.gitignore` edit needed.

No conflict with the plan was found; no additional entry was needed in
`staging_artifacts/TCK-20260729-RETRIEVAL-CACHE-LEVELS/plan.md`'s "Deviations" section beyond
what that section (Revision 1) already documents.

## Test Summary

New suite `tests/tools/test_retrieval_cache.py` (25 tests, all passing), covering AC1-AC4 plus
the 3 new `prune` tests and 2 static guards plus 2 manifest-sentinel tests, per
`staging_artifacts/TCK-20260729-RETRIEVAL-CACHE-LEVELS/test_plan.md`. One test
(`test_recompute_on_content_hash_change`) was corrected mid-implementation: its first draft
incorrectly asserted the old `content_hash`'s row gets evicted when a new hash is written, which
does not match the plan's Step 2 eviction scope (same-hash-different-version only, not
cross-hash) — fixed to assert MISS-then-HIT on the new key instead, with a comment explaining why
the old row legitimately remains.

Commands run, all green:
```
pytest tests/tools/test_retrieval_cache.py -v
  → 25 passed
pytest tests/unit/observability/test_retention_manager.py tests/unit/core/test_retention.py \
       tests/unit/optimization/test_cache_invalidation_policy.py -v
  → 13 passed (retention.py, core/retention.py, world_index.py's CacheInvalidationPolicy all
    untouched and green — naming-collision and out-of-scope-module regression guard confirmed)
pytest tests/tools/test_knowledge_search.py tests/tools/test_hybrid_retrieval.py \
       tests/tools/test_code_test_index.py -m "not slow" -q
  → 103 passed, 28 deselected
```
`pytest tests/` was never run, per the Testing Rule.

## Files Changed

- `tools/retrieval_cache.py` (new)
- `tests/tools/test_retrieval_cache.py` (new)
- `docs/parity_ledger/infrastructure.yaml` (appended `INFRA-295`)

## Completion Summary

Implemented the 3-level SQLite retrieval cache (`tools/retrieval_cache.py`) exactly per the
architecture-review-approved revised plan: embedding/index cache (content-hash +
embedding/chunking-version keyed, same-hash stale-row eviction on version change), query-result
cache (query+filters+corpus_generation+retrieval_version keyed, stale-reject with distinct reason
codes on generation/version drift), and context-packet cache (cited-hash-set +
corpus_generation + policy_version keyed, invalidated on any single field mismatch) — all backed
by one isolated `knowledge-index/retrieval_cache.db` file, never `knowledge-index/knowledge.db`.
Every write path is enforced through one shared MAY-list allowlist guard that raises on any
prohibited field; no raw prompt/chunk/source text is ever persisted (verified by a dedicated
test). Each table carries a `created_at` column and a manual, non-hot-path `prune
--older-than-days N` CLI subcommand — the Durable-State-Rule lifecycle backstop added in the
plan's post-architecture-review revision — confirmed never invoked from any hot-path
`check_*`/`write_*` function. Added `INFRA-295` to the parity ledger. All 25 new tests plus all
three scoped regression suites (retention/core-retention/world_index naming-collision guard;
knowledge_search/hybrid_retrieval/code_test_index siblings) pass. No out-of-scope file was
touched; `.gitignore` already covered the new `.db` file.
