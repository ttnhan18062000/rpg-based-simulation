---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261031-SLOW-KNOWN-REDS-HELD-ROWS-EXPIRY-REDATED-TO-1129
phase: open
date: 2026-10-31
tags: [testing]
---

# TCK-20261031-SLOW-KNOWN-REDS-HELD-ROWS-EXPIRY-REDATED-TO-1129

## Title
The 12 whole-key SimQ held-row slow_known_reds entries are re-dated from 2026-11-15 to 2026-11-29, with nothing else changed

## Status
INPROGRESS

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Owner decision on #715: issuecomment-6540197059 (the date move for the 12 whole-key entries under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE) and issuecomment-6544563421 (the re-date goes in its own PR). rpg-planner-ubuntu asked for it. The entries expire on 2026-11-15, so this must merge before then.

## Scope
In tools/test_architecture/slow_known_reds.yaml, the 12 entries whose ticket is TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE and whose match is a whole-key grade test: expires_on "2026-11-15" becomes "2026-11-29". Twelve single-line changes.

## Out of Scope
- The other 5 entries that expire on 2026-11-15, which stay as they are: tests.regression.test_behavioral_5k* (TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS); three arena entries (tests.arena.test_arena_quests::test_arena_quest_progression, tests.arena.test_arena_regional_control::test_arena_regional_control, tests.arena.test_arena_regional_control::test_arena_conquest_and_debuff, all TCK-20261014-ARENA-GOLD-ASSERTIONS-PREDATE-THE-536-TREASURY-RULES); and the exact-id entry tests.unit.worldassembly.test_corpus_diversity::test_hero_guild_routing_seed42_1000t_cognition_grade_stability, also under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE, whose date is pinned by tests/unit/tools/test_slow_regression_report.py.
- The per-entry notes, owners and added_on dates, which stay unchanged.

## Acceptance Criteria
- [ ] AC1: the yaml diff is exactly the 12 expires_on lines.
- [ ] AC2: tests/unit/tools/test_known_reds.py and tests/unit/tools/test_slow_regression_report.py pass in full.
- [ ] AC3: the 5 other 2026-11-15 entries are untouched.

## Related Tickets
- TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE (owner of the entries, rpg-planner)
- TCK-20261031-N14-KNOWN-V3-ENTRY-RENEWED-TO-1130 (the same kind of one-line renewal)

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- tools/test_architecture/slow_known_reds.yaml

## Assumptions / Open Questions
- The rpg_gate_known.yaml renewal (#797) is a different file, so there is no overlap.

## Implementation Notes
Changed with a per-entry script (match on ticket and match key), not a bulk replace. Checked that exactly 12 lines changed and the other 5 are untouched.

## Test Summary

## Files Changed
- tools/test_architecture/slow_known_reds.yaml (12 lines)

## Completion Summary
