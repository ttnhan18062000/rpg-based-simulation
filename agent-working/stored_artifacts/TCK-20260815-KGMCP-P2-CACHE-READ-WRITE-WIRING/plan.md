---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING
artifact_type: plan
tags: [ai, mcp, security]
---

# Implementation Plan — TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING

## Framing note (security tag)

The `security` tag was added to this ticket's frontmatter after Investigate returned, specifically
because this is the ticket that makes the redaction/secret-scan write-path (built pure/unwired by
`TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`) reachable from a real, running MCP tool call for the
first time — i.e. the ticket that makes payload caching "go live" in
`redaction_retention_policy.md` §4/§11's own words. Security-Review will run after Implement, on the
real diff, per the `security` tag's routing. This plan treats Security-Review as the operative
"security-focused pass" §4/§11 requires (see DD5) — not as an optional formality — and flags exactly
what Security-Review must rule on before this ticket can close.

## Summary

Add one new orchestration module, `tools/knowledge_gateway_cache.py`, that computes the
`evidence_cache_identity_contract.md` §1 lookup identity and §2 evidence-validity identity as two
genuinely separate steps, checks §5/§12.3 branch/working-tree compatibility, and drives the redaction
write-path (`knowledge_gateway_redaction.evaluate_write_candidate()`) on a miss. The actual SQL
(`SELECT`/`INSERT OR REPLACE`/`UPDATE`) against the new `retrieval_provider_result_cache_rows` table
lives in `tools/retrieval_cache.py` itself, as three new functions
(`check_provider_result_cache`, `write_provider_result_cache`,
`record_provider_result_cache_hit`) plus one read-only aggregator
(`provider_result_cache_stats`), following the exact shape of the module's existing three
check/write pairs. `tools/knowledge_gateway_mcp.py::_run_knowledge_context()` gains exactly two new
call-outs (cache-check before `route()`, cache-write before the final response-schema validation) and
`_run_knowledge_status()` gains real cache-domain fields. Two genuine schema/cross-module judgment
calls this ticket's investigation flagged as blocking (`redaction_policy_version` persistence, WAL
mode going live on the real cache file) are resolved below with reasoning (DD3, DD4) and explicitly
flagged for Architecture Review confirmation before Implement proceeds, mirroring the sibling
ticket's own DD2 precedent.

## Design Decisions

### DD1 — Hook placement and new module: confirmed as investigation resolved it

Investigation's own resolution (`staging_artifacts/.../investigation.md:44-63`) is adopted as-is: a
new sibling module `tools/knowledge_gateway_cache.py`, loaded via the same `importlib.util`
sibling-loading idiom `_load_router_module()`/`_load_packet_assembly_module()`/`_load_search_mcp_module()`
already use 3× in `tools/knowledge_gateway_mcp.py` (`tools/knowledge_gateway_mcp.py:96-125`, read
directly). `_run_knowledge_context()` gains exactly 2 new call-outs: after request validation and
before `_kgr.route(query)` (currently `tools/knowledge_gateway_mcp.py:178-183`), and after the
`response` dict is fully built and before `RESPONSE_VALIDATOR.validate(response)`
(currently `tools/knowledge_gateway_mcp.py:286`). No restructuring of steps 3–6 of the existing flow.

### DD2 — SQL layer stays in `tools/retrieval_cache.py`; orchestration lives in the new module

Investigation's own text is self-tensioned on this point: it says the new module's "natural home"
for `check_provider_result_cache()`/`write_provider_result_cache()` is `tools/retrieval_cache.py`
(`investigation.md:88-97`), but also describes the new module as owning "the redaction-orchestrated
real write ... + a real INSERT" (`investigation.md:51-52`). This plan resolves the tension by
splitting responsibility along the same line every other pair in `tools/retrieval_cache.py` already
draws: the literal `SELECT`/`INSERT OR REPLACE`/`UPDATE` SQL text lives in `tools/retrieval_cache.py`
(read directly: `check_index_cache`/`write_index_cache` at `tools/retrieval_cache.py:300-349`,
`check_query_cache`/`write_query_cache` at `:362-418`, `check_packet_cache`/`write_packet_cache` at
`:431-488` — every existing pair follows this shape, and `LEVEL1_CACHE_COLUMNS`'s own docstring at
`tools/retrieval_cache.py:97-103` already anticipates "the later read-write-wiring ticket" adding
functions here). `tools/knowledge_gateway_cache.py` orchestrates: it calls
`retrieval_cache.check_provider_result_cache()` for the lookup, its own functions for
evidence-validity/branch-scope revalidation, `knowledge_gateway_redaction.evaluate_write_candidate()`
for the write decision, and `retrieval_cache.write_provider_result_cache()` to execute the real
`INSERT` on `ALLOW` — "the redaction-orchestrated real write" investigation describes is this
orchestration, not a literal `INSERT` statement living in the new module. This keeps
`tools/retrieval_cache.py` as the repo's sole SQL layer for this table (no new SQL text duplicated
elsewhere) and keeps `tools/knowledge_gateway_cache.py` a pure business-logic layer, consistent with
`tools/knowledge_gateway_redaction.py`'s own "pure functions only" framing.

**Import direction check:** `tools/retrieval_cache.py`'s new functions (Step 3) import
`tools/knowledge_gateway_redaction.py` (for `open_connection_with_limits`, see DD4) — a
one-directional dependency. `tools/knowledge_gateway_redaction.py` itself imports nothing from
`tools/retrieval_cache.py` (confirmed by direct read, `tools/knowledge_gateway_redaction.py:1-42`
lists only `hashlib`, `re`, `sqlite3`, `threading`, `dataclasses`, `pathlib` as imports) — no import
cycle is created.

### DD3 — `redaction_policy_version` persistence: DECISION is option (b), flagged for Architecture Review confirmation

**Decision: add `migration_003_add_redaction_policy_version_column(conn)`.** Unlike the sibling
ticket (which performed no real writes and could defer honestly), this ticket is the one and only
ticket that performs real `INSERT`s into `retrieval_provider_result_cache_rows`. Under option (a)
(drop the value at the write boundary), every real cache row this ticket — or any future ticket —
ever writes would permanently lack the provenance `redaction_retention_policy.md` §6 itself says the
column exists to provide ("a row can be identified as having been written under a specific version
of this policy's rules," `redaction_retention_policy.md:107`). That is not a deferral at this point,
it is a permanent gap, since no later ticket has a natural reason to revisit already-written rows.
Option (b) is a small, mechanically safe addition: `LEVEL1_CACHE_COLUMNS`
(`tools/retrieval_cache.py:104-128`, read directly, exactly 21 columns, confirmed no
`redaction_policy_version` entry) gains a 22nd entry, and one new migration function performs the
`ALTER TABLE`.

**Ordinal:** `migration_003`, never `migration_002` — `cache_migration_plan.md:92-94` (read directly)
reserves `migration_002_add_level2_tables` by name for Level 2 tables, and
`TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS`'s own Anti-Drift Notes (cited in this ticket's
investigation, `investigation.md:387-389`) forbid touching that name "in any form, empty stub
included." `cache_migration_plan.md:111-115` (read directly) explicitly anticipates this exact case:
*"If a future ticket needs to widen an existing populated table's shape, that migration must be
designed separately at that time"* — this is that separately-designed migration.

