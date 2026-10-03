---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION

## Current Behavior

### Context-scan tools run first (per CLAUDE.md), findings summarized
`mcp__knowledge-search__search_docs` (2 queries: "packet dependency invalidation changed_paths
evidence_dependencies Level 2 cache", "evidence_cache_identity_contract branch working-tree
changed_paths intersection revalidation") returned mostly low-relevance hits for the first query
(no real doc chunk on packet-level dependency invalidation exists yet — expected, since this is the
first ticket to build it) and, for the second, correctly surfaced
`evidence_cache_identity_contract.md#5-repositorybranchworking-tree-cache-sco-005` and
`knowledge-gateway-mcp-proposal#123-branch-and-working-tree-awareness-015` as the top real hits —
consistent with the ticket's own Related Docs citations, no new undiscovered doc surfaced.
`graphify query "knowledge_gateway_cache revalidation changed_paths evidence_dependencies packet"`
(BFS depth=2, 89 nodes) confirmed the real, live symbol names this ticket must reuse or extend:
`revalidate_cache_row()`, `is_branch_compatible()`, `working_tree_overlap_forces_revalidation()`,
`select_validation_basis()`, `compute_lookup_identity()` (all `tools/knowledge_gateway_cache.py`),
and `migration_002_add_level2_tables()`/`LEVEL2_CACHE_COLUMNS` (`tools/retrieval_cache.py`). Both
tools were called before any grep/file read, per the Hard Rule.

### `tools/knowledge_gateway_cache.py` — read in full (336 lines, Level 1 orchestration)

This is the real, live Level 1 precedent the ticket asks this investigation to evaluate for reuse.
Four functions matter for §5:

- `working_tree_overlap_forces_revalidation(evidence_paths_json: str, changed_paths: list[str]) ->
  bool` (:196-201) — **fully generic**. It takes a raw JSON-encoded array of paths and a
  `changed_paths` list and returns `bool(set(json.loads(evidence_paths_json)) &
  set(changed_paths))`. It has zero dependency on any table/row shape, column name, or "Level"
  concept — it is pure set-intersection over two plain collections. **This function is directly
  callable, unmodified, against a Level 2 row's `evidence_dependencies` JSON column** — no wrapper
  needed, because the JSON-array-of-paths shape is identical between Level 1's
  `working_tree_overlap` column (populated by `perform_cache_write()` from `source_paths = sorted({c["path"]
  for c in context_entries if c.get("path")})`) and Level 2's `evidence_dependencies` column (per
  the schema ticket's own decision — see "Prior Work" below — the identical JSON-array-of-strings
  convention).
- `is_branch_compatible(row_repo_branch_scope: str, current_repo_branch_scope: str) -> bool`
  (:191-193) — **fully generic**, a bare string equality (`row_repo_branch_scope ==
  current_repo_branch_scope`). Also directly reusable, but Level 2's schema does not store a single
  combined `repo_branch_scope` string — it splits `repository_id` and `branch` into two separate
  columns (§10.3/`LEVEL2_CACHE_COLUMNS`). Direct reuse requires the caller to first construct the
  combined string exactly as `_current_repo_branch_scope()` (:121-129) does
  (`f"{repo_root}::{branch}"`) from the two Level 2 columns before calling — a one-line adapter at
  the call site, not a rewrite of the comparison logic itself.
- `select_validation_basis(capability_descriptor)` / `_capability_descriptor_for(providers_selected)`
  (:157-178) — the §4 PROVIDER_GENERATION-fallback-vs-finer-fingerprint rule, generic over "a list of
  provider IDs," already conservative-merges across multiple providers
  (`all(d.get("fine_grained_fingerprints") for d in descriptors)`). This is **already
  multi-provider-aware** — it was written to handle a `routing_decision.providers_selected` list, not
  a single provider, so it needs no Level-2-specific change at all.
- `revalidate_cache_row(row: dict, *, capability_descriptor, current_provider_generation,
  current_evidence_fingerprint, changed_paths) -> bool` (:204-219) — **NOT generic**. It is the
  top-level orchestrator and it hardcodes three specific Level 1 column names directly off the `row`
  dict: `row["working_tree_overlap"]`, `row["evidence_fingerprints"]`, and
  `row["provider_generation_at_validation"]`. Two of these three columns **do not exist at all** in
  `LEVEL2_CACHE_COLUMNS` (confirmed by direct read of `tools/retrieval_cache.py:154-185`) — Level 2
  has no `evidence_fingerprints` column and no `provider_generation_at_validation` column; it has
  `evidence_dependencies` (paths only, no fingerprint) and `provider_generations` (a **dict**,
  `{provider_id: generation}`, not a single string). `revalidate_cache_row()` cannot be called
  as-is against a Level 2 row — it would `KeyError` on `row["evidence_fingerprints"]` and
  `row["provider_generation_at_validation"]` immediately.

