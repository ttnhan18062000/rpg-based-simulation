---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260731-PARITY-IMPACT-PROOF
phase: done
date: 2026-07-31
tags: [ai, observability, process-improvement, testing]
---

# TCK-20260731-PARITY-IMPACT-PROOF

## Title
Prove deterministic parity-index impact queries against legacy selection behavior

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add the Phase 2 read-only API and prove its behavior against both existing parity-selection
tools. The proof must preserve their legacy semantics as named compatibility output while
explicitly demonstrating the new index's all-shard, faction-inclusive behavior.

## Scope
- Implement the Phase-0-selected CLI/API's `impact`, `entry`, and `health` read operations with
  stable machine-readable schemas, sorted results, selection reasons, and explicit unknown/no-match.
- Support exact path/test/constraint/entry queries from the normalized Phase 1 data. V1 links are
  path-level only; no symbol-coverage claim is permitted.
- Build a versioned equivalence fixture corpus using the Phase 0 baseline. Compare applicable
  results to `find_p0_intersection()` and `cross_reference_touched()` / derived mapping, label each
  intentional difference, and include a faction evidence case.
- Classify malformed/missing/legacy-unstructured inputs through health output without inventing a
  relationship or changing a source/legacy tool.

## Out of Scope
- Changing, retiring, or routing live workflow gates through the index.
- Context packets, retrieval cache/events, semantic search, mutation commands, or source YAML fixes.

## Acceptance Criteria
- [x] `impact`, `entry`, and `health` return deterministic, documented machine-readable output;
      unknown paths are explicit no-match rather than an implicit success.
- [x] The compatibility suite captures exact current legacy results where comparable and documents
      every difference, including P0-substring versus all-priority behavior, ANY-of multi-shard
      semantics, malformed-input treatment, and faction's legacy exclusion.
- [x] All nine shards and their IDs can be represented; faction's source/test evidence appears in
      the new read path despite its zero-P0/legacy exclusion status.
- [x] Legacy scanner/static-gate tests remain unchanged in behavior, and every synthetic fixture
      result plus an unchanged rebuild/query is reproducible.
- [x] Health output reports uncertainty/missing links without modifying YAML or claiming symbol-level coverage.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC
- TCK-20260731-PARITY-INDEX-IMPORTER (dependency)
- TCK-20260731-PARITY-READPATH-GATE (successor)
- TCK-20260705-WORKFLOW-PARITY-SKIP
- TCK-20260705-GATE-DET-PARITY-UPDATER

## Related Docs
- docs/parity_ledger/schema.json
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/

## Related Code Areas
- tools/parity_ledger_scan.py
- tools/gate_checks/parity_updater_static.py
- tools/gate_checks/mechanics_auditor_static.py
- tests/tools/test_parity_ledger_scan.py
- tests/tools/test_parity_updater_static.py
- expected: tests/tools/test_parity_index.py

## Assumptions / Open Questions
- The public command spelling follows Phase 0's recorded ownership decision; this ticket owns
  query semantics, not a second CLI-placement decision.

## Implementation Notes
Legacy outputs are comparison evidence, not the target all-shard semantics.

Implemented `staging_artifacts/TCK-20260731-PARITY-IMPACT-PROOF/plan.md`'s 15 steps in order,
following its Decisions 1-2 verbatim:

