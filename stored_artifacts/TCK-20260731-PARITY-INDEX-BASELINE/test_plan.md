---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-BASELINE
artifact_type: test_plan
tags: [ai, documentation, process-improvement, testing]
---

# Test Plan — TCK-20260731-PARITY-INDEX-BASELINE

## Regression Surface

This ticket touches no `src/` code and does not modify `tools/parity_ledger_scan.py` or
`tools/gate_checks/parity_updater_static.py` (Out of Scope). The regression surface is therefore purely
"prove the existing legacy tools' behavior is unchanged by this ticket's work" — no simulation-domain
regression applies.

**Unit (must stay green, unmodified):**
- `tests/tools/test_parity_ledger_scan.py` — 3 tests (`test_detects_p0_intersection_via_synthetic_fixture`,
  `test_no_intersection_for_representative_docs_only_change`, `test_only_scans_canonical_eight_not_faction`).
  Confirmed passing (3/3) before any Phase-0 artifact work in this investigation.
- `tests/tools/test_parity_updater_static.py` — 10 tests covering `derive_mapping`,
  `expected_subsystems_for_files`, `cross_reference_touched`. Confirmed passing (10/10).
- Combined: `13/13 passed` (measured directly, `pytest tests/tools/test_parity_ledger_scan.py
  tests/tools/test_parity_updater_static.py -q`).

**Frontmatter/validation (must stay green — this ticket's own artifacts must pass it):**
- `tools/validate_frontmatter.py` — validates `artifact_type` against `ARTIFACT_TYPE_VALUES =
  {"investigation", "plan", "test_plan"}` (line 57) and required frontmatter fields (line 216). This
  ticket's `investigation.md`/`test_plan.md`/eventual `plan.md` must pass it.

**No integration or arena-combat tests apply** — this ticket has no simulation-domain surface.

## New Tests Required

Per this ticket's Acceptance Criteria, the "tests" this Phase-0 ticket delivers are the **versioned
fixture/manifest scripts and their own self-verifying tests**, not simulation regression tests. Each
maps to a specific AC:

1. **Test name:** `test_baseline_manifest_is_byte_identical_on_rerun` (or equivalent, exact name is a
   Plan-phase decision)
   **Category:** unit / determinism guard
   **Verifies:** AC #1 — running the baseline-manifest script twice against unchanged
   `docs/parity_ledger/*.yaml` produces byte-identical output (or row/field-identical if the manifest is
   JSON/YAML with non-deterministic key ordering risk — Plan must pick a canonical serialization, e.g.
   `sort_keys=True`).
   **Where:** new test file, e.g. `tests/tools/test_parity_index_baseline.py` (exact path is a
   Plan-phase/CLI-ownership-dependent decision — see investigation.md Risk #4).

2. **Test name:** `test_baseline_manifest_covers_all_nine_shards`
   **Category:** unit
   **Verifies:** AC #1 — "all nine shards are represented" (including `faction.yaml`, which the legacy
   8-file tools exclude — this baseline manifest must NOT inherit that exclusion for its own shard
   enumeration, even though the legacy-tool fixture captures do preserve it as a documented gap).
   **Where:** same new test file as above.

3. **Test name:** `test_baseline_manifest_source_hashes_match_live_files`
   **Category:** unit
   **Verifies:** AC #1 — "source hashes are unchanged"; the manifest's recorded per-shard SHA-256 hashes
   equal a freshly computed hash of the live file at generation time (guards against a stale/hand-edited
   manifest silently diverging from the actual YAML).
   **Where:** same new test file.

4. **Test name:** `test_manifest_records_both_historical_and_current_entry_counts`
   **Category:** unit
   **Verifies:** AC #2 — the manifest explicitly records the current live count (1,945, confirmed by this
   investigation) alongside the idea-doc's historical 1,936 figure and the drift, rather than overwriting
   or silently reproducing either number. Directly guards against the interpretive risk flagged in
   investigation.md Risk #1.
   **Where:** same new test file.

5. **Test name:** `test_manifest_records_legacy_eight_shard_faction_gap`
   **Category:** unit
   **Verifies:** AC #2 — "the legacy eight-shard/faction comparison gap" is explicitly recorded (not just
   implicitly true because `CANONICAL_LEDGER_FILES` has 8 entries) — e.g. an explicit
   `excluded_from_legacy_scan: ["faction.yaml"]` field or equivalent in the manifest.
   **Where:** same new test file.

6. **Test name:** `test_faction_fixture_matches_live_legacy_scan_output`
   **Category:** unit / fixture-capture guard
   **Verifies:** AC #3 — a versioned fixture exists capturing `find_p0_intersection`'s exact output when
   given a changed-path that touches a `faction.yaml`-only `v2_evidence` citation (must return `[]`,
   matching `test_only_scans_canonical_eight_not_faction`'s existing behavior) — this ticket's captured
   fixture must reproduce that exact empty-list result, proving the fixture capture itself is faithful to
   the legacy tool's real behavior, not a guessed value.
   **Where:** `tests/tools/test_parity_index_baseline.py` (or fixtures directory alongside it, e.g.
   `tests/tools/fixtures/parity_index_baseline/`).

7. **Test name:** `test_unmapped_path_fixture_matches_live_legacy_scan_output`
   **Category:** unit / fixture-capture guard
   **Verifies:** AC #3 — "unmapped" case: a changed-path with no `v2_evidence` citation anywhere returns
   `NA`/`None` from `expected_subsystems_for_files`, and the captured fixture matches that.
   **Where:** same new test file/fixtures location.

8. **Test name:** `test_multi_shard_fixture_matches_live_legacy_scan_output`
   **Category:** unit / fixture-capture guard
   **Verifies:** AC #3 — "multi-shard" case: a real or synthetic path cited in 2+ canonical files (e.g.
   one of the ~16%-overlap paths identified in prior investigation, such as `src/engine/apply.py`)
   returns the full multi-file candidate set from `derive_mapping`/`expected_subsystems_for_files`, and
   the captured fixture matches.
   **Where:** same new test file/fixtures location.

