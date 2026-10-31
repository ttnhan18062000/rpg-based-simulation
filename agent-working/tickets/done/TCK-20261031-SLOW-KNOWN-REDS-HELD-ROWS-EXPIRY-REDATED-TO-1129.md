---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261031-SLOW-KNOWN-REDS-HELD-ROWS-EXPIRY-REDATED-TO-1129
phase: done
date: 2026-10-31
tags: [testing]
---

# TCK-20261031-SLOW-KNOWN-REDS-HELD-ROWS-EXPIRY-REDATED-TO-1129

## Title
The 12 whole-key SimQ held-row slow_known_reds entries are re-dated from 2026-11-15 to 2026-11-29, with nothing else changed

## Status
DONE

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

Added by the leads while the ticket was open:
- The known-red entry for tests.unit.worldassembly.test_corpus_diversity::test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability (ticket TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT), added exactly as written on origin/rpg-ubuntu-simq-anchor-bisect-impl (approval #715 6519647030). Owner #715 6544761818 then moved its expires_on to 2026-11-29 and replaced the cause clause of its note; lead-planner set the wording. Nothing else in the entry changed.
- The ticket TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT, copied from origin/rpg-ubuntu-simq-anchor-bisect-impl at d2ed6c8c2 into agent-working/tickets/todos/, text unchanged. Its staging evidence is at that commit and lands with the SimQ PR.

## Out of Scope
- The other 5 entries that expire on 2026-11-15, which stay as they are: tests.regression.test_behavioral_5k* (TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS); three arena entries (tests.arena.test_arena_quests::test_arena_quest_progression, tests.arena.test_arena_regional_control::test_arena_regional_control, tests.arena.test_arena_regional_control::test_arena_conquest_and_debuff, all TCK-20261014-ARENA-GOLD-ASSERTIONS-PREDATE-THE-536-TREASURY-RULES); and the exact-id entry tests.unit.worldassembly.test_corpus_diversity::test_hero_guild_routing_seed42_1000t_cognition_grade_stability, also under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE, whose date is pinned by tests/unit/tools/test_slow_regression_report.py.
- The per-entry notes, owners and added_on dates, which stay unchanged.

## Acceptance Criteria
- [x] AC1: the yaml diff is the 12 expires_on lines plus the added selfmodel entry (7 lines, with its expiry and note changed as above).
- [x] AC2: tests/unit/tools/test_known_reds.py and tests/unit/tools/test_slow_regression_report.py pass in full.
- [x] AC3: the 5 other 2026-11-15 entries are untouched.

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
`pytest tests/unit/tools/test_known_reds.py tests/unit/tools/test_slow_regression_report.py tests/tools/test_agent_working_paths_guard.py`: 135 passed (cores 4-5). `validate_frontmatter.py --content-type ticket` passes on this ticket and on the copied SimQ ticket.

## Files Changed
- tools/test_architecture/slow_known_reds.yaml (12 expires_on lines; 7-line selfmodel entry added, expiry and note updated)
- agent-working/tickets/todos/TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT.md (copied, unchanged)

## Completion Summary
The 12 whole-key held-row entries now expire on 2026-11-29 (#715 6540197059, 6544563421). The selfmodel known-red entry was added with expiry 2026-11-29 and the updated cause clause (#715 6519647030, 6544761818). The other 5 entries expiring on 2026-11-15 are unchanged.