**Idempotency:** SQLite has no `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. `migration_003` must
check `PRAGMA table_info(retrieval_provider_result_cache_rows)` for the column's presence before
altering (see Step 4).

**Flagged for Architecture Review confirmation, not silently decided** — mirroring
`stored_artifacts/TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH/plan.md`'s own DD2 pattern exactly
(`stored_artifacts/.../plan.md:91-96`: "flagged for Architecture Review confirmation... if Review
disagrees, the fallback is Step 7 gaining a `migration_003_add_redaction_policy_version_column`
addition"). If Review disagrees and prefers option (a) instead, Step 4 below is dropped entirely,
`WriteDecision.redaction_policy_version` is simply never passed to
`write_provider_result_cache()`, and `LEVEL1_CACHE_COLUMNS` stays at 21 columns — a strictly smaller
change than this plan currently scopes, requiring no plan revision beyond removing Step 4 and its
dependents.

### DD4 — WAL mode on the real `CACHE_DB_PATH`: DECISION is acceptable, deliberate, and documented

**Decision: yes**, `tools/retrieval_cache.py`'s new Level 1 functions (`check_provider_result_cache`,
`write_provider_result_cache`, `record_provider_result_cache_hit`) open their connection via
`knowledge_gateway_redaction.open_connection_with_limits(CACHE_DB_PATH)` (§9 helper,
`tools/knowledge_gateway_redaction.py:269-285`) rather than the existing `_get_connection()`
(`tools/retrieval_cache.py:135-144`). This is a deliberate choice, not inherited silently:

- **Enumeration of every other opener of the same file** (`CACHE_DB_PATH = Path("knowledge-index/retrieval_cache.db")`,
  `tools/retrieval_cache.py:59`): `_get_connection()` is the sole existing opener, called from 8
  sites — `check_index_cache`, `write_index_cache`, `check_query_cache`, `write_query_cache`,
  `check_packet_cache`, `write_packet_cache`, `prune`, `cmd_stats` (confirmed by direct read of the
  full file). None of these 8 sets `PRAGMA journal_mode=WAL` today. `PRAGMA journal_mode=WAL` is a
  database-file-level setting, persisted in the file header — once this ticket's new functions open
  the real file with WAL enabled, every one of those 8 existing call sites observes WAL mode on their
  next connection too, with zero lines of `_get_connection()` or any of the 8 call sites edited.
- **Why this is acceptable:** WAL mode strictly improves concurrent-reader safety and does not change
  any of the 8 existing functions' query results, transaction semantics, or return shapes — SQLite's
  WAL mode is read/write-compatible with the existing rollback-journal-authored connections; no
  schema, index, or row-visibility behavior changes for the 3 legacy marker-only tables. `busy_timeout`
  (also applied by `open_connection_with_limits`) is connection-scoped only, so it has zero
  cross-call-site persistence effect — only the WAL flag persists.
- **Do NOT edit `_get_connection()` or any of its 8 existing call sites** to add `PRAGMA` statements
  directly — that would touch `tools/retrieval_cache.py`'s existing functions unnecessarily and is
  explicitly the pattern `test_sqlite_defaults_not_silently_implemented`
  (`tests/docs/test_redaction_retention_policy_doc.py`) guards against (see Step 3's citation).
- **`test_sqlite_defaults_not_silently_implemented` compatibility, verified directly, not assumed:**
  that test scans `tools/retrieval_cache.py`'s own source text for the literal strings `"PRAGMA"`,
  `"busy_timeout"`, `"os.chmod"`/`"chmod"`, and `"os"` as an imported module
  (`tests/docs/test_redaction_retention_policy_doc.py:107-125`, cited by the sibling ticket's own
  DD4, `stored_artifacts/.../plan.md:118-128`). Because this plan's new functions only *import and
  call* `knowledge_gateway_redaction.open_connection_with_limits(...)` — never writing the literal
  string `"PRAGMA"` or `"busy_timeout"` into `tools/retrieval_cache.py`'s own source, and never
  calling `.chmod(...)` or `import os` directly in that file — this guard test continues to pass
  unmodified. Confirmed by direct read of the guard's exact string-matching implementation, not
  inferred from its name.
- A new test (Step 12) asserts the real behavioral effect explicitly (journal mode observed on the
  file after a Level 1 write) so a future contributor cannot silently revert or extend this effect
  without the test failing.

This is very likely uncontroversial (a strict concurrency-safety improvement, zero behavior change to
the 8 existing call sites' outputs), so this plan does not block Implement on Review sign-off for
this specific decision — but Architecture Review should see this reasoning alongside DD3 in the same
pass, since it is the other cross-module side effect investigation flagged.

### DD5 — Security-pass precondition (`redaction_retention_policy.md` §4/§11): resolved via this ticket's own Security-Review phase, not silently waived

`redaction_retention_policy.md` §4/§11, quoted verbatim (`redaction_retention_policy.md:88-91`, `:294-297`):
*"This baseline ruleset is a documented starting point, not a production-complete secret scanner...
It must be reviewed and expanded by a security-focused pass before Phase 2 payload caching goes
live"* and *"The secret-scan ruleset in §4 remains explicitly flagged as a non-production-complete
starting baseline that must still be reviewed and expanded by a dedicated security-focused pass
before Phase 2 payload caching goes live; ratifying the policy's overall shape does not waive that
follow-up requirement."*

**This precondition is operative now.** This ticket is precisely the one that makes payload caching
reachable from a real, running `knowledge_context` call — the sibling ticket's own DD3
(`stored_artifacts/TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH/plan.md:98-114`) explicitly declined to
resolve this for itself and required this ticket's own phase to re-ask it, which investigation did
(`investigation.md:345-357`).

**Resolution:** the `security` tag added to this ticket's frontmatter routes it through
Security-Review after Implement, per this repo's standard/epic tier pipeline. This plan treats that
phase as the operative "security-focused pass" the policy requires — it is scheduled to run before
this ticket reaches Finalize/close, i.e. before the code "goes live" in the sense of being merged and
shippable. This plan does **not** pre-decide Security-Review's verdict. Security-Review must
explicitly rule on one of:
1. The disclosed 4-pattern baseline (AWS key, generic API-key assignment, PEM header, Bearer token —
   `tools/knowledge_gateway_redaction.py:121-128`) is judged sufficient to ship with, given this
   ticket's own scope guards (never-cache categories, allowlist, size cap) as defense-in-depth; ship
   as-is with the disclosure comments intact.
2. The baseline is judged insufficient for real live traffic; this ticket must then either expand the
   pattern set within this same ticket's Implement phase (a scope addition Security-Review would be
   authorizing, not this plan) or this ticket blocks on a follow-up hardening ticket before Finalize.
This plan explicitly does not assume outcome 1. **Do not silently treat Security-Review as a
formality** — if it returns `NEEDS_CHANGES`, that is real, blocking information per CLAUDE.md's Gate
Integrity Hard Rule, not an obstacle to route around.

### DD6 — `resolved_entity_ids` mapping from the router's real return shape (resolves investigation Risk 6)

Read directly, `tools/knowledge_gateway_router.py:309-323` (`IdentifierMatch`/`RoutingDecision`
dataclasses) and `:364-389` (`_match_identifier`, the fixed-order dispatcher) and `:397-405` (the
`shape_id` mapping dict inside `route()`). `IdentifierMatch.category` takes exactly 6 values:
`ticket_id`, `parity_id`, `source_path`, `registered_doc_path`, `subsystem_id`, `symbol_name`.
`evidence_cache_identity_contract.md` §1's closed deterministic forms
(`evidence_cache_identity_contract.md:47-54`, read directly) are exactly 5:
`symbol:<qualified-name>`, `ticket:<ticket-id>`, `parity:<entry-id>`, `doc:<registry-id>`,
`subsystem:<registered-name>`. Mapping:

| `IdentifierMatch.category` | `resolved_entity_ids` form |
|---|---|
| `ticket_id` | `ticket:<value>` |
| `parity_id` | `parity:<value>` |
| `registered_doc_path` | `doc:<value>` |
| `subsystem_id` | `subsystem:<value>` |
| `symbol_name` | `symbol:<value>` |
| `source_path` | **no closed form exists** — see below |
| (no match / ambiguous fallback, `matched_identifier is None`) | `[]` (empty) |

**Real gap, not invented by this plan:** a raw repo-relative source-code path
(`IdentifierMatch(category="source_path", ...)`, produced by `match_source_path()`,
`tools/knowledge_gateway_router.py:86-95`) has no corresponding form in §1's closed 5-form list. Note
this is a different concept from `evidence_identity_kinds.schema.json`'s separate `FILE` kind
(`stable_identity_form: "file:<repo-relative-path>"`, read directly) — that schema governs §2's
*evidence-validity* identity, not §1's *lookup* identity, and this plan does not conflate the two
(Non-collapse rule, DD9 below). **Resolution:** `resolved_entity_ids` is `[]` for a `source_path`
match — an honest omission (the contract genuinely defines no form for this case) rather than an
invented 6th form. This is a real, load-bearing limitation of the frozen `evidence_cache_identity_contract.md`
document that this ticket does not have authority to amend (it is a Certified/frozen contract); flag
in Anti-Drift Notes so it is not mistaken for an oversight later.

### DD7 — `routing_policy_version`: new constant lives in the new module, not in the frozen router

No `routing_policy_version`-shaped constant exists anywhere in `tools/knowledge_gateway_router.py`
today (confirmed by direct full read). `tools/knowledge_gateway_router.py` is explicit Out of Scope
for this ticket (ticket's own Out of Scope bullet, re-confirmed still banned by
`test_search_mcp_py_provably_untouched`, `tests/tools/test_knowledge_gateway_mcp.py:170-183`) — so
this plan cannot add the constant there. **Decision:** define
`ROUTING_POLICY_VERSION: int = 1` inside the new `tools/knowledge_gateway_cache.py` module itself,
documented in its own comment as versioning this cache-identity layer's *assumption* about the
router's routing-table shape (`ROUTING_TABLE`'s 7 rows plus `_match_identifier`'s fixed matcher
order, `tools/knowledge_gateway_router.py:151-185`, `:364-389`) — bumped only if a future change to
`knowledge_gateway_router.py` would invalidate previously-cached lookup identities (e.g. a routing
shape added/removed, or matcher order changed such that the same query text now resolves
differently). This is an external-observer's version stamp on a frozen module's shape, analogous in
spirit to how `adapter_version_at_validation` externally stamps a provider's version without that
provider module needing to expose its own version constant for this purpose.

### DD8 — `filters`/`budget_class` field mapping

`knowledge_context_request.schema.json`'s optional fields (`mode`, `budget_tokens`, `changed_paths`,
`include_history`, `evidence_detail` — confirmed via `tools/knowledge_gateway_mcp.py:139-162`'s own
non-`None` field-building code) split three ways for identity purposes:
- `changed_paths` → working-tree overlap (§5), a separate identity axis, not `filters` (DD11/Step 6).
- `budget_tokens` → `budget_class` only, never raw into `filters` (§1's own field description:
  "budget tier ... not the raw numeric budget," `evidence_cache_identity_contract.md:43`).
- `mode`, `include_history`, `evidence_detail` → `filters`, since each affects which result content
  is selected/returned, matching §1's "caller-supplied filter set" framing. Serialized as
  `json.dumps({k: v for k, v in {"mode": mode, "include_history": include_history, "evidence_detail":
  evidence_detail}.items() if v is not None}, sort_keys=True)` — reusing the exact
  normalize-then-hash shape `evidence_cache_identity_contract.md:56-64` cites as the precedent to
  reuse (`_hash_filters`, `tools/retrieval_cache.py:275-276`), called from inside
  `retrieval_cache.py` itself (no private-member reach-through needed, since the new SQL-layer
  functions live in that same module per DD2).

`budget_class` bucket boundaries reuse `redaction_retention_policy.md` §8's own provisional buckets
(`redaction_retention_policy.md:188-190`, read directly: small ≤500, medium 501–2000, large >2000)
applied directly to `budget_tokens`/`DEFAULT_BUDGET_TOKENS` (the same integer-token unit that
document's bucket table was defined against) — the only documented bucket boundaries anywhere in this
subsystem; no better-grounded alternative exists.

### DD9 — Non-collapse rule enforced structurally (§3)

`check_provider_result_cache()` (Step 2) returns only a status/reason_code-shaped result plus the
row's *raw stored column values* — never a `freshness`/`verification` field, matching
`IndexCacheResult`/`QueryCacheResult`/`PacketCacheResult`'s existing shape
(`tools/retrieval_cache.py:294-297`, `:356-359`, `:425-428`, all read directly, each carrying only
`status`/`reason_code`). Evidence-validity revalidation (Step 6) is a separate function, called only
after a lookup hit, consuming the raw row — never folded into the lookup query itself, matching
`evidence_cache_identity_contract.md` §3's rule verbatim (`evidence_cache_identity_contract.md:100-121`).

### DD10 — The frozen `migration_001` primary key is narrower than the 6-field lookup identity: documented limitation, not silently built over

Real finding, not present in investigation.md — surfaced during this plan's own read of
`migration_001_add_level1_tables`'s `CREATE TABLE` statement
(`tools/retrieval_cache.py:216-240`): `retrieval_provider_result_cache_rows`'s primary key is
`(query_hash, repo_branch_scope)` only. `filters`, `budget_class`, and `routing_policy_version` are
ordinary columns, **not** part of the primary key — yet `evidence_cache_identity_contract.md` §1
defines the *full* 6-field tuple as the lookup identity. Two requests sharing the same
`query_hash`/`repo_branch_scope` but genuinely different `filters` (e.g. different `mode`) would
collide on the same physical row under a naive `INSERT OR REPLACE`.

**This ticket does not alter the primary key** — `migration_001` is already shipped/frozen (this
ticket's own Related Tickets lists `CACHE-SCHEMA-MIGRATIONS` as a closed dependency, and widening a
primary key is a materially larger migration than this ticket's minimal-footprint scope authorizes).
**Mitigation within the existing schema:** `check_provider_result_cache()` (Step 2), after the
PK-based `SELECT`, additionally compares the stored `filters`/`budget_class`/`routing_policy_version`
column values against the caller's current computed values — any mismatch is treated as a genuine
`MISS` (not `STALE_REJECTED`; this is a different-identity case, not a staleness case), exactly
mirroring `check_query_cache()`'s own existing pattern of comparing `corpus_generation`/
`retrieval_version` in Python after a broader SQL `SELECT`
(`tools/retrieval_cache.py:362-384`, read directly). **Consequence, stated plainly:** two genuinely
different lookup identities that happen to share `(query_hash, repo_branch_scope)` will thrash each
other's single row slot (each write evicts the other) rather than being served incorrectly — this
degrades to extra cache misses, never to serving a wrong-identity row as a hit, because the
mismatch-detection step always falls through to `MISS` first. Flagged in Anti-Drift Notes as a real,
accepted limitation of the frozen schema, not a bug this ticket introduces or is expected to fix.

### DD11 — TOCTOU/snapshot rule (§12.2, resolves investigation Risk 5)

The proposal's own text (`docs/plans/knowledge-gateway-mcp-proposal.md` §12.2, quoted by
investigation.md) requires snapshotting the path set once before hashing, never re-querying
mid-validation. This is naturally satisfied by construction here: `changed_paths` is a request field,
already present in the validated `request` dict before the cache-check hook runs
(`tools/knowledge_gateway_mcp.py:157-158`), and this plan's working-tree-overlap check
(Step 6) reads `request.get("changed_paths", [])` exactly once at the top of the cache-check
call and threads that same list through — it never calls `git status`/`git diff` again mid-validation.
The only place this module calls real git subprocesses at all is branch-identity resolution (Step 6's
`_current_repo_branch_scope()`, a single `git branch --show-current` call, analogous to
`tools/knowledge_gateway_mcp.py:292-303`'s existing `_git_branch_scope()`), which is unrelated to the
path-set snapshot and carries no TOCTOU risk of its own (a branch name is a single atomic read, not a
multi-file scan).

### DD12 — `knowledge_status` cache-domain fields: which 4 of 6 are populated (confirms investigation's field-split finding)

Per investigation's own reading of both response schemas (`investigation.md:167-189`, re-verified
directly against `knowledge_status_response.schema.json:27-51`): this ticket populates
`cache_entry_counts`, `cache_hit_rate`, `cache_miss_rate`, `cache_stale_rejection_rate` from a new
read-only `retrieval_cache.provider_result_cache_stats()` aggregator (Step 10). `latency_summary_ms`
and `provider_fallback_rate` stay honestly omitted — this ticket adds no latency instrumentation
(confirmed: `tools/retrieval_events.py`'s 3 wrapper functions remain genuinely unused,
`test_wrapper_functions_genuinely_not_applicable_zero_invoked`,
`tests/tools/test_knowledge_gateway_mcp.py:190-214`, unmodified by this ticket). `recent_invalidation_reasons`
and `cache_rebuildable` are also left omitted — the ticket's own AC6/Scope names only "cache entry
counts, hit/miss rates, staleness counts," not these two; adding them would be unrequested scope.

### DD13 — `test_knowledge_status_omits_all_cache_specific_fields_enumerated` narrowing: legitimate correction, precedent cited

This is a real, currently-passing regression test
(`tests/tools/test_knowledge_gateway_mcp.py:120-134`) whose Phase-1-correct assertions this ticket's
own in-scope behavior change deliberately supersedes — not a gate this plan is routing around. This
mirrors the same "legitimate stale-assertion correction, not gate-dodging" pattern already applied
twice earlier in this session's ticket family:
1. `TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS`'s own DD3
   (`stored_artifacts/TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS/plan.md:63-75`) — correcting
   `test_kgmcp_measurement_baseline.py`'s stale banned-path tuple assumption.
2. That same ticket's Step 6
   (`stored_artifacts/TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS/plan.md:480`) — the concrete
   implementation of that correction, permanently removing `tools/retrieval_cache.py` from the
   banned-path tuple rather than ticket-window-scoping it back.
Step 11 below performs the same direct-read-and-justify process: only the 4 fields this ticket's own
scope newly populates (`cache_entry_counts`, `cache_hit_rate`, `cache_miss_rate`,
`cache_stale_rejection_rate`) are removed from the omission-assertion; the remaining guarantee
(`latency_summary_ms`, `provider_fallback_rate` stay absent) is preserved, not weakened wholesale —
matching test_plan.md's own Anti-Drift Test Guard for this exact test
(`staging_artifacts/.../test_plan.md:222-228`).

### DD14 — Cache-DB test isolation fixture, added to `tests/tools/test_knowledge_gateway_mcp.py`

No cache-DB isolation fixture exists yet in that file (confirmed by direct read — no
`tmp_path`/`monkeypatch` touching `CACHE_DB_PATH` anywhere in it today). `tests/tools/test_retrieval_cache.py`'s
own `_isolated_cache_db` autouse fixture (`tests/tools/test_retrieval_cache.py:34-38`, read directly:
`monkeypatch.setattr(rc, "CACHE_DB_PATH", tmp_path / "retrieval_cache.db")`) is the direct precedent.
Step 11 adds an equivalent autouse fixture to `test_knowledge_gateway_mcp.py`, monkeypatching
`retrieval_cache.CACHE_DB_PATH` (imported by the new `tools/knowledge_gateway_cache.py` module, not
redefined there — see Step 5) to a `tmp_path`-scoped file for every test in that file, preventing
cross-test cache pollution of the real on-disk `knowledge-index/retrieval_cache.db`.

## Steps

### Step 1 — `tools/knowledge_gateway_cache.py` module skeleton and constants

**Files:** `tools/knowledge_gateway_cache.py` (new)

**Change:** Create the module with a docstring modeled on
`tools/knowledge_gateway_redaction.py:1-33`'s "what this is / what this is not" convention: this
module computes lookup identity (§1), evidence-validity identity (§2/§3/§4), and branch/working-tree
scope (§5/§12.3) as genuinely separate steps (Non-collapse rule, DD9), and orchestrates
`knowledge_gateway_redaction.evaluate_write_candidate()` plus `retrieval_cache.write_provider_result_cache()`
on a miss. Import `tools/retrieval_cache.py` and `tools/knowledge_gateway_redaction.py` directly
(both are plain, non-sibling-loaded modules already importable via `sys.path`/package layout — verify
against how `tests/tools/test_retrieval_cache.py:31` imports `from tools import retrieval_cache as rc`;
if `tools/knowledge_gateway_cache.py` runs standalone outside the test harness's `sys.path` setup,
use the same `importlib.util` sibling-loading idiom the other `knowledge_gateway_*` modules use for
consistency — implementer's call, no test distinguishes the two, both are valid per repo precedent).

```python
ROUTING_POLICY_VERSION: int = 1  # DD7 — versions this module's assumption about
                                  # knowledge_gateway_router.py's routing-table shape.

