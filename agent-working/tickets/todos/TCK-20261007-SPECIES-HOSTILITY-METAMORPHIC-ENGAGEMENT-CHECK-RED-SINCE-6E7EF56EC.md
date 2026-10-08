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

(Original framing, now resolved as class (a): see Scope and Implementation Notes.) The src merges in the range are #394, #395, #398, #403, #404 and #406.

## Scope
**Owner: testing-implementer** (reassigned 2026-10-07 from rpg-implementer-2 after the bisect; the slow-job budget and the test's statistics are testing's). **Known-red expiry stays 2026-10-28.**
**Class (a); no code or CONFLICT-03 change (ruled by rpg-planner, 2026-10-07).** The bisect (Implementation Notes) is done.
The remaining work is the rescope only: keep the exact assertion (`monotonic_non_decreasing` on `combat_engagement_rate`, baseline against high) and change only the number of seeds N and the horizon (ticks). Derive N and the horizon per `docs/testing/regression_policy.md` and record the derivation in the test docstring; the evidence to start from is in Implementation Notes (about 40 seeds gives +0.625 per seed at about 2.6 sigma; the 3-seed false-fail rate is about 1 in 4).

## Out of Scope
- Changing the metamorphic relation's direction.
- Other species-relation metamorphic tests unless they share the cause.

## Acceptance Criteria
- [x] Onset bisected (#395 shrank the effect; no code regression), with the mechanism explained.
- [x] Classified (a) with that evidence (40-seed result above).
- [ ] (testing-implementer) The rescoped test (same assertion; N and the horizon changed, derivation in the docstring) passes on the landing base, and the slow known-reds entry is removed.

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
**Bisect and classification (rpg-implementer-2, 2026-10-07; rpg-planner accepted class (a)).** Measured in a private detached worktree with the test's own arms (`unit_faction_tension`, 200 ticks, baseline = no wolf/human species entry, high = declared "high"), counting `combat_engagement_started`. Probe scripts are in the implementer's scratchpad (not committed).

Seeds 201-203 (the test's seeds), baseline vs high:
| commit | baseline | high | passes |
|---|---|---|---|
| bc4f7553c | 11 | 21 | yes |
| #394 | 11 | 24 | yes |
| #395 | 19 | 28 | yes |
| #398 | 27 | 23 | no |
| #403 | 24 | 30 | yes |
| #404 | 25 | 24 | no |
| #406 | 26 | 27 | yes |
| main ae3352361 | 27 | 24 | no (reproduced locally) |

**Onset and mechanism.** #395 (attack permission symmetric, CONFLICT-03) is where the effect shrank, not a code regression of the relation's direction. Before #395 "high" engaged about twice as often as the baseline (+10 to +13 per 3 seeds), because permission was one-directional. After it the gap is about zero and the check's result is decided by noise (#398 only looks like the first fail because its baseline rose).
The declared/undeclared boundary does not apply. Both factions already declare each other at the faction level in `faction_relationships.yaml` (`town_to_wild_beasts` medium_contextual, `wild_beasts_to_town` low_base_contextual), so the baseline is declared on both sides and the legacy fallback is never reached (`LegalityServiceV2._declares` ignores species entries). At the baseline `_attack_permitted` already gives hostile for town to wolf (idle and engaged) and wolf to town once engaged. The "high" mutation only makes wolf to town hostile while idle, which adds little engagement once permission is symmetric.

**Does the relation still hold? Yes.** First, seeds 204-215 (12 seeds): baseline 55, high 40 (mixed-sign per-seed differences: +6, -5, -7, +1, -6, -5, +1, the rest 0; six seeds have 0 in both arms); that was noise. Then seeds 301-340 (40 seeds) at main: baseline 115, high 140; mean per-seed difference +0.625, standard error 0.24 (about 2.6 sigma); 10 of the 40 seeds have 0 engagements in both arms. An earlier 12-seed run (seeds 204-215: baseline 55, high 40) was noise.
40-seed figure unpinned; testing re-run gave +0.475 (z 1.66); see the rescope. (The lab path's governor degrades under host load, TCK-20260822, so an unpinned single run is a sample, not a fact; the bisect table above is likewise unpinned.)
**Why the test flips.** The per-seed difference has a standard deviation of about 1.5, so a 3-seed sum has an expected gap of about +1.9 with a standard deviation of about 2.6, and the check fails by chance in about 1 run in 4.

**Disposition: class (a); no code or CONFLICT-03 change, ruled by rpg-planner 2026-10-07.** The test is underpowered and testing owns the rescope (sample size and slow-job budget: about 40 seeds takes about 20 minutes against 1). The rescope derivation must be recorded in the test docstring per `docs/testing/regression_policy.md`.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
