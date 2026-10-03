---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL
artifact_type: investigation
tags: [agent-monitoring, mcp]
---

# Investigation — TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL

Re-verified against the current worktree on 2026-09-10 (`.claude/worktrees/doc-tag-enforcement`,
based on `origin/main`). `mcp__knowledge-search__search_docs` (two queries) and `graphify query
"retrieval_cache access log"` were run first, per the Context Scan rule, before any grep/Read.

## Current Behavior

### `tools/retrieval_cache.py` — the six dead functions and their chain

All six line numbers the ticket cites are still exactly correct today (no drift):

- `check_provider_result_cache()` — :989-1034. Signature: `(query_hash, repo_branch_scope, *,
  normalized_intent, filters_json, budget_class, routing_policy_version) ->
  ProviderResultCacheLookup`.
- `write_provider_result_cache()` — :1049-1093. 18 keyword-only params. Calls `log_cache_access(
  "level1_provider_result", "write", ...)` at :1091-1093.
- `record_provider_result_cache_hit()` — :1096-1114. `(query_hash, repo_branch_scope) -> None`.
  Calls `log_cache_access(..., "hit", ...)` at :1112-1114.
- `check_context_packet_cache()` — :1181-1226. `(query_key_hash, *, normalized_intent,
  entity_ids_json, repository_id, branch, budget_tokens) -> ContextPacketCacheLookup`.
- `write_context_packet_cache()` — :1246-1315. 29 keyword-only params. Calls `log_cache_access(
  "level2_context_packet", "write", packet_id=packet_id)` at :1315.
- `record_context_packet_cache_hit()` — :1318-1336 (2-line drift from the ticket's :1320 — trivial).
  Calls `log_cache_access(..., "hit", ...)` at :1336.

`log_cache_access()` itself: :640-697. `read_cache_access_log()`: :700-722 (returns `[]`, never
raises, if the table doesn't exist — mirrors `provider_result_cache_stats()`'s own contract).
`_get_access_log_connection()` (:627-637) is the only caller of `migration_001_add_level1_tables()`
+ `migration_005_add_cache_access_log_table()` together, and is itself called only from
`log_cache_access()`.

**Zero production callers confirmed by whole-repo grep** (not just `tools/`) for all six functions
plus `log_cache_access`/`read_cache_access_log`: every non-docstring, non-comment reference outside
`tools/retrieval_cache.py` itself is in `tests/tools/test_retrieval_cache.py` or
`tests/tools/test_evidence_cache_identity_contract.py`, except `read_cache_access_log`, which has
exactly the two live readers the ticket names.

**A broader orphaned surface than the ticket's named six** (see Risks/Open Questions — this is a
finding for Plan, not a scope decision made here): `provider_result_cache_stats()` (:1117-1139),
`context_packet_cache_stats()` (:1339-1373), `migration_002_add_level2_tables()` (:326-380),
`migration_003_add_redaction_policy_version_column()` (:383-401), `migration_004_add_level2_
write_path_columns()` (:404-443), `_get_level1_connection()` (:1037-1046), `_get_level2_
connection()` (:1229-1243), `_ensure_level1_schema_for_read()` (:978-986), `_ensure_level2_schema_
for_read()` (:1157-1178), and the `ProviderResultCacheLookup`/`ContextPacketCacheLookup` dataclasses
all also have **zero production callers today** outside each other and the six named dead
functions — their only documented caller, `tools/knowledge_gateway_mcp.py`, no longer exists
(deleted by `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`). `read_current_run_sidecar()` (:557-626)
similarly has exactly one production caller, `log_cache_access()`.

### `migration_001` → `migration_005` dependency — CONFIRMED REAL, not just asserted

