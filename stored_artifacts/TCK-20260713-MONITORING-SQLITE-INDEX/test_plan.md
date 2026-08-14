---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260713-MONITORING-SQLITE-INDEX
artifact_type: test_plan
tags: [agent-monitoring, data-quality, schema]
---

# Test Plan — TCK-20260713-MONITORING-SQLITE-INDEX

## Regression Surface

This ticket adds a new, read-only, on-demand build script. It touches no existing source file, so the regression surface is "prove nothing else moved," not "re-verify unrelated behavior."

**Unit — must keep passing unmodified:**
- `tests/tools/test_validate_agent_monitoring.py` (all tests, especially `test_canonical_vocabulary_single_sourced`, `test_drift_report_is_read_only`, `test_tool_count_drift_report_is_read_only`, `test_multi_invocation_collision_report_is_read_only`) — `validate.py` is read but never modified by this ticket.
- `tests/tools/test_generate_retro.py` — `generate_retro.py`'s `_resolve_status()`/`compute_retro_metrics()` are read (as the AC3 cross-check target) but not modified.
- `tests/tools/test_knowledge_search.py` — not exercised by this ticket's code, but its `TestMakefileTargets`/`TestGitignore` classes are the structural pattern this ticket's own new tests (below) must mirror; run once to confirm the precedent still holds before copying its shape.

