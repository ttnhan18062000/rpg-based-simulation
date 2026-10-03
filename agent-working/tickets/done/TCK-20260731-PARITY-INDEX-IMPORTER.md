---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-IMPORTER
phase: done
date: 2026-07-31
tags: [ai, observability, process-improvement, testing]
---

# TCK-20260731-PARITY-INDEX-IMPORTER

## Title
Build the deterministic read-only parity-ledger SQLite importer and health index

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Implement the Phase 1 index following the Phase 0 architecture decision. It must load every
canonical YAML shard into a normalized, local SQLite database while preserving source bytes and
classifying—not silently correcting—historic or malformed evidence.

## Scope
- Implement the Phase-0-selected CLI/module shape and a deterministic full rebuild to local,
  Gitignored `parity-index/parity.db` (or the recorded equivalent output location).
- Dynamically import every YAML shard, populate normalized generation, entries, code/test/
  constraint/ticket reference, and ordered health data needed by later exact path-level queries.
- Store manifest/source hashes and importer/schema versions; stable ordering must be filename then
  stable entry ID. FTS5 is optional discovery only: probe it and provide exact ID/path lookup when
  unavailable.
- Build in a sibling temporary DB, validate integrity/schema/rows, close/fsync as appropriate,
  then atomically replace the old DB. A failed build must preserve the last good DB and YAML.
- Add on-demand build/ignore conventions selected in Phase 0 and isolated `tmp_path` tests.

## Out of Scope
- Any source YAML write, `parity-record`, v3 source format, context/retrieval/workflow integration,
  Graphify dependency, sqlite-vec, or `impact`/`entry` query API (Phase 2).
- Modifying the legacy scanner/static gate or treating their eight-shard list as importer input.

## Acceptance Criteria
- [x] A rebuild imports all nine source shards (including faction), preserves YAML byte hashes, and
      exposes normalized rows sufficient for joins; no DB is committed.
- [x] Identical inputs give the same logical generation and ordered tables/health findings;
      duplicate IDs, malformed sources, unparseable references, missing local refs/tests, and
      legacy-unstructured evidence are deterministic classified findings, never invented links.
- [x] FTS5-present and forced-unavailable tests both pass; unavailable FTS reports disabled
      discovery while exact ID/path operations remain correct.
- [x] An injected parse/validation/replacement failure leaves a prior good DB byte-identical and
      no usable partial DB; failed input never changes YAML.
- [x] The old eight-shard legacy functions and their tests retain their behavior unchanged.

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC
- TCK-20260731-PARITY-INDEX-BASELINE (dependency)
- TCK-20260731-PARITY-IMPACT-PROOF (successor)
- TCK-20260713-MONITORING-SQLITE-INDEX (lifecycle precedent, not a lifecycle template)

## Related Docs
- docs/parity_ledger/schema.json
- docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/

## Related Code Areas
- docs/parity_ledger/
- tools/agent-monitoring/build_index.py
- tools/parity_ledger_scan.py
- tests/tools/test_build_index.py
- expected: tests/tools/test_parity_index.py

## Assumptions / Open Questions
- Phase 0's recorded CLI/module and fallback decisions are prerequisites; do not reopen them here
  except when an implementation contradiction requires an explicit follow-up.

## Implementation Notes
The monitoring index is useful read-only precedent, but its delete-before-build lifecycle must not
be copied: this ticket requires validated temporary build plus atomic replacement.

Implemented `tools/parity_index.py` following plan.md's 8 steps as a single coherent module (the
steps describe an incremental build-up of one file, not separately-committed increments):

- Atomic lifecycle: `_atomic_replace_db()` builds into a `tempfile.mkstemp`-created sibling file in
  the same directory as the final DB path, runs the whole build against that connection, and only
  calls `os.replace()` on success. Any exception (typed or not) deletes the temp file and never
  touches the final path. No `if db_path.exists(): db_path.unlink()` pattern anywhere.
- Shard discovery is `sorted(Path("docs/parity_ledger").glob("*.yaml"))` inside `_load_shards()` —
  fully independent of `tools.parity_ledger_scan.CANONICAL_LEDGER_FILES`; that module is never
  imported. `_sha256_hex` and `serialize_manifest` are imported from `tools/parity_index_baseline.py`
  and reused verbatim (hashing convention, JSON serialization convention), per the plan's reuse
  directive; that module itself was not modified.
- `entries`, `code_refs`/`test_refs`/`constraint_refs`/`ticket_refs`, `entry_health` (materialized
  table, not a view — Step 4 rationale), and `entry_fts` (FTS5, probe-and-fallback via `_probe_fts5()`
  and `build(force_fts5_unavailable=...)`) all implemented as specified in Decisions 1-3 of plan.md.
- Typed build-abort errors: `ShardParseError`, `DuplicateEntryIdError`, `BuildValidationError`. `build()`
  never raises these to its caller — it catches them internally and always returns a structured dict
  (`{"status": "ok", ...}` or `{"status": "failed", "failure_class": ..., "detail": ...}`), serialized
  via `parity_index_baseline.serialize_manifest`'s convention by the CLI. This is a deliberate,
  documented interpretation of Step 6's "return/raise a structured failure report" language — a
  function that sometimes raises and sometimes returns a dict is harder to test and use than one with
  a single consistent return contract, and nothing in the ticket's ACs requires `build()` to raise.
