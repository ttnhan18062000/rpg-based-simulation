---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING
artifact_type: investigation
tags: [ai, mcp, security]
---

# Investigation — TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING

## Current Behavior

### Context-scan tools run first (per CLAUDE.md), findings summarized
`mcp__knowledge-search__search_docs` (4 queries: "Level 2 context-packet cache lookup write wiring
knowledge_context", "Level 1 provider-result cache lookup write knowledge_gateway_cache
perform_cache_lookup perform_cache_write", "evaluate_write_candidate redaction secret-scan
MAX_PAYLOAD_BYTES packet payload", "compute_lookup_identity normalized_intent resolved_entity_ids
budget_class repo_branch_scope") returned the expected sibling-ticket investigation/plan artifacts
and the frozen contract docs (`evidence_cache_identity_contract.md`, `redaction_retention_policy.md`,
`knowledge-gateway-mcp-proposal.md` §10/§11/§17/§18) as top hits — no first query returned results at
all (genuinely new topic, expected since this is the wiring ticket). `graphify query
"knowledge_gateway_mcp _run_knowledge_context"` and `graphify query "revalidate_context_packet_row"`
(both BFS depth=2) confirmed the real, live symbol names/line numbers this ticket must call or
extend: `_run_knowledge_context()`/`_run_knowledge_status()` (`tools/knowledge_gateway_mcp.py`),
`compute_lookup_identity()`/`perform_cache_lookup()`/`perform_cache_write()`/
`revalidate_context_packet_row()`/`_level2_repo_branch_scope()` (`tools/knowledge_gateway_cache.py`).
Both tools were called before any grep/file read, per the Hard Rule.

### `tools/knowledge_gateway_cache.py` (336 lines, read in full) — the direct Level 1 precedent
Real Level 1 orchestration, in call order from `_run_knowledge_context()`:
1. `compute_lookup_identity(request, routing_decision, effective_budget)` (:137-154) — returns a
   dict of 7 keys: `normalized_intent`, `resolved_entity_ids_json`, `filters_json`, `budget_class`
   (bucketed via `compute_budget_class()`, :89-94, thresholds 500/2000), `routing_policy_version`,
   `repo_branch_scope` (a live `git branch --show-current` read via `_current_repo_branch_scope()`,
   :126-134), `query_hash`.
2. `perform_cache_lookup(request, routing_decision, effective_budget)` (:285-308) — computes
   identity, calls `rc.check_provider_result_cache()` (SELECT by PK `(query_hash,
   repo_branch_scope)`, then Python-side comparison of `normalized_intent`/`filters`/`budget_class`/
   `routing_policy_version` — any mismatch is `MISS`, not stale-rejected), then
   `is_branch_compatible()` (hard partition), then `revalidate_cache_row()` (§4 fallback rule +
   §5 rule 3 `changed_paths` intersection), bumps hit stats only on a genuine revalidated hit, and
   returns the stored `result_payload` JSON or `None`.
3. `perform_cache_write(request, routing_decision, response, effective_budget)` (:321-394) — never
   writes a `PARTIAL`-status response; acquires a per-key stampede guard
   (`rk.acquire_write_guard`); checks `rk.check_db_size_within_limit()`; derives `source_type` from
   `providers_consulted_this_call` (`"context_search" if "context_search" in providers_consulted
   else rk.SOURCE_TYPE_GRAPHIFY"` — already multi-provider-tolerant, defaults to context_search when
   both are present); serializes the **entire already-built `response` dict** (minus
   `cache`/`cache_key_version`) as `raw_payload`; calls `rk.evaluate_write_candidate(source_type=,
   raw_content=)`; on `REJECT`, returns without writing; on `ALLOW`, calls
   `rc.write_provider_result_cache(...)` with the redacted payload and identity/validity columns.

**Material finding on what Level 1 actually caches (not what the proposal's naming implies).**
Level 1's `perform_cache_write()` is called from `_run_knowledge_context()` **after**
`assemble_packet()` has already run (dedup + budget-truncation applied) — `raw_payload` is the fully
assembled, already-dedup'd, already-budget-truncated response dict, not a raw per-provider result.
In this repo's real implementation, Level 1 already functions, in substance, as a full
assembled-packet cache keyed by `(query_hash, repo_branch_scope)` with Python-side verification of
`normalized_intent`/`filters`/`budget_class` (bucketed)/`routing_policy_version`. The proposal's
Level 1-vs-Level-2 distinction (§10.2: Level 1 = "raw provider call results," Level 2 = "assembled
context-packet") does not hold structurally in the real code — both levels store the same kind of
payload (a fully assembled response). The genuine differences are: (a) identity granularity — Level
2's schema (`repository_id`/`branch`/`head_commit`/`working_tree_fingerprint` as 4 separate columns,
`provider_generations` as a per-provider dict, `entity_ids` distinct from Level 1's
`resolved_entity_ids`) is richer/more precise than Level 1's single collapsed `repo_branch_scope`
string and single `provider_generation_at_validation`; (b) revalidation mechanics — Level 2's
`revalidate_context_packet_row()` (below) does per-provider generation comparison, not a single
corpus-wide value; (c) — see Central Question 3 — whether budget identity is exact (`budget_tokens`)
or bucketed (`budget_class`). This is flagged in Risks: Level 2 is a **more precise cache layer
checked first**, not a structurally distinct cache of different content, and the ticket's own
Scope/AC framing ("Level 2 miss falls through to Level 1... on a further miss, live providers") is
architecturally sound under this reading, but Plan should state this explicitly rather than assume
the proposal's original "raw vs. assembled" framing still applies verbatim.

### `tools/knowledge_gateway_mcp.py::_run_knowledge_context()` (:149-331, read in full) — exact hook
points
Real call sequence: build+validate request → `_kgr.route(query)` (router failure fallback,
PARTIAL) → **Level 1 cache-check hook** (:227-232, try/except around
`_kgc.perform_cache_lookup(...)`, fail-open) → if hit, build `hit_response` from cached payload, set
`cache="HIT"`/`cache_key_version`, validate, **return early** (:234-239) → else
`_kgpa.assemble_packet(routing_decision, query, effective_budget)` (:241) → build `response` dict
field-by-field from `packet.*` (:243-317) → set `response["cache"] = "MISS"` (:323) →
**Level 1 cache-write hook** (:319-328, try/except around `_kgc.perform_cache_write(...)`,
fail-open) → validate, return.

**The Level 2 hook must be inserted in two places**: (1) a new Level 2 lookup, tried **before** the
existing Level 1 lookup at :227-232 (a Level 2 hit must skip both `perform_cache_lookup()` and
`assemble_packet()` per AC1's literal wording — "never reaches packet assembly or the Level 1 lookup
at all"), and (2) a new Level 2 write, alongside the existing Level 1 write at :319-328, on the full
miss path (after `assemble_packet()` succeeds) — **before** returning. The Level 1 hooks themselves
must not be modified (Out of Scope), only the call-site sequence around them. `routing_decision` is
already computed by this point (needed for Level 2 identity's `resolved_entity_ids`-equivalent
`entity_ids` column), so a Level 2 lookup can reuse the same `routing_decision` the Level 1 lookup
already uses — no second `route()` call needed.

`_run_knowledge_status()` (:350-414, read in full) — cache-domain fields are built at :390-411 from
`rc.provider_result_cache_stats()` (`{"total_rows", "total_hits"}`, read-only aggregation over
`retrieval_provider_result_cache_rows`), guarded by `if stats["total_rows"] > 0`. No equivalent
Level 2 stats function exists yet in `tools/retrieval_cache.py` — must be added.

### `tools/retrieval_cache.py` — Level 2 schema (read `migration_002_add_level2_tables`,
`LEVEL2_CACHE_COLUMNS`, and the Level 1 read/write functions in full)

`retrieval_context_packet_cache_rows` (28 columns, :326-357): **`packet_id TEXT NOT NULL PRIMARY
KEY`** — not `query_key_hash`. `query_key_hash` is an ordinary (non-unique, non-indexed) column.
This is structurally different from Level 1's composite-PK `(query_hash, repo_branch_scope)` lookup
shape: a real Level 2 lookup function cannot `SELECT ... WHERE packet_id = ?` (the caller does not
know `packet_id` in advance — it is presumably a generated identifier stamped at write time, not
derivable from the request). **A real Level 2 lookup must `SELECT * WHERE query_key_hash = ?` and
then verify the remaining identity fields (`entity_ids`, `filters`-equivalent — none exists as a
named column; see Risk 6 — `repository_id`, `branch`, budget) in Python against possibly multiple
returned rows**, since `query_key_hash` alone has no uniqueness constraint and a naive `fetchone()`
could silently pick the wrong row (e.g. two different branches, or two different budgets, sharing
the same `query_key_hash`). No `write_context_packet_cache()`/`check_context_packet_cache()`
function exists anywhere — this ticket must add both, in `tools/retrieval_cache.py`, mirroring
`write_provider_result_cache()`/`check_provider_result_cache()`'s shape exactly (per this ticket's
own Related Code Areas: `tools/retrieval_cache.py` is where "Level 2 schema/read/write functions
this ticket calls" live).

**Gap confirmed: `LEVEL2_CACHE_COLUMNS` has no `redaction_policy_version` column.** Level 1's table
gained this column via `migration_003_add_redaction_policy_version_column` (an `ALTER TABLE`, added
by the read-write-wiring precedent ticket itself, `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`).
`redaction_retention_policy.md` §6 states `redaction_policy_version` must be "stamped onto any
future payload-bearing cache row" — Level 2 rows are payload-bearing. Since
`evaluate_write_candidate()` always returns a `WriteDecision.redaction_policy_version` value
regardless of table, and this ticket's own Scope requires Level 2 writes to go through that same
enforcement, **this ticket must add an equivalent `migration_004_add_redaction_policy_version_
column_to_level2` (or similarly named) idempotent `ALTER TABLE`** to persist it — mirroring
`migration_003`'s exact pattern (`PRAGMA table_info` existence check, guarded, never touching
`_get_connection()`/`_init_schema()`). This is real, in-scope work per the ticket's own explicit
re-verification requirement ("if verification finds a genuine gap, closing that gap is in scope for
this ticket"), not something Investigate can silently skip or assume Plan will notice unprompted.

### Central Question 1 — module home for Level 2 orchestration: **`tools/knowledge_gateway_cache.py`,
extended in place**
Directly answered by the dependency-invalidation sibling's own investigation (read in full,
confirmed by independent re-read of the same source): `revalidate_context_packet_row()` and
`_level2_repo_branch_scope()` already live in `tools/knowledge_gateway_cache.py` (:227-278), placed
there specifically because they consume only a stored row dict (never a live `PacketAssembly`) and
because a real, currently-passing architecture guard
(`tests/tools/test_knowledge_gateway_cache.py::
test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`, an AST-based import-ban
on `tools.knowledge_gateway_router`/`tools.knowledge_gateway_packet_assembly`) structurally forbids
any module that needs `PacketAssembly`'s fields from living in this file. The new Level 2 lookup/
write orchestration this ticket adds (`perform_context_packet_cache_lookup()`/
`perform_context_packet_cache_write()`, or equivalently named) needs only: a stored row dict (for
lookup, exactly like `perform_cache_lookup()`), and — for write — the already-built `response` dict
plus `packet.evidence_dependencies`/`packet.providers_consulted_this_call` (already plain
lists/strings passed as function arguments from `_run_knowledge_context()`, not the live
`PacketAssembly` object itself). This satisfies the same "no live PacketAssembly import" constraint
Level 1's `perform_cache_write()` already satisfies (it also receives `response` as a plain dict, not
a `PacketAssembly`). **Conclusion: extend `tools/knowledge_gateway_cache.py` in place** — a new
sibling module would duplicate `compute_lookup_identity()`/`_current_repo_branch_scope()`/
`is_branch_compatible()` reuse machinery for no structural benefit, and the direct precedent
(`revalidate_context_packet_row()` already placed here by the immediately-preceding sibling ticket)
would become inconsistent with a second module appearing next to it. Confirmed no invasiveness
concern: `tools/knowledge_gateway_cache.py` already documents in its own module docstring (:18-23)
that "no live Level 2 lookup/write path is wired into the gateway yet (that remains
`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s job)" — i.e. the module's own docstring
already anticipates and assigns this exact extension to this exact ticket.

### Central Question 2 — does `evaluate_write_candidate()` work unmodified for packet-shaped
payloads? **Yes, the function itself needs no code change; a real gap exists elsewhere (see above).**
`evaluate_write_candidate()` (`tools/knowledge_gateway_redaction.py:270-304`, read in full) is a
generic pipeline over a `source_type` string (must be one of exactly 2 allowlisted literals,
`"context_search"`/`"graphify"`) and a `raw_content` string — `redact_content()`,
`scan_for_secrets()`, `check_size_cap()`, `check_never_cache_categories()` all operate on plain text,
with **zero dependency on the internal structure/shape of that text** (single-provider result vs.
multi-provider aggregated packet is invisible to this function; it never parses JSON internally, it
scans/redacts the raw string). Level 1's own `perform_cache_write()` already demonstrates this
function called against a payload that is itself a full, potentially multi-provider-aggregated
response dict (see Current Behavior finding above — Level 1 already serializes the entire assembled
`response`, not a single provider's raw result) — so the "packet aggregates multiple providers"
concern raised by the ticket's own Scope is **already exercised today, unmodified, by Level 1's real
write path**, not a new stress case Level 2 introduces. `source_type` selection for a Level 2 write
can reuse the identical `"context_search" if "context_search" in providers_consulted else
rk.SOURCE_TYPE_GRAPHIFY"` logic Level 1 already uses (:352-356) — no new source-type literal is
needed or justified (Out of Scope also forbids inventing new content categories beyond the ticket's
own scope). **The one genuine gap requiring a real code change is the missing
`redaction_policy_version` persistence column** on the Level 2 table (see above) — not
`evaluate_write_candidate()` itself, which is correctly reusable as-is.

