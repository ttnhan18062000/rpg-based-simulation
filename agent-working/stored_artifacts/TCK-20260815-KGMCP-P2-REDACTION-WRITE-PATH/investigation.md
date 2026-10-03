---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH
artifact_type: investigation
tags: [ai, mcp, security]
---

# Investigation — TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH

## Current Behavior

### `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (the ratified policy this ticket implements)
Ratified as drafted 2026-08-15 (`TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION`). Sections directly
in this ticket's scope, read in full:

- **§2 Allowlist** — only Context Search provider results (`tools/search_mcp.py`, scoped to docs/
  tickets/investigations/working-history already in `knowledge-index/knowledge.db`) and Graphify
  provider results (source-symbol/dependency data already in the graphify graph) are eligible for a
  cache write. Anything else (raw filesystem read, live shell stdout, arbitrary tool-call payload)
  is ineligible until a future ticket adds it.
- **§3 Redaction Rules** — local usernames and machine-specific absolute paths must be stripped and
  replaced with fixed placeholder tokens (`<local-user>`, `<local-path>` or the repo-relative
  rewrite) *before* hashing. The unredacted-content hash and redacted-content hash must differ by
  design; only the redacted-content hash may ever be persisted.
- **§4 Secret-Scan Disclosure** — 4 named regex shapes (AWS-style key ID `AKIA[0-9A-Z]{16}`,
  generic API-key assignment `(api[_-]?key|apikey)\s*[:=]\s*['"][A-Za-z0-9_\-]{16,}['"]`, PEM
  private-key header `-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----`, Bearer token
  `Bearer\s+[A-Za-z0-9\-_.]{20,}`). A match must **reject the write outright**, never redact-and-store.
  Explicitly disclosed, twice (§4 and §11), as a non-production-complete starting baseline needing a
  future dedicated security-focused pass "before Phase 2 payload caching goes live."
- **§5 Payload Size Cap** — 8192 bytes measured on the UTF-8-encoded *redacted* payload. Oversized
  → reject, never truncate.
- **§6 `redaction_policy_version`** — a 4th, genuinely distinct version axis (alongside
  `retrieval_cache_schema_version`, `RETRIEVAL_VERSION`, `retrieval_event_schema_version`),
  "stamped onto any future payload-bearing cache row" (future tense — no such row/column exists
  yet; see Risks below).
- **§7 Never-Cache Enumeration** — 6 independently-enforceable categories: secrets/credentials,
  tokens, raw environment values, unredacted sensitive tool output, arbitrary config-file contents,
  unrestricted raw prompts.
- **§9 SQLite Operational Limits** — documented defaults (256 MB max DB size, WAL mode,
  `busy_timeout=5000`, `0600` file permissions, bounded single-transaction writes, per-key stampede
  guard). §9's own preamble says these were "not implemented in `tools/retrieval_cache.py`" **by the
  policy-authoring ticket** (`TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY`) and deferred
  "implementation ... to a future ticket." This ticket's own Scope explicitly claims that deferred
  work ("Implement the §9 SQLite operational limits ... as real, tested logic").
- **§10 Cache-GC Defaults** — 6 safe-eviction candidate categories, explicitly deferring to
  `evidence_cache_identity_contract.md` §4's fallback rule (never evict a `SYMBOL`/`FILE`-backed
  evidence row on a bare `PROVIDER_GENERATION` bump). `prune()` stays manual-only; no automatic GC
  wiring is implied by "policy" language here.

### `tools/retrieval_cache.py` (the module this ticket's functions operate alongside — read in full, 627 lines, current post-`CACHE-SCHEMA-MIGRATIONS` state)
- `RETRIEVAL_VERSION: int = 1` (line 45) — cache-key-derivation version. Not this ticket's axis.
- `retrieval_cache_schema_version: int = 1` (line 51) — DDL/table-shape version, added by the just-closed
  sibling ticket. Not this ticket's axis either.
- `MAY_LIST_COLUMNS` (lines ~76-95) — write-path allowlist for the 3 legacy marker-only tables.
  Unrelated to the new Level 1 table.
- `LEVEL1_CACHE_COLUMNS: frozenset[str]` (lines ~97-128) — the 21-column allowlist for the new
  `retrieval_provider_result_cache_rows` table (see full enumeration below). **Confirmed by direct
  read: contains no `redaction_policy_version` column.** See Risks below — this is a real gap, not
  an assumption.
