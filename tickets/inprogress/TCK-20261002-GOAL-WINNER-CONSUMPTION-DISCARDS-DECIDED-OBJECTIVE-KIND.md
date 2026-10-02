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

**The consequence is worse than a mislabel, and the mechanism is NOT the one this ticket first
claimed** — see the measurement in Implementation Notes, which corrects it. `ObjectiveIntentResolver`
(`src/domains/adventure/resolver.py:58-64`) does map `REACH_LOCATION`→`MOVE_TO` and
`DEFEAT_ENEMY`→`ATTACK_TARGET`, **but it is never consulted for either kind on this path.**
`tactical.py:262` intercepts `obj.kind == "reach_location"` in a dedicated inline branch and returns
before the resolver is reached; `tactical.py:308` explicitly excludes `DEFEAT_ENEMY` from the resolver
path too. So `ATTACK_TARGET` is structurally unreachable here — not because the mapping is wrong, but
because the mapping is never asked.

What actually happens, measured: the objective's `target` is the **enemy's entity id**, which
`_resolve_target_position` cannot resolve to a node or building, so it falls back to
`obj.target_position` — the enemy's position **frozen at the tick the goal was won**. The entity walks
to that stale point, arrives, and hits `tactical.py:297-299`'s bare `EntityUpdate(entity_id=...)`: an
empty, do-nothing update. Indefinitely.

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
- [ ] **(REWRITTEN 2026-10-02 — the original wording named a mechanism that does not operate.)** An
      entity holding a won `COMBAT_ENGAGE` goal, whose target the **content catalog** agrees is
      hostile, actually attacks it. Asserted end-to-end through a real `Kernel.tick_once()` loop, not
      by constructing an `ObjectiveState` or calling the resolver directly — the defect is in the
      wiring, so a unit test on `ObjectiveIntentResolver` alone passes both before and after.
      Do **not** assert "the objective resolves to `ATTACK_TARGET` via `ObjectiveIntentResolver`":
      measurement shows the resolver is **never consulted** for these objectives (`tactical.py:262`
      intercepts `reach_location` and returns; `:308` excludes `DEFEAT_ENEMY`). A `DEFEAT_ENEMY`
      objective reaches combat through the **hostile-engagement branch**, gated on `hostiles`, so
      that is what the test must exercise.
- [ ] `hostiles` is non-empty for such an entity. This is the measured blocker: it was non-empty in
      **0 of 236** tactical calls on CE-goal holders, including all 12 where the target was within
      1 tile, and in 204/216 `crowded_frontier` cases the *only* exclusion was the catalog hostility
      test. If this criterion fails, the fix has not worked no matter what `obj.kind` says.
- [ ] No goal kind that previously produced a correct `reach_location` objective changes kind. The
      generic fallback stays `REACH_LOCATION` for every scorer that publishes no `obj_kind`.
- [ ] The decision-driven `ATTACK` path volume is measured before and after on at least two corpus
      worlds, and the number is reported in `## Test Summary` **whatever it shows** — including if it
      is unchanged. **The before-baseline is already measured** (Implementation Notes): decision-path
      vs opportunity attacks were 2 vs 119 (`crowded_frontier`) and 3 vs 783
      (`frontier_living_world`), seed 42 / 2000 ticks, with **0** `ATTACK` emissions from CE-goal
      holders and both decision-path attacks coming from entities *without* a `combat_engage` project.
      Re-measure after with the same method and worlds, and report the **catalog-hostile vs raw-only
      target ratio** alongside — at 54% / 34% raw-only (a floor), that ratio is what bounds how far the
      volume can move at all. A smaller-than-hoped delta is a finding about the hostility divergence,
      not a failed ticket.
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
- **SETTLED 2026-10-02 by measurement — see Implementation Notes.** Reading B is **falsified**
  (`hostiles` non-empty in 0 of 236 CE-goal tactical calls, including all 12 within 1 tile). Reading A
  is substantially true but by a different mechanism than stated (arrive at a stale point and emit an
  empty update, 96.8% / 70% of calls — not a pursuit that never lands a blow). Reading C's *mechanism*
  is confirmed and is the proximate cause, but its *predicted signature* is refuted: there are **0**
  decision-path rejections because no attack is ever decided. The original two-reading text is kept
  below for provenance; **do not re-run this discrimination.**

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
- ~~The generic branch sets `score=best_candidate.utility` … possibly a second live defect.~~
  **RESOLVED 2026-10-02: not a defect, the two are consistent.** `_score_scale_max()` classifies by
  enum class, so a `GoalKind` correctly selects the 100.0 ceiling that `utility` is already on. See
  Implementation Notes — and note the **scope guard** recorded there: do not change
  `ProjectState.kind` to a real `ProjectKind` while fixing `obj.kind`, or the score scale silently
  flips to the 2.9 ceiling. This ticket changes `obj.kind` only.
