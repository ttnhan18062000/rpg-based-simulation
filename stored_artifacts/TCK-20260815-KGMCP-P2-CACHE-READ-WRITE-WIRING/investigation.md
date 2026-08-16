---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING

## Current Behavior

### `tools/knowledge_gateway_mcp.py` (the request-handling hook point — read in full, 418 lines)

`_run_knowledge_context()` (`tools/knowledge_gateway_mcp.py:139-287`) is a single flat function with
no wrapper layer today:

1. Builds `request: dict` from only the non-`None` supplied args (`:152-162`).
2. Validates it against `REQUEST_SCHEMA` via `REQUEST_VALIDATOR.validate()`; on failure returns an
   `ERROR` response immediately (`:164-176`).
3. Loads the router/packet-assembly sibling modules via `importlib.util` (`:178-179`, the same
   pattern `_load_router_module()`/`_load_packet_assembly_module()`/`_load_search_mcp_module()`
   already use 3×).
4. Calls `_kgr.route(query)` (`:183`) — catches `FileNotFoundError`/`subprocess.TimeoutExpired` and
   returns a `PARTIAL` fallback response (`:184-208`).
5. Calls `_kgpa.assemble_packet(routing_decision, query, effective_budget)` (`:210`).
6. Builds `response: dict` field-by-field from the returned `PacketAssembly` (`:212-284`).
7. Validates against `RESPONSE_SCHEMA` and returns (`:286-287`).

`_run_knowledge_status()` (`:306-343`) is Phase-1-scoped: builds `providers`/`branch_scope` only,
never emits any cache-domain field, and its own docstring says so explicitly ("no cache exists yet").

**Two natural hook points, minimally invasive to this flow:**
- **Cache-check**: after step 2 (request validated) and before step 4 (`_kgr.route(query)`) —
  right after `:179`, before `:183`.
- **Cache-write**: after step 6 (`response` dict fully built) and before step 7's
  `RESPONSE_VALIDATOR.validate(response)` — right before `:286`.

Neither hook point requires restructuring steps 3–6; the existing dict-building/schema-validation
code stays untouched.

**Resolution of the ticket's own open question (hook placement):** a **new sibling module**,
following the `knowledge_gateway_*` naming precedent `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`
already established (its own plan.md DD1: `tools/knowledge_gateway_redaction.py`), loaded via the
exact same `importlib.util` sibling-loading idiom `_load_router_module()`/`_load_packet_assembly_module()`
already use 3× in this file — e.g. `_load_cache_module()` returning a module at
`tools/knowledge_gateway_cache.py` (exact name is a Plan-phase naming call). This module owns:
lookup-identity computation (contract §1), evidence-validity revalidation (contract §2/§3/§4),
branch/working-tree scope (contract §5/§12.3), and the redaction-orchestrated real write
(`knowledge_gateway_redaction.evaluate_write_candidate()` + a real `INSERT`). `_run_knowledge_context()`
itself gains exactly 2 new call-outs at the 2 hook points above — not a rewrite, not a proxy that
wraps the whole function. Reasoning: `tools/knowledge_gateway_packet_assembly.py` is explicitly
Out-of-Scope (its own guard tests `test_module_does_not_modify_or_import_retrieval_cache` and
`test_module_does_not_edit_knowledge_gateway_router` confirm it currently has zero cache
relationship and this ticket must not create one there), so the cache-check/cache-write logic
cannot live in the assembler; putting it in a brand-new dedicated module (rather than inlining ~150
lines of identity/validation/redaction-orchestration logic directly into
`_run_knowledge_context()`) keeps that function's existing, already-tested control flow legible and
matches this subsystem's own established pattern of one module per concern
(`knowledge_gateway_router.py`, `knowledge_gateway_packet_assembly.py`,
`knowledge_gateway_redaction.py`, each single-purpose).

