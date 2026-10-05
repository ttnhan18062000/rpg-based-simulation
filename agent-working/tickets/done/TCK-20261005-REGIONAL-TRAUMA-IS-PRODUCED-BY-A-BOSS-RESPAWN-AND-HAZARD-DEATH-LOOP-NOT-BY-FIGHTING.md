---
status: historical
layer: world
authority: P0
audience: agent
ticket_id: TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING
phase: done
date: 2026-10-05
tags: [world, combat, investigation]
---

# TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING

## Title
232 of 233 deaths on `frontier_living_world` are hazard drain with no killer, 158 of them world bosses that
spawn every ~100 ticks and die within a few ticks at fixed tiles — so every regional-trauma figure this
project has measured comes from a respawn-and-die loop, not from combat

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
Measured by `rpg-implementer-2` closing out the contested-zone death split (`audit_mode`,
`max_tick_budget_ms=1e9`, seed 42, `frontier_living_world` run twice **byte-identical**, so these are values;
base `54c31ee73`, stack on `main` `7a9f302db`). Full write-up in that ticket's `investigation.md`.

**The finding:**
- `frontier_living_world`, 233 deaths: **232 are `HAZARD` drain with no killer. 1 is `DEFEAT`.**
- **158 (68%) are `WORLD_BOSS` deaths.** A boss appears from tick 2111 roughly every 100 ticks, one each in
  `goblin_camp` and `bandit_road` (79 + 79), and dies of hazard drain within a few ticks at a handful of
  fixed tiles.
- 68 more are goblin/orc warrior hazard deaths at two spawn tiles.
- Credited trauma: `goblin_camp` **117**, `bandit_road` **116**, **every other region 0** — exactly the two
  regions that cross the instability threshold of 50.

**Why it happens. CORRECTED 2026-10-05 — the planner's first mechanism was misleading and is withdrawn.**

The planner originally wrote: "`data/content/social/factions.yaml` declares `hazard_immunities` for 10
factions; **`monster_horde` declares none**". That grep result is true but the inference drawn from it was
wrong, and `rpg-designer` caught it. **`monster_horde` is not a catalog faction at all** — there is no entry
for it in `factions.yaml` (planner re-verified: zero matches); it is a `legacy_engine_bucket`. So "it declares
no immunities" says nothing about any designed population.

**The corrected mechanism:** `spawn_monster` gives the spawned boss **no catalog faction**, so it falls back
to the bare legacy bucket and inherits no declared endurance. It then takes
`hazard_level * (1 + calamity_intensity) * 10` HP/tick in a region authored at hazard 3.0 (`goblin_camp`) or
2.0 (`bandit_road`) and dies within ticks.

**This also means the goblins are not the ones dying — and that is now an open question, not a fact.**
`goblin_warband` **is** a catalog faction and **is** immune to `NATURAL_TERRAIN`
(`factions.yaml:43,51`), and **both loop regions declare `hazard_kind: "NATURAL_TERRAIN"`**
(`goblin_camp_conflict.yaml:14` at level 3.0, `bandit_road_trade_pressure.yaml:14` at level 2.0) — all
planner-verified. So a `goblin_warband` entity should take **zero** drain in either region.

**Leading hypothesis, to be tested in scope 1, not assumed:** the 68 "goblin/orc warrior" hazard deaths
have the same cause as the boss — they are `spawn_monster`-created entities that received no catalog faction
and therefore lost their declared endurance. If that holds, the defect is **not boss-specific**: it is that
runtime-spawned monsters are stripped of the faction endurance their catalog counterparts have, and the boss
loop is its most visible symptom.

**Ruled out as a fix, per `rpg-designer` and the owner's 2026-07 ruling**
(`TCK-20260701-HAZARD-NATIVE-IMMUNITY`): granting immunity to the legacy bucket. Endurance is declared per
faction for that faction's own in-fiction reason, never derived from location or hostility, and "a hazard
nobody is flagged as enduring must hurt every faction present". Giving the bucket immunity would hand every
unaffiliated monster endurance for no fiction reason. The correct shape is to give the boss a **real faction
with its own declared endurance** — which is boss feature design, and therefore deferred.

**What this invalidates, and it is most of this week's trauma reasoning:**
1. **Regional trauma is not a record of bloodshed on the current corpus.** The Mechanics Bible describes
   trauma as recent bloodshed; on `frontier_living_world` it is a boss respawn counter.
2. **ENV-06's threshold reachability rests on this loop.** Trauma crosses 50 only in the two loop regions.
   The planner previously retired a caveat about ENV-06 reachability on the strength of those crossings; that
   retirement is **withdrawn** — the threshold is reachable, but only because of this defect.
