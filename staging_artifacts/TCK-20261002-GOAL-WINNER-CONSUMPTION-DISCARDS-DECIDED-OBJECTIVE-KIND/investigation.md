---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND
artifact_type: investigation
tags: [strategy, cognition, combat]
---

# Investigation — goal-winner consumption discards the decided objective kind

The ticket body carries the defect statement, the measured verdict and the two scope guards. **This
file is the evidence record**: the reproducible probe method, the full per-world numbers, and the
Scope 4 per-`GoalKind` audit that the ticket requires but does not contain. It does not restate the
ticket's narrative.

## 1. Probe method — reproducible, read-only

Script lived in the session scratchpad only, never in the repo. `git status --porcelain src/` was clean
after every run.

Reused `stored_artifacts/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION/investigation.md`'s
own method, deliberately, so the numbers are comparable to the chain's earlier measurement:

- real `Kernel.tick_once()` loop — **not** direct object construction; the defect is in the wiring, so
  a unit-level probe proves nothing
- `PROD_SMALL`, `DeterministicRNG(42)`, `flags={"no_frame_pacing": True, "no_replay": True}`
- **`executor=LocalSequentialExecutor()` passed explicitly** — that artifact's own guard against
  concurrent-evaluation probe corruption. Omitting it invalidates the run.
- worlds compiled via `WorldRepository.load_world_with_context` + `WorldCompiler.compile(spec, 42, context=…)`
- class-attribute wraps, all restored in `finally`: `ScoreModifierSystem.apply_modifiers` (re-deriving
  the winner with `intelligence.py`'s own rule — sort `(-utility, kind)`, skip `utility < 20.0` or no
  target), `CombatEngageScorer.score`, `TacticalDecisionSystem.evaluate_entity_intent`, the real
  `FactionSemanticsService` singleton's `is_hostile_compat`, `ObjectiveIntentResolver.resolve`,
  `CombatResolutionSystem.resolve_attack` / `resolve_multi_attack`, `CombatActions.execute_attack`
- plus a per-tick read-only scan of every entity's `strategic.projects` for `kind == combat_engage`

Interpreter: the repo venv (`…/rpg-based-simulation/.venv/bin/python3`). Plain `python3` lacks pydantic.

**Worlds / seed / ticks:** `crowded_frontier` (38 entities), `frontier_living_world` (49),
`quest_dense_frontier` (6) — all seed **42**, **2000 ticks**.

**Comparability constraint:** every number here is **post-`TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`**,
which dropped measured combat volume 85-96%. Do **not** compare against pre-fix figures in older
tickets.

## 2. Goal competition — `COMBAT_ENGAGE` is the most frequent winner

| world | competitions | `combat_engage` wins | share | top winner | distinct CE projects |
|---|---|---|---|---|---|
| `crowded_frontier` | 1767 | **485** | 27.4% | region_stabilization (611) | 27 |
| `frontier_living_world` | 1744 | **568** | **32.6%** | **combat_engage** | 36 |
| `quest_dense_frontier` | 410 | 0 | 0% | town_return (261) | 0 |

`quest_dense_frontier` is a **real zero reported as a finding**: `CombatEngageScorer` returned
`utility == 0.0` in **410/410** calls — never a raw-enum-different-faction live neighbour within radius
10 for its 6 entities. It discriminates nothing. **The verdict therefore rests on two worlds, not
three.**

## 3. Objective kind produced, and what consumes it

| world | `reach_location` samples | `defeat_enemy` |
|---|---|---|
| `crowded_frontier` | **50 279 / 50 279 (100%)** | 0 |
| `frontier_living_world` | **60 835 / 60 835 (100%)** | 0 |

`ObjectiveIntentResolver.resolve` was called **only** with `investigate` objectives (360 / 154 times,
all → `MOVE_TO`) and **never once** for a `combat_engage` project's objective. `tactical.py:262`
intercepts `obj.kind == "reach_location"` in a dedicated inline branch and returns before the resolver;
`tactical.py:308` excludes `DEFEAT_ENEMY` from the resolver path as well, routing it to the
hostile-engagement branch instead. **`ATTACK_TARGET` is unreachable on this path because the resolver is
never asked, not because the mapping is wrong.**

What the objective does instead (branch-confirmed by calling `_resolve_target_position` on live
objectives):

