---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260606-DOCSITE-FM-ARCHIVE
phase: done
date: 2026-06-06
tags: [docsite, fm, archive]
---

# TCK-20260606-DOCSITE-FM-ARCHIVE

## Title
Apply minimal frontmatter to archived and historical docs (bulk pass)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Apply minimal frontmatter to `docs/archive/` (173 files), `docs/superpowers/specs/` (33 files), and `docs/specs/` (4 files). These are historical records — they don't need full classification, just enough frontmatter to be indexed correctly by Docusaurus and the Registry without polluting search results for current docs.

## Scope
- Apply minimal frontmatter to all `.md` files in:
  - `docs/archive/`
  - `docs/superpowers/specs/`
  - `docs/specs/`
- Write `tools/add_frontmatter_archive.py` — bulk script, idempotent
- Infer `original_date` from filename date patterns where present (e.g. `2026-03-15-foo.md` → `2026-03-15`)
- All files in these directories get: `status: archive`, `authority: P2`, `audience: historical`
- `layer` inferred from directory path or filename keywords (e.g. `combat_movement` → `combat`, `resource_` → `economy`)
- Files that cannot be auto-classified get `layer: misc`

## Minimal frontmatter for archive:
```yaml
---
status: archive
authority: P2
audience: historical
layer: combat            # auto-inferred from filename
original_date: 2026-03-15  # from filename date prefix if present
---
```

## Out of Scope
- Reading or updating content of any archived file
- Reclassifying archive files as active
- Deleting any archive files
- `docs/archive/` subdirectories that contain non-markdown files

## Acceptance Criteria
- [ ] Every `.md` file in `docs/archive/`, `docs/superpowers/specs/`, `docs/specs/` has frontmatter
- [ ] All have `status: archive` and `authority: P2`
- [ ] `original_date` populated from filename where detectable (regex: `\d{4}-\d{2}-\d{2}`)
- [ ] `layer` auto-inferred — script reports count of files that fell back to `layer: misc`
- [ ] `tools/validate_frontmatter.py` passes on all modified files
- [ ] Script is idempotent
- [ ] Existing file content is not modified (frontmatter prepended only)

## Related Tickets
- TCK-20260606-DOCSITE-SCHEMA (dependency)
- TCK-20260606-DOCSITE-REGISTRY (consumer)
- TCK-20260606-DOCSITE-INTEGRATION (consumer — archive section of the site)

## Related Docs
- `docs/guidelines/frontmatter_schema.md` (dependency)
- `tickets/todos/PLAN-DOCSITE.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/add_frontmatter_archive.py` (new)
- `docs/archive/**/*.md` (frontmatter prepended, content unchanged)
- `docs/superpowers/specs/*.md` (frontmatter prepended, content unchanged)
- `docs/specs/*.md` (frontmatter prepended, content unchanged)

## Assumptions / Open Questions
- Layer inference keywords for archive filenames: `combat` / `movement` → `combat`, `resource` / `economy` / `crafting` → `economy`, `strategy` / `cognition` / `intel` → `strategy`, `world` / `region` / `ecology` → `world`, `entity` / `aspect` → `core`, `phase_` / `phase0` etc. → infer from phase number range, others → `misc`
- `docs/archive/` contains subdirectories (`entity-enhance/`, `profiling_performance/`, etc.) — the script should recurse into them
- This ticket is lowest priority of the three frontmatter passes — archive docs are read-only history and don't gate anything

## Implementation Notes

- Script written at `tools/add_frontmatter_archive.py` using `rglob("*.md")` on three target dirs.
- Idempotency guard: `content.startswith("---")` — exact start-of-file check, not lstrip.
- Layer keyword map ordered by precedence: combat → movement → economy → strategy → world → core → observability → performance → testing → engine → simulation. First match wins.
- `original_date: unknown` emitted (not omitted) for archive files without a date in the filename — validator requires the field to be present, so omitting it would break validation.
- `authority: P2` and `audience: historical` included as extra fields; `_validate_archive` ignores extra keys so no validation errors.
- `STRAT-KNOWLEDGE-UNIFICATION` correctly resolves to `strategy` via `strat` substring match.
- `sim_test_init_instruction_*.md` resolves to `testing` (not `simulation`) because `testing` layer is checked before `simulation` and `test` appears in the stem — this is correct behaviour.
- 272 files modified on first run; 0 on second run (confirmed idempotent).
- 25 files fell back to `layer: misc` (free-form proposals, phase plans, meta docs).
- Validator passed: 235 archive + 33 superpowers/specs + 4 specs = 272 files, 0 violations.

## Test Summary

- 60 unit tests in `tests/tools/test_add_frontmatter_archive.py`, all passing.
- Groups: layer keyword coverage (29 tests across all 11 categories), misc fallback (6), date extraction (5), has_frontmatter detection (4), build_frontmatter output (8), process_file behaviour (5), idempotency (3).
- Uses `tmp_path` fixture throughout — no filesystem side-effects.

## Files Changed

- `tools/add_frontmatter_archive.py` — new script
- `tests/tools/test_add_frontmatter_archive.py` — new tests
- `docs/archive/**/*.md` — 235 files modified (frontmatter prepended)
- `docs/superpowers/specs/*.md` — 33 files modified (frontmatter prepended)
- `docs/specs/*.md` — 4 files modified (frontmatter prepended)

## Completion Summary

Bulk frontmatter pass complete. All 272 archive/historical docs now have valid `status: archive` frontmatter with inferred `layer` and `original_date`. Validator reports 0 violations across all three directories. Script is idempotent and fully tested (60 tests, 0 failures).
