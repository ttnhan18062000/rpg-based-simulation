---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260826-PARITY-FACTION-CANONICAL-SCAN
artifact_type: test_plan
tags: [ai, workflows, faction, determinism]
---

# Test Plan — TCK-20260826-PARITY-FACTION-CANONICAL-SCAN

## Regression Surface

Unit (tools-lane, pure functions — no simulation/kernel involved):
- `tests/tools/test_parity_ledger_scan.py` — `find_p0_intersection`/`ShardParseError` coverage.
  Contains one test (`test_only_scans_canonical_eight_not_faction`) that must be rewritten (see
  New Tests Required), the rest (`test_detects_p0_intersection_via_synthetic_fixture`,
  `test_no_intersection_for_representative_docs_only_change`,
  `test_find_p0_intersection_malformed_shard_raises_labeled_error_not_crash`) must keep passing
  unmodified.
- `tests/tools/test_parity_updater_static.py` — `derive_mapping`/`expected_subsystems_for_files`/
  `cross_reference_touched`/`next_available_id`/`search_existing_entries` coverage. Contains one
  test (`test_excludes_faction_yaml`, lines 90-99) that must be rewritten — **found during
  investigation, not named in the ticket's own Scope bullets**. `test_reuses_canonical_ledger_files_constant`
  (identity check, `CANONICAL_LEDGER_FILES is SCAN_CANONICAL_LEDGER_FILES`) must keep passing
  unmodified — it is unaffected by tuple contents. All other tests in this file (`derive_mapping`
  path-extraction/multi-subsystem/malformed-yaml-skip tests, `expected_subsystems_for_files`/
  `cross_reference_touched`/`next_available_id`/`search_existing_entries` tests below line 110)
  must keep passing unmodified.
- `tests/tools/test_parity_index.py` — full file, includes `TestEquivalenceFixtures` and
  `TestAllShardsCoverage`. Contains one test needing a partial rewrite
  (`test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`, lines 1029-1063 —
  only the `legacy_mapping` half, not the `legacy_hits` half, see New Tests Required). All other
  tests, including `test_impact_and_entry_cover_all_nine_shards_including_faction` and every
  `_pi.*` (SQLite index) test, must keep passing unmodified — this ticket does not touch
  `tools/parity_index.py`.
- `tests/tools/test_parity_index_baseline.py` — full file. Contains three tests needing rewrite
  (see New Tests Required): `test_manifest_records_legacy_eight_shard_faction_gap` (found during
  investigation, not individually named in the ticket's Scope bullets, but in a file the ticket
  does name), `test_faction_fixture_matches_live_legacy_scan_output`,
  `test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture`. All other
  tests (manifest determinism/coverage, source-hash, entry-count-drift, no-mutation guard,
  missing-`test_path` count, unmapped/multi-shard/malformed-yaml fixture tests, V1 decision-doc
  completeness, anti-scope-creep guards) must keep passing unmodified.
- `tests/tools/test_gate_a_readpath_review.py` — full file. Investigation found no assertion that
  literally breaks from this fix (see investigation.md Risks and Open Questions — the
  `FACTION_EXCLUSION` adjudication text becomes stale prose but every downstream assertion
  compares against the SQLite index's `impact()` output, which is already `faction.yaml`-inclusive
  and unaffected by `CANONICAL_LEDGER_FILES`). Run this file as-is; if it fails, that is signal the
  investigation's trace was wrong somewhere and needs re-checking before proceeding, not something
  to route around.

