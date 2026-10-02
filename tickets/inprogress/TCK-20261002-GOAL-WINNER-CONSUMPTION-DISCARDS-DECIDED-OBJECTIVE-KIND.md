---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND
phase: open
date: 2026-10-02
tags: [strategy, cognition, combat]
---

# TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND

## Title
Goal-winner consumption hardcodes `kind="reach_location"` for every goal without a bespoke branch,
so a winning `COMBAT_ENGAGE` is dispatched as `MOVE_TO` instead of `ATTACK_TARGET` — the decision
layer's chosen action is silently replaced on the live path

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
This is the root cause that `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` identified and then
never filed a fix for. The epic has been idle 13 days; every link in its `SEQUENCE.md` is an
investigation, and there is no implementation ticket anywhere in the chain. Surfaced during the
2026-10-02 epic-staleness review and re-verified live on `origin/main` before filing.

`StrategicIntelligenceSystem`'s winner-consumption code (`src/systems/strategic_systems/intelligence.py`)
materialises a winning goal into a `ProjectState` + `ObjectiveState`. It has bespoke `elif` branches
per `GoalKind` — `SOCIAL_CONTRACT` (:1606-1617), region stabilization (:1643-1653),
`OCCUPATION_CHANGE` (:1678-1686) — and each of those reads its real objective kind out of
`best_candidate.metadata["obj_kind"]`, resolved by the scorer. Every other goal falls into the
generic `else` at **:1707-1714**, which hardcodes:

```python
obj = ObjectiveState(
    id=f"{cand_kind_str}_{best_candidate.target_id}",
    kind="reach_location",            # <-- never derived from best_candidate.kind
    target=best_candidate.target_id,
    target_position=best_candidate.target_pos,
    status=ObjectiveStatus.ACTIVE,
)
```

`GoalKind.COMBAT_ENGAGE` has no bespoke branch, and `CombatEngageScorer`
(`src/ai/goals/scorers.py:101-131`) sets **no metadata at all** — it returns only `utility`,
`target_id` (the nearest hostile's entity id) and `target_pos` (that hostile's position). So a
COMBAT_ENGAGE win becomes a `reach_location` objective aimed at the hostile.

**The consequence is exact, and it is not merely a mislabel.** `ObjectiveIntentResolver`
(`src/domains/adventure/resolver.py:58-64`) maps objective kind to action intent:

| objective kind | resolved action intent |
|---|---|
| `REACH_LOCATION` | `MOVE_TO` |
| `DEFEAT_ENEMY` | `ATTACK_TARGET` |

So the entity decides to engage, and the pipeline dispatches it to **walk toward** the enemy.
`ObjectiveKind.DEFEAT_ENEMY` is produced nowhere on this path — its only producer in `src/` is
`src/domains/adventure/mapper.py:37` (`RouteFamily.HUNT_WEAK_ENEMY`), an unrelated route-generation
path. The branch is dead by construction.

This matches, and now mechanises, the chain's recorded verdict: the decision layer does not fail to
choose combat — it chooses combat and the choice is discarded at dispatch. The epic measured the
decision-driven `ATTACK` path firing 0-2 times per 1000-2000 ticks while the incidental
opportunity-attack mechanic fired 181-2177 times.