_BUDGET_CLASS_SMALL_MAX = 500     # DD8 — reused from redaction_retention_policy.md §8's
_BUDGET_CLASS_MEDIUM_MAX = 2000   # provisional buckets (small/medium/large).


def compute_budget_class(budget_tokens: int) -> str:
    if budget_tokens <= _BUDGET_CLASS_SMALL_MAX:
        return "small"
    if budget_tokens <= _BUDGET_CLASS_MEDIUM_MAX:
        return "medium"
    return "large"
```

**Do NOT touch:** `tools/knowledge_gateway_router.py` (DD7 explicitly forbids adding
`routing_policy_version` there).

**Verify:** `test_module_docstring_states_non_collapse_and_orchestration_role`,
`test_compute_budget_class_small_medium_large_boundaries`.

### Step 2 — `retrieval_cache.py::check_provider_result_cache()` (SQL-layer lookup, Non-collapse-safe)

**Files:** `tools/retrieval_cache.py`

**Change:** Add a typed result dataclass and lookup function, mirroring `QueryCacheResult`/
`check_query_cache()`'s exact shape (`tools/retrieval_cache.py:356-384`) but extended to also return
the raw stored row (needed by the orchestrator's separate validity step, DD9) and to apply DD10's
mismatch-as-miss mitigation:

```python
@dataclass(frozen=True)
class ProviderResultCacheLookup:
    status: str                 # HIT or MISS — never a freshness/verification field (DD9)
    reason_code: str | None
    row: dict | None            # raw stored column values, present only on HIT


def check_provider_result_cache(
    query_hash: str,
    repo_branch_scope: str,
    *,
    normalized_intent: str,
    filters_json: str,
    budget_class: str,
    routing_policy_version: int,
) -> ProviderResultCacheLookup:
    """SELECT by the real primary key (query_hash, repo_branch_scope), then compare the stored
    normalized_intent/filters/budget_class/routing_policy_version columns against the caller's
    current computed values (DD10 — the PK alone is narrower than the full 6-field lookup
    identity). Any mismatch is a MISS, not STALE_REJECTED (this is a different-identity case,
    not a staleness case)."""
    _ensure_level1_schema_for_read(migration_001_add_level1_tables)  # see Step 3's helper
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM retrieval_provider_result_cache_rows "
            "WHERE query_hash = ? AND repo_branch_scope = ?",
            (query_hash, repo_branch_scope),
        ).fetchone()
        columns = [d[0] for d in conn.execute(
            "SELECT * FROM retrieval_provider_result_cache_rows LIMIT 0"
        ).description]
    finally:
        conn.close()
    if row is None:
        return ProviderResultCacheLookup(status=MISS, reason_code="no_cached_row", row=None)
    row_dict = dict(zip(columns, row))
    if (
        row_dict["normalized_intent"] != normalized_intent
        or row_dict["filters"] != filters_json
        or row_dict["budget_class"] != budget_class
        or row_dict["routing_policy_version"] != str(routing_policy_version)
    ):
        return ProviderResultCacheLookup(status=MISS, reason_code="identity_mismatch_on_shared_key", row=None)
    return ProviderResultCacheLookup(status=HIT, reason_code=None, row=row_dict)
```

`_ensure_level1_schema_for_read` is a one-line private helper reusing the existing plain
`_get_connection()` for reads (no WAL needed for a read-only path against a table that may not exist
yet on a fresh DB — a `SELECT` against a missing table raises `sqlite3.OperationalError`; call
`migration_001_add_level1_tables(conn)` once via a short-lived connection first, mirroring the "safe
to call again" idempotency `migration_001_add_level1_tables`'s own docstring already guarantees,
`tools/retrieval_cache.py:198-205`).

**Other writers to a shared resource:** `retrieval_provider_result_cache_rows` — this function only
reads it; the only writers are Step 3's `write_provider_result_cache()`/`record_provider_result_cache_hit()`,
both added by this same ticket. No other function anywhere in the repo touches this table (confirmed:
`TestMigrations::test_migration_001_function_is_never_called_from_any_check_or_write_function`,
`tests/tools/test_retrieval_cache.py:406-410`, iterates only the original 6 functions and does not,
and per its own construction cannot, cover this ticket's new functions — a separate assertion is
needed, see Step 12).

**Do NOT touch:** the 6 existing `check_*_cache`/`write_*_cache` functions or their SQL text.

**Verify:** `test_check_provider_result_cache_creates_table_on_first_real_use` (test_plan.md's own
named test), `test_check_provider_result_cache_miss_on_no_row`,
`test_check_provider_result_cache_hit_on_matching_full_identity`,
`test_check_provider_result_cache_miss_on_filters_mismatch_despite_pk_match` (DD10's mitigation,
directly exercised),
`test_lookup_function_never_returns_a_freshness_or_verification_field` (test_plan.md's own named
AST-based guard, DD9).

### Step 3 — `retrieval_cache.py::write_provider_result_cache()` / `record_provider_result_cache_hit()` (SQL-layer writes, WAL-mode connection per DD4)

**Files:** `tools/retrieval_cache.py`

**Change:**

```python
def _get_level1_connection() -> sqlite3.Connection:
    """DD4/DD2 — opens CACHE_DB_PATH via knowledge_gateway_redaction.open_connection_with_limits()
    (WAL + busy_timeout + 0600-on-create), not the plain _get_connection() the 3 legacy tables use.
    Ensures the Level 1 table (and, if DD3 is confirmed, the redaction_policy_version column) exist
    before any write."""
    conn = _kgr_redaction.open_connection_with_limits(CACHE_DB_PATH)
    migration_001_add_level1_tables(conn)
    migration_003_add_redaction_policy_version_column(conn)  # Step 4 — omit this line entirely
                                                              # if Architecture Review selects DD3
                                                              # option (a) instead.
    return conn


