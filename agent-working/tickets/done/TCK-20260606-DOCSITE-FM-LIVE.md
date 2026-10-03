---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260606-DOCSITE-FM-LIVE
phase: done
date: 2026-06-06
tags: [docsite, fm, live]
---

# TCK-20260606-DOCSITE-FM-LIVE

## Title
Apply frontmatter to all live and authoritative docs in docs/

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Apply the frontmatter schema (from TCK-20260606-DOCSITE-SCHEMA) to every actively-referenced markdown file in `docs/`, excluding `docs/archive/` and `docs/superpowers/specs/` (covered by Ticket 5). This is the largest frontmatter pass — roughly 150 files across 13 subdirectories.

## Scope
Apply frontmatter to:
- `docs/mechanics/` — 8 files, all `status: authoritative`, `authority: P0`
- `docs/engine/` — classify individually: named contract files → `active P1`, dated phase packages → `historical P2`
- `docs/core/` — 5 files, `status: authoritative`, `authority: P0`
- `docs/architecture/` — 8 ADRs, `status: active`, `authority: P1`
- `docs/systems/` — 10 files, `status: active`, `authority: P1`
- `docs/combat/` — 9 files, milestone rulebooks, `status: active` for current milestone, `historical` for earlier
- `docs/observability/` — key `.md` files only (skip the 15 JSON baselines); phase docs `historical`, how-to-run `active`
- `docs/performance/` — 11 files, reports are `historical`, optimization_architecture is `active`
- `docs/strategy/` — 10 files, bounded cognition contracts `active`
- `docs/compliance/` — 3 files, `active`
- `docs/testing/` + `docs/test_coverage/` — 7 files, taxonomy `active`, coverage reports `historical`
- `docs/ai/` — 5 files, `status: active`, `authority: P1`
- `docs/guidelines/` — 3 files, `active`
- Loose files: `docs/README.md`, `docs/logic_checklist_exhaustive.md`, `docs/optimization_audit_ledger.md`

Write a Python script `tools/add_frontmatter_live.py` that:
1. Walks the target directories
2. Skips files that already have frontmatter
3. Infers `status` and `authority` from a classification map defined in the script
4. Writes the frontmatter block to each file
5. Prints a summary of files modified vs skipped

## Out of Scope
- `docs/archive/` (Ticket 5)
- `docs/superpowers/specs/` (Ticket 5)
- `docs/specs/` (Ticket 5)
- `docs/parity_ledger/` (YAML files, not markdown)
- `docs/scenarios/` (YAML files)
- `docs/entity/*.mmd` (Mermaid diagram, not markdown)
- Tickets and stored artifacts (Ticket 4)

## Acceptance Criteria
- [ ] Every `.md` file in the in-scope directories has a valid frontmatter block
- [ ] `tools/validate_frontmatter.py` passes on all modified files with zero violations
- [ ] `docs/mechanics/` files are all `authority: P0`, `status: authoritative`
- [ ] `docs/core/` files are all `authority: P0`, `status: authoritative`
- [ ] `docs/engine/` files are individually classified — no bulk `active` for everything
- [ ] Older milestone docs (e.g. `combat_movement_m1`) are `status: historical`
- [ ] Script is idempotent — running it twice does not duplicate frontmatter
- [ ] `last_verified: 2026-06-06` set on all `authority: P0` files
- [ ] `docs/README.md` updated to note that all docs have frontmatter and are browsable via Docusaurus

## Related Tickets
- TCK-20260606-DOCSITE-SCHEMA (dependency — schema must be defined first)
- TCK-20260606-DOCSITE-REGISTRY (consumer)
- TCK-20260606-DOCSITE-INTEGRATION (consumer)

## Related Docs
- `docs/guidelines/frontmatter_schema.md` (to be created by SCHEMA ticket)
- `tickets/todos/PLAN-DOCSITE.md`

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/add_frontmatter_live.py` (new)
- `docs/**/*.md` (modified, not code changes)

## Assumptions / Open Questions
- `docs/engine/` classification heuristic: files with phase numbers in their name and no "contract" or "spec" in the name are treated as `historical`. Review output before committing.
- `last_verified` on authoritative files: set to today (`2026-06-06`). Future updates require manually bumping this when content is reviewed.
- Performance reports in `docs/performance/` are date-stamped historical records — classify as `status: historical`, `authority: P2`. The `optimization_architecture.md` is `active P1`.

## Implementation Notes

Wrote `tools/add_frontmatter_live.py` following the archive script pattern. The script uses a
`UNIFORM_MAP` for 9 directories where all files get identical classification, and `HEURISTIC_FNS`
for 5 directories (engine, combat, observability, performance, test_coverage) where per-filename
regex/stem logic determines status/authority. Three loose files at `docs/` root are handled via
an explicit `LOOSE_FILES` dict keyed by path string.

Engine historical pattern (`ENGINE_HISTORICAL_PAT`) catches phase packages, milestone test matrices,
replacement/legacy ledger docs, sweep/inventory/freeze docs, and ephemeral build artifacts. It uses
`phase\d` (digit required) so structural docs like `phase_dependency_map.md` and
`phase_allocation_map.md` correctly resolve as `active`.

Actual file count: 247 (244 across 14 subdirs + 3 loose). All 247 validated by
`tools/validate_frontmatter.py` with zero violations. Second run confirmed 0 modified / 247 skipped.

## Test Summary

`tests/tools/test_add_frontmatter_live.py` — 109 tests, all passing.

Groups: classify_engine historical (22 cases), classify_engine active (17 cases), classify_combat (9),
classify_observability (8), classify_performance (10), classify_test_coverage (4), has_frontmatter (4),
build_frontmatter (6), process_file (5), idempotency (4), get_fields directory routing (21).

## Files Changed

- `tools/add_frontmatter_live.py` (new)
- `tests/tools/test_add_frontmatter_live.py` (new)
- `docs/README.md` (frontmatter + browsability note)
- `docs/**/*.md` — 246 additional files received frontmatter prepend

## Completion Summary

Applied frontmatter to 247 live docs/ markdown files via tools/add_frontmatter_live.py; 0 validator violations; 109 tests pass. Docs/README.md updated with Docusaurus browsability note.