**Why this is a hard bug and not a balance or parity issue** (per the user's 2026-10-02 direction):
it is on the live path, it runs in ordinary corpus play, and it produces wrong world truth — the
action the entity is recorded as having decided is not the action the engine executes. No flag gates
it and no dormancy protects it.

## Scope
1. Derive the objective kind from the winning candidate instead of hardcoding it, in the generic
   `else` branch at `intelligence.py:1707-1714`. Preferred shape, to be confirmed in
   `investigation.md`: read `best_candidate.metadata.get("obj_kind")` with `REACH_LOCATION` as the
   explicit fallback, which repairs every present and future `GoalKind` at once and follows the
   pattern the three bespoke branches already established. A fourth bespoke `elif` for
   `COMBAT_ENGAGE` is the alternative and is explicitly **not** preferred — see Out of Scope on
   stacking branches.
2. Have `CombatEngageScorer` publish `obj_kind: ObjectiveKind.DEFEAT_ENEMY` in its metadata, the way
   `OccupationChangeGoalScorer` (`src/ai/goals/occupation_change_scorer.py:98`),
   `region_stabilization_scorer.py:86` and `social_contract_scorer.py:75` already do. The scorer
   resolves the objective kind; the consumer does not infer it.
3. **Measure the behavioural delta before and after, and report it even if it is zero.** See
   Assumptions — there is a real possibility the fix does not increase attack volume, because
   `TacticalDecisionSystem`'s hostile-engagement branch is gated on `hostiles`, not on `obj.kind`
   (`src/engine/tactical.py:308` and its comment). The honest deliverable is the measured number,
   not an assumed improvement.
4. Audit the other `GoalKind`s that fall through to the generic branch and record, per kind, whether
   `reach_location` is correct for it or whether it is a second instance of this defect. Record the
   finding; fix only what item 1's single change already fixes.

## Out of Scope
- Retuning the XP threshold or per-kill values. `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME`
  owns that and is explicitly blocked until real combat volume is re-measured; doing it here would
  silence the signal rather than fix it.
- The `ProjectState.score` scale question in the generic branch (see Assumptions) — recorded, not
  fixed here, unless item 3's measurement shows it is load-bearing for this defect.
- Adding further per-`GoalKind` bespoke branches. The repo's Strategic/Tactical rule is explicit that
  strategic problems are not solved by stacking more tactical special cases; four bespoke branches
  where one generic derivation belongs is the shape to remove, not extend.
- `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE`'s boss-gate half, and the
  Lair trauma/maturity reachability questions.

## Acceptance Criteria
- [ ] A winning `GoalKind.COMBAT_ENGAGE` materialises an objective of kind
      `ObjectiveKind.DEFEAT_ENEMY`, with the hostile's entity id as `target`.
- [ ] `ObjectiveIntentResolver` resolves that objective to `ATTACK_TARGET`, asserted end-to-end
      through a real `Kernel.tick_once()` path rather than by constructing an `ObjectiveState`
      directly — the defect lives in the wiring, so a unit test on the resolver alone would have
      passed before the fix.
- [ ] No goal kind that previously produced a correct `reach_location` objective changes kind. The
      generic fallback stays `REACH_LOCATION` for every scorer that publishes no `obj_kind`.
- [ ] The decision-driven `ATTACK` path volume is measured before and after on at least two corpus
      worlds, and the number is reported in `## Test Summary` **whatever it shows** — including if it
      is unchanged. A zero delta is a finding about `tactical.py:308`, not a failed ticket.
- [ ] Determinism holds: canonical/replay/fingerprint/hash sweep green, and any recorded-hash
      fixture that moves is identified and explained rather than regenerated silently.
- [ ] The per-`GoalKind` audit from Scope 4 is recorded in `investigation.md`.
- [ ] `docs/mechanics/04_strategic_cognition.md` (goal hierarchy / dispatch) and the
      `strategic_cognition.yaml` parity entry reflect the corrected behaviour, with the parity entry's
      `status` and `v2_evidence` updated.

## Related Tickets
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — the parent chain whose root cause this fixes.
  Its `SEQUENCE.md` link (1) recorded the verdict; no fix was ever filed. **Filing this does not
  resume the epic** — links (2), (3) and (5) stay where they are.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (done) — the P0 investigation that
  produced the verdict. Its 2026-09-19 addendum names `intelligence.py:1711` and the scorer at
  `src/ai/goals/scorers.py:101` (it cites `:108`; that citation has drifted).
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (done) — found combat to be incidental
  rather than decisional; chain link (2).
- `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS` (done) — corrected
  `resolve_multi_attack()`'s hostility test and dropped measured combat volume 85-96%. Any
  before/after measurement here must be taken **after** that fix, not compared to pre-fix numbers.
- `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` (blocked) — downstream; its own
  measurement must be re-run after this lands, not before.

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` — goal hierarchy, interruption resistance
- `docs/engine/contracts/tactical_contract.md` §7 — objective target resolution
- `docs/parity_ledger/strategic_cognition.yaml` — the parity entries for goal dispatch

## Related Stored Artifacts
- `stored_artifacts/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION/` — the measurement
  that produced the verdict this ticket acts on
- Staging artifacts for this ticket: `staging_artifacts/TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND/`

## Related Code Areas
- `src/systems/strategic_systems/intelligence.py:1707-1714` — the generic `else` branch, the defect
- `src/systems/strategic_systems/intelligence.py:1606-1617,1643-1653,1678-1686` — the three bespoke
  branches that already do it correctly, i.e. the pattern to generalise
- `src/ai/goals/scorers.py:101-131` — `CombatEngageScorer`, publishes no metadata
- `src/ai/goals/occupation_change_scorer.py:98` — reference for publishing `obj_kind`
- `src/domains/adventure/resolver.py:58-64` — `ObjectiveIntentResolver`, where kind becomes an intent
- `src/engine/tactical.py:308` — the hostile-engagement branch and its `obj.kind` exclusion comment
- `src/core/strategic.py:110-124` — `ObjectiveKind`, a `str` Enum
- `src/domains/adventure/mapper.py:37` — the only other `DEFEAT_ENEMY` producer

## Assumptions / Open Questions
- **The fix's behavioural delta is genuinely uncertain and must not be assumed positive.**
  `src/engine/tactical.py:308`'s comment states DEFEAT_ENEMY is "excluded — handled entirely by the
  hostile-engagement branch below (gated on `hostiles`, not `obj.kind`)". If that branch already
  fires on proximity regardless of objective kind, then correcting the kind may change *which* branch
  handles the entity without changing whether it attacks. Two readings are open: either the
  `reach_location` objective was actively steering entities into `MOVE_TO` and suppressing
  engagement, or the hostile branch was already catching them and the mislabel was mostly cosmetic.
  Scope 3 exists to settle this by measurement. **Settle it before writing the plan**, because the
  two readings imply different fixes.
- `ObjectiveKind` is a `str` Enum, so the raw `"reach_location"` literal compares equal to
  `ObjectiveKind.REACH_LOCATION`. This is a style inconsistency, **not** a type defect — do not
  report it as one.
- The generic branch sets `score=best_candidate.utility`, while all three bespoke branches use
  `metadata["raw_score"]` and carry an explicit "NEVER best_candidate.utility" warning about a
  scale mismatch (`_score_scale_max()`'s 2.9-ceiling scale vs utility's 100-ceiling normalisation).
  Whether the generic branch is therefore also wrong depends on how `_score_scale_max()` classifies a
  `kind` that is a `GoalKind` rather than a real `ProjectKind` — **unverified, and out of scope to
  fix**, but it should be checked and recorded, because if it is wrong it is a second live defect in
  the same eight lines.
- Which other `GoalKind`s reach the generic branch has not been enumerated. Scope 4 covers it.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