### Central Question 3 — should `budget_tokens` be part of the Level 2 lookup-identity key?
**Real, unresolved tension between the frozen contract and the actual truncation behavior — flagged
for Plan/Architecture Review, not silently resolved here.**

`evidence_cache_identity_contract.md` §1 states explicitly: `budget_class` is "the caller's budget
tier (token/latency budget bucket), **not the raw numeric budget**." Taken literally, this instructs
against using raw `budget_tokens` in the lookup-identity key at all, at either level.

However, the dedup/budget-enforcement sibling's own investigation (read in full) resolves that
`assemble_within_budget()`'s truncation is driven by the literal `effective_budget` integer, not by
`budget_class`'s coarse small/medium/large bucket (thresholds 500/2000 tokens). Two requests for the
same query with different `budget_tokens` values that happen to fall in the **same** bucket (e.g.
600 and 1800, both `"medium"`) can produce **differently-truncated packets** (different
`included_statements`, different `answer`, different `budget_returned`,
`budget_truncated`/`omitted_statement_count`). If Level 2's lookup identity uses only `budget_class`
(mirroring Level 1 verbatim), a Level 2 hit could silently serve a packet truncated for one caller's
actual budget to a different caller who requested a materially different budget in the same bucket —
a genuine correctness defect specific to Level 2 (Level 1 does not have this defect in the same way,
because Level 1's payload IS also budget-truncated — this defect already latently exists at Level 1
too, but is out of this ticket's scope to fix there per Out of Scope's "Level 1's own already-tested
logic is reused as-is, not modified"). This is a real, concrete, ticket-relevant tension between
§1's literal instruction and Level 2's own correctness requirement (AC1 requires the second identical
call to be a "genuine" hit; nothing in AC1 defines "identical" to include budget, but a materially
different, wrongly-truncated packet served silently would violate the spirit of "genuine hit").

**Recommendation, not a silent decision:** Level 2's lookup identity should extend
`compute_lookup_identity()`'s 6 fields with one additional exact field — the literal
`budget_tokens`/`effective_budget` integer, not merely `budget_class` — recorded as an intentional,
documented divergence from §1's literal "not the raw numeric budget" sentence in
`docs/guidelines/intentional_divergences.md` (rationale class: **Bounded** or **Hardened** — §1 was
written before Level 2's budget-truncating packet-cache existed and did not anticipate a caching
layer whose payload itself varies continuously with the exact budget value, not just its bucket).
This must be an explicit Plan-phase/Architecture-Review decision (mirroring how the schema ticket's
own Non-collapse-rule-vs-§10.3 tension was explicitly flagged and resolved via a divergence entry,
§2.44), not something Investigate silently picks.

## Mechanics / Engine Constraints

Agent-orchestration/retrieval tooling, not simulation logic — no Mechanics Bible chapter or core
engine contract (`kernel.md`/`authoritative_pipeline.md`) governs this module, consistent with every
existing `docs/parity_ledger/infrastructure.yaml` KGMCP-subsystem entry's `support_boundary` field.
The governing "laws" are this subsystem's own frozen contracts:
- `evidence_cache_identity_contract.md` §1 (lookup identity — binding on this ticket's Level 2
  identity extension; see Central Question 3's flagged tension), §3 (Non-collapse rule — binding on
  the shape of the new Level 2 lookup function: must return a bare status/row, never a raw
  `freshness`/`verification` verdict without a separate validity step — this ticket **inherits an
  explicit, named obligation** from `docs/guidelines/intentional_divergences.md` §2.44's own
  "Verification" clause, quoted: "`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`... must add
  a test asserting that whatever lookup function it introduces for
  `retrieval_context_packet_cache_rows` never returns the raw `freshness`/`verification` column
  values off a row without a separate, explicit revalidation step first"), §4 (provider-generation
  fallback — already implemented at Level 2 by `revalidate_context_packet_row()`, reused unmodified),
  §5 (repo/branch/working-tree scope — already implemented at Level 2, reused unmodified).
- `redaction_retention_policy.md` §2 (allowlist — reused unmodified), §3 (redaction — reused
  unmodified), §4 (secret-scan — reused unmodified), §5 (64 KiB payload size cap — **must be
  independently re-verified against real Level 2 packet sizes**, not assumed; see Risks), §6
  (`redaction_policy_version` stamping — **real gap**, no persistence column exists yet at Level 2;
  see Current Behavior), §11 (Ratification Status — confirms this policy applies subsystem-wide, not
  Level-1-scoped).
- `cache_migration_plan.md` §2 (already implemented by the schema ticket; this ticket's own new
  migration, if any, for the `redaction_policy_version` column must follow the same idempotent
  `CREATE TABLE IF NOT EXISTS`/`ALTER TABLE` pattern and must not touch the already-shipped
  `migration_002`).

## Docs Requiring Update

- `docs/plans/knowledge-gateway-mcp-proposal.md`: §20 Phase 3's second bullet, "Store and return
  actual packet payloads," is currently unmarked and, unlike its 3 sibling bullets (confirmed by
  direct grep — "Assemble deduplicated multi-provider packets" and "Enforce caller budgets using
  measured output size" were deliberately left unmarked by the dedup/budget sibling ticket because
  that ticket *hardened*, not *originated*, Phase-1-existing capability), this bullet's core
  capability — a live Level 2 lookup/write path that actually stores and returns cached packet
  payloads — genuinely does not exist anywhere before this ticket. This ticket should mark it
  **Done**, citing this ticket ID.
