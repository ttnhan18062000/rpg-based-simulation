---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-IMPORTER
artifact_type: test_plan
tags: [ai, observability, process-improvement, testing]
---

# Test Plan — TCK-20260731-PARITY-INDEX-IMPORTER

## Regression Surface

This ticket touches no `src/` code and does not modify `tools/parity_ledger_scan.py`,
`tools/gate_checks/parity_updater_static.py`, `tools/parity_index_baseline.py`, or
`tools/agent-monitoring/build_index.py` (Out of Scope: "Do NOT modify the legacy scanner/static gate").

**Unit (must stay green, unmodified):**
- `tests/tools/test_parity_ledger_scan.py` — 3 tests. Confirmed passing (3/3) in this investigation.
- `tests/tools/test_parity_updater_static.py` — 10 tests. Confirmed passing (10/10) in this investigation.
- `tests/tools/test_parity_index_baseline.py` — the Phase-0 baseline/fixture/decision-doc test suite;
  must remain green and untouched (this ticket does not modify the Phase-0 script or its tests).
- Combined regression command confirmed in this investigation:
  `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py
  tests/tools/test_parity_index_baseline.py -q` — all pass as of this investigation.

**Known pre-existing failure, NOT part of this ticket's regression surface and not to be fixed as a
drive-by:**
- `tests/tools/test_build_index.py::TestMakeTarget::test_makefile_dry_run_agent_monitoring_index` fails
  today (`make --dry-run agent-monitoring-index` prints "up to date" instead of a `build_index.py`-
  containing command line — a Makefile phony-target/timestamp quirk unrelated to this ticket's Scope).
  All other 44 tests in `tests/tools/test_build_index.py` pass. If the implementer's scoped regression run
  includes this file (e.g. because a reviewer asks for the full `tools/agent-monitoring/` + parity
  comparison), this single pre-existing failure must be reported as pre-existing, not attributed to this
  ticket's changes, and must not be "fixed" — `Makefile`/`build_index.py` are outside Related Code Areas.

**Frontmatter validation (must stay green):**
- `tools/validate_frontmatter.py` against this ticket's own staging artifacts
  (`investigation.md`, `test_plan.md`, and the eventual `plan.md`).

**No integration or arena-combat tests apply** — this ticket has no simulation-domain surface (agent-
infrastructure tooling only, per the Phase-0 precedent's own finding, independently reconfirmed here: no
`docs/mechanics/` or `docs/engine/` contract governs parity-ledger tooling).

## New Tests Required

Mapped to this ticket's Acceptance Criteria (5 ACs). Exact test names below are recommendations; Plan may
adjust naming but must preserve one-to-one AC coverage.

**AC #1 — Rebuild imports all nine shards, preserves YAML byte hashes, exposes normalized rows for joins;
no DB is committed to git.**

1. `test_importer_imports_all_nine_shards`
   Category: unit
   Verifies: a build against a `tmp_path`-isolated synthetic 9-shard corpus (including a `faction.yaml`-
   named fixture) populates `entries` with rows from every shard — never inherits the legacy 8-file
   exclusion.
   Where: `tests/tools/test_parity_index.py`

2. `test_importer_preserves_source_byte_hashes`
   Category: unit / source-safety guard
   Verifies: source YAML fixture files are byte-identical before and after a build (hash before/after
   comparison, mirroring `test_build_index.py`'s `test_source_jsonl_files_byte_identical_after_build`
   pattern) and that `ledger_generation`'s recorded per-shard hash matches an independently recomputed
   SHA-256 of each fixture file.
   Where: `tests/tools/test_parity_index.py`

3. `test_entries_table_supports_join_to_code_test_constraint_ticket_refs`
   Category: unit / schema-shape guard
   Verifies: for a fixture entry with a `code_refs`/`test_refs`/`constraint_refs`/`ticket_refs`-eligible
   structured field, the built DB's `entries.id` join against the corresponding ref table returns the
   expected row — proves the schema is actually query-joinable, not merely present.
   Where: `tests/tools/test_parity_index.py`

4. `test_db_not_tracked_by_git`
   Category: architecture guard
   Verifies: the importer's default output path (`parity-index/parity.db` or the Plan-selected equivalent)
   is covered by a `.gitignore` entry added by this ticket, and `git check-ignore -v <path>` (mirroring
   `test_build_index.py`'s `TestGitignore.test_git_check_ignore`) exits 0 for it.
   Where: `tests/tools/test_parity_index.py`

**AC #2 — Identical inputs give the same logical generation and ordered tables/health findings; duplicate
IDs, malformed sources, unparseable references, missing local refs/tests, and legacy-unstructured evidence
are deterministic classified findings, never invented links.**

5. `test_build_is_deterministic_on_unchanged_source`
   Category: unit / determinism guard
   Verifies: two builds against the same unchanged fixture corpus produce identical row counts, identical
   `entries`/health-finding ordering (filename then stable entry ID, per Scope), and identical
   `ledger_generation.source_manifest_hash`.
   Where: `tests/tools/test_parity_index.py`

6. `test_duplicate_cross_shard_id_rejected_at_import`
   Category: unit / invariant-enforcement guard
   Verifies: a fixture corpus with the same `id` appearing in two different shard files causes the build to
   reject (not silently tolerate) the duplicate — directly enforces the v1 decision doc's "Discovery / IDs"
   decision that cross-shard ID uniqueness is a v1 enforced invariant, not an observed fact. Must assert
   both (a) the rejection is surfaced deterministically (a specific error/classification, not a crash with
   an unrelated traceback) and (b) — per AC #4's atomic-lifecycle requirement — that a prior-good DB (if
   one existed) is left byte-identical (see test 14 below for the fuller atomic-lifecycle proof; this test
   asserts the trigger condition specifically for duplicate IDs).
   Where: `tests/tools/test_parity_index.py`

7. `test_malformed_yaml_shard_produces_classified_finding_not_crash`
   Category: unit
   Verifies: a fixture shard with invalid YAML syntax produces a deterministic health/build-report finding
   (e.g. `malformed_source` classification) rather than an unhandled exception — mirrors
   `parity_updater_static.py`'s `derive_mapping`'s `try/except Exception: continue` tolerance, but for the
   importer's own classified-finding vocabulary (not silent skip — Scope requires "deterministic classified
   findings," which is stricter than the legacy tool's silent skip).
   Where: `tests/tools/test_parity_index.py`

8. `test_unparseable_code_ref_never_invents_a_link`
   Category: unit / anti-invention guard
   Verifies: a fixture entry whose `v2_evidence` text contains a path-like substring that cannot be parsed
   with high confidence (per the idea doc's "Structured reference evolution" section) is classified
   `legacy_unstructured`, and no `code_refs` row is fabricated for it.
   Where: `tests/tools/test_parity_index.py`

9. `test_missing_test_path_produces_entry_health_finding`
   Category: unit
   Verifies: a fixture `verified`/`divergent` entry missing `test_path` produces an `entry_health` row
   classifying the gap (mirrors `parity_index_baseline.py`'s `_missing_evidence_health` scope, but at
   per-entry row granularity) — never fabricates a `test_path` value.
   Where: `tests/tools/test_parity_index.py`

**AC #3 — FTS5-present and forced-unavailable tests both pass; unavailable FTS reports disabled discovery
while exact ID/path operations remain correct.**

10. `test_fts5_present_populates_entry_fts_table`
    Category: unit
    Verifies: against this environment's real `sqlite3` (confirmed FTS5-compiled in this investigation —
    `FTS5 OK`), a build populates the `entry_fts` virtual table and a query against it returns expected
    fixture rows.
    Where: `tests/tools/test_parity_index.py`

11. `test_fts5_forced_unavailable_falls_back_to_exact_lookup`
    Category: unit / fallback guard
    Verifies: with the FTS5-availability probe forced to report unavailable (via the injectable seam Plan
    must design — see investigation.md Risk #3; this environment cannot exercise this branch by relying on
    genuine FTS5 absence), the build completes successfully, reports FTS discovery as disabled in the
    build-report, and exact ID/path lookups (`entries` table queries, not `entry_fts`) still return correct
    results for the same fixture corpus.
    Where: `tests/tools/test_parity_index.py`

**AC #4 — An injected parse/validation/replacement failure leaves a prior good DB byte-identical and no
usable partial DB; failed input never changes YAML.**

12. `test_failed_build_preserves_prior_good_db_byte_identical`
    Category: unit / atomic-lifecycle guard
    Verifies: build a valid DB once (capture its bytes/hash), then inject a build-time failure (e.g. a
    malformed-beyond-recovery fixture, an integrity-check failure, or a duplicate-ID trigger) on a second
    build attempt against the same target path; assert the target DB file's bytes are unchanged
    (byte-identical to the pre-failure capture) and that no `.tmp`/partial database file is left behind in
    the target directory.
    Where: `tests/tools/test_parity_index.py`

13. `test_failed_build_never_writes_to_source_yaml`
    Category: unit / source-safety guard
    Verifies: source fixture YAML files are byte-identical before and after a deliberately-failing build
    attempt — an injected failure must never cascade into a source write.
    Where: `tests/tools/test_parity_index.py`

14. `test_build_uses_sibling_temp_file_then_atomic_replace`
    Category: architecture guard
    Verifies: during a successful build, a sibling temporary file is created in the same directory as the
    final DB path (same-filesystem requirement for atomic `os.replace`), and the final DB path only
    receives content via a rename/replace operation, never via in-place `sqlite3.connect(final_path)` +
    incremental writes to the live target file (mirrors the v1 decision doc's explicit rejection of
    `build_index.py`'s `if db_path.exists(): db_path.unlink()` pattern — assert that literal pattern is
    absent from `tools/parity_index.py`'s source, same static-inspection idiom as
    `test_build_index.py::test_build_index_never_touches_write_path_modules`).
    Where: `tests/tools/test_parity_index.py`

**AC #5 — The old eight-shard legacy functions and their tests retain their behavior unchanged.**

15. `test_legacy_eight_shard_tests_unmodified_and_green`
    Category: regression / anti-drift guard
    Verifies: `tests/tools/test_parity_ledger_scan.py` and `tests/tools/test_parity_updater_static.py`
    (13 tests total) pass unmodified after this ticket's implementation — run as a subprocess or via
    pytest's own test collection from within this ticket's own test module, asserting the combined exit
    code is 0. (This may be satisfied by the Scoped Pytest Commands below rather than a literal test-in-a-
    test; Plan should decide whether a wrapper test is warranted or whether the scoped command itself is
    sufficient evidence — recommend the latter, consistent with the Phase-0 precedent's own choice not to
    write a meta-test for this.)
    Where: N/A if satisfied by the scoped command; otherwise `tests/tools/test_parity_index.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_parity_index.py -v
```
The new importer's own test suite — all 14 (or Plan-adjusted count) new tests above.

```
pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v
```
Regression confirmation — legacy 8-file tools' behavior stays exactly as documented (13 tests, confirmed
13/13 passing in this investigation before implementation).