| | `crowded_frontier` | `frontier_living_world` |
|---|---|---|
| position source = `obj.target_position` (stale), `node_id`/`building_id` both `None` | **100%** | **100%** |
| arrived-noop (`tactical.py:297-299`, bare `EntityUpdate`) | **209/216 (96.8%)** | **14/20 (70%)** |
| en-route → `NavigationUpdate(WANDER)` | 7 (3.2%) | 6 (30%) |
| live target ≥3 tiles from the stale point | **183/212 (86%)** | 13/20 |
| objective samples not `ACTIVE` | **0 of 50 279** | **0 of 60 835** |

Distance to the **live** target (`crowded_frontier`): 9 at 0-1, 20 at 2-3, **176 at 4-10**, 8 at >10.

This is the third defect, now owned by
`TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES`.

## 4. Why `hostiles` is empty — the discriminating measurement

For every tactical call made while the entity held an ACTIVE `combat_engage` project, the target's state
was recomputed independently:

`crowded_frontier` (216 calls):
- **204 — alive, in the perception-filtered neighbour list, perception gate passed, raw=True, `catalog=False`**
- 4 — out of range / not perceived, catalog=False
- 3 — out of range / not perceived, catalog=True
- 1 — target dead

`frontier_living_world` (20 calls): 11 alive+perceived with `catalog=False`; 2 alive+perceived with
`catalog=True` (see the caveat in §7); 7 out of range.

**`hostiles` non-empty: 0 / 216 and 0 / 20.** In the dominant case the *only* thing excluding the
target was the catalog hostility test. **Reading B is falsified** — proximity gating does not rescue the
branch, because the same catalog test rejects the target the scorer chose.

Raw-enum vs catalog on the targets actually selected (catalog called exactly as
`LegalityServiceV2._is_engagement_hostile` does: `EntityIdentityResolver().resolve(…).faction_id` with
`get_faction_id_str` fallback, `RelationContext(distance=1.0, combat_engaged=True)`,
`is_hostile_compat`):

| world | selections | raw hostile | catalog hostile | **raw-only** | catalog-only |
|---|---|---|---|---|---|
| `crowded_frontier` | 683 | 683 (100%, by construction) | 314 | **369 (54.0%)** | 0 |
| `frontier_living_world` | 773 | 773 (100%) | 513 | **260 (33.6%)** | 0 |

Inside the 34-97% band `legality.py:516-544`'s own docstring cites. **Both are floors** — see §7.

## 5. Attack volume — decision path vs incidental

| world | decision-path `resolve_attack` | opportunity `resolve_multi_attack` | ratio |
|---|---|---|---|
| `crowded_frontier` | **2** (2 SURVIVE, 0 REJECTED) | **119** (99 SURVIVE, 9 DEFEAT, 5 REJECTED) | 1 : 59 |
| `frontier_living_world` | **3** (3 SURVIVE, 0 REJECTED) | **783** (201 SURVIVE, 17 DEFEAT, 536 REJECTED) | 1 : 261 |
| `quest_dense_frontier` | 0 | 0 | — |

**Both decision-path attacks came from entities that did NOT hold a `combat_engage` project.** From
CE-goal holders: **0 / 216 and 0 / 20 `ATTACK` emissions, and 0 rejections.** Reading C's mechanism is
confirmed; its predicted "decided then rejected" signature is refuted — the divergence bites upstream of
any attack decision, so nothing exists to reject.

This reproduces the chain's recorded shape (decision path 0-2 per 1000-2000 ticks vs incidental in the
hundreds-to-thousands) on today's post-fix code.

## 6. Scope 4 — per-`GoalKind` audit of the generic branch (AC requirement)

Four kinds have bespoke branches and never reach the generic `else`: `ADVENTURE_ROUTE` (:1576),
`SOCIAL_CONTRACT` (:1604), `REGION_STABILIZATION` (:1641), `OCCUPATION_CHANGE` (:1676). All four read
`obj_kind` from scorer metadata.

Everything else falls through to the generic `else` at :1707. Registered scorers
(`src/ai/goals/__init__.py:14-27`), with what each puts in `target_id`:

