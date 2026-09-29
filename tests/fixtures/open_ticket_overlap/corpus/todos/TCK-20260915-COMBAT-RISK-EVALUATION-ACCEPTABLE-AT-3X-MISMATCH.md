---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH
phase: open
date: 2026-09-15
tags: [combat]
---

# TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH

## Title
`CombatPostureSelector`'s own risk evaluation judged a 3.4x combat-stat mismatch (35hp/8atk vs
120hp/24atk) as `risk_eval.acceptable`, producing posture `"skirmish"` rather than a risk-rejected
posture, at first contact — took ~200 ticks to reach `"avoid"` in a separate, earlier run of the
same pairing

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found while building and running the first scenario for
`TCK-20260915-MECHANIC-VERIFICATION-SCENARIOS` (`tests/mechanic_scenarios/
test_combat_judgement_withdrawal.py`) — a real, compiled, catalog-driven pairing:
`goblin_scout` (hp=35, atk=8, def=2) vs `orc_warchief` (hp=120, atk=24, def=8), a genuine,
catalog-authored mismatch (`faction_relationships.yaml`'s `goblin_warband -> orc_clan`
relationship is literally named `"weaker_rival_fear"`).

**At first contact, `CombatPostureSelector.select()` (`src/domains/combat_engagement/selector.py`)
classified the goblin's own assessment as `"skirmish"` — a risk-*accepted* posture.** Per the
selector's own branch structure (confirmed by direct read this session, in the sibling
investigation): `"skirmish"` only fires when `risk_eval.acceptable` is already `True` — meaning
the risk evaluation itself, not just the resulting posture label, judged a 35hp/8atk attacker's
odds against a 120hp/24atk opponent (a ~3.4x mismatch on both dealt and received damage
potential) as an acceptable fight to be in. In a separate, earlier, non-adjacent run of the same
two archetypes (2000+ ticks, not forced to melee range), the goblin's posture did not shift to
`"avoid"` (a risk-rejected posture) until roughly tick 200+.

**Two candidate explanations, not yet distinguished**:
1. An "optimistic first-contact, calibrates down with information" read, consistent with
   `docs/mechanics/04_strategic_cognition.md` §13's own framing (uncertainty is maximal at
   parity, estimates calibrate as information accrues) — plausible, but §13 also implies the gap
   should be *easy* to read correctly at a spread this large, which cuts the other way.
2. A real defect in the risk/capability-estimate computation
   (`CapabilityEstimateService.estimate()`, referenced from `src/engine/tactical.py`'s own
   `target_score()` and presumably feeding `CombatPostureSelector`'s own risk evaluation) —
   systematically under-weighting a large, already-known stat gap rather than correctly reading
   it from the start.

If candidate 1 is the real explanation, taking ~200 ticks to notice an opponent four times one's
own combat capability is itself worth naming as a finding, not a fully satisfying answer on its
own.

## Scope
- Trace `risk_eval.acceptable`'s own computation (likely inside `CombatPostureSelector` or a
  service it calls) to determine what inputs it weighs and how a 3.4x hp/atk mismatch produces
  `acceptable=True` at first contact.
- Determine whether `CapabilityEstimateService.estimate()`'s own inputs (real stats vs. some
  uncertainty-weighted/partial-information model) explain the initial optimism, and if so,
  whether the calibration rate (~200 ticks to reach `avoid` in the sampled run) is itself
  intentional pacing or an unintended side effect of how confidence accrues.
- Propose (not build without review) whether this is working as designed, or whether the risk
  evaluation should weigh a stat gap this large more heavily from first contact.

## Out of Scope
- The posture-veto gate itself (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-
  EXECUTION`, already closed) — that mechanism's own correctness was independently confirmed via
  this same scenario's differential test (posture=`"avoid"` -> attack withheld; no posture
  recorded -> attack proceeds), and is not in question here.
- Any change to the `goblin_scout`/`orc_warchief` archetype stats themselves.

## Acceptance Criteria
- A real, evidence-backed explanation for why the risk evaluation reads a 3.4x mismatch as
  acceptable at first contact.
- If a defect: a scoped, reviewed fix proposal (not built without review).
- If working as designed: documented as such, with the calibration-rate observation (~200 ticks)
  named explicitly rather than left implicit.

## Related Tickets
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` (the gate this finding is
  explicitly distinct from — that mechanism's correctness is not in question)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` §13 (the spec this finding tests against)
- `docs/plans/mechanic_verification_scenarios_proposal.md` (the design this finding was surfaced
  building the first scenario for)
- `tests/mechanic_scenarios/test_combat_judgement_withdrawal.py` (the scenario itself)

## Related Stored Artifacts
_(none yet — filed as a finding, not yet investigated)_

## Related Code Areas
- `src/domains/combat_engagement/selector.py` (`CombatPostureSelector.select()`)
- `src/engine/tactical.py` (`CapabilityEstimateService.estimate()` usage, `target_score()`)
- `data/content/entities/stat_profiles.yaml` (`goblin_scout_base`, `warlord_base`)

## Assumptions / Open Questions
- Which of the two candidate explanations (optimistic-first-contact-by-design vs. a real
  under-weighting defect) is correct is not yet known — check before assuming either.

## Implementation Notes
_(none — filed as a finding, not yet investigated)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_
