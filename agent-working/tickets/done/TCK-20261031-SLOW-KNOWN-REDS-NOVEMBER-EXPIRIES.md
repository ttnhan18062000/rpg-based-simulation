---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261031-SLOW-KNOWN-REDS-NOVEMBER-EXPIRIES
phase: done
date: 2026-10-31
tags: [testing]
---

# TCK-20261031-SLOW-KNOWN-REDS-NOVEMBER-EXPIRIES

## Title
Five slow_known_reds entries expiring 2026-11-15 are settled: three arena entries retired, behavioral_5k renewed to 12-15, the hero_guild exact-id entry renewed to 11-29

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Five entries in tools/test_architecture/slow_known_reds.yaml expire on 2026-11-15 and were outside the owner's 12-entry re-date (#715 6540197059). lead-planner-u24 relayed the question from the ubuntu lead; rpg-planner gave its status.
- Renew behavioral_5k to 2026-12-15: owner yes, #715 6544659163. The rebaseline waits for the SURV-07 repairs.
- Renew hero_guild to 2026-11-29: owner yes, #715 6544745270. It reads a held row under the same ticket as the 12 re-dated entries, so it expires with them.
- Retire the 3 arena entries: testing's change. TCK-20261014-ARENA-GOLD-ASSERTIONS-PREDATE-THE-536-TREASURY-RULES is done and its Completion Summary leaves this retirement to testing.

## Scope
The five entries above, the hero_guild date pin, and one test that the fixed arena tests are unowned.

## Out of Scope
- The 12 re-dated entries (ubuntu's rpg-ubuntu-slow-reds-expiry-redate).
- The selfmodel_probe entry: it sits on ubuntu's rpg-ubuntu-simq-anchor-bisect-impl, and only one branch may carry it.
- tests.arena.test_arena_stress::test_arena_stress_50v50, which belongs to another ticket.

## Acceptance Criteria
- [x] AC1: the three arena entries are gone; only expires_on changes on behavioral_5k and hero_guild.
- [x] AC2: the arena tests pass on main.
- [x] AC3: test_slow_regression_report.py and test_known_reds.py pass.

## Related Tickets
- TCK-20261014-ARENA-GOLD-ASSERTIONS-PREDATE-THE-536-TREASURY-RULES
- TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS
- TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- tools/test_architecture/slow_known_reds.yaml
- tests/unit/tools/test_slow_regression_report.py

## Assumptions / Open Questions
- hero_guild staying red is inferred from its held row and from one held-rows red in slow runs 41186264369, 41117211368 and 41029975115; the test was not rerun here.

## Implementation Notes
tests.arena.test_arena_quests::test_arena_quest_progression named a test that no longer exists; it was split into three.

## Test Summary
test_slow_regression_report.py + test_known_reds.py: 125 passed in 0.81s. tests/arena quests + regional_control: 5 passed in 6.87s.

## Files Changed
- tools/test_architecture/slow_known_reds.yaml
- tests/unit/tools/test_slow_regression_report.py

## Completion Summary
Arena retired; behavioral_5k renewed to 2026-12-15; hero_guild renewed to 2026-11-29. None of the arena tests failed in the three slow runs above.