`migration_001_add_level1_tables()` (:271-323) is the only function that creates
`retrieval_cache_generation` (`CREATE TABLE IF NOT EXISTS retrieval_cache_generation` at
:280-286). `migration_005_add_cache_access_log_table()` (:445-506) does **not** create that table
itself — it only creates `retrieval_cache_access_log` (:479-499), then unconditionally runs
`DELETE FROM retrieval_cache_generation` (:500) and `INSERT INTO retrieval_cache_generation ...`
(:501-505). Run migration_005 on a connection that never had migration_001 applied and the `DELETE
FROM`/`INSERT INTO` against a nonexistent table raises `sqlite3.OperationalError`. This is not
inference — `_get_access_log_connection()`'s own docstring (:628-633) says so explicitly ("Runs
migration_001 first ... a prerequisite migration_005 assumes exists"), and
`TestMigration005CacheAccessLog` (test file, see below) never once calls `migration_005` without
first calling `migration_001` in the same test. **The ticket's Out-of-Scope claim is real and
correctly directs retention of `migration_001`.**

### Retro machinery — `tools/agent-monitoring/generate_retro.py`

- `KGMCP_REFETCH_WINDOW_SECONDS = 300` — :703.
- `_kgmcp_access_log_group_key()` — :706-709.
- `_kgmcp_verdict()` — :712-800.
- `compute_kgmcp_cache_efficiency_metrics()` — :803-1011 (ticket said `:803-1015`; `1015` is
  actually the start of the next function, `compute_retro_metrics`, at :1014 — 4-line drift).
- Wired into `compute_retro_metrics()`'s returned dict at :1299-1301 (`"kgmcp_cache_efficiency":
  compute_kgmcp_cache_efficiency_metrics(kgmcp_access_log or [], tools=tools or [],
  all_tools=all_tools)`) — confirmed this is the **only** wiring point; no other caller of
  `compute_kgmcp_cache_efficiency_metrics` exists in production code (grep confirmed; the only
  other hits are 3 in `tests/tools/test_retrieval_cache.py` and the model-docstring cross-reference
  in `src/api/agent_ops_dashboard/models.py:222-223`).
- The `## KGMCP Cache Efficiency` Markdown render block is **:2121-2214**, not `:2121-2148` as the
  ticket states — :2121-2148 is only the opening (heading + verdict callout); the block continues
  through the summary table, `### Per-Ticket`, `### Per-Agent`, `### Repeated Refetches`,
  `### Dead Writes` subsections and the derivation footer, ending right before the unrelated `##
  Skill Usage` heading at :2216. This is a real, material line-range correction Plan should use,
  not the ticket's own approximate figure.
- `generate()` (:1565-…) takes `kgmcp_access_log=None` as a keyword param (:1567), reads it back
  out of `metrics["kgmcp_cache_efficiency"]` into local `kce` at :1607, and only that render block
  consumes `kce`.