- `docs/parity_ledger/infrastructure.yaml`: new entry required, next real ID after the confirmed live
  max (`INFRA-348`, the dependency-invalidation sibling's own entry, confirmed by direct grep) —
  **`INFRA-349`** — describing the new Level 2 lookup/write functions
  (`tools/retrieval_cache.py::check_context_packet_cache()`/`write_context_packet_cache()`, or
  equivalently named), their orchestration in `tools/knowledge_gateway_cache.py`, the
  `_run_knowledge_context()` hook-point insertion, and (if this ticket closes the gap) the new
  `redaction_policy_version` migration. Status should be `verified`, priority `P1` (consistent with
  every other KGMCP-subsystem entry — none is P0), with a real `test_path`.
- `docs/guidelines/intentional_divergences.md`: §2.44's own "Verification" clause names this ticket
  explicitly and requires a new test (see Mechanics/Engine Constraints above) — this ticket should
  either add a note confirming that obligation was discharged (update §2.44's Status/Verification
  text) or, if Central Question 3's budget-identity tension is resolved by extending the lookup
  identity beyond `budget_class`, add a **new** divergence entry (next available numbering) for that
  decision, per §1's own "not the raw numeric budget" sentence being knowingly overridden.

Two frozen contract docs (`docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`,
`docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`) were originally
considered and provisionally flagged **not required** here at Investigate time — both are
design-only from earlier DONE tickets, and this ticket's own work (a real Level 2 migration for
`redaction_policy_version`, and the budget-identity extension) was assumed resolvable entirely via
`intentional_divergences.md` entries instead of edits to either doc, consistent with every sibling
ticket's own Anti-Drift Hazards on these two files (see Anti-Drift Hazards below).

