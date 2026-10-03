---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260709-REGISTRY-DRIFT-CHECK-GATE
artifact_type: test_plan
tags: [testing, observability]
---

# Test Plan — TCK-20260709-REGISTRY-DRIFT-CHECK-GATE

## Regression Surface

**Unit (must keep passing unmodified in behavior, though the file itself gets new tests appended):**

- `tests/tools/test_generate_registry.py` — all 41 existing tests, across:
  - `TestDocEntryGeneration` (7 tests) — `collect_docs()` unaffected by `--check`.
  - `TestTicketEntryGeneration` (6 tests) — `collect_tickets()` unaffected.
  - `TestArtifactJoin` (4 tests) — `join_artifact_files()` unaffected.
  - `TestSortOrder` (5 tests) — `sort_entries()` unaffected.
  - `TestTitleExtraction` (5 tests), `TestRelatedCodeAreas` (5 tests) — parsing helpers unaffected.
  - `TestYAMLOutput` (4 tests, including `test_registry_yaml_written` and
    `test_registry_exits_nonzero_on_missing_doc_frontmatter`) — **these are the tests most at risk
    from a careless refactor**; they call `generate_registry(tmp_path, output)` positionally and
    assert a real file gets written with `rc == 0`/`rc == 1`. Any new `check` parameter must default
    to `False` and leave this exact behavior byte-identical.
  - `TestRealDocsTree` (2 tests) — `test_registry_exits_zero_on_real_docs_tree` runs
    `generate_registry()` against the actual repo root; must still pass (confirms no live
    frontmatter gap exists today — already verified locally, rc=0).
  - `TestEdgeCases` (4 tests) — `_invert_date` and combined doc+ticket sort, unaffected.

**Integration:**

- `tests/tools/test_done_checker_static.py` — `check_registry_entry_regenerated()` tests
  (`TCK-20260709-REGISTRY-REGEN-ON-CLOSE`) call `generate_registry()` in its default (write) mode.
  Confirm this ticket's changes to `generate_registry()`'s signature (adding a `check` kwarg) do not
  break that call site — it must still call `generate_registry(root, registry_output)` with exactly
  two positional args and get the same write behavior.

**Arena-combat:** None — this ticket touches no simulation/combat code.

## New Tests Required