9. **Test name:** `test_malformed_yaml_fixture_matches_live_legacy_scan_output`
   **Category:** unit / fixture-capture guard
   **Verifies:** AC #3 — "malformed" case: `derive_mapping`'s `try/except Exception: continue` tolerance
   (parity_updater_static.py line 53-56) is captured with a fixture proving the legacy tool skips a
   malformed shard rather than raising — matching `test_derive_mapping_skips_malformed_yaml_file`'s
   existing behavior in `test_parity_updater_static.py`.
   **Where:** same new test file/fixtures location.

10. **Test name:** `test_v1_decision_artifact_covers_all_scope_boundaries`
    **Category:** architecture guard (documentation-completeness, not code-behavior)
    **Verifies:** AC #4 — a structural check (e.g. a simple presence/section-heading check, not a
    behavioral test) that the v1-decision artifact this ticket produces explicitly addresses every named
    Scope boundary: ownership, discovery/IDs, normalized schema, FTS fallback, atomic lifecycle,
    path-only links, output convention, CLI/module ownership. This is closer to a doc-completeness lint
    than a pytest unit test — Plan should decide whether this is a pytest test at all or a manual Verify
    checklist item; recommend the former for determinism, following the `done_checker_static.py`
    precedent of scripted-not-prose verification wherever a check can be made objective.
    **Where:** same new test file, or `tools/gate_checks/` if Plan decides this warrants a determinism
    gate.

11. **Test name:** `test_no_database_or_gitignore_or_make_target_created`
    **Category:** architecture guard / anti-scope-creep
    **Verifies:** AC #5 — "No DB, workflow/config/context integration, source rewrite, or mutation
    command is introduced." A structural test asserting no `.db`/`.sqlite` file exists under any path
    this ticket's script writes to, `.gitignore` has no new `parity-index/`-style entry yet, and the
    `Makefile` has no new parity-index target yet (mirrors `TCK-20260713-MONITORING-SQLITE-INDEX`'s own
    `test_agent_monitoring_index_not_in_test_ci_all_targets`-style negative-assertion pattern, but
    inverted — proving absence here, not restricted wiring).
    **Where:** same new test file.

## Scoped Pytest Commands

```
pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v
```
Regression confirmation — legacy tools' existing behavior stays exactly as documented (13 tests).

```
pytest tests/tools/test_parity_index_baseline.py -v
```
(or whatever exact filename Plan settles on) — the new Phase-0 baseline/fixture/decision tests above.

```
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/investigation.md staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/test_plan.md staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/plan.md
```
Frontmatter validity for this ticket's own staging artifacts — required for `done-checker`'s
`frontmatter_valid` condition.

**Never:** `pytest tests/` (repo-wide) — this ticket's regression surface is narrowly `tests/tools/`
only; no `src/` or simulation-domain test directory is affected.

## Anti-Drift Test Guards

- **`test_reuses_canonical_ledger_files_constant`** (existing, `test_parity_updater_static.py:98-101`) —
  already guards that `parity_updater_static.CANONICAL_LEDGER_FILES` and `parity_ledger_scan.CANONICAL_LEDGER_FILES`
  stay the same object (`is`, not `==`). This ticket's fixture-capture work must not accidentally trigger
  a refactor that breaks this identity — any new baseline script should *import*, never *redefine*, this
  constant if it needs the 8-file list for comparison purposes.
- **New guard: `test_baseline_script_never_writes_to_docs_parity_ledger`** — asserts the baseline-manifest
  generation script opens every `docs/parity_ledger/*.yaml` file read-only and never calls `write_text`/
  `open(..., "w")` on any path under `docs/parity_ledger/`. Mirrors `TCK-20260713-MONITORING-SQLITE-INDEX`'s
  `test_build_index_never_touches_write_path_modules` anti-drift pattern (source-safety proof by static
  inspection, not just by observed byte-identity after one run).
- **New guard: `test_baseline_manifest_does_not_coerce_missing_test_path`** — asserts the manifest counts
  and classifies the 1,347 `verified`/`divergent` entries missing `test_path` as a health-gap count, and
  never fabricates a `test_path` value or silently excludes them from the entry count. Directly guards
  the "Do not coerce or repair" Anti-Drift Hazard from investigation.md.
- **New guard: `test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture`** — a
  single test asserting both halves of the ticket's central tension are true simultaneously: the
  baseline manifest's own shard enumeration includes `faction.yaml` (9 shards), while the *legacy-tool
  fixture capture* (item 6-9 above) still reproduces the legacy tools' 8-file exclusion faithfully. A
  regression here (e.g. someone "fixing" the fixture to include faction, changing its expected output)
  would silently misrepresent what the legacy tools currently do — which is exactly the gap this ticket
  exists to expose, not paper over.
- **New guard: `test_v1_decision_artifact_does_not_authorize_mutation_cli`** — a text-presence check on
  the v1-decision artifact ensuring it does not specify a working `parity-record` CLI implementation
  (only records that it "stays deferred," per this ticket's Scope). Guards against scope creep where a
  "decision record" quietly becomes a design spec detailed enough to be mistaken for authorization to
  build Phase 3's mutation tool now.
