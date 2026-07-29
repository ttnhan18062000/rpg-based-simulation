---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-CACHE-LEVELS
artifact_type: investigation
tags: [ai, observability]
---

# Investigation — TCK-20260729-RETRIEVAL-CACHE-LEVELS

## Current Behavior

**No retrieval cache module exists anywhere in the repo today.** Both `tools/retrieval_cache.py`
and `tests/tools/test_retrieval_cache.py` are listed in the ticket as `expected:` — confirmed:
neither file exists. This is genuinely new code, not an extension.

**`src/observability/reporting/retention.py`** (out of scope, read for pattern only):
- `RetentionPolicy.classify_run()` (L26-57) returns `(category, reason, retention_days)` with
  three day-based tiers: `baseline_source_run` (permanent, L36-37), `important_failed_run`
  (`protected_retention_days`, default 30, L54-55), `recent_run` (`normal_retention_days`,
  default 7, L57 fallback).
- `RetentionManager` (L60-241) scans `data/runs/*` directories on the filesystem and deletes
  heavy telemetry files for expired runs (`execute_cleanup()`, L169-241), preserving
  `run_manifest.json` with a `telemetry_pruned` flag.
- This governs **filesystem artifacts under `data/runs/{run_id}/`** — no relationship to
  retrieval, SQLite, or hashes. The ticket's Out of Scope forbids touching this file; the new
  module must not import from it or extend `RetentionPolicy`/`RetentionManager`.

**`src/core/retention.py`** (out of scope, read for pattern only):
- `BoundedBuffer[T]` (L26-89): an in-memory, deque-backed, fixed-`capacity` collection with an
  `OverflowPolicy` (`REJECT`/`EVICT_OLDEST`/`TRUNCATE_NEWEST`/`COMPACT`). No time-based duration
  concept, no persistence, no SQLite — a pure count-bounded eviction primitive, orthogonal to
  what this ticket needs (content-hash/version-keyed, duration-backstopped, SQLite-persisted).

**`src/engine/world_index.py::CacheInvalidationPolicy`** (L11-52) — confirmed distinct and
unrelated, exactly as the ticket's Assumptions section warns:
- `invalidated_indexes(dirty: DirtySet) -> Set[str]` (L18-33) and `should_invalidate(domain, dirty)`
  (L36-52) are static methods that map a per-tick `DirtySet` (resource/building/movement/
  ground-item/corpse/region dirty IDs) onto which in-memory `WorldIndexes` spatial buckets must be
  rebuilt this tick. It is tick-scoped, in-memory only (never persisted to SQLite), keyed by
  `DirtySet` membership — not content hash or version numbers. `graphify query
  "CacheInvalidationPolicy world_index"` confirms its only edges are to `AuthoritativeState`,
  `ResourceNodeState`, `BuildingState`, `DirtySet` — nothing retrieval-related.
- **The new module must use a distinctly-named class** — reusing or resembling
  `CacheInvalidationPolicy` would be a direct naming collision with unrelated simulation-tick code.

**`tools/knowledge_search.py`** — the manifest/index precedent:
- `_write_manifest()` (L571-587) / `_load_manifest()` (L590-599): `manifest.json`'s actual schema
  today is `{"version": 1, "built_at": "<ISO8601>", "paths": {path: mtime, ...}}`. **There is no
  `corpus_generation` or `retrieval_version` field anywhere in this schema.** `version` is a fixed
  schema-format constant (always `1`), not a corpus generation counter.
- `cmd_build()` (L627-750) fully rebuilds: `if db_path.exists(): db_path.unlink()` (L680-681)
  before recreating `knowledge_vec`/`knowledge_docs` tables — the whole `knowledge.db` file is
  destroyed and rewritten on every non-incremental build.
- `cmd_build_incremental()` (L753-942) also rewrites the whole DB file at the end (L884-886:
  `if db_path.exists(): db_path.unlink()`) even though only changed docs are re-embedded — the
  final on-disk file is still fully replaced every time either build path runs.
- Only one SQLite file exists in the repo today: `knowledge-index/knowledge.db` (confirmed via
  `find`), alongside `bm25.pkl`, `embeddings_cache.pkl`, `manifest.json` — all under
  `knowledge-index/`, all gitignored. No `.db` file exists under `tools/` or `agent-monitoring/`.

