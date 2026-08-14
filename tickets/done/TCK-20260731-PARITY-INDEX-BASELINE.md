---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-BASELINE
phase: done
date: 2026-07-31
tags: [ai, documentation, process-improvement, testing]
---

# TCK-20260731-PARITY-INDEX-BASELINE

## Title
Capture the parity-ledger baseline and decide v1 index boundaries

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Before implementing an index, create reproducible evidence for the current ledger and legacy tools, then make the v1 architecture decisions that later tickets must follow. The legacy tools hard-code eight shards and exclude `faction.yaml`; the baseline must expose rather than erase that distinction.

## Scope
- Produce a deterministic, versioned baseline manifest from dynamically enumerated `docs/parity_ledger/*.yaml`, including sorted files/content hashes, entries/IDs, status/priority counts, parser/schema coverage, and source/test-reference parse coverage.
- Capture fixed changed-path fixtures and exact outputs of `parity_ledger_scan.py` and `parity_updater_static.py`, including faction exclusion and malformed/unmapped/multi-shard behavior.
- Record v1 decisions for ownership, discovery/IDs, normalized schema, FTS fallback, atomic lifecycle, path-only links, output convention, and CLI/module ownership; `parity-record` stays deferred.

## Out of Scope
- Creating an index/database or changing `.gitignore`/Make targets.
- Changing YAML fields, legacy tools, context assembly, workflows, FTS/query commands, or a mutation CLI.

## Acceptance Criteria
- [x] Unchanged source inputs yield byte-identical baseline output and all nine shards are represented; source hashes are unchanged.
- [x] Manifest records the historical 1,936-entry snapshot and the legacy eight-shard/faction comparison gap.
- [x] Fixture inputs and expected legacy outputs are versioned for faction, unmapped, and multi-shard cases.
- [x] A v1 decision artifact resolves each Scope boundary including CLI ownership and FTS-independent fallback.
- [x] No DB, workflow/config/context integration, source rewrite, or mutation command is introduced.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC
- TCK-20260731-PARITY-INDEX-IMPORTER
- TCK-20260705-GATE-DET-PARITY-UPDATER

## Related Docs
- docs/parity_ledger/schema.json
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/

## Related Code Areas
- docs/parity_ledger/
- tools/parity_ledger_scan.py
- tools/gate_checks/parity_updater_static.py
- tests/tools/test_parity_ledger_scan.py
- tests/tools/test_parity_updater_static.py

## Assumptions / Open Questions
- Historic schema-field gaps are classified for health/reporting later; this ticket must not coerce source status or repair source data.

## Implementation Notes
The legacy tools are compatibility fixtures only. They are not the desired all-shard v1 behavior.

Implemented per `staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/plan.md`'s 6 steps exactly,
no deviations:

1. **`tools/parity_index_baseline.py`** — new flat module (no new package, per the CLI/module
   ownership decision in Step 4). `build_manifest(ledger_dir)` dynamically globs all 9
   `docs/parity_ledger/*.yaml` shards (`sorted(Path(ledger_dir).glob("*.yaml"))`), computes a
   per-shard SHA-256, entry count, ID list, and status/priority tallies, then rolls up
   corpus-level totals: `entry_count_current` (1,945 live), `entry_count_historical_reference`
   (1936, from the idea doc), an explicit `drift` object, `duplicate_ids` (0, observed fact not
   enforced invariant), `excluded_from_legacy_scan` (`["faction.yaml"]`, derived by diffing the
   9-file glob against `CANONICAL_LEDGER_FILES` imported by identity from
   `tools.parity_ledger_scan`, never redefined), `schema_coverage` (describes
   `docs/parity_ledger/schema.json` as it actually parses — only the `divergent`->
   `divergence_note` rule survives the duplicate top-level `"if"` key, confirmed by running
   `json.loads` against the live file), and `missing_evidence_health` (1,347 `verified`/
   `divergent` entries missing `test_path`, counted only, never backfilled).
   `serialize_manifest()` emits `json.dumps(..., sort_keys=True, indent=2, ensure_ascii=True)` +
   trailing newline for byte-identical reruns. `main()` writes only to this ticket's own staging
   directory (`staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/baseline_manifest.json`);
   every `docs/parity_ledger/*.yaml` read uses `Path.read_text()`/`Path.read_bytes()` only, never
   opened in write mode.
2. **`tests/tools/test_parity_index_baseline.py`** — determinism/coverage tests
   (`test_baseline_manifest_is_byte_identical_on_rerun`,
   `test_baseline_manifest_covers_all_nine_shards`,
   `test_baseline_manifest_source_hashes_match_live_files`,
   `test_manifest_records_both_historical_and_current_entry_counts`,
   `test_manifest_records_legacy_eight_shard_faction_gap`) plus two anti-drift guards
   (`test_baseline_script_never_writes_to_docs_parity_ledger` — static source-text scan plus a
   runtime `monkeypatch` on `Path.write_text`/`write_bytes` proving `build_manifest()` never
   writes anywhere; `test_baseline_manifest_does_not_coerce_missing_test_path`).
