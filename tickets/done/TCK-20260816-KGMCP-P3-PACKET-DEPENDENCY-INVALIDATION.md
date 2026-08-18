---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION
phase: done
date: 2026-08-16
tags: [ai, mcp]
---

# TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION

## Title
Add packet dependency records and targeted invalidation for the Level 2 context-packet cache

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Proposal §20 Phase 3's fourth bullet is "Add packet dependency records and targeted invalidation."
A Level 2 cached packet's `evidence_dependencies` field (§10.3's `CachedPacket` schema) must record
exactly which evidence sources a packet depends on, so that a targeted change to one of those
sources invalidates only the affected packet(s) — never a repository-wide invalidation, and never a
missed invalidation that serves stale content. `evidence_cache_identity_contract.md` §5 already
designed and froze this exact mechanism at the Level 1 provider-result granularity (branch is a
hard partition; a new commit alone is not a miss; `changed_paths` intersection against a cached
row's dependency paths, not whole-tree hashing). This ticket investigates whether that same §5
mechanism can be reused or extended at the packet level, rather than reinventing an equivalent
mechanism for Level 2.

## Scope
- Implement real packet dependency records: each Level 2 cached packet's `evidence_dependencies`
  column (per the schema ticket's row shape) captures every evidence source path/symbol/hash the
  packet's answer and context items actually depend on — aggregated from the dependencies of every
  provider result the packet assembled, not merely a superset copy of every source ever consulted.
- Investigate whether `evidence_cache_identity_contract.md` §5's `changed_paths`-intersection logic
  (currently implemented at Level 1 granularity by `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`)
  can be called/reused directly against a packet's aggregated `evidence_dependencies`, or whether it
  needs a packet-specific extension (e.g. because a packet's dependency set spans multiple
  providers' evidence, unlike a single Level 1 row). Document the finding and the chosen approach
  explicitly in this ticket's own Investigate phase — do not assume either answer.
- Implement real targeted invalidation: a `changed_paths` intersection hit against a packet's
  dependency paths forces that packet (and only that packet, plus any other packet sharing the same
  dependency) to be revalidated/invalidated; an unrelated changed source does not invalidate it.
- Preserve §5's already-frozen invariants at the packet level: branch identity is a hard partition
  before any fingerprint comparison; a new commit alone with unchanged evidence fingerprints is not
  a miss.
- Real tests: a changed cited source invalidates the affected packet (real test, not a fixture-only
  claim where a live path exists); an unrelated changed source does not invalidate an unrelated
  packet; a packet cached on one branch is not served on an incompatible branch even with identical
  dependency fingerprints.

## Out of Scope
- Level 2 schema/table creation — depends on `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS`
  already existing; this ticket does not create tables, only populates and invalidates the
  dependency-tracking columns/rows that ticket defines.
- Deduplication or budget-enforcement logic — `TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-
  ENFORCEMENT`'s job.
- Live wiring of Level 2 cache lookup/write into `_run_knowledge_context()` — that is
  `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s job; this ticket builds the invalidation
  logic as real, independently-testable functions, not necessarily hooked into the live call path
  yet (the wiring ticket integrates it).
- Modifying `evidence_cache_identity_contract.md` §5 itself unless investigation finds it must be
  extended to explicitly cover packet-level (vs. row-level) dependency sets — any such extension
  must be a documented addition, not a silent reinterpretation of the frozen §1-§4 identity split.
- Semantic/fuzzy dependency matching (Phase 5) — this ticket uses exact evidence-identity matching
  only, consistent with §5's existing design.
- Cache-GC scheduling for stale/invalidated packets — out of scope unless trivially covered by
  reusing Level 1's existing GC predicates (§10 of `redaction_retention_policy.md`).

## Acceptance Criteria
- [x] Every Level 2 cached packet's `evidence_dependencies` field accurately records the real
      aggregated evidence dependencies of the packet's own answer/context items — verified by a
      real test comparing the recorded set against the actual sources the packet's constituent
      provider results depended on.
- [x] A changed cited source (real fixture or live-path test, per what the ticket's Investigate
      phase finds feasible) causes the affected packet to be invalidated/revalidated — real test,
      not a documentation claim.
- [x] An unrelated changed source does not invalidate a packet with no dependency overlap — real
      test.
- [x] Branch identity remains a hard partition at the packet level: a packet cached on one branch is
      never served as valid on an incompatible branch, even with identical dependency fingerprints —
      real test.
- [x] A new commit alone, with unchanged evidence fingerprints, does not force a packet cache miss —
      real test, mirroring §5's Level 1 precedent.
- [x] The Investigate-phase finding on whether §5's `changed_paths`-intersection logic was reused
      directly or extended is documented explicitly in this ticket's Implementation Notes, with the
      reasoning for whichever choice was made.
- [x] A real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry is added for this
      ticket's own behavior change, per this repo's own governance rule. Written as `INFRA-348`
      via `tools/parity_ledger_writer.py::write_entry()` in the separate Parity phase.

## Related Tickets
- TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC (parent)
- TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS (dependency; supplies the
  `evidence_dependencies`-bearing schema this ticket populates and invalidates against)
- TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DONE; the real Level 1 implementation of §5's
  branch/working-tree/`changed_paths` logic this ticket investigates reusing at the packet level)
- TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY (DONE; froze `evidence_cache_identity_contract.md` §5,
  the design this ticket investigates reusing/extending)

## Related Docs
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §5
  (Repository/branch/working-tree cache scope — the frozen `changed_paths`-intersection design)
- `docs/plans/knowledge-gateway-mcp-proposal.md` §10.3 (`evidence_dependencies` field), §12.1-§12.3
  (Evidence Dependency Granularity, Evidence-Aware Invalidation, Branch and Working-Tree
  Awareness), §20 Phase 3, §21 ("A changed cited source causes a stale rejection," "An unrelated
  changed source does not invalidate the cached packet," "Branch-local results are not reused
  across incompatible branches," "Relevant uncommitted changes invalidate affected cached
  evidence")

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/knowledge_gateway_cache.py` (Level 1's real `perform_cache_lookup()`/evidence-validity
  revalidation logic — the direct precedent for whatever this ticket reuses or extends)
- `tools/retrieval_cache.py` (Level 2 schema this ticket populates, once the schema ticket lands)

## Assumptions / Open Questions
- Whether §5's `changed_paths`-intersection logic is reused by direct function call against a
  packet's aggregated dependency set, or needs a packet-specific wrapper/extension, is the central
  open question this ticket's own Investigate phase must resolve and document — not decided here.
- Whether packet-level dependency tracking needs its own junction table (packet_id ×
  evidence_path/hash) versus a single JSON column on the Level 2 row is coordinated with, but not
  decided by, this ticket alone — if the schema ticket already chose a representation, this ticket
  follows it; if not yet decided, this ticket's Investigate phase should flag the need back rather
  than silently picking one that conflicts with the schema ticket's own design.

## Implementation Notes
Implemented exactly per the approved `staging_artifacts/TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-
INVALIDATION/plan.md` (post-Architecture-Review-correction), with no deviations. Two additive
pieces, neither wired into a live call path (that is `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-
WRITE-WIRING`'s job):

1. **`PacketAssembly.evidence_dependencies: list[str]`** (`tools/knowledge_gateway_packet_
   assembly.py`) — new dataclass field, placed after `evidence`, before `conflicts`. Populated by
   a new helper `_evidence_dependencies(context_entries)` (`sorted({c.path for c in context_entries
   if c.path})`), called in `assemble_packet()` from `final_context`, not `final_evidence`. Only
   one `PacketAssembly(...)` construction site exists in the whole repo
   (`assemble_packet()`'s own `return`), confirmed by grep before and after the change — no other
   constructor could break.

2. **`_level2_repo_branch_scope(repository_id, branch)`** and **`revalidate_context_packet_row(row,
   *, capability_descriptor, current_provider_generations, current_repository_id, current_branch,
   changed_paths)`** (`tools/knowledge_gateway_cache.py`) — a new sibling pair to
   `revalidate_cache_row()`, added immediately after it. `_level2_repo_branch_scope()` is a pure
   string join (`f"{repository_id}::{branch}"`, matching `_current_repo_branch_scope()`'s own
   format), never a `git` read. `revalidate_context_packet_row()` performs, strictly in this order:
   (1) branch-compatibility check via the adapter + `is_branch_compatible()` (returns `False`
   immediately on incompatibility, before any other comparison), (2)
   `working_tree_overlap_forces_revalidation()` against `row["evidence_dependencies"]`, (3)
   `select_validation_basis()` — fails closed (`False`) on any basis other than
   `"PROVIDER_GENERATION"` (DD4), (4) a per-provider dict comparison of
   `json.loads(row["provider_generations"])` against the caller-supplied
   `current_provider_generations`. All four reused primitives
   (`is_branch_compatible`, `working_tree_overlap_forces_revalidation`, `select_validation_basis`,
   `_capability_descriptor_for`) are called directly, unmodified — none reimplemented.
   `revalidate_cache_row()` itself is byte-unchanged. The function never reads
   `row["head_commit"]`/`row["working_tree_fingerprint"]` (DD2) and never imports
   `tools.knowledge_gateway_packet_assembly` — the existing AST-based architecture guard
   (`test_module_does_not_import_knowledge_gateway_router_or_packet_assembly`) still passes,
   re-verified directly after the change.

**Investigate-phase reuse-vs-extension finding (AC6).** §5's two low-level primitives
(`is_branch_compatible()`, `working_tree_overlap_forces_revalidation()`) are fully generic — reused
by direct, unmodified call, with only a one-line adapter (`_level2_repo_branch_scope()`) needed to
reconstruct the combined `repo_branch_scope` string from Level 2's split `repository_id`/`branch`
columns. `revalidate_cache_row()` itself (the orchestrator) is **not** directly reusable — it
hardcodes Level 1 column names (`working_tree_overlap`, `evidence_fingerprints`,
`provider_generation_at_validation`) that either do not exist in `LEVEL2_CACHE_COLUMNS` at all, or
exist under a differently-shaped column (`provider_generations` is a `{provider_id: generation}`
dict at Level 2, vs. Level 1's single string). This required a genuinely new sibling orchestrator
(`revalidate_context_packet_row()`), not a parameter tweak, for two structural reasons: (a) the
dict-shaped multi-provider generation comparison Level 1's schema has no equivalent of, and (b)
Level 2 has no lookup-orchestrator caller yet to do the branch check first (unlike Level 1's
`perform_cache_lookup()`), so the new function must perform that check itself, first, internally.

**DD1 — aggregation source correction (implemented as specified).** `evidence_dependencies` is
computed from `final_context`, not `final_evidence`. The two are identical in the ordinary/
truncated branches (same `source_id`/`evidence_id` filter), but diverge in the §16
budget-assembly-failure branch: `final_context` is correctly emptied there (matching the packet's
own empty `answer`/`statements`), while `final_evidence` is deliberately left as the full,
unfiltered `evidence_entries` list by the sibling DEDUP-BUDGET ticket's own design. Aggregating
from `final_evidence` would have produced an inaccurate superset on that one failure path, which
AC1 explicitly forbids ("not merely a superset copy of every source ever consulted"). Verified by a
new, Plan-derived test
(`test_evidence_dependencies_empty_in_section16_budget_assembly_failure_not_full_unfiltered_evidence`)
asserting `evidence_dependencies == []` while `packet.evidence` remains non-empty on that branch.

**DD4 — fail-closed default when `select_validation_basis()` returns `"FINER"` (implemented as
specified, a genuine safety default, not a placeholder).** Level 2's `LEVEL2_CACHE_COLUMNS` has no
`evidence_fingerprints`-equivalent column, so there is no schema-legal way to perform §4's
finer-grained comparison when a provider advertises `fine_grained_fingerprints: True`.
`revalidate_context_packet_row()` treats this as "cannot verify with the data this schema
provides" and returns `False` (forces revalidation) rather than assuming validity without proof.
Unreachable against both real providers today (both report `fine_grained_fingerprints: False`,
confirmed directly against `provider_capabilities_context_search.json`/
`provider_capabilities_graphify.json`) — exercised only via a fixture capability descriptor
(`test_revalidate_context_packet_row_fails_closed_when_finer_basis_selected_but_no_level2_
fingerprint_column_exists`), stated honestly, not presented as a live-provider-exercised path.

**Honest limitation carried over from Level 1 (same class as investigation.md Risk 4):** the §4
hard rule's `"FINER"` branch has no real, live-provider-exercised path at Level 2 either, mirroring
Level 1's own identical limitation — both real providers report `fine_grained_fingerprints: False`
today.

**`working_tree_fingerprint` (DD2):** intentionally not populated or read by either new function —
no cited doc defines what value it should hold, the `changed_paths`-intersection mechanism against
`evidence_dependencies` is §5 rule 3's own complete, sufficient mechanism, and this ticket ships no
write function for the table at all (confirmed:
`test_no_actual_read_write_functions_added_for_the_new_level2_table` still passes).

**Scope guards confirmed via direct grep/git diff, not merely claimed:** `tools/retrieval_cache.py`
is byte-unchanged by this ticket's own diff (this implementer session never opened it with
Edit/Write — only Read/grep for verification); `tools/knowledge_gateway_router.py` is
byte-unchanged; no `check_context_packet_cache()`/`write_context_packet_cache()` pair was added; no
junction table was added (`test_no_junction_table_or_new_sqlite_table_introduced_by_this_ticket`
independently re-confirms `tools/retrieval_cache.py` still has exactly 6 real
`CREATE TABLE IF NOT EXISTS \w+\s*\(` DDL statements, matching the Architecture-Review-corrected
baseline in plan.md).

Document-Update (parity ledger `INFRA-348`, proposal §20 annotation, module docstring/comment
updates) is explicitly left to the separate Document-Update phase per plan.md Step 6, not done in
this Implement pass.

## Test Summary
All scoped pytest commands from `test_plan.md` were run directly against this session's diff:

```
python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v   # 42 passed (38 existing + 4 new)
python3 -m pytest tests/tools/test_knowledge_gateway_cache.py -v             # 30 passed (20 existing + 10 new)
python3 -m pytest tests/tools/test_retrieval_cache.py::TestLevel2Migrations -v  # 13 passed, unmodified
python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -q               # 22 passed, unmodified
python3 -m pytest tests/tools/test_knowledge_gateway_router.py -q            # 31 passed, unmodified
```

New tests added (14 total — the 10 enumerated in `test_plan.md`'s New Tests 1-3/5-11 that this
ticket's own diff required, plus the existing regression re-run of New Test 12, plus 2 Plan-derived
tests from DD1/DD4):

- `tests/tools/test_knowledge_gateway_packet_assembly.py`: `test_evidence_dependencies_aggregated_
  from_packet_evidence_paths`, `test_evidence_dependencies_excludes_paths_from_omitted_budget_
  truncated_statements`, `test_evidence_dependencies_omits_graphify_symbol_evidence_with_no_path`,
  `test_evidence_dependencies_empty_in_section16_budget_assembly_failure_not_full_unfiltered_
  evidence` (Plan-derived, DD1).
- `tests/tools/test_knowledge_gateway_cache.py`: `test_level2_repo_branch_scope_matches_current_
  repo_branch_scope_join_format`, `test_revalidate_context_packet_row_rejects_on_changed_paths_
  intersection`, `test_revalidate_context_packet_row_survives_unrelated_changed_path`,
  `test_revalidate_context_packet_row_rejects_cross_branch_even_with_identical_dependencies`,
  `test_revalidate_context_packet_row_survives_new_commit_alone_unchanged_generations`,
  `test_revalidate_context_packet_row_multi_provider_generations_dict_all_checked`,
  `test_revalidate_context_packet_row_never_returns_freshness_or_verification_field`,
  `test_revalidate_context_packet_row_fails_closed_when_finer_basis_selected_but_no_level2_
  fingerprint_column_exists` (Plan-derived, DD4), `test_working_tree_overlap_forces_revalidation_
  called_unmodified_against_evidence_dependencies_shape`, `test_no_junction_table_or_new_sqlite_
  table_introduced_by_this_ticket`.

Invariants independently re-verified this session (not merely asserted): exactly one
`PacketAssembly(...)` construction site exists repo-wide (grep, before and after); the AST-based
`test_module_does_not_import_knowledge_gateway_router_or_packet_assembly` guard passes;
`tools/retrieval_cache.py` real DDL count is 6 (`re.findall(r"CREATE TABLE IF NOT EXISTS \w+\s*\("
, source)`); `git diff` on `tools/retrieval_cache.py`/`tools/knowledge_gateway_router.py` shows no
change attributable to this implementer session.

## Files Changed
- `tools/knowledge_gateway_packet_assembly.py` — added `evidence_dependencies: list[str]` field to
  `PacketAssembly`; added `_evidence_dependencies()` helper; wired into `assemble_packet()`.
- `tools/knowledge_gateway_cache.py` — added `_level2_repo_branch_scope()` adapter and
  `revalidate_context_packet_row()` orchestrator, as a new "Step 9" section after
  `revalidate_cache_row()`; module docstring's "What this is not" section corrected
  post-Architecture-Verify (its "no Level 2/Level 3 caching" line was stale now that Level 2
  revalidation-decision logic genuinely lives here — fixed to accurately describe the new function
  while still correctly disclosing no live Level 2 lookup/write path is wired in yet).
- `tests/tools/test_knowledge_gateway_packet_assembly.py` — added 4 new tests (3 from test_plan.md
  New Tests 1-3, 1 Plan-derived per DD1).
- `tests/tools/test_knowledge_gateway_cache.py` — added 10 new tests (New Tests 4-11 from
  test_plan.md's enumerated set, plus 1 Plan-derived per DD4).

Not touched by this ticket (verified): `tools/retrieval_cache.py`, `tools/knowledge_gateway_
router.py`, `tools/knowledge_gateway_mcp.py`, `evidence_cache_identity_contract.md`.

**Document-Update phase (this pass):**
- `docs/parity_ledger/infrastructure.yaml` — **not edited** in this pass. Next real ID confirmed
  `INFRA-348` (`INFRA-347` is the current live max, re-confirmed by direct
  `grep -n "^- id: INFRA-3" docs/parity_ledger/infrastructure.yaml` this session), but the write
  itself is deferred to the separate Parity phase, per this repo's own established convention: both
  immediately-preceding Phase 3 siblings (`PACKET-CACHE-SCHEMA-MIGRATIONS` → `INFRA-346`,
  `PACKET-DEDUP-BUDGET-ENFORCEMENT` → `INFRA-347`) wrote their own entries under a distinct
  "Parity:"/"Parity-Update:" heading, separate from and after their "Document-Update:" heading — not
  as part of Document-Update. Following that same convention here rather than writing the entry
  early.

**Parity phase (ran after the above):**
- `docs/parity_ledger/infrastructure.yaml` — added `INFRA-348` (status=verified, priority=P1,
  proof_type=regression) via `tools/parity_ledger_writer.py::write_entry()`, citing
  `PacketAssembly.evidence_dependencies`/`_evidence_dependencies()`/`_level2_repo_branch_scope()`/
  `revalidate_context_packet_row()` with real line numbers in
  `tools/knowledge_gateway_packet_assembly.py` and `tools/knowledge_gateway_cache.py`, and the 14
  new tests (4 in `test_knowledge_gateway_packet_assembly.py` + 10 in
  `test_knowledge_gateway_cache.py`) as `test_path`. `support_boundary` states explicitly that this
  ticket builds real, tested logic not yet wired into a live Level 2 lookup/write path
  (`TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING`'s job), that `tools/retrieval_cache.py`
  was not touched, that `revalidate_context_packet_row()` never imports
  `tools.knowledge_gateway_packet_assembly`, and that both DD1 and DD4 were independently confirmed
  non-vacuous by Architecture-Verify via live break/restore testing.
- Citation-drift correction on two prior entries whose cited line numbers in
  `tools/knowledge_gateway_cache.py` / `tools/knowledge_gateway_packet_assembly.py` shifted because
  of this ticket's own insertions (both corrected in place, mirroring this epic's established
  precedent — not duplicated as new entries):
  - `INFRA-343` (`tools/knowledge_gateway_cache.py`): `compute_lookup_identity()` 132-155→137-154,
    `select_validation_basis()` 157-163→162-166, `is_branch_compatible()` 191-194→196-198,
    `working_tree_overlap_forces_revalidation()` 196-202→201-206, `revalidate_cache_row()`
    204-219→209-224 (docstring-correction shift, +5), `perform_cache_lookup()` 226-249→285-308,
    `perform_cache_write()` 262-335→321-394 with internal refs :282-283→:341-342 (PARTIAL-status
    refusal), :306→:365 (`evaluate_write_candidate()` call), :307→:366 (verdict check) (Step-9-
    insertion shift, +59). `revalidate_cache_row()` itself reconfirmed byte-unchanged.
  - `INFRA-347` (`tools/knowledge_gateway_packet_assembly.py`): `PacketAssembly.budget_truncated`/
    `omitted_statement_count` field declarations 630-631→631-632 (+1, the new
    `evidence_dependencies` field lands above them), the cardinality assertion 662-670→680-688 and
    its post-`assemble_within_budget()` computation 689-690→707-708 (+18, the new
    `_evidence_dependencies()` helper lands above both), and the `PacketAssembly` constructor
    threading 740-741→760-761 (+20, the `evidence_dependencies=` constructor argument lands above
    them too).
  - `INFRA-336` checked and confirmed to require no correction — it cites
    `tools/knowledge_gateway_packet_assembly.py` by function name only, no line numbers, so nothing
    to drift.
- Ran `python3 tools/parity_index.py build` as a separate, visible Bash call after all three writes
  (redundant with `write_entry()`'s own in-process rebuild for correctness, but required for the
  `parity_write_safety` retro metric per `.claude/agents/parity-updater.md`).
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 3 — **not edited; deliberately left
  unmarked**, an independent Document-Update-phase decision, not a default deferral to either prior
  sibling's precedent. Read directly: the fourth bullet, "Add packet dependency records and targeted
  invalidation," combines two sub-capabilities the doc's own strictly-binary (blank/`**Done**`)
  convention (confirmed by the schema-migrations sibling's own explicit check across all 7 phases —
  no partial-progress annotation exists anywhere) does not let this ticket honestly split apart:
  - "packet dependency records" — genuinely satisfied, live, and reachable *today*: `assemble_
    packet()` is already wired into the production `knowledge_context` MCP tool since Phase 1 (see
    §20 Phase 1's own "Expose `knowledge_context`..." Done bullet), so this ticket's `evidence_
    dependencies` field is populated on every real packet a live caller receives right now, with no
    further wiring needed.
  - "targeted invalidation" — real, tested logic (`revalidate_context_packet_row()`), but **not**
    reachable from any live call path yet: no Level 2 `check_context_packet_cache()`/`write_context_
    packet_cache()` pair exists anywhere in the repo (confirmed above), so there is no live cache row
    for this function to ever be invoked against until `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-
    WRITE-WIRING` lands. This mirrors the schema-migrations sibling's own reasoning for its unmarked
    bullet almost exactly ("real, tested [code] landed, but not yet an operationally reachable
    capability") — not the dedup-budget sibling's different reasoning (pre-existing capability,
    hardened not originated), which does not apply here (investigation.md's own confirmation that no
    dependency-tracking/invalidation mechanism existed anywhere before this ticket stands).
  Since the bullet's "and" joins one live-reachable half to one not-yet-reachable half, and the doc
  provides no mechanism to credit only the live half, marking the whole bullet **Done** now would
  overclaim the "targeted invalidation" half specifically. Left unmarked, consistent with (though
  independently re-derived from, not copied from) both prior Phase 3 siblings' own precedent of never
  claiming a bullet before its full, reachable capability lands.

## Completion Summary
Implemented `PacketAssembly.evidence_dependencies` (aggregated from `final_context`, per DD1's
corrected aggregation source) and the new `revalidate_context_packet_row()`/
`_level2_repo_branch_scope()` pair in `tools/knowledge_gateway_cache.py`, giving the Level 2
context-packet cache real, testable dependency records and targeted-invalidation logic that reuses
§5's `is_branch_compatible()`/`working_tree_overlap_forces_revalidation()` primitives unmodified
and fails closed on the `"FINER"`-validation-basis branch (DD4) where Level 2's schema has no
fingerprint column to support it. Both pieces are additive, pure, and not yet wired into any live
lookup path (explicit Out of Scope — the read-write-wiring ticket's job). 14 new tests were added
across the two affected test files and the full regression surface (packet_assembly, cache,
Level 2 migrations, MCP integration, router) passes unmodified. Document-Update ran:
`docs/parity_ledger/infrastructure.yaml` was deliberately left for the separate Parity phase (real
next ID confirmed `INFRA-348`, per this repo's own established convention, not written there), and
`docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 3's fourth bullet was deliberately left
unmarked — this ticket's dependency-record aggregation half is live/reachable today, but its
targeted-invalidation half has no live call path to be reachable through until the read-write-wiring
ticket lands, and the doc's own strictly-binary convention has no way to credit only the reachable
half without overclaiming the other (see Files Changed for the full, independently-derived
reasoning).

Parity has now run: `INFRA-348` was added to `docs/parity_ledger/infrastructure.yaml` (verified/P1/
regression) via the schema-validating writer, citing real line numbers for
`evidence_dependencies`/`_evidence_dependencies()`/`_level2_repo_branch_scope()`/
`revalidate_context_packet_row()` and all 14 new tests, with an explicit `support_boundary`
disclosing the not-yet-wired-in limitation. `INFRA-343` and `INFRA-347`'s own citations into
`tools/knowledge_gateway_cache.py` and `tools/knowledge_gateway_packet_assembly.py` were corrected
in place (not duplicated) for line-number drift this ticket's own insertions caused;
`python3 tools/parity_index.py build` was run as a separate visible call afterward. AC7 (the parity
ledger entry) is now satisfied — all seven Acceptance Criteria are complete. The remaining P0/AC-
blocking item, if any, is that this ticket is still `tickets/inprogress/` rather than
`tickets/done/`; Verify/Finalize have not yet run in this pass.
