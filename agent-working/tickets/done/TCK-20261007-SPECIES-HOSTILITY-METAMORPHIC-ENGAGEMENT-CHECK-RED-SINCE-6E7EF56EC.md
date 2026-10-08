---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC
phase: done
date: 2026-10-07
tags: [combat, regression]
---

# TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC

## Title
The species-hostility metamorphic check went red between bc4f7553c and 6e7ef56ec: making wolf-to-human hostility "high" now lowers the combat engagement rate compared with leaving it undeclared.

## Status
DONE

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
- [x] (testing-implementer) The rescoped test (same assertion; N and the horizon changed, derivation in the docstring) passes on the landing base, and the slow known-reds entry is removed.

## Related Tickets
- `TCK-20261006-...` from #395 (symmetric attack permission) and AGENCY-07 #398, both in the onset range.

## Related Docs
- `docs/world_rules/` CONFLICT-03; `docs/mechanics/02_combat_laws.md` §7.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261007-SPECIES-HOSTILITY-METAMORPHIC-ENGAGEMENT-CHECK-RED-SINCE-6E7EF56EC/` (`plan.md`, `investigation.md`, `test_plan.md`)

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

**Ruling on the observable (rpg-planner, 2026-10-07, relayed by testing-planner; verbatim).** "The relation 'raising declared hostility between two factions never lowers their combat engagement' is a claim about pairs that meet. It is observed faithfully by the unchanged metric (combat engagements, baseline vs high, pooled over seeds) on a setup where the two groups come into contact within the horizon. A run in which they never meet carries no evidence either way. Rule (a): measure on a contact-rich layout of the same world content. Use the same factions, the same faction-level declarations and the same species mutation, with the wolf pack placed within perception range of the town at spawn, or a dedicated lab world declared the same way. The assertion keeps its exact form: pooled high >= pooled baseline, no tolerance band. — rpg-planner, 2026-10-07" Option (b), a per-contact rate, is rejected because its denominator moves with hostility.

**Rescope measurements (testing-implementer, 2026-10-07; private worktree, the test's own procedure with per-seed counts kept; seed lists fixed before measuring; 6-core workstation).** All at `ae3352361ea77ee3545612d1de3748be19ac321e` unless stated.
- **Unpinned, the evidence for the pin.** Seeds 301-340 x 200t: baseline 122, high 141, mean per-seed diff +0.475, SD 1.81, z 1.66, wall time 949 s. Lane B's run of the same configuration at the same SHA gave 115 vs 140 (z about 2.6), so the same seeds at the same SHA give different counts: the lab path is not deterministic unpinned (the governor degrades under host load, the parked cause in TCK-20260822). Seeds 301-320 x 400t unpinned: 104 vs 138, +1.70, SD 5.55, z 1.37, wall time 892 s.
- **Pinned governor (test-only).** `Kernel.__init__` imports its default `ResourceGovernor` lazily from `src.engine.governor` (kernel.py:121), and the lab path builds `Kernel` without one (src/lab/orchestrator.py:219/233). A test-scoped monkeypatch to a pinned-NORMAL subclass (mode fixed, `force_mode` a no-op, as `_PinnedNormalGovernor` in tests/integration/campaigns/test_catalog_entity_spawn_wiring.py) reaches every lab run: 80 pinned governors for 40 seeds x 2 arms. No src change.
- **Pinned, original layout.** Seeds 301-340 x 200t, run twice: identical per-seed counts (deterministic). Baseline 122, high 141, mean diff +0.475, SD 2.37, SE 0.376, z 1.26. Per-seed diffs: [-5, -4, -2, -1, 0 x26, +1 x4, +3, +3, +5, +6, +10]; 10/40 seeds have 0 engagements in both arms. Smallest N for z >= 2.33: about 136 seeds (about 63 min); rejected. Seeds 301-320 x 500t pinned: 98 vs 106, +0.40, SD 2.23, z 0.80, 4/20 zero in both arms, wall time 1437 s; rejected.
- **Pinned, contact-rich layout (ruling (a)).** A test-scoped override of `WorldRepository.load_world` for `unit_faction_tension` only: the `wolf_den` region's bounds become (41,30,48,40), next to `hometown` (10,10,40,40), and its `wolf_den_nest` place moves to (44,35). Everything else is unchanged and still goes through `WorldValidator` and the compiler: factions, faction-level declarations, populations and the species mutation. Placement is decided only by `PopulationSpec.spawn_region` (a uniform draw inside the region's bounds). The wolves are outside `hometown`, and no leash is set (the compiler sets no `home_position` / `leash_radius`; the default 0 means none). Seeds 301-340 x 200t, run twice: identical. Baseline 73, high 653, mean diff +14.5, SD 8.54, SE 1.35, z 10.7. No negative seed (diffs 0..31); 2/40 zero in both arms; baseline > 0 on 20/40 seeds, high > 0 on 38/40. Wall time 1012 s and 1030 s.

**Rescope landed (testing-implementer, 2026-10-07/08).** `tests/integration/lab/test_species_relations_metamorphic_validation.py` now pins the governor (a test-scoped monkeypatch of `src.engine.governor.ResourceGovernor` to a pinned-NORMAL subclass), uses the contact-rich layout (a test-scoped `WorldRepository.load_world` override: `wolf_den` (41,30,48,40), nest (44,35)), runs seeds 301-310 x 200t (fixed in advance), and has a non-vacuity guard: pooled baseline > 0 and at least 2 baseline seeds with an engagement (measured 4 of 10). The guard is not an effect check. The assertion form is unchanged. Two runs at `2a9b41b30472562633a04081d5f68a9c7f89d63d` both passed in 250.5 s with identical per-seed counts: baseline {301:0, 302:4, 303:3, 304:0, 305:4, 306:0, 307:0, 308:0, 309:0, 310:6} = 17, high {301:0, 302:19, 303:14, 304:22, 305:20, 306:6, 307:1, 308:11, 309:9, 310:35} = 137 (mean +12.0, SD 8.98, z 4.23). Reviewed and approved by testing-planner.
- **Epic C criterion 4: first MET-clean exercise.** The expectation change (the test's sample, layout and governor) was preceded by its authority in an earlier commit: rpg-planner's ruling (a), recorded verbatim with all measurements in this ticket in `f78c547a6`, before the test commit `2a9b41b30`. For testing-planner to add to the Epic C record.
- **Warning, pre-existing:** the test rewrites `data/content/social/species_relations.yaml` in place (restored and asserted in `finally`). Run it only in a private worktree, never alongside another session using the same checkout.
- **Watch item (testing-planner):** `_PinnedNormalGovernor` now exists in two test files (this one and `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`); extract a shared helper at the third use.

## Test Summary
The rescoped test passed twice at `2a9b41b30` with identical per-seed counts (17 vs 137; 250.5 s each, `--resource-budget large`). `data/content/social/species_relations.yaml` is identical to main afterwards. `tests/unit/tools/test_slow_regression_report.py` and the known-reds lint pass after the species entry is removed (50 passed). Landing base: after merging origin/main `33360e617` (merge commit `286316f43`), the test passed again in 284.7 s and 290.5 s with the same per-seed counts (baseline 17, high 137; 4 of 10 baseline seeds non-zero); `species_relations.yaml` unchanged afterwards; the 20 run directories were cleaned by run id.

## Files Changed
- `tests/integration/lab/test_species_relations_metamorphic_validation.py`: pinned governor, contact-rich layout, seeds 301-310, non-vacuity guard, docstring derivation
- `tools/test_architecture/slow_known_reds.yaml`: species-hostility entry removed
- this ticket and its stored artifacts (`plan.md`, `investigation.md`, `test_plan.md`)

## Completion Summary
Class (a), rescoped by testing. The relation is unchanged and holds: on a contact-rich layout of the same world content (rpg-planner's ruling (a)), with a pinned governor, high hostility gives 137 engagements against 17 in the baseline over seeds 301-310 (z 4.23; z 10.7 over 301-340), deterministic at a SHA. The stock layout could not show it at any affordable sample size, because wolves and humans rarely meet within 200 ticks. The known-reds entry is removed. No src, data or anchor change. First MET-clean exercise of Epic C criterion 4.
