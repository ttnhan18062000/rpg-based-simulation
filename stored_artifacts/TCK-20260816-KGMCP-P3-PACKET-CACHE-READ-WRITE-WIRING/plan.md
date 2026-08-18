---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING
artifact_type: plan
tags: [ai, mcp, security]
---

# Implementation Plan — TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING

## Summary

This plan wires a real Level 2 (assembled-packet) cache lookup/write path into
`_run_knowledge_context()`, checked before Level 1, reusing `revalidate_context_packet_row()`/
`_level2_repo_branch_scope()` (already shipped, unmodified) and adding two new orchestrator
functions (`perform_context_packet_cache_lookup()`/`perform_context_packet_cache_write()`) to
`tools/knowledge_gateway_cache.py`, plus real `check_context_packet_cache()`/
`write_context_packet_cache()` read/write functions to `tools/retrieval_cache.py`. It resolves the
three open items investigation.md flagged as explicit Plan Decisions (PD1-PD3 below), plus two
additional gaps this plan's own fact-verification pass surfaced while reading the real schema
(PD4-PD5) that were not previously flagged in investigation.md.

**Plan Decision PD1 (packet_id derivation, resolves investigation.md's "presumably not derivable"
framing of Risk 3).** `packet_id` is computed deterministically as a hash over the Level 2 lookup
identity fields, mirroring how Level 1's `query_hash` is deterministically derived from
`normalized_intent` alone (`tools/knowledge_gateway_cache.py:145,153`). This makes
`write_context_packet_cache()`'s `INSERT OR REPLACE` naturally idempotent per-identity (a repeat
identical request overwrites the same row instead of growing the table with a fresh UUID each time).
This does **not** remove the need for real multi-row disambiguation in `check_context_packet_cache()`
(PD3) — the lookup function still queries by the non-unique `query_key_hash` column, per
investigation.md Risk 3 / Anti-Drift Hazard and test_plan.md's own
`test_level2_lookup_disambiguates_multiple_rows_sharing_the_same_query_key_hash`; the two decisions
are complementary, not substitutes for each other.

**Plan Decision PD2 (budget-identity divergence, resolves Central Question 3).** Adopted as
investigation.md recommended: Level 2's own, new, additively-named lookup-identity function
(`compute_context_packet_lookup_identity()`) includes the literal `budget_tokens` integer, not
`budget_class`. This is confirmed the right call — `assemble_within_budget()`'s real truncation
behavior (per the dedup/budget sibling ticket) is driven by the literal integer, not the bucket, so
using only `budget_class` risks silently serving a wrongly-truncated packet across two different
budgets in the same bucket. Recorded as a new intentional-divergence entry (Step 7), mirroring the
precedent §2.44 already set.

**Plan Decision PD3 (Level 2 lookup disambiguation, resolves Risk 3).** `check_context_packet_cache()`
queries `SELECT * FROM retrieval_context_packet_cache_rows WHERE query_key_hash = ?` (`.fetchall()`,
never `.fetchone()`) and disambiguates in Python by comparing `normalized_intent`/`entity_ids`/
`repository_id`/`branch`/`budget_requested` against the caller's current identity — real logic, not
a placeholder, directly satisfying the ticket's own explicit test requirement.

**Plan Decision PD4 (new, this plan's own finding — Level 2 schema cannot faithfully reconstruct a
hit response without 3 more columns).** Reading `LEVEL2_CACHE_COLUMNS` (`tools/retrieval_cache.py:154-185`)
against the real response fields `_run_knowledge_context()` builds
(`tools/knowledge_gateway_mcp.py:243-255`) shows Level 2's schema has no column for
`budget_truncated`, `omitted_statement_count`, or `provider_failures` — all three exist on the live
response dict today, and a Level 2 "hit" that silently drops them (falling back to schema-optional
omission, since none of the three is `required` per `knowledge_context_response.schema.json:7-13`)
would not be a *genuine* hit as AC1 requires, and would fabricate-by-omission a
`budget_truncated: (absent)` result that could differ from what was actually assembled. This plan
folds these 3 columns into the same `migration_004` ordinal that closes the `redaction_policy_version`
gap (Step 1) — multiple columns per migration ordinal is already precedented by `migration_002`
adding 28 columns in one `CREATE TABLE`.