def write_provider_result_cache(
    *,
    query_hash: str, normalized_intent: str, resolved_entity_ids_json: str, filters_json: str,
    budget_class: str, routing_policy_version: int, repo_branch_scope: str,
    provider_name_json: str, adapter_version_json: str, result_payload: str,
    source_ids_json: str, source_paths_json: str, provider_generation: str,
    evidence_fingerprints_json: str, validated_negative_scopes: str | None,
    adapter_version_at_validation_json: str, working_tree_overlap_json: str,
    provider_generation_at_validation: str,
    redaction_policy_version: int | None = None,  # only written if DD3 option (b) is confirmed
) -> None:
    conn = _get_level1_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO retrieval_provider_result_cache_rows "
            "(query_hash, normalized_intent, resolved_entity_ids, filters, budget_class, "
            " routing_policy_version, repo_branch_scope, provider_name, adapter_version, "
            " result_payload, source_ids, source_paths, provider_generation, "
            " evidence_fingerprints, validated_negative_scopes, adapter_version_at_validation, "
            " working_tree_overlap, provider_generation_at_validation, created_at, "
            " last_hit_at, hit_count)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0)",
            (query_hash, normalized_intent, resolved_entity_ids_json, filters_json, budget_class,
             str(routing_policy_version), repo_branch_scope, provider_name_json,
             adapter_version_json, result_payload, source_ids_json, source_paths_json,
             provider_generation, evidence_fingerprints_json, validated_negative_scopes,
             adapter_version_at_validation_json, working_tree_overlap_json,
             provider_generation_at_validation, time.time()),
        )
        conn.commit()
    finally:
        conn.close()


def record_provider_result_cache_hit(query_hash: str, repo_branch_scope: str) -> None:
    """Called only after a genuine, revalidated HIT (never on a bare lookup hit — DD9) —
    increments hit_count and stamps last_hit_at."""
    conn = _get_level1_connection()
    try:
        conn.execute(
            "UPDATE retrieval_provider_result_cache_rows "
            "SET hit_count = hit_count + 1, last_hit_at = ? "
            "WHERE query_hash = ? AND repo_branch_scope = ?",
            (time.time(), query_hash, repo_branch_scope),
        )
        conn.commit()
    finally:
        conn.close()
```

`_kgr_redaction` is a module-level `import` of `tools/knowledge_gateway_redaction.py` at this file's
top (or an `importlib.util` sibling-load, consistent with whichever style Step 1 settles on for the
new orchestration module — pick one style and use it consistently across both files).

**Other writers to a shared resource:** enumerated in full at DD4. Summary: `CACHE_DB_PATH` is also
opened by the 6 legacy `check_*`/`write_*` functions plus `prune`/`cmd_stats` (all via
`_get_connection()`, unaffected in output, only observing WAL mode going forward per DD4);
`retrieval_provider_result_cache_rows` itself has no other writer anywhere in the repo before this
ticket (confirmed — no `INSERT`/`UPDATE` against that table name exists anywhere in `tools/` prior to
this step, per investigation's own full-file read).

**Do NOT touch:** `_get_connection()` itself (DD4 — legacy call sites keep using it unmodified).

**Verify:** `test_write_provider_result_cache_creates_table_and_inserts_row`,
`test_write_provider_result_cache_insert_or_replace_overwrites_same_pk`,
`test_record_provider_result_cache_hit_increments_hit_count_and_stamps_last_hit_at`,
`test_wal_mode_effect_on_real_cache_db_path_is_a_documented_deliberate_choice` (test_plan.md's own
named test — assert journal mode via `PRAGMA journal_mode` on a `tmp_path`-scoped file after a
`write_provider_result_cache()` call, per DD4's own citation requirement).

### Step 4 — `migration_003_add_redaction_policy_version_column` (contingent on DD3's Architecture Review confirmation)

**Files:** `tools/retrieval_cache.py`

**Change:**

```python
def migration_003_add_redaction_policy_version_column(conn: sqlite3.Connection) -> None:
    """Adds redaction_policy_version to retrieval_provider_result_cache_rows (DD3). Never called
    from _get_connection()/_init_schema() or any of the original 6 check/write functions — invoked
    only from _get_level1_connection() (Step 3), idempotent via an explicit PRAGMA table_info
    existence check (SQLite has no ALTER TABLE ADD COLUMN IF NOT EXISTS)."""
    columns = [row[1] for row in conn.execute(
        "PRAGMA table_info(retrieval_provider_result_cache_rows)"
    ).fetchall()]
    if "redaction_policy_version" not in columns:
        conn.execute(
            "ALTER TABLE retrieval_provider_result_cache_rows "
            "ADD COLUMN redaction_policy_version INTEGER"
        )
        conn.commit()
```

`LEVEL1_CACHE_COLUMNS` (`tools/retrieval_cache.py:104-128`) gains a 22nd entry,
`"redaction_policy_version"`.

**If Architecture Review selects DD3 option (a) instead:** drop this step entirely, drop the
`migration_003_add_redaction_policy_version_column(conn)` call from `_get_level1_connection()`
(Step 3), drop the `redaction_policy_version` parameter from `write_provider_result_cache()`, and
`LEVEL1_CACHE_COLUMNS` stays at 21 columns. Step 12's guard test switches from the migration-specific
tests below to `test_level1_cache_columns_unchanged_unless_migration_003_explicitly_added`
(test_plan.md's own named fallback test).

**Other writers to a shared resource:** none — this is a schema `ALTER`, applied once per fresh
database via the idempotency check; no other function issues DDL against this table.

**Do NOT touch:** `migration_001_add_level1_tables` or `migration_002` (name reserved, per DD3's
citation of the schema-migrations ticket's Anti-Drift Notes) — this is a wholly new, separately
numbered function, never folded into either.

**Verify:** `test_migration_003_adds_column_to_fresh_database`,
`test_migration_003_is_idempotent_on_already_migrated_database`,
`test_migration_003_preserves_existing_rows_and_the_20_other_columns`,
`test_migration_002_name_never_reused_or_stubbed` (static guard, mirrors the schema-migrations
ticket's own precedent for this exact name-reservation rule).

### Step 5 — `knowledge_gateway_cache.py::compute_lookup_identity()`

**Files:** `tools/knowledge_gateway_cache.py`

**Change:**

```python
_IDENTIFIER_CATEGORY_TO_FORM = {
    "ticket_id": "ticket:{}",
    "parity_id": "parity:{}",
    "registered_doc_path": "doc:{}",
    "subsystem_id": "subsystem:{}",
    "symbol_name": "symbol:{}",
    # "source_path" intentionally absent — DD6, no closed form exists in
    # evidence_cache_identity_contract.md §1 for this category.
}


def compute_resolved_entity_ids(routing_decision) -> list[str]:
    match = routing_decision.matched_identifier
    if match is None:
        return []
    form = _IDENTIFIER_CATEGORY_TO_FORM.get(match.category)
    if form is None:
        return []  # DD6 — source_path (or any future unmapped category) has no closed form
    return [form.format(match.value)]


def compute_lookup_identity(request: dict, routing_decision, effective_budget: int) -> dict:
    """Returns the 6-field §1 tuple as a plain dict. Called once per request, before route()
    per DD1's hook placement, so routing_decision here is the just-computed real decision."""
    filters = {
        k: request[k] for k in ("mode", "include_history", "evidence_detail") if k in request
    }
    return {
        "normalized_intent": rc._normalize_query(request["query"]),
        "resolved_entity_ids_json": json.dumps(sorted(compute_resolved_entity_ids(routing_decision))),
        "filters_json": json.dumps(filters, sort_keys=True),
        "budget_class": compute_budget_class(effective_budget),
        "routing_policy_version": ROUTING_POLICY_VERSION,
        "repo_branch_scope": _current_repo_branch_scope(),
        "query_hash": rc._hash_text(rc._normalize_query(request["query"])),
    }
```

`rc` is the imported/sibling-loaded `tools/retrieval_cache.py` module (Step 1). `_normalize_query`/
`_hash_text` are private to that module (`tools/retrieval_cache.py:267-272`) — calling them from a
different module reaches into another module's private surface, the same tradeoff the sibling
ticket's Step 3 explicitly declined for `redact_content()`'s hashing
(`stored_artifacts/.../plan.md:293-299`, DD explicitly duplicated the one-liner instead). Since these
two are single-line, stable, load-bearing normalization primitives that `evidence_cache_identity_contract.md:56-64`
*itself* says a future implementation "should reuse... not invent a second one," this plan reuses
them directly rather than duplicating — a deliberate deviation from the sibling ticket's own
precedent, justified because the contract doc explicitly asks for reuse here (unlike §3's hashing,
where no such reuse instruction exists). Document this reasoning in the new module's own docstring so
it reads as a considered choice, not an inconsistency with the sibling ticket's style.

**Other writers to a shared resource:** none — this is a pure computation function, no I/O.

**Do NOT touch:** `tools/knowledge_gateway_router.py` (DD7); do not invent a 6th `resolved_entity_ids`
form for `source_path` (DD6).

**Verify:** `test_compute_resolved_entity_ids_maps_all_five_closed_forms`,
`test_compute_resolved_entity_ids_empty_for_source_path_match`,
`test_compute_resolved_entity_ids_empty_for_ambiguous_fallback`,
`test_compute_lookup_identity_filters_excludes_budget_tokens_and_changed_paths`,
`test_compute_lookup_identity_query_hash_matches_retrieval_cache_normalization`.

### Step 6 — `knowledge_gateway_cache.py`: evidence-validity revalidation + branch/working-tree scope (separate step from Step 5, DD9)

**Files:** `tools/knowledge_gateway_cache.py`

**Change:**

```python
def select_validation_basis(capability_descriptor: dict) -> str:
    """§4's fallback rule, structural form. Returns 'PROVIDER_GENERATION' when the descriptor
    does not advertise fine_grained_fingerprints; 'FINER' otherwise. Never the default when finer
    evidence IS available (AC3)."""
    return "PROVIDER_GENERATION" if not capability_descriptor.get("fine_grained_fingerprints") else "FINER"


def is_branch_compatible(row_repo_branch_scope: str, current_repo_branch_scope: str) -> bool:
    """§5 rule 2 — hard partition, checked before any fingerprint comparison."""
    return row_repo_branch_scope == current_repo_branch_scope


def working_tree_overlap_forces_revalidation(evidence_paths_json: str, changed_paths: list[str]) -> bool:
    """§5 rule 3 — changed_paths ∩ evidence dependency paths only, never a full-tree hash.
    changed_paths is read once by the caller from the validated request dict (DD11) and passed
    through unchanged."""
    evidence_paths = set(json.loads(evidence_paths_json))
    return bool(evidence_paths & set(changed_paths))