**Integration — write-path guard (must stay green, proves this ticket didn't touch the write path):**
- `tests/tools/test_agent_monitoring_legacy_reader.py`
- `tests/tools/test_agent_monitoring_manifest.py`
- `tests/tools/test_monitoring_bypass_fix.py`
- `tests/tools/test_monitoring_writer.py`
- `tests/tools/test_monitoring_writer_lockfile_candidate.py`
- `tests/tools/test_monitoring_writer_single_source.py`

**Arena-combat:** not applicable — `tools/agent-monitoring/` has no simulation/combat surface.

## New Tests Required

All new tests live in `tests/tools/test_build_index.py` (new file), mirroring `tests/tools/test_knowledge_search.py`'s class-per-concern grouping.

1. **`test_build_creates_gitignored_sqlite_db`** — unit. AC1: running `python3 tools/agent-monitoring/build_index.py` against a fixture/tmp corpus reads all 3 JSONL files, writes a SQLite file with `runs`/`events`/`tools` tables, and the process exits 0.
2. **`test_source_jsonl_files_byte_identical_after_build`** — unit. AC2: sha256 hash of `runs.jsonl`/`events.jsonl`/`tools.jsonl` computed before and after a `build_index.py` run is identical (bit-for-bit), including with a fixture containing the 3 known off-schema `tools.jsonl` shapes.
3. **`test_resolved_status_matches_generate_retro_resolve_status`** — unit, cross-module consistency check (mirrors the shape of `test_canonical_vocabulary_single_sourced`). AC3: for every row in a fixture built from the *live* `runs.jsonl` (or a representative sample covering the 60 observed key-shapes), assert the `runs` table's `resolved_status` column equals `generate_retro.py::_resolve_status(record)` for that `run_id`.
4. **`test_completeness_matches_validate_legacy_allowlists`** — unit, on the **same fixture data `tests/tools/test_validate_agent_monitoring.py` uses** (AC4 explicitly names this fixture). Assert the `runs` table's completeness/terminal-status classification agrees with `validate.py::_record_is_complete()` for each fixture record.
5. **`test_type_checker_legacy_shape_does_not_crash_build`** — unit, regression guard tied to the Investigation's Prior Work finding: the `TCK-20260623-TYPE-CHECKER` 6th legacy shape (`"outcome":"success"`, no `end_ts`/`final_status`/`status`) must not raise during build; its `resolved_status` may legitimately be `NULL`/unresolved — assert no exception, not a specific resolved value.
6. **`test_build_twice_produces_same_row_counts`** — unit. AC5 (row-count-identical form — see Investigation Risk #5 on why byte-identical SQLite output is not a safe assumption): run `build_index.py` twice against unchanged inputs, assert each table's row count is identical across both runs.
7. **`test_makefile_has_agent_monitoring_index_target`** / **`test_makefile_agent_monitoring_index_calls_build_index`** — unit, mirrors `test_knowledge_search.py::test_makefile_has_knowledge_index_target`/`test_makefile_knowledge_index_calls_build`. AC6: `Makefile` has an `agent-monitoring-index:` target that invokes `tools/agent-monitoring/build_index.py`.
8. **`test_agent_monitoring_index_not_in_test_ci_all_targets`** — unit, mirrors `test_knowledge_index_not_in_test_target`. Architecture guard: `agent-monitoring-index` must not be a dependency of `test:`/`ci:`/`all:` Makefile targets (keeps the on-demand-only design intent out of the CI critical path).
9. **`test_db_path_in_gitignore`** — unit, mirrors `test_knowledge_index_in_gitignore`. AC6: the new DB's directory/path is listed in `.gitignore`.
10. **`test_build_index_skips_offschema_tools_records`** — unit, new-finding regression guard. Fixture `tools.jsonl` containing the 3 confirmed off-schema shapes (`{"tool":"implement-epic","last_run":...}`, `{"run_id":...,"tools_used":[...]}`, `{"session_id":...,"run_id":...,"seq":...,"ts":...}` with no `tool` key) — assert `build_index.py` completes without exception and those 3 records are excluded from the `tools` table (or land in a clearly-flagged quarantine state), never silently coerced into a fabricated `tool` value.
11. **`test_events_table_tolerates_duplicate_run_id_seq`** — unit/architecture guard, tied to the pause/resume seq-collision precedent. Fixture `events.jsonl` with two records sharing the same `(run_id, seq)` (the documented historical collision signature) — assert the build does not crash on a `UNIQUE(run_id, seq)` constraint violation.
12. **`test_no_incremental_build_flag_exists`** — architecture guard (anti-drift). Assert `build_index.py`'s argparse surface has no `--incremental` flag/mode, unlike `knowledge_search.py`.
13. **`test_build_index_never_touches_write_path_modules`** — architecture guard. Source-text/import-graph check (mirrors `test_canonical_vocabulary_single_sourced`'s style): `tools/agent-monitoring/build_index.py` must not import or call `pre_tool_hook`, `post_tool_hook`, `record_run`, `record_events`, or `writer.write_line`.
14. **`test_build_index_imports_vocabulary_not_reencoded`** — architecture guard. Assert `build_index.py` imports `CANONICAL_TIERS`/`WORKFLOW_PHASES`/`WORKFLOW_AGENTS` (or equivalent) from `vocabulary.py` rather than redefining literal phase/agent/tier sets inline.

## Scoped Pytest Commands

```bash
# Primary — the new build script's own test suite
pytest tests/tools/test_build_index.py -v

# Regression — confirm the write path / existing readers are unaffected
pytest tests/tools/test_validate_agent_monitoring.py tests/tools/test_generate_retro.py -v
pytest tests/tools/test_agent_monitoring_legacy_reader.py tests/tools/test_agent_monitoring_manifest.py \
  tests/tools/test_monitoring_bypass_fix.py tests/tools/test_monitoring_writer.py \
  tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_monitoring_writer_single_source.py -v

# Broader scoped sweep of the whole tools/agent-monitoring/ + build_index surface (still not repo-wide)
pytest tests/tools/ -k "monitoring or build_index or knowledge_search" -v
```

**Never:** `pytest tests/` (repo-wide). Scope stays inside `tests/tools/` — this ticket touches nothing under `src/`.

## Anti-Drift Test Guards

- `test_build_index_never_touches_write_path_modules` — catches accidental coupling to the hook/writer write path, which CLAUDE.md's hard rule and the idea doc both require stays untouched.
- `test_no_incremental_build_flag_exists` — catches incremental-build scope creep explicitly rejected by the idea doc.
- `test_source_jsonl_files_byte_identical_after_build` — catches any accidental write-back to the source JSONL files, including "fixing" the 3 off-schema `tools.jsonl` records in place.
- `test_agent_monitoring_index_not_in_test_ci_all_targets` — catches the new Make target being wired into the CI-blocking path, which would silently change the "on-demand only" design contract.
- `test_build_index_imports_vocabulary_not_reencoded` — catches phase/agent/tier vocabulary drift by re-derivation instead of import, the exact anti-pattern `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT` was created to eliminate.
- `test_type_checker_legacy_shape_does_not_crash_build` — catches a future contributor "fixing" the one permanently-documented unresolvable legacy record instead of leaving it as the accepted exception `docs/agent-monitoring/schema.md`'s Known Limitations section already documents.
