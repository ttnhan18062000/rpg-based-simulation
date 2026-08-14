---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
artifact_type: investigation
tags: [combat, calibration]
---

# Investigation — TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION

## The two systems

Two structurally independent, fully live subsystems both write to the same
`entity.strategic.current_project_id` / `ProjectState.kind` field, using two different enums for
the same real-world concept ("this entity is fighting"):

### System A — `AdventureDecisionPhase` (route-based)

- **Source**: `src/domains/adventure/` (`phase.py`, `generator.py`, `service.py`, `mapper.py`,
  `schema.py`). Documented in `docs/simulation/domains/adventure_contract.md`
  (`status: authoritative`, `last_verified: 2026-07-03`) and `docs/mechanics/
  adventure_routing_contract.md`.
- **What it handles**: generates up to 25 candidate `RouteFamily` options per hero per tick
  (RECOVER, BUY_UPGRADE, CRAFT_UPGRADE, TRAIN_SKILL, TAKE_EASY_QUEST, **HUNT_WEAK_ENEMY**,
  GATHER_RESOURCE, SELL_LOOT_FOR_GOLD, ASK_INFORMATION, SCOUT_LOCATION, **FORM_PARTY**,
  RETURN_TOWN, QUEST_OPPORTUNITY, PROTECT_TARGET, OWN_SURVIVAL), scores each via
  `score = urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty`,
  selects the highest-scoring non-blocked route, and maps it to a `ProjectState` via
  `RouteToProjectMapper._MAP` (`src/domains/adventure/mapper.py`) — e.g.
  `HUNT_WEAK_ENEMY → ProjectKind.COMBAT = "combat"`, `FORM_PARTY → ProjectKind.SOCIAL = "social"`.
- **Cadence/locking**: runs every tick for every eligible hero; on a hit, creates a fresh project
  with `lock_until_tick = min(tick+10, tick+50)` (capped at 50 ticks — in this test's specific
  compiled world, observed to renew every exactly 10 ticks). Skips heroes with an unexpired lock
  (`phase.py:97`) unless `_threat_resolved()` (an early-release condition, but only useful for
  releasing OUT of retreat/recover-type locks — see below).
- **E11D calibration** (`TCK-20260619-E11D-SCORING-CAL`, cited by the failing test's own docstring)
  tuned THIS system's bravery/caution coefficients (`risk_multiplier = max(0.1, (1+caution*0.8) -
  bravery*0.6)`), used in every route's shared `risk_penalty` term. `HUNT_WEAK_ENEMY` has no
  dedicated personality-bias trait of its own (only `RECOVER/RETURN_TOWN→caution`,
  `GATHER_RESOURCE/SELL_LOOT→greed`, `SCOUT/ASK_INFO→curiosity`, `CRAFT/TRAIN→industry`,
  `FORM_PARTY→sociability` are listed) — bravery only affects it indirectly via the risk penalty,
  meaning **E11D's own 4.92x baseline almost certainly measured `ProjectKind.COMBAT="combat"`
  (System A's own combat route), not `GoalKind.COMBAT_ENGAGE="combat_engage"`** (System B, below).

### System B — `StrategicIntelligenceSystem` / `GoalRegistry` (goal-based)

- **Source**: `src/systems/strategic_systems/intelligence.py` (`StrategicIntelligenceSystem`,
  compliance IDs STRAT-002 through STRAT-234 — the Mechanics Bible chapter 04 "goal hierarchy,
  interruption resistance" implementation) + `src/ai/goals/` (`GoalRegistry`, `CombatEngageScorer`,
  `SocialScorer`, etc., `GoalKind` values).
- **What it handles**: a from-scratch `fused_strategic_pass()` per eligible entity (not
  hero-only — covers any strategic entity) that layers directive/concern/lead evaluation, THEN
  (only if nothing more urgent fires) falls through to `GoalRegistry.get_all_scores()` — every
  registered `GoalScorer` (`CombatEngageScorer`: `utility = 40 + bravery*40 + stamina_ratio*20`
  when hostiles are visible, confirmed via direct read to use the CORRECT positive bravery sign;
  `SocialScorer`: flat `utility = 10.0` always; `CombatRetreatScorer`: `utility -= bravery*30`,
  also correct) — filters candidates to `utility >= 20.0` and `target_id/target_pos` set, picks
  the highest scorer, and maps its `GoalKind` directly as the new `ProjectState.kind` (e.g.
  `GoalKind.COMBAT_ENGAGE = "combat_engage"`).
- **Cadence/locking**: gated by `SystemCadence`/`should_run()` (not necessarily every tick).
  Explicitly documented, by its own docstring, as implementing "interruption resistance / margin
  logic" and "current project gets reservation/retention priority" (Logic IDs STRAT-185/186/187).

### The precedence bug

`src/engine/pipeline.py` runs `AdventureDecisionPhase` (line ~240) BEFORE
`StrategicIntelligenceSystem.fused_strategic_pass()` (line ~347) in the same tick's `refine()`
sequence. `StrategicIntelligenceSystem.evaluate_project_switch()` (`intelligence.py:881-932`) is
the real gate governing whether ANY candidate (from either system) can take over
`current_project_id`:

```
if current.lock_until_tick > current_tick:
    if (candidate_project.kind == "danger" and candidate_project.score > 80) or candidate_project.kind == "detour":
        pass
    else:
        return None