def revalidate_cache_row(
    row: dict, *, capability_descriptor: dict, current_provider_generation: str,
    current_evidence_fingerprint: str | None, changed_paths: list[str],
) -> bool:
    """True = still valid (serve as a genuine HIT). False = stale (treat as MISS, refresh).
    A distinct step from the lookup (Step 2/DD9) — consulted only after a lookup hit."""
    if working_tree_overlap_forces_revalidation(row["working_tree_overlap"], changed_paths):
        return False
    basis = select_validation_basis(capability_descriptor)
    if basis == "PROVIDER_GENERATION":
        # Hard rule (§4): a SYMBOL/FILE-backed row (finer fingerprint recorded) must never be
        # invalidated by a bare PROVIDER_GENERATION bump alone.
        if row.get("evidence_fingerprints", "").startswith(("symbol:", "file:")):
            return True
        return row["provider_generation_at_validation"] == current_provider_generation
    return row["evidence_fingerprints"] == current_evidence_fingerprint


def _current_repo_branch_scope() -> str:
    """Independent of tools/knowledge_gateway_mcp.py::_git_branch_scope() (avoids a
    circular/backwards import — this module is loaded BY knowledge_gateway_mcp.py, not the
    other way around); same underlying git command, single atomic read (DD11)."""
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=str(_REPO_ROOT),
        capture_output=True, text=True,
    ).stdout.strip() or "DETACHED"
    return f"{_REPO_ROOT}::{branch}"
```

**Other writers to a shared resource:** none — pure computation, no I/O beyond the single git
subprocess call, which is read-only.

**Do NOT touch:** do not call `git status`/`git diff` a second time anywhere in this step (DD11 —
would reintroduce the TOCTOU risk §12.2 exists to prevent).

**Verify:** `test_provider_generation_fallback_used_for_both_real_providers_today` (loads the real
`provider_capabilities_context_search.json`/`provider_capabilities_graphify.json` — both confirmed
directly to report `fine_grained_fingerprints: false` — and asserts `select_validation_basis` returns
`"PROVIDER_GENERATION"` for both), `test_finer_fingerprint_preferred_over_provider_generation_when_capability_advertises_it`,
`test_symbol_backed_cache_row_rejected_on_direct_fingerprint_mismatch_fixture`,
`test_symbol_backed_cache_row_survives_unrelated_generation_bump_fixture` (both explicitly
docstring-labeled as fixture-based, per test_plan.md's own honesty requirement — real live providers
cannot exercise this path today, confirmed above),
`test_cached_result_from_feature_branch_not_served_on_different_branch`,
`test_new_commit_alone_does_not_force_cache_miss_when_evidence_unchanged`,
`test_working_tree_fingerprint_uses_changed_paths_intersection_not_full_tree_hash`.

### Step 7 — `knowledge_gateway_cache.py::perform_cache_lookup()` orchestrator

**Files:** `tools/knowledge_gateway_cache.py`

**Change:** Ties Steps 2/5/6 together as genuinely separate calls (Non-collapse rule, DD9):

```python
def perform_cache_lookup(request: dict, routing_decision, effective_budget: int) -> dict | None:
    """Returns the cached payload dict on a genuine, revalidated HIT; None on any MISS/stale
    result. Bumps hit stats only on a genuine hit (never on a bare lookup hit)."""
    identity = compute_lookup_identity(request, routing_decision, effective_budget)
    lookup = rc.check_provider_result_cache(
        identity["query_hash"], identity["repo_branch_scope"],
        normalized_intent=identity["normalized_intent"], filters_json=identity["filters_json"],
        budget_class=identity["budget_class"], routing_policy_version=identity["routing_policy_version"],
    )
    if lookup.status != rc.HIT:
        return None
    if not is_branch_compatible(lookup.row["repo_branch_scope"], identity["repo_branch_scope"]):
        return None
    capability_descriptor = _capability_descriptor_for(routing_decision.providers_selected)
    valid = revalidate_cache_row(
        lookup.row, capability_descriptor=capability_descriptor,
        current_provider_generation=rc._corpus_generation(),
        current_evidence_fingerprint=None,  # PROVIDER_GENERATION-only for both real providers today
        changed_paths=request.get("changed_paths", []),
    )
    if not valid:
        return None
    rc.record_provider_result_cache_hit(identity["query_hash"], identity["repo_branch_scope"])
    return json.loads(lookup.row["result_payload"])
```

**Other writers to a shared resource:** see Step 2/Step 3 — this function is the sole call site that
chains a read followed conditionally by the hit-count write; no other code path calls
`record_provider_result_cache_hit` (Step 12's guard confirms this statically).

**Do NOT touch:** do not collapse `lookup.status != rc.HIT` and `revalidate_cache_row(...)` into one
combined condition/function — they must remain two distinct calls (DD9).

**Verify:** `test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit` (test_plan.md's
own named integration test — spies on `_run_search`/`match_symbol_name`, asserts zero calls on the
second identical request).

### Step 8 — `knowledge_gateway_cache.py::perform_cache_write()` orchestrator

**Files:** `tools/knowledge_gateway_cache.py`

**Change:**

```python
def perform_cache_write(request: dict, routing_decision, packet, effective_budget: int) -> None:
    """Fire-and-forget from the caller's perspective (Step 9 wraps this in try/except for
    fail-open semantics) — never returns the write outcome to the response."""
    identity = compute_lookup_identity(request, routing_decision, effective_budget)
    cache_key = f"{identity['query_hash']}:{identity['repo_branch_scope']}"
    if not rk.acquire_write_guard(cache_key):
        return  # another in-process write for this exact key is already in flight
    try:
        if not rk.check_db_size_within_limit(rc.CACHE_DB_PATH):
            return  # §9 ceiling — skip write, still return the live result to the caller
        source_type = rk.SOURCE_TYPE_CONTEXT_SEARCH if "context_search" in packet.providers_consulted_this_call else rk.SOURCE_TYPE_GRAPHIFY
        raw_payload = json.dumps({
            "answer": packet.answer, "statements": [...], "context": [...], "evidence": [...],
        }, sort_keys=True)  # implementer: reuse the exact same _omit_none()-shaped serialization
                             # tools/knowledge_gateway_mcp.py already builds for the response, to
                             # avoid a second, divergent serialization of the same packet fields.
        decision = rk.evaluate_write_candidate(source_type=source_type, raw_content=raw_payload)
        if decision.verdict != rk.ALLOW:
            return
        provider_generation = rc._corpus_generation()
        rc.write_provider_result_cache(
            query_hash=identity["query_hash"], normalized_intent=identity["normalized_intent"],
            resolved_entity_ids_json=identity["resolved_entity_ids_json"],
            filters_json=identity["filters_json"], budget_class=identity["budget_class"],
            routing_policy_version=identity["routing_policy_version"],
            repo_branch_scope=identity["repo_branch_scope"],
            provider_name_json=json.dumps(sorted(packet.providers_consulted_this_call)),
            adapter_version_json=json.dumps(_adapter_versions_for(packet.providers_consulted_this_call)),
            result_payload=decision.redacted_payload,
            source_ids_json=json.dumps(sorted({c.source_id for c in packet.context if c.source_id})),
            source_paths_json=json.dumps(sorted({c.path for c in packet.context if c.path})),
            provider_generation=provider_generation,
            evidence_fingerprints_json=f"generation:{'+'.join(sorted(packet.providers_consulted_this_call))}@{provider_generation}",
            validated_negative_scopes=None,  # honest omission — see plan DD notes below
            adapter_version_at_validation_json=json.dumps(_adapter_versions_for(packet.providers_consulted_this_call)),
            working_tree_overlap_json=json.dumps(sorted({c.path for c in packet.context if c.path})),
            provider_generation_at_validation=provider_generation,
            redaction_policy_version=decision.redaction_policy_version,  # omit this kwarg entirely
                                                                          # if DD3 resolves to option (a)
        )
    finally:
        rk.release_write_guard(cache_key)
```

`rk` is the imported/sibling-loaded `tools/knowledge_gateway_redaction.py` module. `validated_negative_scopes`
stays `None` for every write this ticket performs — deriving a real negative-claim scope would
require deeper cooperation from `tools/knowledge_gateway_packet_assembly.py`'s `NegativeClaimSupport`
handling, and that module is explicit Out of Scope/frozen for this ticket; `None` is an honest
omission (the column is nullable, `tools/retrieval_cache.py:231`, confirmed by direct read of the
`CREATE TABLE` statement), not a fabricated placeholder. `working_tree_overlap_json` stores the
evidence's own dependency-path set (the same set later intersected against a *future* request's
`changed_paths` at read time, Step 6) — this is this plan's own interpretation of the contract's
somewhat storage-ambiguous `working_tree_overlap` field name, stated explicitly here rather than
silently assumed.

**Other writers to a shared resource:** the write guard (`acquire_write_guard`/`release_write_guard`,
`tools/knowledge_gateway_redaction.py:307-322`) is in-process-lock-based, module-private state inside
`knowledge_gateway_redaction.py` — no other module reads or writes `_write_locks`. The real
`INSERT`/`UPDATE` calls chain to Step 3's functions, whose own writer-enumeration already covers this.

**Do NOT touch:** do not call `rc.write_provider_result_cache()` anywhere else in this module or
`tools/knowledge_gateway_mcp.py` except from inside this one orchestrator function (Step 12's static
guard enforces this — AC5's "no raw/unredacted write path exists anywhere").

**Verify:** `test_cache_write_calls_evaluate_write_candidate_before_any_insert`,
`test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module` (adapted per DD2's
call-site split: statically confirms `retrieval_cache.write_provider_result_cache()` is called only
from `perform_cache_write()`, and that `perform_cache_write()` never calls
`write_provider_result_cache()` before `evaluate_write_candidate()` returns `ALLOW` — a call-order/
call-site AST check spanning both files, not a single-file literal-text grep, since DD2 moved the
literal `INSERT` text into `tools/retrieval_cache.py`; this is a deliberate refinement of
test_plan.md's originally-described single-module guard, recorded here per CLAUDE.md's
never-silently-deviate rule, not a weakening of the guarantee it protects),
`test_per_key_stampede_guard_prevents_concurrent_duplicate_write` (re-run against the real orchestrator,
not just `knowledge_gateway_redaction.py`'s own unit test of the guard primitive),
`test_size_cap_gate_skips_write_without_raising_when_db_over_ceiling`.

### Step 9 — `tools/knowledge_gateway_mcp.py`: 2 hook call-outs + `cache`/`cache_key_version` response fields

**Files:** `tools/knowledge_gateway_mcp.py`

**Change:** Load the new module via `_load_cache_module()` (new function, same shape as the 3
existing `_load_*_module()` helpers, `tools/knowledge_gateway_mcp.py:96-125`). Insert:

- **Cache-check**, right after `_kgpa = _load_packet_assembly_module()` (`:179`) and before
  `routing_decision = _kgr.route(query)` (`:183`) — but note: `compute_lookup_identity()` needs
  `routing_decision` (for `resolved_entity_ids`), which does not exist yet at this point in the
  flow. **Resolved ordering:** `route()` must run first regardless (it is cheap/local except for the
  `symbol_name` case, and the response always needs it), so the cache-check call-out actually goes
  *immediately after* `routing_decision = _kgr.route(query)` succeeds (`:183`) and *before*
  `packet = _kgpa.assemble_packet(...)` (`:210`) — a one-line adjustment to DD1's originally-stated
  insertion point, justified because `compute_lookup_identity()` structurally requires
  `routing_decision.matched_identifier` (Step 5), which does not exist before `route()` runs. Wrap in
  `try/except Exception` (broad, matching this file's own existing fail-open precedent at
  `:184-208` for router failures) — a cache-check failure must never prevent the provider path from
  running (test_plan.md's `test_knowledge_gateway_failure_semantics.py` regression requirement).
  On a genuine hit, short-circuit: build the response directly from the cached payload
  (`status`/`freshness`/`verification` etc. must still be reconstructed — store these inside
  `result_payload`'s JSON alongside `answer`/`context`/`evidence`, or default to the last-known
  values; implementer's call on exact reconstruction shape, but the response must still pass
  `RESPONSE_VALIDATOR.validate(response)` before returning) and set `response["cache"] = "HIT"`,
  `response["cache_key_version"] = REPORTED_SCHEMA_VERSION` (or a new dedicated constant — see
  Anti-Drift Notes), skip `assemble_packet()` entirely.
- **Cache-write**, right before `RESPONSE_VALIDATOR.validate(response)` (`:286`), only on a genuine
  miss (i.e. only in the code path that actually called `assemble_packet()`). Wrap in the same
  fail-open `try/except`. Set `response["cache"] = "MISS"` before the write attempt (independent of
  whether the write itself succeeds — the response's `cache` field describes what happened on *this*
  call, not the write outcome).

**Other writers to a shared resource:** `_run_knowledge_context()`'s existing control flow
(steps 3–6, `tools/knowledge_gateway_mcp.py:178-284`) has no other concurrent modifier — this is the
sole ticket touching this function, and Phase 1's own shipped code is otherwise frozen. The two
insertion points do not alter any existing dict key already being built.

**Do NOT touch:** `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`
(explicit Out of Scope, re-confirmed still banned by `test_search_mcp_py_provably_untouched`) — the
cache hook lives entirely in the new module plus these two call-outs in `knowledge_gateway_mcp.py`
itself.

**Verify:** `test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit` (full
integration), `test_cache_hit_rejected_when_corpus_generation_changes_and_no_finer_fingerprint_exists`,
plus re-running all pre-existing tests in `tests/tools/test_knowledge_gateway_failure_semantics.py`
unmodified.

### Step 10 — `retrieval_cache.py::provider_result_cache_stats()` + `knowledge_status` population

**Files:** `tools/retrieval_cache.py`, `tools/knowledge_gateway_mcp.py`

**Change:**

```python
def provider_result_cache_stats() -> dict:
    """Read-only aggregation over retrieval_provider_result_cache_rows. Never mutates."""
    conn = _get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM retrieval_provider_result_cache_rows").fetchone()[0]
        total_hits = conn.execute(
            "SELECT COALESCE(SUM(hit_count), 0) FROM retrieval_provider_result_cache_rows"
        ).fetchone()[0]
    finally:
        conn.close()
    return {"total_rows": total, "total_hits": total_hits}
