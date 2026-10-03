---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-CACHE-LEVELS
artifact_type: plan
tags: [ai, observability]
---

# Implementation Plan — TCK-20260729-RETRIEVAL-CACHE-LEVELS

## Summary

Build a single new, standalone module `tools/retrieval_cache.py` implementing three
independently-invalidatable SQLite-backed caches — `retrieval_index_cache`,
`retrieval_query_cache`, `retrieval_packet_cache` — per the idea doc's Cache design table and the
already-resolved retention/redaction policy's category names and MAY/PROHIBITED field list. The
module owns its own SQLite file (`knowledge-index/retrieval_cache.db`), distinct from
`knowledge-index/knowledge.db`, to avoid the confirmed hazard that `knowledge_search.py`'s build
commands unconditionally `unlink()` and rewrite `knowledge.db` on every rebuild. Each cache level
gets its own table, a narrow MAY-list-only write path, and a `check(...)` function that returns a
`hit` / `miss` / `stale-rejected` status plus reason code, keyed and invalidated exactly per the
idea doc's table (content hash + embedding/chunking version for index cache; normalized query +
filters + corpus_generation + retrieval_version for query cache; cited-source content hashes +
corpus_generation + policy version for packet cache). `corpus_generation` is derived as a proxy
from `manifest.json`'s existing `built_at` field (read-only, no changes to `knowledge_search.py`);
`retrieval_version` is a new module-level constant owned entirely by this module. Each of the three
tables also carries a `created_at` column (an ordinary MAY-list management column) and the CLI
gets one manual, non-hot-path `prune --older-than-days N` subcommand — this is the row-lifecycle
mechanism required by Decision C of `docs/observability/retrieval_retention_redaction_policy.md`
("caches ARE eligible for duration-based expiry... a safety backstop"), added in response to an
architecture-review finding on an earlier version of this plan (see "Deviations"). Work proceeds
in 9 narrow, independently-verifiable steps: module skeleton + schema, index-cache logic,
query-cache logic, packet-cache logic, MAY-list enforcement guard, naming/import isolation guards,
CLI entrypoint (mirroring sibling tools, including `prune`), parity ledger entry, and full
regression verification.

## Resolved Decisions

These three items were flagged as open questions in `investigation.md`'s "Risks and Open
Questions" section. Per the calling agent's explicit direction, all three are resolved here with
a stated default — none is carried forward as a genuinely unresolved question.

**1. Cache DB file location — `knowledge-index/retrieval_cache.db`, a separate file from
`knowledge-index/knowledge.db`.**
This is a correctness requirement, not a style preference. `investigation.md` confirms (citing
`tools/knowledge_search.py:680-681` and `:884-886`) that both `cmd_build()` and
`cmd_build_incremental()` unconditionally `db_path.unlink()` and fully rewrite `knowledge.db` on
every run. If the new cache tables lived inside that same file, every index rebuild — full or
incremental — would silently destroy every cached row with no error, no warning, and no test able
to catch it short of a full rebuild-then-assert cycle. A separate file makes this hazard
structurally impossible: `knowledge_search.py` never opens, imports, or references
`retrieval_cache.db`, so nothing in that module's rebuild path can touch it. This follows the
precedent `ticket_plan_structure_phase3.md` and this ticket's own investigation both cite:
`tools/agent-monitoring/build_index.py`'s "second, independent SQLite-backed store" pattern —
sibling infrastructure tooling already established that pattern for exactly this reason
(isolating a derived/cache store from a primary store's rebuild lifecycle). Step 8 adds a
regression test asserting the two file paths are never equal, per `test_plan.md`'s File-isolation
guard.

**2. `corpus_generation` source — proxy derived from `manifest.json`'s existing `built_at` field.**
Investigation's option (a): read `knowledge-index/manifest.json` (via `_load_manifest()`'s
existing schema — `{version, built_at, paths}`) and use `built_at` directly as the
`corpus_generation` value. This is a read-only consumption of a field that already exists — zero
new footprint in `knowledge_search.py`, no new counter system, no risk of the two notions of
"generation" diverging because there is only one. It is an accepted coarse proxy (a byte-identical
rebuild still bumps `built_at`), which is fine: AC2/AC3 test *trigger correctness on change*, not
precision of what counts as a "real" content change — a stricter content-hash-based generation
counter would be new infrastructure this ticket has no mandate to build in `knowledge_search.py`
itself (which is explicitly not in this ticket's touched-files list; it is read, never written).
If `manifest.json` does not exist at cache-check time (index never built), `corpus_generation`
resolves to an explicit `_NO_MANIFEST` sentinel string — never a fabricated timestamp — following
the sentinel-over-fabrication precedent below.

**3. `retrieval_version` source — new module-level constant `RETRIEVAL_VERSION = 1` defined in
`tools/retrieval_cache.py` itself.**
No existing source for "version of retrieval logic" exists anywhere in the repo (confirmed by
investigation). Rather than deriving it from something unrelated, this plan defines it as a plain
integer constant at module scope, manually bumped by a future contributor whenever this module's
own key derivation or invalidation logic changes in a way that should invalidate all previously
cached rows. This mirrors the sentinel-over-fabrication precedent already established in this
same tool epic: `tools/hybrid_retrieval.py`'s `UNRATED = "unrated"` sentinel (with an import-time
disjointness assertion against real enum values) and `tools/code_test_index.py`'s
`DOCSTRING_GAP`/`ASSOCIATED_TESTS_GAP` sentinels — both exist because "no real value is available,
don't fake one" is the established shape for this exact class of problem. `RETRIEVAL_VERSION`
follows the same spirit: an explicit, visible, intentionally-manual value instead of an invented
derivation from unrelated data.