Architecture/schema guard (indirect — confirms `faction.yaml`'s conformance is not disturbed):
- No test currently validates `faction.yaml` against `schema.json` directly by name (checked); any
  generic parity-ledger schema validator test in the repo (if one exists outside this ticket's
  named files) is out of this ticket's declared file set and not expected to change, since no
  ledger content changes.

## New Tests Required

1. **Rewrite: `test_parity_ledger_scan.py::test_only_scans_canonical_eight_not_faction`**
   - Category: unit
   - Verifies: `"faction.yaml" in CANONICAL_LEDGER_FILES` and that a synthetic `faction.yaml` P0
     fixture IS now picked up by `find_p0_intersection` (invert the current `hits == []` /
     `"faction.yaml" not in CANONICAL_LEDGER_FILES` assertions to `hits == [("faction.yaml",
     "FAC-001", ...)]` / `"faction.yaml" in CANONICAL_LEDGER_FILES`). Rename if the old name no
     longer describes the behavior (e.g. `test_scans_canonical_nine_including_faction`).
   - Location: `tests/tools/test_parity_ledger_scan.py`

2. **New: real-`FAC-013` P0 intersection test (ticket AC #2)**
   - Category: unit (exercises the real ledger, not just a synthetic fixture)
   - Verifies: `find_p0_intersection(["src/observability/event_extractor.py"],
     ledger_dir="docs/parity_ledger")` returns a hit including `("faction.yaml", "FAC-013",
     "src/observability/event_extractor.py")` — proving the real, live P0 gap this ticket exists
     to close is actually closed, not just a synthetic-fixture claim.
   - Location: `tests/tools/test_parity_ledger_scan.py` (mirrors the existing
     `test_no_intersection_for_representative_docs_only_change`'s "negative control against the
     real 8/9-file ledger" pattern, but as a positive control)

3. **Rewrite: `test_parity_updater_static.py::test_excludes_faction_yaml`**
   - Category: unit
   - Verifies: inverse of current behavior — `derive_mapping` run against a synthetic
     `faction.yaml` fixture now DOES include the cited `src/` path in its mapping, keyed to
     `{"faction.yaml"}`. Rename to reflect inclusion (e.g. `test_includes_faction_yaml`).
   - Location: `tests/tools/test_parity_updater_static.py`

4. **New: `expected_subsystems_for_files` includes `faction.yaml` as a candidate (ticket AC #3)**
   - Category: unit
   - Verifies: for a real `src/` path cited only in `faction.yaml`'s `v2_evidence` (e.g.
     `src/observability/event_extractor.py`, from `FAC-013`), `expected_subsystems_for_files(["src/observability/event_extractor.py"])`
     against the real `docs/parity_ledger` no longer returns `None` and includes `"faction.yaml"`
     in the candidate list.
   - Location: `tests/tools/test_parity_updater_static.py`

5. **Rewrite: `test_parity_index_baseline.py::test_manifest_records_legacy_eight_shard_faction_gap`**
   - Category: unit
   - Verifies: `manifest["excluded_from_legacy_scan"] == []` (was `== ["faction.yaml"]`). Rename to
     reflect the closed gap (e.g. `test_manifest_records_no_legacy_shard_gap`).
   - Location: `tests/tools/test_parity_index_baseline.py`

6. **Rewrite: `test_parity_index_baseline.py::test_faction_fixture_matches_live_legacy_scan_output`**
   - Category: unit
   - Verifies: the `faction_case` fixture (`tests/tools/fixtures/parity_index_baseline/faction_case/faction.yaml`,
     a P0 entry) now DOES produce a hit via `find_p0_intersection` — invert `hits == []` to the
     real expected hit tuple.
   - Location: `tests/tools/test_parity_index_baseline.py`

7. **Rewrite: `test_parity_index_baseline.py::test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture`**
   - Category: unit
   - Verifies: both halves flip — `"faction.yaml" in CANONICAL_LEDGER_FILES` (was `not in`) and the
     fixture-based `find_p0_intersection` call now returns the real hit (was `== []`). Rename to
     drop "but_excluded" from the name since it's no longer true (e.g.
     `test_faction_yaml_included_in_manifest_shard_list_and_legacy_fixture`).
   - Location: `tests/tools/test_parity_index_baseline.py`

8. **Partial rewrite: `test_parity_index.py::TestEquivalenceFixtures::test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`**
   - Category: unit
   - Verifies: keep the "new index" half unchanged (still proves `impact()`/`entry()` see
     `faction.yaml` — that side is untouched by this ticket). Update the "legacy exclusion" half:
     `legacy_mapping` (via `derive_mapping`) now DOES contain `"src/factions/diplomacy.py"` (mapped
     to `{"faction.yaml"}`) — invert that assertion. Leave the `legacy_hits ==
     []`/`find_p0_intersection` assertion as-is (it stays `[]`, but now because the fixture entry's
     priority is `P1` not because `faction.yaml` is unscanned — update the inline comment to say
     so, don't just leave the stale "Legacy exclusion: both comparison targets never see
     faction.yaml at all" comment in place since it becomes half-false). Consider renaming the test
     (e.g. `test_faction_evidence_case_present_in_both_legacy_and_new_index`) since "despite_legacy_exclusion"
     no longer describes reality for the `derive_mapping` half.
   - Location: `tests/tools/test_parity_index.py`

9. **New: `implement-ticket.js` Parity-phase prompt lists `faction.yaml` (ticket AC #4)**
   - Category: architecture guard / static-text check
   - Verifies: a simple string-containment check (e.g. grep-in-test or a small Node/Python
     assertion reading the file) that the Parity-phase prompt string at the location around line
     1264 lists `faction.yaml` among the 9 files. If no existing test file covers
     `implement-ticket.js` prose content, add a minimal one, or fold this into whatever test suite
     already asserts against this workflow file's static content (check for one before creating a
     new file — none was found scoped to this specific string during investigation, but a broader
     `implement-ticket.js` static-content test suite may exist elsewhere in `tests/tools/` and
     should be checked at Plan time rather than assumed absent).
   - Location: an existing `tests/tools/test_*implement_ticket*` file if one exists, else a new
     narrowly-scoped test file.

## Scoped Pytest Commands

Primary regression command (matches the ticket's own AC #6, includes the file investigation
confirmed is unaffected but should still run as a safety net):

```
pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py tests/tools/test_gate_a_readpath_review.py -v
```

Fast iteration subset while rewriting the two tests investigation found outside the ticket's named
files:

```
pytest tests/tools/test_parity_updater_static.py -v
```

Never: `pytest tests/` — this ticket's blast radius is fully contained within `tests/tools/`.

## Anti-Drift Test Guards

- `tests/tools/test_parity_index.py::TestAllShardsCoverage::test_impact_and_entry_cover_all_nine_shards_including_faction`
  must keep passing byte-for-byte unmodified — it is the existing proof that the SQLite-index side
  was already correct before this ticket, and must remain correct after (regression guard against
  accidentally touching `tools/parity_index.py`, which is explicitly Out of Scope).
- `tests/tools/test_parity_updater_static.py::test_reuses_canonical_ledger_files_constant` (identity
  check `CANONICAL_LEDGER_FILES is SCAN_CANONICAL_LEDGER_FILES`) must keep passing — guards against
  a drift where someone "fixes" the gap by defining a second, parallel 9-file tuple in
  `parity_updater_static.py` instead of appending to the single shared source of truth in
  `parity_ledger_scan.py`.
- A guard that `find_p0_intersection` still returns `[]` for a non-P0 `faction.yaml` entry (use any
  of `FAC-001`–`FAC-012`/`FAC-014`/`FACTION-TENSION-001`, all P1/P2) even after the tuple fix —
  proves the P0-only filter still works correctly for the newly-included shard, not just that the
  shard is scanned at all.
- A guard on `derive_mapping`'s existing multi-shard ANY-of semantics: confirm no `src/` path
  currently cited in both `faction.yaml` and one of the original 8 shards silently collapses to a
  single value once `faction.yaml` is added (the module's own docstring guarantees this — "must
  never collapse to a single value" — but this specific new-shard-added case has no direct
  regression test today; worth adding one with two shards including `faction.yaml` sharing a
  citation, mirroring `test_derive_mapping_handles_multi_subsystem_file`'s existing shape).
- `tests/tools/test_gate_a_readpath_review.py::TestMetrics::test_gate_a_decision_reports_all_four_named_metrics`
  (asserts `analyst_effort_proxy["shards_scanned_legacy"] == 8`) must keep passing unmodified as a
  literal value — if Plan decides to touch this file's hardcoded `8` literals (see
  investigation.md's open question), this specific assertion's expected value must be updated in
  lockstep with the literal it checks, never left silently mismatched.