**Plan Decision PD5 (new, this plan's own finding — `mode` has no Level 2 column and needs none).**
`mode` is absent from `LEVEL2_CACHE_COLUMNS` entirely. Investigation's Risk 5 already established
`assemble_packet(routing_decision, query_text, budget_requested)`
(`tools/knowledge_gateway_packet_assembly.py:664`, confirmed 3-arg signature) never branches on
`mode` — it is a pure request-echo field. This plan does not add a `mode` column; instead, the
mcp.py hook site (Step 5) sets `hit_response["mode"]` from the *current* request, exactly mirroring
the existing miss-path pattern, which is more correct than replaying a possibly-stale stored value.

## Steps

### Step 1 — `migration_004`: close the `redaction_policy_version` gap and 3 write-fidelity gaps (PD4)
**Files:** `tools/retrieval_cache.py`
**Change:** Add `redaction_policy_version INTEGER`, `budget_truncated INTEGER`,
`omitted_statement_count INTEGER`, `provider_failures TEXT` to the `LEVEL2_CACHE_COLUMNS` frozenset
(currently 28 entries, `:154-185`, confirmed by direct read — none of these 4 names present),
mirroring the comment precedent already used for `LEVEL1_CACHE_COLUMNS`'s 22nd column
(`:138-141`, "added by migration_003..."). Add
`migration_004_add_level2_write_path_columns(conn)` immediately after
`migration_003_add_redaction_policy_version_column` (`:367-385`, read in full) — mirror its exact
idempotent pattern per column: `PRAGMA table_info(retrieval_context_packet_cache_rows)` existence
check, `ALTER TABLE ... ADD COLUMN <name> <TYPE>` only if absent, single `conn.commit()`. Ordinal 4
confirmed the next open one (no `migration_004_*` exists anywhere in the file today, grep-confirmed).
**Do NOT touch:** `migration_001_add_level1_tables`, `migration_002_add_level2_tables`,
`migration_003_add_redaction_policy_version_column`, `_init_schema`, `_get_connection`,
`LEVEL1_CACHE_COLUMNS`.
**Other writers to this shared resource:** `migration_001`/`migration_002`/`migration_003` are the
only other DDL writers in this file; this step is additive-only (`ALTER TABLE ADD COLUMN`) against
a table only `migration_002` has ever created, never touching Level 1's table or any row Level 1's
write path has already written. No other code path issues DDL against
`retrieval_context_packet_cache_rows`.
**Verify:** new unit test `test_migration_004_adds_redaction_policy_version_budget_truncated_omitted_statement_count_provider_failures_columns_idempotently` (`tests/tools/test_retrieval_cache.py`, mirrors the existing `TestMigrations`/migration_003 test pattern); `test_level2_write_stamps_redaction_policy_version_column` (test_plan.md, AC4).

### Step 2 — Level 2 connection helpers + real read/write/stats functions
**Files:** `tools/retrieval_cache.py`
**Change:**
- `_ensure_level2_schema_for_read()`: mirrors `_ensure_level1_schema_for_read()` (`:641-649`) exactly
  — plain `_get_connection()`, calls `migration_002_add_level2_tables(conn)` only (not migration_004,
  mirroring Level 1's own precedent of not calling `migration_003` from its read-ensure helper).
- `_get_level2_connection()`: mirrors `_get_level1_connection()` (`:700-709`) exactly —
  `_kgr_redaction.open_connection_with_limits(CACHE_DB_PATH)`, then
  `migration_002_add_level2_tables(conn)`, then `migration_004_add_level2_write_path_columns(conn)`.
- `ContextPacketCacheLookup` frozen dataclass (`status`, `reason_code`, `row`) mirrors
  `ProviderResultCacheLookup` (`:634-638`) exactly.
- `check_context_packet_cache(query_key_hash, *, normalized_intent, entity_ids_json, repository_id,
  branch, budget_tokens) -> ContextPacketCacheLookup` (PD3): `_ensure_level2_schema_for_read()`;
  `SELECT * FROM retrieval_context_packet_cache_rows WHERE query_key_hash = ?` — `.fetchall()`,
  **never** `.fetchone()` (`packet_id` is the real PK per `migration_002`'s `CREATE TABLE`, `:327`;
  `query_key_hash` is an ordinary, non-unique, unindexed column, `:329`, confirmed by direct read).
  Build each `row_dict` via the same `columns = [d[0] for d in conn.execute(...LIMIT 0).description]`
  + `dict(zip(columns, row))` pattern `check_provider_result_cache` already uses (`:680-687`).
  Compare `normalized_intent`/`entity_ids`/`repository_id`/`branch`/`budget_requested` against the
  caller's values; return the first exact match as `HIT`; if rows were returned but none matched,
  `MISS` with `reason_code="identity_mismatch_on_shared_key"` (mirrors `:694-696`'s reason code for
  the analogous Level 1 case); if zero rows returned, `MISS` with `reason_code="no_cached_row"`.
- `write_context_packet_cache(*, packet_id, normalized_intent, query_key_hash, entity_ids_json,
  answer, statements_json, context_items_json, evidence_json, conflicts_json,
  evidence_dependencies_json, provenance_providers_json, providers_consulted_this_call_json,
  repository_id, branch, head_commit, working_tree_fingerprint, provider_generations_json,
  policy_version, response_schema_version, budget_requested, budget_returned, status, freshness,
  verification, lifecycle, redaction_policy_version, budget_truncated, omitted_statement_count,
  provider_failures_json) -> None`: `conn = _get_level2_connection()`; single `INSERT OR REPLACE`
  covering every column of the post-`migration_004` `LEVEL2_CACHE_COLUMNS` set, `created_at=time.time()`,
  `hit_count=0`, `last_validated_at=NULL` — mirrors `write_provider_result_cache()`'s shape
  (`:712-750`) exactly, including its `conn.commit()`/`finally: conn.close()` structure.
  `head_commit`/`working_tree_fingerprint`/`lifecycle` accept `None` — nullable per `migration_002`'s
  `CREATE TABLE` (`:341-342`,`:351`, no `NOT NULL`, confirmed by direct read) — honest omission,
  mirroring `perform_cache_write()`'s own `validated_negative_scopes=None` precedent
  (`tools/knowledge_gateway_cache.py:387`).
- `record_context_packet_cache_hit(packet_id) -> None`: mirrors `record_provider_result_cache_hit()`
  (`:753-766`) exactly.
- `context_packet_cache_stats() -> dict`: mirrors `provider_result_cache_stats()` (`:769-791`) exactly
  — table-existence check via `sqlite_master`, returns `{"total_rows": 0, "total_hits": 0}` on a
  fresh/unmigrated DB (never raises).
**Do NOT touch:** `check_provider_result_cache`, `write_provider_result_cache`,
`record_provider_result_cache_hit`, `provider_result_cache_stats`, `_get_level1_connection`,
`_ensure_level1_schema_for_read`.
**Other writers to `retrieval_context_packet_cache_rows`:** none exist before this ticket
(`INFRA-348`'s own `support_boundary` text: "No Level 2 check_context_packet_cache()/
write_context_packet_cache() pair exists anywhere in the repo"). `write_context_packet_cache()` is
the sole writer this ticket introduces and, per Step 4's new AST guard, the sole writer this table
will ever have. `prune()` (`:805-827`) only touches the 3 legacy marker tables
(`_TABLE_NAME_BY_ALIAS`, `:798-802` — `index`/`query`/`packet`, not `context_packet`) and must not be
extended to include this table (Out of Scope: GC scheduling beyond the dependency ticket).
**Verify:** `TestLevel2Migrations::test_check_and_write_functions_now_exist_for_the_new_level2_table`
(replaces `test_no_actual_read_write_functions_added_for_the_new_level2_table`);
`test_level2_lookup_disambiguates_multiple_rows_sharing_the_same_query_key_hash`;
`test_level2_context_packet_cache_stats_function_never_raises_on_unmigrated_db` (AC6).

### Step 3 — Level 2 lookup identity + orchestration in `knowledge_gateway_cache.py`
**Files:** `tools/knowledge_gateway_cache.py`
**Change:**
- New `_current_branch() -> str`: additive helper, `subprocess.run(["git", "branch",
  "--show-current"], cwd=str(_REPO_ROOT), capture_output=True, text=True).stdout.strip() or
  "DETACHED"` — returns only the branch name (unlike `_current_repo_branch_scope()`, `:126-134`,
  which returns the combined `"{root}::{branch}"` string).
- New `compute_context_packet_lookup_identity(request, routing_decision, effective_budget) -> dict`
  (additively named per Anti-Drift Hazard — never touches `compute_lookup_identity()`'s existing
  6-field shape): `normalized_intent = rc._normalize_query(request["query"])` (reuse, `:145`
  precedent), `entity_ids_json = json.dumps(sorted(compute_resolved_entity_ids(routing_decision)))`
  (reuse `compute_resolved_entity_ids()`, `:113-123`, unmodified), `repository_id = str(_REPO_ROOT)`,
  `branch = _current_branch()`, `budget_tokens = effective_budget` (PD2), `query_key_hash =
  rc._hash_text(normalized_intent)` (reuse `rc._hash_text`, same function Level 1's `query_hash`
  derivation already reuses at `:153`), `packet_id = rc._hash_text(json.dumps({those 6 fields},
  sort_keys=True))` (PD1). Returns all 7 keys as a flat dict.
- New `_current_provider_generations_for(provider_ids) -> dict[str, str]`:
  `{pid: rc._corpus_generation() for pid in provider_ids}` — mirrors the exact value Level 1's write
  path already stamps into `provider_generation`/`provider_generation_at_validation`
  (`perform_cache_write()`, `:369,385,390`, all using the single `rc._corpus_generation()` value),
  reshaped into the per-provider dict `revalidate_context_packet_row()` consumes (`:274`).
- New `perform_context_packet_cache_lookup(request, routing_decision, effective_budget) -> dict |
  None`: compute identity; call `rc.check_context_packet_cache(...)`; on non-`HIT`, return `None`;
  else `stored_provider_ids = list(json.loads(lookup.row["provider_generations"]).keys())`,
  `current_provider_generations = _current_provider_generations_for(stored_provider_ids)`,
  `capability_descriptor = _capability_descriptor_for(routing_decision.providers_selected)` (reuse
  unmodified, `:169-183`); call `revalidate_context_packet_row(lookup.row, capability_descriptor=...,
  current_provider_generations=..., current_repository_id=identity["repository_id"],
  current_branch=identity["branch"], changed_paths=request.get("changed_paths", []))` (reuse
  unmodified, `:244-278` — this function already performs its own branch-compatibility check
  internally at `:259-260`, so this new lookup function must **not** duplicate an
  `is_branch_compatible()` call before it); on `False`, return `None`; else
  `rc.record_context_packet_cache_hit(identity["packet_id"])`, return
  `_context_packet_row_to_response(lookup.row)`.
- New `_context_packet_row_to_response(row) -> dict`: deserializes the row's typed/JSON columns into
  the same field names `_run_knowledge_context()`'s own `response` dict uses (`status`, `freshness`,
  `verification`, `provenance_providers`, `providers_consulted_this_call`, `answer`,
  `budget_requested`, `budget_returned`, `budget_truncated`, `omitted_statement_count`, `statements`,
  `context` [from `context_items`], `evidence`, `conflicts`), plus `provider_failures` only if that
  column is non-null (never a fabricated placeholder for a pre-Step-1 row). **Deliberately does not
  set `mode`** (PD5) — the mcp.py hook site (Step 5) supplies it from the current request instead.
- New `perform_context_packet_cache_write(request, routing_decision, response, effective_budget, *,
  evidence_dependencies) -> None`: mirrors `perform_cache_write()`'s structure (`:321-394`) exactly —
  same `PARTIAL`-status guard, same `raw_payload` construction (same
  `_RESPONSE_KEYS_EXCLUDED_FROM_CACHE_PAYLOAD` reused unmodified) and `evaluate_write_candidate()`
  verdict-gated early return, same `source_type` derivation line (no new source-type literal, Out of
  Scope). Uses a **distinct write-guard key namespace**, `f"level2:{identity['packet_id']}"` (vs.
  Level 1's `f"{query_hash}:{repo_branch_scope}"`, `:344`) — both share
  `rk._write_locks`/`acquire_write_guard()`/`release_write_guard()`
  (`tools/knowledge_gateway_redaction.py:345-364`, unmodified), so the distinct namespace prevents a
  Level 1 write and a concurrent Level 2 write for the same query from contending unnecessarily.
  Persists `provider_generations_json = json.dumps({pid: rc._corpus_generation() for pid in
  providers_consulted})`, `budget_requested=identity["budget_tokens"]`,
  `budget_truncated=response.get("budget_truncated")`,
  `omitted_statement_count=response.get("omitted_statement_count")`,
  `provider_failures_json=json.dumps(response["provider_failures"]) if
  response.get("provider_failures") else None`,
  `evidence_dependencies_json=json.dumps(sorted(evidence_dependencies))`, `head_commit=None`/
  `working_tree_fingerprint=None`/`lifecycle=None` (honest omissions, Step 2 rationale),
  `response_schema_version=CONTEXT_PACKET_RESPONSE_SCHEMA_VERSION` — new local module constant `= 1`,
  mirrors `ROUTING_POLICY_VERSION`'s own local-constant pattern (`:79`). **Must not** import
  `tools.knowledge_gateway_mcp.REPORTED_SCHEMA_VERSION` — `knowledge_gateway_mcp.py` is the module
  that loads `knowledge_gateway_cache.py` via sibling-loading, not the reverse; importing it back
  would be circular.
**Do NOT touch:** `compute_lookup_identity()`, `_current_repo_branch_scope()`,
`perform_cache_lookup()`, `perform_cache_write()`, `revalidate_cache_row()`,
`revalidate_context_packet_row()`, `_level2_repo_branch_scope()`, `is_branch_compatible()`,
`_capability_descriptor_for()`, `compute_resolved_entity_ids()`.
**Other writers to shared resources:** `rk._write_locks`/`acquire_write_guard`/`release_write_guard`
— the only other writer/reader is Level 1's `perform_cache_write()` (`:345,394`), keyed differently
(`f"{query_hash}:{repo_branch_scope}"`), so no collision between namespaces is possible; both share
the same in-process dict, which is safe since the guard is keyed per-string. `CACHE_DB_PATH` — shared
by both Level 1 and Level 2 connections, both via the same WAL-mode `open_connection_with_limits()`
(`:311-327`, unmodified); each level already serializes its own writes independently via its own
guard key, so no new locking contract is introduced.
**Verify:** `test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit` (AC1),
`test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh` /
`test_level2_hit_rejected_on_provider_generation_bump_real_call` (AC3),
`test_level2_cached_result_from_feature_branch_not_served_on_different_branch` (AC5),
`test_level2_lookup_function_never_returns_a_freshness_or_verification_field` (§2.44 obligation).

### Step 4 — Architecture guard: no bypass path for Level 2 writes (AC4)
**Files:** `tests/tools/test_knowledge_gateway_cache.py`
**Change:** Add `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`
(exact name per test_plan.md), mirroring the existing
`test_no_raw_insert_statement_bypasses_redaction_anywhere_in_cache_module`'s AST-based technique:
assert no `.execute(`/`sqlite3` literal appears in `tools/knowledge_gateway_cache.py`'s source
(true after Step 3 — all real SQL stays in `tools/retrieval_cache.py`, per this module's own
docstring, `:10-13`, unmodified); assert `rc.write_context_packet_cache` is called from exactly one
place across `tools/*.py`; assert `rk.evaluate_write_candidate` precedes
`rc.write_context_packet_cache` in source order with an intervening `decision.verdict`-gated early
return.
**Do NOT touch:** the existing Level 1 version of this test.
**Verify:** itself, run against Step 3's real diff.

### Step 5 — Level 2 hooks in `_run_knowledge_context()`
**Files:** `tools/knowledge_gateway_mcp.py`
**Change:** Two insertions into `_run_knowledge_context()` (`:149-331`), no other lines touched:
(a) Immediately **before** the existing Level 1 cache-check hook (currently `:227-232`), insert a
new Level 2 cache-check hook, wrapped in the same fail-open `try/except Exception` discipline: call
`_kgc.perform_context_packet_cache_lookup(request, routing_decision, effective_budget)`; on a
non-`None` result, `hit_response = dict(cached_packet)`; set `hit_response["mode"] = mode` if `mode
is not None` (PD5 — Step 3's `_context_packet_row_to_response()` deliberately omits `mode`); set
`hit_response["cache"] = "HIT_L2"` (schema-valid: `cache` is `"type": "string"`, no closed enum,
`docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json:28-31`,
confirmed by direct read — no schema change needed for this field); set
`hit_response["cache_key_version"] = _kgc.ROUTING_POLICY_VERSION`; validate; **return early** —
before `assemble_packet()` (`:241`) and before the existing Level 1 lookup hook, satisfying AC1's
literal "never reaches packet assembly or the Level 1 lookup at all."
(b) Immediately **after** `response["cache"] = "MISS"` (currently `:323`) and **before** the
existing Level 1 cache-write hook (currently `:324-328`), insert a new Level 2 cache-write hook in
its **own separate** fail-open `try/except Exception` block (kept separate from the Level 1 write's
own try/except, so a Level 2 write failure can never suppress the Level 1 write, and vice versa —
Risk 6's "both writes happen on one full miss" requirement): call
`_kgc.perform_context_packet_cache_write(request, routing_decision, response, effective_budget,
evidence_dependencies=packet.evidence_dependencies)` (`packet` is already in scope from `:241`;
`packet.evidence_dependencies` is a plain `list[str]` field,
`tools/knowledge_gateway_packet_assembly.py:627`, confirmed present — not the `PacketAssembly`
object itself, satisfying the "no live PacketAssembly import into knowledge_gateway_cache.py"
constraint).
**Do NOT touch:** the router-failure fallback block (`:192-220`), the existing Level 1 hooks' own
internal bodies (only the call-site sequence around them changes), `_git_branch_scope()`.
**Other writers to the `response` dict / call sequence:** none besides `_run_knowledge_context()`
itself. The existing Level 1 write hook (`:324-328`, unmodified internally, now second in sequence)
is the other writer of a cache row on this same miss path — this step ensures both writes are
attempted independently and neither's failure blocks the other.
**Verify:** `test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit` (AC1,
spies confirm neither `assemble_packet` nor `perform_cache_lookup` is called on the hit path);
`test_level2_miss_falls_through_to_unmodified_level1_lookup` (AC2);
`test_level2_write_reject_verdict_results_in_zero_rows_written` (AC4);
`test_level2_double_write_on_full_miss_writes_both_level1_and_level2_rows` (Risk 6);
`test_cache_layer_failure_is_fail_open_and_never_blocks_the_provider_path` (regression, must pass
with 2 independent fail-open hooks instead of 1).

### Step 6 — `knowledge_status` Level 2 fields (AC6)
**Files:** `tools/knowledge_gateway_mcp.py`,
`docs/engine/contracts/knowledge_gateway_mcp/knowledge_status_response.schema.json`
**Change:** In `_run_knowledge_status()` (`:350-414`), after the existing Level 1 `stats =
_load_cache_module().rc.provider_result_cache_stats()` block (`:395-411`, unmodified), add:
`level2_stats = _load_cache_module().rc.context_packet_cache_stats()`; `if level2_stats["total_rows"]
> 0:` append `{"kind": "context_packet", "count": level2_stats["total_rows"]}` to
`response.setdefault("cache_entry_counts", [])` (additive array item — the item shape
`kind`/`freshness`/`count` already permits an arbitrary `kind` string, no schema change needed for
this part, `docs/engine/contracts/knowledge_gateway_mcp/knowledge_status_response.schema.json:27-37`);
set `response["level2_cache_hit_rate"]`/`response["level2_cache_miss_rate"]` from the same
hit/(hit+row) ratio formula Level 1 already uses (`:405,409-410`, unmodified formula, applied to
`level2_stats`). If either level has `total_rows > 0`, set `response["cache_hit_attribution"] =
{"level1_hits": stats["total_hits"] if stats["total_rows"] > 0 else 0, "level2_hits":
level2_stats["total_hits"] if level2_stats["total_rows"] > 0 else 0}`. Never fabricate these 3 new
fields when Level 2 has zero rows — omit entirely, mirroring this function's own
"never a fabricated `0`/`null`/`{}` placeholder" discipline (`:358-359`).
Schema change (additive only — `additionalProperties: false` at the top level, `:7`, confirmed by
direct read, so new top-level keys require explicit declarations): add
`"level2_cache_hit_rate": {"type": "number"}`, `"level2_cache_miss_rate": {"type": "number"}`,
`"cache_hit_attribution": {"type": "object", "properties": {"level1_hits": {"type": "integer"},
"level2_hits": {"type": "integer"}}}` to `properties` (after `cache_stale_rejection_rate`, `:40`). No
`schema_version` bump — mirrors the dedup/budget sibling ticket's own precedent of adding
`budget_truncated`/`omitted_statement_count` to a sibling response schema without a version bump.
**Do NOT touch:** `gateway_version`/`reported_schema_version`/`providers`/`branch_scope`
construction (`:383-388`), `_git_branch_scope()`, the existing Level 1 block's own formula/omission
logic (`:395-411`) beyond appending after it.
**Other writers to this schema file:** none — this status-response schema file has never been
touched by any prior Phase-3 sibling ticket (the dedup/budget sibling touched
`knowledge_context_response.schema.json`, a different file, cited only as a naming precedent).
`_run_knowledge_status()` is the sole writer of the `response` dict this schema validates against.
**Verify:** `test_knowledge_status_reports_real_level2_cache_entry_counts_and_rates_distinct_from_level1`
(AC6); `test_knowledge_status_level2_fields_omitted_when_level2_cache_has_zero_rows` (AC6);
`test_knowledge_status_reports_real_cache_entry_counts_and_rates_after_writes` (regression, Level 1
fields unchanged in shape); `test_knowledge_status_omits_all_cache_specific_fields_enumerated`
(regression, update per test_plan.md's own note, not delete).

### Step 7 — `intentional_divergences.md` §2.45 (PD2)
**Files:** `docs/guidelines/intentional_divergences.md`
**Change:** Add `### 2.45 Level 2 Lookup Identity Includes Exact budget_tokens, Not budget_class
(TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING)` immediately after `### 2.44` (ends at line
1282's `- **Status**: ACTIVE`, before the `---`/`## 3.` section break at `:1284-1286`, confirmed by
direct read). Content: **Old Behavior** — `evidence_cache_identity_contract.md` §1
(`docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md:43`, confirmed)
states `budget_class` is "the caller's budget tier ..., not the raw numeric budget"; Level 1's
`compute_lookup_identity()` (`tools/knowledge_gateway_cache.py:137-154`, unmodified) follows this
literally. **New Behavior** — Level 2's `compute_context_packet_lookup_identity()` (Step 3) includes
the literal `budget_tokens` integer in `packet_id`'s hash input and in
`check_context_packet_cache()`'s disambiguation comparison. **Rationale: Bounded** —
`assemble_within_budget()`'s truncation is driven by the literal `effective_budget` integer, not
`budget_class`'s bucket (thresholds 500/2000, `tools/knowledge_gateway_cache.py:85-94`); two
requests in the same bucket can produce differently-truncated packets; §1 predates Level 2's
existence. Bounded because the divergence is scoped only to Level 2's new identity function — Level
1's `compute_lookup_identity()` is unmodified. **Verification** —
`test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit` (AC1) plus a new
negative-case test asserting two calls differing only in `budget_tokens` within the same
`budget_class` bucket do not collide on the same Level 2 row. **Status**: ACTIVE.
**Do NOT touch:** entries `2.1`-`2.44`, the `## 3. Unsupported / Retired Behavior` section or
anything below it.
**Verify:** no pytest test — reviewed by Architecture Review / Finalize (divergence docs are not
pytest-checked).

### Step 8 — Parity ledger entry `INFRA-349` (AC8)
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Add `id: INFRA-349`, mirroring `INFRA-348`'s real shape (`:9659` onward, read in full):
`status: verified`, `priority: P1` (no P0 entries exist anywhere in this KGMCP subsystem, confirmed
by grep), `text:` describing the Level 2 lookup/write functions added in Steps 1-6, `legacy_evidence:
null`, `v2_evidence:` real `file:line` citations against the actual landed diff (filled in by
Implementer/parity-updater post-implementation, not pre-guessed here), `proof_type: regression`,
`test_path:` the tests enumerated in Steps 1-6's Verify lines, `divergence_note:` pointing to the
new `intentional_divergences.md` §2.45 entry (Step 7), `support_boundary:` stating this ticket makes
`revalidate_context_packet_row()`/`_level2_repo_branch_scope()` reachable from a live call path for
the first time (discharging `INFRA-348`'s "not yet reachable" framing) and that
`tools/knowledge_gateway_router.py` was not touched.
**Do NOT touch:** `INFRA-341`, `INFRA-343`, `INFRA-346`, `INFRA-347`, `INFRA-348` (precedent only).
**Verify:** parity-ledger schema validation tooling (`docs/parity_ledger/schema.json`-based check),
not a pytest test.

### Step 9 — Mark §20 Phase 3's "Store and return actual packet payloads" bullet Done
**Files:** `docs/plans/knowledge-gateway-mcp-proposal.md`
**Change:** Mark §20 Phase 3's second bullet **Done**, citing this ticket ID — the one bullet
investigation.md confirmed genuinely originates in this ticket (unlike the 2 sibling bullets, which
the dedup/budget ticket already marked as hardening pre-existing capability).
**Do NOT touch:** any other §20 bullet or phase section.
**Verify:** none (doc-only, reviewed by doc-updater/Finalize).

### Step 10 — Scope guard: router byte-unchanged (AC7)
**Files:** `tests/tools/test_knowledge_gateway_mcp.py`
**Change:** Add `test_knowledge_gateway_router_py_provably_untouched`, mirroring the existing
`test_search_mcp_py_provably_untouched`'s content-hash/`git diff`-based technique. Add this test
first (or run it continuously across Steps 1-9) so any accidental edit to
`tools/knowledge_gateway_router.py` is caught immediately, not only at the end.
**Do NOT touch:** `tools/knowledge_gateway_router.py` itself, under any circumstance, in any step.
**Verify:** itself; re-run after every other step as a standing guard.

## Scope Guards

- `tools/knowledge_gateway_router.py` stays byte-unchanged — enforced continuously by Step 10 (AC7).
- `tools/knowledge_gateway_packet_assembly.py` is never imported by `tools/knowledge_gateway_cache.py`
  — enforced by the existing, unmodified
  `test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`.
- `compute_lookup_identity()`, `_current_repo_branch_scope()`, `perform_cache_lookup()`,
  `perform_cache_write()`, `revalidate_cache_row()`, `revalidate_context_packet_row()`,
  `_level2_repo_branch_scope()`, `is_branch_compatible()` — all Level 1/Level 2-revalidation
  functions this ticket calls but never edits (Steps 3, 5).
- `check_provider_result_cache`, `write_provider_result_cache`, `record_provider_result_cache_hit`,
  `provider_result_cache_stats`, `_get_level1_connection`, `_ensure_level1_schema_for_read`,
  `migration_001_add_level1_tables`, `migration_002_add_level2_tables`,
  `migration_003_add_redaction_policy_version_column` — all Level 1 read/write/migration functions
  (Steps 1, 2).
- `evaluate_write_candidate()`, `redact_content()`, `scan_for_secrets()`, `check_size_cap()`,
  `check_never_cache_categories()`, `ALLOWED_SOURCE_TYPES`/`SOURCE_TYPE_*` constants — reused as-is,
  no new source-type literal invented (Step 3).
- `prune()` and `_TABLE_NAME_BY_ALIAS` — never extended to include
  `retrieval_context_packet_cache_rows` (Out of Scope: GC scheduling beyond the dependency ticket).
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` and
  `evidence_cache_identity_contract.md` — frozen, design-only; never edited (divergences recorded in
  `intentional_divergences.md` instead, Step 7).
- `knowledge_context_response.schema.json`'s `cache` field — no schema edit; `"HIT_L2"` is
  schema-valid as-is (open string, no enum).
- `docs/parity_ledger/infrastructure.yaml`'s existing entries `INFRA-341`/`INFRA-343`/`INFRA-346`/
  `INFRA-347`/`INFRA-348` — cited, never edited.

## Dependency Map

- Step 1 → Step 2 (Level 2 read/write functions reference `migration_004`'s columns and
  `_get_level2_connection()`/`_ensure_level2_schema_for_read()`).
- Step 2 → Step 3 (orchestration functions call `rc.check_context_packet_cache`/
  `rc.write_context_packet_cache`/`rc.record_context_packet_cache_hit`).
- Step 3 → Step 4 (the AST guard test asserts against Step 3's real module diff).
- Step 3 → Step 5 (the mcp.py hooks call Step 3's orchestrator functions).
- Step 2 → Step 6 (knowledge_status calls `rc.context_packet_cache_stats()`).
- Step 3 → Step 7 (the divergence entry documents Step 3's `compute_context_packet_lookup_identity()`
  design).
- Steps 1-7 → Step 8 (the parity ledger entry documents the full landed diff).
- Step 5 → Step 9 (the proposal bullet is only markable Done once the live wiring actually lands).
- Step 10 is independent and should run continuously alongside every other step, not only at the end.
- Steps 1, 4 (test-only addition against Step 3), 6, 7, 9, 10 have no dependency on each other beyond
  what is listed above and may be implemented/verified in any relative order once their stated
  prerequisite step has landed.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — identical repeated call is a genuine Level 2 hit, never reaching assembly or Level 1 lookup | Steps 3, 5 | `test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit` |
| AC2 — Level 2 miss falls through to Level 1's unmodified lookup | Steps 3, 5 | `test_level2_miss_falls_through_to_unmodified_level1_lookup` |
| AC3 — Level 2 hit rejected/refreshed when dependency-invalidation logic determines staleness | Steps 2, 3 | `test_level2_hit_rejected_on_changed_paths_intersection_triggers_real_refresh`, `test_level2_hit_rejected_on_provider_generation_bump_real_call` |
| AC4 — Level 2 writes independently verified through redaction/secret-scan/size-cap, no bypass | Steps 1, 2, 3, 4 | `test_level2_cache_write_calls_evaluate_write_candidate_before_any_insert`, `test_no_raw_insert_statement_bypasses_redaction_anywhere_in_level2_cache_module`, `test_level2_write_reject_verdict_results_in_zero_rows_written`, `test_level2_write_stamps_redaction_policy_version_column`, `test_level2_write_respects_max_payload_bytes_size_cap_with_real_measured_packet` |
| AC5 — branch/working-tree scope enforced before a Level 2 hit is served | Steps 2, 3 | `test_level2_cached_result_from_feature_branch_not_served_on_different_branch` |
| AC6 — `knowledge_status` Level 2 fields real/populated/distinct from Level 1 | Step 6 | `test_knowledge_status_reports_real_level2_cache_entry_counts_and_rates_distinct_from_level1`, `test_knowledge_status_level2_fields_omitted_when_level2_cache_has_zero_rows`, `test_level2_context_packet_cache_stats_function_never_raises_on_unmigrated_db` |
| AC7 — `tools/knowledge_gateway_router.py` remains byte-unchanged | Step 10 | `test_knowledge_gateway_router_py_provably_untouched` |
| AC8 — real, schema-valid `infrastructure.yaml` entry added | Step 8 | parity-ledger schema validation tooling (not pytest) |

## Anti-Drift Notes

- Do not modify `revalidate_context_packet_row()`, `_level2_repo_branch_scope()`,
  `compute_lookup_identity()`'s existing 6-field shape, `perform_cache_lookup()`, or
  `perform_cache_write()` — every Level 2 identity/orchestration addition is a new, additively-named
  function.
- `perform_context_packet_cache_lookup()` must not duplicate `is_branch_compatible()` before calling
  `revalidate_context_packet_row()` — that function already performs the branch check internally
  (`:259-260`); duplicating it is redundant, not merely wasteful — a future edit that only updates one
  of the two copies would silently create divergent branch-check logic.
- `check_context_packet_cache()` must never collapse to a `fetchone()` — `packet_id` is the real PK,
  `query_key_hash` is not unique; a naive single-row fetch on a shared `query_key_hash` risks silently
  returning the wrong row across two different branches or budgets.
- The new Level 2 lookup function (`perform_context_packet_cache_lookup()`) must never return the raw
  `freshness`/`verification` row values without `revalidate_context_packet_row()` having run first —
  this is a named, inherited obligation from `intentional_divergences.md` §2.44's own Verification
  clause, not optional coverage.
- No new `source_type` literal for Level 2 writes — reuse the same 2-literal allowlist
  (`context_search`/`graphify`) and the same provider-selection logic Level 1's
  `perform_cache_write()` already uses.
- The 2 mcp.py fail-open hooks (Level 2 lookup, Level 2 write) must each be wrapped in their own
  independent `try/except Exception` block, separate from the Level 1 hooks' own try/except blocks —
  a Level 2 failure must never suppress or be suppressed by a Level 1 outcome on the same call.
- `mode` is never persisted to a Level 2 row and never read back off one (PD5) — it is set on the hit
  response from the current request only.
- `response_schema_version` for Level 2 writes uses a new local constant in
  `knowledge_gateway_cache.py`, never an import of `tools.knowledge_gateway_mcp.REPORTED_SCHEMA_VERSION`
  (would be circular — `knowledge_gateway_mcp.py` loads `knowledge_gateway_cache.py`, not the
  reverse).
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` and
  `evidence_cache_identity_contract.md` are frozen and design-only — the new migration (Step 1) and
  the budget-identity extension (PD2/Step 7) are recorded via `intentional_divergences.md` instead of
  edits to either frozen doc.
- `knowledge_status_response.schema.json`'s new fields (`level2_cache_hit_rate`,
  `level2_cache_miss_rate`, `cache_hit_attribution`) are additive only, no `schema_version` bump,
  consistent with the established `budget_truncated`/`omitted_statement_count` precedent on the
  sibling response schema.

## Deviations (Implement phase, discovered via real test execution)

1. **`_get_level2_connection()`/`_ensure_level2_schema_for_read()` must also call
   `migration_001_add_level1_tables(conn)` before `migration_002_add_level2_tables(conn)` — Step
   2's literal text ("mirrors `_get_level1_connection()` exactly — `migration_002` then
   `migration_004`") omitted this and caused a real, test-caught failure
   (`sqlite3.OperationalError: no such table: retrieval_cache_generation`).
   `migration_002_add_level2_tables()` itself assumes `retrieval_cache_generation` already exists
   (created only by `migration_001` — documented by `TestLevel2Migrations`'s own class docstring:
   "the real chain this module's own production caller uses today is `migration_001` ->
   `migration_003` -> `migration_002`"). Level 2 is now itself a production caller of
   `migration_002`, reached via a hook that runs *before* the Level 1 hooks (Step 5) — on a
   genuinely fresh DB the very first call would hit this missing-table error inside the fail-open
   try/except, silently preventing Level 2 from ever bootstrapping its own schema. Fixed by adding
   `migration_001_add_level1_tables(conn)` as the first call in both functions (not
   `migration_003` — that migration only touches the Level 1 table, irrelevant here). Both new
   functions' docstrings document this explicitly. Discovered and fixed during real
   `pytest`-execution of the new `tests/tools/test_retrieval_cache.py::TestContextPacketCache`
   tests, not silently routed around.

2. **`test_new_level2_table_column_set_matches_proposal_section_10_3_cachedpacket_field_list`**
   (pre-existing, `tests/tools/test_retrieval_cache.py`) required updating to also run
   `migration_004_add_level2_write_path_columns(conn)` before comparing the live table's column set
   against `LEVEL2_CACHE_COLUMNS` — mirrors the exact precedent
   `test_new_table_column_set_matches_proposal_section_10_2_row_shape` already set for Level 1's
   own `migration_003` widening. `LEVEL2_CACHE_COLUMNS` now includes the 4 columns
   `migration_004` adds, so `migration_002` alone (the test's original scope) is a strict subset by
   design, not a stale assertion routed around.

3. **Five pre-existing Level 1-scoped regression tests in
   `tests/tools/test_knowledge_gateway_mcp.py`** needed real updates, not silent breakage, because
   Level 2 is now checked *before* Level 1 (this ticket's entire point) and therefore genuinely
   changes what an unmodified repeat call demonstrates:
   - `test_identical_repeated_knowledge_context_call_is_a_genuine_cache_hit`,
     `test_cached_result_from_feature_branch_not_served_on_different_branch`,
     `test_new_commit_alone_does_not_force_cache_miss_when_evidence_unchanged`,
     `test_knowledge_status_reports_real_cache_entry_counts_and_rates_after_writes` — each now
     force Level 2's lookup (and, for the `knowledge_status` test, also Level 2's write) to a
     no-op via `monkeypatch.setattr(kgc_mod, "perform_context_packet_cache_lookup", lambda *a,
     **k: None)`, so the test continues to exercise Level 1's own unmodified hit/branch-scope/
     stats mechanics specifically, exactly as it did before this ticket — the dedicated Level
     2-specific versions of each are new, separately-named tests per test_plan.md's own AC map.
   - `test_cache_write_calls_evaluate_write_candidate_before_any_insert` — updated from asserting
     `calls == [1]` to `calls == [1, 1]`: `evaluate_write_candidate()` is now genuinely called
     twice on a real full miss (once for the Level 2 write, which runs first, and once for the
     Level 1 write immediately after — Risk 6's own explicitly-required double-write behavior).
     The assertion that it precedes any real Level 1 `INSERT` (`provider_result_cache_stats()`
     `total_rows == 0` inside the spy) still holds on both calls and remains unmodified in
     substance.
   All five changes were driven by real `pytest` failures surfaced while running the test suite,
   not anticipated in advance — recorded here per CLAUDE.md's never-silently-deviate rule.