| GoalKind | scorer | `target_id` | resolves to | is `reach_location` correct? |
|---|---|---|---|---|
| HARVESTING | `HarvestScorer` | `str(nid)` — resource node | `resource_nodes[id]` | **yes** — arrival dispatches INTERACT |
| FATIGUE | `SleepScorer` | `str(best_bldg.id)` | `buildings[id]` | **yes** — arrival dispatches REST |
| HUNGER | `EatScorer` | `str(best_bldg.id)` | `buildings[id]` | **yes** — arrival dispatches EAT |
| RECOVER | `RecoverScorer` | `str(best_bldg.id)` | `buildings[id]` | **yes** |
| GUILD | `GuildNeedScorer` | `str(building.id)` | `buildings[id]` | **yes** |
| SOCIAL | `SocialScorer` | `"town_center"` | `target_position` fallback | **yes** — a genuine fixed place |
| TOWN_RETURN | `TownScorer` | `"town_center"` | `target_position` fallback | **yes** |
| COMBAT_RETREAT | `CombatRetreatScorer` | `"town_center"` | `target_position` fallback | **yes** — retreat really is to a place |
| RESOLVE_BLOCKER | `ResolveBlockerScorer` | `str(blocker.id)` | neither; coords parsed per blocker kind | **yes, with a caveat** — see below |
| **COMBAT_ENGAGE** | `CombatEngageScorer` | `str(nearest_hostile.id)` — **an entity** | nothing; falls to stale `target_position` | **NO — the only wrong case** |
| CRAFTING | *(no scorer registered)* | — | — | n/a |

**Conclusion, and it validates the chosen fix shape:** the generic branch's hardcoded `reach_location`
is **correct for 9 of the 10 registered fall-through kinds**. `COMBAT_ENGAGE` is the sole confirmed
defect. So the fix must be **additive** — read `metadata["obj_kind"]` with `REACH_LOCATION` as the
explicit fallback — and must not change any kind that publishes no `obj_kind`. A fourth bespoke
`elif` would also work but leaves the generic branch unable to express a correct kind for any future
scorer.

`RESOLVE_BLOCKER` caveat worth carrying forward: its scorer's own comment (`scorers.py:191-195`) records
that *"a `resolve_blocker` project that can never actually complete (e.g. an `access` blocker with no
parseable coordinates) starves every other goal indefinitely"*, and it guards that with a timeout on
already-failed blockers. **That is existing in-repo precedent for the non-termination half of the third
ticket** — the same starvation shape was found and guarded there, so the third ticket does not need to
invent a mechanism from scratch.

## 7. Floors, caveats, and what was not measured

- **The raw-only disagreement percentages are FLOORS, not exact.** The probe used
  `RelationContext(distance=1.0, combat_engaged=True)` — legality's own, permissive context — while
  `tactical.py:210-223` builds its context with the *real* distance, real `combat_engaged` and species
  ids. Direct evidence it matters: 2 `frontier_living_world` calls where the probe said `catalog=True`,
  target in neighbours and perceived, yet tactical's own `hostiles` was still empty. Real agreement at
  real range is **lower** than 46% / 66%; real disagreement is **higher** than 54% / 34%.
- **Opportunity-path rejection reasons unmeasured.** `resolve_multi_attack` filters illegal attackers
  internally and surfaces only an aggregate `outcome_kind`, so the 5 and 536 rejections carry no
  per-attacker `failure_reason`.
- **"0 objectives abandoned" is a floor claim.** Live projects were sampled per tick, so a project
  deleted between ticks would vanish rather than show a terminal status. 27 and 36 distinct CE projects
  did churn over 2000 ticks — what is absent is any *observed* terminal status.
- **Tactical call counts drift ±~3%** run to run (`tac_calls_with_ce_project`: 212 / 213 / 216 / 218
  across four identical-seed runs), while every **simulation outcome** was exactly reproducible (485
  wins, 2 decision attacks, 119 opportunity, every run). Believed to be the governor's latency-adaptive
  scheduling of brain evaluations; **not chased to root cause.** All per-call *ratios* above were stable
  across every run; absolute call counts are ±3.
- **One of three worlds contributes nothing** (`quest_dense_frontier`). `hero_guild_routing` and
  `metropolis` were not run; `metropolis` is in any case disclosed in the prior artifact as having
  spawn-collision data defects.
- **Instrument positive control held:** the probe did capture the 1 `ATTACK` emission per world from
  non-CE entities and their downstream `resolve_attack` dispatches (2 and 3), so the zero from the
  CE-holder bucket is a real zero, not a blind wrap. `PerceptionGate.can_perceive` was independently
  confirmed stateless/pure before relying on out-of-band calls to it.