```
pytest tests/tools/test_parity_index_baseline.py -v
```
Regression confirmation — Phase-0's baseline/fixture/decision-doc suite stays green and untouched.

```
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260731-PARITY-INDEX-IMPORTER/investigation.md staging_artifacts/TCK-20260731-PARITY-INDEX-IMPORTER/test_plan.md staging_artifacts/TCK-20260731-PARITY-INDEX-IMPORTER/plan.md
```
Frontmatter validity for this ticket's own staging artifacts — required for `done-checker`'s
`frontmatter_valid` condition.

```
python3 -c "import sqlite3; c=sqlite3.connect(':memory:'); c.execute('CREATE VIRTUAL TABLE t USING fts5(x)'); print('FTS5 OK')"
```
Environment FTS5-availability sanity check — re-run at implementation time in case the CI/build environment
differs from this investigation's environment (confirmed `FTS5 OK` here, but the forced-unavailable test
path must not assume this holds everywhere).

**Never:** `pytest tests/` (repo-wide) — this ticket's regression surface is narrowly `tests/tools/` only;
no `src/` or simulation-domain test directory is affected.

**Do NOT include `tests/tools/test_build_index.py` in the required-green regression set** — it has one
pre-existing, unrelated failure (`test_makefile_dry_run_agent_monitoring_index`, see Regression Surface
above) that this ticket must not be blamed for or attempt to fix.

