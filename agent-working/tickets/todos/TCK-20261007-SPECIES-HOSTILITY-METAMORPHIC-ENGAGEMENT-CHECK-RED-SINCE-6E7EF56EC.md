---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC
phase: open
date: 2026-10-07
tags: [combat, regression]
---

# TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC

## Title
The species-hostility metamorphic check went red between bc4f7553c and 6e7ef56ec: making wolf-to-human hostility "high" now lowers the combat engagement rate compared with leaving it undeclared.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Reported by testing-planner. `tests/integration/lab/test_species_relations_metamorphic_validation.py::test_species_hostility_increase_does_not_decrease_combat_engagement_rate` failed in Slow regression run 37604139091, at main `6e7ef56ec`. It passed in run 37551894246, at `bc4f7553c`. The test has not changed since #123. It runs world `unit_faction_tension` (a human town_council and a wolf wild_beast_pack) on seeds 201-203 for 200 ticks. The relation it checks is that declaring wolf-to-human hostility `high` must not lower `combat_engagement_rate` compared with having no wolf-to-human entry.

rpg-planner's ruling (2026-10-07): **the metamorphic relation remains intended law.** Declared hostility is an input to permission and to the decision to engage. #395 made permission symmetric (CONFLICT-03); it did not make hostility irrelevant. Raising declared hostility must never reduce engagement. The bisect decides the class:
- **(b):** a real regression, for example #395 treating "no entry" as more permissive than "high", or #398's retreat rule interacting with it. Fix the code.
- **(a):** the relation holds in law, but three seeds at 200 ticks is too small a sample, so an unrelated behaviour change flipped a near-tie. Then strengthen the test's sample, with its derivation recorded, rather than loosening the relation. That change goes through testing's review (Epic C criterion 4: Bible and ledger first).

The src merges in the range are #394, #395, #398, #403, #404 and #406.

## Scope
1. Bisect the onset over the range to one merge, using the test's own seeds. The test rewrites `data/content/social/species_relations.yaml` in place, so run it only in a private worktree.
2. Report engagement rate per seed, for the baseline and for `high`, before and after the onset. Report the mechanism: which path makes `high` engage less (permission, target choice, retreat or spawn).
3. Fix as (b), or strengthen the test as (a), per the ruling above. If CONFLICT-03 or COMB legality needs a clarification, route it through rpg-planner to the designer.

## Out of Scope
- Changing the metamorphic relation's direction.
- Other species-relation metamorphic tests unless they share the cause.

## Acceptance Criteria
- [ ] Onset bisected to one PR, with the mechanism explained.
- [ ] Classified (a) or (b) with that evidence.
- [ ] The test passes on all 3 seeds on the landing base, and the slow known-reds entry is removed.

## Related Tickets
- `TCK-20261006-...` from #395 (symmetric attack permission) and AGENCY-07 #398, both in the onset range.

## Related Docs
- `docs/world_rules/` CONFLICT-03; `docs/mechanics/02_combat_laws.md` §7.

## Related Stored Artifacts
- _(none yet)_

## Related Code Areas
- `src/engine/legality.py`, `src/ai/tactical_threat.py`, `data/content/social/species_relations.yaml`
- `tests/integration/lab/test_species_relations_metamorphic_validation.py`

## Assumptions / Open Questions
- Is the test's sample (3 seeds, 200 ticks) too small to be stable? The bisect answers this.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
