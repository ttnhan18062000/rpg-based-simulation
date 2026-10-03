---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP
artifact_type: test_plan
tags: [testing, bug]
---

# Test Plan — TCK-20260817-TESTS-TOOLS-LANE-STALE-REFERENCE-SWEEP

## Regression Surface

This ticket touches only test/doc infrastructure files — no `src/` behavior changes — so the
regression surface is the `tests/tools` lane itself plus the two adjacent lanes whose collected
tests overlap the edited files.

**unit (via `tests/unit/content`, `unit-core-world` CI job):**
- `tests/unit/content/test_content_usage_matrix.py` — all 8 tests, especially
  `test_generate_and_save_report` (must still write a valid `.md` file with the report table
  intact after the frontmatter prepend) and `test_matrix_exists_and_can_be_imported`.

**tools (`tests/tools`, `api-tools` CI job, `-m "not slow"`):**
- `tests/tools/test_gate_a_readpath_review.py` — full file, all classes.
- `tests/tools/test_generate_registry.py::TestRealDocsTree` (both tests).
- `tests/tools/test_validate_frontmatter.py::TestPreviouslyFrontmatterMissingDocs` (all 12
  parametrized cases — not just `content_usage_matrix.md`'s own case, to confirm no regression on
  the other 11).
- `tests/tools/test_context_kind_priority_decision.py` — full file (11 tests).
- `tests/tools/test_exact_lookup_convention_decision.py` — full file (12 tests).
- `tests/tools/test_stored_artifact_kind_decision.py` — full file (11 tests).
- `tests/tools/test_epic_staleness_check.py` — full file (all ~17 tests, not just the 2 being
  restructured — the synthetic-fixture helpers and other tests in this file must keep passing
  unmodified).
- `tests/tools/test_search_mcp.py` — full file (`TestMcpJson`, `TestDeriveTitle`, `TestRunSearch`,
  and any other classes in the file).
- `tests/tools/test_entity_event_ledger.py` — full file (both `test_entity_ledger_evidence_
  citations_are_real_files` and `test_entity_ledger_covers_every_entity_update_field`, plus any
  other tests reading `docs/event_ledger/entity.yaml`).
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py` — full file (17 tests), confirming the
  16 non-mutation tests still run and pass under `-m "not slow"` after the marker is added, and
  under `-m "slow"` including the marked test.
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py` — full file (31 tests), same
  split check.
- `tests/tools/test_parity_ledger_scan.py`, `tests/tools/test_parity_index.py` — regression check
  that narrowing the frozen-hash dicts (Group 3) did not silently mask any other real drift in
  `tools/parity_index.py`/`tools/generate_registry.py`.

**docs/architecture (frontmatter validator itself):**
- `tests/tools/test_validate_frontmatter.py` — full file, not just the one parametrized group, in
  case the new `content_usage_matrix.md` frontmatter interacts with any other validator rule
  (e.g. `STATUS_VALUES`/`LAYER_VALUES` enum checks).

## New Tests Required

1. **Test name:** (extend) `test_command_is_python3` → rewritten in place to assert the real
   contract.
   **Category:** unit (static doc/config assertion).
   **What it verifies:** `.mcp.json`'s `knowledge-search` server `command` field is `"bash"` (the
   real, intentional, already-shipped `TCK-20260624-FIX-TOOLS-SERVER` portability fix), not the
   stale `"python3"` literal.
   **Where:** `tests/tools/test_search_mcp.py::TestMcpJson`.

2. **Test name:** (extend) `test_args_point_to_search_mcp` → rewritten in place.
   **Category:** unit (static doc/config assertion).
   **What it verifies:** `args[0]` is `"tools/start_search_mcp.sh"` (the wrapper script actually
   invoked), not a stale assumption that `args[0]` is `search_mcp.py` directly. This is a 2nd real
   failure found during Investigate, beyond the ticket's own named Group 7 scope — see
   investigation.md.
   **Where:** `tests/tools/test_search_mcp.py::TestMcpJson`.

3. **Test name:** `test_start_search_mcp_wrapper_invokes_python3` (new).
   **Category:** unit (static file-content assertion).
   **What it verifies:** `tools/start_search_mcp.sh`'s own text contains a `python3` invocation —
   proves the full `.mcp.json` → wrapper → interpreter chain end-to-end, not just the first hop,
   closing the gap that made the original stale test look locally "correct in spirit" while
   asserting the wrong literal.
   **Where:** `tests/tools/test_search_mcp.py::TestMcpJson` (new method on the same class).

