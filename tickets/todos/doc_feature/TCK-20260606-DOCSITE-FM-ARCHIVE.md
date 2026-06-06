# TCK-20260606-DOCSITE-FM-ARCHIVE

## Title
Apply minimal frontmatter to archived and historical docs (bulk pass)

## Status
OPEN

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

## Test Summary

## Files Changed

## Completion Summary