**Direct answer to Investigate Question 1**: Level 1's revalidation logic splits into two tiers, not
one. The two low-level primitives (`working_tree_overlap_forces_revalidation`,
`is_branch_compatible`) are already written generically over "a JSON string of dependency paths" /
"two branch-scope strings" and are directly reusable by call, unmodified. The one orchestrator
(`revalidate_cache_row`) is hardcoded to Level 1's specific column names and cannot be reused as-is
— it needs a packet-specific sibling function, not a parameter tweak, because the underlying data
shape genuinely differs (see next section).

### `tools/retrieval_cache.py` — `LEVEL2_CACHE_COLUMNS` / `migration_002_add_level2_tables()` (read
in full, confirming the exact frozen Level 2 row shape this ticket populates/invalidates against)

`LEVEL2_CACHE_COLUMNS` (:154-185, 28 columns) confirms the real column set. For §5 purposes, the
relevant columns are: `evidence_dependencies` (`TEXT NOT NULL`, JSON array — the column this
ticket's own aggregation must populate), `repository_id` (`TEXT NOT NULL`), `branch` (`TEXT NOT
NULL`), `head_commit` (`TEXT`, nullable), `working_tree_fingerprint` (`TEXT`, nullable — a column
name that exists but is NOT the same mechanism as §5 rule 3's `changed_paths`-intersection; nothing
in `cache_migration_plan.md`/`evidence_cache_identity_contract.md`/the schema ticket's own artifacts
defines what populates this column, and no code anywhere computes a value for it — flagged in Risks
below, not silently assumed to be redundant with `evidence_dependencies`), and `provider_generations`
(`TEXT NOT NULL`, JSON — but shaped as a **dict** `{provider_id: generation}` per §10.3's
`provider_generations{}` notation, confirmed against the proposal's own literal schema block at
`docs/plans/knowledge-gateway-mcp-proposal.md:581`, not a single string like Level 1's
`provider_generation_at_validation`). No `evidence_fingerprints`-equivalent column exists at Level 2
at all.

**Direct answer to Investigate Question 4**: the schema ticket's own investigation.md (read in full,
§"Resolution of the 3 Assumptions/Open-Questions", Open Question 2, lines 164-183) explicitly
decided the representation this ticket must follow: **a single JSON-text column
(`evidence_dependencies TEXT NOT NULL`), holding a JSON array of dependency-path strings — no
junction table.** Its own Anti-Drift Hazards (lines 342-346) explicitly forbid this ticket from
introducing a junction table "to help." This is binding, not optional — this ticket follows it
verbatim, does not re-decide it.

### `tools/knowledge_gateway_packet_assembly.py` — read in full (745 lines)

`PacketAssembly` (:616-633) currently has **no `evidence_dependencies` field at all** — confirmed by
direct read of the dataclass definition (fields: `status`, `freshness`, `verification`,
`provenance_providers`, `providers_consulted_this_call`, `answer`, `statements`, `context`,
`evidence`, `conflicts`, `budget_requested`, `budget_returned`, `budget_truncated`,
`omitted_statement_count`, `provider_failures`, `negative_claim_support`). The just-DONE dedup/budget
sibling ticket added `budget_truncated`/`omitted_statement_count` and `Statement.evidence_hash` (both
present and confirmed in the live file) but did **not** add any evidence-dependency aggregation field
— its own investigation.md (read in full) never mentions `evidence_dependencies` once, confirming it
is a genuinely new, unbuilt piece this ticket must add, not something the sibling already exposed.

The raw material to build the aggregation already exists on the dataclass, however: `EvidenceEntry`
(:226-232) carries a `path: Optional[str]` field per entry, populated for every `context_search`
result (`source_path`, always a real repo-relative path — :281-284/:288-293) and `None` for every
`graphify` result (:314-320/:324-330, since `match_symbol_name()`'s raw stdout carries no path,
only the query text used to build a `symbol:<query_text>` evidence ID). `PacketAssembly.evidence`
(`final_evidence`, :706-707) is already filtered down to exactly the evidence entries backing the
statements that survived dedup + budget truncation — i.e. `final_evidence` already IS the
"aggregated from the dependencies of every provider result the packet assembled" set the ticket's
own Scope asks for; nothing upstream of it needs to change.

**Direct answer to Investigate Question 3, part A (where aggregation should live).**
`{e.path for e in final_evidence if e.path}` — a one-line, deterministic aggregation over data
`assemble_packet()` already computes at every call — is structurally identical to how Level 1's
`perform_cache_write()` already derives `source_paths` today (`tools/knowledge_gateway_cache.py:312`:
`source_paths = sorted({c["path"] for c in context_entries if c.get("path")})`). This is real,
already-established precedent for computing exactly this kind of set from already-assembled
provider-result data. The natural home for the *aggregation* is therefore
`tools/knowledge_gateway_packet_assembly.py::assemble_packet()` itself — either as a new
`PacketAssembly.evidence_dependencies: list[str]` field computed alongside `final_evidence`
(mirroring exactly how the sibling ticket added `budget_truncated`/`omitted_statement_count` as new
computed fields on the same dataclass, in the same orchestrator function), or as a small dedicated
helper function in the same module that `assemble_packet()` calls. This is **not** a hypothetical
choice — it is structurally forced by a real architecture guard, confirmed next.

**Direct answer to Investigate Question 3, part B (where the guard is enforced) — the load-bearing
finding of this investigation.** `tests/tools/test_knowledge_gateway_cache.py::
test_module_does_not_import_knowledge_gateway_router_or_packet_assembly` (:243-259) is a real,
currently-passing, AST-based architecture guard that asserts
`tools/knowledge_gateway_cache.py` contains **no** `import`/`from ... import` statement naming
`tools.knowledge_gateway_router` or `tools.knowledge_gateway_packet_assembly`, in any form. This
means **any aggregation logic that needs to read `PacketAssembly`'s fields (statements/context/
evidence) structurally cannot live inside `tools/knowledge_gateway_cache.py`** without breaking this
existing, tested guard — confirming the aggregation must live in
`tools/knowledge_gateway_packet_assembly.py` (the module that owns `PacketAssembly` construction),
never in the cache-orchestration module. This directly and concretely answers Question 3's "where do
AGGREGATION and INVALIDATION each belong" framing: they belong in **two different modules**, not
one, for a real structural reason (an existing import-direction guard), not a stylistic preference.

**Direct answer to Investigate Question 3, part C (where invalidation/revalidation should live).**
The packet-level revalidation function (the Level 2 sibling to `revalidate_cache_row()`) does **not**
need to read a live `PacketAssembly` at all — by design, it revalidates a previously-**stored** Level
2 row (a plain dict of column values, exactly the same shape `revalidate_cache_row()` already
consumes for Level 1) against the current `changed_paths`/branch scope/corpus generation. It has no
structural need to import `knowledge_gateway_packet_assembly.py`, so it can live in
`tools/knowledge_gateway_cache.py` alongside `revalidate_cache_row()` as a new sibling function
(e.g. `revalidate_context_packet_row()`), reusing `working_tree_overlap_forces_revalidation()` and
`is_branch_compatible()` by direct in-module call — consistent with `evidence_cache_identity_
contract.md` §1's own explicit instruction (quoted in this module's own docstring, :40-45) that "a
future implementation should reuse the same normalize-then-hash shape, not invent a second one,"
applied here by direct analogy to the two already-generic §5 primitives.

**This ticket's own Out of Scope explicitly forbids implementing `_run_knowledge_context()` wiring
and forbids adding `check_*_cache`/`write_*_cache`-style read/write functions against the new table
(the schema ticket's own Anti-Drift Hazards assign that explicitly to
`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`)** — so this ticket's own new functions must
be pure, independently-testable logic (a computation and a boolean revalidation decision), never
wired to a live `check_context_packet_cache()`/`write_context_packet_cache()` pair, because those
functions do not exist yet and are explicitly out of this ticket's scope to create.

### `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §5 — read in
full

Three rules, verbatim (lines 149-171): (1) a new commit alone is not automatically a cache miss —
compatibility depends on evidence-fingerprint stability, not raw commit SHA; (2) branch identity is
a hard partition, checked before any fingerprint comparison, never a soft signal; (3) working-tree
fingerprinting uses `changed_paths` intersection against a cached row's dependency paths, never
whole-tree hashing. All three rules are level-agnostic in their own text — nothing in §5 restricts
itself to "Level 1 rows"; it describes "a packet cached against the same repository identity" in
rule 1's own wording, i.e. it was already written with packet-level (not just provider-result-level)
scope in mind. This supports treating §5 as the single frozen design both levels implement, with
Level 2 needing only a structurally-adapted orchestrator, never a reinterpretation of the rules
themselves.

### Proposal §12.1-§12.3 — read in full (`docs/plans/knowledge-gateway-mcp-proposal.md:687-777`)

§12.2's own invalidation-propagation model states explicitly (lines 726-742): *"changed document ->
invalidate cached items citing that document -> invalidate packets containing those items -> preserve
unrelated packets"* — i.e. the proposal's own design already frames packet-level dependency as a
derived/aggregated concept built from item-level (Level 1-equivalent) dependencies, exactly the
aggregation this ticket's Scope describes and exactly what `final_evidence`'s `path` fields already
provide raw material for. §12.1's evidence-kind table confirms `SYMBOL`/`FILE`/`DOCUMENT`/
`DOCUMENT_SECTION` kinds each have a real "preferred fingerprint," but per
`tools/knowledge_gateway_cache.py`'s own confirmed real behavior
(`test_provider_generation_fallback_used_for_both_real_providers_today`), **neither real provider
today (`context_search`, `graphify`) advertises `fine_grained_fingerprints: True`** — both
`provider_capabilities_context_search.json`/`provider_capabilities_graphify.json` report
`PROVIDER_GENERATION` as the only real, exercised validation basis. This same limitation
structurally carries over to Level 2: a packet-level revalidation function's §4 hard-rule branch
(SYMBOL/FILE-backed evidence never invalidated by a bare generation bump alone) is real code but,
exactly like Level 1's own precedent, only exercisable via a fixture/monkeypatched capability
descriptor today, never against a live provider call — this must be stated honestly in Implementation
Notes, not glossed over as "fully exercised."

## Mechanics / Engine Constraints

Agent-orchestration/retrieval tooling, not simulation logic — no Mechanics Bible chapter or core
engine contract (`kernel.md`/`authoritative_pipeline.md`) governs this module, consistent with every
existing `infrastructure.yaml` entry for this subsystem (INFRA-336, INFRA-345, INFRA-346, INFRA-347
all state this explicitly in their `support_boundary` field). The governing "laws" are this
subsystem's own frozen contracts:
- `evidence_cache_identity_contract.md` §5 (repo/branch/working-tree cache scope — binding on this
  ticket's entire invalidation-logic scope) and §3 (Non-collapse rule — binding on the shape of any
  new revalidation function: it must return a bare `bool`/status, never a `freshness`/`verification`
  field, exactly like `revalidate_cache_row()`'s own existing return-type discipline).
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10.3 (the frozen `evidence_dependencies[]` field
  name and position in `CachedPacket`), §12.1-§12.3 (the invalidation-propagation model this ticket
  implements), §21 ("A changed cited source causes a stale rejection," "An unrelated changed source
  does not invalidate the cached packet," "Branch-local results are not reused across incompatible
  branches," "Relevant uncommitted changes invalidate affected cached evidence" — the four literal
  acceptance-criteria sentences this ticket's own tests must make true).
- `redaction_retention_policy.md` §10 (Cache-GC Defaults) — confirmed by direct read: `prune()`
  remains operator-invoked-only today, no automatic GC exists, and this section's own six
  safe-eviction candidates are explicitly deferred, non-authoritative policy for a future ticket, not
  something this ticket must implement or even touch — the ticket's own Out of Scope note ("unless
  trivially covered by reusing Level 1's existing GC predicates") resolves to **not applicable**: there
  is nothing to trivially reuse, since no automatic GC code exists at either level.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: new entry required, next real ID after the confirmed live
  max (`INFRA-347`, the dedup/budget sibling's own entry) — `INFRA-348` — describing the new
  packet-dependency-aggregation function, the new packet-level revalidation function, and their
  respective real module homes, mirroring INFRA-346/INFRA-347's own level of citation detail.
## Docs Considered But Not Required (resolved during Document-Update, not left open)

- `docs/plans/knowledge-gateway-mcp-proposal.md` §20: originally flagged above (in an earlier draft
  of this investigation) for annotation, on the reasoning that this ticket's dependency-invalidation
  mechanism genuinely does not exist anywhere before this ticket (unlike the dedup/budget sibling's
  capability, which predated it). **Resolved as NOT required**, for a substantive reason found during
  Document-Update, not an oversight: the bullet, "Add packet dependency records and targeted
  invalidation," bundles two sub-capabilities under close reading of its own wording. The "packet
  dependency records" half is genuinely live and reachable today — `assemble_packet()` is already
  wired into the production `knowledge_context` MCP tool since Phase 1, so every real packet now
  carries an accurate `evidence_dependencies` field with zero further wiring. The "targeted
  invalidation" half is real, tested logic (`revalidate_context_packet_row()`), but is NOT reachable
  from any live call path — no Level 2 `check_context_packet_cache()`/`write_context_packet_cache()`
  pair exists anywhere yet; that is `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s job.
  Since the proposal doc's own convention is strictly binary (blank or `**Done**`, with no
  partial-progress annotation form anywhere in the document), and the bullet's "and" joins one live
  half to one not-yet-reachable half, marking it fully Done now would overclaim the invalidation
  half specifically. §20 was deliberately left unmarked by Document-Update rather than annotated —
  this is the final resolution, not an open item for a later ticket to pick up.

None of the Mechanics Bible chapters (`docs/mechanics/`) or core engine contracts require any
change — this subsystem is explicitly outside their scope (see Mechanics/Engine Constraints above).
`evidence_cache_identity_contract.md` itself must **not** be edited unless Plan/Implement concludes
§5 genuinely cannot be reused without a documented extension — this investigation's own finding is
that §5's two low-level primitives ARE directly reusable and its three *rules* are already
level-agnostic in their own wording, so no edit to the frozen contract doc is currently indicated;
if Plan reaches a different conclusion during design, that would require a
`docs/guidelines/intentional_divergences.md` entry, not a silent §5 edit, per this ticket's own Out
of Scope.

## Parity Ledger Overlap

- `INFRA-346` (`docs/parity_ledger/infrastructure.yaml`) — the schema ticket's entry; not modified by
  this ticket (this ticket adds no read/write function against `retrieval_context_packet_cache_rows`,
  matching the schema ticket's own explicit boundary), but its `support_boundary` field's own
  documented obligation (§2.44's Non-collapse-rule divergence, "Verification" clause) is assigned to
  the *later* `READ-WRITE-WIRING` ticket, not this one — confirmed by direct re-read, not this
  ticket's job to discharge.
- `INFRA-347` (dedup/budget sibling) — no functional overlap (different fields:
  `evidence_hash`/`budget_truncated` vs. this ticket's new `evidence_dependencies` aggregation +
  revalidation function), but this ticket adds a new field to the same `PacketAssembly` dataclass
  INFRA-347 also modified — re-verify INFRA-347's own line-range citations for drift once this
  ticket's diff lands, per the established re-verification-caveat convention both prior sibling
  investigations already used for their own overlapping-file citations.
- No P0 entries are touched by this ticket's scope — every existing KGMCP-subsystem entry cited above
  is P1, consistent with the subsystem's existing priority pattern; the new `INFRA-348` entry this
  ticket adds should also be P1, not P0 (confirmed no `test_path` P0-gate risk).
- `docs/guidelines/intentional_divergences.md` §2.44 (Level 2 Packet-Cache Freshness/Verification
  Column Co-location) is cited for context, not touched: its own "Verification" obligation names
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING` explicitly as the ticket that must add the
  guarding test for whatever lookup function it introduces — this ticket introduces no lookup
  function against the table (only pure, standalone aggregation/revalidation logic), so §2.44's
  obligation is not inherited here. This ticket's own new revalidation function must independently
  satisfy the *spirit* of §3's Non-collapse rule regardless (return a bare bool, never a raw
  `freshness`/`verification` value) — see Anti-Drift Hazards.

## Prior Work

- `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` (DONE, sibling child 1) — supplies the real,
  frozen `evidence_dependencies TEXT NOT NULL` (JSON array, single column, no junction table) row
  shape this ticket populates and invalidates against. Its own investigation.md/plan.md were read in
  full for the exact representation decision (quoted above) — this ticket follows it verbatim, per
  its own Assumptions section's explicit deferral.
- `TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT` (DONE, sibling child 2) — confirmed by
  direct read of the live `PacketAssembly` dataclass and its own investigation.md: it added
  `Statement.evidence_hash`/`_content_hash()`/`budget_truncated`/`omitted_statement_count`, but
  **exposes nothing resembling an aggregated evidence-dependency set** — `PacketAssembly.evidence`
  (a list of `EvidenceEntry`, each with an optional `path`) is the closest existing material, and this
  ticket must build the aggregation itself, as a new field/function, not reuse an existing one.
- `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` (DONE) — the real Level 1 implementation of §5's
  branch/working-tree/`changed_paths` logic this ticket investigates and confirms is partially
  (not wholly) reusable — see Current Behavior above for the precise split.
- `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY` (DONE) — froze `evidence_cache_identity_contract.md`
  §5 itself; read in full for this investigation.

## Risks and Open Questions

1. **`working_tree_fingerprint` column has no defined producer anywhere — flagged, not resolved
   here.** `LEVEL2_CACHE_COLUMNS` includes a `working_tree_fingerprint` column (nullable `TEXT`), and
   §12.3's own prose mentions "a fingerprint of relevant uncommitted changes" as part of cache scope,
   but no cited doc (proposal, `evidence_cache_identity_contract.md`, `cache_migration_plan.md`, the
   schema ticket's own artifacts) defines what value this column should hold or how it differs from
   `evidence_dependencies`'s own changed-paths-intersection mechanism. This investigation's own
   reading of §5 rule 3 is that the `changed_paths`-intersection approach (against `evidence_
   dependencies`) is the *actual, sufficient* working-tree-awareness mechanism — §5 explicitly frames
   intersection as an alternative *to* whole-tree/fingerprint hashing ("does not need to hash the
   entire working tree ... obtain changed paths, intersect them"). Whether `working_tree_fingerprint`
   is: (a) vestigial/reserved-but-unused column space from the schema ticket's uniform-JSON-column
   convention, (b) a future Phase 4+ concept, or (c) something this ticket must actually populate is
   a genuine open question this ticket's own Plan phase must decide explicitly — Investigate does not
   assume an answer. Leaning: since neither this ticket's own Scope bullets nor its Acceptance
   Criteria mention `working_tree_fingerprint` by name (only `evidence_dependencies` and
   `changed_paths` intersection are named), the most defensible reading is that this ticket's own
   scope does not require populating it — but this should be an explicit Plan-phase decision, stated
   in Implementation Notes, not a silent omission.
2. **Packet-level revalidation across multiple providers' generations is genuinely new orchestration,
   not a parameter change — the central finding answering Investigate Question 2.** Level 1's
   `revalidate_cache_row()` compares a single `provider_generation_at_validation` string against a
   single `current_provider_generation` string (both real providers today share one corpus-wide
   generation signal via `rc._corpus_generation()`, so in practice this collapses to one value even
   though `write_provider_result_cache()` itself only ever writes one provider's result per row).
   Level 2's `provider_generations` column is genuinely dict-shaped (`{provider_id: generation}`,
   per §10.3), because a single packet aggregates possibly-multiple providers' results. Today, since
   `_corpus_generation()` is a single, corpus-wide, non-provider-specific signal (proxying
   `knowledge-index/manifest.json`'s `built_at`), every provider's entry in that dict would hold the
   identical value on any given call — meaning the dict-vs-string difference is not currently
   *observable* in practice, but the revalidation function's own signature/logic must still be
   written generically over "however many providers this packet actually consulted"
   (`packet.providers_consulted_this_call`), not hardcoded to exactly one, because a future provider
   with its own independent generation signal would otherwise silently under- or over-invalidate.
   This confirms: yes, packet-level revalidation genuinely differs in structure from Level 1's, and a
   packet-specific wrapper (not a direct call) is required — resolves Question 2 definitively.
3. **`is_branch_compatible()` reuse requires the caller to reconstruct the combined
   `repo_branch_scope` string from Level 2's split `repository_id`+`branch` columns** — a one-line
   adapter, not a design gap, but must be done consistently with `_current_repo_branch_scope()`'s
   exact `f"{repo_root}::{branch}"` format (`tools/knowledge_gateway_cache.py:129`) so a Level 2 row
   written under one format and compared under a differently-shaped reconstruction wouldn't silently
   never match. Flagged for Plan to make this exact string-construction logic a single named
   helper, not inlined ad hoc at each call site.
4. **§4's hard rule (SYMBOL/FILE-backed evidence never invalidated by bare generation bump) has no
   real, live-provider-exercised path at Level 2, mirroring Level 1's own honest limitation.** Both
   real providers report `fine_grained_fingerprints: False` today (confirmed directly against both
   `provider_capabilities_*.json` files and the existing `test_provider_generation_fallback_used_
   for_both_real_providers_today` test). Any packet-level revalidation logic implementing this branch
   will, like Level 1's own precedent, only be exercisable via fixture/monkeypatched capability
   descriptors, not a real end-to-end call — must be stated honestly in this ticket's own
   Implementation Notes and test naming (e.g. `_fixture` suffix, mirroring Level 1's own
   `test_symbol_backed_cache_row_rejected_on_direct_fingerprint_mismatch_fixture` naming convention),
   not silently presented as "fully covered by a live path."
5. **This ticket's own Out of Scope explicitly does not require wiring a real `check_*_cache`/
   `write_*_cache` pair for Level 2 into `tools/retrieval_cache.py`** (that belongs to
   `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`) — this means the acceptance criteria's
   "real test, not a fixture-only claim where a live path exists" language must be satisfied via
   direct unit tests against the new aggregation/revalidation functions (constructing a
   `PacketAssembly`/row dict directly and calling the functions), not via an end-to-end
   `_run_knowledge_context()` round-trip, since no live Level 2 storage/lookup path exists yet for
   this ticket to round-trip through. This is a real, structural constraint on what "real test" can
   mean for this ticket specifically — flagged so Plan/Test do not silently assume a live-path
   integration test is achievable when it structurally is not yet (the wiring ticket adds that path).

## Anti-Drift Hazards

- **Do not reimplement `working_tree_overlap_forces_revalidation()` or `is_branch_compatible()`** —
  both are real, generic, already-tested functions in `tools/knowledge_gateway_cache.py`. This
  ticket's own new Level 2 revalidation function must call them directly (same-module call), never
  duplicate their logic under a new name.
- **Do not import `tools/knowledge_gateway_packet_assembly.py` from `tools/knowledge_gateway_
  cache.py`** — a real, currently-passing architecture guard
  (`test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`) forbids this. The
  dependency-aggregation logic (which needs `PacketAssembly`'s fields) must live in
  `knowledge_gateway_packet_assembly.py`; the revalidation-decision logic (which needs only a stored
  row dict + `changed_paths` + generation signals, never a live `PacketAssembly`) must live in
  `knowledge_gateway_cache.py`. Collapsing these into one module/function that imports across this
  boundary would break the guard and violate the Level 1 ticket's own established module-boundary
  discipline.
- **Do not add `check_context_packet_cache()`/`write_context_packet_cache()`-style read/write
  functions against `retrieval_context_packet_cache_rows`** — explicit Out of Scope, assigned to
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`. This ticket ships pure, independently
  callable/testable functions only.
- **Do not add a junction table or any relational dependency-tracking machinery** — the schema
  ticket's own Anti-Drift Hazards explicitly forbid this; `evidence_dependencies` is a single JSON
  column, already frozen by the schema ticket's own decision.
- **Do not let the new revalidation function return a raw `freshness`/`verification` value** — must
  return a bare `bool` (valid/invalid), exactly like `revalidate_cache_row()`'s own existing
  contract, consistent with §3's Non-collapse rule (the schema ticket's own §2.44 divergence entry
  concerns the *schema*, not this ticket's *function* — this ticket's function-shape discipline is a
  separate, still-binding obligation of its own, not discharged by that entry).
- **Do not silently populate `working_tree_fingerprint`** with an invented value to "complete" the
  row shape — Risk 1 above flags this as a genuinely undefined column; inventing a value for it
  without an explicit Plan-phase decision and doc citation would be exactly the kind of
  "collapse investigation into exact coordinates too early" CLAUDE.md's Uncertainty Rule warns
  against.
- **Do not implement semantic/fuzzy dependency matching** — explicit Out of Scope (Phase 5); this
  ticket uses exact evidence-identity (path-string) matching only, consistent with §5's existing
  design and with `working_tree_overlap_forces_revalidation()`'s own exact-set-intersection
  mechanism.
- **Do not implement automatic Cache-GC scheduling** — confirmed above (Mechanics/Engine Constraints)
  that no automatic GC exists at either level to "trivially reuse"; the Out of Scope carve-out
  resolves to not-applicable, not a hidden obligation to build GC scaffolding.