```

`"danger"` here is `ConcernKind.DANGER` — a THIRD, separate world-emergence/concern-pressure
vocabulary (`src/systems/world_systems/{routine,intake,events}.py`), unrelated to either System A
or System B's own combat semantics. `GoalKind.COMBAT_ENGAGE` (`"combat_engage"`) is **not** on this
bypass allowlist — a `combat_engage` candidate, no matter how high its utility, cannot interrupt an
active lock. Only `AdventureDecisionPhase`'s own re-evaluation (which runs unconditionally every
tick, before `StrategicIntelligenceSystem`) can naturally let a lock expire and immediately
re-lock in the SAME tick — meaning: **on any tick where an `AdventureDecisionPhase`-owned lock
expires, `AdventureDecisionPhase` runs first and re-locks before `StrategicIntelligenceSystem`
ever gets a chance to see the window open.** `GoalRegistry`'s `combat_engage` can only ever win a
hero's project slot on a tick where `AdventureDecisionPhase` itself defers (no valid non-blocked
route candidate that specific tick) — a condition uncorrelated with bravery, hostile proximity, or
combat urgency. Once `combat_engage` DOES win (via that race), its own fresh lock then
symmetrically blocks `AdventureDecisionPhase`'s subsequent re-evaluations, so it persists — exactly
matching the observed data.

## Direct evidence (traced live, `SEED=42`, `TICKS=400`, the failing test's exact scenario)

8 heroes spawn at varying distances from 4 monsters in a 32×32 arena. 2 heroes die during the run
(including the single highest-bravery hero, id=8, bravery=0.8368 — removed from the quartile
computation entirely). Of the 6 survivors:

| hero | bravery | project kind (400/400 ticks) | mechanism |
|---|---|---|---|
| 3 | 0.1024 | `combat_engage` (343/400) | System B won a race window early (~tick 57), then self-perpetuated |
| 5 | 0.7926 | `combat_engage` (335/400) | Same — System B won early (~tick 65) |
| 7 | 0.7421 | `combat_engage` (337/400) | Same — System B won early (~tick 63) |
| 1 | 0.7674 | `social` (400/400, `FORM_PARTY`) | System A's own route won every single 10-tick re-evaluation, never deferred |
| 4 | 0.6552 | `social` (400/400, `FORM_PARTY`) | Same, **despite a live, adjacent hostile from tick 9 onward** (directly confirmed — monster 11 stayed within 1-2 tiles of hero 4 from tick 9-19, hero 4 never once left `FORM_PARTY`) |
| 6 | 0.5960 | `social` (400/400, `FORM_PARTY`) | Same |

Confirmed via direct instrumented per-tick trace (`current_project_id` changes, not just `.kind`
string) that hero 4's project genuinely gets **re-created every exactly 10 ticks** by System A
(`proj.form_party.ent4.t0`, `.t10`, `.t20`, ... `.t390` — 40 distinct project instances, each with a
fresh `lock_until_tick`), never once losing the race to System B despite System B's own
`CombatEngageScorer` utility for hero 4 (with an adjacent live hostile) being well above the
threshold that should win under normal (unlocked) `evaluate_project_switch()` comparison.

Given the quartile test sorts alive heroes by bravery and slices `q_size = max(1, n//4)` (here,
`6//4 = 1`, so exactly one hero per quartile), the test ends up comparing hero 3 (bravery 0.10,
`combat_engage` via a lucky early System-B race win) against hero 5 (bravery 0.79, ALSO
`combat_engage`, ALSO a System-B race win) — both real combat-engaging heroes, with a small
(343 vs 335, ~2%) rate difference that is noise from exactly when each one's race window opened,
not a bravery signal at all. The REAL, stark, bravery-uncorrelated split in this run's data — 3 of
6 heroes permanently locked into `social` for the entire 400-tick run regardless of bravery
(0.60, 0.66, 0.77 span the range) or hostile proximity (hero 4 had one adjacent) — is invisible to
the quartile math because those 3 heroes cluster in the MIDDLE of the bravery distribution, not
the extremes the `q_size=1` slice actually compares.