**Test files (regression surface, read fully):**
- `tests/unit/observability/test_retention_manager.py` (3 tests) and
  `tests/unit/core/test_retention.py` (3 tests) — exercise `RetentionPolicy`/`RetentionManager`
  and `BoundedBuffer` respectively; both files must remain unmodified and passing, proving
  `retention.py`/`core/retention.py` were not touched by this ticket.
- `tests/tools/test_knowledge_search.py` (~2000 lines) — confirms the manifest schema above via
  `_write_manifest`/`_load_manifest`; has no cache-level tests today (no test class references
  "cache"). `TestCorpusScopeGuard` proves `src/`/`tests/` are never indexed — irrelevant boundary
  but confirms the corpus-scope-guard test pattern this ticket's new suite should mirror for its
  own "MAY-list only" boundary guard.

## Mechanics / Engine Constraints

**None.** This is agent-orchestration/retrieval tooling, not simulation logic — the same posture
already established for the entire Phase 3 batch:
- `docs/engine/contracts/context_packet_contract.md` §4: "this contract governs
  agent-orchestration/retrieval tooling, not simulation logic, the same posture already recorded
  for agent-monitoring tooling under `docs/parity_ledger/infrastructure.yaml`'s INFRA-281 through
  INFRA-292 entries (`support_boundary` field)."
- Sibling tickets `TCK-20260729-DETERMINISTIC-CODE-INDEX` (INFRA-293) and
  `TCK-20260729-HYBRID-RETRIEVAL-FUSION` (INFRA-294) both used the identical `support_boundary`
  posture — no Mechanics Bible chapter or Engine Contract constrains simulation semantics here.