**Confirmed NOT banned from editing:** `tests/tools/test_knowledge_gateway_mcp.py::test_search_mcp_py_provably_untouched`
(`:170-183`) bans exactly 4 paths — `tools/search_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, `tools/retrieval_events.py`. `tools/knowledge_gateway_mcp.py`
itself and `tools/retrieval_cache.py` are absent from that tuple — both are legitimately editable by
this ticket. Separately, `tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_introduced`
(confirmed by direct read, current tuple: `tools/search_mcp.py`, `tools/hybrid_retrieval.py`,
`tools/context_packet_assembler.py`, `tools/retrieval_events.py`) also excludes both files — this
was already narrowed by `CACHE-SCHEMA-MIGRATIONS`'s own Step 6 (removing `tools/retrieval_cache.py`
permanently, not ticket-window-scoped back).

### `tools/retrieval_cache.py` (628 lines, current post-migrations-ticket state, read in full)

- `LEVEL1_CACHE_COLUMNS` (`:104-128`): 21 columns, confirmed by direct read — no
  `redaction_policy_version` column (see Risks).
- `migration_001_add_level1_tables(conn)` (`:198-248`): creates
  `retrieval_provider_result_cache_rows` (PK `(query_hash, repo_branch_scope)`) plus
  `retrieval_cache_generation`. **Not called by `_get_connection()`, `_init_schema()`, or any
  existing `check_*_cache()`/`write_*_cache()`/`prune()` function** — confirmed by direct read and
  by the existing guard test `TestMigrations::test_migration_001_function_is_never_called_from_any_check_or_write_function`
  (`tests/tools/test_retrieval_cache.py:406-410`), which `inspect.getsource()`s exactly the 6
  *existing* functions (`check_index_cache`, `write_index_cache`, `check_query_cache`,
  `write_query_cache`, `check_packet_cache`, `write_packet_cache`) and asserts `"migration_001"`
  is absent from each. **This guard does not, and cannot, cover a brand-new function this ticket
  adds** — so a new `check_provider_result_cache()`/`write_provider_result_cache()` pair (this
  ticket's own job, the natural home being `tools/retrieval_cache.py` itself, following the exact
  established pattern of the other 3 check/write pairs) is free to call
  `migration_001_add_level1_tables(conn)` at its own top, idempotently (`CREATE TABLE IF NOT EXISTS`),
  the same way `_get_connection()` already unconditionally calls `_init_schema()` on every connect
  for the 3 marker-only tables. This is the concrete mechanism by which the Level 1 table becomes
  guaranteed-present the first time this ticket's real code path runs, without violating
  `cache_migration_plan.md` §5's "no auto-apply-`migrate`-on-connect" freeze (that freeze is about
  not folding `migration_001` into the *generic*, all-tables `_init_schema()`/`_get_connection()`
  path — not about a table-specific new function guaranteeing its own table exists).
- No `check_provider_result_cache()`/`write_provider_result_cache()`-style function exists yet for
  the Level 1 table — confirmed by direct read. This ticket must add both.
- `CACHE_DB_PATH: Path = Path("knowledge-index/retrieval_cache.db")` (`:59`) — the single real file;
  `_get_connection()` (`:135-144`) is the sole existing opener, 8 call sites, zero `PRAGMA`,
  `busy_timeout`, or file-permission code (unchanged since the redaction ticket's own investigation
  confirmed this).

### `tools/knowledge_gateway_redaction.py` (403 lines, read in full — this ticket's other dependency)

Pure functions only, confirmed by direct read: `check_allowlist()`, `redact_content()`,
`scan_for_secrets()`, `check_size_cap()`, `check_never_cache_categories()`, `WriteDecision` /
`evaluate_write_candidate()` (the fixed-order orchestrator: allowlist → redact → secret-scan
(short-circuit) → size-cap → never-cache → stamp+hash → `ALLOW`), `open_connection_with_limits(db_path)`
/ `check_db_size_within_limit(db_path)` (both require a caller-supplied `db_path`, never default to
`CACHE_DB_PATH` — confirmed at `:269-289`), `acquire_write_guard()`/`release_write_guard()`
(in-process `threading.Lock`, non-multi-process-safe by its own docstring), and 6
`gc_eligible_*`/`gc_eligibility_never_flags_protected_evidence` predicates over a Plan-invented
`CacheRowSnapshot` (not a mirror of `LEVEL1_CACHE_COLUMNS` — its own docstring says so). **Nothing
in this module opens the real `CACHE_DB_PATH`, issues `INSERT`/`UPDATE`, or is imported by any of
the 3 live-gateway files** — this ticket is the first real caller of all of the above against a real
connection/table.

`redaction_policy_version: int = 1` (`:47`) is stamped on every `WriteDecision`, ALLOW and REJECT
alike, but **stays in-memory only** — `WriteDecision.redaction_policy_version` (`:225`) has no
persisted column counterpart (see Risks item 1, the central open decision this ticket must resolve).

### `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` (read in full)

- §1 Lookup identity: exactly 6 fields — `normalized_intent`, `resolved_entity_ids`, `filters`,
  `budget_class`, `routing_policy_version`, `repo_branch_scope` — all 6 already exist as
  `LEVEL1_CACHE_COLUMNS` columns.
- §2 Evidence-validity identity: exactly 5 fields — `evidence_fingerprints`,
  `validated_negative_scopes`, `adapter_version_at_validation`, `working_tree_overlap`,
  `provider_generation_at_validation` — all 5 also already exist as columns.
- §3 Non-collapse rule: lookup and validity are checked as separate steps; a lookup hit is never
  itself a validity verdict.
- §4 `PROVIDER_GENERATION` fallback rule: consulted only when a `SYMBOL`/`FILE`-backed record's own
  finer fingerprint is unavailable — such a record "must never be invalidated by an unrelated
  corpus-wide `PROVIDER_GENERATION` bump alone."
- §5 Branch/working-tree scope: (1) a new commit alone is never a cache miss if evidence
  fingerprints are unchanged; (2) branch identity is a hard partition, checked *before* any
  fingerprint comparison; (3) working-tree fingerprinting uses `changed_paths` ∩ cached-evidence-paths,
  never a full-tree hash — `changed_paths` is an already-frozen request field
  (`knowledge_context_request.schema.json`, array of strings, asserted at
  `tests/tools/test_knowledge_gateway_contract_schemas.py:178`).

### `docs/plans/knowledge-gateway-mcp-proposal.md` §12/§12.1/§12.2/§12.3 (read in full)

Consistent with the contract doc, adds: (a) the 8 evidence-kind table with per-kind preferred
fingerprint (`docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json`); (b)
"primary validation is lazy and occurs before serving a hit... falling back to provider generation
only where the provider capability contract lacks reliable finer-grained evidence" — the exact §12.2
rule AC2 requires; (c) deletion/rename represented as missing-old-identity + new-path-identity, and
"the gateway should snapshot the path set before hashing and retry or reject the hit if the
working-tree state changes during validation" (a race-condition-shaped requirement not yet reflected
in any existing code); (d) §12.3 repeats the branch/commit rules verbatim.

### Real provider capability contracts (AC3) — read directly, not assumed

`docs/engine/contracts/knowledge_gateway_mcp/provider_capabilities_context_search.json` and
`provider_capabilities_graphify.json` — **both** currently declare `"fine_grained_fingerprints": false`
and `"generation_fingerprint": true`. This is a load-bearing fact for AC3 (see Risks item 2): neither
of the two real, live providers this ticket's real code will call can supply anything finer than the
corpus-wide `PROVIDER_GENERATION` signal today. `evidence_identity_kinds.schema.json`'s
`preferred_fingerprint` table (exercised structurally by the Phase 0 fixture test,
`tests/tools/test_evidence_cache_identity_contract.py::test_provider_generation_is_fallback_only_symbol_result_survives_unrelated_generation_bump`)
still defines real, finer preferred fingerprints for `SYMBOL`/`FILE`/`DOCUMENT_SECTION` etc. — those
are the contract's target shape, not something either live adapter can produce yet.

### `knowledge_context_response.schema.json` / `knowledge_status_response.schema.json` (read in full)

- The context response schema already defines top-level `cache` (open string, e.g. `"HIT"`,
  deliberately not a closed enum per its own Design Decision D3 note) and `cache_key_version`
  (integer) — neither populated by `_run_knowledge_context()` today. `additionalProperties` is
  intentionally **not** restricted at the top level of this schema (its own description explains
  why), so adding these two keys needs no schema edit.
- The status response schema already defines all 6 of §9.2's cache-domain fields
  (`cache_entry_counts[]`, `cache_hit_rate`, `cache_miss_rate`, `cache_stale_rejection_rate`,
  `latency_summary_ms{}`, `provider_fallback_rate`) plus `recent_invalidation_reasons[]` and
  `cache_rebuildable` — none `required`, and `additionalProperties: false` at the top level, so only
  these exact names may ever be added, never an invented field. No schema edit is needed for AC6
  either. `latency_summary_ms`'s sub-fields (`lookup`, `evidence_validation`, `provider_fallback`,
  `packet_assembly`, `end_to_end`) correspond 1:1 to `measurement_baseline_contract.md` §2's 5
  measurement points — none of which has a live-wired emitter anywhere in the repo yet (confirmed:
  `tools/retrieval_events.py`'s 3 Wrapper functions remain unused by the live gateway per
  `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`'s own D1 finding, re-confirmed by
  `test_wrapper_functions_genuinely_not_applicable_zero_invoked`). **This ticket's own scope does
  not add latency instrumentation** — `latency_summary_ms` and `provider_fallback_rate` should stay
  honestly omitted (Phase-1's own precedent: omit, never fabricate `0`/`null`), while
  `cache_entry_counts`/`cache_hit_rate`/`cache_miss_rate`/`cache_stale_rejection_rate` become
  genuinely populable from the real cache this ticket wires in. Flagged for Plan to confirm this
  exact field split explicitly (not silently assumed).

### Existing regression test that WILL break, deliberately (not a gate to route around)

`tests/tools/test_knowledge_gateway_mcp.py::test_knowledge_status_omits_all_cache_specific_fields_enumerated`
(`:120-134`) currently hard-asserts **all 7** cache-domain fields are absent and
`set(response.keys()) == {"gateway_version", "reported_schema_version", "providers", "branch_scope"}`
— exactly the Phase-1-correct claim `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`'s own AC3 required at
the time. Once this ticket populates real cache-domain fields in `_run_knowledge_status()`, this
test's assertions become stale by design, in exactly the same way
`test_no_live_gateway_code_or_search_mcp_edits_introduced`'s stale banned-path tuple was corrected
by `CACHE-SCHEMA-MIGRATIONS`'s own DD3 (a direct, read-and-justify correction of a ticket-scoped
assumption that has since expired — not a routed-around gate). This ticket must update this test's
assertions to match the new, deliberately-widened Phase-2 field set (while still asserting that
`latency_summary_ms`/`provider_fallback_rate` — the fields this ticket's own scope does *not*
populate — remain honestly omitted), and must record the correction explicitly, mirroring the exact
precedent.

## Mechanics / Engine Constraints

Agent-orchestration/retrieval tooling — no Mechanics Bible chapter or `docs/engine/` kernel/pipeline
contract governs this subsystem (same category as every other `INFRA-*` entry in this family,
per `evidence_cache_identity_contract.md` §6's and `redaction_retention_policy.md` §12's own explicit
"no parity ledger entry accompanies this document" disclaimers). Governing laws are the Knowledge
Gateway MCP's own frozen contracts, all read in full above:
`evidence_cache_identity_contract.md` §1-§5, `redaction_retention_policy.md` §2-§10,
`cache_migration_plan.md` §1-§5, and proposal §11-§12.3.

## Docs Requiring Update

- `docs/plans/knowledge-gateway-mcp-proposal.md`: §20 Phase 2's "Validate direct evidence
  fingerprints before hits, falling back to provider generation only when the provider capability
  contract lacks reliable finer-grained evidence." and "Add exact normalized-query reuse." bullets
  need **Done** annotation once this ticket lands, per the epic's own annotation-convention
  requirement and the Phase 0/Phase 1 precedent already visible throughout this same section.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`: §4/§11's "must be
  reviewed and expanded by a security-focused pass before Phase 2 payload caching goes live"
  precondition becomes operative the moment this ticket's code starts genuinely serving/writing
  cache rows during live gateway operation (see Risks item 4) — the doc's own disclosure language
  needs either an explicit "still open, now live" acknowledgment or a recorded resolution, not
  silence. §6's "stamped onto any future payload-bearing cache row" (future tense) and its
  "unresolved, left for a future ticket's Plan phase to decide explicitly" sentence
  (`redaction_retention_policy.md:134-135`) need updating once this ticket's own Plan phase decides
  Risks item 1 (in-memory-only vs. a new migration column) — whichever way it resolves, the doc must
  say so in past tense, mirroring the exact §8/§9 tense-correction precedent already twice
  demonstrated in this same doc.
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`: if Plan decides Risks item 1
  needs a real column, this doc's §2 ordered-migration-function list needs a new entry
  (`migration_003_...`, never `migration_002` — see Risks item 1) documenting the new migration by
  name, since §2 currently enumerates only `migration_001`/`migration_002`.
- `docs/parity_ledger/infrastructure.yaml`: a new entry, next available ID confirmed by direct grep
  to be `INFRA-343` (last existing entries are `INFRA-341` — schema/migrations — and `INFRA-342` —
  redaction write-path, both `status: verified`, `priority: P1`), covering this ticket's real
  read/write wiring: the new `check_provider_result_cache()`/`write_provider_result_cache()`
  functions, the cache-hook call sites in `tools/knowledge_gateway_mcp.py`, and the evidence-validity
  revalidation logic — following `INFRA-341`/`INFRA-342`'s exact shape (`P1`, `proof_type:
  regression`, real `test_path`s).

## Parity Ledger Overlap

- `INFRA-341` (schema/migrations, `status: verified`, `P1`) and `INFRA-342` (redaction write-path,
  `status: verified`, `P1`) — both direct upstream dependencies this ticket sits on. Neither needs
  editing: both entries' own text already correctly scopes itself as schema-only / pure-functions-only
  and explicitly attributes the live-wiring work to this ticket by name. No P0 entries anywhere in
  this subsystem (confirmed by both dependency tickets' own Parity Ledger Overlap sections and by
  direct precedent: `evidence_cache_identity_contract.md` §6 / `redaction_retention_policy.md` §12
  both explicitly disclaim any parity ledger entry for the contract docs themselves).
- New entry needed for *this ticket's own code* (see Docs Requiring Update) — `INFRA-343`, `P1`, not
  `P0` (matching the established pattern for this whole subsystem so far).

## Prior Work

- `TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS` (done) — built `LEVEL1_CACHE_COLUMNS`,
  `migration_001_add_level1_tables()`. Its own plan.md DD6 explains exactly why `migration_001` is
  never auto-invoked, and its own Anti-Drift Notes explicitly forbid adding `migration_002_add_level2_tables`
  "in any form (empty stub included)" — directly load-bearing for Risks item 1 below (any new
  migration this ticket's Plan adds must use ordinal 3+, never 2).
- `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH` (done) — built `evaluate_write_candidate()` and the
  §9 SQLite-limits helpers this ticket is the first real caller of. Its own plan.md DD2 explicitly
  left the `redaction_policy_version` persistence question open for this ticket ("Flagged for
  Architecture Review confirmation... if Review disagrees, the fallback is Step 7 gaining a
  `migration_003_add_redaction_policy_version_column` addition"). Its own DD3 explicitly requires
  this ticket's Investigate phase to re-ask the security-pass-precondition question independently
  (done above, Risks item 4). Its own DD9 explicitly flags that this ticket is the one that must
  decide, deliberately, whether enabling WAL mode against the real `CACHE_DB_PATH` for the first time
  is acceptable (Risks item 3).
- `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE` (done) — built `tools/knowledge_gateway_mcp.py` itself,
  including `_run_knowledge_context()`/`_run_knowledge_status()`'s exact current shape read above.
- `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY` (done) — froze the identity contract this ticket
  implements as real logic for the first time; its own Phase 0 test file
  (`tests/tools/test_evidence_cache_identity_contract.py`) is fixture-based (no live invalidation
  function existed at Phase 0) and is the direct precedent this ticket's own SYMBOL/FILE-fingerprint
  tests should follow, since no real live provider can supply a finer-than-generation fingerprint yet
  either (Risks item 2).
- `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY` — its own module docstring's "Honesty notes" section (esp.
  the `NegativeClaimSupport` SCOPED/COMPLETE-branches-only-reachable-via-monkeypatch disclosure) is
  the direct style precedent this ticket should follow when disclosing that its own SYMBOL/FILE-kind
  fingerprint revalidation path is real, tested logic but not exercisable end-to-end against real
  live provider data today (Risks item 2).

## Risks and Open Questions

1. **BLOCKING for Plan — `redaction_policy_version` persistence is genuinely unresolved and this
   ticket cannot silently pick a side.** `LEVEL1_CACHE_COLUMNS` (21 columns, confirmed by direct
   read) has no `redaction_policy_version` column; `WriteDecision.redaction_policy_version` is
   in-memory only. `cache_migration_plan.md` §2 pre-authorizes only `migration_001`/`migration_002`
   (the latter reserved for Level 2/Phase 3 tables — this ticket's own dependency's Anti-Drift Notes
   explicitly forbid touching that name in any form). Two real options, neither silently assumable:
   (a) this ticket's real `write_provider_result_cache()` simply never persists
   `redaction_policy_version` — the value is computed, checked, and then dropped on the floor at the
   real-write boundary, which is honest but means a real cache row carries no on-disk record of which
   redaction-policy version wrote it (undermines part of §6's own stated purpose: "a row can be
   identified as having been written under a specific version of this policy's rules"); or (b) add a
   new, not-yet-frozen `migration_003_add_redaction_policy_version_column(conn)` doing a genuinely new
   *kind* of migration (`ALTER TABLE ... ADD COLUMN`, not `CREATE TABLE IF NOT EXISTS` — SQLite has no
   `ADD COLUMN IF NOT EXISTS`, so idempotency needs an explicit `PRAGMA table_info` existence check
   before altering). Both the dependency ticket's own plan.md DD2 and this investigation flag this as
   requiring **explicit Architecture Review sign-off**, not an implementer's silent pick, given DD2's
   own words: "if Review disagrees, the fallback is Step 7 gaining a
   `migration_003_add_redaction_policy_version_column` addition — a genuinely new, not-frozen-plan
   migration ordinal — a materially different, larger change... a Review override here should trigger
   a plan revision."
2. **Real, structural limitation on AC3 test coverage — flag honestly, do not overstate.** Both real
   `provider_capabilities_*.json` files declare `"fine_grained_fingerprints": false` today. AC3's own
   wording ("never used as the default path when finer-grained evidence IS available") is trivially
   satisfiable against real live providers *because finer-grained evidence is never available from
   either one yet* — this is not a defect this ticket introduces, and not something this ticket's
   scope is meant to fix (that's a future provider-adapter-capability ticket's job). Consequence: a
   genuine end-to-end test of "cache hit rejected because a `SYMBOL`/`FILE`-kind evidence fingerprint
   changed" (AC2's bullet 2) **cannot be exercised against real live provider output today** — it must
   use constructed/fixture-level evidence records, mirroring
   `test_evidence_cache_identity_contract.py`'s own Phase-0 fixture-based test pattern (itself
   explicitly justified there as "since no live invalidation function exists yet at Phase 0" — the
   same justification now transfers here for the SYMBOL/FILE path specifically, even though a live
   invalidation function *does* exist after this ticket, its two real inputs still cannot produce
   fine-grained fingerprints). The only fingerprint-mismatch path realistically exercisable against
   real live providers is the `PROVIDER_GENERATION`-level one (a real `corpus_generation` bump via
   `manifest.json`'s `built_at`, mirroring `_corpus_generation()`'s existing precedent). Test plan
   must state this split explicitly, mirroring `knowledge_gateway_packet_assembly.py`'s own "Honesty
   notes" disclosure precedent for its `NegativeClaimSupport` SCOPED/COMPLETE branches — never present
   the SYMBOL/FILE path as "tested end-to-end against real data" when it is not.
3. **WAL-mode cross-module effect — this ticket is the first real caller of `open_connection_with_limits()`
   against the real `CACHE_DB_PATH`.** `PRAGMA journal_mode=WAL` is file-persistent (unlike
   `busy_timeout`, connection-scoped only). None of `tools/retrieval_cache.py`'s 8 existing
   `_get_connection()` call sites set it today. If this ticket's new `check_provider_result_cache()`/
   `write_provider_result_cache()` open the real cache file via
   `knowledge_gateway_redaction.open_connection_with_limits(CACHE_DB_PATH)` (the obvious, intended
   real use of that helper — its own docstring names "child 3" as the one who "makes that connection
   deliberately, later"), every subsequent `_get_connection()` call against the same file — including
   all 3 legacy marker-only tables' existing check/write functions — will observe WAL mode too, a real
   behavioral effect on code this ticket's own Out-of-Scope says it must not touch *the source of*.
   The dependency ticket's own plan.md DD9 explicitly requires this to be "an explicit sentence in
   that ticket's own investigation, not silent inheritance" — recorded here: **Plan must explicitly
   decide and document whether enabling WAL mode file-wide is acceptable** (very likely yes, as a
   reliability improvement for concurrent readers/writers across the whole file, but it is a
   deliberate choice, not a default).
4. **Security-pass precondition — re-asked independently per the dependency ticket's own DD3
   instruction, not inherited.** `redaction_retention_policy.md` §4/§11 (quoted verbatim): "must be
   reviewed and expanded by a security-focused pass **before Phase 2 payload caching goes live**."
   `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH`'s own plan.md DD3 concluded its own shipping was not
   blocked because it wired nothing into a live request path — and explicitly said the opposite
   conclusion does *not* transfer to this ticket, since this ticket is precisely the one that makes
   caching "go live" (real writes reachable from a real, running MCP tool call). Under the plain
   reading of the ratified text, **this precondition is now operative** the moment this ticket's code
   ships and is reachable from `knowledge_context`. This is not something Investigate can resolve
   unilaterally — flagging it here as a real, named precondition for Plan/Architecture-Review/human
   sign-off to consciously accept or explicitly defer (e.g., by scoping this ticket's live rollout
   behind a flag, or by treating this as the trigger that schedules the still-owed security-focused
   pass), not something to silently proceed past.
5. **§12.2's "snapshot the path set before hashing and retry or reject the hit if the working-tree
   state changes during validation"** (proposal text, read directly) describes a TOCTOU-shaped
   requirement with no existing precedent anywhere in this codebase's cache code. Achievable (compute
   `changed_paths` once, pass the same snapshot through the whole validation call, never re-query
   `git status` mid-check) but must be an explicit Plan step, not an incidental detail — a validation
   step that silently re-reads working-tree state twice would violate this rule without any test
   catching it unless a dedicated test forces a mid-call mutation.
6. **`resolved_entity_ids` computation is not yet specified anywhere.** §1's lookup-identity tuple
   names `resolved_entity_ids` as "any entity IDs the caller's intent already resolved to," using the
   5 closed deterministic forms (`symbol:`, `ticket:`, `parity:`, `doc:`, `subsystem:`) — but neither
   `knowledge_gateway_router.py::route()` nor `knowledge_gateway_packet_assembly.py::assemble_packet()`
   currently returns anything shaped like a resolved-entity-ID list (confirmed by reading both
   modules' real return shapes, `RoutingDecision` and `PacketAssembly`). This ticket's cache-lookup
   identity computation must derive `resolved_entity_ids` from real request/response data (e.g. the
   router's own stable-identifier matchers, `match_ticket_id`/`match_parity_id`/`match_source_path`/
   `match_symbol_name`, already computed during routing) rather than inventing a second, redundant
   resolution pass — flagged for Plan to trace precisely which existing router-internal values map to
   this field, since `RoutingDecision`'s exact field shape was not re-verified line-by-line in this
   investigation (Plan should re-read `tools/knowledge_gateway_router.py:315-323` directly before
   committing to a mapping).

## Anti-Drift Hazards

- **Do not fold cache-check/cache-write logic into `tools/knowledge_gateway_packet_assembly.py`.**
  Explicit Out of Scope; that module's own guard tests (`test_module_does_not_modify_or_import_retrieval_cache`,
  `test_module_does_not_edit_knowledge_gateway_router`) currently prove zero cache relationship and
  must keep proving it.
- **Do not touch `tools/knowledge_gateway_router.py`** — confirmed still banned by
  `test_search_mcp_py_provably_untouched`.
- **Do not add `migration_002_add_level2_tables` in any form** — reserved for Level 2/Phase 3, per the
  dependency ticket's own explicit Anti-Drift Note. Any new migration this ticket's Plan adds must be
  ordinal 3+.
- **Do not silently decide Risks item 1 (redaction_policy_version persistence) without Architecture
  Review sign-off** — both this investigation and the dependency ticket's own plan.md DD2 require it
  explicitly.
- **Do not present the SYMBOL/FILE-kind evidence-fingerprint revalidation path as tested against real
  live provider data** — it cannot be, today, per Risks item 2. Fixture-based testing is legitimate
  and precedented (Phase 0's own contract test file), but must be labeled honestly, not silently
  conflated with "real invocation" style tests the way `test_knowledge_context_tool_real_invocation_validates_against_response_schema`
  is for the non-cache path.
- **Do not fabricate `latency_summary_ms`/`provider_fallback_rate` values in `knowledge_status`.**
  This ticket adds no latency instrumentation — those two fields must stay honestly omitted, exactly
  like Phase 1's own omission discipline for all 7 cache fields before this ticket.
- **Do not silently let `test_knowledge_status_omits_all_cache_specific_fields_enumerated` start
  failing without updating it.** It is a real, currently-passing regression test whose Phase-1-correct
  assertions are being deliberately superseded by this ticket's own scope — update it explicitly, with
  a comment recording why, mirroring `CACHE-SCHEMA-MIGRATIONS`'s own DD3 precedent for a stale-test
  correction. Do not "fix" it by weakening its remaining guarantee (that `latency_summary_ms`/
  `provider_fallback_rate` stay omitted) — only the fields this ticket genuinely populates should be
  removed from its omission-list assertion.
- **Do not add cache-DB state pollution across test runs.** No cache-DB isolation fixture exists yet
  in `tests/tools/test_knowledge_gateway_mcp.py` (confirmed by direct read — no `tmp_path`/monkeypatch
  fixture touching `CACHE_DB_PATH` anywhere in that file today, unlike `tests/tools/test_retrieval_cache.py`'s
  existing `_isolated_cache_db` autouse fixture). Once real cache reads/writes are wired in, every test
  in this file that calls `_mod._run_knowledge_context(...)` must run against an isolated cache DB
  (mirroring `test_retrieval_cache.py`'s own precedent) — otherwise repeated test runs will pollute the
  real on-disk `knowledge-index/retrieval_cache.db` and/or produce flaky cross-test cache hits (e.g.
  test 9's fake query silently served from a previous test's real cache write).
