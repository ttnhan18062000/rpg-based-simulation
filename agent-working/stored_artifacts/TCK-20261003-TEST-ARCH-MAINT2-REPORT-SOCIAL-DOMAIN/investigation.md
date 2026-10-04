---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261003-TEST-ARCH-MAINT2-REPORT-SOCIAL-DOMAIN

## Context scan

`search_docs`, graphify and `tools/knowledge_search.py` were unavailable all session; the scan is targeted reads
of `tools/test_architecture/core_rpg_report.py`, `tests/unit/tools/test_core_rpg_report.py`,
`docs/plans/test_architecture/reference/architecture_design_notes.md` §3.1 and a read-only probe over the real
test tree.

## Findings

- The tool lists social only through `_UNOWNED_DOMAIN_IMPORT_PREFIXES` (`src.systems.social_systems.party*`).
  `DOMAIN_IMPORT_PREFIXES` is summed into `_GAMEPLAY_IMPORT_PREFIXES` (line 76) and also feeds
  `impact_report.py`, `marker_check.py` and the `domain` marker vocabulary, so a social key there changes
  the core-RPG candidate set by construction.
- §3.1 social row: `src/systems/social_systems/`, `party*.py` stays in the Party row, `memory.py` excluded as
  dormant (`TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`).
- Probe at `origin/main` `f76fda2cc03dc32481f66c6ba18d980ed28bdff2`, 1600 test files, current classes
  not-core-rpg 1396, uncertain 119, classified 78, unowned-domain 7 (core-RPG candidates 197):
  design A (inside gameplay prefixes) gives 236 candidates and moves five party files out of the Party row
  (rejected); design B (exclusive class) gives 197 but not-core-rpg 1364; design C (non-exclusive signal) moves
  no existing count and finds 37 social-signal files (not-core-rpg 32, uncertain 2, classified 1,
  unowned-domain 2), 1 party-and-social file, 2 memory-only files, 0 bare-package-only files.
- Existing pins: `tests/unit/tools/test_core_rpg_report.py:469` pins `schema_version == 2`;
  `test_fixed_states_and_required_limits` requires `unowned-domain` and `not a gate` in the limits;
  `impact_report.py` has its own `SCHEMA_VERSION = 1`.
