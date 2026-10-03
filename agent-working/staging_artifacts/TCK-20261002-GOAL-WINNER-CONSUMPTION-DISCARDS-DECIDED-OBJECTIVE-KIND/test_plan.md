---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND
artifact_type: test_plan
tags: [strategy, cognition, combat]
---

# Test plan — goal-winner consumption discards the decided objective kind

## Proof Plan

- **Level:** integration / mechanic-scenario. A unit test cannot prove this fix.
- **Proof kind:** behavioural, through a real `Kernel.tick_once()` loop, plus a measured before/after.
- **Oracle source:** `docs/mechanics/04_strategic_cognition.md` (goal hierarchy and dispatch) and the
  `docs/parity_ledger/strategic_cognition.yaml` entry for goal dispatch. The behavioural oracle is: *a
  goal the entity decided on is the goal the engine executes.*
- **Expected effect:** `ATTACK` emissions from entities holding a won `COMBAT_ENGAGE` goal rise from a
  measured **0** to a non-zero number, bounded above by the fraction of selected targets the content
  catalog agrees are hostile.
- **Selected commands:** see "Scoped commands" below.

**The single most important constraint: the defect is in the wiring.** A unit test that constructs an
`ObjectiveState` and calls `ObjectiveIntentResolver.resolve` passes **both before and after** the fix and
proves nothing. Worse, the investigation measured that the resolver is **never consulted** for these
objectives at all. Every assertion that matters must run through a real kernel tick.

## New tests

**T1 — the nine correct kinds do not change (regression guard, write this first).**
`tests/unit/strategic/` (co-locate with existing winner-consumption tests). For each registered
fall-through `GoalKind` whose scorer publishes **no** `obj_kind` — HARVESTING, FATIGUE, HUNGER, SOCIAL,
TOWN_RETURN, COMBAT_RETREAT, RECOVER, RESOLVE_BLOCKER, GUILD — assert the materialised objective is still
`REACH_LOCATION`. `investigation.md` §6 is the source of that list and of *why* each is correct. This is
the test that catches the plausible regression, so it goes in before the fix.

**T2 — the fallback is explicit, not incidental.** Assert that a candidate with `metadata == {}` and one
with `metadata == {"obj_kind": None}` both yield `REACH_LOCATION`. Guards against a bare
`.get("obj_kind")` writing `None` into `obj.kind`.

**T3 — `hostiles` is non-empty for a catalog-hostile target.** The real gate. Scenario with two entities
whose factions the **content catalog** calls hostile, within perception range. Assert
`TacticalDecisionSystem`'s `hostiles` list is non-empty for the entity holding the won `COMBAT_ENGAGE`
project. Measured before: **0 / 236** across both worlds, including all 12 calls at ≤1 tile. If this
fails, nothing else about the fix matters.

**T4 — end-to-end: decided combat is executed combat.** `tests/mechanic_scenarios/`. Real
`Kernel.tick_once()`, seeded, `LocalSequentialExecutor()`. Two catalog-hostile entities adjacent or
near-adjacent. Assert, in one run: `COMBAT_ENGAGE` wins; the objective's kind is `DEFEAT_ENEMY`; and a
real attack resolution occurs attributable to that entity. This is the ticket's headline AC.

**T5 — negative control: a raw-enum-hostile-but-catalog-friendly target is NOT attacked.** Two entities
sharing a catalog-friendly relation but differing in the raw 4-value `Faction` enum — which the
investigation measured as 54% / 33.6% of all selected targets. Assert no `COMBAT_ENGAGE`-driven attack.
**This is the test that proves step 1a actually changed the predicate** rather than the scorer merely
getting luckier. Without it, T4 could pass on a target both tests happen to agree on.

**T6 — scope guard, score scale unchanged.** Assert the generic branch still produces
`ProjectState.kind` as a `GoalKind` (not a `ProjectKind`) and `score == best_candidate.utility`. Pins the
ticket's scope guard so a later "type cleanup" fails loudly instead of silently flipping the ceiling from
100.0 to 2.9.

**T7 — determinism.** Two identical seeded runs produce identical canonical state hashes. Then the
existing determinism/canonical/replay/fingerprint/hash/checkpoint sweep.

## Existing tests to run (scoped — do not run the whole suite)

```
pytest tests/unit/strategic/ tests/unit/ai/ -q
pytest tests/mechanic_scenarios/ -q
pytest tests/unit/engine/ tests/unit/movement/ -q
pytest tests/integration/ -q -m "not slow"
```
Then the determinism sweep as the repo runs it (canonical / replay / fingerprint / hash / checkpoint).

Specifically re-run and inspect, because they sit on the changed paths:
- any test touching `ObjectiveIntentResolver` or `_resolve_target_position` —
  `TCK-20260807-TOWN-RETURN-TARGET-RESOLUTION-BUG`'s own tests especially, since `"town_center"` scorers
  share the fallback
- `tests/mechanic_scenarios/test_perception_pipeline_wiring.py` — exercises the same tactical path
- anything asserting `_is_engagement_hostile` or `is_hostile_compat`, which step 1a adds a caller to
- `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`'s own tests

## Fixtures and expected movement

**Expect recorded-hash and event-count fixtures to move.** This changes which entities attack, so
combat-derived state will differ. Per the ticket: **identify and explain each moved fixture; never
regenerate silently.** If a fixture's new value cannot be explained by "these entities now attack and
previously did not", stop — that is a real finding, not a fixture refresh.

Build a **frozen fixture** only if a scenario needs one, and keep it minimal: the entities the assertions
actually read plus ~10-15 for realism, not a whole corpus world.

## Coverage against the required classes

| class | covered by |
|---|---|
| normal flow | T4 |
| edge cases | T2 (empty / `None` metadata), T5 (enum-vs-catalog divergence) |
| failure modes | T3 (the empty-`hostiles` blocker), T5 |
| regression-prone paths | T1 (the nine correct kinds), T6 (score scale) |
| architecture — read-only logic did not mutate live state | the scorer stays pure; assert it returns a `GoalScore` and writes nothing |
| architecture — authoritative apply path used | T4 runs through `Kernel.tick_once()`, not a direct mutation |
| architecture — typed records round-trip | T7 canonical hash + the existing serialisation sweep |

## Known gaps, stated rather than left implicit

- `quest_dense_frontier` produced **0** `COMBAT_ENGAGE` wins in 410 competitions, so it cannot serve as a
  measurement world. Use `crowded_frontier` and `frontier_living_world`.
- The before-baseline's raw-only percentages (54.0% / 33.6%) are **floors**, measured under a permissive
  `RelationContext`. Step 1a uses the real distance, so the after-numbers are not a like-for-like
  comparison against them. Report both contexts if feasible; if not, say which was used.
- Tactical **call counts** drift ±~3% run to run from the governor's latency-adaptive brain scheduling,
  while simulation outcomes were exactly reproducible. Assert on **outcomes and ratios**, never on an
  absolute tactical-call count.
- The arrived-noop rate (96.8% / 70%) is expected to stay high. That is
  `TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES`'s defect. Do not
  treat it as this ticket failing, and do not fix it here.