- `main()` (:2267-…) calls `read_cache_access_log()` once at :2278 (`all_kgmcp_access_log`, never
  period-sliced — see :2276-2277's comment) and passes it into `generate()` at :2305-2308.
- **No other caller of `compute_kgmcp_cache_efficiency_metrics` exists besides the one wiring point
  at :1299** — confirmed by grep. The only production consumer of the computed dict downstream of
  that wiring point is `src/api/agent_ops_dashboard/ingest.py` (see below).

### `src/api/agent_ops_dashboard/ingest.py` — the critical part

This is materially bigger and more cross-stack than the ticket's framing ("resolve ingest.py:44's
use of `read_cache_access_log`") suggests. The real coupling:

- Import at :44 (`from retrieval_cache import read_cache_access_log`), plus 5 `Kgmcp*` model
  imports at :66-70 (`KgmcpCacheEfficiencyStats`, `KgmcpCacheTicketStats`, `KgmcpCoverageStats`,
  `KgmcpDeadWriteEntry`, `KgmcpRepeatedRefetchEntry`, from `src/api/agent_ops_dashboard/models.py`).
- `DashboardCache.get_agent_monitoring_stats()` (:826-963) calls `compute_retro_metrics(...,
  kgmcp_access_log=read_cache_access_log())` at :874-880 — i.e. it doesn't just read the log, it
  **reuses the exact same `compute_retro_metrics()`/`compute_kgmcp_cache_efficiency_metrics()`
  pipeline the CLI retro uses** (by design — `TCK-20260718-RETRO-STATS-REFACTOR`'s whole point was
  "CLI Markdown report and JSON API always report identical numbers," and :1602-1605's own comment
  in `generate_retro.py` says so explicitly). It then unpacks `metrics["kgmcp_cache_efficiency"]`
  into a `KgmcpCacheEfficiencyStats` Pydantic object at :931-962, field-for-field.
- `kgmcp_cache_efficiency: KgmcpCacheEfficiencyStats` is a **required** (non-`Optional`) field of
  `AgentMonitoringStats` (`models.py:290`), itself built from 5 more required model classes
  (`models.py:228-272`).
- **This is a real, currently-reachable HTTP endpoint**: `src/api/agent_ops_dashboard/main.py:103-
  109` registers `GET /api/stats/agent-monitoring` (`response_model=AgentMonitoringStats`) on a
  standalone FastAPI app (`main.py:1-8` — explicitly "not mounted on `src/api/server.py` (the main
  simulation API) — a separate product/port"). A real client calling it today gets a **genuinely
  computed, non-trivial block** — not silently all-zero. Since `retrieval_cache_access_log` is
  already permanently empty (its only writer chain is the dead KGMCP gateway), `total_hits`/
  `total_writes`/`dead_write_count`/`repeated_refetches` are 0, but `coverage.search_calls_total`
  is computed from real `tools.jsonl` search/graphify call counts (nonzero in any real corpus), so
  `verdict` genuinely resolves to `"NOT IN USE"` with a real, non-fabricated explanation string
  (per `_kgmcp_verdict()`'s own logic at :736-745) — a real, currently-true, currently-negative
  finding, not a placeholder.
- **The dashboard frontend is NOT dead on this data** — it is a real, wired, tested UI section, not
  an orphaned type. `dashboard-frontend/src/api.ts:230-292` mirrors all 5 `Kgmcp*` TypeScript
  interfaces plus the required `kgmcp_cache_efficiency` field on the stats response type.
  `dashboard-frontend/src/views/StatsView.tsx:515-601` renders a full "KGMCP cache efficiency"
  section: a color-coded verdict callout (`data-testid="kgmcp-verdict"`), 6 `StatTile`s (hits,
  writes, reuse rate, dead writes, repeated refetches, coverage), and conditional per-ticket/
  per-agent tables (`data-testid="kgmcp-per-ticket-table"`/`"kgmcp-per-agent-table"`).
  `dashboard-frontend/src/test/StatsView.test.tsx` has 14 `kgmcp`-referencing lines exercising this
  section; `dashboard-frontend/src/test/App.test.tsx:86` builds a `kgmcp_cache_efficiency` fixture
  object (required for the mocked response to type-check).
- **Two docs not listed in the ticket's "Related Docs" also fully document this field/section** and
  will need updating regardless of which resolution Plan picks: `docs/observability/agent_ops_
  dashboard_contract.md` (field-for-field API contract at :73,82,89-91,180,188, plus UI-section
  description at :312,317,320-323) and `docs/guides/agent_ops_dashboard.md` (:130,140, cross-
  referencing the contract doc). See "Docs Requiring Update" below.
- **No other consumer of `GET /api/stats/agent-monitoring` exists in the repo** besides
  `dashboard-frontend`. Grepped every `.py`/`.ts`/`.tsx`/`.md` for the literal route path; the only
  hits are the route/ingest/frontend files themselves, their own tests, and historical
  tickets/stored-artifacts prose. This bounds the real breaking-change blast radius of any full-
  removal option to this one in-repo frontend, updated in the same change.

### Cascading "no reader remains" question

The ticket's own Scope text says remove `log_cache_access`/`read_cache_access_log` "once no reader
remains." `read_cache_access_log` currently has exactly 2 readers (`generate_retro.py:main()` and
`ingest.py:get_agent_monitoring_stats()`). The retro side is unconditionally being removed by this
ticket's own Scope item 2. So "no reader remains" becomes true **iff** Plan's resolution for
`ingest.py` also stops calling `read_cache_access_log()` — which is only automatically true under
Option A/C below (see Risks/Open Questions), not under Option B (a stub that still needs a data
source, though it could hardcode instead of calling the real function).

## Mechanics / Engine Constraints

None. This ticket touches only `tools/`, `src/api/agent_ops_dashboard/`, `dashboard-frontend/`, and
`docs/parity_ledger/` — no `docs/mechanics/` chapter or `docs/engine/` contract governs agent-
monitoring tooling or the dashboard API. The Mechanics Bible / Engine Contracts / Authoritative
Mechanics Rule do not apply here.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: INFRA-343's `test_path` cites
  `tests/tools/test_retrieval_cache.py::TestProviderResultCache,...::TestMigration003,...::
  TestProviderResultCacheStats` — all three classes are in this ticket's own deletion scope (see
  Test Plan), so this citation goes stale the moment they're deleted. Must be updated via
  `tools/parity_ledger_writer.py`, per ticket Scope and CLAUDE.md's raw-YAML-edit prohibition.