- `migration_001_add_level1_tables(conn)` (lines 198-248) — creates
  `retrieval_provider_result_cache_rows` with exactly these 21 columns: `query_hash`,
  `normalized_intent`, `resolved_entity_ids`, `filters`, `budget_class`, `routing_policy_version`,
  `repo_branch_scope`, `provider_name`, `adapter_version`, `result_payload`, `source_ids`,
  `source_paths`, `provider_generation`, `evidence_fingerprints`, `validated_negative_scopes`,
  `adapter_version_at_validation`, `working_tree_overlap`, `provider_generation_at_validation`,
  `created_at`, `last_hit_at`, `hit_count`. PK `(query_hash, repo_branch_scope)`. Standalone —
  not called from `_get_connection()`/`_init_schema()`/any `check_*`/`write_*`/`prune()` path, so it
  never auto-runs.
- `_get_connection()` (lines 135-144) — the single existing connection-opening path. Zero `PRAGMA`,
  zero `busy_timeout`, zero file-permission code today (confirmed by direct read, matches
  `redaction_retention_policy.md` §9's own description).
- No `check_provider_result_cache()` / `write_provider_result_cache()`-style function exists for the
  new table yet — confirmed both by direct read of the file and by `INFRA-341`'s own
  `support_boundary` text ("no read/write logic against the new table exists yet ... nor any
  redaction/secret-scanning/size-cap enforcement on `result_payload` (`TCK-20260815-KGMCP-P2-
  REDACTION-WRITE-PATH`'s job)"). That confirms this ticket's pure functions are meant to be called
  by, not to themselves perform, the real INSERT — the actual write function is
  `CACHE-READ-WRITE-WIRING`'s (child 3's) job, consistent with this ticket's own Out of Scope
  ("Wiring this write-path logic into the real gateway's request handling ... This ticket builds
  pure, directly-testable functions; the next ticket calls them from the real code path").

### `tests/docs/test_redaction_retention_policy_doc.py` (read in full — the file this ticket's own briefing flagged as a scope question)
This file's `_RETRIEVAL_CACHE_PY` constant (line 24) is hard-scoped to exactly one path:
`Path(__file__).parent.parent.parent / "tools" / "retrieval_cache.py"`. Every source-text/AST
assertion in `test_sqlite_defaults_not_silently_implemented` (lines 107-125: `"PRAGMA" not in
source`, `"busy_timeout" not in source`, `"os.chmod" not in source`, `"chmod" not in source`,
`"os" not in imported_modules`) reads only that one file's text via `_RETRIEVAL_CACHE_PY.read_text()`
and `ast.parse(source)` on that same text. **It does not read, import, or otherwise constrain any
other file.** Confirmed by reading the whole test module (158 lines) — no glob, no directory walk,
no second path constant. **Conclusion: the constraint is scoped only to `tools/retrieval_cache.py`.
A new module this ticket adds under `tools/` may use `PRAGMA`, `busy_timeout`, `chmod`, or
`import os` freely — the test cannot see it.**

This resolves the architecture question raised by this ticket's own Scope tension: §9 SQLite
operational limits (which genuinely need `PRAGMA`/`busy_timeout`/file-permission code to be "real,
tested logic," not just a docstring) must live in the **new** module this ticket creates, not in
`tools/retrieval_cache.py` — otherwise `test_sqlite_defaults_not_silently_implemented` breaks
immediately and CLAUDE.md's hard rule against editing/weakening a gate to route around it would bar
"fixing" that test to permit the change. The new module's §9 functions should accept and operate on
a `sqlite3.Connection` (or open one to a caller-supplied path) so they are independently testable
without being wired into `_get_connection()`'s hot path — consistent with this ticket's "pure,
directly-testable functions" framing and with `CACHE-READ-WRITE-WIRING` (child 3) being the ticket
that actually wires anything into a live request path.

### `tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_introduced` (read directly, lines 343-362)
Banned-path tuple is exactly 4 entries after the schema-migrations ticket's edit: `tools/search_mcp.py`,
`tools/hybrid_retrieval.py`, `tools/context_packet_assembler.py`, `tools/retrieval_events.py`.
`tools/retrieval_cache.py` was already removed from this tuple (with a citing comment) by the just-closed
sibling ticket. A brand-new module path is not in this tuple and cannot be, since the tuple is a
literal 4-item constant — this ticket introducing a new file does not touch this guard at all.

### `docs/parity_ledger/infrastructure.yaml` — `INFRA-341` (just added by the sibling ticket, read in full, lines 9023-9087+)
Its own `support_boundary` text explicitly disclaims covering "any redaction/secret-scanning/
size-cap enforcement on `result_payload`" and attributes that work to this ticket by name. Confirms
the schema ticket and this ticket agree on the boundary: schema shape vs. write-path enforcement
logic are cleanly split.

### `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 2 bullets (read directly, lines 1210-1228)
4 bullets: "Add SQLite schema and migrations" (**Done**, cites the schema ticket), "Store actual
bounded normalized results" (closest match to this ticket's redaction/allowlist/size-cap work —
"bounded" = size cap, "normalized" = allowlist-and-redacted shape), "Validate direct evidence
fingerprints before hits ..." (out of scope here — `CACHE-READ-WRITE-WIRING`'s job), "Add exact
normalized-query reuse" (also `CACHE-READ-WRITE-WIRING`'s job). This ticket's own doc annotation
target is the "Store actual bounded normalized results" bullet.

## Mechanics / Engine Constraints

Agent-orchestration/retrieval tooling — no Mechanics Bible chapter or `docs/engine/` kernel/pipeline
contract governs this subsystem's semantics (same category as `INFRA-294` through `INFRA-341`,
confirmed by direct precedent in the sibling ticket's own investigation and restated by `INFRA-341`'s
`support_boundary`). Governing laws are the Knowledge Gateway MCP's own frozen contracts:

- `redaction_retention_policy.md` §2-§10 (this ticket's direct implementation target).
- `evidence_cache_identity_contract.md` §1-§3 (Non-collapse rule — column-naming discipline this
  ticket must not violate if its pure functions produce a dict/dataclass shaped like a future cache
  row: never reuse a lookup-identity field name for a validity-identity concept, and vice versa).
- `docs/observability/retrieval_retention_redaction_policy.md` (the prior, more general policy this
  document extends per its own §1 — not restated here since `redaction_retention_policy.md` already
  supersedes the overlapping parts for payload rows specifically).

## Docs Requiring Update

- `docs/plans/knowledge-gateway-mcp-proposal.md`: annotate §20 Phase 2's "Store actual bounded
  normalized results" bullet Done once this ticket's redaction/allowlist/secret-scan/size-cap
  functions land, per the Phase 0/Phase 1 epics' own annotation convention the epic ticket requires.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`: §6 currently says
  `redaction_policy_version` is "stamped onto any future payload-bearing cache row" (future tense).
  Once this ticket ships a real, callable stamping function, that sentence's tense is stale in the
  same way `redaction_retention_policy.md` §8's own token-counting section already had to be
  corrected from present-tense "no callable ships" to past-tense "implemented as a real callable at
  ..." after `KGMCP-P1-PACKET-ASSEMBLY` shipped (§8's own trailing paragraph is the precedent to
  mirror). §9's "not implemented ... deferred to a future ticket" sentence needs the equivalent
  update once this ticket's SQLite-limits functions land, citing the new module/function by path —
  mirroring the exact tense-correction pattern §8 already demonstrates.
- `docs/parity_ledger/infrastructure.yaml`: a new entry (next ID after `INFRA-341`) for this
  ticket's own new module — allowlist check, redaction function, secret-scan function, size-cap
  check, `redaction_policy_version` stamping, SQLite-limits functions, GC-eligibility check
  functions — following `INFRA-341`'s own precedent shape (P1 priority, `proof_type: regression`,
  real `test_path`s into the new module's test file).

## Parity Ledger Overlap

- `INFRA-341` (`docs/parity_ledger/infrastructure.yaml`, status `verified`, priority `P1`) — the
  schema-only entry this ticket's work sits directly downstream of. Its own text explicitly
  disclaims covering this ticket's scope; no edit to `INFRA-341` itself is needed (its claims remain
  true — schema-only, no enforcement — after this ticket lands, since this ticket adds a *new* file,
  not edits to `tools/retrieval_cache.py`'s cited line ranges). Not a P0 entry — no existing gate
  requires a specific `test_path` here beyond "keep passing."
- No P0 entries in `docs/parity_ledger/` are touched by this ticket's scope (this subsystem's
  contract docs are explicitly outside the parity ledger per `evidence_cache_identity_contract.md`
  §6's own precedent, restated by `redaction_retention_policy.md` §12's closing paragraph: "No
  `docs/parity_ledger/` entry accompanies this document").
- New entry needed for the *code* this ticket ships (see Docs Requiring Update) — the pattern is
  code gets a parity entry, contract docs do not.

## Prior Work

- `TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS` (done, sibling/dependency) — built
  `LEVEL1_CACHE_COLUMNS`, `migration_001_add_level1_tables()`, the `retrieval_provider_result_cache_rows`
  table this ticket's functions will eventually feed. Its own Out of Scope explicitly deferred
  "Redaction/secret-scanning/size-cap enforcement at write time" to this ticket by name, and its own
  Anti-Drift Hazards explicitly forbade itself from implementing it — clean boundary, no overlap.
- `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY` (done, ratified) — wrote the policy this ticket
  implements. Its own §8 closing paragraph is the direct precedent for how this ticket should update
  the policy doc's tense once its own callables ship (see Docs Requiring Update).
- `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY` — implemented `kgmcp_char_heuristic_v1` as the first real
  callable born from this same policy doc (§8), including updating the doc's own tense from
  "no callable ships" to "implemented as a real callable at ..." — the exact template this ticket
  should follow for §6 and §9.
- `tools/retrieval_events.py` — precedent for "distinct version constant, tested for
  non-collision with sibling version constants" (`test_schema_version_constant_distinct_from_
  cache_key_version_constant`, `tests/tools/test_retrieval_events.py:78-83`, asserting
  `retrieval_event_schema_version == 1` and that the name is absent from the sibling module's
  `dir()`). This ticket's `redaction_policy_version` distinctness test should mirror that exact
  shape against all 3 sibling constants (`RETRIEVAL_VERSION`, `retrieval_cache_schema_version`,
  `retrieval_event_schema_version`).
- `tools/agent_codex_posttool_adapter/redaction.py` — explicitly disclaimed by the policy doc itself
  (§4) as an unrelated subsystem (truncates/selects `agent-monitoring/tools.jsonl` fields; not a
  secret scanner). Confirmed by direct read of the policy text — do not treat as reusable precedent
  for this ticket's secret-scan logic.

## Risks and Open Questions

1. **RESOLVED — security-pass precondition does not block this ticket's shipping, but the same
   question is not resolved for child 3.** The ratified policy's own exact wording (§4): "It must be
   reviewed and expanded by a security-focused pass **before Phase 2 payload caching goes live**."
   §11 restates this identically: "...must still be reviewed and expanded by a dedicated
   security-focused pass before Phase 2 payload caching goes live; ratifying the policy's overall
   shape does not waive that follow-up requirement." This ticket's own Out of Scope is explicit that
   it does **not** wire anything into the live gateway request path ("Wiring this write-path logic
   into the real gateway's request handling — that's `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s
   job"), and produces only pure, directly-testable functions that nothing in the live system calls
   yet. Under the plain reading of "before Phase 2 payload caching **goes live**," caching does not
   "go live" until child 3 wires these functions into real request handling and the cache begins
   actually serving/writing rows during real gateway operation. Therefore: **this ticket's own
   shipping is not blocked by the security-pass precondition** — it may ship the disclosed
   non-production-complete 4-pattern baseline as-is, exactly as its own Out of Scope already
   anticipates ("Expanding or hardening the §4 secret-scan baseline beyond what's already ratified"
   is explicitly out of scope here). **However, this does not resolve the precondition for child 3.**
   `CACHE-READ-WRITE-WIRING` is the ticket that actually makes caching "go live," so it inherits this
   exact same open question more acutely — its own Investigate phase must re-ask it, not assume this
   ticket's resolution transfers, since a different ticket doing the actual live-wiring is precisely
   the point at which §4/§11's precondition text becomes operative. Flagging this explicitly for
   Plan and for the epic's own tracking, per this ticket's own Assumptions/Open Questions instruction
   to cite exact wording and not silently assume resolved.

2. **Real schema gap: no `redaction_policy_version` column exists on `retrieval_provider_result_cache_rows`.**
   Confirmed by direct read of `LEVEL1_CACHE_COLUMNS` (21 columns, enumerated above) and the live
   `CREATE TABLE` statement in `migration_001_add_level1_tables()` — neither contains
   `redaction_policy_version`. The policy doc's own §6 language is future-tense ("stamped onto any
   future payload-bearing cache row") confirming no column exists yet. This ticket's AC4 ("
   `redaction_policy_version` is a real, stamped value distinct from the other 3 version axes") is
   achievable without a DB column: this ticket's pure function(s) can return
   `redaction_policy_version` as a field on a decision/result object (mirroring how
   `emit_retrieval_event()` in `tools/retrieval_events.py:133` stamps `retrieval_event_schema_version`
   into the dict it returns/writes, itself a precedent for "stamp onto an in-memory record before
   persistence"). But **durably persisting** that value into an actual DB row requires a column that
   does not exist today. `cache_migration_plan.md` §2 explicitly says neither `migration_001` nor
   `migration_002` includes `ALTER TABLE ADD COLUMN` — so adding this column is not pre-authorized by
   any frozen migration design. This is a real coordination gap between this ticket and
   `CACHE-READ-WRITE-WIRING` (child 3): either (a) this ticket's Plan phase decides the pure function
   only returns the value in-memory and child 3's own Plan must add a `migration_003`-style column
   addition before it can persist it, or (b) this ticket's Plan phase decides adding the column now
   (via a new additive migration function, consistent with `cache_migration_plan.md`'s own
   `CREATE TABLE IF NOT EXISTS`/idempotent philosophy, though a column-add technically needs `ALTER
   TABLE ADD COLUMN` which the frozen plan's §2 did not anticipate for either named migration) is
   this ticket's job since it is the ticket that owns `redaction_policy_version`'s real value. Not
   resolved here — flagged for Plan to decide explicitly, not silently assumed.

3. **`retrieval_cache_schema_version` (schema-shape) vs. this ticket's own module version.** If the
   new redaction module needs its own DDL/behavior version at all (it does not own a table itself,
   only produces functions), no new version constant is needed beyond `redaction_policy_version`
   itself — noted only to rule out inventing a 5th version axis by accident, which
   `measurement_baseline_contract.md:169` (read via grep) already anticipates and warns against
   ("never a fifth, latency-specific version constant").

## Anti-Drift Hazards

- **Do not add `PRAGMA`/`busy_timeout`/`chmod`/`import os` to `tools/retrieval_cache.py`.**
  Confirmed by direct read that `test_sqlite_defaults_not_silently_implemented`
  (`tests/docs/test_redaction_retention_policy_doc.py:107-125`) is scoped only to that one file, but
  that scoping is precisely why this ticket's §9 work must land in the **new** module instead — do
  not "fix" the test's scope to allow adding this to `retrieval_cache.py`; that would be editing a
  gate to route around it, barred by CLAUDE.md's hard rule.
- **Do not expand or harden the §4 secret-scan baseline beyond the 4 documented patterns.** Explicit
  Out of Scope. Implement exactly the 4 regexes as documented, verbatim, not "improved" versions —
  any real hardening is a separate future security-focused-pass ticket's job per §4/§11's own
  disclosure.
- **Do not implement any actual `INSERT`/`UPDATE` against `retrieval_provider_result_cache_rows`.**
  That is `CACHE-READ-WRITE-WIRING`'s (child 3's) job, per this ticket's own Out of Scope framing
  ("the next ticket calls them from the real code path") and confirmed by `INFRA-341`'s
  `support_boundary` text naming this exact split. A "reject the write outright" function should
  return a decision/verdict, not perform or block a SQL statement that doesn't exist yet.
- **Do not touch `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
  or `tools/knowledge_gateway_mcp.py`.** Explicit Out of Scope, matching the sibling ticket's own
  identical guard.
- **Do not silently add a `redaction_policy_version` column to `retrieval_provider_result_cache_rows`
  without flagging it** — see Risks item 2. If Plan decides to add the column, it must be recorded
  as a deliberate, documented decision (and likely needs its own migration function name, since
  `cache_migration_plan.md` §2 pre-authorized only `migration_001`/`migration_002` and neither
  includes `ALTER TABLE ADD COLUMN`), not slipped in as an incidental part of this ticket's "real,
  tested logic" scope bullet.
- **Do not reuse a lookup-identity or validity-identity field name from
  `evidence_cache_identity_contract.md` §1/§2 for an unrelated redaction-specific concept**, and vice
  versa — the Non-collapse rule (§3) is a naming discipline this ticket's own dataclasses/return
  types must respect if they carry fields that overlap conceptually with the future cache row shape
  (e.g. do not name a redaction-check's decision field `evidence_fingerprints`).
- **Do not present the secret-scan baseline as more complete than the ratified doc claims.** Any
  docstring/comment this ticket writes describing the 4-pattern ruleset must preserve the "starting
  baseline, not production-complete, security-focused pass still owed" framing verbatim in spirit —
  do not silently drop that disclosure while implementing it as real code, per this ticket's own
  Scope bullet 3's explicit instruction.