## Third finding: `RouteFamily.HUNT_WEAK_ENEMY` is dead code

Directly tested the "System A actually handles hero combat via `ProjectKind.COMBAT`" hypothesis:
re-ran the exact scenario counting BOTH `"combat_engage"` and `"combat"` as combat participation.
Result: **identical to counting `combat_engage` alone** — `ProjectKind.COMBAT="combat"` never
appears once, for any hero, across the full 400-tick run. Confirmed via direct source read:
`grep -n "HUNT_WEAK_ENEMY" src/domains/adventure/generator.py` returns zero matches —
`AdventureRouteGenerator.generate()` has no code path that ever produces a `HUNT_WEAK_ENEMY`
candidate, despite it being a real, mapped `RouteFamily` member
(`RouteToProjectMapper._MAP[RouteFamily.HUNT_WEAK_ENEMY] = (ProjectKind.COMBAT,
ObjectiveKind.DEFEAT_ENEMY)`). This route family is dead in the current generator — System A can
never route a hero into combat at all, in any scenario, regardless of bravery, hostiles, or
opportunities. This means `TCK-20260619-E11D-SCORING-CAL`'s own original 4.92x baseline — if it
measured `ProjectKind.COMBAT` via this same route family, which is the more likely reading given
`HUNT_WEAK_ENEMY` is the only combat-tagged family in System A and the calibration note's own
bravery/caution coefficients live in System A's shared risk-penalty term — is not reproducible
today under any circumstances: the code path it calibrated has since gone dead (whether via a
regression in `generator.py`, or the baseline was always measuring `GoalKind.COMBAT_ENGAGE`
through some earlier version of the precedence interaction that behaved differently before
System A existed or before its relocking cadence was this aggressive — not confirmed either way
without a deeper git-archaeology pass on `generator.py`'s own history, not yet done).

Net effect for heroes in this test's own scenario: the ONLY real path to combat participation is
System B's `combat_engage`, and System B is itself structurally starved by System A's own
aggressive relocking (finding 2, above) except during rare, bravery-uncorrelated race windows.

## Historical confirmation: is System A a design drift, or intentional?

Checked the real origin tickets and commit history, not assumed:

- **2026-05-27**, `TCK-20260527-COG-GOAL-REGISTRY`: builds `GoalRegistry`/`CombatEngageScorer`
  (`GoalKind.COMBAT_ENGAGE`) — explicitly "Bravery/aggression biases combat intent when threats
  are present," wired into `fused_strategic_pass()`. This is the ORIGINAL, and — per the evidence
  below — still the ONLY live, combat-decision mechanism.
- **2026-05-28**, `TCK-20260528-COG-PHASE3-DECISION`: builds `AdventureDecisionPhase` ("Phase 3").
  Its own **Out of Scope** section explicitly lists: **"Combat engagement cognition (Phase 4)"** —
  System A was deliberately, explicitly scoped to exclude combat decision-making from day one, not
  as an oversight. `RouteFamily.HUNT_WEAK_ENEMY`'s own dead generator logic (finding 3, above) is
  this deferral's direct, confirmed consequence — a stub left for a "Phase 4" that was supposed to
  own combat, never filled in.
- **2026-05-30**, commit `8bd3bf0a`/`6fe08820` ("Entity Enhance Phase 4"): builds
  `src/domains/combat_engagement/` — **this is the literal "Phase 4"** the prior ticket deferred
  to. But `CombatEngagementPhase.apply()` (confirmed via direct read: no reference to
  `current_project_id` anywhere in `phase.py`) is a pure tactical **execution** phase — it
  resolves damage/aftermath/rewards for combat already underway (matches yesterday's own
  `TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS` fix description: "action
  routing's real ATTACK dispatch"). It never decides WHETHER an entity should pursue combat.

**Conclusion**: "Phase 4" never actually took over the combat-DECISION responsibility Phase 3
deferred to it — it only ever handled combat-RESOLUTION. The decision of whether to engage was,
by default and without anyone explicitly re-confirming it, left with the original 05-27
`GoalRegistry`/`CombatEngageScorer` mechanism the whole time. `AdventureDecisionPhase` is **not**
a design drift or a wrong/duplicate system — it is a legitimately, deliberately-scoped
non-combat routing layer (recovery, crafting, training, quests, scouting, trade, socializing).
The real gap is narrower and more precise than "two systems duplicate the same job": **nobody
ever revisited `AdventureDecisionPhase`'s own interruption-resistance interaction with the
still-live `GoalRegistry` combat mechanism after Phase 3 shipped, so its routine-activity locking
(built without any awareness that combat decisions belong to a separate, older system) ended up
silently starving that system rather than yielding to it.**

This directly confirms the user's own hypothesis: the two are not competing alternatives that
need consolidating into one system (a large, high-risk rewrite) — they need to be **wired
together correctly**: `AdventureDecisionPhase`'s own lock-bypass/interruption logic (or, more
precisely, `StrategicIntelligenceSystem.evaluate_project_switch()`'s allowlist, the actual gate
both systems' candidates pass through) needs to recognize a genuine `GoalKind.COMBAT_ENGAGE`
candidate as combat-cognition's own legitimate domain and let it through, the same way `"danger"`
and `"detour"` already do. Reviving `RouteFamily.HUNT_WEAK_ENEMY` (my earlier draft
recommendation) would be the WRONG fix — it would build a second, redundant combat-decision path
inside System A, duplicating what `GoalRegistry` already correctly owns, rather than fixing the
real gap: System A's own locking not yielding to System B's already-correct decision.

## Root cause summary

Not a bravery-scoring bug (both scorers use the correct sign, confirmed by direct read). Not
random test flakiness (deterministic across repeated runs at the same seed). Two real, independent
findings:

1. **Statistical**: `q_size = max(1, n // 4)` collapses to a single-entity comparison whenever the
   alive population drops to <8 (2 of 8 heroes died in this run), making the assertion a
   noise-sensitive individual comparison rather than a real quartile-vs-quartile statistic.
2. **Architectural**: `StrategicIntelligenceSystem.evaluate_project_switch()`'s lock-bypass
   allowlist (`"danger"` with score>80, or `"detour"`) does not include `GoalKind.COMBAT_ENGAGE`,
   combined with `AdventureDecisionPhase` running first in the pipeline and re-locking
   aggressively (every ≤50, here every 10, ticks) — this means `GoalRegistry`'s own
   bravery-driven `combat_engage` goal can only ever win an entity's project slot on ticks where
   `AdventureDecisionPhase` itself happens to defer, a condition uncorrelated with bravery or
   combat urgency. This is very likely NOT the intended design — `docs/mechanics/
   04_strategic_cognition.md`'s own hierarchy implies bravery-driven combat urgency should be able
   to interrupt routine activity, and `CombatEngageScorer`'s own utility formula (up to 100 for a
   maximally brave, full-stamina hero facing a hostile) reads as designed to represent genuine
   urgency, not routine background behavior. Whether this is a real design gap in
   `evaluate_project_switch()`'s own bypass allowlist, or intentional (route-based System A is
   meant to always take precedence for heroes, and System B is only a fallback for non-hero
   entities or entities System A doesn't cover) is not yet confirmed with direct evidence — the
   next investigation step.

## Post-Batch Re-Investigation (2026-08-11)

Re-investigated after the 4-ticket batch (C1 `TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY`,
C2 `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, C3 `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`,
C4 `TCK-20260810-D22-DORMANT-WIRING-AUDIT`) landed and the test still showed identical
`top_rate=0.8375 / bottom_rate=0.8575`. Read C2's `stored_artifacts/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION/{investigation,plan}.md`
in full, the real landed `src/systems/strategic_systems/intelligence.py:929-1006` (`evaluate_project_switch`,
`_score_scale_max`, module constants at lines 27-53), `src/core/strategic.py:309-323`
(`CognitionProfile` defaults), `src/domains/adventure/{phase.py,mapper.py}`, and re-ran the exact
failing scenario (SEED=42, TICKS=400, 32x32 arena, 8 heroes) with `StrategicIntelligenceSystem.
evaluate_project_switch` monkeypatched to log every call's real candidate/current kind, score,
computed max, lock state, and result -- 1365 real calls captured, not estimated.

### Hypothesis verification: CONFIRMED, with real numbers

The suspected formula is the exact landed code (`intelligence.py:988-993`):
```python
candidate_max = _score_scale_max(candidate_project.kind)
current_max = _score_scale_max(current.kind)
candidate_pct = candidate_project.score / candidate_max
normalized_effective_current_pct = (current.score / current_max) + (retention_margin / current_max)
if not (candidate_pct > normalized_effective_current_pct and candidate_pct > _INTERRUPTION_URGENCY_FLOOR_PCT):
    return None
```
`_ADVENTURE_ROUTE_SCORE_MAX = 2.9` (System A), `_GOAL_UTILITY_SCORE_MAX = 100.0` (System B),
default `retention_margin = interruption_resistance(0.3) * resistance_multiplier(30.0) = 9.0`
(`src/core/strategic.py:320-321`, confirmed, not estimated).

Direct trace evidence, both real cross-system calls where a locked System-A `current` (a real
`ProjectKind.SOCIAL`/FORM_PARTY project) was challenged by a System-B `candidate`
(`GoalKind.COMBAT_ENGAGE`):

| tick | hero | candidate.score (raw) | candidate_pct | current.score (raw) | normalized_effective_current_pct | switched? |
|---|---|---|---|---|---|---|
| 2 | 8 | 132.58 | 1.3258 | 0.8207 | 3.3864 | **False** |
| 6 | 4 | 114.45 | 1.1445 | 0.6857 | 3.3399 | **False** |

`retention_margin / current_max = 9.0 / 2.9 = 3.1034` alone -- before adding `current.score/current_max`
(only ~0.19-0.28 for the real, post-C2-mapper-fix FORM_PARTY scores observed, which cluster at
0.55-0.82, nowhere near the 2.9 ceiling) -- already exceeds every real `candidate_pct` observed for
`CombatEngageScorer` (`40 + bravery*40 + stamina_ratio*20`, hard-capped at 100, so `candidate_pct`
tops out at 1.0 exactly at maximum bravery+stamina, occasionally >1.0 only because `RoutineService`/
`ScoreModifierSystem`/leadership-influence biasing pushes some observed values to 1.1-1.33). **A
System-B candidate can never mathematically clear `normalized_effective_current_pct` while the
current project is System-A-typed, for any real value either system's scorers can produce today.**
Confirmed exhaustively, not just for these two samples: **0 of 24** total `evaluate_project_switch()`
calls made while `current.lock_until_tick > current_tick` resulted in a switch anywhere in the run
(across all 8 heroes, all kinds, all ticks) -- the lock-bypass branch never once fired in this entire
400-tick run. This includes same-system (System-B-vs-System-B) and detour cases, not only the
cross-system case; the cross-system (System-A-current, System-B-candidate) case above is simply the
mathematically-guaranteed-impossible subset of that zero.

**This is a real, confirmed remaining defect in C2's landed normalization**, distinct from and
additional to what C2 itself tested: C2's own `test_score_normalization.py` (Step 6, both tests)
only exercises the *opposite* direction -- `candidate` is System A (small max) against a System B
`current` (large max) -- never the direction that actually occurs in this scenario (`current` is
System A / small max, `candidate` is System B / large max, locked). **No test in the C2 batch
exercises the locked, cross-system, small-max-current direction at all** -- confirmed by re-reading
every test in `tests/unit/strategic/test_interruption_resistance.py::TestGenericInterruptionBypass`
and `tests/unit/strategic/test_score_normalization.py` (19 tests total, all currently passing per a
fresh `pytest tests/unit/strategic/test_interruption_resistance.py tests/unit/strategic/
test_project_continuity.py tests/unit/strategic/test_score_normalization.py -q` run this session).
The `retention_margin` term (`STRAT-005`, unnormalized, ~9.0 by default) is a raw-score-scale
constant; dividing it by a system's own declared max (`2.9` for System A) rather than by some shared
scale inflates its effective weight ~34x when `current` happens to be System-A-typed -- structurally
guaranteeing the "current project retention priority" (STRAT-187) becomes absolute/un-interruptible
for that direction, not merely favored, which is a stronger guarantee than STRAT-186's own stated
intent ("switching requires margin **or** explicit emergency" -- implying emergencies should still be
able to get through).

### Why the test still shows byte-identical rates: NOT the same reason for all heroes

The full per-hero, per-tick trace shows the C2 architectural fix **did** materially change behavior
for the heroes that were actually affected by the pre-batch starvation bug:

| hero | bravery | pre-batch (from original investigation, 400/400 ticks) | post-batch (this session, 400 ticks) |
|---|---|---|---|
| 4 | 0.6552 | `social` 400/400 (never escaped) | `social` 16/400, `combat_engage` 384/400 -- escaped at **tick 16** |
| 8 | 0.8368 | (died before pre-batch trace could observe long-run) | `social` 12/400, `combat_engage` 388/400 -- escaped at **tick 12** (later died) |
| 1 | 0.7674 | `social` 400/400 | `social` 99/400, `combat_engage` 301/400 -- escaped at **tick 99** |
| 6 | 0.5960 | `social` 400/400 | `social` 94/400, `resolve_blocker` 306/400 (never `combat_engage` -- a *different* System-B goal won instead, 0/400 combat_engage) |

Heroes 1/4/8 (and 6, into a different goal) are no longer permanently locked into `social` for the
full run -- a real, confirmed behavioral change. But tracing **how** they escaped shows it was **not**
via the (broken) normalized lock-bypass gate documented above: every one of them escaped only *after*
their System-A project's own short lock (`lock_until_tick = min(tick+10, tick+50)`, observed to
always be exactly `tick+10` in this scenario) naturally expired, at which point
`evaluate_project_switch()`'s `if current.lock_until_tick > current_tick:` branch is skipped entirely
and falls through to the pre-existing, C2-untouched raw comparison
(`if candidate_project.score > effective_current_score:`, `effective_current_score = current.score
(~0.5-0.8) + retention_margin (9.0) ~ 9.5-9.8`) -- trivially cleared by any real `CombatEngageScorer`
utility (40-130+). **The real fix that helped these heroes was C2's Step 7 (`AdventureDecisionPhase.
apply()` routed through `evaluate_project_switch()` instead of unconditionally overwriting
`current_project_id_set` every ~10 ticks)** -- this stopped System A from perpetually re-locking a
fresh `social`/FORM_PARTY project every exactly 10 ticks forever (the pre-batch mechanism, confirmed
by the original investigation's 40-distinct-project-instance trace). Post-C2, System A's own
re-commit attempt is now itself subject to `evaluate_project_switch()` -- and once System B has won
the slot via the unlocked path, subsequent System-A `social` candidates trying to reclaim it hit the
(now correctly restrictive, in this direction) normalized gate: e.g. for hero 4 post-switch,
`candidate_max=2.9` (weak `social` candidate ~0.24 pct) vs `normalized_effective_current_pct ~
(111/100)+(9/100)=1.20` -- correctly blocked, matching the observed 384/400 sustained `combat_engage`.

**The two heroes the test's own broken quartile math actually compares (hero 3, bottom quartile;
hero 5, top quartile) were never subject to the starvation bug in the first place** -- confirmed
directly: both heroes had `current_project_id = None` (no project at all) the first time
`evaluate_project_switch()` was called for them (tick 57 for hero 3, tick 65 for hero 5) -- they
simply had not yet met `GoalRegistry`'s `utility >= 20.0` / `target_id or target_pos` eligibility
bar (monster not yet in range, or scorer conditions not yet met) before that tick, not because a
competing System-A lock was blocking them. Once eligible, `evaluate_project_switch()`'s "no current
project" branch (lines 958-963, unconditional, untouched by C2) accepted the candidate immediately.
**These exact tick numbers (57, 65) and resulting rates (343/400 = 0.8575, 335/400 = 0.8375) are
identical, digit-for-digit, to the pre-batch investigation's own table** -- because nothing in these
two heroes' code paths touches anything C2 changed. This is why 3 independent Test-phase runs (during
C2's own Implement/Test and C3's Test) all reported the identical 0.8375/0.8575 pair: it is not
residual staleness or a caching artifact, it is the deterministic, reproducible output of a
mechanism the batch never touched for these two specific individuals.

### Statistical finding (q_size collapse): CONFIRMED UNCHANGED post-batch

Re-ran and directly checked: **6 of 8 heroes alive at tick 400** (heroes 2 and 8 died -- notably,
hero 8 died despite successfully escaping into `combat_engage` at tick 12, illustrating that combat
participation itself carries lethality risk uncorrelated with the quartile math), identical
alive-count to the pre-batch trace. `q_size = max(1, 6 // 4) = 1` -- still an exact single-entity
comparison (hero 3 vs hero 5), not a real quartile statistic. This finding is completely independent
of the architectural batch and remains exactly as originally diagnosed.

### Additional finding: no bravery correlation across the full alive population either

Computed `combat_engage` rate for all 6 alive heroes (not just the quartile-extreme pair), sorted by
bravery, to check whether a real signal exists anywhere in the distribution that the quartile math is
simply failing to capture:

| hero | bravery | combat_engage rate |
|---|---|---|
| 3 | 0.1024 | 0.8575 |
| 6 | 0.5960 | **0.0000** (won `resolve_blocker` instead, every tick it had a project) |
| 4 | 0.6552 | 0.9600 |
| 7 | 0.7421 | 0.8425 |
| 1 | 0.7674 | 0.7525 |
| 5 | 0.7926 | 0.8375 |

No monotonic or even weakly-positive trend -- lowest-bravery hero 3 (0.86) outranks 4 of the 5 more
brave heroes; hero 6 (mid-bravery) never engages combat at all in favor of a competing System-B goal
(`GoalKind.RESOLVE_BLOCKER`, not investigated further -- out of this ticket's scope, but flagged as a
possible confound: `GoalRegistry` competition among System-B goals themselves, not just System-A-vs-B,
also drives real per-hero variance). **Even setting the q_size=1 statistical bug aside entirely, this
run's real per-entity data does not show a clean bravery-driven 2x (or any consistent direction)
signal at n=6** -- a material finding for Plan: fixing only the quartile-slicing math (e.g., requiring
a minimum n, or asserting on a larger population) may still not produce a passing, meaningful 2x
result at this seed/population scale, because individual "did I win the race to eligibility" and
"did a same-system competing goal outscore combat_engage" effects currently dominate over any
bravery signal in the 40 (bravery coefficient) `CombatEngageScorer` term. This is evidence, not a
recommendation to lower the threshold by default -- Plan must weigh it against alternatives (larger
population/seed set, multiple-seed averaging, or a scenario redesign) before concluding recalibration
is the only path.

### Root cause summary (post-batch)

The test still fails for two layered, now-confirmed-independent reasons:

1. **Statistical (unchanged, still dominant for this specific test)**: `q_size=1` at n=6 alive
   heroes means the test literally compares two individuals, and this run's two specific individuals
   (hero 3, hero 5) happen to be ones whose `combat_engage` entry never involved the mechanism C2
   fixed -- so the batch's real behavioral improvement is invisible to this test's own assertion,
   through no fault of the fix.
2. **Architectural (partially fixed, one real residual defect confirmed)**: C2's Step 7 rewiring
   (`AdventureDecisionPhase.apply()` routed through `evaluate_project_switch()`) successfully broke
   the perpetual 10-tick re-lock cycle that permanently starved heroes 1/4/6/8 pre-batch -- confirmed
   via real per-tick trace, a genuine fix. However, C2's own new normalized lock-bypass gate
   (`candidate_pct > normalized_effective_current_pct`) is confirmed, via 24 real locked-state calls
   (0 passes) and exact arithmetic, to be **structurally unable to ever let a System-B candidate
   interrupt a still-locked System-A current** -- `retention_margin(9.0) / _ADVENTURE_ROUTE_SCORE_MAX
   (2.9) ~ 3.10` alone exceeds any realistic System-B `candidate_pct` (max ~1.0-1.3 observed). This
   did not block this specific test's fix from working only because System A's own locks are short
   (10 ticks, capped at 50) -- the *unlocked* raw-score path (C2-untouched) rescues stuck heroes once
   the lock naturally expires. A scenario with longer System-A locks, or any future tightening of
   `_threat_resolved()`/the per-hero own-lock gate in `phase.py`, would re-expose full starvation with
   no escape path. **Not this ticket's scope to fix** (it belongs to C2's own subsystem and would
   itself need a dedicated ticket -- normalizing `retention_margin` against a shared/common scale, or
   against `current_max` in a way that doesn't structurally dominate, is a real design decision, not
   a one-line change) -- flagged here as a newly-discovered, real, confirmed defect for a follow-up
   ticket, not assumed away.

### Open questions for Plan (not decided here)

- Does making `test_bravery_quartile_combat_rate_2x` pass require (a) fixing only the quartile-math
  statistical bug (e.g., correlate across the full alive population instead of an extreme-pair
  comparison, or enforce a minimum-population guard), (b) recalibrating the 2x threshold with real
  evidence (per AC2's own explicit allowance), or (c) both? The "no bravery correlation across the
  full population" finding above suggests (a) alone may not be sufficient without also addressing why
  `CombatEngageScorer`'s bravery term (40/100 of its own range) isn't producing a strong enough signal
  against race-timing/competing-goal noise at this population scale.
- Should the newly-confirmed `retention_margin`/`current_max` normalization defect be filed as a new
  ticket now (real, confirmed, but not blocking this ticket's own AC2)? Recommended, not decided here
  -- it's a genuine STRAT-185/186 gap between documented intent ("switching requires margin or
  explicit emergency") and actual behavior (emergency-equivalent System-B candidates can never clear
  a locked System-A current, full stop).
- `GoalKind.RESOLVE_BLOCKER` beating `combat_engage` for hero 6 (a same-system, System-B-vs-System-B
  competition, unrelated to the two-system precedence bug this batch addressed) was observed but not
  investigated further -- flagged as a possible additional confound in any recalibration attempt, not
  confirmed as a bug.

### Correction (post-batch, architecture review finding)

Line 24's original citation of `docs/simulation/domains/adventure_contract.md` as
`status: authoritative` is factually wrong -- verified via `git blame` this session: the doc's real
frontmatter has been `status: active` since its creation (commit `2729f3cc3`, 2026-06-13), never
`authoritative`. This does not change any substantive finding above -- the doc still exists, still
made the stale 4.92x/System-A claim, still needs correcting -- but `status: active` docs don't carry
CLAUDE.md's Authoritative Mechanics Rule "100% semantic parity, same-session" force the way
`status: authoritative` docs do. Left uncorrected in the original line 24 text above (historical
record of what was believed true at investigation time); flagged here instead, per this session's own
"document carefully, avoid misdirection" convention.