- `docs/observability/agent_ops_dashboard_contract.md`: documents `kgmcp_cache_efficiency:
  KgmcpCacheEfficiencyStats` as a field-for-field API contract (:73,82,89-91) and the "KGMCP cache
  efficiency" UI subsection (:312,317,320-323). Whichever of the src/api/ options Plan picks
  (removal, stub, or Optional-and-null), this contract text becomes wrong as written and must
  change to match.
- `docs/guides/agent_ops_dashboard.md`: cross-references the contract doc's `kgmcp_cache_efficiency`
  field at :130,140 as part of the dashboard's documented Stats tab feature set — same reasoning as
  above, must be updated in step with whichever option Plan picks.

The `docs/parity_ledger/infrastructure.yaml` entries **INFRA-346** (`status: verified`, P1,
`test_path: tests/tools/test_retrieval_cache.py::TestLevel2Migrations`) and **INFRA-390**
(`status: verified`, P2, `test_path: ...::TestReadCurrentRunSidecar::test_scoped_sidecar_wins_over_
stale_unscoped_when_both_exist`) are NOT written here as required-update bullets, because whether
they need updating depends on an as-yet-undecided scope question (see Risks/Open Questions —
whether `migration_002`/`read_current_run_sidecar()` are removed alongside the six named functions
is not resolved by this investigation). If Plan decides to expand removal scope to cover the
broader orphaned surface, these two entries' `test_path` citations will go stale in exactly the
same way INFRA-343's does, and should be added as Format 1 bullets at that point — flagged here so
Plan doesn't miss them, not required by this document itself since the underlying condition isn't
yet decided.