**Correction, made during Document-Update (this investigation's own "not required" call for
`cache_migration_plan.md` was wrong, not merely superseded):** direct re-read of
`cache_migration_plan.md` §2 during Document-Update found it is **not**, in practice, actually
frozen against annotation edits — two prior sibling tickets
(`TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS`'s own Document-Update phase,
`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` before it) already edited this exact file to
annotate a migration's ordinal as "now real, implemented code" once its body landed — a real,
precedented, repeatable pattern this investigation failed to check for before writing the "frozen,
never edited" characterization above. Applying that same precedent, `cache_migration_plan.md` §2
had two genuine, concrete staleness gaps this ticket's own landing created: (1) migration 2's own
annotation stated "No read/write logic against this table exists yet — that remains separate, later
work (`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`)" — false as of this ticket's own
landing; (2) `migration_004_add_level2_write_path_columns` (added by this ticket, Step 1) had no
entry anywhere in §2's ordered migration list. Both gaps were closed in Document-Update: see the
ticket's own Files Changed for the exact diff. `evidence_cache_identity_contract.md`, by contrast,
was independently re-checked and confirmed genuinely not required — see "Docs Considered But Not
Required" below for the specific reasoning, which is a different, still-valid finding from the one
corrected here.

**Additional doc touched during Document-Update, beyond this section's original list:**
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §6 — not flagged above
at Investigate time (this investigation's original analysis treated §2–§5 as "reused unmodified"
and only flagged §6's `redaction_policy_version` *persistence* as a real gap for
`tools/retrieval_cache.py` itself, not for this doc's own prose). Document-Update found §6's own
established narrative pattern (each landing ticket that extends `redaction_policy_version`'s
persistence gets a short "resolved/extended by TCK-XXX" paragraph, e.g. the existing
`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` paragraph already there) applies directly to this
ticket's own `migration_004` extension of the same column onto the Level 2 table, and to this
ticket's own AC4 independent re-verification finding (Level 2 writes route through
`evaluate_write_candidate()` unmodified, via a new architecture-guard test). A short paragraph was
appended following that exact precedent shape — see Files Changed.