## Anti-Drift Test Guards

- **`test_legacy_eight_shard_tests_unmodified_and_green`** (item 15 above) — the direct guard that this
  ticket's importer work does not accidentally trigger a refactor of `CANONICAL_LEDGER_FILES` or either
  legacy module. Any new importer code that needs shard-list comparison (e.g. to log "N more shards
  imported than the legacy scanner covers") must *import*, never redefine, `CANONICAL_LEDGER_FILES`.
- **`test_build_uses_sibling_temp_file_then_atomic_replace`** (item 14) — static-inspection guard that the
  `build_index.py`-style `if db_path.exists(): db_path.unlink()` anti-pattern (confirmed present in that
  file, line 180-181, by this investigation) never appears in `tools/parity_index.py`'s source. This is the
  single most important anti-drift guard in this test plan, since the ticket's own Implementation Notes and
  the v1 decision doc both call this out by name as the failure mode to avoid.
- **`test_failed_build_never_writes_to_source_yaml`** (item 13) — mirrors
  `test_baseline_script_never_writes_to_docs_parity_ledger`'s pattern from the Phase-0 test suite
  (source-safety proof by direct byte-comparison, not just by absence of an exception).
- **`test_duplicate_cross_shard_id_rejected_at_import`** (item 6) — guards against the importer silently
  "observing" a duplicate ID the way `parity_index_baseline.py`'s manifest does (Phase 0 recorded
  duplicates as an *observed fact*, explicitly not an enforced invariant) — this ticket must not regress to
  that weaker Phase-0 behavior; the v1 decision doc requires *rejection*, a materially stronger contract.