`tests/tools/test_generate_retro.py`'s golden-fixture test,
`test_compute_retro_metrics_output_unchanged_pre_and_post_migration_on_fixed_corpus` (cited as
**INFRA-379**'s `test_path`, `status: verified`, P2), will need its `_FIXED_CORPUS_EXPECTED_REPORT`
golden string updated once the `## KGMCP Cache Efficiency` render block is removed (the golden text
currently includes that section verbatim) — this is a required code/fixture change (see Test Plan),
but INFRA-379's own `test_path` doesn't change (same test file/name), so no parity-ledger doc edit
is needed for INFRA-379 itself, only the test fixture.

The `docs/agent-monitoring/schema.md` doc (path: `docs/agent-monitoring/schema.md`, under
`docs/agent-monitoring/`) is not required to change for this ticket: its `retrieval_version`/
`cache_level`/`cache_status` field docs (:310-327) document the separate, unrelated general 3-level
retrieval cache (`index`/`query`/`packet` — `docs/observability/retrieval_retention_redaction_
policy.md`'s cache design), not the Level 1/Level 2 provider-result/context-packet KGMCP chain this
ticket removes. Confirmed by reading the actual field table: `cache_level` there is documented as
`index | query | packet`, never `level1_provider_result | level2_context_packet`.

The `docs/guides/agent_monitoring.md` doc (path: `docs/guides/agent_monitoring.md`) is also not
required to change for this ticket, for a related but distinct reason: its `## Report Sections`
table (:55-76) is a maintained enumeration of every retro section — but it **already has no row for
"KGMCP Cache Efficiency"** today, a pre-existing documentation gap that predates this ticket (the
section has rendered since `TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-
DASHBOARD` without ever being added to this table). Since there is no existing row to remove,
deleting the render block requires no edit here. Worth a doc-updater aside if convenient, but not a
gap this ticket's removal work creates or is responsible for fixing.

## Parity Ledger Overlap

- **INFRA-343** (`status: unsupported`, P1) — ticket's own named target. Confirmed current text
  exactly: `test_path: tests/tools/test_retrieval_cache.py::TestProviderResultCache,tests/tools/
  test_retrieval_cache.py::TestMigration003,tests/tools/test_retrieval_cache.py::
  TestProviderResultCacheStats`. All three classes are deleted by this ticket's own Scope — must be
  updated via `tools/parity_ledger_writer.py` in the same session, per ticket Scope item.
- **INFRA-341** (`status: verified`, P1) — checked and ruled out: its cited test,
  `TestCrashRecovery::test_deleted_cache_db_rebuild_does_not_silently_resurrect_level1_payload_
  rows` (:566-…), calls `migration_001_add_level1_tables()` directly via a raw `conn.execute()`
  INSERT — it never calls any of the six dead functions. `migration_001` is explicitly retained.
  No update needed.
- **INFRA-346** (`status: verified`, P1) — test_path cites only `TestLevel2Migrations`
  (tests `migration_002_add_level2_tables`). Not touched by this investigation's confirmed dead-
  code scope, but see the cascading-scope open question above — conditionally at risk.
- **INFRA-349** (`status: unsupported`, P1, `test_path: null`) — already carries no live-evidence
  claim; unaffected either way.
- **INFRA-379** (`status: verified`, P2) — its cited test's golden fixture needs a content update
  (not a parity-ledger doc update) once the retro render block is removed. See Docs Requiring
  Update above and Test Plan below.
- **INFRA-390** (`status: verified`, P2) — test_path cites `TestReadCurrentRunSidecar::
  test_scoped_sidecar_wins_over_stale_unscoped_when_both_exist`, which tests
  `read_current_run_sidecar()` directly (not through `log_cache_access()`). Conditionally at risk
  under the same cascading-scope open question — flagged, not resolved here.

No other `docs/parity_ledger/*.yaml` file (checked `substrate.yaml`, `combat_movement.yaml`,
`strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`, `social_narrative.yaml`,
`world_dynamics.yaml` are all unrelated subsystems by name) overlaps this ticket's scope —
`infrastructure.yaml` is the sole relevant file.

## Prior Work

- `TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD` (done) — built the
  entire chain this ticket retires: `log_cache_access`/`read_cache_access_log`, the retro's KGMCP
  Cache Efficiency machinery, and the `ingest.py`/`models.py`/`StatsView.tsx` API+UI surface.
- `TCK-20260824-RETRO-METRIC-CAVEATS` — added the "architectural, not fixable" coverage-rate
  disclosure text still present in `_kgmcp_verdict()`'s docstring and the render block's caveat
  paragraph (:2139-2145) — this disclosure becomes moot once the section is removed, not something
  to "fix" further.
- `TCK-20260826-KGMCP-CACHE-TICKET-ATTRIBUTION` / `TCK-20260826-KGMCP-COVERAGE-RATE-OVERFLOW` —
  iterative bug fixes on this same metric, both now moot for the same reason.
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` / `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` — the root
  cause: deleted the gateway and its cache orchestrator, orphaning everything this ticket now
  removes. `TCK-20260908`'s own `stored_artifacts` corrected INFRA-343 on PR #152 with the precise
  reasoning this investigation re-confirms is now stale again.
- `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS` (done, sibling) — resolved a related but
  separate orphaned-tooling gap (the `kgmcp_phase*_runner.py` measurement scripts), explicitly
  out of scope here per this ticket's own Out of Scope section.

## Risks and Open Questions

**1. The `src/api/agent_ops_dashboard/ingest.py` resolution — the real options, laid out for Plan.**

This is the one genuine design decision in this ticket (per the ticket's own framing) and the
investigation above shows it is bigger than a single import line: it's a required Pydantic field on
a live HTTP endpoint, consumed end-to-end by a tested React component. Three realistic options:

- **Option A — Full removal across the whole stack.** Delete `KgmcpCacheEfficiencyStats` and its 4
  sibling model classes from `models.py`; drop the `kgmcp_cache_efficiency` field from
  `AgentMonitoringStats`; remove `ingest.py`'s `read_cache_access_log` import and the
  `kgmcp_access_log=`/`KgmcpCacheEfficiencyStats(...)` construction; remove the 5 `Kgmcp*`
  interfaces and the `kgmcp_cache_efficiency` field from `dashboard-frontend/src/api.ts`; remove the
  rendered section (:515-601) from `StatsView.tsx`; update `StatsView.test.tsx` (14 refs) and
  `App.test.tsx`'s fixture (:86); update both dashboard docs.
  *What breaks:* any external client of `GET /api/stats/agent-monitoring` that currently depends on
  `kgmcp_cache_efficiency` being present — none found in this repo, but the endpoint has no
  versioning/deprecation window, so this is a real, un-softened breaking schema change for anyone
  outside this repo.
  *What doesn't break:* nothing else — `compute_retro_metrics()`'s other keys, the rest of
  `AgentMonitoringStats`, and the rest of the dashboard are untouched.
  *Consistency:* matches the retro/CLI side exactly (full section removal, not a stub) — both
  consumers of `compute_retro_metrics()` end up in the same "this measurement no longer exists"
  state, honoring the ticket's own framing that "both sides resolve together."

- **Option B — Keep the endpoint/field, always return a fixed "feature retired" stub.** Keep every
  model class and the field, but hardcode a static `KgmcpCacheEfficiencyStats(total_hits=0,
  total_writes=0, ..., verdict="RETIRED", verdict_explanation="<reason>", ...)` in `ingest.py`
  instead of calling `read_cache_access_log()`/`compute_retro_metrics(kgmcp_access_log=...)`, and
  leave `StatsView.tsx` rendering it (showing a permanent "RETIRED" verdict banner).
  *What breaks:* nothing externally — schema is preserved byte-for-byte.
  *What doesn't break:* nothing.
  *Cost:* leaves a permanent, hand-maintained, always-fake-looking-but-actually-static block in
  production API code and UI — the CLAUDE.md hard rule against "hidden or implicit durable
  behavior" doesn't literally forbid an explicit, documented stub, but it is still permanent
  placeholder logic future readers must remember is fake, and it's the one option that leaves the
  retro (CLI) and the dashboard (API/UI) in genuinely different end states for the same underlying
  "this measurement is retired" fact — arguably worse for long-term clarity than either removing it
  everywhere or leaving it real everywhere.

- **Option C — Make the field `Optional[...] = None`, stop computing it, render conditionally.**
  Keep the model classes but make `kgmcp_cache_efficiency: Optional[KgmcpCacheEfficiencyStats] =
  None` on `AgentMonitoringStats`; `ingest.py` passes `None`/omits `kgmcp_access_log`; `compute_
  retro_metrics()` either drops the key when not supplied or the caller ignores it; `StatsView.tsx`
  wraps the whole section in a null-check and simply doesn't render it.
  *What breaks:* any strict external consumer that assumes the field is always present and non-null
  (weaker break than Option A, since the field still type-checks as present-but-nullable).
  *What doesn't break:* nothing else.
  *Cost:* nearly the same footprint as Option A (every layer still needs touching: model, ingest.py,
  frontend interface + conditional render, both test files, both docs) but leaves a permanent
  always-null field forever, which is its own small tax and doesn't fully match "both sides resolve
  together" if the retro CLI drops the section outright while the API/UI keep a vestigial null
  field around.

**My own read, as a recommendation only (not a decision):** Option A is the more defensible choice.
The real external blast radius is low (zero non-repo consumers found), it matches exactly what this
same ticket already does on the CLI/retro side (outright removal, not a stub or a nullable
placeholder), and it avoids the two forms of permanent-fake-value cost that Options B and C both
carry to different degrees. Plan should weigh this against the ticket's own instruction to route
this specific decision through Architecture-Review before implementing, since it is the one part of
this ticket touching production API surface and a breaking-schema-change judgment call is exactly
the kind of thing that review exists to catch.

**2. The broader orphaned-surface question (see Current Behavior above).** The ticket names exactly
six functions as "dead." This investigation found a larger family of functions/dataclasses/migration
steps (`provider_result_cache_stats`, `context_packet_cache_stats`, `migration_002/003/004`, both
`_get_level{1,2}_connection`/`_ensure_level{1,2}_schema_for_read` helper pairs, both `*Lookup`
dataclasses, and `read_current_run_sidecar()`) that also have zero production callers today, purely
as a consequence of the six named functions and `log_cache_access` being their only real-world
callers. The ticket's Scope list doesn't mention any of them, and its Out-of-Scope section
explicitly protects only `migration_001`. Whether that silence is intentional (leave this
infrastructure standing, e.g. as forward-compatible schema code in case Level 1/2 caching returns)
or an oversight this ticket should also sweep is a real open question for Plan — flagged, not
decided here, since deciding it changes the diff footprint materially (it would touch `TestLevel2
Migrations`, `TestMigration004`, and potentially INFRA-346/INFRA-390 as noted above).

**3. `migration_005`'s own fate is likewise not fully resolved by the ticket's literal text.** The
ticket's Out-of-Scope reasoning for retaining `migration_001` is explicitly grounded in "`migration_
005` assumes [`retrieval_cache_generation`] exists" — which only makes sense as a forward-looking
concern if `migration_005` itself is *also* retained as code (not deleted alongside `log_cache_
access`/`read_cache_access_log`). The Acceptance Criteria's explicit requirement that "`migration_
005` still works — proven by a test" reinforces that both `migration_001` and `migration_005` are
meant to survive as pure, standalone, still-tested schema functions, even though after this ticket
neither will have any production caller left (their only production path today is `log_cache_
access()` → `_get_access_log_connection()` → `migration_001` then `migration_005`, and `log_cache_
access` is being removed). This reading is consistent with treating SQLite migrations as an
append-only historical record that's never retroactively deleted even once its consuming feature is
gone — but it is still worth Plan stating explicitly, since it's a second (smaller) instance of the
same "deliberately-retained code with zero live callers" pattern as `migration_001` itself.

## Anti-Drift Hazards

- **Don't let "remove the dead cache functions" silently expand into "also fix/refactor the general
  3-level retrieval cache"** — `check_index_cache`/`check_query_cache`/`check_packet_cache` and
  their `write_*`/`Result` dataclasses (the *original*, non-KGMCP 3-level cache from
  `TCK-20260729-RETRIEVAL-CACHE-LEVELS`) are live, unrelated, and explicitly out of scope. They
  share this file and loosely similar naming (`check_*_cache`/`write_*_cache`) with the dead KGMCP
  functions — easy to grep-and-delete the wrong set if not careful about the Level 1/Level 2 vs.
  index/query/packet distinction.
- **Don't touch `docs/agent-monitoring/schema.md`'s `retrieval_version`/`cache_level`/`cache_status`
  field docs** — confirmed above to document the unrelated general cache, not this ticket's dead
  chain, despite superficially similar terminology.
- **Don't delete `docs/engine/contracts/knowledge_gateway_mcp/`** — explicitly retained per the
  ticket's own Out of Scope, and a live test (`test_evidence_cache_identity_contract.py:30-33`)
  reads 4 files there. Don't let "clean up everything KGMCP-named" sweep this in.
- **Don't silently rewrite `_FIXED_CORPUS_EXPECTED_REPORT`'s golden text by hand-editing whatever
  diff `pytest` shows** — regenerate it deliberately from a real `generate()` call after the render
  block is removed and review the diff, since this is the one place a subtle rendering bug (e.g. an
  extra blank line left behind at the render-block boundary, given the block's real end is :2214,
  not the ticket's approximate :2148) would silently pass if the "expected" value were copied
  uncritically from a buggy actual output.
- **Don't resolve the `ingest.py` design question by unilaterally picking Option A/B/C and skipping
  Architecture-Review** — the ticket's own Assumptions/Open Questions section requires this
  specific decision to go through review before implementing; this is the one part of the ticket
  where "just delete it, tests will catch problems" is not sufficient given the live HTTP endpoint
  and required (non-Optional) schema field involved.