The binding constraints instead come from three Phase 2 decision docs (all already resolved,
must not be re-litigated):
- `docs/observability/retrieval_retention_redaction_policy.md` §Decision C — the exact category
  names and placeholder durations: `retrieval_index_cache` (~30d), `retrieval_query_cache` (~7d),
  `retrieval_packet_cache` (~14d or ticket-lifetime). §"MAY-Contain vs PROHIBITED Fields" — the
  exhaustive MAY list (content hashes, source/entity/ticket/run IDs, counts, reason codes, scores,
  latency, corpus/graph generation and retrieval version numbers, cache level/status) and
  PROHIBITED list (raw prompt text, raw retrieved chunk/source text, unredacted tool payloads, any
  field reproducing source content). The doc explicitly states durations "are placeholders by
  analogy... not measured values" (§Decision C footer) — tests must assert invalidation-trigger
  correctness, not duration enforcement (also stated directly in this ticket's own Out of Scope).
- `docs/engine/contracts/context_packet_contract.md` §2 — `hash` and `score` are already-named
  `ContextPacket.included[]` fields; the retention/redaction doc's MAY-list is required to stay
  consistent with this vocabulary (its own text, lines 51-54) rather than inventing new terms.
- Idea doc `idea_context_efficient_agent_retrieval_observability.md` §"3. Cache design" (lines
  137-151) — the literal Key/Value/Invalidation table this ticket's AC1-3 implement verbatim:
  - Embedding/index: key = content hash + embedding/chunking version; invalidation = source,
    model, or chunking change.
  - Query result: key = normalized query + filters + corpus generation + retrieval version;
    invalidation = any indexed-source or ranking change.
  - Context packet: key = task/ticket intent + phase + changed paths + scenario + policy version;
    invalidation = any cited source hash, corpus generation, policy, or budget change.

## Parity Ledger Overlap

**No existing entry covers retrieval caches specifically.** Grep across all 4 populated
`docs/parity_ledger/*.yaml` files for `retrieval|knowledge_search|cache` returns only unrelated
hits (`MovementPlanCache`, `ReadModelCache`, `DashboardCache` — in-memory simulation/API caches)
plus three genuinely related sibling entries, all in `infrastructure.yaml`, all `status: verified`,
`priority: P2`, using the `support_boundary` field (not a Mechanics Bible/engine-contract claim):

- **INFRA-292** (`tests/tools/test_retrieval_baseline_metrics.py`) — retrieval baseline metrics
  reporting tool, `TCK-20260728-RETRIEVAL-BASELINE-METRICS`.
- **INFRA-293** (`tests/tools/test_code_test_index.py`) — deterministic code/test symbol index,
  `TCK-20260729-DETERMINISTIC-CODE-INDEX`.
- **INFRA-294** (`tests/tools/test_hybrid_retrieval.py`) — RRF fusion module,
  `TCK-20260729-HYBRID-RETRIEVAL-FUSION`.

**No P0 entries touched.** Following this exact precedent, the implementation should append a new
`INFRA-295` entry to `docs/parity_ledger/infrastructure.yaml` for the new
`tools/retrieval_cache.py` module, `status: verified`, `priority: P2`, `test_path:
tests/tools/test_retrieval_cache.py`, and a `support_boundary` field matching the established
"agent-orchestration/retrieval tooling only — no simulation behavior, Mechanics Bible chapter, or
engine contract governs this module's semantics" wording used by INFRA-292/293/294.

## Prior Work

- **`docs/observability/retrieval_retention_redaction_policy.md`** (`TCK-20260728-RETRIEVAL-RETENTION-REDACTION`,
  decision-only, no code) — already resolved the category names/durations/MAY-PROHIBITED list this
  ticket must follow exactly; its own investigation.md (`stored_artifacts/TCK-20260728-RETRIEVAL-RETENTION-REDACTION/investigation.md`)
  independently confirmed no cache/redaction concept existed anywhere prior to that ticket, and
  flagged (Risk 4) that the three cache levels have "materially different natural retention
  shapes" and must not share one blanket duration — already reflected in Decision C's per-level
  table this ticket consumes.
- **`TCK-20260729-DETERMINISTIC-CODE-INDEX`** (done, `tools/code_test_index.py`) and
  **`TCK-20260729-HYBRID-RETRIEVAL-FUSION`** (done, `tools/hybrid_retrieval.py`) — the two sibling
  Phase 3 tickets in this same batch, both already closed. Both establish the concrete pattern
  this ticket should follow:
  - Standalone `tools/*.py` module, own `argparse` CLI, no `.claude/workflows/*.js` wiring.
  - Module-level docstring stating scope and explicit non-goals (see `tools/hybrid_retrieval.py`
    L1-18).
  - `_TOOLS_DIR = Path(__file__).resolve().parent` + `sys.path.insert` for cross-tool imports,
    since `tools/` is not a package (`tools/hybrid_retrieval.py` L26-30, `tools/knowledge_search.py`
    L41-44).
  - Explicit sentinel pattern for values with no natural source rather than silent fabrication:
    `tools/hybrid_retrieval.py`'s `UNRATED = "unrated"` sentinel (with an import-time assertion
    that it's disjoint from the real enum values it stands in for) and
    `tools/code_test_index.py`'s `DOCSTRING_GAP`/`ASSOCIATED_TESTS_GAP` sentinels — both are the
    established shape for handling "no real value exists, don't fake one" cases. This is directly
    relevant to the `corpus_generation`/`retrieval_version` open question below.
  - Both append an `INFRA-29x` parity ledger entry following the identical `support_boundary`
    pattern (see Parity Ledger Overlap above) rather than a Mechanics Bible claim.
  - Both note in Test Summary that new tests are runnable without live ML dependencies
    (sentence-transformers/sqlite-vec/rank-bm25) by stubbing only the narrow ANN-query seam —
    the new cache module's tests should follow the same dependency-free-by-default pattern, since
    cache read/write/invalidation logic itself has no ML dependency at all.
- **`tests/unit/optimization/test_cache_invalidation_policy.py`** — the existing test suite for
  `world_index.py`'s (unrelated) `CacheInvalidationPolicy`; confirms via `graphify query` that this
  class's only consumers are `WorldIndexService`/`AuthoritativeState`/`DirtySet` — no retrieval
  relationship, and its test file must remain untouched as a naming-collision regression guard.

## Risks and Open Questions

1. **`corpus_generation`/`retrieval_version` has no existing source — this is a genuine open
   implementation decision, not resolvable by investigation alone.** `manifest.json`'s actual
   schema (`version`/`built_at`/`paths`) has no field of either name. Two non-mutually-exclusive
   options observed in the code:
   - (a) Derive `corpus_generation` from `manifest.json`'s existing `built_at` timestamp (already
     present, changes whenever `knowledge_search.py build`/`build --incremental` runs) — zero
     footprint, no change to `knowledge_search.py`, but only a coarse proxy: rebuilding with
     byte-identical corpus content still bumps `built_at`, so it is not a true
     content-based generation counter.
   - (b) A new, independent monotonic counter or content-hash owned entirely by the new cache
     module (e.g. hash the corpus paths/mtimes dict from `manifest.json`, or maintain a private
     counter file) — avoids ever touching `knowledge_search.py`, but invents a second notion of
     "corpus generation" separate from the index's own `manifest.json`.
   - `retrieval_version` (the version of *retrieval logic*, not the corpus) has no natural source
     at all — no version constant exists anywhere for "retrieval logic version" today. This likely
     needs a new explicit module-level constant (mirroring `tools/hybrid_retrieval.py`'s
     `DEFAULT_RRF_K`-style constants) bumped manually when retrieval/ranking logic changes.
   - **This investigation does not resolve which option to take — flagging per this ticket's own
     Assumptions section, which explicitly defers this to planning.** Planning should pick one and
     state it explicitly; whichever is chosen, follow the sentinel-over-fabrication precedent
     above if any input value is genuinely unavailable at cache-check time.
