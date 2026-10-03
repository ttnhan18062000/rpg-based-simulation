---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-FM-ARCHIVE
artifact_type: test_plan
tags: [docsite, fm, archive]
---

# Test Plan — TCK-20260606-DOCSITE-FM-ARCHIVE

## Regression Surface

This ticket introduces `tools/add_frontmatter_archive.py` (new file). It does not modify any existing source code. The regression surface is therefore:

1. The new script itself (unit + integration tests)
2. The validator (`tools/validate_frontmatter.py`) — no changes; regression check via existing tests
3. All 272 modified `.md` files — must pass `validate_frontmatter.py` after the script runs
4. No changes to `src/`, `tests/` (non-tools), or any simulation logic

Existing test suite is **not affected**. The only test file that needs to be created is `tests/tools/test_add_frontmatter_archive.py`.

---

## New Tests Required

### Test file location
`tests/tools/test_add_frontmatter_archive.py`

### Test groups

---

### Group 1 — `infer_layer(stem)` unit tests

Test the layer inference function in isolation.

| Test | Input | Expected |
|---|---|---|
| `test_layer_combat_from_stem` | `combat_movement_finalized` | `combat` |
| `test_layer_movement_from_stem` | `movement_rules` | `combat` |
| `test_layer_economy_from_stem` | `resource_phase5_milestone1` | `economy` |
| `test_layer_economy_resource_prefix` | `resource_handbook` | `economy` |
| `test_layer_strategy_from_stem` | `strategy_implementation_milestone_3` | `strategy` |
| `test_layer_strategy_intel_keyword` | `intel_capacity_implementation` | `strategy` |
| `test_layer_strategy_thinking_keyword` | `thinking_implementation_phase_1` | `strategy` |
| `test_layer_world_from_stem` | `world_phase_20_28` | `world` |
| `test_layer_core_entity_keyword` | `entity_enhance_phase1` | `core` |
| `test_layer_core_aspect_keyword` | `aspect_design` | `core` |
| `test_layer_observability_obs_prefix` | `obs_sim_phase3` | `observability` |
| `test_layer_observability_full_keyword` | `observability_memory_issue` | `observability` |
| `test_layer_performance_perf_prefix` | `perf_plan_v2` | `performance` |
| `test_layer_performance_full_keyword` | `performance_hardening_plan` | `performance` |
| `test_layer_performance_optimization_keyword` | `optimization_implementation_milestone5` | `performance` |
| `test_layer_misc_fallback_generic` | `pitch` | `misc` |
| `test_layer_misc_fallback_phase_plan` | `phase_0_ds_implementation_plan` | `misc` |
| `test_layer_misc_fallback_repair` | `repair_implementation` | `misc` |
| `test_layer_case_insensitive` | `STRAT-KNOWLEDGE-UNIFICATION` (lowercased) | `strategy` |
| `test_layer_priority_order_combat_over_misc` | `combat_resource_doc` | `combat` (first match wins) |

---

### Group 2 — `extract_date(filename)` unit tests

Test date extraction from filenames.

| Test | Input | Expected |
|---|---|---|
| `test_date_extracts_prefix_pattern` | `2026-03-20-aspect-oriented-modularization-design.md` | `2026-03-20` |
| `test_date_extracts_from_middle` | `doc-2026-05-14-notes.md` | `2026-05-14` |
| `test_date_returns_unknown_when_absent` | `combat_movement_finalized.md` | `"unknown"` |
| `test_date_returns_first_match` | `2026-03-21-2026-04-01-two-dates.md` | `2026-03-21` |
| `test_date_no_partial_matches` | `20260321notseparated.md` | `"unknown"` (no hyphens → no match) |

---

### Group 3 — Frontmatter prepend (core write logic)

Test using `tmp_path`; do not touch real `docs/`.

| Test | Setup | Assert |
|---|---|---|
| `test_prepends_frontmatter_to_bare_file` | File with no `---` | File now starts with `---\nstatus: archive\n` |
| `test_skips_file_with_existing_frontmatter` | File already starts with `---\nstatus: archive\n---\n` | File content unchanged; skip logged |
| `test_prepended_content_passes_validator` | Bare file processed by script | `validate_file(path)` returns `[]` |
| `test_original_content_preserved` | File with body `# Title\nsome content\n` | Body intact after prepend |
| `test_correct_layer_written` | `resource_handbook.md` (no FM) | Frontmatter contains `layer: economy` |
| `test_correct_date_written_when_present` | `2026-04-17-combat-movement-m1-design.md` | Frontmatter contains `original_date: 2026-04-17` |
| `test_unknown_date_written_when_absent` | `strategy_implementation.md` | Frontmatter contains `original_date: unknown` |
| `test_authority_and_audience_included` | Any bare file | Frontmatter contains `authority: P2` and `audience: historical` |
| `test_status_is_archive` | Any bare file | Frontmatter contains `status: archive` |

---

### Group 4 — Idempotency

| Test | Steps | Assert |
|---|---|---|
| `test_idempotent_single_run` | Run script on tmp dir twice | Second run produces no changes (all files skipped) |
| `test_idempotent_content_unchanged` | Read content after 1st run, re-run, read again | Byte-for-byte identical |
| `test_idempotent_skip_count_equals_total_after_second_run` | Track skip counter after 2nd run | skip_count == total file count |

---

### Group 5 — Directory recursion and file filtering

| Test | Setup | Assert |
|---|---|---|
| `test_recurses_into_subdirectory` | `tmp/docs/archive/subdir/deep.md` (no FM) | Deep file gets frontmatter prepended |
| `test_skips_non_md_files` | `tmp/docs/archive/proposal.txt` alongside `.md` files | `.txt` untouched |
| `test_empty_directory_no_error` | Empty `tmp/archive/` dir | Exits 0, 0 files processed |
| `test_processes_multiple_target_dirs` | Files in all three target dirs | All files processed in one invocation |

---

### Group 6 — Reporting / output contract

| Test | Assert |
|---|---|
| `test_reports_prepended_count` | stdout or return value includes count of prepended files |
| `test_reports_skipped_count` | includes count of skipped files |
| `test_reports_misc_layer_count` | includes count of files that fell back to `layer: misc` |

---

### Group 7 — Validator integration (end-to-end)

These tests run `validate_frontmatter.py` as a subprocess against the output of the script, mirroring the acceptance criteria.

| Test | Assert |
|---|---|
| `test_validator_passes_on_script_output_archive_layer` | `validate_frontmatter.py docs/archive/subdir.md` exits 0 for a file with `layer: combat` |
| `test_validator_passes_on_script_output_misc_layer` | Same for `layer: misc` |
| `test_validator_passes_on_script_output_with_unknown_date` | `original_date: unknown` — validator does not enforce ISO format; should pass |
| `test_validator_fails_if_frontmatter_missing` | Sanity check: a bare file without running script fails validation |

---

## Scoped Pytest Commands

Run only the new script tests (fast, no I/O to real docs/):
```bash
pytest tests/tools/test_add_frontmatter_archive.py -v
```

Run new script tests plus the existing validate_frontmatter tests (full tools suite):
```bash
pytest tests/tools/ -v
```

Run with markers to exclude slow tests:
```bash
pytest tests/tools/ -v -m "not slow"
```

Post-implementation acceptance check (run validator against all three directories):
```bash
python3 tools/validate_frontmatter.py docs/archive/
python3 tools/validate_frontmatter.py docs/superpowers/specs/
python3 tools/validate_frontmatter.py docs/specs/
```

All three must exit 0 for the acceptance criteria to be met.