3. **`tests/tools/fixtures/parity_index_baseline/{faction_case,unmapped_case,multi_shard_case,
   malformed_yaml_case}/`** — small synthetic YAML shards (not copies of the live ledger) plus
   4 fixture-comparison tests calling the legacy functions (`find_p0_intersection`,
   `expected_subsystems_for_files`, `derive_mapping`) exactly as they exist today, and
   `test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture` proving
   both halves of the central tension (9-shard manifest coverage vs. 8-shard legacy exclusion)
   simultaneously.
4. **`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md`** —
   new companion doc (idea doc itself untouched) with one section per required heading:
   Ownership, Discovery / IDs, Normalized schema, FTS fallback, Atomic lifecycle, Path-only
   links, Output convention, CLI/module ownership (decided: flat `tools/parity_index.py` /
   deferred `tools/parity_record.py`, no new package), `parity-record` deferral, and Known gaps
   (the `schema.json` duplicate-`if` defect; the missing
   `..._review_claude.md` companion doc, confirmed absent from the repo and `git log --all`).
   Also declares cross-shard ID uniqueness a v1 enforced invariant for Phase 1/IMPORTER (today's
   0-duplicate observed fact is not itself the invariant declaration).
5. **`test_v1_decision_artifact_covers_all_scope_boundaries`** — scripted heading-presence check
   against the Step 4 doc, appended to the same test file.
6. **Anti-scope-creep guards** — `test_no_database_or_gitignore_or_make_target_created` (no
   `.db`/`.sqlite` under this ticket's staging dir, no new `.gitignore`/`Makefile` entries) and
   `test_v1_decision_artifact_does_not_authorize_mutation_cli` (asserts "stays deferred" is
   present, no `parity-record validate/propose/apply` CLI spec, no code fences at all in the
   decision doc).

Verification run: `pytest tests/tools/test_parity_index_baseline.py -v` (15/15 passed);
`pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v`
(13/13 passed, unmodified — confirmed via `git status --porcelain` showing zero diff on
`tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`,
`docs/parity_ledger/*.yaml`, `docs/parity_ledger/schema.json`, `.gitignore`, `Makefile`).
`python3 tools/validate_frontmatter.py` passed on the ticket, all 3 staging artifacts, and the
new decision doc.

## Test Summary
15/15 new tests passing (`tests/tools/test_parity_index_baseline.py`). 13/13 pre-existing legacy
tests unchanged and green (`tests/tools/test_parity_ledger_scan.py`,
`tests/tools/test_parity_updater_static.py`). No `src/` behavior touched, so no simulation
regression surface applies.

## Files Changed
- `tools/parity_index_baseline.py` (new)
- `tests/tools/test_parity_index_baseline.py` (new)
- `tests/tools/fixtures/parity_index_baseline/faction_case/faction.yaml` (new)
- `tests/tools/fixtures/parity_index_baseline/unmapped_case/combat_movement.yaml` (new)
- `tests/tools/fixtures/parity_index_baseline/multi_shard_case/combat_movement.yaml` (new)
- `tests/tools/fixtures/parity_index_baseline/multi_shard_case/strategic_cognition.yaml` (new)
- `tests/tools/fixtures/parity_index_baseline/malformed_yaml_case/combat_movement.yaml` (new)
- `tests/tools/fixtures/parity_index_baseline/malformed_yaml_case/town_resource.yaml` (new)
- `docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md` (new)
- `staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/baseline_manifest.json` (new, generated
  evidence artifact — migrates to `stored_artifacts/` at ticket close)

## Completion Summary
Delivered all three Phase-0 artifact types with zero deviation from plan.md: (1) a deterministic
baseline-manifest generator (`tools/parity_index_baseline.py`) that dynamically enumerates all 9
`docs/parity_ledger/*.yaml` shards and reproduces byte-identical JSON snapshots recording source
hashes, the live 1,945-entry count alongside the idea doc's dated 1,936 historical figure with
explicit drift, the legacy 8-shard/faction exclusion gap, the `schema.json` duplicate-`"if"`-key
parsing defect as an observed fact, and the 1,347-entry missing-`test_path` health count (never
coerced/backfilled); (2) versioned synthetic fixture captures reproducing
`parity_ledger_scan.find_p0_intersection` and `parity_updater_static.derive_mapping`/
`expected_subsystems_for_files`'s exact legacy behavior for faction, unmapped, multi-shard, and
malformed-YAML cases; (3) a v1 decision record
(`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md`) resolving
every open Scope boundary — ownership, discovery/IDs (declaring cross-shard ID uniqueness an
enforced invariant), normalized schema, FTS fallback, atomic lifecycle, path-only links, output
convention, and CLI/module ownership (flat `tools/parity_index.py`, no new package) — while
explicitly keeping `parity-record` deferred and recording known gaps. No database, index,
`.gitignore`/Makefile change, or mutation CLI was created; all read-only/do-not-touch boundaries
(`docs/parity_ledger/*.yaml`, `schema.json`, the two legacy tool modules, their existing 13
tests) were verified untouched via `git status --porcelain`. 15 new tests plus the 13 pre-existing
legacy tests all pass (28/28 total in this ticket's regression surface).
