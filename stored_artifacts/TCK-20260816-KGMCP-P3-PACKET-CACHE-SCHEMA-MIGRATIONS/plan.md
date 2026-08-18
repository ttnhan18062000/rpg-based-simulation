---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS

## Architecture-Review Corrections (Pass 1 — NEEDS_CHANGES)

This revision applies exactly two corrections mandated by Architecture Review's first-pass
`NEEDS_CHANGES` ruling. These are **Review-mandated corrections**, not implementer-discovered
deviations — DD1 and DD3 were confirmed sound and are untouched, and the overall table design
(DD5/DD6) was approved and is untouched.

1. **DD2 (version-stamp mechanism) — overturned.** The original DD2 (only `migration_002` hardcodes
   a literal; `migration_001` and the shared `retrieval_cache_schema_version` constant left
   untouched) was ruled wrong: it leaves the constant's own inline comment ("Bumped once per new
   migration function added, never aliased to either sibling constant") permanently false once
   `migration_002` exists, and it misses a third existing test outside the original regression
   surface — `tests/tools/test_knowledge_gateway_redaction.py:482`
   (`TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`),
   which asserts `rc.retrieval_cache_schema_version == 1`. DD2 below is rewritten to the corrected
   mechanism: `migration_001`'s INSERT now stamps a hardcoded literal `1` (decoupled from the mutable
   constant), `migration_002` keeps its own hardcoded literal `2` (this part of the original DD2 was
   already correct), the module-level constant is bumped to `2`, and the one dependent test is
   corrected from `== 1` to `== 2`. See corrected DD2, new Step 3, and new Step 4 below.