All new tests live in `tests/tools/test_generate_registry.py` (existing file, per the ticket's
own Related Code Areas and the established location for this tool's tests) unless noted otherwise.

1. **`test_check_writes_no_file_when_in_sync`**
   Category: unit.
   Verifies: build a fixture repo whose on-disk `docs/REGISTRY.yaml` already matches what a fresh
   regen would produce (write the fixture, call `generate_registry(..., check=False)` once to
   produce a canonical baseline file, then call again with `check=True`); assert return code `0`
   and that the output file's mtime/content is unchanged (i.e., no write occurred) — most directly,
   assert the file's byte content is identical before/after the `check=True` call.
   Location: `tests/tools/test_generate_registry.py`, new `TestCheckMode` class.

2. **`test_check_exits_nonzero_on_stale_fixture`**
   Category: unit.
   Verifies: build a fixture repo, write a deliberately-stale `docs/REGISTRY.yaml` (e.g. missing an
   entry, or with a `title` field that doesn't match the source doc's `# H1`), call
   `generate_registry(..., check=True)`; assert return code is non-zero **and distinguishable from
   `1`** (the pre-existing frontmatter-error code) — assert the specific drift exit code chosen at
   Implement (recommended `2`, per investigation.md Risk #3). Assert no file was written (content of
   the stale fixture on disk is unchanged after the call).
   Location: `tests/tools/test_generate_registry.py`, `TestCheckMode`.

3. **`test_check_ignores_header_timestamp_drift`**
   Category: unit (regression guard for investigation.md's top-flagged risk).
   Verifies: write an on-disk `docs/REGISTRY.yaml` whose entries exactly match a fresh regen but
   whose header `# Generated: <ts>` line has an old/different timestamp; assert `--check` (or
   `check=True`) still returns `0` — proves the diff compares parsed entries, not raw file text
   including the header. This is the single most important new test in this ticket; without it, a
   naive raw-text-diff implementation would pass tests #1/#2 above by accident (if both fixtures
   happen to be generated in the same test run/second) while still being broken in real CI (where
   the checked-in file's timestamp is always stale relative to a fresh run).
   Location: `tests/tools/test_generate_registry.py`, `TestCheckMode`.

4. **`test_check_reports_readable_diff_summary`**
   Category: unit.
   Verifies: build a stale fixture (as in #2) with a known, specific discrepancy (e.g. one entry's
   `tags` differs); call in `--check` mode; assert the stderr/stdout output contains identifiable,
   human-readable evidence of *what* differs (e.g. the affected path or a count of added/removed/
   changed entries) — not just a bare non-zero exit. Exact format is a new convention (no existing
   `tools/*.py` precedent, per investigation.md) — assert on content substance (e.g. the differing
   entry's `path` string appears in the output), not on an exact string match that would make the
   test brittle to formatting choices made at Implement.
   Location: `tests/tools/test_generate_registry.py`, `TestCheckMode`.

5. **`test_check_writes_no_file_on_missing_output`**
   Category: unit (edge case per investigation.md Risk #5).
   Verifies: `--check` mode where the on-disk output path does not exist at all; assert non-zero
   (drift) exit and no file created at that path afterward.
   Location: `tests/tools/test_generate_registry.py`, `TestCheckMode`.

6. **`test_check_short_circuits_on_doc_frontmatter_error`**
   Category: unit (edge case per investigation.md Risk #4).
   Verifies: a fixture with a doc missing frontmatter (same shape as the existing
   `test_registry_exits_nonzero_on_missing_doc_frontmatter` fixture) combined with `--check`; assert
   the pre-existing exit code `1` (frontmatter error) takes precedence over drift-detection — the
   diff step is never reached/reported when entries can't be computed.
   Location: `tests/tools/test_generate_registry.py`, `TestCheckMode`.

7. **`test_cli_check_flag_end_to_end`**
   Category: integration (subprocess, mirrors `tests/tools/test_add_frontmatter_tickets.py`'s
   `TestValidateFrontmatterAcceptsOutput` pattern, lines 337-417).
   Verifies: `subprocess.run([sys.executable, "tools/generate_registry.py", "--root", str(tmp_path),
   "--output", str(fixture_path), "--check"], capture_output=True, text=True)` against both a
   matching fixture (assert `result.returncode == 0`) and a stale one (assert non-zero,
   distinguishable from `1`) — exercises `main()`'s actual `argparse` wiring, not just the
   `generate_registry()` function directly, since the AC is phrased in terms of the CLI invocation
   (`python3 tools/generate_registry.py --check`).
   Location: `tests/tools/test_generate_registry.py`, new `TestCLICheckFlag` class (separate from
   `TestCheckMode` since it's subprocess-based, matching the existing file's convention of grouping
   in-process vs. CLI-level tests separately where a CLI-level test exists at all).

8. **`test_check_mode_backward_compat_default_still_writes`**
   Category: architecture guard (regression-prevention for the default-write contract).
   Verifies: calling `generate_registry(root, output)` with exactly two positional args (no `check`
   kwarg at all) still writes the file and returns the pre-existing `0`/`1` semantics — proves the
   new parameter is additive, not a breaking signature change. This directly guards the ~35 existing
   tests' assumption named in the ticket's own Assumptions section.
   Location: `tests/tools/test_generate_registry.py`, `TestCheckMode` (or `TestYAMLOutput`,
   colocated with the existing `test_registry_yaml_written`).

9. **CI wiring verification** — not a pytest test per se, but the AC requires a CI job/step. If
   implemented as a new pytest test reusing the `api-tools` job (recommended in investigation.md,
   Risk #2), test #7 above (`test_cli_check_flag_end_to_end`) run **against the real repo root**
   (mirroring `TestRealDocsTree.test_registry_exits_zero_on_real_docs_tree`'s pattern — no `--root`
   override, real `docs/REGISTRY.yaml` as `--output`) is itself the CI gate; no separate `.yml` step
   needed. If implemented as a bespoke `run:` step instead, add a manual verification note to the
   ticket's Implementation Notes confirming the step was exercised locally
   (`python3 tools/generate_registry.py --check`, expect exit `0` against the current tree) since a
   `.yml`-only change has no pytest coverage possible (mirrors the precedent noted in
   `TCK-20260709-REGISTRY-REGEN-ON-CLOSE`'s plan.md Step 3 for `implement-ticket.js`, an analogous
   non-Python file with no test harness).

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_generate_registry.py -v --tb=short
```

Regression cross-check (confirms the sibling ticket's `check_registry_entry_regenerated()` call
site, which uses `generate_registry()`'s default write path, is unaffected by the new `check` kwarg):

```
python3 -m pytest tests/tools/test_generate_registry.py tests/tools/test_done_checker_static.py -v --tb=short
```

Never `pytest tests/` (repo-wide) — out of scope per Testing Rule; this ticket's blast radius is
`tools/generate_registry.py` and its own test file only.

## Anti-Drift Test Guards

- **`test_check_ignores_header_timestamp_drift`** (New Test #3) is itself the primary anti-drift
  guard for this ticket's own implementation — it exists specifically to catch the
  raw-text-diff-including-header failure mode flagged as the top risk in investigation.md. Any
  future refactor of the header format (e.g. adding another timestamp-like field) should re-run
  this test before trusting `--check`'s output.
- **`test_check_mode_backward_compat_default_still_writes`** (New Test #8) guards against a future
  change silently flipping the default value of a `check`-like parameter, which would turn every
  existing write-mode call site (`Makefile`'s `docs-registry` target, `check_registry_entry_regenerated()`)
  into a silent no-op.
- **No test should assert a specific entry count** against the real `docs/REGISTRY.yaml` or
  `docs/` tree (only against `tmp_path` fixtures with a known, fixed entry set) — guards against
  the exact class of drift `TCK-20260709-REGISTRY-COUNT-STALE-DOCS` already had to clean up once
  this session.
- **A guard test should confirm `_SKIP_DOC_SUBDIRS`, `collect_docs`, `collect_tickets`, and
  `sort_entries` are untouched** — reuse the existing `test_skip_doc_subdirs_exist_on_disk` test
  (already present, `TestRealDocsTree`, line 397) as-is; it already fails loudly if
  `_SKIP_DOC_SUBDIRS` drifts from the real `docs/` subdirectory set, which is exactly the kind of
  adjacent-system change this ticket must not introduce as scope-creep.
- **A test should confirm `check_registry_entry_regenerated()` (in `tools/gate_checks/done_checker_static.py`,
  from the sibling ticket) still calls `generate_registry()` in write mode, not check mode** — i.e.,
  this ticket must never flip that call site to `check=True`, which would silently break the
  Finalize-time auto-write guarantee (`INFRA-263`). The existing
  `test_check_registry_entry_regenerated_passes_when_entry_present` test in
  `tests/tools/test_done_checker_static.py` already exercises this end-to-end (it asserts a file
  gets written and an entry appears) — re-running it as part of this ticket's regression surface
  (see Scoped Pytest Commands) is sufficient; no new test needed specifically for this guard.