## Docs Considered But Not Required (resolved during Document-Update, not left open)

- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` — genuinely
  re-checked, not assumed, during Document-Update. §2.44 (the immediately preceding sibling
  ticket's own divergence entry, which quotes this contract's §3 Non-collapse rule at length) added
  **no** cross-reference footnote or pointer to `intentional_divergences.md` anywhere in this
  document — confirmed by direct full-text re-read: zero occurrences of `intentional_divergences`,
  `§2.44`, or any ticket ID anywhere in the file. Since §2.44 is the direct, most-recent precedent
  for exactly this situation (a divergence from one of this contract's own rules, `budget_class`
  vs. `budget_tokens` under §1 here, is analogous to §2.44's own divergence from §3) and it set no
  such footnote precedent, adding one now for §2.45 would be a new, unprecedented convention this
  ticket has no mandate to introduce unilaterally. This document's own frozen §1/§3/§4/§5 rule text
  is correctly left untouched — the divergence itself lives entirely in
  `intentional_divergences.md` §2.45 (see Docs Requiring Update above), consistent with this
  document's own "Phase 0 contract for a future implementation" framing and every sibling ticket's
  Anti-Drift Hazards on this file.

## Parity Ledger Overlap

- `INFRA-346` (schema ticket) — not modified; this ticket's new migration (if the
  `redaction_policy_version` gap is closed) is additive to the same table, following the same
  precedent `migration_003` set relative to `migration_001`.
- `INFRA-347` (dedup/budget ticket) — not modified; `PacketAssembly.budget_truncated`/
  `omitted_statement_count` are read (not written) by this ticket's Level 2 write path (they are
  already fields on the `response` dict `_run_knowledge_context()` builds, exactly like Level 1's
  write path already consumes them).
- `INFRA-348` (dependency-invalidation ticket) — **directly discharged by this ticket.** Its own
  `support_boundary` field states explicitly: "No Level 2 `check_context_packet_cache()`/
  `write_context_packet_cache()` pair exists anywhere in the repo, so there is no live cache row for
  `revalidate_context_packet_row()` to ever be invoked against until
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING` lands and performs that wiring." This ticket
  is the one that makes `revalidate_context_packet_row()`/`_level2_repo_branch_scope()` reachable
  from a live call path for the first time — `INFRA-348`'s own text should be re-verified (not
  edited) for continued accuracy once this ticket lands, since its "not yet reachable" framing
  becomes stale (not incorrect, but describing a pre-this-ticket state) the moment this ticket wires
  the lookup in.