4. **Test name:** `test_epic_ticket_decision_9_marked_resolved` → path constant updated in place
   (no new test; existing test body unchanged).
   **Category:** unit (static doc assertion).
   **What it verifies:** unchanged — `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Open
   Decision 9 is marked resolved. Only `_EPIC_TICKET_PATH`'s directory segment changes
   (`inprogress` → `backlogs`).
   **Where:** `tests/tools/test_exact_lookup_convention_decision.py`.

5. **Test name:** `test_no_code_changes_to_named_tools_modules` (×3, one per decision-doc file) →
   dict entries narrowed in place, each with an added inline disclosure comment citing this ticket
   and the confirmed reason (`tools/parity_index.py` / `tools/generate_registry.py` legitimately
   changed via unrelated later work, per `git log`).
   **Category:** unit (frozen-content-hash guard).
   **What it verifies:** unchanged in spirit — the *remaining* named files in each dict were not
   touched by that historical decision-only ticket. Only the stale entry is removed, never the
   whole guard.
   **Where:** `tests/tools/test_context_kind_priority_decision.py`,
   `tests/tools/test_exact_lookup_convention_decision.py`,
   `tests/tools/test_stored_artifact_kind_decision.py`.

6. **Test name:** (new, or extended module-level skip machinery) — no new *assertions* are added
   to `test_gate_a_readpath_review.py`; the fix is `@pytest.mark.skipif`/`pytest.skip()` guards on
   existing tests, with a dated, ticket-cited reason string.
   **Category:** integration (documented, honest skip — not a new behavioral test).
   **What it verifies:** running the file after the fix shows `10 skipped` (not failed/errored) for
   the corpus-dependent tests, and `6 passed` (unchanged) for `TestNoMutation` +
   `TestDecisionDocIntegrity`. A regression test for this shape: assert (in a small new test, or as
   part of Verify's scoped run) that `pytest tests/tools/test_gate_a_readpath_review.py -v` reports
   `0 failed, 0 errors`.
   **Where:** `tests/tools/test_gate_a_readpath_review.py` (module-level `_CORPUS_AVAILABLE` +
   `_SKIP_REASON` constants, applied via decorators/`pytest.skip()`).

7. **Test name:** `generate_matrix_report()`'s output now includes a frontmatter block — covered
   by the *existing* `test_generate_and_save_report` (no new test needed, since that test already
   asserts `"# Content Usage Matrix Report" in report` and writes the file; the frontmatter
   presence is exercised transitively by `TestRealDocsTree` and
   `TestPreviouslyFrontmatterMissingDocs` re-reading the regenerated file). Optionally add one
   direct assertion in `tests/unit/content/test_content_usage_matrix.py` that `report.startswith("---\n")`
   to make the frontmatter contract explicit at the source, not just downstream.
   **Category:** unit.
   **What it verifies:** `generate_matrix_report()` itself, not just the file it produces, carries
   the frontmatter — protects against a future refactor of the write path silently dropping it.
   **Where:** `tests/unit/content/test_content_usage_matrix.py` (new assertion, existing test or a
   small new one).

8. **Test name:** `test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run` (×2, one
   per file) → decorated `@pytest.mark.slow` in place, no assertion changes.
   **Category:** unit (marker-only change).
   **What it verifies:** unchanged test body; only its collection lane changes. Verify with two
   separate scoped runs (see below) that it is excluded under `-m "not slow"` and still passes
   under `-m "slow"`.
   **Where:** `tests/tools/test_kgmcp_phase2_baseline_recomparison.py:375`,
   `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py:667`.

9. **Test name:** `test_epic_staleness_synthetic_never_started_epic_end_to_end` (new,
   replaces/supersedes the real-obsiso-dependent assertions).
   **Category:** integration (exercises the full `compute_stale_epics_report`/`find_stale_epics`
   pipeline, matching the original test's intent, but fully synthetic).
   **What it verifies:** a synthetic `tmp_path`-based epic (folder mode, mirroring OBSISO's
   original shape: a subfolder with `SEQUENCE.md` listing child ticket IDs) with **zero** rows for
   any of its child IDs in a synthetic `working_log.csv` and a synthetic (empty) `runs.jsonl` is:
   (a) absent from `find_stale_epics(...)`'s returned list, and (b) present in
   `compute_stale_epics_report(...)`'s `"Informational:"` section, not its stale section — the
   exact same two assertions the original `test_does_not_flag_never_started_real_obsiso_epic` made,
   against synthetic inputs built with the same `tmp_path` helper pattern already used by
   `test_does_not_flag_recently_active_epic`/`test_epic_with_all_children_stale` in this file.
   **Where:** `tests/tools/test_epic_staleness_check.py` (replaces
   `test_does_not_flag_never_started_real_obsiso_epic`).

10. **Test name:** `test_advisory_only_no_file_mutation_synthetic` (new, replaces the
    `REAL_OBSISO_DIR`-dependent version).
    **Category:** unit (mutation guard).
    **What it verifies:** hashing a synthetic `tmp_path` epic folder's files before/after calling
    `compute_stale_epics_report(...)`/`find_stale_epics(...)` shows no byte change — same mechanism
    as the original, on a controlled directory instead of a live, mutable repo path (so the test
    can never silently start failing again just because a folder gets archived).
    **Where:** `tests/tools/test_epic_staleness_check.py` (replaces
    `test_advisory_only_no_file_mutation`).

11. **Test name:** `test_entity_ledger_evidence_citations_are_real_files` — no new test; existing
    test body unchanged, only `docs/event_ledger/entity.yaml:30`'s prose edited so the second
    `event_extractor.py` mention carries its real path prefix.
    **Category:** unit (data-file correction, not a test-code change).
    **What it verifies:** unchanged — every `.py`-shaped substring the test's regex extracts from
    every ledger entry's `evidence` field resolves to a real file on disk.
    **Where:** `docs/event_ledger/entity.yaml`.

## Scoped Pytest Commands

Never `pytest tests/`. Scoped to the affected domains:

```bash
# Primary regression target — the real api-tools CI-lane command, must be 0 failed / 0 errors
pytest tests/tools -m "not slow" --tb=short -q