- Which other `GoalKind`s reach the generic branch has not been enumerated. Scope 4 covers it.

## Implementation Notes

### 2026-10-02 — MEASURED. Verdict: two defects compound, and a third was found. Three corrections to this ticket.

Probe run on **current unmodified code**, real `Kernel.tick_once()` loop, reusing
`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`'s own method (`PROD_SMALL`,
`DeterministicRNG(42)`, `LocalSequentialExecutor()` explicitly — that artifact's guard against
concurrent-evaluation probe corruption), seed 42, **2000 ticks**, worlds `crowded_frontier` (38
entities), `frontier_living_world` (49), `quest_dense_frontier` (6). No `src/` file touched. All
figures below are **post-`TCK-20260919`** and are **not comparable** to any pre-fix number in older
tickets.

**Correction 1 — `COMBAT_ENGAGE` is not a rare winner. It is the most frequent one.**

| world | goal competitions | `combat_engage` wins | share |
|---|---|---|---|
| `crowded_frontier` | 1767 | **485** | 27.4% |
| `frontier_living_world` | 1744 | **568** | **32.6% — top winner** |
| `quest_dense_frontier` | 410 | 0 | 0% (scorer returned `utility == 0.0` in 410/410; no raw-enum-different-faction live neighbour in radius 10 for its 6 entities — a real zero, contributes nothing either way) |

So this is a **high-volume** defect, not an edge case. The prior chain's "zero `DEFEAT_ENEMY`
objectives ever sampled" reproduces, and the cause is now pinned: the goal wins constantly and
winner-consumption converts **every** win to `reach_location` — 50 279/50 279 and 60 835/60 835
objective samples, zero `defeat_enemy`.

**Correction 2 — the resolver is never consulted, so `ATTACK_TARGET` is structurally unreachable.**
`ObjectiveIntentResolver.resolve` was called **only** with `investigate` objectives (360 / 154 times,
all → `MOVE_TO`) and **never once** for a `combat_engage` project's objective. `tactical.py:262`
intercepts `reach_location` and returns first; `tactical.py:308` excludes `DEFEAT_ENEMY` as well. This
ticket's original AC2 was written against a mechanism that does not operate — fixed below.

**Correction 3 — reading B is FALSIFIED, and reading C's mechanism is the proximate cause.**
`hostiles` was non-empty in **0 of 236** tactical calls on entities holding a won `COMBAT_ENGAGE`
project, across both worlds — *including* the 12 calls where the target was within 1 tile. Being gated
on proximity rather than `obj.kind` does not save it, because the same catalog test `hostiles` uses
rejects the very target the scorer chose. The discriminating measurement, `crowded_frontier` (216
calls): **204 had the target alive, in the perception-filtered neighbour list, and passing the
perception gate — the only thing excluding it from `hostiles` was the catalog hostility test.**

Raw-enum vs catalog on the targets actually selected (catalog called exactly as
`_is_engagement_hostile` does):

| world | selections | raw-enum hostile | catalog hostile | **raw-only (disagreement)** | catalog-only |
|---|---|---|---|---|---|
| `crowded_frontier` | 683 | 683 (100%, by construction) | 314 | **369 (54.0%)** | 0 |
| `frontier_living_world` | 773 | 773 (100%) | 513 | **260 (33.6%)** | 0 |