- Manually ran `python3 tools/parity_index.py build` against the real `docs/parity_ledger/` (9 shards)
  as a one-off sanity check (not committed, cleaned up after): 9 shards, 1,945 entries,
  `missing_test_path=1347`, `missing_v2_evidence=0` — exact match to
  `stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/baseline_manifest.json`'s
  `missing_evidence_health` counts, corroborating the entry_health logic against the live corpus per
  the plan's Anti-Drift Notes ("verify against a realistic multi-shard fixture ... not by the spec
  text alone").
- Added the required `parity-index/` `.gitignore` stanza (Step 1) referencing this ticket.

**BLOCKING CONFLICT DISCOVERED — not resolved, reported per project instruction not to work around
gate/test failures silently:**

Adding the `parity-index/` `.gitignore` entry (required by plan.md Step 1, and by this ticket's own
Scope: "Add on-demand build/ignore conventions selected in Phase 0") causes a **pre-existing test in
`tests/tools/test_parity_index_baseline.py`** (from `TCK-20260731-PARITY-INDEX-BASELINE`, commit
`1ec93c0d`) to fail:

```
tests/tools/test_parity_index_baseline.py::test_no_database_or_gitignore_or_make_target_created
    assert "parity-index" not in gitignore_text   # now fails — this ticket added it
```

That test's own docstring/intent (see its neighboring `test_v1_decision_artifact_does_not_authorize_
mutation_cli`) is to prove Phase 0 did *not* prematurely create Phase 1 artifacts. It appears to be a
phase-boundary tripwire that was always going to fail the moment Phase 1/IMPORTER correctly landed the
`.gitignore` entry v1_decisions_phase0.md's own "Ownership" section requires — not a bug introduced by
this implementation.

This directly conflicts with two of this ticket's own binding constraints, both stated as absolute:
plan.md's Scope Guards ("Do not modify `tools/parity_index_baseline.py` or
`tests/tools/test_parity_index_baseline.py`") and test_plan.md's Regression Surface ("must remain
green and untouched"). There is no way to satisfy "add the required `.gitignore` entry" and "leave
`test_parity_index_baseline.py` green and unmodified" simultaneously without either (a) obfuscating the
`.gitignore` entry to dodge the test's literal substring match — rejected, this is exactly the
"edit an artifact to make a gate pass instead of fixing the substance" anti-pattern the project
forbids — or (b) editing `test_parity_index_baseline.py`'s now-stale Phase-0-only assertion, which is
explicitly out of this ticket's authorized scope.

**Resolved (user decision, 2026-08-02):** narrowed `test_no_database_or_gitignore_or_make_target_created`
in `tests/tools/test_parity_index_baseline.py` to check `TCK-20260731-PARITY-INDEX-BASELINE`'s own
commit diff (`git diff-tree --no-commit-id --name-only -r 1ec93c0d`) instead of the live `.gitignore`/
`Makefile` contents. The test's real intent was always "Phase 0's own commit didn't jump ahead into
Phase 1's territory" — a historical fact about one specific commit that stays true forever — not "no
ticket in this epic may ever add a `parity-index/` ignore entry," which was never the property BASELINE
needed to prove and was always going to break the moment Phase 1 correctly shipped. This is a narrow
scope-correction on a mis-written assertion, not an edit to dodge a gate: the underlying substance (Phase
0 didn't create the DB/gitignore/Make target) is unchanged and still verified, now against ground truth
that can't drift. Full regression suite (`test_parity_index_baseline.py` + `test_parity_index.py` +
`test_parity_ledger_scan.py` + `test_parity_updater_static.py`) is 44/44 green after the fix.

## Test Summary
New suite: `pytest tests/tools/test_parity_index.py -v` — 16/16 passed (all tests from test_plan.md's
AC #1-#4 mapping, plus the two Step 8 anti-drift guards).

Regression: `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -q`
— 13/13 passed, unmodified (AC #5).

Regression: `pytest tests/tools/test_parity_index_baseline.py -q` — 15/15 passed after the narrow
`test_no_database_or_gitignore_or_make_target_created` fix (see Implementation Notes).

Full combined run: `pytest tests/tools/test_parity_index_baseline.py tests/tools/test_parity_index.py
tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v` — **44/44 passed.**

## Files Changed
- `tools/parity_index.py` (new)
- `tests/tools/test_parity_index.py` (new)
- `.gitignore` (added `parity-index/` stanza)
- `tests/tools/test_parity_index_baseline.py` (narrowed one stale assertion in
  `test_no_database_or_gitignore_or_make_target_created` to check BASELINE's own commit diff instead
  of live `.gitignore`/`Makefile` state — see Implementation Notes; user-approved resolution)

## Completion Summary
Built the Phase 1 parity-ledger SQLite importer (`tools/parity_index.py`) following plan.md's 8 steps:
atomic sibling-temp-file-then-`os.replace` build lifecycle, independent 9-shard discovery, `entries`
plus four path-level reference tables, a materialized `entry_health` table, and an `entry_fts` FTS5
table with an injectable forced-unavailable fallback seam. Typed abort errors
(`ShardParseError`/`DuplicateEntryIdError`/`BuildValidationError`) guarantee no partial/corrupt DB is
ever left in place. A genuine cross-ticket conflict was found mid-implementation (this ticket's required
`.gitignore` entry broke a BASELINE-ticket test whose assertion was time-bound to "as of Phase 0" but
written as a permanent live-state check) — reported rather than worked around, then resolved per
explicit user decision by narrowing that one assertion to check BASELINE's own historical commit diff.
Full combined regression suite is 44/44 green.