3. **`TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`** (P1) measures
   entities fleeing on trauma 2.3-3.0. Those trauma values are produced by this loop. The units mismatch it
   describes is still real arithmetic, but the *observed* flee behaviour is a consequence of boss respawns.
4. **`TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION`** removes the growth cap per owner
   decision 12. Hazard drain is what kills the bosses; their deaths raise trauma; trauma above 50 drives hazard
   growth. **That closes a positive feedback loop** — more hazard, faster deaths, more trauma, more hazard,
   with trauma decaying at 0.0005/tick against growth at 0.01/tick. This must be understood before that ticket
   lands.
5. **The world-boss deferral collides with it.** Owner decision 10's amendment (both bosses deferred; memo
   row 10, catalog `ENV-06`) states a boss spawn "is never evidence for any decision here". **The deferred
   feature is currently generating 68% of the deaths that every trauma measurement rests on.** Deferring the
   feature did not stop the loop.

**Why P0.** It is not a cosmetic miscount: it is the input to trauma, calamity, hazard growth, panic/flee
appraisal and `ENV-06`, and it silently redefines what all of them mean. Every before/after on this corpus is
measuring a respawn loop unless it is excluded.

**Not established:** whether the loop exists on worlds other than `frontier_living_world` (four other worlds
were measured for the zero rows but not for the boss cadence), whether bosses are meant to spawn in a hazard
region they cannot survive, and whether the spawn cadence (~100 ticks) is itself correct.

## Provenance and mechanism (added 2026-10-05 from `rpg-designer`, planner-verified)

**Which path.** `WORLD_BOSS` deaths come from `check_for_boss_spawn`'s region branch
(`src/world/boss.py:~100`), which spawns an `ancient_sentinel` retagged `world_boss` at the **region
centre**. `:226` is a separate LAIR-place `dragonkin` occupant. Both use the same gate.

**Why it fires now — the root cause is a previous reachability fix.** The gate is
`maturity >= BOSS_SPAWN_THRESHOLD AND trauma >= BOSS_SPAWN_TRAUMA_THRESHOLD`, and those constants are
**`2.0` and `8.0`** (`boss.py:26-27`, planner-verified). They were lowered from **50 / 20** by
`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` as a reachability fix, recorded as
**provisional in D-05**. That change is what turned the loop on.

**Why it sustains itself.** A few real deaths push trauma to 8. The boss spawns into hazard it has no
immunity to (a legacy `MONSTER_HORDE` entity with no catalog `hazard_immunities`), dies within ticks,
adds +1 trauma, and respawns because the "one active living boss per region" condition is satisfied the
moment it dies.

**Spawn position couples this to decision 13.** `bandit_road`'s centre is **(70,50)**, which the planner
confirmed lies inside **all three** of `bandit_road`, `near_forest` and `wolf_den` — the triple overlap.
So the region-precedence rule decides **which hazard kind and level kills the boss**, and the two
tickets are not independent.

**A second, separate defect found in the same code.** `boss.py:109-110` comments "Rule: never inside
town/sanctuary" and implements `if abs(cx) < 20 and abs(cy) < 20` — a radius around the **world origin
(0,0)**, not a check against any town. The guard is not town-aware at all. Planner-verified. **File
separately rather than fixing here.**

## Scope
1. **Confirm the loop and its cadence** on `frontier_living_world`, and measure whether it occurs on the other
   corpus worlds. All runs under `audit_mode` with the budget disabled.