# Confirm the 2 re-marked tests are excluded from the fast lane...
pytest tests/tools/test_kgmcp_phase2_baseline_recomparison.py tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py -m "not slow" -v

# ...and still pass under the slow lane at large budget (matching the real slow-job command)
pytest tests/tools/test_kgmcp_phase2_baseline_recomparison.py tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py -m "slow" --resource-budget large -v

# Group 2 — regenerator + downstream doc-validation consumers
pytest tests/unit/content/test_content_usage_matrix.py tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -q

# Group 4 — the corpus-dependent skip file, full detail
pytest tests/tools/test_gate_a_readpath_review.py -v

# Group 5 — epic staleness, full file
pytest tests/tools/test_epic_staleness_check.py -v

# Groups 3, 6, 7, 8 — the remaining named files, one combined run
pytest tests/tools/test_context_kind_priority_decision.py tests/tools/test_exact_lookup_convention_decision.py tests/tools/test_stored_artifact_kind_decision.py tests/tools/test_search_mcp.py tests/tools/test_entity_event_ledger.py -v

# Full lane, twice — must both be clean
pytest tests/tools -m "not slow" --tb=short -q
pytest tests/tools -m "slow" --resource-budget large --tb=short -q
```

## Anti-Drift Test Guards

- **Group 3/4 frozen-hash dicts:** the regression command above must show the *other* (non-stale)
  entries in each `_EXPECTED_TOOLS_HASHES`/protected-files dict still pass — a fix that
  accidentally removes a still-valid entry (over-narrowing) would silently stop protecting that
  file, which `git diff` review at Verify time must also catch, not just the test's own green.
- **Group 4 skip guard:** assert the skip count is exactly 10 and the pass count is exactly 6 after
  the fix (`pytest tests/tools/test_gate_a_readpath_review.py -v` output) — a different split would
  indicate the `_CORPUS_AVAILABLE` guard was applied to the wrong test set (e.g. accidentally
  skipping `TestNoMutation` or `TestDecisionDocIntegrity`, which must never depend on the corpus).
- **Group 5 synthetic fixture:** the new synthetic test must still fail loudly (i.e., the epic
  *would* show up in the stale list) if given a non-empty `working_log.csv` row for one of its
  child IDs dated more than `DEFAULT_STALENESS_WINDOW_DAYS` (5) days before `now` — sanity-check
  this by temporarily asserting the *opposite* case still works via the file's own existing
  `test_epic_with_all_children_stale` (unmodified), proving the synthetic zero-activity test and
  the synthetic stale test are genuinely exercising different code paths, not both trivially
  passing due to a fixture-construction bug.
- **Group 1 marker scope:** confirm via `pytest tests/tools/test_kgmcp_phase2_baseline_recomparison.py
  tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py -m "not slow" -v` that exactly 16 +
  30 = 46 tests still run (not the two `test_zero_mutation_...` tests) — a marker applied to the
  wrong function name, or accidentally at module level, would silently drop far more tests than
  intended from the fast lane's real coverage.
- **Group 2 generator:** re-run `tests/unit/content/test_content_usage_matrix.py::
  test_generate_and_save_report` and then independently re-validate the regenerated
  `docs/mechanics/content_usage_matrix.md` with `python3 tools/validate_frontmatter.py
  docs/mechanics/content_usage_matrix.md` (or the equivalent scoped validator invocation) — proves
  the frontmatter survives a real regeneration cycle, not just a hand-edited snapshot that the next
  test run would silently overwrite again.
- **Group 8:** re-run the full `docs/event_ledger/entity.yaml` evidence-citation test (not just
  `ENTITY-003`'s case) to confirm the edit did not introduce a new bare-filename regex match
  elsewhere in the same entry's prose.