```

This function reads via `_get_connection()` (not `_get_level1_connection()`) since it is read-only and
does not need to guarantee table existence beyond a graceful `0`-row result on a fresh DB (wrap the
`SELECT`s in a table-existence check first, returning zeros rather than raising, since `knowledge_status`
must never error out because no cache activity has happened yet).

In `_run_knowledge_status()` (`tools/knowledge_gateway_mcp.py:306-343`), add, after the existing
`response` dict is built and before `STATUS_RESPONSE_VALIDATOR.validate(response)`:

```python
stats = _load_cache_module().rc.provider_result_cache_stats()  # or import retrieval_cache directly
if stats["total_rows"] > 0:
    response["cache_entry_counts"] = [{"kind": "provider_result", "count": stats["total_rows"]}]
    denom = stats["total_hits"] + stats["total_rows"]  # implementer: derive real hit/miss/stale
    response["cache_hit_rate"] = ...       # counts from a real, precisely-defined formula —
    response["cache_miss_rate"] = ...      # this plan intentionally does not hand-wave the exact
    response["cache_stale_rejection_rate"] = ...  # divisor; Implement must define it against real,
                                                    # test-observable call counts, not invent a
                                                    # plausible-looking placeholder ratio.
```

**Other writers to a shared resource:** none — read-only aggregation; the 4 fields it populates are
newly-added keys in `_run_knowledge_status()`'s response dict (no existing key is touched or removed).

**Do NOT touch:** `latency_summary_ms`, `provider_fallback_rate`, `recent_invalidation_reasons`,
`cache_rebuildable` — stay omitted (DD12).

**Verify:** `test_knowledge_status_reports_real_cache_entry_counts_and_rates_after_writes`
(test_plan.md's own named test).

### Step 11 — Test file updates: cache-DB isolation fixture + `test_knowledge_status_omits_all_cache_specific_fields_enumerated` narrowing

**Files:** `tests/tools/test_knowledge_gateway_mcp.py`

**Change:** Add the autouse isolation fixture per DD14:

```python
@pytest.fixture(autouse=True)
def _isolated_cache_db(tmp_path, monkeypatch):
    from tools import retrieval_cache as rc
    monkeypatch.setattr(rc, "CACHE_DB_PATH", tmp_path / "retrieval_cache.db")
    yield
```

Update `test_knowledge_status_omits_all_cache_specific_fields_enumerated` (`:120-134`) per DD13:
remove `cache_entry_counts`/`cache_hit_rate`/`cache_miss_rate`/`cache_stale_rejection_rate` from
`_CACHE_SPECIFIC_FIELDS` (line 109-117's set) and from the exact-keys assertion at line 132; add a
comment citing DD13 and the two precedent locations. Keep asserting `latency_summary_ms` and
`provider_fallback_rate` (plus `recent_invalidation_reasons`/`cache_rebuildable`, per DD12) remain
absent — do not delete this test's remaining guarantee.

**Other writers to a shared resource:** none — this is a test-file-only change.

**Do NOT touch:** any other assertion in this test file's other 9 tests.

**Verify:** the updated test itself, plus a full re-run of the file's other 9 pre-existing tests
unmodified.

### Step 12 — New test module + architecture guards

**Files:** `tests/tools/test_knowledge_gateway_cache.py` (new)

**Change:** Collect every test named in Steps 1–8's own Verify lists, plus:
- `test_module_does_not_import_knowledge_gateway_router_or_packet_assembly` (mirrors
  `tests/tools/test_knowledge_gateway_packet_assembly.py`'s own
  `test_module_does_not_modify_or_import_retrieval_cache`-style AST guard, applied to the new
  module in the opposite direction).
- `test_migration_001_still_never_called_from_the_original_six_check_or_write_functions`
  (re-run of the existing guard, per test_plan.md's own instruction to explicitly re-verify, not
  merely trust it).
- `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module` (per Step 8's DD2-adapted
  shape).

**Do NOT touch:** any existing test file's assertions.

**Verify:** both Scoped Pytest Commands in test_plan.md, run in full, plus a third command for the new
file: `.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_cache.py -v`.

### Step 13 — Whole-ticket regression pass

**Files:** none (verification only)

**Change:** Run all three Scoped Pytest Commands from test_plan.md (the two existing ones plus the
new file's own command) in full. Confirm the full regression surface listed in test_plan.md's
"Regression Surface" section passes unmodified, with the single, deliberate exception of
`test_knowledge_status_omits_all_cache_specific_fields_enumerated` (Step 11).

**Verify:** all commands green; zero unexplained test file diffs outside the files this plan names.

## Scope Guards

- No edit to `tools/knowledge_gateway_router.py` or `tools/knowledge_gateway_packet_assembly.py` —
  not read, not imported, not opened by any step (Step 12's guard test enforces the import half
  mechanically; `test_search_mcp_py_provably_untouched` enforces the byte-diff half).
- No `migration_002_add_level2_tables` added in any form (DD3).
- No edit to `_get_connection()` or any of its 8 existing legacy call sites (DD4) — the new WAL-mode
  connection path is additive, via a new `_get_level1_connection()` helper only.
- No `redaction_policy_version` persisted without Architecture Review's explicit confirmation of DD3
  — if Review has not yet confirmed by Implement time, ship Step 3/Step 4 in DD3-option-(a) shape
  (no migration, value dropped at the write boundary) and record the deferral, rather than guessing.
- No expansion of the §4 secret-scan baseline's 4 patterns as part of this ticket's own Implement
  step — any hardening happens only if Security-Review (DD5) explicitly authorizes it as part of this
  same ticket's scope.
- No fabricated `latency_summary_ms`/`provider_fallback_rate`/`recent_invalidation_reasons`/
  `cache_rebuildable` values in `knowledge_status` (DD12).
- No second, informal `resolved_entity_ids` form invented for `source_path` matches (DD6) — `[]` is
  the honest answer given the frozen contract's own gap.
- No `routing_policy_version` constant added to `tools/knowledge_gateway_router.py` (DD7).
- No raw/unredacted write path — every real `INSERT` into `retrieval_provider_result_cache_rows`
  is reachable only via `perform_cache_write()` after `evaluate_write_candidate()` returns `ALLOW`
  (Step 8/Step 12 guard).
- No second `git status`/`git diff` subprocess call mid-validation (DD11).
- No test in `tests/tools/test_retrieval_cache.py`, `tests/tools/test_knowledge_gateway_redaction.py`,
  or `tests/tools/test_evidence_cache_identity_contract.py` is edited — this ticket only adds new
  tests/classes to the first, and calls (never edits) the other two's existing functions.
- No `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md` edits.

## Dependency Map

- Step 1 (module skeleton) has no dependency; must land first.
- Step 2 depends on Step 1's constants being importable (module must exist) but is otherwise
  independent SQL-layer work in `tools/retrieval_cache.py`.
- Step 3 depends on Step 1 only for `knowledge_gateway_redaction` being importable — independent of
  Step 2's function bodies.
- Step 4 depends on Step 3 (`_get_level1_connection()` calls it) and on Architecture Review's DD3
  confirmation — **may be entirely dropped** per that confirmation; all other steps must remain
  correct either way (Step 3's `redaction_policy_version` parameter is optional/omittable).
- Step 5 depends on Step 1 (constants) and Step 2/3 only for the `rc` import alias — no functional
  call dependency yet.
- Step 6 is independent of Step 5 (no shared code) but both feed Step 7.
- Step 7 depends on Steps 2, 5, 6 all existing.
- Step 8 depends on Steps 1, 3, 5 (identity) and the sibling ticket's
  `knowledge_gateway_redaction.evaluate_write_candidate()`/`open_connection_with_limits()`/
  `acquire_write_guard()` (already shipped, read-only dependency).
- Step 9 depends on Steps 7 and 8 both existing (it calls both orchestrators) — this is the
  integration point, must land after both.
- Step 10 is independent of Steps 5–9 (separate read path) but conventionally lands after Step 3
  (needs the table to exist for a meaningful non-zero-row test).
- Step 11 depends on Step 9 existing (the test file's new isolation fixture and narrowed assertions
  only make sense once real cache fields can appear).
- Step 12 depends on all of Steps 1–10 existing.
- Step 13 depends on everything — must be last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — identical repeated call is a genuine cache hit, second call never reaches `_run_search()`/`graphify query` | Steps 2, 5, 6, 7, 9 | `test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit` |
| AC2 — cache hit rejected/refreshed on direct evidence fingerprint mismatch | Step 6 | `test_cache_hit_rejected_when_corpus_generation_changes_and_no_finer_fingerprint_exists`, `test_symbol_backed_cache_row_rejected_on_direct_fingerprint_mismatch_fixture` |
| AC3 — `PROVIDER_GENERATION` fallback only when finer evidence unavailable, confirmed against real provider capability files | Step 6 | `test_provider_generation_fallback_used_for_both_real_providers_today`, `test_finer_fingerprint_preferred_over_provider_generation_when_capability_advertises_it` |
| AC4 — branch/working-tree scope is real (hard branch partition; new commit alone ≠ miss) | Step 6 | `test_cached_result_from_feature_branch_not_served_on_different_branch`, `test_new_commit_alone_does_not_force_cache_miss_when_evidence_unchanged`, `test_working_tree_fingerprint_uses_changed_paths_intersection_not_full_tree_hash` |
| AC5 — cache writes go through the redaction write-path; no raw/unredacted write path exists | Step 8 | `test_cache_write_calls_evaluate_write_candidate_before_any_insert`, `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module` |
| AC6 — `knowledge_status`'s cache-domain fields are real and populated | Step 10 | `test_knowledge_status_reports_real_cache_entry_counts_and_rates_after_writes` |

## Unresolved Questions — for Architecture Review before Implement

1. **DD3 — `redaction_policy_version` persistence.** This plan's call is option (b)
   (`migration_003_add_redaction_policy_version_column`), with reasoning stated in full above.
   Architecture Review must confirm or override before Step 4 is implemented. If overridden to
   option (a), Step 4 is dropped and Step 3's `redaction_policy_version` parameter/kwarg is removed —
   no other step changes.
2. **DD4 — WAL mode going live on the real `CACHE_DB_PATH`.** This plan's call is that it is
   acceptable (a strict concurrency-safety improvement, zero output-behavior change to the 8 existing
   legacy call sites). Flagged for Architecture Review's awareness alongside DD3, not blocking by
   itself.
3. **DD5 — the security-focused pass precondition.** This plan's call is that this ticket's own
   Security-Review phase (triggered by the `security` tag) is the operative pass, run before
   Finalize. Security-Review itself must render the actual verdict (ship as-is vs. require
   hardening) — this plan does not pre-decide that verdict and neither should Architecture Review;
   it is named here only so it is not silently skipped.

## Anti-Drift Notes

- **DD3 is this plan's single most consequential open call, mirroring the sibling ticket's own DD2.**
  An implementer must not silently pick option (a) or (b) without checking whether Architecture
  Review has ruled — if Review has not yet ruled by Implement time, default to option (a) (the
  strictly smaller, non-schema-touching change) and record the deferral explicitly, rather than
  guessing toward the larger change.
- **DD5's Security-Review is not a formality.** Do not write, in any code comment or doc this ticket
  produces, language implying the security-focused pass is "satisfied" by this ticket's own Implement
  step alone — it is satisfied only by Security-Review's own explicit verdict.
- **DD6's `source_path` gap is a real, frozen-contract limitation, not an oversight to "helpfully"
  patch by inventing a 6th `resolved_entity_ids` form.** `evidence_cache_identity_contract.md` is a
  Certified/frozen document; amending its closed 5-form list is out of this ticket's authority.
- **DD10's PK-narrower-than-lookup-identity limitation is accepted, not silently built over.** Do not
  "fix" it by widening `migration_001`'s primary key — that is a larger, separately-designed
  migration this ticket does not authorize (`cache_migration_plan.md:111-115`'s own words).
- **Do not let `perform_cache_write()`'s `raw_payload` serialization silently diverge from the
  response's own field shapes.** Step 8 explicitly calls out reusing the same field set
  `tools/knowledge_gateway_mcp.py`'s existing `_omit_none()`-based response building already
  constructs, to avoid two different serializations of the same packet drifting apart over time.
- **Do not collapse Step 2's lookup and Step 6's validity check into one function or one SQL query**
  — DD9/the Non-collapse rule is the single strongest architectural constraint this ticket must
  respect, and it is the one investigation and both contract docs treat as non-negotiable.
- **Do not silently delete `test_knowledge_status_omits_all_cache_specific_fields_enumerated`'s
  remaining guarantee** (`latency_summary_ms`/`provider_fallback_rate` stay absent) while narrowing it
  — only the 4 newly-populated fields move out of the omission-assertion (DD13).

## Docs and Parity — Deferred (for later phases, not Implement)

- **Document-Update phase:** `redaction_retention_policy.md` §6's "left for a future ticket's Plan
  phase to decide explicitly" sentence (`redaction_retention_policy.md:134-135`) needs updating to
  past tense once DD3 is confirmed either way; §9's "Wiring these functions into ... the live
  gateway's actual connection-opening path remains a separate, not-yet-started ticket" sentence
  (`redaction_retention_policy.md:222-223`) needs the same tense correction once this ticket lands.
  `cache_migration_plan.md` §2 needs a `migration_003` entry added to its ordered list if DD3
  resolves to option (b). `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 2's relevant
  bullets get annotated Done.