- `INFRA-341`/`INFRA-343` (Level 1 schema/redaction) — unmodified, cited only for precedent.
- No P0 entries exist anywhere in this KGMCP subsystem (confirmed: every cited entry is P1) — the new
  `INFRA-349` entry should also be P1, consistent with the established subsystem pattern; no P0
  `test_path` gate risk.
- `docs/guidelines/intentional_divergences.md` §2.44 — see Docs Requiring Update; this ticket
  inherits a named, explicit obligation from this entry, not merely context.

## Prior Work

- `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` (DONE) — the direct structural precedent for this
  entire ticket. Its stored `investigation.md`/`plan.md`/`test_plan.md` were not re-read in full here
  (this investigation reads the real, current *code* it produced instead, per CLAUDE.md's "verify,
  don't assume" rule) — `tools/knowledge_gateway_cache.py` and `tools/knowledge_gateway_mcp.py`'s own
  current source is the authoritative record of what that ticket actually shipped, confirmed above.
- `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` (DONE) — supplies `LEVEL2_CACHE_COLUMNS`/
  `migration_002_add_level2_tables`; its stored investigation.md was read in full for the exact
  per-column provenance and the 3 flagged risks (version-bump coupling, Non-collapse tension,
  `schema_version` naming collision — all already resolved in the shipped code, reconfirmed by direct
  read of `tools/retrieval_cache.py`).
- `TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT` (DONE) — supplies the real
  `budget_truncated`/`omitted_statement_count` fields and the budget-tolerance resolution this
  investigation's Central Question 3 directly builds on; its stored investigation.md was read in full.
- `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION` (DONE) — supplies
  `PacketAssembly.evidence_dependencies`/`revalidate_context_packet_row()`/
  `_level2_repo_branch_scope()`; its stored investigation.md was read in full and is the single
  richest source for this ticket's own module-placement and revalidation-reuse decisions (Central
  Question 1 above is a direct, independently-reconfirmed extension of its own findings).