2. **SQLite file placement is a real correctness hazard, not just a style choice.**
   `knowledge_search.py::cmd_build()` unconditionally calls `db_path.unlink()` before rebuilding
   `knowledge.db` (L680-681), and `cmd_build_incremental()` does the same at the end of its run
   (L885-886) even though it only re-embeds changed docs. **If the new cache tables were added to
   `knowledge.db` itself, every full or incremental index rebuild would silently destroy all cache
   rows** — a correctness bug, not a design nitpick. A separate `.db` file avoids this entirely and
   matches `ticket_plan_structure_phase3.md`'s own explicit guidance citing
   `tools/agent-monitoring/build_index.py`'s "second, independent SQLite-backed store" precedent.
   Investigation recommends a separate file (e.g. `knowledge-index/retrieval_cache.db` or
   `tools/retrieval_cache.db`); Planning should make the final call and a regression test should
   assert the two files never collide.
3. **Exact module file path is only a suggestion, not fixed.** The ticket's own Assumptions flag
   `tools/retrieval_cache.py` as a "suggested" path, following `tools/knowledge_search.py`'s
   precedent. No blocker — just confirming this is Planning's call, not already decided.
4. **`ContextPacket` itself does not exist in code yet** (`context_packet_contract.md` §4: "no
   code enforces this contract yet"). The packet-cache level (AC3) must therefore key/invalidate
   on the fields the contract *specifies* (cited-source content hashes, `corpus_generation`,
   `policy version`) without assuming a real `ContextPacket` class/serializer is available to
   import — the cache module operates on those fields directly, not on an assembled packet object.

## Anti-Drift Hazards

- **Do not touch `src/observability/reporting/retention.py`, `src/core/retention.py`, or
  `src/engine/world_index.py`.** Explicit ticket Out of Scope; the existing regression tests for
  all three (`test_retention_manager.py`, `test_retention.py`, `test_cache_invalidation_policy.py`)
  must remain byte-identical and passing — any diff touching these files is a scope violation.
- **Do not name any new class `CacheInvalidationPolicy`** or anything that could be confused with
  `world_index.py`'s existing class of that exact name — the ticket calls this out explicitly, and
  investigation confirms the two domains (tick-scoped in-memory spatial indexes vs.
  content-hash/version-keyed persisted retrieval caches) are unrelated.
- **Do not treat the 30d/7d/14d durations as load-bearing.** Both the ticket's Out of Scope and
  the retention/redaction policy doc state these are placeholders. Tests must assert
  invalidation-*trigger* correctness (hash/version mismatch), never assert that eviction happens
  at a specific day boundary.
- **Do not store anything beyond the MAY-list.** No raw prompt text, no raw retrieved chunk/source
  text, no unredacted tool payloads, no field that reproduces source content instead of
  referencing it by hash/ID. AC4 requires an explicit test proving this by introspecting stored
  rows.
- **Do not add a new `agent-monitoring/*.jsonl` event type** (Phase 4, explicitly out of scope for
  this ticket) or wire anything into `.claude/workflows/*.js` (Phase 5-6, explicitly out of scope).
- **Do not introduce Qdrant/Postgres/Neo4j or any external DB** — SQLite only, per both the idea
  doc and this ticket's Out of Scope.
- **Do not build a re-ranker beyond fusion+metadata filtering** — that boundary was already
  implemented and closed by `TCK-20260729-HYBRID-RETRIEVAL-FUSION`; this ticket is cache-only.
- **Do not force-resolve Open Decisions 5 or 6** of the epic idea doc — both remain explicitly
  deferred.
- **Category names must be the exact literal strings** `retrieval_index_cache`,
  `retrieval_query_cache`, `retrieval_packet_cache` — no invented names, per
  `ticket_plan_structure_phase3.md`'s explicit instruction ("same names, same field restrictions —
  do not invent new cache-level names").