- **Parity phase:** a new `docs/parity_ledger/infrastructure.yaml` entry, `INFRA-343` (next ID after
  `INFRA-341`/`INFRA-342`, both confirmed present and `status: verified` by direct read of that
  file's tail), covering this ticket's real read/write wiring — following `INFRA-341`/`INFRA-342`'s
  exact shape (`P1` priority, `proof_type: regression`, real `test_path`s).

## Deviations (recorded during Implement, per CLAUDE.md's never-silently-deviate rule)

All Architecture Review-ruled decisions (DD3/DD4/DD5/DD10, per the orchestrator's explicit
sign-off) were implemented exactly as ruled. The items below are implementer-level completions,
necessary corrections, or genuine conflicts this plan's own pseudocode did not fully anticipate —
each is a narrow, justified change, not a routed-around gate.

1. **Import style (Step 1's own granted latitude).** `tools/knowledge_gateway_cache.py` and
   `tools/retrieval_cache.py`'s new dependency on `tools/knowledge_gateway_redaction.py` both use
   the real package import (`from tools import X as Y`), with each module bootstrapping its own
   `sys.path` entry for the repo root first (mirroring `tests/tools/test_retrieval_cache.py`'s own
   precedent), rather than the `importlib.util` sibling-loading idiom. This is required, not
   optional: a sibling-loaded copy of `retrieval_cache`/`knowledge_gateway_redaction` would be a
   second, independent module object, silently defeating `tests/tools/test_knowledge_gateway_mcp.py`'s
   own `_isolated_cache_db` fixture (`monkeypatch.setattr(rc, "CACHE_DB_PATH", ...)`) and any
   `monkeypatch.setattr(kgr, "evaluate_write_candidate", ...)`-style spy in the new tests. Documented
   in the new module's own docstring.
2. **`_ensure_level1_schema_for_read()` implemented as a no-arg helper**, not literally matching
   Step 2's pseudocode call shape (`_ensure_level1_schema_for_read(migration_001_add_level1_tables)`).
   It only ever needs to guarantee the one fixed Level 1 table via `migration_001_add_level1_tables`
   — accepting an arbitrary migration function as a parameter added no real flexibility this
   function's single real call site uses. Same documented purpose, simpler signature.
3. **`write_provider_result_cache()`'s real INSERT includes the `redaction_policy_version` column**
   in its column list/VALUES (Step 3's own literal SQL sketch omitted it, since DD3 was still
   pending Architecture Review confirmation at Plan-writing time). Now that DD3 is confirmed
   (option (b)), this is simply Step 3's own designed behavior completed, not a new decision.
4. **`perform_cache_write()`'s signature is `(request, routing_decision, response, effective_budget)`**,
   not Step 8's literal `(request, routing_decision, packet, effective_budget)`. This directly
   implements Step 8's own Anti-Drift Note ("avoid two different serializations of the same packet
   fields drifting apart over time" / "reuse the same field set
   `tools/knowledge_gateway_mcp.py`'s existing `_omit_none()`-based response building already
   constructs"): the cleanest way to satisfy that instruction is to serialize the exact `response`
   dict `_run_knowledge_context()` has already finished building (right before schema validation),
   rather than re-deriving a second, parallel serialization from the raw `PacketAssembly` dataclass
   inside the new module. All fields Step 8's pseudocode needed from `packet` (`providers_consulted_this_call`,
   `context`-derived source ids/paths) are equally available on `response`.
5. **Two supporting helper functions not explicitly spelled out by Steps 1-6's own code**:
   `_capability_descriptor_for(providers_selected)` (a conservative merge — `fine_grained_fingerprints`
   is True only if *every* consulted real provider's descriptor advertises it) and
   `_adapter_versions_for(providers_consulted)` (loads real adapter versions from the two
   `provider_capabilities_*.json` files). Both are referenced by Step 7/8's own pseudocode
   (`_capability_descriptor_for(routing_decision.providers_selected)`,
   `_adapter_versions_for(packet.providers_consulted_this_call)`) but never defined anywhere in
   Steps 1-6 — implemented as the natural, minimal completion of what those call sites need.
6. **`cache_key_version` is set to `_kgc.ROUTING_POLICY_VERSION`**, not `REPORTED_SCHEMA_VERSION`
   (Step 9's own text offered either, parenthetically: "or a new dedicated constant"). Reusing
   `REPORTED_SCHEMA_VERSION` would conflate two genuinely different version concepts (response
   *schema shape* vs. *cache-key derivation logic* version) — exactly the aliasing
   `tools/retrieval_cache.py`'s own `RETRIEVAL_VERSION`/`retrieval_cache_schema_version`/
   `retrieval_event_schema_version` three-way split (and its own dedicated regression test) already
   establishes as this repo's convention to avoid. `ROUTING_POLICY_VERSION` is the one already-real,
   already-computed identity field this ticket's own DD7 defines for exactly this purpose.
7. **`perform_cache_write()` now skips writing when `response["status"] == "PARTIAL"`** — not named
   anywhere in the plan's 13 steps. Discovered as a real regression during Implement: without this
   gate, a transient provider failure (e.g. graphify exiting non-zero) got cached and replayed
   verbatim on the next identical query, permanently masking a since-recovered provider until the
   row was evicted — concretely broke
   `tests/tools/test_knowledge_gateway_failure_semantics.py::test_graphify_nonzero_returncode_distinguished_from_legitimate_empty_result`,
   which issues the same query twice expecting two independently-computed outcomes. A PARTIAL
   result (budget-assembly failure or a real provider failure, per `assemble_packet()`'s own status
   derivation) is not a stable, cacheable outcome — a retry moments later may fully succeed. `OK`/
   `CONFLICTED` responses are still cached normally.
8. **`tests/tools/test_knowledge_gateway_failure_semantics.py` also gained the `_isolated_cache_db`
   autouse fixture** (patches `CACHE_DB_PATH`/`_MANIFEST_PATH`), beyond DD14's literal scope (which
   named only `tests/tools/test_knowledge_gateway_mcp.py`). Required because this file's
   `_run_knowledge_context()` calls now genuinely read/write the real Level 1 cache too — without
   isolation, its own sequential same-query test (item 7 above) would be flaky/order-dependent
   against the real on-disk cache file across repeated runs.
9. **Two pre-existing guard tests narrowed from a blind `"PRAGMA" not in source` check to
   specifically ban only `"PRAGMA journal_mode"`/`"PRAGMA busy_timeout"`**:
   `tests/docs/test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_implemented`
   and `tests/tools/test_knowledge_gateway_redaction.py::TestSqliteOperationalLimits::test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py`.
   Both guards' own stated purpose (block `tools/retrieval_cache.py` from re-implementing
   `open_connection_with_limits()`'s own connection-tuning logic locally) is fully preserved and
   still enforced. Neither anticipated DD3's own explicit, Architecture Review-confirmed
   instruction — "guarded by an explicit PRAGMA table_info idempotency check" — which necessarily
   puts one, real, literal `PRAGMA table_info(...)` SQL statement into
   `migration_003_add_redaction_policy_version_column`'s own body: a schema-introspection PRAGMA,
   unrelated to `journal_mode`/`busy_timeout` connection tuning. `busy_timeout`/`os.chmod`/`chmod`/
   `import os` bans are untouched and still absolute.
10. **`tests/tools/test_retrieval_cache.py::TestMigrations::test_new_table_column_set_matches_proposal_section_10_2_row_shape`
    updated to also apply `migration_003_add_redaction_policy_version_column` before comparing the
    live table's columns against `LEVEL1_CACHE_COLUMNS`.** A mechanical, unavoidable consequence of
    DD3 (Architecture Review-confirmed) growing `LEVEL1_CACHE_COLUMNS` to 22 entries — `migration_001`
    alone (the test's original scope) now produces a 21-column table, a strict, by-design subset
    (DD3's whole point is that `migration_001` itself stays untouched/frozen).
11. **`provider_result_cache_stats()`-driven rate formula for `knowledge_status`** (Step 10 left this
    undefined on purpose, requiring Implement to pick a real, test-observable formula):
    `cache_hit_rate = total_hits / (total_hits + total_rows)`,
    `cache_miss_rate = total_rows / (total_hits + total_rows)`,
    `cache_stale_rejection_rate = 0.0`. The last is a real, not fabricated, zero: this ticket's real
    schema/functions track no counter distinguishing "a served candidate was rejected by
    evidence-validity revalidation" from an ordinary no-cached-row miss (DD9/DD10's own
    mismatch-as-miss design collapses both into the same `MISS`/`None` outcome) — there is no other
    real count to divide by.
12. **Minor wording-only fixes to my own new comments/docstrings** in `tools/retrieval_cache.py` and
    `tools/knowledge_gateway_cache.py`, to avoid literal substrings (`"busy_timeout"`, `"freshness"`,
    `"verification"`, `"migration_002"`) that would otherwise trip pre-existing, unrelated guard
    tests in `tests/tools/test_evidence_cache_identity_contract.py` and
    `tests/tools/test_retrieval_cache.py::TestMigrations::test_migration_002_name_never_reused_or_stubbed`
    (a new test this ticket itself added, self-tripped by its own docstring wording on first run).
    No test assertions were weakened for any of these — only my own new prose was reworded.
13. **Gap fix, applied after Architecture-Verify flagged it (not part of the original Implement
    pass):** Step 8's own Verify list names two tests —
    `test_per_key_stampede_guard_prevents_concurrent_duplicate_write` and
    `test_size_cap_gate_skips_write_without_raising_when_db_over_ceiling` — that did not exist as
    genuine integration-level tests against `perform_cache_write()` itself when Implement's Test
    Summary was first written. `test_per_key_stampede_guard_prevents_concurrent_duplicate_write`
    existed only at `tests/tools/test_knowledge_gateway_redaction.py:431`, exercising
    `acquire_write_guard`/`release_write_guard` as bare primitives — never through
    `perform_cache_write()`, which is what Step 8's own parenthetical ("re-run against the real
    orchestrator, not just `knowledge_gateway_redaction.py`'s own unit test of the guard primitive")
    explicitly required. `test_size_cap_gate_skips_write_without_raising_when_db_over_ceiling` did
    not exist anywhere — the `if not rk.check_db_size_within_limit(rc.CACHE_DB_PATH): return` branch
    inside `perform_cache_write()` (`tools/knowledge_gateway_cache.py:289-290`) had zero test
    coverage. This is an honest oversight from the original Implement pass (both gates fail open, so
    the gap was silent rather than a functional break), not a deliberate omission — Implement's own
    Test Summary listed `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module`
    and the AST call-order guard as covering Step 8, but never actually ran the two named
    concurrency/size-cap tests against the real function.

    **Fix, both added to `tests/tools/test_knowledge_gateway_cache.py`:**
    - `test_per_key_stampede_guard_prevents_concurrent_duplicate_write` calls the real
      `perform_cache_write()` from two threads sharing the identical cache key. The first call is
      deliberately held inside its write step via a blocking replacement of
      `rc.write_provider_result_cache` (entered only after the real `rk.acquire_write_guard()` call
      inside `perform_cache_write()` itself succeeded); the second thread is started only once the
      first is confirmed inside the critical section, so its own `perform_cache_write()` call must
      genuinely observe the guard as held and return without ever reaching
      `rc.write_provider_result_cache()`. Asserts exactly one write call occurred.
    - `test_size_cap_gate_skips_write_without_raising_when_db_over_ceiling` replaces
      `rk.check_db_size_within_limit` (the real function `perform_cache_write()` calls through — not
      a reimplementation of the size logic, and not a real 256 MB `SQLITE_MAX_DB_SIZE_BYTES` DB file
      grown on disk) to return `False`, then calls `perform_cache_write()` directly and asserts it
      returns `None` without raising and without ever calling `rc.write_provider_result_cache`.

    Neither the stampede-guard nor the size-cap gate logic itself was weakened, removed, or altered
    to make these tests pass — both exercise the real, unmodified gates exactly as they existed
    before this fix. Full re-run of both of Test Summary's originally-reported scoped commands plus
    the new module file: 142 passed (unchanged) + 139 passed (was 137, +2) = 281 passed total (was
    279); domain sweep `pytest tests/tools/ -k "knowledge_gateway or retrieval_cache or
    evidence_cache"` now 255 passed (was 253, +2).

14. **Post-Security-Review fix cycle (2026-08-16), applied after Security-Review BLOCKED the
    ticket — not part of the original Implement pass, and not a plan-pseudocode deviation in the
    same sense as items 1-13 above, but recorded here per the same "never silently deviate"
    discipline.** Security-Review's stated blocking reason:
    `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §4/§11 requires the
    §4 secret-scan baseline to be "reviewed and expanded by a security-focused pass before Phase 2
    payload caching goes live" — and this ticket is precisely that go-live moment (the first ticket
    to make cache writes genuinely reachable from a live `knowledge_context` call). The reviewer
    named concrete gaps in the 4-pattern baseline shipped by the sibling
    `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH` (`tools/knowledge_gateway_redaction.py:121-128`):
    no named-service token formats (GitHub, Slack), no OpenAI/Anthropic API-key formats, no generic
    `password`/`secret`-named assignment (the existing pattern only covers `api[_-]?key`/`apikey`),
    no basic-auth-in-URL pattern. The reviewer characterized the fix as "narrow, not a redesign...
    small, bounded, low-effort given the existing dict-of-regexes shape" — the user explicitly
    authorized closing this ticket's own blocking gate by making that expansion.

    **Scope note on editing a sibling-owned file:** `tools/knowledge_gateway_redaction.py` is owned
    by `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH` (already DONE) — this plan's own Step list never
    named that file as one this ticket would edit. Editing it here is legitimate specifically
    because *this* ticket's own Security-Review gate (not the sibling's, whose Security-Review
    already passed and closed) names the sibling's pattern set as the blocking precondition — the
    precondition is phrased in terms of what must be true "before Phase 2 payload caching goes
    live," and this ticket is that go-live event. This mirrors the precedent already set this
    session by `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`, which legitimately edited files owned by
    prior, already-DONE sibling tickets (`tools/knowledge_gateway_packet_assembly.py`,
    `tools/knowledge_gateway_mcp.py`) when its own scope required it.

    **What changed:** `_SECRET_SCAN_PATTERNS` (`tools/knowledge_gateway_redaction.py`) grew from 4
    to 10 entries — `github_token`, `slack_token`, `openai_api_key`, `anthropic_api_key`,
    `generic_password_or_secret_assignment`, `basic_auth_in_url` added alongside the original 4.
    `openai_api_key`'s pattern (`sk-(?!ant-)[A-Za-z0-9]{20,}`) uses a negative lookahead
    specifically so an Anthropic key (`sk-ant-...`) is never double-matched, or mis-attributed, as
    an OpenAI key — verified by two new dedicated cross-match tests, not just asserted in prose.
    `check_never_cache_categories()`'s token-vs-credential classification (previously a bare
    `secret_match == "bearer_token"` check) was generalized to a new `_TOKEN_SHAPED_SECRET_PATTERNS`
    frozenset (`{"bearer_token", "github_token", "slack_token"}`) — a direct, mechanical consequence
    of adding two more named-service *token* patterns, not an independent design decision. The
    module docstring and `scan_for_secrets()` docstring were updated to record the expansion; the
    two literal phrases the existing test suite asserts on verbatim
    (`"not a production-complete secret scanner"`,
    `"security-focused pass before Phase 2 payload caching goes live"`) were deliberately preserved
    unchanged so `TestModuleDisclosure` and `tests/docs/test_redaction_retention_policy_doc.py`
    required no modification.

    `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §4's illustrative
    pattern table grew from 4 to 10 rows; §4 and §11 prose updated to record that the
    security-focused pass named as a precondition has now been performed, without claiming the
    baseline is production-complete — it is expanded, not perfected, and the doc says so explicitly.

    **Tests:** 14 new tests in `tests/tools/test_knowledge_gateway_redaction.py::TestSecretScan`
    (one detect + one reject-outright pair per new pattern, mirroring the existing 4 patterns'
    pairs exactly, plus 2 cross-match tests for the OpenAI/Anthropic boundary) and 2 new tests in
    `TestNeverCacheCategories` confirming the new patterns' token-vs-credential classification. No
    existing test was weakened, deleted, or had an assertion loosened.

    **Verification:** both of test_plan.md's Scoped Pytest Commands re-run green —
    `tests/tools/test_knowledge_gateway_mcp.py tests/tools/test_retrieval_cache.py
    tests/tools/test_knowledge_gateway_redaction.py tests/tools/test_evidence_cache_identity_contract.py`
    → 158 passed (was 142, +16); the second command (packet-assembly/router/failure-semantics/
    baseline/contract-schemas/policy-doc/cache) → 139 passed (unchanged — none of those files touch
    `tools/knowledge_gateway_redaction.py`). `tests/tools/test_knowledge_gateway_redaction.py` alone
    → 65 passed (was 51, +14). **New combined total: 297 passed (was 281, +16).** Domain sweep
    (`pytest tests/tools/ -k "knowledge_gateway or retrieval_cache or evidence_cache"`) → 271 passed
    (was 255, +16).