- `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION` (DONE) — the real `MAX_PAYLOAD_BYTES =
  65536` value and its measured-range provenance (10,612–30,548 bytes, single-provider-scoped
  responses) this ticket's own write-path re-verification must check against Level 2 packet sizes.

## Risks and Open Questions

1. **Central Question 3's budget-identity tension (see above) is a genuine open architectural
   decision, not resolved here.** Blocks Plan from silently reusing `compute_lookup_identity()`
   verbatim for Level 2 — an explicit extension decision is required, with a divergence-note
   citation if raw `budget_tokens` is added to the key.
2. **`redaction_policy_version` has no persistence column on the Level 2 table (see Current
   Behavior) — a real, concrete gap this ticket's own Scope requires closing, not merely noting.**
   Plan must decide the exact migration ordinal/name (next open ordinal after `migration_003` is
   `migration_004`, confirmed by direct read — no `migration_004_*` function exists anywhere in
   `tools/retrieval_cache.py` today) and follow `migration_003`'s idempotent `ALTER TABLE` pattern
   exactly.
3. **Level 2's lookup shape is not a simple PK lookup (see Current Behavior) — `query_key_hash` is
   an unindexed, non-unique ordinary column, not the primary key (`packet_id` is).** A real Level 2
   `check_context_packet_cache()` must `SELECT ... WHERE query_key_hash = ?` and disambiguate among
   possibly-multiple returned rows in Python (by `entity_ids`/`repository_id`/`branch`/budget), never
   assume a single-row result the way Level 1's composite-PK lookup safely can. Flagged so Plan does
   not silently write a `fetchone()`-based lookup that could return the wrong row when multiple
   Level 2 packets share a `query_key_hash` (e.g. same query, different branches).
