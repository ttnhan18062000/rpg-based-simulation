---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING

Written at closure.

- Roadmap §4.5 is a by-failure-class triage table with no per-domain owner table. The existing ownership map
  (`architecture_design_notes.md` §3.1) already has a social row, so the owner-routing row is that row,
  updated (reviewer decision, 2026-10-03). `regression_policy.md` §13.4 routes test-found defects through the map.
- `pytest-cov` is not installed; `coverage.py` 7.16.1 is (pinned in `requirements.txt`), so coverage was run with `coverage run`.
- 20 files outside `tests/unit/social` import `social_systems`; several test other components (combat ecology,
  strategic contracts, party-related engine and observability tests), so the import search over-selects by subject.
- `guilds.py` (in the social directory) is imported by `src/systems/guild_system.py`, an ownership-map Quests / guild file.
- The only kernel-running `tests/unit/social` file is `test_multi_hero.py` (G3 relevance, and a placement candidate).

Docs to update: `docs/testing/social_test_report_2026-10-03.md` (new), `docs/plans/test_architecture/reference/architecture_design_notes.md` (one row).
