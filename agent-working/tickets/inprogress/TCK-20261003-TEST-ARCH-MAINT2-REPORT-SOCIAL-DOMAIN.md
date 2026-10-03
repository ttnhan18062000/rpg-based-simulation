---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN
phase: open
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN

## Title
Teach `core_rpg_report.py` the social domain as a reported, non-core signal

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary

Phase 2 C2 found that `tools/test_architecture/core_rpg_report.py` lists social code only as party
(`_UNOWNED_DOMAIN_IMPORT_PREFIXES`, the Party row). The §3.1 ownership-map row merged in #302 maps
`src/systems/social_systems/` as its own domain: `party*.py` stays in the Party row and `memory.py` is excluded
as dormant. Make the report classify social imports accordingly, **without silently changing the core-RPG
figures**, and record the social row once at the then-current `origin/main`.

## Scope

1. In `core_rpg_report.py`, add a social import signal: a module under `src.systems.social_systems` that is
   neither `party*` nor `memory`. The prefixes live in their own constant, **not** in `DOMAIN_IMPORT_PREFIXES`
   (see Implementation Notes: that dict feeds `_GAMEPLAY_IMPORT_PREFIXES`, `impact_report.py`,
   `marker_check.py` and the `domain` marker vocabulary).
2. Report social as a **separate, non-exclusive field**: files with the social signal, broken down by their
   existing class, plus the overlap and exclusion counts. The existing `class` values and counts do not move.
   "Own domain `social`" in the request means a **reported domain signal, not an exclusive `class`** (design
   C, chosen by test-architecture-reviewer at plan review of `38423a1151a0ee2c9f6d6de0a55ad67406d009d4`).
3. Bump `SCHEMA_VERSION` 2 to 3 (the JSON gains keys) and say what v3 added in a short note at the top of the
   module's docstring or schema comment. `impact_report.py` has its own `SCHEMA_VERSION = 1` and is unaffected.
4. Update the Party-row and the §3.1 sentence in `V0_LIMITS` so they say what the code now does.
5. Tests in `tests/unit/tools/test_core_rpg_report.py` only: signal present/absent, party excluded, memory
   excluded, parse-error stays `None`, an assertion for the new social keys, the existing schema test updated
   so it still checks the v2 renames, and **the invariance test** (the existing class counts of a fixture tree
   are identical with and without a social importer added).
6. Run the report once at the then-current `origin/main` (full SHA) and record the social row as a dated
   addendum in `docs/testing/social_test_report_2026-10-03.md` (that doc is the batch report the C2/C3/C4
   figures live in; `docs/testing/core_rpg_test_baseline_2026-09-30.md` is the report's own earlier output doc
   for the core-RPG baseline and is not edited).
7. `make knowledge-index-update` if any `docs/` file changes.

## Out of Scope

- Any `tests/` path outside `tests/unit/tools/`; any RPG test; any `src/` or `docs/parity_ledger/` change.
- Adding social to `DOMAIN_IMPORT_PREFIXES`, the `domain` marker vocabulary or `test_taxonomy.md` §10.
- Re-classifying any test file or changing a core-RPG denominator.
- A new tool or script; a new social domain batch (scale-out is paused).

## Acceptance Criteria

- [ ] `classify_file`'s `class` is byte-identical for every existing test file: the class counts at the
  measured SHA are unchanged (`not-core-rpg`, `uncertain`, `classified`, `unowned-domain`, `parse-error`).
- [ ] The social field is reported with the denominator (test files scanned), the by-class breakdown, the
  party-and-social overlap and the memory-only exclusion count; the Party row is unchanged.
- [ ] Tests cover the cases in Scope item 4 and pass; no other test file changes.
- [ ] The dated addendum records the social row with the full `origin/main` SHA and the exact command, and
  restates that the figures are execution/import evidence, not a gate.
- [ ] `git diff --name-only origin/main...HEAD` shows `tests/` paths only under `tests/unit/tools/`.

## Related Tickets

- `TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING` (done; found the gap)
- Siblings: `TCK-20261003-TEST-ARCH-MAINT2-ESCAPED-DEFECT-SEPTEMBER-COUNT`, `TCK-20261003-TEST-ARCH-MAINT2-EPIC-B-COST-ROW-304`

## Related Docs

- `docs/plans/test_architecture/reference/architecture_design_notes.md` §3.1 (social row, Party row)
- `docs/testing/social_test_report_2026-10-03.md`
- `docs/testing/test_taxonomy.md` §10 (read only)

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING/`

## Related Code Areas

- `tools/test_architecture/core_rpg_report.py`
- `tests/unit/tools/test_core_rpg_report.py`

## Assumptions / Open Questions

- Context scan: `search_docs`, graphify and `tools/knowledge_search.py` were unavailable all session; the scan
  is targeted reads and a read-only probe over the real test tree. Disclosed, not a gate.
- **Question for the reviewer:** "own domain `social`" is satisfied here as a reported domain signal, not as a
  new exclusive `class`. The alternative (an exclusive class) moves 32 files out of `not-core-rpg`. Which?
- Whether adding keys bumps `schema_version` 2 to 3 (the existing test pins `== 2`): proposed yes, because
  the JSON shape gains keys; the test is updated in the same change.

## Implementation Notes

Measured at `origin/main` `f76fda2cc03dc32481f66c6ba18d980ed28bdff2` (read-only probe over 1600 test files,
scratch script, nothing written to the repo). Current classes: not-core-rpg 1396, uncertain 119, classified 78,
unowned-domain 7 (core-RPG candidates = classified + uncertain = **197**).

| Design | Core-RPG candidates | Other effect | Verdict |
|---|---|---|---|
| A. social inside `_GAMEPLAY_IMPORT_PREFIXES` | 197 -> **236** | `unowned-domain` 7 -> 2: five party files also import non-party social and leave the Party row | rejected: changes the denominator and breaks "party* stays in the Party row" |
| B. exclusive class `social` (after the party check) | 197 (unchanged) | `not-core-rpg` 1396 -> 1364; 32 files move | possible; changes a published count |
| C. non-exclusive social signal field (proposed) | 197 (unchanged) | no existing count moves | proposed |

Under C, 37 files carry a social (non-party, non-memory) submodule import: not-core-rpg 32, uncertain 2,
classified 1, unowned-domain 2. One file imports both party and social code; two import `memory` only (excluded);
no file imports only the bare package. Rule used by the probe: a name that starts with
`src.systems.social_systems.` and is neither `party*` nor `memory`. The bare package name is not a signal on
its own, because `from pkg import x` adds both `pkg` and `pkg.x` to the import list.

## Test Summary

## Files Changed

## Completion Summary