4. **65536-byte size cap was derived from real single-provider-scoped Level 1 payloads
   (10,612–30,548 bytes) — no real measurement exists yet for genuinely multi-provider Level 2
   packets.** However, Level 1's own `response` payload (per the Current Behavior finding above) is
   already the fully assembled, potentially-multi-provider packet — meaning the 65536-byte
   measurement basis may already implicitly cover multi-provider aggregation today (since Level 1's
   `raw_payload` and a Level 2 `raw_payload` would, for the same query, be near-identical in content
   and size). This should be explicitly re-verified with a real test against the actual measured
   corpus (mirroring `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION`'s own methodology), not
   assumed identical without measurement — the ticket's own Scope explicitly requires this
   verification, not an inference from this investigation.
5. **No `entity_ids`-equivalent to Level 1's `filters_json` exists as a named Level 2 identity
   field for verification beyond `entity_ids`/`repository_id`/`branch`.** `LEVEL2_CACHE_COLUMNS` has
   no `filters`-equivalent column at all (confirmed: absent from the 28-column set). If the caller's
   `mode`/`include_history`/`evidence_detail` filters genuinely need to distinguish Level 2 packets
   (as they do at Level 1, per `compute_lookup_identity()`'s `filters` dict), a real gap exists: two
   requests differing only in `mode` could incorrectly collide on the same Level 2 row. Flagged for
   Plan — either (a) confirm no observable Level 2 collision risk exists today (since `assemble_
   packet()` does not itself branch on `mode`/`include_history`/`evidence_detail` — verify this
   directly against `assemble_packet()`'s real signature, which takes only `routing_decision,
   query_text, budget_requested`, no `mode`/filters argument — so the packet's actual content is
   filter-independent, meaning the gap may be benign, not a genuine correctness defect), or (b) add
   the missing identity coverage. This is a genuine open question, not silently assumed benign here.
6. **Double-write question**: does the existing Level 1 write hook still fire, unchanged, on a full
   Level 2+Level 1 miss (in addition to the new Level 2 write)? The ticket's Out of Scope text
   ("Level 1's own already-tested logic is reused as-is, not modified, except for the minimal
   call-site change needed to fall through from a Level 2 miss") implies yes — both writes happen on
   a genuine full miss. This should be an explicit Plan-phase statement (with a test proving both
   rows get written on one full-miss call), not an implicit assumption.

## Anti-Drift Hazards

- **Do not modify `revalidate_context_packet_row()`, `_level2_repo_branch_scope()`,
  `compute_lookup_identity()`'s existing 6-field shape, `perform_cache_lookup()`, or
  `perform_cache_write()`** — all are real, tested, already-shipped functions. Any Level 2 identity
  extension (Central Question 3) must be a **new**, additively-named function
  (`compute_context_packet_lookup_identity()` or similar), never a signature change to the existing
  Level 1 function.
- **Do not modify `tools/knowledge_gateway_router.py`** — explicit AC ("remains byte-unchanged").
- **Do not modify `tools/knowledge_gateway_packet_assembly.py`** — not listed in Related Code Areas;
  this ticket reads `PacketAssembly` fields already threaded through as plain arguments/dict values,
  never imports the module (preserves
  `test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`).
- **Do not let the new Level 2 lookup function return a raw `freshness`/`verification` value from a
  row without a separate revalidation step** — inherited obligation from
  `intentional_divergences.md` §2.44, and the same Non-collapse-rule discipline
  `revalidate_context_packet_row()` and `revalidate_cache_row()` already both honor (bare bool/status
  return only).
- **Do not silently pick a resolution to Central Question 3 (budget identity)** — must be an explicit
  Plan/Architecture-Review decision with a divergence-note citation if raw `budget_tokens` is used.
- **Do not silently skip the `redaction_policy_version` persistence gap** — real, in-scope work per
  the ticket's own explicit re-verification requirement, not an optional nice-to-have.
- **Do not write a Level 2 lookup as a bare `fetchone()` on `query_key_hash` alone** — `packet_id` is
  the real PK; `query_key_hash` is unindexed/non-unique; a naive single-row fetch risks silently
  returning the wrong row.
- **Do not edit `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` or
  `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`** — both frozen,
  design-only, from earlier DONE tickets. Any new migration or budget-identity extension this ticket
  adds is recorded via `docs/guidelines/intentional_divergences.md` instead, mirroring every prior
  sibling ticket's own Anti-Drift Hazards on these two files.
- **Do not invent a new `source_type` literal for Level 2 writes** — reuse the same 2-literal
  allowlist (`context_search`/`graphify`) and the same provider-selection logic Level 1's
  `perform_cache_write()` already uses; `evaluate_write_candidate()`'s allowlist is frozen at exactly
  2 entries (Out of Scope: no new eligible source type).
- **Do not add a new `knowledge_status_response.schema.json` field name without an explicit Plan
  decision** — the schema has `additionalProperties` unrestricted at the top level for the request
  side but real, closed `properties` definitions; the dedup/budget sibling's own precedent shows
  additive schema edits are legitimate when a ticket's real scope requires a new field (it added
  `budget_truncated`/`omitted_statement_count`), but the exact field names for "Level 2 entry
  counts"/"Level 2 hit/miss rates"/"Level 2 vs. Level 1 hit attribution" are undecided — `cache_
  entry_counts` is already a generic `{kind, freshness, count}` array (a new `kind: "context_packet"`
  item fits without a schema change), but no per-level hit/miss-rate breakdown field exists at all
  today (`cache_hit_rate`/`cache_miss_rate`/`cache_stale_rejection_rate` are single top-level
  scalars) — new fields are required for that half of the AC, and Plan must name them explicitly.
