---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261014-NAME-LITERALS-IN-SRC-SCAN
phase: done
date: 2026-10-14
tags: []
---

# TCK-20261014-NAME-LITERALS-IN-SRC-SCAN

## Title
Scan src/ for string literals that name content ids (D56: code reads no names), and keep the scan as the M1 "no name checks" probe.

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
rpg-planner, for the designer: before route weighting, list every string literal in src/ that is compared against, or used to look up, a content id of any kind (terrain, species, role, item, place, building, faction), in any letter case. Read-only; fix nothing.

## Scope
- An AST script, `tools/name_literal_scan.py`, that loads the content catalogs and the world-declared ids and walks src/ for equality and `in` tests, subscript keys, `.get` keys and defaults, match arms, dict keys, call arguments and parameter defaults.
- One table of findings in stored artifacts.

## Out of Scope
- Fixing any finding.
- Tests and logging/presenter strings.

## Acceptance Criteria
- Each finding has file:line, the literal, the catalog, whether the id exists as written (exact, case, missing), decision or default role, and whether the enclosing function has callers.
- The script is kept in tools/ with a test.

## Related Tickets
D72 (terrain cost in content), the cover and high-ground ticket (TCK-20261014-TERRAIN-DECLARES-COVER-AND-HIGH-GROUND-IN-CONTENT).

## Related Docs
None.

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261014-NAME-LITERALS-IN-SRC-SCAN/ (plan, investigation with the table, test_plan).

## Related Code Areas
tools/name_literal_scan.py; src/ (read only).

## Assumptions / Open Questions
The scan is lexical: it reports candidates. "Missing" and "case" rows are dead against content as written; "exact" rows include generic words that happen to be ids of a small catalog.

## Implementation Notes
`tools/name_literal_scan.py` loads the catalogs from `CatalogRepository` plus ids declared in data/worlds, parses every src/**/*.py, and classifies each literal by exact, case-insensitive and hint-based match. Hints come from words in the compared-with expression (terrain, species, role, region/place, faction, ...); an entity `.kind` counts as a species id. Logging calls, docstrings, f-strings and raise messages are skipped; src/api and src/rendering are counted only.

## Test Summary
`tests/unit/tools/test_name_literal_scan.py` (2 tests) on a sample source.

## Files Changed
tools/name_literal_scan.py; tests/unit/tools/test_name_literal_scan.py; this ticket and its stored artifacts.

## Completion Summary
623 findings on rpg-next 3696d0402 (case 91, exact 364, missing 112, other-catalog 56), delivered as the investigation table. Nothing fixed.