2. **DD4 (Non-collapse rule tension) — committed to option (b).** Unresolved Question 2 is no longer
   open: Architecture Review ruled the `freshness`/`verification` columns are approved (required by
   the ticket's own Scope/AC2) but constitute a genuine, intentional divergence from
   `evidence_cache_identity_contract.md` §3's Non-collapse rule Bullet 1, and must be formally
   recorded via a `docs/guidelines/intentional_divergences.md` entry during this ticket's own
   Document-Update phase — not left as an open question. See the corrected "Docs to Update" section
   below for the required entry content (rationale class `Bounded`, verification path pointing at
   `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`).

## Summary

Implement `migration_002_add_level2_tables(conn: sqlite3.Connection) -> None` in
`tools/retrieval_cache.py`, at the exact reserved ordinal (immediately after
`migration_001_add_level1_tables`, immediately before `migration_003_add_redaction_policy_version_column`),
adding one new, wholly independent, `CREATE TABLE IF NOT EXISTS`-only table —
`retrieval_context_packet_cache_rows` — whose 28 columns map 1:1 onto proposal §10.2's Level 2
row-shape bullets and §10.3's `CachedPacket` field list, with one deliberate rename
(`schema_version` → `response_schema_version`, resolving a real naming collision against this
module's own `retrieval_cache_schema_version` DDL-version constant) and every array/dict-shaped
field stored as a JSON-serialized `TEXT` column, mirroring Level 1's already-shipped
`LEVEL1_CACHE_COLUMNS` convention exactly. The single highest-risk decision in this plan —
how `migration_002` stamps `retrieval_cache_generation` without corrupting `migration_001`'s
already-shipped, already-tested version-stamping behavior — is resolved, per Architecture Review's
corrected DD2 (see "Architecture-Review Corrections" above), by fully decoupling both migrations'
on-disk stamps from the mutable module constant: `migration_001`'s INSERT is changed to a hardcoded
literal `1` and `migration_002`'s INSERT keeps its own hardcoded literal `2`, and the module-level
`retrieval_cache_schema_version` constant is then bumped to `2` to honor its own "bump once per new
migration function added" comment. This requires exactly **one existing test correction** —
`tests/tools/test_knowledge_gateway_redaction.py:482`, which asserts the live constant's value
directly — a narrow, Architecture-Review-confirmed correction, not a routed-around gate; the test's
actual intent (axis-independence between the four version constants) is fully preserved, only the
literal expected value changes because the constant's own meaning genuinely changed. A second real
tension — §10.3's `freshness`/`verification` columns sitting on the same lookup-identity-shaped row
as `evidence_cache_identity_contract.md` §3's Non-collapse rule's "never" language — is committed to
option (b) per Architecture Review's ruling: the columns are included exactly as the ticket's own
Scope and AC2 require, and a `docs/guidelines/intentional_divergences.md` entry recording the
divergence is now a required Document-Update-phase deliverable of this plan (see "Docs to Update"
below), not an open question. No read/write logic, no dependency-invalidation logic, and no
redaction/budget enforcement is added — schema only, exactly as this ticket's Out of Scope requires.

## Design Decisions

### DD1 — Table name, table count, and JSON-text-column convention: adopt investigation's resolutions as-is

**New table name: `retrieval_context_packet_cache_rows`.** Confirmed by direct read: neither
`cache_migration_plan.md` (full read) nor `evidence_cache_identity_contract.md` (full read) names
the Level 2 table anywhere beyond generic "the Level 2 tables" (`cache_migration_plan.md:92-94`).
The existing marker-only `retrieval_packet_cache_rows` table already occupies the nearest-sounding
name (`tools/retrieval_cache.py:194-204`, `packet_key_hash` PK) and must never be reused or
confused with the new table (ticket AC4). `retrieval_context_packet_cache_rows` follows the
established `retrieval_<level-concept>_cache_rows` convention
(`retrieval_provider_result_cache_rows` for Level 1, `tools/retrieval_cache.py:230`) and cannot
collide with any existing table name (verified: not present anywhere in
`tools/retrieval_cache.py`'s current source, confirmed by direct read of the full file).

**One table, not a junction table.** Adopted as investigation resolved it: §10.3 treats
`evidence_dependencies[]` as structurally identical in kind to seven other array-shaped
`CachedPacket` fields (`docs/plans/knowledge-gateway-mcp-proposal.md:568-576`, confirmed by direct
read) — nothing in the proposal singles it out for relational treatment, and the existing marker-only
`retrieval_packet_cache_rows` table already proves a plain JSON-text column supports exactly this
invalidation shape in this module today (`check_packet_cache()`'s
`set(current_cited_hashes) != set(json.loads(stored_hashes_json))` against `cited_hashes_json`,
`tools/retrieval_cache.py:486-488` per investigation's direct citation). A junction table would
introduce relational-integrity/join-query machinery this module has never used anywhere and that no
cited doc requests.

**JSON-text-column convention.** Adopted as investigation confirmed directly against
`migration_001`'s real DDL (`tools/retrieval_cache.py:212-262`, read above) and
`LEVEL1_CACHE_COLUMNS` (`tools/retrieval_cache.py:115-142`): every array/dict-shaped Level 1 field is
a plain `TEXT` column holding a caller-pre-serialized `json.dumps(...)` string. This plan applies the
identical convention to all 9 array/dict-shaped Level 2 fields (`entity_ids`, `statements`,
`context_items`, `evidence`, `conflicts`, `evidence_dependencies`, `provenance_providers`,
`providers_consulted_this_call` — arrays; `provider_generations` — dict).

### DD2 — Risk 1 resolution (CORRECTED per Architecture Review Pass 1): both migrations hardcode their own literal target version; the shared `retrieval_cache_schema_version` constant is bumped to `2`

**This section supersedes the original DD2.** The original recommendation (only `migration_002`
hardcodes a literal; `migration_001` and the shared constant left completely untouched) was ruled
wrong by Architecture Review Pass 1 for two reasons, both confirmed sound and not re-litigated here:

1. It leaves the module-level constant's own inline comment
   (`tools/retrieval_cache.py:60-61`: "Bumped once per new migration function added, never aliased
   to either sibling constant") permanently false the moment `migration_002` exists as a second
   migration function and the constant is never bumped.
2. It misses a third existing test outside the original regression surface:
   `tests/tools/test_knowledge_gateway_redaction.py:482`
   (`TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`,
   confirmed by direct read), which asserts `rc.retrieval_cache_schema_version == 1` against the
   **live constant value directly**, not against any generation-table stamped value. Leaving the
   constant at `1` while a second migration exists makes this test pass for the wrong reason —
   it would silently stay green while asserting a now-stale claim about the module's own schema
   state.

**Read directly, not inferred:** `migration_001_add_level1_tables`
(`tools/retrieval_cache.py:212-262`) issues `DELETE FROM retrieval_cache_generation` followed by
`INSERT INTO retrieval_cache_generation (retrieval_cache_schema_version, migrated_at) VALUES (?, ?)`
using the **live module-level `retrieval_cache_schema_version` constant** (`tools/retrieval_cache.py:62`,
currently `1`) at line 260 — not a hardcoded literal. Two existing, currently-passing tests call
`migration_001` in isolation and hardcode the expectation that the *stamped generation-table value*
is exactly `1`: `test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration`
(`tests/tools/test_retrieval_cache.py:375-387`, asserts `schema_version == 1`) and
`test_migration_is_idempotent_when_run_twice` (`tests/tools/test_retrieval_cache.py:389-423`,
asserts `generation_rows == [(1,)]`).

**Also read directly:** `migration_003_add_redaction_policy_version_column`
(`tools/retrieval_cache.py:265-283`) is already-shipped precedent that **not every migration touches
`retrieval_cache_generation`** — it does an `ALTER TABLE ... ADD COLUMN` and never calls `DELETE
FROM retrieval_cache_generation`/`INSERT INTO retrieval_cache_generation` at all, despite
`cache_migration_plan.md` §2's literal text stating every migration "on successful application,
updates `retrieval_cache_generation`" (`cache_migration_plan.md:116-117`). This precedent is
unaffected by this correction and is cited only as background — it does not bear on the constant-vs-
hardcoded-literal question corrected below.

**Corrected mechanism (Architecture-Review-mandated, applied exactly as specified):**

1. `migration_001_add_level1_tables`'s INSERT statement (`tools/retrieval_cache.py:258-261`) is
   changed to stamp a **hardcoded literal `1`** — `VALUES (1, ?)` — instead of reading the live
   `retrieval_cache_schema_version` constant. This decouples the migration's on-disk stamp from the
   mutable global. It is a **value-neutral refactor**: the constant's current value is already `1`,
   so the stamped output is bit-identical to today's behavior. Both existing tests that assert the
   stamped value (`test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration`,
   `test_migration_is_idempotent_when_run_twice`) continue to pass unmodified — confirmed by
   inspection of what each asserts (generation-table row contents, not the live constant) and by the
   fact the hardcoded literal (`1`) equals the constant's pre-bump value.
2. `migration_002_add_level2_tables` keeps its own hardcoded literal `2` in its INSERT — this part of
   the original DD2 was already correct and is unchanged (see Step 2).
3. The module-level `retrieval_cache_schema_version` constant (`tools/retrieval_cache.py:62`) is
   bumped from `1` to `2`, honoring its own pre-existing "bump once per new migration function added"
   comment (`tools/retrieval_cache.py:60-61`, comment text unchanged — it was already correct, the
   value just wasn't following it).
4. `tests/tools/test_knowledge_gateway_redaction.py:482` is corrected from `== 1` to `== 2` — see
   Step 4. This is the one existing-test correction this plan now requires (down from the ticket's
   own originally-posed "narrow the two `TestMigrations` tests" alternative to a single, different,
   smaller correction — the two `TestMigrations` tests need no change at all per point 1 above).

**Why this is more correct than the original DD2, not merely different:** with `migration_001` and
`migration_002` each hardcoding their own literal and neither reading the live constant, bumping the
shared constant to `2` carries **zero risk** of corrupting a future `migration_001`-alone run (the
exact risk the original DD2 was trying to avoid) — `migration_001`'s stamped value is now permanently
`1` regardless of the constant's value, by construction. The constant becomes a pure "highest
migration ordinal shipped" signal, consistent with its own comment, with no coupling to either
migration's actual stamped behavior.

**Other reader of the constant, enumerated:** besides the corrected `migration_001` (no longer reads
it) and `migration_002` (never read it), exactly one other reader exists in the repository today —
`tests/tools/test_knowledge_gateway_redaction.py:482`, corrected in Step 4. No production code path
(`check_*_cache`, `write_*_cache`, `prune`, `cmd_stats`, `_get_level1_connection`,
`_get_connection`, `_init_schema`) reads `retrieval_cache_schema_version` anywhere else (confirmed by
direct read of the full file — the only other occurrence is the DDL column name string
`"retrieval_cache_schema_version"` inside the `CREATE TABLE retrieval_cache_generation` statement in
`migration_001`, which is a column name, not a reference to the Python constant).

**Ordering assumption, stated explicitly:** this plan's tests exercise the chain
`migration_001` → `migration_003` → `migration_002`, matching this module's actual production calling
order today (`_get_level1_connection()`, `tools/retrieval_cache.py:598-607`, calls `migration_001`
then `migration_003`; `migration_002` is not wired into that helper — out of scope, no wiring added).
`migration_002` does not itself verify that `migration_001` was previously applied — no such
verification exists for any migration in this module today (confirmed: `migration_003` does not
verify `migration_001` ran first either), and adding one would be new defensive-verification scope
this ticket does not need to build.

### DD3 — Risk 3 resolution: rename `schema_version` to `response_schema_version`

**Read directly:** `cache_migration_plan.md` §1 (`cache_migration_plan.md:26-48`) states
`retrieval_cache_schema_version` was deliberately named to avoid "the bare, ambiguous string
`schema_version`," citing two other already-scoped version concepts in this vocabulary
(`RETRIEVAL_VERSION`, `retrieval_event_schema_version`). Using the literal bare name `schema_version`
for §10.3's field would reintroduce exactly the ambiguity that naming discipline exists to prevent —
even though §10.3's `schema_version` is a genuinely different, fifth concept: the per-packet
wire-response-schema version. Confirmed by direct read:
`docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json:5` has a
top-level `"schema_version": 1` field, distinct from every DDL/table-shape or event-field-shape
concept. **Chosen column name: `response_schema_version`**, tracing directly to that file's own field.
This is adopted without needing Architecture Review sign-off (the ticket's own prompt frames this one
as "confirm this reasoning is sound and document the exact chosen name," not as a review-gated
judgment call) — the reasoning is sound and the traced source is unambiguous.

### DD4 — Risk 2 (Non-collapse rule vs. `freshness`/`verification`): included per ticket's own Scope/AC; RESOLVED by Architecture Review Pass 1 to option (b) — `intentional_divergences.md` entry required

**Read directly, both docs in full.** `evidence_cache_identity_contract.md` §3
(`evidence_cache_identity_contract.md:100-121`) states two things at different specificity levels:

- The general sentence: "No function, table row, or schema object may expose both a lookup-identity
  field (§1) and a validity-verdict field (§2) keyed by the same primary identity in a way that lets
  a lookup hit be read as a validity result without a separate, explicit validity check step."
- Bullet 1 (concrete): "A lookup-table row (or its equivalent) may carry lookup-identity fields and,
  at most, a status used purely for cache bookkeeping ... **never** a freshness/verification verdict
  about the underlying evidence's current truth."
- Bullet 2 (concrete): "A function that performs a lookup ... must not return a freshness/verification
  field ... Any future addition of a freshness/verification field to one of those return shapes
  without a separate validity-check function is a violation of this rule, not an enhancement."

The new `retrieval_context_packet_cache_rows` table's `packet_id`/`normalized_intent`/
`query_key_hash` columns are structurally lookup-identity-shaped (one field, `normalized_intent`, is
even the literal §1 field name). Bullet 1's "never" language, read literally, forbids exactly the
co-existence this ticket's own §10.3-sourced `freshness`/`verification` columns would create on that
same row. Bullet 2's language, by contrast, is scoped to **function return shapes** — and this
ticket adds no `check_*`/`write_*`-style function for the new table (explicit Out of Scope, guarded
by test 11 in Step 5 below), so bullet 2 is not violated by the letter.

**Resolution (Architecture Review Pass 1, committed — no longer an open question):** the columns are
included in Step 1's `LEVEL2_CACHE_COLUMNS` exactly as proposal §10.2/§10.3 and this ticket's own
Scope/AC2 require — dropping them to sidestep the tension would fail this ticket's own acceptance
criteria. Architecture Review ruled this is a genuine, intentional divergence from §3's Non-collapse
rule Bullet 1 (schema knowingly carries a lookup-identity-shaped row alongside last-computed
`freshness`/`verification` fields) and requires a formal `docs/guidelines/intentional_divergences.md`
entry — option (b) from the original Unresolved Question 2 list, not option (a) (no entry needed) or
option (c) (some other resolution). The entry's required content (rationale class `Bounded`,
verification path) is specified in "Docs to Update" below and is a required Document-Update-phase
deliverable of this plan, not a follow-up left to chance.

### DD5 — Column mapping: proposal §10.2/§10.3 → new table (authoritative for the "matches exactly" test)

`docs/plans/knowledge-gateway-mcp-proposal.md` §10.3 (`:561-593`, read in full) is the literal
28-field `CachedPacket` schema. Every field maps 1:1 to a new column, with exactly one rename (DD3)
and no field added or dropped:

| §10.3 field | Column | Type | Notes |
|---|---|---|---|
| `packet_id` | `packet_id` | `TEXT NOT NULL PRIMARY KEY` | Single-column PK, mirroring the existing marker-only `retrieval_packet_cache_rows`'s own `packet_key_hash TEXT NOT NULL PRIMARY KEY` shape (`tools/retrieval_cache.py:195`) — no composite key invented; §10.3 lists `packet_id` first as a dedicated identifier field, unlike Level 1, which had no separate ID column. |
| `normalized_intent` | `normalized_intent` | `TEXT NOT NULL` | Literal §10.3 name; also the literal `evidence_cache_identity_contract.md` §1 lookup-identity field name — same concept, reused verbatim, no new meaning invented. |
| `query_key_hash` | `query_key_hash` | `TEXT NOT NULL` | Literal §10.3 name. |
| `entity_ids[]` | `entity_ids` | `TEXT NOT NULL` (JSON array) | DD1 convention. |
| `answer` | `answer` | `TEXT` (nullable) | Response schema's own `answer` property is optional, not in its `required` list (`knowledge_context_response.schema.json:7-13`) — a `task_context`-mode packet may have no `answer`. |
| `statements[]` | `statements` | `TEXT NOT NULL` (JSON array) | DD1 convention. |
| `context_items[]` | `context_items` | `TEXT NOT NULL` (JSON array) | §10.3's own name kept verbatim (not renamed to the response schema's `context`, since §10.3 is the authoritative source for this table's shape per the ticket's own Scope). |
| `evidence[]` | `evidence` | `TEXT NOT NULL` (JSON array) | DD1 convention. |
| `conflicts[]` | `conflicts` | `TEXT NOT NULL` (JSON array) | DD1 convention. |
| `evidence_dependencies[]` | `evidence_dependencies` | `TEXT NOT NULL` (JSON array) | DD1 convention; single-column, no junction table (DD1). |
| `provenance_providers[]` | `provenance_providers` | `TEXT NOT NULL` (JSON array) | DD1 convention. |
| `providers_consulted_this_call[]` | `providers_consulted_this_call` | `TEXT NOT NULL` (JSON array) | DD1 convention. |
| `repository_id` | `repository_id` | `TEXT NOT NULL` | §10.3 lists 4 separate scope fields, not Level 1's collapsed `repo_branch_scope` — not a free naming choice (investigation's own structural-difference finding, `docs/plans/knowledge-gateway-mcp-proposal.md:577-580`). |
| `branch` | `branch` | `TEXT NOT NULL` | Per §5's hard-partition rule (`evidence_cache_identity_contract.md:156-159`) — must be its own column, never merged into `repository_id`. |
| `head_commit` | `head_commit` | `TEXT` (nullable) | Per §5 rule 1 (`evidence_cache_identity_contract.md:151-155`), a new commit alone is not a hard invalidation signal — nullable since a packet's compatibility does not strictly require this value to be always known. |
| `working_tree_fingerprint` | `working_tree_fingerprint` | `TEXT` (nullable) | Per §5 rule 3, this is populated by future changed-paths intersection logic (not this ticket's job) — nullable at schema-creation time. |
| `provider_generations{}` | `provider_generations` | `TEXT NOT NULL` (JSON dict) | DD1 convention, dict-shaped. |
| `policy_version` | `policy_version` | `TEXT NOT NULL` | Literal §10.3 name. |
| `schema_version` | `response_schema_version` | `INTEGER NOT NULL` | **Renamed per DD3.** Type `INTEGER` traced to `knowledge_context_response.schema.json:5`'s own `"schema_version": 1` (integer literal). |
| `budget_requested` | `budget_requested` | `INTEGER` | Traced to `knowledge_context_response.schema.json:122` (`"type": "integer"`). |
| `budget_returned` | `budget_returned` | `INTEGER` | Traced to `knowledge_context_response.schema.json:123` (`"type": "integer"`). |
| `status` | `status` | `TEXT NOT NULL` | Enum-ref'd in the response schema (`$ref shared_enums.schema.json#/definitions/status`); stored as `TEXT`, mirroring how `cache_status`/`reason_code` are already stored as plain `TEXT` on the 3 marker-only tables (no enum type in SQLite). |
| `freshness` | `freshness` | `TEXT NOT NULL` | See DD4 — included per ticket Scope/AC2; divergence from the Non-collapse rule ruled option (b) and recorded via Step 6's `intentional_divergences.md` entry. |
| `verification` | `verification` | `TEXT NOT NULL` | See DD4 — same as above. |
| `lifecycle` | `lifecycle` | `TEXT` (nullable) | No contract-literal enum or `required` reference found for `lifecycle` in any of the three read contract docs or the response schema — Plan could not confirm a fixed value set exists yet; stored as an open `TEXT` column, nullable, following the same "deliberately open string, not a closed enum" precedent the response schema itself uses for its own `cache` field (`knowledge_context_response.schema.json:28-31`). |
| `created_at` | `created_at` | `REAL NOT NULL` | Matches the existing `time.time()`-stamped convention used by every other table in this module. |
| `last_validated_at` | `last_validated_at` | `REAL` (nullable) | Mirrors Level 1's `last_hit_at` nullable-`REAL` shape (`tools/retrieval_cache.py:250`). |
| `hit_count` | `hit_count` | `INTEGER NOT NULL DEFAULT 0` | Matches Level 1's identical column (`tools/retrieval_cache.py:251`). |

This table is the literal content of `LEVEL2_CACHE_COLUMNS` (Step 1) and the new table's `CREATE
TABLE` DDL (Step 2), and is the authoritative definition of "matches §10.2/§10.3 exactly" for Step
3's structural test.

### DD6 — Not added to `_TABLE_NAME_BY_ALIAS` / `MAY_LIST_COLUMNS`, no CLI wiring, no read/write function

Mirrors the Level 1 precedent's own DD7 exactly, confirmed by direct read of the current file:
`_TABLE_NAME_BY_ALIAS` (`tools/retrieval_cache.py:696-700`) has exactly 3 entries today
(`index`/`query`/`packet`, mapping to the 3 marker-only tables) — Level 1's table was never added to
it, and this ticket does not add Level 2's table to it either, per this ticket's own Out of Scope
(no lifecycle/GC policy decided for the new table yet, `redaction_retention_policy.md` §10 is
explicit that this is future scope). `_COMMAND_DISPATCH`/`_build_parser()` (5 entries today, no
`migrate`/`rebuild`) is not touched. No `check_*`/`write_*`-style function is added for the new
table.

## Steps

### Step 1 — Add the `LEVEL2_CACHE_COLUMNS` allowlist constant

**Files:** `tools/retrieval_cache.py`

**Change:** Add a new module-level frozenset constant immediately after `LEVEL1_CACHE_COLUMNS`
(`tools/retrieval_cache.py:115-142`), listing all 28 columns from DD5's mapping table:

```python
# Column set for the new Level 2 assembled-context-packet cache table
# (retrieval_context_packet_cache_rows), mapped 1:1 onto
# docs/plans/knowledge-gateway-mcp-proposal.md §10.2's Level 2 row-shape bullets and §10.3's
# CachedPacket field list — see plan.md DD5 for the full per-column provenance table. One field is
# renamed from §10.3's literal `schema_version`: `response_schema_version` (DD3), to avoid colliding
# with this module's own retrieval_cache_schema_version DDL-version constant
# (cache_migration_plan.md §1). NOT a write-path validation allowlist (unlike MAY_LIST_COLUMNS) —
# this ticket ships no write function for this table; this constant exists so the structural test
# below and the later read-write-wiring ticket have one documented source of truth for the column
# set, not two.
LEVEL2_CACHE_COLUMNS: frozenset[str] = frozenset(
    {
        "packet_id",
        "normalized_intent",
        "query_key_hash",
        "entity_ids",
        "answer",
        "statements",
        "context_items",
        "evidence",
        "conflicts",
        "evidence_dependencies",
        "provenance_providers",
        "providers_consulted_this_call",
        "repository_id",
        "branch",
        "head_commit",
        "working_tree_fingerprint",
        "provider_generations",
        "policy_version",
        "response_schema_version",
        "budget_requested",
        "budget_returned",
        "status",
        "freshness",
        "verification",
        "lifecycle",
        "created_at",
        "last_validated_at",
        "hit_count",
    }
)
```

**Do NOT touch:** `LEVEL1_CACHE_COLUMNS` (`tools/retrieval_cache.py:115-142`) itself — no field
added, removed, or reordered in it; `MAY_LIST_COLUMNS` (`tools/retrieval_cache.py:87-106`) — do not
add any of these 28 names into it (DD6).

**Verify:** `test_new_level2_table_column_set_matches_proposal_section_10_3_cachedpacket_field_list`
(Step 5).

### Step 2 — Implement `migration_002_add_level2_tables(conn)`, inserted between `migration_001` and `migration_003`

**Files:** `tools/retrieval_cache.py`

**Change:** Insert a new function **textually between** the end of `migration_001_add_level1_tables`
(closing `conn.commit()` at `tools/retrieval_cache.py:262`) and the `def
migration_003_add_redaction_policy_version_column` line (`tools/retrieval_cache.py:265`) — this
exact source position is what Step 5's ordinal test checks (AC1 requires ordinal 2, "immediately
before the already-landed `migration_003_...`"). Note the `retrieval_cache_generation` INSERT below
already uses migration_002's own hardcoded literal `2` (unchanged from the original DD2 — Architecture
Review confirmed this part was already correct); what changes under the corrected DD2 is
`migration_001`'s own INSERT and the module constant, both handled separately in Step 3:

```python
def migration_002_add_level2_tables(conn: sqlite3.Connection) -> None:
    """Adds the Level 2 assembled-context-packet cache table, per cache_migration_plan.md §2 and
    proposal §10.2/§10.3. CREATE TABLE IF NOT EXISTS only — additive, never touches the 3 legacy
    marker-only tables or the Level 1 retrieval_provider_result_cache_rows table. Idempotent: safe
    to call again on a database that already has this migration applied. Not called by
    _get_connection(), _init_schema(), or _get_level1_connection() (see plan.md DD6/Out of Scope) —
    must be invoked directly. Per plan.md DD2 (Architecture-Review-corrected mechanism): stamps
    retrieval_cache_generation with its own hardcoded literal target version (2), scoped to this
    migration's own INSERT only. Neither this function nor migration_001 reads the live
    retrieval_cache_schema_version module constant when stamping retrieval_cache_generation --
    migration_001's own INSERT independently hardcodes its own literal (1, see Step 3) -- so the
    module constant (bumped to 2 in Step 3) can be updated freely for introspection purposes without
    risk of retroactively changing either migration's stamped output.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retrieval_context_packet_cache_rows (
            packet_id TEXT NOT NULL PRIMARY KEY,
            normalized_intent TEXT NOT NULL,
            query_key_hash TEXT NOT NULL,
            entity_ids TEXT NOT NULL,
            answer TEXT,
            statements TEXT NOT NULL,
            context_items TEXT NOT NULL,
            evidence TEXT NOT NULL,
            conflicts TEXT NOT NULL,
            evidence_dependencies TEXT NOT NULL,
            provenance_providers TEXT NOT NULL,
            providers_consulted_this_call TEXT NOT NULL,
            repository_id TEXT NOT NULL,
            branch TEXT NOT NULL,
            head_commit TEXT,
            working_tree_fingerprint TEXT,
            provider_generations TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            response_schema_version INTEGER NOT NULL,
            budget_requested INTEGER,
            budget_returned INTEGER,
            status TEXT NOT NULL,
            freshness TEXT NOT NULL,
            verification TEXT NOT NULL,
            lifecycle TEXT,
            created_at REAL NOT NULL,
            last_validated_at REAL,
            hit_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute("DELETE FROM retrieval_cache_generation")
    conn.execute(
        "INSERT INTO retrieval_cache_generation "
        "(retrieval_cache_schema_version, migrated_at) VALUES (?, ?)",
        (2, time.time()),
    )
    conn.commit()
```

Note: `retrieval_cache_generation` itself (the single-row metadata table) is created by
`migration_001`, not here — `migration_002` assumes it already exists, consistent with this plan's
own stated realistic ordering (`migration_001` runs before `migration_002` — DD2's "Ordering
assumption" paragraph). If `migration_002` is ever called on a connection where `migration_001` has
never run, `DELETE FROM retrieval_cache_generation` / `INSERT INTO ...` will raise
`sqlite3.OperationalError: no such table` — this is intentional, matching the "no auto-apply,
explicit invocation only" design already established for `migration_001` (no `migrate` entry point
exists to paper over out-of-order calls) — not a defect this ticket needs to guard against with new
code.

**Other writers to `retrieval_cache_generation` (enumerated, per fact-verification requirement):**
exactly one other writer exists in the file today — `migration_001_add_level1_tables`
(`tools/retrieval_cache.py:256-261`), which also does `DELETE FROM retrieval_cache_generation` +
`INSERT ...`. As of this ticket (Step 3), that INSERT stamps its own hardcoded literal `1` rather
than reading the live module constant — see Step 3, not this step; Step 2 itself makes no edit to
`migration_001`. `migration_003_add_redaction_policy_version_column`
(`tools/retrieval_cache.py:265-283`) does **not** write to this table at all (confirmed by direct
read — no `retrieval_cache_generation` reference anywhere in its body). No other function in the
file (`check_*_cache`, `write_*_cache`, `prune`, `cmd_stats`, `_get_level1_connection`) references
`retrieval_cache_generation`. Ordering interaction: because this plan's own test chain calls
`migration_001` then `migration_003` then `migration_002` (DD2's stated realistic order,
matching `_get_level1_connection()`'s real production call order for the first two), the row ends up
holding `migration_002`'s literal `2` as the last writer — a simple last-write-wins `DELETE`+`INSERT`
pattern, no concurrent-writer race is introduced (same single-connection, single-threaded call
pattern every existing writer already uses; no new threading/multiprocessing is introduced by this
step).

**Other writers to `retrieval_context_packet_cache_rows` (the new table itself):** none — this ticket
adds no `write_*`-style function (Out of Scope; guarded by test 11 in Step 5).

**Do NOT touch (in this step):** `_init_schema()` (`tools/retrieval_cache.py:161-205`) — do not add
the new `CREATE TABLE` there; `migration_001_add_level1_tables`'s own body
(`tools/retrieval_cache.py:212-262`) — **this step** makes zero edits to it (its INSERT is edited
separately, in Step 3, not as part of implementing `migration_002`);
`migration_003_add_redaction_policy_version_column`
(`tools/retrieval_cache.py:265-283`) — zero edits, only insert the new function *before* it in source
order; `retrieval_index_cache_rows`, `retrieval_query_cache_rows`, `retrieval_packet_cache_rows`,
`retrieval_provider_result_cache_rows` — no `ALTER TABLE` against any of them; no `PRAGMA`,
`busy_timeout`, `chmod`, or `import os` anywhere in this function or file.

**Verify:** `test_migration_002_function_exists_with_reserved_name_and_ordinal`,
`test_migration_002_applies_cleanly_to_a_fresh_database`,
`test_migration_002_applies_cleanly_on_top_of_legacy_only_schema_with_zero_data_loss`,
`test_migration_002_applies_cleanly_on_top_of_level1_already_migrated_schema_with_zero_data_loss`,
`test_migration_002_is_idempotent_when_run_twice`,
`test_retrieval_cache_schema_version_correctly_reflects_new_schema_state_after_migration_002`,
`test_new_level2_table_name_does_not_collide_with_existing_marker_only_packet_table` (all Step 5).

### Step 3 — Decouple `migration_001`'s version stamp from the mutable module constant; bump the constant to 2 (Architecture-Review-mandated correction)

**Files:** `tools/retrieval_cache.py`

**Change:** Two edits in the same file, applied together (per corrected DD2 above):

1. In `migration_001_add_level1_tables` (`tools/retrieval_cache.py:212-262`), change the INSERT call
   at lines 258-261 from:

   ```python
   conn.execute(
       "INSERT INTO retrieval_cache_generation "
       "(retrieval_cache_schema_version, migrated_at) VALUES (?, ?)",
       (retrieval_cache_schema_version, time.time()),
   )
   ```

   to:

   ```python
   conn.execute(
       "INSERT INTO retrieval_cache_generation "
       "(retrieval_cache_schema_version, migrated_at) VALUES (?, ?)",
       (1, time.time()),
   )
   ```

   i.e. replace the `retrieval_cache_schema_version` tuple element (the live module constant, read
   at `tools/retrieval_cache.py:62`) with the hardcoded literal `1`. Nothing else in the function
   changes — the `CREATE TABLE` DDL, the `DELETE FROM retrieval_cache_generation` call, and the
   column name string `"retrieval_cache_schema_version"` in the SQL text are untouched (that string
   is a DDL column name, not the Python constant, and is out of scope for this edit). Add a short
   inline comment above the changed line citing plan.md DD2 and noting this decouples the stamp from
   the mutable constant.

2. Bump the module-level constant at `tools/retrieval_cache.py:62` from:

   ```python
   retrieval_cache_schema_version: int = 1
   ```

   to:

   ```python
   retrieval_cache_schema_version: int = 2
   ```

   The existing comment immediately above it (`tools/retrieval_cache.py:58-61`, "DDL/table-shape
   version for this module's migrations ... Bumped once per new migration function added, never
   aliased to either sibling constant") is **not edited** — it was already correct; only the value
   was out of date relative to it, which this edit fixes now that `migration_002` (a second migration
   function) exists.

**Value-neutrality check for edit 1 (why the two existing `TestMigrations` tests are unaffected):**
before this edit, the live constant's value is `1`, so `migration_001` already stamps `1` into
`retrieval_cache_generation` today. After this edit, `migration_001` stamps the hardcoded literal
`1` — the identical value, by construction. `test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration`
(`tests/tools/test_retrieval_cache.py:375-387`, asserts `schema_version == 1`) and
`test_migration_is_idempotent_when_run_twice` (`tests/tools/test_retrieval_cache.py:389-423`,
asserts `generation_rows == [(1,)]`) both call `migration_001` in isolation on a fresh connection —
neither test reads the module constant directly, both only inspect the generation-table row contents
via SQL `SELECT`. Since the stamped value is unchanged (`1` before and after), both tests require
**zero edits** and continue to pass.

**Other reader of the bumped constant (enumerated, per fact-verification requirement):** exactly one
reader exists outside `tools/retrieval_cache.py` itself —
`tests/tools/test_knowledge_gateway_redaction.py:482`
(`TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`), which
asserts `rc.retrieval_cache_schema_version == 1` directly against the live constant. This test
**does** need correction because it reads the constant's value directly, unlike the two
`TestMigrations` tests above which read the generation-table row instead — see Step 4. No other
file in the repository references `retrieval_cache_schema_version` as a bare name (confirmed:
`migration_002`'s own INSERT uses its own hardcoded literal `2`, never the constant — Step 2/DD2).

**Do NOT touch:** `migration_001_add_level1_tables`'s `CREATE TABLE IF NOT EXISTS
retrieval_cache_generation` DDL text — only the INSERT's value tuple changes, not any column
definition; `migration_002_add_level2_tables`'s own hardcoded `2` (Step 2) — already correct, not
touched by this step; `migration_003_add_redaction_policy_version_column`'s body
(`tools/retrieval_cache.py:265-283`) — no `retrieval_cache_generation` reference exists there to
touch; the constant's own comment text (`tools/retrieval_cache.py:58-61`) — value only, comment
unedited since it was already correct.

**Verify:** existing `test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration`
and `test_migration_is_idempotent_when_run_twice` (both `tests/tools/test_retrieval_cache.py`,
`TestMigrations` class) continue passing unmodified — confirms value-neutrality of edit 1;
`test_retrieval_cache_schema_version_correctly_reflects_new_schema_state_after_migration_002`
(Step 5, `TestLevel2Migrations`) confirms the full chain and the constant's new value of `2`.

### Step 4 — Correct `tests/tools/test_knowledge_gateway_redaction.py:482` from `== 1` to `== 2` (Architecture-Review-mandated correction)

**Files:** `tests/tools/test_knowledge_gateway_redaction.py`

**Change:** In `TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`
(`tests/tools/test_knowledge_gateway_redaction.py:479-489`, confirmed by direct read), change line
482 from:

```python
        assert rc.retrieval_cache_schema_version == 1
```

to:

```python
        assert rc.retrieval_cache_schema_version == 2
```

No other line in this test changes. The test's actual intent — confirming
`redaction_policy_version`, `RETRIEVAL_VERSION`, `retrieval_cache_schema_version`, and
`retrieval_event_schema_version` are four axis-independent module constants, never aliased to one
another, verified via the four `assert ... == 1`/`not in dir(...)` lines and the trailing comment
"Same value today is a coincidence, not a shared identity" — is fully preserved. Only the expected
literal for `retrieval_cache_schema_version` changes, because Step 3 genuinely changed that
constant's value (it is no longer "today" a coincidental `1` shared with the other three constants;
`retrieval_cache_schema_version` is now `2` while the other three remain `1`, which if anything makes
the test's own "coincidence, not shared identity" point more visibly true, not less). This is a
narrow, Architecture-Review-confirmed correction to a test's literal expected value — not an edit
that routes around a gate or weakens what the test verifies.

**Do NOT touch:** the other three `assert ... == 1` lines in this test (`kgr.redaction_policy_version
== 1`, `rc.RETRIEVAL_VERSION == 1`, `re_mod.retrieval_event_schema_version == 1`) — none of those
three constants are touched by this ticket; the five `not in dir(...)` lines; the class's sibling
method `test_redaction_policy_version_is_stamped_on_every_write_decision`; every other test class in
this file (`TestSourceTypeClassification`, `TestRedactionRules`, and all others — full inventory in
test_plan.md's updated Regression Surface, see "Test-Plan Updates (test_plan.md)" below).

**Verify:** `tests/tools/test_knowledge_gateway_redaction.py::TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`
passes with the corrected literal; full-file run
`pytest tests/tools/test_knowledge_gateway_redaction.py -v` shows no other test in the file affected.

### Step 5 — Add the `TestLevel2Migrations` test class

**Files:** `tests/tools/test_retrieval_cache.py`

**Change:** Add a new `class TestLevel2Migrations:` block, placed after `TestMigration003`
(`tests/tools/test_retrieval_cache.py:742-786`) and before `TestProviderResultCacheStats`
(`tests/tools/test_retrieval_cache.py:786`), containing all 12 tests exactly as specified in
`test_plan.md`'s "New Tests Required" section (this plan does not restate their bodies — test_plan.md
is the authoritative spec for each test's assertions):

1. `test_migration_002_function_exists_with_reserved_name_and_ordinal`
2. `test_migration_002_applies_cleanly_to_a_fresh_database`
3. `test_migration_002_applies_cleanly_on_top_of_legacy_only_schema_with_zero_data_loss`
4. `test_migration_002_applies_cleanly_on_top_of_level1_already_migrated_schema_with_zero_data_loss`
   — run in the order `migration_001` → `migration_003` → `migration_002` (DD2's stated realistic
   chain), not any other ordering.
5. `test_new_level2_table_column_set_matches_proposal_section_10_3_cachedpacket_field_list` —
   asserts `PRAGMA table_info(retrieval_context_packet_cache_rows)`'s column-name set equals
   `rc.LEVEL2_CACHE_COLUMNS` exactly (Step 1).
6. `test_migration_002_is_idempotent_when_run_twice`
7. `test_migration_002_does_not_alter_existing_marker_only_or_level1_table_column_sets`
8. `test_retrieval_cache_schema_version_correctly_reflects_new_schema_state_after_migration_002` —
   part (a) uses the full chain `migration_001` → `migration_003` → `migration_002` and asserts the
   generation row reads `2` (DD2); part (b) uses `migration_001` **alone**, on a separate connection,
   and asserts the generation row reads `1` unchanged — the direct regression guard for DD2/Risk 1.
9. `test_evidence_dependencies_column_is_json_text_and_supports_set_intersection_like_the_existing_marker_only_packet_table`
10. `test_new_level2_table_name_does_not_collide_with_existing_marker_only_packet_table`
11. `test_no_actual_read_write_functions_added_for_the_new_level2_table`
12. `test_no_pragma_busy_timeout_chmod_or_os_import_introduced_by_level2_migration`

**Do NOT touch:** any existing test class or method in this file (`TestIndexCache`, `TestQueryCache`,
`TestPacketCache`, `TestMayListEnforcement`, `TestStaticGuards`, `TestPrune`, `TestMigrations`,
`TestRetrievalVersionAndManifest`, `TestCrashRecovery`, `TestProviderResultCache`,
`TestMigration003`, `TestProviderResultCacheStats`) — all must keep passing unmodified, in
particular `TestMigrations`'s two version-stamp tests (see DD2 — no edit needed or permitted here).

**Verify:** `pytest tests/tools/test_retrieval_cache.py -v` (full file, all existing + 12 new tests
pass).

### Step 6 — Document-Update phase: add the DD4 `intentional_divergences.md` entry (Architecture-Review-mandated, committing Unresolved Question 2 to option (b))

**Files:** `docs/guidelines/intentional_divergences.md`

**Phase:** Document-Update (not Implement) — this step runs after Steps 1-5 land, in this ticket's
own Document-Update phase, per the project's standard workflow ordering. It is listed here as a plan
Step, not left as a passive "Docs to Update" bullet, because Architecture Review ruled DD4's
Unresolved Question 2 must be committed to option (b) explicitly, not merely mentioned in passing.

**Change:** Read directly and confirmed: `docs/guidelines/intentional_divergences.md` has a §1
"Divergence Summary Table" (`:12-41`, columns `Subsystem | Feature | Rationale Class | Status`, one
row per entry) and a §2 "Detailed Records" (`:42` onward, per-entry fields confirmed by reading the
first entry, `2.1 Strict Channeling Enforcement`, `:44-49`: `**Subsystem**`, `**Old Behavior**`,
`**New Behavior**`, `**Rationale**`, `**Verification**`). Add one new §1 summary row and one new §2
detailed-record entry, following both formats exactly:

- **§1 row:** `Subsystem` = `Knowledge Gateway MCP / Packet Cache`; `Feature` =
  `Level 2 Packet-Cache Freshness/Verification Column Co-location`; `Rationale Class` = `Bounded`;
  `Status` = `RATIFIED` (Architecture Review's ruling on DD4/Unresolved Question 2 is the ratification
  — no separate approval step is pending).
- **§2 entry**, mirroring the confirmed 5-field layout:
  - **Subsystem**: Knowledge Gateway MCP / Packet Cache.
  - **Old Behavior**: no equivalent — this is a new table (`retrieval_context_packet_cache_rows`,
    `tools/retrieval_cache.py`, `migration_002_add_level2_tables`), not a modification of prior
    behavior; state this explicitly rather than fabricating a prior state.
  - **New Behavior**: the new table carries `freshness` and `verification` columns on the same row as
    lookup-identity fields (`packet_id`, `normalized_intent`, `query_key_hash`), which
    `evidence_cache_identity_contract.md` §3's Non-collapse rule Bullet 1
    (`evidence_cache_identity_contract.md:100-121`) says a lookup-table row should "never" carry.
  - **Rationale**: `Bounded`. The divergence is schema-only and explicitly bounded: no lookup
    function exists on this table yet (this ticket adds no `check_*`/`write_*`-style function — DD6,
    Step-5-test-11-guarded), so Bullet 2's function-return-shape rule is not violated by this ticket.
    The wire contract's own `required: [status, freshness, verification, ...]` list (traced in DD5 to
    `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`)
    operationally justifies persisting last-computed values as row state.
  - **Verification**: `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING` (the next ticket in this
    ticket's own sibling sequence, confirmed present in
    `tickets/todos/knowledge-gateway-mcp-phase3/`) must add a test asserting that whatever lookup
    function it introduces for `retrieval_context_packet_cache_rows` never returns the raw
    `freshness`/`verification` column values off a row without a separate, explicit revalidation step
    first — i.e. Bullet 2 stays enforced procedurally by that ticket's own function design, even
    though Bullet 1's schema-level "never" is knowingly overridden by this ticket's table shape. This
    obligation must be stated explicitly in the entry's own **Verification** field text (not only in
    this plan) so the READ-WRITE-WIRING ticket's own investigation phase finds it via normal
    doc/parity-search rather than depending on this plan being re-read.

**Do NOT touch:** any other row in §1 or entry in §2 of `docs/guidelines/intentional_divergences.md`;
`evidence_cache_identity_contract.md` itself — never edited to weaken or reinterpret §3 (frozen
contract doc, Scope Guards).

**Verify:** manual review during Document-Update phase confirms the entry exists with all three
required fields above; no automated test is required by this plan for this step's own content (doc
entries are not test-verified in this repo's pattern), but the entry's *existence* is a Definition-of-
Done gate item ("No important decision is undocumented") and is checked by `done-checker` before this
ticket can move to `tickets/done/`.

## Scope Guards

- No `PRAGMA`, `busy_timeout`, `chmod`, or `import os` anywhere in `tools/retrieval_cache.py`
  (hard-enforced by `tests/docs/test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_implemented`,
  belt-and-suspenders guarded again by Step 5's test 12).
- No `ALTER TABLE` against `retrieval_index_cache_rows`, `retrieval_query_cache_rows`,
  `retrieval_packet_cache_rows`, or `retrieval_provider_result_cache_rows` — additive-only, one new
  `CREATE TABLE IF NOT EXISTS` only.
- No edit to `_init_schema()` or `migration_003_add_redaction_policy_version_column`'s body —
  `migration_002` is inserted between `migration_001` and `migration_003` in source order (Step 2),
  never merged into or altering either. `migration_001_add_level1_tables`'s body **is** edited, but
  only in the single, narrow way specified in Step 3 (the INSERT's value tuple) — no other line of
  `migration_001` changes (Architecture-Review-mandated correction to the original DD2/Scope Guards,
  see "Architecture-Review Corrections" at the top of this plan).
- The module-level `retrieval_cache_schema_version` constant's **value** (`tools/retrieval_cache.py:62`)
  is edited by this plan (bumped `1` → `2`, Step 3) — this reverses the original plan's guard, per
  Architecture Review's corrected DD2. The constant's **comment** (`tools/retrieval_cache.py:58-61`)
  is not edited — it was already correct.
- No edit to `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, or
  `tools/knowledge_gateway_mcp.py` — not read, not opened, not imported by any step in this plan
  (ticket AC7).
- No `migrate` or `rebuild` CLI subcommand added to `_build_parser()`/`_COMMAND_DISPATCH`
  (`cache_migration_plan.md` §5 freeze).
- No `check_*`/`write_*`-style function added for `retrieval_context_packet_cache_rows` — schema
  only (guarded by Step 5 test 11).
- No dependency-invalidation logic beyond the raw `evidence_dependencies` column existing — no
  junction table, no relational dependency-tracking machinery (DD1).
- No redaction/secret-scanning/size-cap enforcement logic against `answer`/`statements`/
  `context_items`/`evidence` — schema only; the 64 KiB per-row cap question
  (`redaction_retention_policy.md` §5) is explicitly out of this ticket's job, see "Flagged, Not This
  Ticket's Job" below.
- No new column added to `MAY_LIST_COLUMNS`, and `retrieval_context_packet_cache_rows` is never
  added to `_TABLE_NAME_BY_ALIAS` (DD6).
- No edit to `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` or
  `evidence_cache_identity_contract.md` — both frozen, from DONE tickets. (The DD4 divergence is
  recorded in `docs/guidelines/intentional_divergences.md` instead, per Step 6/"Docs to Update"
  below — never by editing the frozen contract docs themselves.)
- No `docs/parity_ledger/` edit as part of this plan's Steps — deferred to this ticket's own later
  Parity phase (see Parity Ledger — Deferred below).
- No second SQLite database file created — `CACHE_DB_PATH` (`tools/retrieval_cache.py:70`) is not
  reassigned or duplicated anywhere.
- No `ContextPacket` class defined or imported in `tools/retrieval_cache.py` (guarded by
  `tests/tools/test_context_packet_assembler.py::TestWorkflowIsolationGuards::test_assembler_does_not_import_contextpacket_from_retrieval_cache`).
- No edit to `tests/tools/test_kgmcp_measurement_baseline.py` — `tools/retrieval_cache.py` is already
  excluded from its banned-edit-path tuple (confirmed by direct read,
  `tests/tools/test_kgmcp_measurement_baseline.py:343-361`); nothing to correct this time.
- In `tests/tools/test_knowledge_gateway_redaction.py`, only the single literal at line 482 is edited
  (Step 4) — no other line, assertion, or test method in that file is touched.

## Dependency Map

- Step 1 (`LEVEL2_CACHE_COLUMNS`) has no dependency; can be implemented first.
- Step 2 (`migration_002_add_level2_tables`) depends on Step 1 — its `CREATE TABLE` DDL must match
  `LEVEL2_CACHE_COLUMNS` exactly (DD5).
- Step 3 (decouple `migration_001`'s stamp; bump the constant) has no dependency on Steps 1-2; it can
  be implemented independently, but must land before Step 4 (Step 4's corrected literal, `2`, is only
  correct once Step 3's constant bump has landed).
- Step 4 (correct `test_knowledge_gateway_redaction.py:482`) depends on Step 3 (see above).
- Step 5 (`TestLevel2Migrations`) depends on Steps 1 and 2 both existing (tests call
  `rc.migration_002_add_level2_tables` directly and assert against `rc.LEVEL2_CACHE_COLUMNS`) and on
  Step 3 (test 8's part (a) asserts the post-`migration_002` generation row against the corrected
  chain, and depends on `migration_001`'s stamp already being decoupled per Step 3 for its part (b)
  assertion to be meaningful).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `migration_002_add_level2_tables(conn)` exists, exact reserved name, ordinal 2 (immediately before `migration_003`) | Step 2 (source-order insertion) | `test_migration_002_function_exists_with_reserved_name_and_ordinal` (Step 5) |
| AC2 — new table's columns match §10.2/§10.3 exactly | Steps 1, 2 (DD5 mapping table is the authoritative definition of "exactly") | `test_new_level2_table_column_set_matches_proposal_section_10_3_cachedpacket_field_list` (Step 5) |
| AC3 — migration applies cleanly/idempotently against fresh DB, legacy-only DB, and Level-1-already-migrated DB, zero data loss | Step 2 | `test_migration_002_applies_cleanly_to_a_fresh_database`, `test_migration_002_applies_cleanly_on_top_of_legacy_only_schema_with_zero_data_loss`, `test_migration_002_applies_cleanly_on_top_of_level1_already_migrated_schema_with_zero_data_loss`, `test_migration_002_is_idempotent_when_run_twice` (Step 5) |
| AC4 — `retrieval_packet_cache_rows` byte-for-byte unmodified | Step 2 (additive-only; DD1's distinct name choice) | `test_migration_002_does_not_alter_existing_marker_only_or_level1_table_column_sets`, `test_new_level2_table_name_does_not_collide_with_existing_marker_only_packet_table` (Step 5) |
| AC5 — `retrieval_provider_result_cache_rows` (Level 1) and its columns unmodified | Step 2 | `test_migration_002_does_not_alter_existing_marker_only_or_level1_table_column_sets` (Step 5) |
| AC6 — `knowledge-index/retrieval_cache.db` remains the single cache database file | Step 2 (no new `CACHE_DB_PATH` value or connection target introduced) | Verify-phase manual check: `grep -n "CACHE_DB_PATH" tools/retrieval_cache.py` shows one assignment (`:70`), unchanged |
| AC7 — `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_mcp.py` byte-unchanged | No step touches these files (Scope Guards) | Verify-phase: `git diff --stat HEAD -- tools/knowledge_gateway_router.py tools/knowledge_gateway_packet_assembly.py tools/knowledge_gateway_mcp.py` is empty |
| AC8 — schema-valid `docs/parity_ledger/infrastructure.yaml` entry added | Not this plan's Steps — deferred to this ticket's own Parity phase (see Parity Ledger — Deferred below); next available ID confirmed `INFRA-346` (current max is `INFRA-345`, confirmed by direct grep of the live file) | Parity phase's own schema-validation gate |

Note: AC1-AC8 above are unchanged by both Architecture-Review corrections — neither correction adds,
removes, or reinterprets any ticket AC. Steps 3-4 (the DD2 correction) and the DD4 divergence-entry
requirement (Step 6/"Docs to Update") are corrections to *how* this plan satisfies the existing ACs
correctly, not new scope.

## Resolved by Architecture Review (Pass 1) — formerly "Unresolved Questions"

Both items below were flagged as open questions in the original plan and have now been ruled on by
Architecture Review's first pass. Neither is open any longer; Implement must follow the ruling
exactly as stated, not re-litigate it.

1. **DD2 — `migration_002`'s version-stamping mechanism — RULING: the original recommendation
   (option scoped only to `migration_002`) was overturned.** Architecture Review ruled the corrected
   mechanism in DD2 above: `migration_001`'s INSERT is changed to a hardcoded literal `1` (Step 3),
   `migration_002` keeps its own hardcoded literal `2` (unchanged, Step 2), the shared
   `retrieval_cache_schema_version` module constant is bumped to `2` (Step 3), and
   `tests/tools/test_knowledge_gateway_redaction.py:482` is corrected from `== 1` to `== 2` (Step 4).
   No further sign-off is needed on this point; Implement follows Steps 2-4 as specified.
2. **DD4 — `freshness`/`verification` columns vs. the Non-collapse rule's "never" language — RULING:
   option (b).** Architecture Review confirmed the columns are approved (required by the ticket's own
   Scope/AC2) and ruled this is a genuine, intentional divergence from
   `evidence_cache_identity_contract.md` §3's Non-collapse rule Bullet 1, requiring a
   `docs/guidelines/intentional_divergences.md` entry (rationale class `Bounded`) added during this
   ticket's own Document-Update phase — Step 6 above. No further sign-off is needed on this point;
   Implement/Document-Update follows Step 6 as specified.

## Flagged, Not This Ticket's Job (carried forward, not a Plan decision)

- **`redaction_retention_policy.md` §5's 64 KiB per-row payload cap has no Level-2-specific
  carve-out**, despite a Level 2 packet row structurally aggregating multiple providers'
  `context_items`/`evidence`/`statements` (§10.2: "Stores the final bounded packet returned to an
  agent"). Confirmed by direct read: §5 (`redaction_retention_policy.md:119-146`) states the cap
  plainly with no per-level exception language. This ticket does not decide or enforce anything about
  this — schema only, no redaction/size-cap enforcement is in scope (ticket's own Out of Scope). This
  is explicit required context for `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s and
  `TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT`'s own future verification work — not
  something this schema ticket resolves. No step in this plan attempts to enforce, raise, or
  special-case the cap for the new table.

## Docs to Update (for Document-Update phase)

- `docs/parity_ledger/infrastructure.yaml`: new entry `INFRA-346` (confirmed next-available ID)
  describing `migration_002_add_level2_tables()`, `LEVEL2_CACHE_COLUMNS`, and
  `retrieval_context_packet_cache_rows`'s real column set, with real `tools/retrieval_cache.py`
  line-number evidence once Steps 1-5 land. Not written by this plan (deferred to Parity phase).
- `cache_migration_plan.md`: **must NOT be edited** — frozen design-only, per its own header and the
  Level 1 precedent's identical Anti-Drift Hazard.
- `evidence_cache_identity_contract.md`: **must NOT be edited** by this plan's own Steps — frozen
  contract doc, §3 not weakened or reinterpreted. The DD4 divergence is recorded separately (below),
  never by editing this file.
- `docs/guidelines/intentional_divergences.md`: **required** new entry (no longer contingent —
  Architecture Review ruled DD4/Unresolved Question 2 to option (b)), added in Step 6 above. Full
  required content (§1 summary row, §2 detailed-record fields, rationale class `Bounded`,
  verification path naming `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s future
  obligation) is specified in Step 6, not restated here.

## Parity Ledger — Deferred

Not written by this plan or by Implement — flagged here for this ticket's own later Parity phase:

- **New entry `INFRA-346`** (confirmed next-available ID: real max existing ID in
  `docs/parity_ledger/infrastructure.yaml` is `INFRA-345`, confirmed by direct grep of the live file)
  describing `migration_002_add_level2_tables()`, `LEVEL2_CACHE_COLUMNS`, and
  `retrieval_context_packet_cache_rows`, with real `tools/retrieval_cache.py` line-number evidence
  once Steps 1-5 land.
- **`INFRA-341`/`INFRA-343`'s existing `v2_evidence` line-range citations** will drift once
  `migration_002`, `LEVEL2_CACHE_COLUMNS`, and Step 3's edits to `migration_001`/the module constant
  are inserted/applied above/around the cited ranges — must be re-verified against the
  post-implementation file during this ticket's own Parity phase, per the same precedent the Level 1
  ticket's own plan already documented following.

## Test-Plan Updates (test_plan.md) — Architecture-Review-mandated

The following correction to `staging_artifacts/TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS/test_plan.md`
is required alongside this plan (Correction 1, item 5) and must be applied before Implement runs:

- **Regression Surface**: add `tests/tools/test_knowledge_gateway_redaction.py` (specifically
  `TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`,
  `:479-489`) as an explicitly-listed regression item — this test was outside the original regression
  surface entirely and Architecture Review found it depends directly on
  `retrieval_cache_schema_version`'s value, which Step 3 changes.
- **Scoped Pytest Commands**: add `.venv/bin/python3 -m pytest tests/tools/test_knowledge_gateway_redaction.py -v`
  as a fifth scoped command, alongside the existing four (`test_retrieval_cache.py`,
  `test_kgmcp_measurement_baseline.py`, `test_redaction_retention_policy_doc.py`,
  `test_context_packet_assembler.py`).

This correction should be applied to `test_plan.md` directly (by the same process revising this
plan) rather than left as a note here only — `test_plan.md`'s own Regression Surface and Scoped
Pytest Commands sections are the authoritative source Implement and Verify actually run against.

## Anti-Drift Notes

- **This plan's stance on the module constant has reversed from the pre-review version — read
  carefully.** The constant **is** bumped to `2` (Step 3), by explicit Architecture Review mandate.
  Do not revert to the old guard ("never bump it") — that guard belonged to the overturned original
  DD2 and no longer applies. What must NOT happen: bumping the constant **without** also making
  Step 3's paired edit to `migration_001`'s INSERT (hardcoding its own literal `1`). Bumping the
  constant alone, while `migration_001` still reads it live, is exactly the bug the original DD2
  correctly worried about (a `migration_001`-alone run would falsely stamp `2`) — the fix is doing
  *both* edits in Step 3 together, not skipping the `migration_001` edit.
- Do not skip Step 4 (the `tests/tools/test_knowledge_gateway_redaction.py:482` correction) after
  doing Step 3 — the constant bump makes that test's `== 1` assertion false; leaving it unedited
  after bumping the constant breaks a real, currently-passing test.
- Do not edit any assertion in `tests/tools/test_retrieval_cache.py`'s `TestMigrations` class
  (`test_retrieval_cache_schema_version_is_queryable_and_correct_after_migration`,
  `test_migration_is_idempotent_when_run_twice`) — both remain correct unmodified after Step 3,
  because `migration_001`'s hardcoded literal (`1`) equals its pre-correction stamped value
  (value-neutral refactor, see Step 3). Editing these tests "to be safe" or "to match the version
  bump" is not needed and would be a scope error — they test the generation-table row, not the
  constant.
- Do not drop `freshness`/`verification` from `LEVEL2_CACHE_COLUMNS` to "resolve" DD4's tension —
  the ticket's own Scope and AC2 require them. This is fully resolved (option (b), Step 6) — do not
  reopen it or treat it as still requiring a judgment call.
- Do not skip Step 6 (the `docs/guidelines/intentional_divergences.md` entry) — Architecture Review
  ruled it required, not optional; a plan that ships Steps 1-5 without Step 6 leaves DD4's ruling
  unrecorded, which fails this ticket's Definition-of-Done ("No important decision is undocumented").
- Do not implement any read/write logic (`check_*`/`write_*`-style functions) against the new table
  — schema only, per this ticket's own Out of Scope; guarded by Step 5 test 11.
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING` owns that work (and separately inherits the
  Step 6 verification obligation for `freshness`/`verification`, see Step 6).
- Do not implement dependency-invalidation logic beyond the raw `evidence_dependencies` column
  existing — no junction table "to help" the sibling dependency-invalidation ticket; DD1's
  single-JSON-column decision is deliberate and evidence-backed, guarded by Step 5 test 9.
  `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION` owns that work.
- Do not implement redaction/secret-scanning/size-cap enforcement for the new table's payload-shaped
  columns — schema only. The per-row-cap-vs-aggregation risk is explicitly not this ticket's job to
  resolve (see "Flagged, Not This Ticket's Job" above).
- Do not add `migration_002` to `_get_level1_connection()` or any other connect-time auto-apply path
  — no `migrate`/`rebuild` CLI subcommand exists or should be added; `migration_002` remains
  independently, explicitly invoked only, matching `migration_001`'s own established pattern.
- Do not name the new table anything resembling `retrieval_packet_cache_rows` — that name is
  permanently claimed by the existing, unrelated, BACKLOG-tier marker-only table this ticket must
  leave byte-for-byte unmodified.
- `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, and
  `tools/knowledge_gateway_mcp.py` are not read, opened, or imported by any step in this plan — do
  not add an import of any of them into `tools/retrieval_cache.py` "for convenience."

## Deviations (recorded during Implement)

Four items surfaced during Implement that this plan and `test_plan.md` did not anticipate. None
change this plan's Design Decisions (DD1-DD6) or its Steps 1-6 as specified; all four are narrow,
evidence-backed corrections to pre-existing test assertions whose literal content became false as
a direct, intended consequence of this ticket's approved design landing — the same class of
correction as Step 4's `test_knowledge_gateway_redaction.py:482` fix, just not enumerated by this
plan in advance.

1. **`tests/tools/test_retrieval_cache.py::TestMigration003::test_migration_002_name_never_reused_or_stubbed`**
   (pre-existing, added by `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` as an ordinal-2
   reservation guard) asserted `"migration_002" not in source` — literally false the moment Step 2
   lands, by construction (this ticket's entire purpose is to land `migration_002`). Neither
   `investigation.md` nor this plan catalogued this test. Renamed to
   `test_migration_002_landed_with_the_reserved_name_not_stubbed_or_renamed` and updated to assert
   the function exists under its exact reserved name exactly once — preserving the guard's real
   intent (catch a stub or a rename) rather than leaving it asserting a now-false claim.

2. **Step 5 tests 2 and 3, as literally worded in `test_plan.md`, conflict with this plan's own
   Step 2/DD2 design.** `test_plan.md`'s test 2 ("brand-new (never-migrated) connection... with no
   error") and test 3 ("run `migration_002_add_level2_tables` alone (no `migration_001`)") both
   call `migration_002` without `migration_001` having run first. Step 2's own "Note" paragraph
   (this plan, not test_plan.md) explicitly documents that this exact call pattern raises
   `sqlite3.OperationalError: no such table: retrieval_cache_generation` by design, and DD2's
   "Ordering assumption" paragraph states this plan's own tests exercise the chain
   `migration_001 -> migration_003 -> migration_002`. Resolved in favor of Step 2/DD2's explicit,
   reasoned design (the more authoritative, twice-reviewed artifact, and the one that directly
   anticipated and ruled on this exact scenario) over `test_plan.md`'s unrevised prose: both tests
   now run `migration_001` first (test 3 additionally omits `migration_003`, preserving the
   "legacy-only" vs. "Level-1-already-migrated" distinction AC3 requires between tests 3 and 4).
   AC3's three required starting-state scenarios are still each covered by a distinct test.

3. **`tests/tools/test_evidence_cache_identity_contract.py::test_no_shared_code_or_table_conflates_lookup_hit_with_validity_proof`**
   (pre-existing, from `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`) asserted `"freshness"` and
   `"verification"` are absent from `tools/retrieval_cache.py`'s entire source text — a blanket,
   file-wide proxy for the Non-collapse rule that predates this ticket's Architecture-Review-ruled
   DD4 exception. Not in this plan's or `test_plan.md`'s scoped file list. Narrowed (not weakened)
   to check the three `check_*_cache` lookup functions' own source specifically — the actual thing
   Bullet 2 (and this test's own section title, "real retrieval_cache.py lookup functions carry no
   validity/freshness verdict") protects — since DD4/Step 6's ratified, now-documented
   (`docs/guidelines/intentional_divergences.md` §2.44) exception permits the columns to exist on
   the new table's own schema, where no lookup function reads them.

4. **`tests/tools/test_kgmcp_phase2_baseline_recomparison.py::test_no_frozen_kgmcp_dependency_edited`**
   (pre-existing, from the sibling `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` ticket) still
   listed `tools/retrieval_cache.py` in its `git diff --stat HEAD` banned-edit-path tuple. Not in
   this plan's or `test_plan.md`'s scoped file list, and not the same file as
   `tests/tools/test_kgmcp_measurement_baseline.py` (confirmed already excluding
   `tools/retrieval_cache.py`, per investigation.md's Prior Work). This file's own existing code
   comment, directly above the banned-path tuple, already documents the identical precedent for
   `tools/knowledge_gateway_redaction.py` ("this check only ever validly reflected THIS ticket's
   own uncommitted diff at the moment it was authored — it was never meant as a permanent
   repo-wide ban"). Applied the same treatment to `tools/retrieval_cache.py`, with an equivalent
   documenting comment citing this ticket and its two prior legitimate editors.

None of these four required any change to `tools/retrieval_cache.py` itself beyond what Steps 1-3
already specify, and none weaken any check's real, substantive protection — each narrows or
updates a literal expected value/assertion to match a ratified, documented design decision this
plan (or Architecture Review) already made.