2. **Establish the intended semantics before changing anything. This needs an owner ruling, not an
   implementer's choice.** The candidates are not equivalent:
   (a) `monster_horde` should have hazard immunities — **REJECTED by `rpg-designer`**: its premise is wrong
       (no such catalog faction; see the corrected mechanism above) and granting the legacy bucket immunity
       contradicts the owner's 2026-07 endurance ruling. The correct (a)-shaped fix is a real faction with
       declared endurance for the boss, which is deferred feature design.
   (b) bosses should not spawn into a region whose hazard kills them — **REJECTED for now**: redesigns a
       deferred feature, which row 10 forbids ("neither tuned, retired nor wired to new inputs") and row 7
       parks. Revisit when bosses are designed.
   (c) hazard drain should not apply to boss-kind entities — **REJECTED**: an exemption by entity kind is
       exactly the coupling the 2026-07 ruling removed.
   (d) trauma should not count ambient attrition — **RECOMMENDED by `rpg-designer` as a new rule, draft
       `ENV-07`**: "Regional trauma counts deaths with a violent cause. Ambient attrition (environmental
       drain, natural death) is exposure, not unrest, and does not count." Worded as **violent cause**, not
       "has a killer", so a future declared catastrophe (a plague) can be admitted by its own decision rather
       than excluded by definition. The catalog is **silent** today: Bible 05 §2 says regions react to
       "violence and activity" but adds +1 for "every entity death"; `ENV-06` calls the result "unrest".
   (e) the boss branches inert behind a default-OFF flag — **RECOMMENDED as a NEW owner decision, not as
       enforcement of the existing deferral.** The drafted deferral forbids *touching* the branch (row 10:
       "neither tuned, retired or wired to new inputs"; `ENV-06`: "must neither tune nor retire the boss
       branch"), so making it inert is arguably *retiring* it — the deferral as written **forbids (e) rather
       than implying it**. The owner must say explicitly that "deferred now means inert". Precedent: the
       default-OFF `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` on the same trigger. `rpg-designer` notes this
       reverses its earlier "lair stays live, nothing removed" and must be presented as a reversal.
   **(d) and (e) are independent of each other** and should be two separate owner decisions. (d) is the
   semantic fix; (e) makes the deferral honest.
   **(d) and (e) are the two that would retroactively clean every existing measurement**; the others only stop
   future loops. Report the options with evidence; do not pick one.
   **`rpg-designer`'s recommendation, 2026-10-05, for the owner — not an instruction to implement:** make
   **both** boss branches inert behind a flag defaulting **OFF** while the feature is deferred, i.e. option
   (e). Precedent: `ENV-06` already records the magical/demonic spawn path as
   `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`, default OFF, untouched. The designer notes this **reverses**
   what it previously told the owner ("nothing gets removed, the lair boss stays live") — a default-OFF flag
   is still not removal, but it does stop a live path, so it must be presented to the owner as a reversal and
   not as housekeeping.
   **The trauma-semantics question is going to the owner separately, by the designer**, with options
   (A) every death counts, as today; **(B) only deaths with an agent cause count** (its recommendation);
   (C) hazard deaths count at reduced weight. **The decisive measurement: even with the bosses removed, the
   remaining 74 deaths are still hazard drain, against 1 `DEFEAT` in 10,000 ticks** — so trauma counts
   environmental attrition whether or not the loop is stopped, and under (B) trauma on this corpus goes to
   roughly zero. **Hold every trauma-producer change until that is ruled.**
3. **Quantify the contamination.** For each corpus world, deaths split by cause (`HAZARD` / `DEFEAT` / other)
   and by whether the victim is a boss. This is the number that says which of this week's figures survive.
4. **Re-express the trauma figures excluding no-killer deaths**, as a parallel series. Do not change the
   producer yet — this is to show the owner what trauma would read if it counted only bloodshed.
5. Only after the owner rules on scope 2: implement, with a disabling control, a divergence entry and a parity
   ledger update.

## Out of Scope
- Implementing any of (a)-(e) before the owner rules.
- Un-deferring or tuning world bosses. **Deferred by owner decision 10, both bosses.** This ticket reports that
  the deferral is not holding; it does not re-open the feature.
- The region-precedence rule (decision 13) — though note the interaction in Related Tickets.
- Changing `hazard_level` authored values, or the growth cap (owner decision 12, separate ticket).

## Acceptance Criteria
- [x] Loop confirmed with cadence on `frontier_living_world` (first boss spawn tick 2101, then every 100 ticks in each of two regions, 79 + 79); present in 15 of the 24 corpus worlds; absent in the rest.
- [x] Per-world death split by cause and by boss/non-boss victim (`probes/contamination_24_worlds_*.jsonl`).
- [x] Options (a)-(e) presented with evidence (`investigation.md` section 6); decisions 14 (flag over all three boss branches, the calamity branch included) and 15 (`ENV-07`) were then ratified by the owner and implemented. (a), (b) and (c) were rejected by the designer; the spawn-path faction defect is a separate ticket and is not part of this one.
- [x] A parallel trauma series excluding no-killer deaths for `frontier_living_world` and two other worlds (`investigation.md` section 4).
- [x] Which existing tickets' figures survive and which do not is stated (`investigation.md` section 7).
- [x] Nothing in `src/` changed before the owner ruled; the implementation follows decisions 14 and 15.
- [x] Disabling control: the boss flag is default OFF and a test pins flag-OFF inert and flag-ON unchanged on all three branches; trauma before and after measured under `audit_mode` (section 8).
- [x] Divergence entries DEV-010 and DEV-011 and parity-ledger entries WORLD-125 and WORLD-126.

## Related Tickets
- `TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA` — the
  measurement that found this. Its verdict (**H3** for own ground, H1 narrowly, H2 unsupported, H4 inseparable
  from H3) stands independently.
- `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` (P1) — its trauma inputs
  come from this loop.
- `TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION` — **closes a feedback loop with this
  one; read this ticket before landing that one.**
- `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER` — hazard drain for a tile is taken from the same
  position-to-region lookup, so a precedence rule changes **which hazard drains those spawn tiles**, not only
  which region is credited. Decision 13 is therefore also a hazard-semantics decision.
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` and `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`
  — the trauma/calamity chain this feeds.

## Related Docs
- `docs/mechanics/05_world_evolution.md` — regional trauma as recent bloodshed, and the instability threshold.
- `docs/world_rules/space-environment/environment.md` — catalog rule `ENV-06` and its deferral bullet.
- `docs/plans/systemic_world/owner_decision_memo.md` — decision 10 and its both-bosses amendment, including
  "a boss spawn of either kind is never evidence for any decision here".

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-.../investigation.md` and
  `probes/geometry.jsonl` (static geometry, all 24 worlds, owned-tile shares).

## Related Code Areas
- `data/content/social/factions.yaml` — 10 factions declare `hazard_immunities`; **`monster_horde` declares
  none** (planner-verified); `undead_remnants` declares only `UNDEAD_CORRUPTION` (line 126).
- `src/world/boss.py:100`, `:226` — the `BossService` maturity/trauma spawn gate.
- `src/world/environment.py:36` — `calculate_hazard_drain`, `hazard_level * (1 + calamity_intensity)`.
- The trauma producer that credits a death to a region, and the position-to-region lookup it uses.

## Assumptions / Open Questions
- **Lane.** Lane B (`rpg-implementer-2`), world domain. Measurement and reporting only; **no `src/` change is
  authorised by this ticket.**
- Open: are world bosses *supposed* to be hazard-immune? `undead_remnants` is immune to its own region's
  hazard kind, which suggests the content pattern is "a region's own population survives its own hazard" —
  `monster_horde` having no immunities at all may simply be a content omission.
- Open: `quest_dense_frontier` crashed at kernel construction (artifact-manifest JSON decode error) and was not
  measured. Unrelated to this defect but unexplained; worth its own ticket if it reproduces.
- The contested-zone split moves with the base (triple zone 74 pre-#347 vs 34 now) because **where bosses die
  moves**. The zero rows and the H3 verdict do not move.

## Implementation Notes
Implemented under owner decisions 14 and 15. `src/core/violent_cause.py` defines the one set of violent death causes (`VIOLENT_DEATH_OUTCOME_KINDS`, derived from the terminal combat outcomes) and `is_violent_building_destruction`; `WorldDynamicsSystem.resolve_dynamics` and `apply_plan.py`'s building `+2.0` consult them. `ENABLE_WORLD_BOSS_SPAWN` (default OFF, registered in `feature_flags.py`) gates `BossService.check_for_boss_spawn`, `BossService.check_for_lair_spawn` and the calamity boss in `CalamityService.process_world_dynamics`; the calamity trigger still advances `last_calamity_tick`. Not touched: spawn siting, the origin-radius town guard in `boss.py`, boss faction identity, the spawn-path faction defect (separate ticket), `src/core/state.py`. Measurement and findings: stored artifacts `investigation.md`, sections 1-8.

## Test Summary
New: `tests/unit/world/test_world_boss_spawn_flag.py` (7), `tests/unit/core/test_violent_cause.py` (10), `tests/unit/engine/test_trauma_counts_violent_cause_only.py` (6). Seven existing tests that asserted a boss spawn now set the flag ON explicitly (recorded as the consequence of decision 14). Full CI lane set: see the closing note.

## Files Changed
`src/core/violent_cause.py` (new), `src/engine/world_dynamics.py`, `src/engine/apply_plan.py`, `src/world/boss.py`, `src/world/calamity.py`, `src/domains/optimization/feature_flags.py`, `docs/mechanics/05_world_evolution.md`, `docs/guidelines/intentional_divergences.md` (DEV-010, DEV-011), `docs/parity_ledger/world_dynamics.yaml` (WORLD-125, WORLD-126), the three new test files and three edited test files, stored artifacts and probes.

## Completion Summary
Regional trauma on this corpus was a respawn-and-die counter, not a record of bloodshed: 65% of 2,144 deaths in 24 worlds were world bosses dying of hazard drain at spawn tiles, 98.5% were hazard drain, and none of the hazard deaths had been wounded first. Owner decision 15 (`ENV-07`) makes trauma count only violent-cause deaths, and decision 14 makes all three boss branches inert behind a default-OFF flag. Measured under `audit_mode` (seed 42, 10,000 ticks): `frontier_living_world` trauma 110.0 to 0 (peak 4.42), `simq_scale_stress_seed42` 104.0 to 0 (peak 1.96), **identical with the boss flag ON** because the boss gate no longer opens. The runtime-spawned warriors' hazard deaths (no catalog faction) remain and are a separate ticket. Every "trauma crossed 50" figure taken before this change measured the loop, and `ENV-06` calamity reachability through trauma is gone in default runs.