**4. Module file path — `tools/retrieval_cache.py` (flat `tools/` module, no subpackage).**
Confirmed as the ticket's own suggested path and consistent with `tools/knowledge_search.py` and
`tools/hybrid_retrieval.py`'s existing flat-module precedent for this epic. Tests live at
`tests/tools/test_retrieval_cache.py`, mirroring `tests/tools/test_hybrid_retrieval.py`.

**5. Lifecycle mechanism for the three cache tables — a `created_at` column on all three tables
plus a manual, non-hot-path `prune --older-than-days N` CLI subcommand (added in this revision;
see "Deviations" below).**
This was not one of `investigation.md`'s three originally-flagged open questions; it is added
here in response to an architecture-review `NEEDS_CHANGES` verdict on an earlier version of this
plan. The finding: as originally specified, none of the three tables had any timestamp column,
and Step 7's CLI exposed read-only introspection only (`stats`, `check-index`, `check-query`,
`check-packet`) — no delete/prune path of any kind. A row for a query or packet that is never
asked again, or an index-cache row for content that leaves the corpus, had **no path to ever
being removed**; all three tables would grow strictly monotonically forever. That is a Durable
State Rule (CLAUDE.md) violation — durable rows with no defined lifecycle — and it is precisely
the risk `docs/observability/retrieval_retention_redaction_policy.md` Decision C anticipates:
unlike `agent-monitoring/*.jsonl`'s append-only-forever events, caches "ARE eligible for
duration-based expiry," with duration explicitly framed there as "a safety backstop, not the
primary invalidation signal" — i.e., caches are *not* self-bounding via hash/version mismatch
alone, and are expected to have some backstop path.
The fix: (a) add `created_at` to `MAY_LIST_COLUMNS` as an ordinary management column, on the same
footing as `reason_code`/`cache_status` — it is metadata about the row, not content, so it does
not touch the MAY/PROHIBITED content boundary at all; (b) add one manual CLI subcommand,
`prune --older-than-days N`, that an operator invokes by hand to delete rows older than a
supplied threshold, across all three tables. This is deliberately **not** wired into the
`check_*`/`write_*` hot path — no TTL check runs on every cache lookup or write, no schedule, no
default threshold baked into the module. This distinction matters for the ticket's actual
Out-of-Scope wording ("Treating the idea doc's 30d/7d/14d durations as load-bearing values — no
test may assert eviction based on elapsed days/a manipulated clock; every invalidation test
constructs its stale condition via a hash/version mismatch only"): that line bans tests that
assert *exact duration enforcement* against the primary hit/miss/stale-reject invalidation path
(Steps 2-4) — it does not, and was never read by the reviewer to, ban the module from having *any*
prune mechanism at all. `prune`'s own test seeds a row with an explicit past `created_at` value
and asserts a count before/after — no clock mocking, no elapsed-day precision assertion, no
change to Steps 2-4's hash/version-mismatch tests. See "Deviations" below for what changed
relative to the pre-review version of this plan.

## Steps

### Step 1 — Module skeleton, schema constants, MAY-list allowlist, DB path isolation
**Files:** `tools/retrieval_cache.py` (new)
**Change:**
- Module docstring stating scope explicitly (mirror `tools/hybrid_retrieval.py` L1-18 style):
  what this module is (3-level SQLite retrieval cache), what it is not (no re-ranker, no external
  DB, no `retention.py`/`world_index.py` relationship, no workflow wiring), and the source ticket.
- `from __future__ import annotations`; standard imports (`sqlite3`, `json`, `hashlib`, `time`,
  `pathlib.Path`, `dataclasses`, `enum`, `typing`). No import from
  `src.observability.reporting.retention`, `src.core.retention`, or `src.engine.world_index`
  (Step 6 adds a static test asserting this).
- `_TOOLS_DIR = Path(__file__).resolve().parent` (mirror existing sibling pattern) — not
  strictly required for cross-tool imports here since this module only reads `manifest.json`
  directly by path, but keep for consistency if any cross-tool import is added later; do not add
  `sys.path.insert` unless actually needed.
- `RETRIEVAL_VERSION: int = 1` module-level constant, with a comment explaining it is manually
  bumped on breaking changes to this module's own key/invalidation logic (Resolved Decision 3).
- `_NO_MANIFEST = "no_manifest"` sentinel constant for missing `manifest.json` (Resolved
  Decision 2), with a short comment citing the sentinel-over-fabrication precedent
  (`tools/hybrid_retrieval.py::UNRATED`, `tools/code_test_index.py`'s gap sentinels).
- `CACHE_DB_PATH: Path` — resolves to `knowledge-index/retrieval_cache.db`, computed relative to
  the repo root (mirror how `tools/knowledge_search.py` locates `knowledge-index/`), **not**
  hardcoded to a different absolute location, and not equal to `knowledge-index/knowledge.db`.
- Exact category name constants: `INDEX_CACHE_CATEGORY = "retrieval_index_cache"`,
  `QUERY_CACHE_CATEGORY = "retrieval_query_cache"`, `PACKET_CACHE_CATEGORY =
  "retrieval_packet_cache"` — literal strings, no derivation, per
  `ticket_plan_structure_phase3.md`'s explicit instruction not to invent names.
- `CacheStatus` enum or literal-typed constants: `HIT = "hit"`, `MISS = "miss"`,
  `STALE_REJECTED = "stale-rejected"` — three distinct values (test_plan.md requires miss and
  stale-rejected to be distinguishable).
- `MAY_LIST_COLUMNS: frozenset[str]` — the explicit allowlist constant used by Step 5's guard
  test. Populate with the MAY-list categories from the policy doc: content hash columns
  (`content_hash`, `cited_hashes`/similar), ID columns (`source_id`, `entity_id`, `ticket_id`,
  `run_id` as applicable per table), count columns, `reason_code`, `score`, `latency_ms`,
  `corpus_generation`, `retrieval_version`/`embedding_version`/`chunking_version`/
  `policy_version` as relevant per table, `cache_status`, and `created_at` (see below). No
  column named anything resembling `text`, `prompt`, `chunk`, `payload`, or `content` (as
  opposed to `content_hash`).
- `created_at` — an ordinary MAY-list management column, added to `MAY_LIST_COLUMNS` on the same
  footing as `reason_code`/`cache_status` (metadata about the row, not content). Present on all
  three tables (Steps 2-4). Per Decision C of
  `docs/observability/retrieval_retention_redaction_policy.md`, caches — unlike
  `agent-monitoring/*.jsonl`'s append-only-forever events — are explicitly "eligible for
  duration-based expiry" with duration framed as a backstop, not the primary invalidation signal
  (hash/version mismatch remains primary, per Anti-Drift Notes below). This column is what makes
  that backstop exercisable: without it no row in any of the three tables has any lifecycle path
  at all, which is a Durable State Rule (CLAUDE.md) violation — a store with no defined lifecycle
  for content that stops being asked for. `write_*_cache()` (Steps 2-4) stamps
  `created_at = time.time()` (Unix epoch float, UTC) itself on every insert/overwrite — it is
  system-set at write time, not a caller-supplied kwarg — so it reflects "last written," matching
  the "last-written-at" semantics a prune-by-age pass needs. It is not part of any table's
  composite/primary key.
- `def _get_connection() -> sqlite3.Connection` — opens `CACHE_DB_PATH`, creates parent dir if
  needed, does **not** delete/unlink any existing file (unlike `knowledge_search.py`'s rebuild
  functions) — this module never destructively rewrites its own DB file except via explicit
  per-row eviction on invalidation.
- `def _init_schema(conn) -> None` — `CREATE TABLE IF NOT EXISTS` for all three tables (see Steps
  2-4 for exact per-table columns), called idempotently, never `DROP TABLE`.
**Do NOT touch:** `tools/knowledge_search.py`, `src/observability/reporting/retention.py`,
`src/core/retention.py`, `src/engine/world_index.py`. Do not add a `manifest.json`-writing code
path — read only.
**Verify:** New module imports cleanly (`python3 -c "import tools.retrieval_cache"` or equivalent
sys.path setup matching sibling tools); no test file yet required for this step alone, but Step 6
will assert `CACHE_DB_PATH != knowledge-index/knowledge.db` path and the category-name literals.

### Step 2 — Embedding/index cache (AC1)
**Files:** `tools/retrieval_cache.py`
**Change:**
- Table `retrieval_index_cache_rows` (or equivalent name under the `retrieval_index_cache`
  category) with columns from `MAY_LIST_COLUMNS`: `content_hash TEXT`, `embedding_version TEXT`
  (or `chunking_version TEXT` — combine per idea doc: "content hash + embedding/chunking
  version"; use two columns `embedding_version` and `chunking_version` if the idea doc
  distinguishes them, else one `index_version`), `source_id TEXT`, `cache_status TEXT`,
  `reason_code TEXT`, `created_at TEXT` (Unix epoch or ISO8601, stamped by `write_index_cache` on
  every insert/overwrite — see Step 1's `created_at` entry). Primary/unique key on
  `(content_hash, embedding_version, chunking_version)` or equivalent composite; `created_at` is
  not part of this key.
- `def check_index_cache(content_hash: str, embedding_version: str, chunking_version: str) ->
  IndexCacheResult` (small dataclass: `status`, `reason_code`) — looks up by the composite key
  exactly; if found → `HIT`; if not found → `MISS`.
- `def write_index_cache(content_hash: str, embedding_version: str, chunking_version: str,
  **may_list_kwargs) -> None` — inserts a row; rejects/drops any kwarg not in `MAY_LIST_COLUMNS`
  (Step 5 tests this defensively — implement the drop/reject here).
- `def invalidate_index_cache_on_change(old_content_hash, new_content_hash, old_version,
  new_version) -> bool` or simpler: since the key itself is the hash+version composite, a
  "change" naturally produces a cache miss on the new key — implement stale-row eviction as: when
  `write_index_cache` is called for a `content_hash` that already has rows under different
  version values, delete those stale rows (`DELETE FROM ... WHERE content_hash = ? AND
  (embedding_version != ? OR chunking_version != ?)`) before inserting the new row. This
  satisfies "changing either causes recompute and stale-row eviction" from AC1.
**Do NOT touch:** Any other cache table's code (Steps 3-4 not yet written). Do not implement
duration-based eviction (no `~30d` TTL logic) — per Out of Scope, durations are not load-bearing.
**Verify:** `test_index_cache_hit_on_unchanged_content_hash_and_chunking_version`,
`test_index_cache_recompute_on_content_hash_change`,
`test_index_cache_recompute_on_chunking_version_change`,
`test_index_cache_category_name_is_retrieval_index_cache`.

### Step 3 — Query-result cache (AC2)
**Files:** `tools/retrieval_cache.py`
**Change:**
- Table `retrieval_query_cache_rows` with columns: `query_hash TEXT` (hash of normalized query
  text — never the raw query text itself, per MAY-list), `filters_hash TEXT` (hash of filters
  dict), `corpus_generation TEXT`, `retrieval_version INTEGER`, `cache_status TEXT`,
  `reason_code TEXT`, `score REAL` (optional, if a top score is cached), `latency_ms REAL`
  (optional), `created_at TEXT` (Unix epoch or ISO8601, stamped by `write_query_cache` on every
  insert/overwrite — see Step 1's `created_at` entry). Composite key: `(query_hash, filters_hash,
  corpus_generation, retrieval_version)`; `created_at` is not part of this key.
- `def _corpus_generation() -> str` — implements Resolved Decision 2: reads
  `knowledge-index/manifest.json` via the same schema `_load_manifest()` in
  `knowledge_search.py` uses (`{version, built_at, paths}`), returns `built_at`; returns
  `_NO_MANIFEST` sentinel if the file is absent. This is the single shared helper both Step 3 and
  Step 4 call.
- `def check_query_cache(query: str, filters: dict, corpus_generation: str, retrieval_version:
  int) -> QueryCacheResult` — hash `query` (normalized — e.g. lowercased/stripped) and `filters`
  (stable JSON-sorted hash) internally, never store raw query text as a column value. Look up by
  composite key:
  - No row with matching `(query_hash, filters_hash)` at all → `MISS`.
  - Row exists with matching `(query_hash, filters_hash)` but different `corpus_generation` or
    different `retrieval_version` → `STALE_REJECTED` with a reason code distinguishing which
    field changed (e.g. `reason_code = "corpus_generation_mismatch"` vs
    `"retrieval_version_mismatch"`).
  - Row exists with all four fields matching → `HIT`.
- `def write_query_cache(...)` — same MAY-list-kwargs-only discipline as Step 2.
**Do NOT touch:** `_corpus_generation()` must not write to `manifest.json` or call any
`knowledge_search.py` build function — read-only consumption only.
**Verify:** `test_query_cache_hit_on_identical_query_filters_and_versions`,
`test_query_cache_stale_reject_on_corpus_generation_change`,
`test_query_cache_stale_reject_on_retrieval_version_change`,
`test_query_cache_miss_reason_code_distinct_from_stale_reject_reason_code`,
`test_query_cache_category_name_is_retrieval_query_cache`.

### Step 4 — Context-packet cache (AC3)
**Files:** `tools/retrieval_cache.py`
**Change:**
- Table `retrieval_packet_cache_rows` with columns: `packet_key_hash TEXT` (hash of
  task/ticket-intent + phase + changed-paths + scenario, per idea doc's key definition),
  `cited_hashes_json TEXT` (JSON array of the cited-source content hashes that were true at write
  time — array of hashes only, never source text), `corpus_generation TEXT`, `policy_version
  TEXT`, `cache_status TEXT`, `reason_code TEXT`, `created_at TEXT` (Unix epoch or ISO8601,
  stamped by `write_packet_cache` on every insert/overwrite — see Step 1's `created_at` entry;
  not part of the `packet_key_hash` primary key).
- `def check_packet_cache(packet_key_hash: str, current_cited_hashes: list[str],
  corpus_generation: str, policy_version: str) -> PacketCacheResult`:
  - No row for `packet_key_hash` → `MISS`.
  - Row exists but `set(current_cited_hashes) != set(stored cited_hashes)` (any single cited
    hash differs) → `STALE_REJECTED`, reason code e.g. `"cited_hash_mismatch"`. This
    specifically satisfies AC3's "invalidated when any cited source's content hash no longer
    matches" — test with only one of several hashes changed.
  - Row exists, hashes match, but `corpus_generation` or `policy_version` differs → `
    STALE_REJECTED` with a distinct reason code per field (`"corpus_generation_mismatch"` /
    `"policy_version_mismatch"`), mirroring Step 3's per-field reason code pattern.
  - All match → `HIT`.
- `def write_packet_cache(...)` — same MAY-list-kwargs-only discipline; note per investigation
  Risk 4, no real `ContextPacket` class is imported or assumed — this function takes the raw
  fields (`packet_key_hash`, `cited_hashes`, `corpus_generation`, `policy_version`) directly as
  arguments, not an assembled packet object.
**Do NOT touch:** Do not import `ContextPacket` from anywhere (it does not exist in code yet per
`context_packet_contract.md` §4) — operate on the raw fields only, exactly as investigation Risk
4 specifies.
**Verify:** `test_packet_cache_hit_when_all_cited_hashes_and_versions_match`,
`test_packet_cache_invalidated_on_single_cited_source_hash_mismatch`,
`test_packet_cache_invalidated_on_corpus_generation_change`,
`test_packet_cache_invalidated_on_policy_version_change`,
`test_packet_cache_category_name_is_retrieval_packet_cache`.

### Step 5 — MAY-list enforcement guard (AC4)
**Files:** `tools/retrieval_cache.py`
**Change:**
- In each `write_*_cache()` function (Steps 2-4), before inserting: filter/validate that every
  kwarg key is in `MAY_LIST_COLUMNS`; if a caller passes a key shaped like `raw_text`, `prompt`,
  `chunk_text`, `source_text`, or any key not in the allowlist, either raise `ValueError` or
  silently drop it before the SQL insert (silently drop is safer for a defensive guard that must
  never break a caller — prefer raise, since a raise is louder and this is new code with no
  existing callers to break; document the choice in the module docstring).
- Add a small `def _validate_may_list_kwargs(kwargs: dict, table: str) -> dict` helper shared by
  all three `write_*_cache()` functions, so the enforcement logic lives in exactly one place.
- `created_at` is stamped internally by each `write_*_cache()` function itself (`time.time()`),
  never accepted as a caller-supplied kwarg — so it never flows through
  `_validate_may_list_kwargs()`'s caller-input path. It is still listed in `MAY_LIST_COLUMNS` and
  still asserted present by Step 5's `test_all_three_cache_tables_expose_only_may_list_columns`
  (which introspects `PRAGMA table_info`, not caller kwargs), since it is a real, inspectable
  column on all three tables.
**Do NOT touch:** Schema/logic from Steps 2-4 beyond wrapping their insert calls with this
validation helper.
**Verify:** `test_all_three_cache_tables_expose_only_may_list_columns` (introspects `PRAGMA
table_info` against `MAY_LIST_COLUMNS`), `test_no_stored_row_contains_raw_prompt_or_chunk_text`,
`test_write_path_rejects_a_prohibited_field_if_offered`.

### Step 6 — Naming-collision and import-isolation static guards
**Files:** `tools/retrieval_cache.py` (no change expected — this step is test-only, listed
separately because it verifies a property of Steps 1-5's code rather than adding new runtime
behavior)
**Change:** None to the module itself if Steps 1-5 were followed correctly (no class named
`CacheInvalidationPolicy`, no import from the three out-of-scope modules). If Step 6's tests fail
against the code written in Steps 1-5, fix the module to comply — do not weaken the tests.
**Do NOT touch:** `src/engine/world_index.py`, `tests/unit/optimization/
test_cache_invalidation_policy.py` (must stay byte-identical/passing, serving as the
naming-collision regression guard per test_plan.md).
**Verify:** New tests in `tests/tools/test_retrieval_cache.py`:
- Static test asserting no class named `CacheInvalidationPolicy` (or near-identical) is defined
  in `tools/retrieval_cache.py` (e.g. via `inspect.getmembers` + name check, or AST parse).
- Static test asserting `tools/retrieval_cache.py` never imports from
  `src.observability.reporting.retention`, `src.core.retention`, or `src.engine.world_index`
  (e.g. AST-parse the module source and check `Import`/`ImportFrom` node module names).
- File-isolation test: `retrieval_cache.CACHE_DB_PATH != <knowledge_search's knowledge.db path>`
  (Resolved Decision 1 / test_plan.md's File-isolation guard).
Plus regression: `tests/unit/optimization/test_cache_invalidation_policy.py`,
`tests/unit/observability/test_retention_manager.py`, `tests/unit/core/test_retention.py` all
still pass, unmodified.

### Step 7 — CLI entrypoint, including manual `prune` subcommand (AC4 lifecycle fix)
**Files:** `tools/retrieval_cache.py`
**Change:** Add a minimal `argparse`-based `if __name__ == "__main__":` block exposing
introspection subcommands (`stats` — print row counts per table; `check-index`, `check-query`,
`check-packet` — manual CLI invocations of the `check_*` functions for debugging), mirroring
`tools/hybrid_retrieval.py`'s and `tools/knowledge_search.py`'s existing CLI shape, **plus** one
new mutating subcommand:
- `prune --older-than-days N [--table {index,query,packet,all}]` — deletes rows from the
  specified table(s) (default `all`) where `created_at` is older than `N` days before "now"
  (`time.time() - N * 86400`), and prints the number of rows deleted per table. Implemented as a
  plain `DELETE FROM <table> WHERE created_at < ?` per table, using the same `_get_connection()`
  as everything else — no new schema, no new module-level state.
- This is the lifecycle mechanism required by
  `docs/observability/retrieval_retention_redaction_policy.md` Decision C: caches "ARE eligible
  for duration-based expiry," with duration framed there as "a safety backstop, not the primary
  invalidation signal" (hash/version mismatch, per Steps 2-4, remains primary). `prune` is that
  backstop: a human/operator runs it manually, supplying whatever `N` they choose at invocation
  time — this module hardcodes no default threshold and no schedule.
- `prune` is **not** called from `check_*_cache()` or `write_*_cache()` — those hot-path
  functions never read `created_at` for eviction decisions and never call `prune` themselves.
  Confirming this stays non-hot-path is deliberate: it keeps every existing Steps 2-4
  hash/version-mismatch invalidation test unaffected, and it means no test needs to assert
  exact-duration enforcement (mocked clocks, `time.sleep`, or elapsed-day assertions) to cover
  `prune` — a single test can seed rows with an explicit `created_at` value in the past (no clock
  manipulation needed, since the row's own stored value is the input) and assert row count
  before/after. This keeps the ticket inside its actual Out-of-Scope wording (see Resolved
  Decision 5 below) while closing the "no row can ever be removed" gap.
No `.claude/workflows/*.js` wiring (explicit Out of Scope) — `prune` is a manual CLI-only
operation, never scheduled or auto-invoked by any workflow file.
**Do NOT touch:** No `.claude/workflows/` file, no `tools/agent-monitoring/*.py` writer. Do not
add a TTL/expiry check inside `check_index_cache`, `check_query_cache`, `check_packet_cache`,
`write_index_cache`, `write_query_cache`, or `write_packet_cache` — `prune` is the only code path
that reads `created_at` for deletion purposes.
**Verify:** Manual smoke check for `stats`/`check-*` (`python3 tools/retrieval_cache.py stats`
runs without error against a freshly-created empty DB). Dedicated pytest coverage for `prune`:
`test_prune_deletes_rows_older_than_threshold_across_all_three_tables`,
`test_prune_leaves_rows_newer_than_threshold_untouched`,
`test_prune_is_not_invoked_by_any_check_or_write_function` (static/behavioral — asserts
`check_*_cache`/`write_*_cache` source or call graph never references the prune function).

### Step 8 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Append a new `INFRA-295` entry following the exact shape of `INFRA-292`/`293`/`294`
(id, text, status: `verified`, priority: `P2`, legacy_evidence: `null`, v2_evidence citing
specific `tools/retrieval_cache.py` line ranges for the three `check_*`/`write_*` function pairs,
the `CACHE_DB_PATH` isolation, the `created_at` column on all three tables, and the `prune`
subcommand, proof_type: `regression`, test_path:
`tests/tools/test_retrieval_cache.py`, divergence_note: `null`, support_boundary: matching
wording — "Agent-orchestration/retrieval tooling only — no simulation behavior, Mechanics Bible
chapter, or engine contract governs this module's semantics (same category as INFRA-281 through
INFRA-294). No `src/` file touched; `knowledge-index/knowledge.db` never opened or modified by
this module — a separate `knowledge-index/retrieval_cache.db` file is used specifically to avoid
`knowledge_search.py`'s unconditional rebuild-time `unlink()` of `knowledge.db`.").
**Do NOT touch:** Any other entry in `infrastructure.yaml`; do not renumber existing
`INFRA-29x` entries.
**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`
parses cleanly (test_plan.md's Parity ledger drift guard).

### Step 9 — Full regression verification
**Files:** none (verification only)
**Change:** None.
**Do NOT touch:** n/a.
**Verify:** Run exactly the three scoped pytest commands from `test_plan.md`:
```
pytest tests/tools/test_retrieval_cache.py -v
pytest tests/unit/observability/test_retention_manager.py tests/unit/core/test_retention.py \
       tests/unit/optimization/test_cache_invalidation_policy.py -v
pytest tests/tools/test_knowledge_search.py tests/tools/test_hybrid_retrieval.py \
       tests/tools/test_code_test_index.py -m "not slow" -q
```
Never run `pytest tests/`. Also confirm `.gitignore`'s existing `knowledge-index/` directory
entry (line 264) already covers `knowledge-index/retrieval_cache.db` — no `.gitignore` edit
needed (confirmed during planning; re-verify at implementation time that no runtime `.db`/`.pkl`
artifact is accidentally staged in `git status`).

## Scope Guards

Verbatim from the ticket's Out of Scope section — none of the following may be touched by this
ticket's diff:
- Touching `src/observability/reporting/retention.py`, `src/core/retention.py`, or any
  `tools/agent-monitoring/*.py` writer.
- Any new `agent-monitoring/*.jsonl` event type (Phase 4).
- Shadow packets, workflow adoption, or any `.claude/workflows/*.js` wiring (Phase 5-6).
- Any external vector/graph DB (Qdrant/Postgres/Neo4j/hosted RAG) — SQLite only.
- Any lightweight re-ranker beyond fusion+metadata filtering (that boundary belongs to the
  already-closed `TCK-20260729-HYBRID-RETRIEVAL-FUSION`).
- Force-resolving Open Decisions 5 or 6 of the epic idea doc.
- Treating the idea doc's 30d/7d/14d durations as load-bearing values — no test may assert
  eviction based on elapsed days/a manipulated clock; every invalidation test constructs its
  stale condition via a hash/version mismatch only.

Additional guards from investigation's Anti-Drift Hazards, reiterated for the implementer:
- Do not name any new class `CacheInvalidationPolicy` (collision with `src/engine/world_index.py`).
- Do not modify `src/engine/world_index.py` or its test file
  `tests/unit/optimization/test_cache_invalidation_policy.py` at all.
- Do not modify `tools/knowledge_search.py` — `manifest.json` is read-only input to
  `_corpus_generation()`, never written by this module.
- Do not store anything beyond `MAY_LIST_COLUMNS` in any of the three tables — no raw prompt
  text, no raw retrieved chunk/source text, no unredacted tool payloads.
- Category name strings must be exactly `retrieval_index_cache`, `retrieval_query_cache`,
  `retrieval_packet_cache` — no invented variants.

## Dependency Map

- Step 1 (skeleton, constants, DB path) is a hard prerequisite for Steps 2-7 — all reference
  `CACHE_DB_PATH`, `MAY_LIST_COLUMNS`, category-name constants, and `_get_connection()`/
  `_init_schema()` defined there.
- Steps 2, 3, and 4 (the three cache levels) are independent of each other — implementable and
  testable in any order once Step 1 lands. Step 3 and Step 4 both call the `_corpus_generation()`
  helper — implement it once in Step 3 (first consumer) and reuse in Step 4, rather than
  duplicating.
- Step 5 (MAY-list guard) depends on Steps 2-4's `write_*_cache()` functions existing, since it
  wraps their insert paths.
- Step 6 (naming/import guards) depends on Steps 1-5 being complete — it is a verification pass
  over the finished module.
- Step 7 (CLI, including `prune`) depends on Steps 2-4's `check_*`/`write_*` functions existing
  to expose via CLI, and on Step 1's `created_at` column/`MAY_LIST_COLUMNS` entry existing for
  `prune` to query against; independent of Step 5/6, could be done in parallel with them.
- Step 8 (parity ledger) depends on the module being functionally complete (Steps 1-6 at
  minimum) since the `v2_evidence` field cites specific line ranges.
- Step 9 (regression verification) is last, depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — Index cache: hit on unchanged hash+version; recompute+evict on either change | Step 1 (schema/constants), Step 2 (logic) | `test_index_cache_hit_on_unchanged_content_hash_and_chunking_version`, `test_index_cache_recompute_on_content_hash_change`, `test_index_cache_recompute_on_chunking_version_change`, `test_index_cache_category_name_is_retrieval_index_cache` |
| AC2 — Query cache: stale-reject on corpus_generation/retrieval_version change, observable reason code | Step 1, Step 3 | `test_query_cache_hit_on_identical_query_filters_and_versions`, `test_query_cache_stale_reject_on_corpus_generation_change`, `test_query_cache_stale_reject_on_retrieval_version_change`, `test_query_cache_miss_reason_code_distinct_from_stale_reject_reason_code`, `test_query_cache_category_name_is_retrieval_query_cache` |
| AC3 — Packet cache: invalidated on cited-hash mismatch or corpus_generation/policy version change | Step 1, Step 4 | `test_packet_cache_hit_when_all_cited_hashes_and_versions_match`, `test_packet_cache_invalidated_on_single_cited_source_hash_mismatch`, `test_packet_cache_invalidated_on_corpus_generation_change`, `test_packet_cache_invalidated_on_policy_version_change`, `test_packet_cache_category_name_is_retrieval_packet_cache` |
| AC4 — Every stored row is MAY-list only, inspectable, no raw text | Step 1 (allowlist constant, including `created_at`), Step 5 (enforcement) | `test_all_three_cache_tables_expose_only_may_list_columns`, `test_no_stored_row_contains_raw_prompt_or_chunk_text`, `test_write_path_rejects_a_prohibited_field_if_offered` |
| Durable State Rule (CLAUDE.md, not a ticket AC — architecture-review-mandated) — every row has a defined lifecycle | Step 1 (`created_at` column), Step 7 (`prune --older-than-days N`) | `test_prune_deletes_rows_older_than_threshold_across_all_three_tables`, `test_prune_leaves_rows_newer_than_threshold_untouched`, `test_prune_is_not_invoked_by_any_check_or_write_function` |

## Anti-Drift Notes

- **Duration values are decorative in the hot path, not behavioral.** The idea doc's
  ~30d/~7d/~14d figures must never appear as a TTL check, clock comparison, or *scheduled*
  eviction trigger inside `check_index_cache`, `check_query_cache`, `check_packet_cache`,
  `write_index_cache`, `write_query_cache`, or `write_packet_cache`. Every hit/miss/stale-reject
  decision in this plan is triggered by a hash/version mismatch at read or write time, never by
  elapsed wall-clock time. The one exception, added in this revision, is Step 7's manual
  `prune --older-than-days N` CLI subcommand — an operator-invoked, non-hot-path deletion pass
  using the `created_at` column, matching Decision C of
  `docs/observability/retrieval_retention_redaction_policy.md` ("caches ARE eligible for
  duration-based expiry... a safety backstop, not the primary invalidation signal"). `prune` is
  not a schedule, has no default threshold, and is never called by any `check_*`/`write_*`
  function — it does not weaken this note's core rule that hash/version mismatch is the *primary*
  invalidation signal for Steps 2-4. A future ticket wiring `prune` into an automatic schedule
  (e.g. a cron-style workflow or CI job) is new scope, not this ticket's.
- **`_corpus_generation()` is read-only against `manifest.json`.** It must never call
  `knowledge_search.py`'s `cmd_build`/`cmd_build_incremental`, never write to `manifest.json`,
  and must degrade gracefully (via the `_NO_MANIFEST` sentinel) rather than raise or fabricate a
  value if the manifest is absent — this keeps the module fully independent of whether an index
  has ever been built, which matters since this ticket's own tests must run without live ML
  dependencies.
- **`ContextPacket` does not exist as a class yet** (`context_packet_contract.md` §4). Step 4's
  packet-cache functions must take raw fields (`packet_key_hash`, `cited_hashes`,
  `corpus_generation`, `policy_version`) as arguments — never import or assume a `ContextPacket`
  class/serializer.
- **The three category-name constants are the load-bearing contract with the retention/redaction
  policy doc** — any test or code path using a differently-spelled or abbreviated category name
  (e.g. `idx_cache`, `query_cache` without the `retrieval_` prefix) is a drift bug, not a valid
  simplification.
- **`write_*_cache()`'s MAY-list rejection behavior (raise vs. drop) must be consistent across
  all three functions** — Step 5 centralizes this in one shared `_validate_may_list_kwargs()`
  helper specifically so the three cache levels cannot silently diverge in this behavior.
- **No P0 parity ledger entries are touched.** `INFRA-295` is `priority: P2`, matching sibling
  entries `INFRA-292`/`293`/`294` — this module has no Mechanics Bible or engine-contract
  relationship to satisfy at a stricter tier.

## Deviations

**Revision 1 (this version) — architecture-review `NEEDS_CHANGES` remediation.**
An `architecture-reviewer` pass on the pre-revision version of this plan returned
`NEEDS_CHANGES`, citing a Durable State Rule (CLAUDE.md) violation: the plan created a new
durable SQLite file with three tables, none of which carried any timestamp/`created_at`/
`last_accessed` column, and whose only CLI surface (Step 7) was read-only introspection
(`stats`/`check-index`/`check-query`/`check-packet`) with no prune/delete/vacuum path. Result: a
row for a query or packet never asked again, or an index-cache row for content that leaves the
corpus, had no path to ever being removed — all three tables would grow strictly monotonically
forever, which is exactly the risk
`docs/observability/retrieval_retention_redaction_policy.md` Decision C anticipates by making
caches (unlike `agent-monitoring/*.jsonl`'s append-only-forever events) explicitly "eligible for
duration-based expiry" as a backstop. The review found the pre-revision plan had over-read the
ticket's Out-of-Scope line (which bars only *tests asserting exact duration-enforcement
precision*) into a blanket ban on any lifecycle mechanism existing in the module at all.

Changes made in this revision, all additive to the pre-revision plan (no other step, Resolved
Decision, or scope guard was rewritten):
- Added a `created_at` column to all three table schemas (Step 2 `retrieval_index_cache_rows`,
  Step 3 `retrieval_query_cache_rows`, Step 4 `retrieval_packet_cache_rows`) and to
  `MAY_LIST_COLUMNS` (Step 1) as an ordinary management column, same class as
  `reason_code`/`cache_status`.
- Amended Step 7 to add a manual, non-hot-path `prune --older-than-days N` CLI subcommand that
  deletes rows past an operator-supplied age threshold across all three tables, with three new
  dedicated tests. Confirmed non-hot-path: no `check_*_cache`/`write_*_cache` function reads
  `created_at` or calls `prune`.
- Added Resolved Decision 5 documenting the fix and citing Decision C as the reason a lifecycle
  mechanism is required — and drawing the line between "tests must not assert exact
  duration-enforcement precision" (still true, unchanged — no test mocks a clock or asserts
  elapsed-day behavior against the primary hash/version-mismatch invalidation path) versus "the
  module must have some prune mechanism at all" (the actual gap, now fixed).
- Updated the Summary, the AC map (added a non-ticket-AC row for the Durable State Rule
  requirement, satisfied by Step 1 + Step 7), Step 8's parity-ledger `v2_evidence` description,
  and the Anti-Drift Notes' duration-values note to reconcile with `prune`'s existence.
- No change to Resolved Decisions 1-4, to Steps 2-4's hit/miss/stale-reject logic or their
  existing tests, to the Scope Guards list (left verbatim), or to any ticket-AC1-3 mapping.