Inside the 34-97% band `legality.py:516-544`'s docstring cites. **These are FLOORS:** the probe used
`RelationContext(distance=1.0, combat_engaged=True)` (legality's own context), while
`tactical.py:210-223` builds its context with real distance, real `combat_engaged` and species ids —
and 2 calls where the probe said catalog=True still had empty `hostiles`. Real disagreement is
*higher* than 54% / 34%.

**Reading C's predicted signature is refuted.** There are **0 decision-path rejections** from
CE-goal holders — because no attack is ever decided. 0/216 and 0/20 `ATTACK` emissions. The divergence
bites **upstream** of any attack decision, so there is nothing to reject. Decision-path vs incidental
attacks reproduce the chain's shape: 2 vs 119 (`crowded_frontier`), 3 vs 783
(`frontier_living_world`) — and **both decision-path attacks came from entities NOT holding a
`combat_engage` project.**

**THE THIRD DEFECT, not previously in this ticket: the objective targets a moving entity through a
fixed-point mechanism, and never terminates.** `CombatEngageScorer` sets `target_id=str(hostile.id)`,
which *is* int-castable, so `_resolve_target_position` parses it, finds no `resource_nodes[15]` and no
`buildings[15]`, leaves `node_id`/`building_id` as `None`, and falls through to the
`obj.target_position` fallback added by `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG` for scorers
with non-int-castable ids like `"town_center"`. That fallback is correct for its own purpose and here
**silently converts "a moving entity" into "a fixed stale point".** Measured: position source was
`obj.target_position` in **100%** of cases; the entity hit the arrived-and-do-nothing branch in
**209/216 (96.8%)** and **14/20 (70%)**; the **live** target was ≥3 tiles from the stale point in
**183/212 (86%)**; `movement_mode` was `WANDER`, not `PURSUE`; and **0** of 50 279 / 60 835 objective
samples was ever in a status other than `ACTIVE`, so the project slot is held permanently. Distance to
the live target: 9 calls at 0-1, 20 at 2-3, **176 at 4-10**, 8 at >10 — they are not adjacent and
failing to swing, they are standing still where the enemy used to be.

**Consequence for the plan — neither fix alone works, and two is probably not enough.** Fixing only
`obj.kind` routes the objective to the hostile-engagement branch, where `hostiles` is still empty from
the catalog divergence. Fixing only the hostility source leaves winner-consumption still writing
`reach_location`. And fixing both still leaves an objective whose `target` is an entity id that nothing
on this path can track, and which never terminates. **The plan must decide explicitly whether the
third defect is in this batch or its own ticket** — my lean is its own ticket, filed before
implementation starts so the batch's scope stays honest, because the target-resolution and
non-termination problems are not about the decided objective *kind* at all.

Floors, caveats and what was not measured, carried from the probe rather than dropped: the
disagreement percentages are floors (above); opportunity-path rejection reasons are unmeasured
(`resolve_multi_attack` surfaces only an aggregate `outcome_kind`); "0 objectives abandoned" means no
sample showed a non-`ACTIVE` status, not provably never — 27 and 36 distinct CE projects did churn;
tactical **call counts** drift ±~3% run to run (212/213/216/218 over four identical-seed runs) while
every **simulation outcome** was exactly reproducible (485 wins, 2 decision attacks, 119 opportunity,
every run) — believed to be the governor's latency-adaptive brain scheduling, not chased to root
cause; `hero_guild_routing` and `metropolis` were not run. Instrument positive control held: the probe
did capture the 1 `ATTACK` per world from non-CE entities and their downstream dispatches, so the zero
from the CE bucket is a real zero, not a blind wrap.

### 2026-10-02 — RESOLVED: the generic branch's `score` is CORRECT. Do not "clean up" `ProjectState.kind`.

The Assumptions section flagged `score=best_candidate.utility` in the generic branch as possibly a second
defect, because all three bespoke branches carry an explicit "NEVER best_candidate.utility" warning.
**Checked, and it is not a defect — the two are consistent.** No separate ticket is needed. But the
reason it is consistent is a trap, so it is recorded here as a scope guard.

`_score_scale_max()` (`intelligence.py:111-128`) classifies **by the actual Python enum class**, not by
string value:

```python
if isinstance(kind, ProjectKind):
    return _ADVENTURE_ROUTE_SCORE_MAX     # 2.9  (intelligence.py:32)
return _GOAL_UTILITY_SCORE_MAX            # 100.0 (intelligence.py:47)
```

- The **bespoke** branches set `ProjectState.kind = proj_kind`, a real `ProjectKind` → the **2.9**
  ceiling → so they must *not* store a 100-scale `utility`, hence their warning and their use of
  `metadata["raw_score"]`.
- The **generic** branch sets `kind = best_candidate.kind`, a `GoalKind` (`:1718`) → the **100.0**
  ceiling → which is exactly the scale `best_candidate.utility` is already on. Correct as written.

**SCOPE GUARD — the trap, and the most likely way this ticket introduces a regression.** A natural
instinct while fixing the objective kind is to also "fix the type confusion" by making
`ProjectState.kind` a real `ProjectKind` instead of a `GoalKind`. **Do not.** That single change silently
flips the score scale from the 100.0 ceiling to the 2.9 ceiling while `score` still holds a utility
value — so a score of, say, 80.0 would be read against a 2.9 ceiling. The existing comment at
`:1699-1703` ("read back through `_score_scale_max()`'s 2.9-ceiling scale **once kind is a real
ProjectKind**") is describing precisely this coupling, and `_score_scale_max`'s own docstring warns
against a value-based check because `ProjectKind.HARVESTING` and `GoalKind.HARVESTING` share a string
value.

So this ticket changes **`obj.kind` only**. `ProjectState.kind` and `score` in the generic branch stay
exactly as they are. If the `GoalKind`/`ProjectKind` vocabulary split is ever to be unified, that is
already tracked elsewhere (`_score_scale_max`'s docstring cites D22/C4) and must move `kind` and `score`
together, in its own ticket, with the scale change declared.

### 2026-10-02 — THIS FIX IS NOT SAFE TO LAND ALONE (found before implementation)

Raised by `world-rule-catalog-design`'s decision-7 triage and then **verified directly here**, because
it changes what this ticket must contain.

`CombatEngageScorer` selects its target with a **raw legacy-enum** comparison
(`src/ai/goals/scorers.py:108`):

```python
hostiles = [n for n in neighbors if n.identity.faction != entity.identity.faction and n.combat.alive]
```

`Faction` is a **4-value `IntEnum`** (`src/core/enums.py:33-37`: `HERO_GUILD`, `MONSTER_HORDE`,
`TOWN_COUNCIL`, `NEUTRAL`), so every content faction collapses onto four slots.

Meanwhile the engagement path no longer uses that test. `LegalityServiceV2._is_engagement_hostile`
(`src/engine/legality.py:516-544`) resolves real faction ids and asks the content catalog
(`is_hostile_compat`). Its own docstring states the measured delta, quoted verbatim:

> "Replaces the prior raw `entity.identity.faction != other.identity.faction` legacy-enum comparison,
> which never consulted the content catalog and was measured to disagree with it on **34%-97% of every
> pair either source flagged as hostile**
> (`TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`)."

**So today the scorer's wrong target choice is harmless only because this ticket's defect throws the
choice away.** Repairing dispatch without unifying the scorer's hostility test would start dispatching
attacks at targets chosen by a test known to disagree with the engagement test on 34-97% of flagged
pairs. The dormancy is load-bearing in the same way `stats_dirty`'s was.

**Consequence for Scope 3 — a third reading, now the most likely one.** The Assumptions section offered
two: either the `reach_location` objective was suppressing engagement, or the hostile-engagement branch
was already catching entities and the mislabel was cosmetic. There is a third: the fix produces
**decided attacks that the engagement path then rejects**, because scorer and legality disagree on who
is hostile. The measurement must therefore count *rejected* attack attempts and stuck/abandoned combat
objectives, not only successful attacks. A rise in rejections is the signature of this reading.

**Scope change, to be reflected in the plan:** unifying `scorers.py:108` onto the catalog test is a
**prerequisite within this batch**, not a follow-up. The triage recommended landing it "with or right
after" the dispatch fix; the 34-97% figure argues against "right after" — between the two commits the
simulation would be actively dispatching mis-targeted attacks.

`TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` owns the full sweep of raw-enum sites (with
`TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM` to be folded into it). Only the
`scorers.py:108` site is claimed here, because only it is coupled to this defect. **Do not absorb the
rest of the sweep into this ticket** — note that `SensoryFilter.filter_saliency` runs on the line
immediately above (`scorers.py:107`) and is a sweep site of its own, so the boundary needs stating
explicitly in the plan rather than assumed.

Unverified and deliberately not claimed: how often either path fires in corpus play. The 34-97% figure
is a disagreement rate over flagged pairs, **not** a frequency of occurrence.

## Test Summary
_(not started)_

## Files Changed

Implementation has not started. The entries below are **docs this ticket's branch already carries and
that its commit subjects already name** — recorded here because `done_checker`'s
`docs_to_update_coverage` reverse check correctly flagged them as touched-but-unrecorded, and the honest
fix is to make the record true rather than to quiet the check.

**Not part of the dispatch fix.** They are the owner-decision work that rode on this branch because the
branch needed a ticket file for `pr_render` to produce a body at all (see
`feedback_pr_render_closes_includes_filed_tickets` — a ticketless branch cannot be PR'd). Listing them
so a reviewer is not surprised by them in the diff:

- `docs/plans/systemic_world/owner_decision_memo.md` — owner decision 7 (row 7, foundation before
  features) and decision 8 (row 8, perception authority). **Row 7 and row 8 are the only copy of their
  definitions.** Verbatim text authored by `world-rule-catalog-design`.
- `docs/plans/systemic_world/roadmap.md` — the §8 decision-7 superseding note, the §8 approved work
  order, and the §10 count and list. Verbatim, same author.
- `docs/plans/simulation_semantic_control_plane/rollout_plan.md` — annotation of the explicit non-goal
  that decision 7 partly supersedes ("Do not stop normal RPG-core engineering work until the mapping is
  complete"). Written by this session, not the rule owner, and it is an SCP plan doc this session owns.

Docs this ticket's **own fix** will change, per `plan.md` step 4 — not yet touched:
- `docs/mechanics/04_strategic_cognition.md`
- `docs/parity_ledger/strategic_cognition.yaml`

## Completion Summary
_(not started)_