- **Step 1**: Added `_STATUS_SEVERITY`, `_PRIORITY_ORDER`, `_IMPACT_PATH_TABLES` module constants,
  `IndexNotBuiltError`, `_connect_readonly(db_path)` (opens `sqlite3.connect(f"file:{db_path}?mode=ro",
  uri=True)`, raises `IndexNotBuiltError` if the db file doesn't exist), and `_selection_reason(table,
  source_field, relation)` to `tools/parity_index.py`, alongside the existing `_REF_TABLES` constant.
  None of `_create_schema`/`_populate_ref_tables`/`_populate_entry_health`/`build()` internals touched.
- **Step 2**: Added `entry(entry_id, db_path=None) -> dict` — `SELECT *` from `entries`, explicit
  `{"entry_id": ..., "found": False}` on miss, else full record plus `code_refs`/`test_refs`/
  `constraint_refs`/`ticket_refs`/`health_findings` each ordered per plan. Wired `entry` subparser into
  `main()`; restructured `main()`'s dispatch to branch on `args.command` (previously `build` was the
  only branch), catching `IndexNotBuiltError` for a structured `{"status": "error", ...}` + exit 1.
- **Step 3**: Added `impact(changed_path=None, test_path=None, symbol=None, db_path=None) -> dict`.
  `no_filter_provided` when both filters are `None`; exact `WHERE path = ?` against `code_refs`/
  `constraint_refs`/`ticket_refs` for `changed_path`, against `test_refs` for `test_path`; results
  sorted by `(_PRIORITY_ORDER, _STATUS_SEVERITY, entry_id)`; `no_match` when the filters produce zero
  rows, else `ok`. Wired `impact` subparser (`--changed-path`, `--test`, `--db-path`).
- **Step 4**: Added `--symbol` to the `impact` subparser and threaded it through `impact()`'s existing
  `symbol` parameter (already present from Step 3). `warnings` key appended only when `symbol is not
  None`; never present otherwise. Never reaches a `WHERE` clause.
- **Step 5**: Added `health(subsystem=None, priority=None, db_path=None) -> dict` — joins
  `entry_health`/`entries`, optional exact `subsystem`/`priority` filters, ordered by
  `(entries.shard, entries.id)` matching Phase 1's own `ORDER BY shard, id` convention, plus a
  `ledger_generation` summary header. Wired `health` subparser (`--subsystem`, `--priority`,
  `--db-path`).
- **Step 6**: Replaced the docstring's stale "`impact_candidates` ... intentionally not built here"
  line with a truthful statement naming this ticket as the one that added `impact`/`entry`/`health`,
  and that `search` remains out of scope. No other docstring paragraph touched.
- **Step 7**: Renamed `TestArchitectureGuards::test_importer_does_not_implement_impact_or_entry_or_health_cli`
  to `test_impact_entry_health_still_forbid_search_cli` per Decision 1, deleting the
  `impact`/`entry`/`health`-absence assertions (now positively covered by Steps 2/3/5's own new test
  classes) and keeping only the `search`-forbidden assertions, with the docstring explaining the
  narrowing and citing this ticket ID.
- **Steps 8-11**: Added `TestEquivalenceFixtures` with
  `test_equivalence_p0_substring_vs_all_priority_documented` (imports `find_p0_intersection` from
  `tools.parity_ledger_scan`), `test_equivalence_any_of_multi_shard_semantics_matches_legacy` (imports
  `derive_mapping` from `tools.gate_checks.parity_updater_static`, mirrors
  `test_derive_mapping_handles_multi_subsystem_file`'s fixture shape),
  `test_equivalence_malformed_input_treatment_documented_as_divergence` (reuses the malformed-shard
  fixture pattern, asserts the divergence rather than reconciling it), and
  `test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion` (the ticket's most
  load-bearing new test per test_plan.md's Anti-Drift Test Guards).
- **Step 12**: Added `TestAllShardsCoverage::test_impact_and_entry_cover_all_nine_shards_including_faction`,
  built on `_full_nine_shard_corpus`'s naming convention with a `v2_evidence` path added specifically to
  the `faction.yaml` fixture entry for this test.
- **Step 13**: Added `TestDeterminism::test_impact_query_is_reproducible_on_unchanged_index`, calling
  `impact`/`entry`/`health` twice each against an unchanged index and asserting
  `serialize_manifest(...)` byte-identical output.
- **Step 14**: Added `TestArchitectureGuards::test_health_subcommand_never_writes_to_docs_parity_ledger`
  (additive, alongside the untouched existing write-path guard test), snapshotting fixture shard YAML
  bytes before/after a `health(...)` call with `missing_test_path`/`legacy_unstructured` findings
  present.
- **Step 15**: Ran all three scoped pytest commands (see Test Summary) plus
  `python3 tools/validate_frontmatter.py` against all three staging artifacts — all green.

No deviations from `plan.md`'s function signatures, schemas, sort orders, or CLI flag names. One
documentation-discipline note recorded per this ticket's own instructions: Step 7's test-narrowing
(deleting three assertions from a test used elsewhere in the suite) is logged explicitly in
`staging_artifacts/TCK-20260731-PARITY-IMPACT-PROOF/plan.md`'s new Deviations section, even though it
was plan-approved, following the IMPORTER ticket's own precedent for this class of change.

No `src/` files touched. No `docs/parity_ledger/*.yaml` entry added or edited — investigation.md's
Parity Ledger Overlap section already established none is required (no `src/` behavior change, no
`v2_evidence` touched, no gate behavior changed).

## Test Summary
All new and existing tests green, verified via the three scoped commands test_plan.md specifies:

- `pytest tests/tools/test_parity_index.py -v` — 29 passed (15 Phase-1 tests, one renamed per Step 7,
  14 new Phase-2 tests).
- `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v` —
  13 passed, zero edits to either file or its tests.
- `pytest tests/tools/test_parity_index_baseline.py -v` — 15 passed, Phase-0 suite untouched.
- `python3 tools/validate_frontmatter.py` against `investigation.md`, `test_plan.md`, and `plan.md` —
  all three OK.
- Manual CLI smoke test (`build`, `entry`, `impact` with/without `--symbol`, `health` with filters,
  and `entry`/`health`/`impact` against a nonexistent db path) confirmed the `IndexNotBuiltError`
  exit-1 path, the `no_filter_provided`/`no_match`/`ok` statuses, and the `--symbol` warnings field
  all behave as specified.
- `tests/tools/test_build_index.py` intentionally excluded from the required-green set (pre-existing,
  unrelated Makefile phony-target failure, per test_plan.md).

## Files Changed
- `tools/parity_index.py` — added `entry`/`impact`/`health` read functions, shared read-only query
  infrastructure (`_connect_readonly`, `_selection_reason`, `_STATUS_SEVERITY`/`_PRIORITY_ORDER`/
  `_IMPACT_PATH_TABLES`), `IndexNotBuiltError`, CLI subparsers/dispatch for the three new subcommands,
  and a docstring correction. `build()` and all Phase-1 internals unchanged.
- `tests/tools/test_parity_index.py` — added `TestEntryQuery`, `TestImpactQuery`, `TestHealthQuery`,
  `TestEquivalenceFixtures`, `TestAllShardsCoverage` classes; extended `TestDeterminism` and
  `TestArchitectureGuards` with one new test method each; renamed/narrowed
  `test_importer_does_not_implement_impact_or_entry_or_health_cli` to
  `test_impact_entry_health_still_forbid_search_cli`; added `sys.path`/import setup for
  `find_p0_intersection` and `derive_mapping`.

## Completion Summary
Added the Phase-2 read-only `impact`/`entry`/`health` query surface to `tools/parity_index.py` in
place (no new module), each opening the index via a read-only SQLite URI connection, with
deterministic sort orders, synthesized selection reasons, and explicit no-match/unknown responses.
Built a versioned equivalence fixture corpus proving the new index's behavior against
`find_p0_intersection` (P0-only, substring) and `cross_reference_touched`/`derive_mapping` (all-priority,
ANY-of-multi-shard) as two independently distinct comparisons, plus a faction-evidence case and a
malformed-input divergence case (labeled, not reconciled). Narrowed Phase 1's own architecture-guard
test to only its still-valid `search`-forbidden assertion, per that test's own named forward reference
to this ticket. No `src/` code touched, no `docs/parity_ledger/*.yaml` content changed, no legacy
comparison-target function modified. All 5 acceptance criteria satisfied; 57/57 tests green (43
pre-existing across `test_parity_index.py`/`test_parity_index_baseline.py`/`test_parity_ledger_scan.py`/
`test_parity_updater_static.py` plus 14 new tests in `test_parity_index.py`), frontmatter valid on all
three staging artifacts.