- **`test_fts5_forced_unavailable_falls_back_to_exact_lookup`** (item 11) — guards against an implementation
  that only ever exercises the FTS5-present branch because the CI/dev environment happens to have FTS5
  compiled in (confirmed true here) — without an injectable seam and this test, the fallback path could
  silently rot or never actually work when a future runtime lacks FTS5.
- **New guard recommended for Plan to size: `test_importer_does_not_implement_impact_or_entry_or_health_cli`**
  — a text-presence/absence check on `tools/parity_index.py`'s source or `--help` output confirming no
  `impact`, `search --query`, or working `health` subcommand is implemented beyond what Phase 1's own Scope
  requires (build/import only) — guards against silently absorbing Phase 2's CLI surface
  (`parity-index impact ...` / `parity-index search ...` per the idea doc's Read Path CLI sketch) into this
  ticket ahead of the Phase-2 legacy-equivalence proof gate.
- **New guard recommended for Plan to size: `test_no_mutation_cli_or_write_path_to_docs_parity_ledger`** —
  mirrors the Phase-0 precedent's `test_v1_decision_artifact_does_not_authorize_mutation_cli`, but for
  actual code rather than prose: assert `tools/parity_index.py` contains no `parity-record`-shaped mutation
  entrypoint and no `open(..., "w")`/`write_text` call targeting any path under `docs/parity_ledger/`.
