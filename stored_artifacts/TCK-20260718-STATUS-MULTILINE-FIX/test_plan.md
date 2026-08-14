---
artifact_type: test_plan
ticket_id: TCK-20260718-STATUS-MULTILINE-FIX
date: 2026-07-18
---

# Test Plan — TCK-20260718-STATUS-MULTILINE-FIX

## Regression Surface

- `tests/tools/test_status_drift_check.py` — all 12 pre-existing tests must keep passing
  unmodified against the rewritten extraction (colon-format skip, epic-tier exemption,
  legacy-naming exemption, CLI/marker contract, read-only guard, aggregate-both-scans).
- `tests/tools/test_generate_registry.py` — `TestRealDocsTree::test_check_flag_detects_no_drift_
  against_real_registry` must pass after `docs/REGISTRY.yaml` regeneration.
- `tests/tools/test_validate_frontmatter.py` — must keep passing (no frontmatter schema changes
  made, only `phase` value corrected on one file).

## New Tests Required

- `test_uses_real_dashboard_extraction_function` — anti-drift guard proving the checker module
  imports and calls the actual `parse_body_section`, not a reimplemented regex.
- `test_stray_trailing_line_after_done_flagged` — proves Class A's shape (`DONE\nINPROGRESS`) is
  now caught as FAIL.
- `test_done_bleeding_into_trailing_bold_block_flagged` — proves Class B's shape (`DONE` +
  trailing bold-text block, no next heading) is now caught as FAIL.
- `test_done_with_trailing_content_after_proper_tier_heading_passes` — proves a well-formed file
  (real `## Tier` heading immediately follows) still resolves cleanly to PASS, confirming the fix
  targets the missing-heading-boundary bug specifically, not a blanket rejection.

## Scoped Test Commands

```
python3 -m pytest tests/tools/test_status_drift_check.py -q
python3 -m pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -q
```

## Anti-Drift Test Guards

- Every file-edit step used an `assert` (Python `re.sub` result != original text, or
  `str.endswith(expected_block)`) before writing — any file whose actual content didn't match the
  expected pattern would raise loudly rather than silently no-op or corrupt.
- Post-fix, `check_status_drift()` was run live against the real corpus (not just fixtures) and
  confirmed 0 findings — both `check_ticket_status_drift()` and
  `check_runs_jsonl_final_status_drift()` return PASS.
- `parse_body_section` was called directly (not re-derived) on all 15 touched files post-fix to
  confirm each resolves to exactly `'DONE'` — same verification method used to derive the original
  Class A/B/C file lists, closing the loop.
