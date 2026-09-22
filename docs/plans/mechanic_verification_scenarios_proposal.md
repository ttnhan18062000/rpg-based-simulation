---
status: active
layer: simulation
authority: P1
audience: agent
tags: [simulation-quality, testing, architecture]
---

# Plan — Production-Like Mechanic Verification Scenarios

**Status, scoped 2026-09-15. This is a design proposal, not an implementation — nothing here is
built.** Answers "does this specific mechanic work when its own conditions are met?" with a small,
deterministic, production-like scenario and an explicit assertion about the mechanic — replacing
the 2000–5000-tick hand-instrumented corpus probes this arc has been running all week to answer
exactly this question, at high cost and with a real non-determinism confound (the census's own
first `stability-check` run found 382 files differing between two identical runs of the same
world).

---

## 1 · Division of labor (settled before any design choice below)

Three instruments, three questions, no overlap — stated explicitly so this component is never
cited for what another one measures, the way SimQ was nearly cited as evidence a narrow change
(the combat posture gate) was safe when its own corpus runs at a scale too small to see it at all:

| Instrument | Question | Shape |
|---|---|---|
| **SimQ** | Is the simulation, broadly, healthy? Is the economy working, is the world interesting, did the numbers drift? | Corpus-wide, emergent, pillar-scored. Unchanged by this proposal. |
| **The execution census** (`tools/execution_census.py`) | Which branches does nothing in the corpus ever exercise? | Branch coverage, differenced against unit tests. Points at *where* a mechanic scenario is needed. |
| **This component** | Does *this* mechanic work when its own conditions are staged? | Small, deterministic, production-like, one mechanic per scenario, one explicit assertion about it. |

This component is not built on SimQ's corpus or its pillar scoring — that machinery is shaped for
broad emergent measurement and would drag its own scale-blindness along. The certification-harness
path (below) is the right foundation because it is already per-scenario and per-run, not
corpus-aggregate.

## 2 · What exists today, read before proposing anything

`src/certification/harness.py::CertificationHarness.run_scenario()` +
`src/certification/scenarios.py` (the `COMBAT_ARENA_*` family) already solve real, hard pieces of
this problem:

- **A real, working reproducibility check**: every scenario run is executed twice (with a third
  sequential baseline run), and a hash mismatch is a real conformance failure
  (`ConformanceEvaluator.evaluate`'s hash-comparison path). This is the exact property the census's
  own `stability-check` had to invent from scratch for corpus worlds — the harness already has it,
  natively, for scenario runs.
- **A real watchdog/timeout loop**, proof-bundle persistence (`CertificationRecorder`), and hardware
  classification — genuinely reusable infrastructure, not combat-specific.
- **`ScenarioExpectations` / `ConformanceEvaluator`** — read directly
  (`src/certification/models.py`, `src/certification/conformance.py`). This vocabulary is entirely
  about **performance/stability conformance**: memory envelope, telemetry-gap detection, governor
  mode sequence, hash reproducibility, lifecycle outcome. It has **no concept of a gameplay-outcome
  assertion**. Every existing arena test (`tests/arena/test_arena_regional_control.py`, etc.) bolts
  a handful of plain Python `assert`s onto `result.final_state` after calling `run_scenario()` —
  ad hoc, per test, with nothing declaring "this scenario exercises mechanic X, and X's own success
  condition is Y." A scenario that fails today reports "conformance failed" or a bare
  `AssertionError somewhere in the test function" — not "the faction-sentiment mechanic didn't
  reach TENSE."
- **Scenario construction is 100% synthetic** (`ArenaInjector.build_regional_control_test` and its
  siblings hand-assemble entities via `V2EntityBuilder` — raw dataclass construction, e.g.
  `.identity(faction=Faction.MONSTER_HORDE)` using the **legacy enum**, not the catalog-driven
  `faction_id`/`alignment_bucket` system real corpus worlds use). **This directly contradicts the
  explicit "production-like, not synthetic" constraint** for the new component: `WorldCompiler` is
  never invoked, no catalog content is loaded, no real world-compile path is exercised. A fixture
  built this way proves a mechanic's *code* works against hand-picked component values; it does not
  prove anything about how that mechanic behaves against real, catalog-driven, compiled content —
  exactly the gap this arc's own investigations kept finding (e.g. the legacy-`Faction`-enum vs.
  catalog-`faction_id` divergence bugs filed this same session).

**Conclusion of this read**: the harness's *execution* machinery (tick loop, reproducibility,
watchdog, persistence, hardware/profile handling) is worth keeping and extending. Its *scenario
construction* approach and its *conformance vocabulary* are both real gaps against what this
component needs to be — not because they're badly built, but because they were built to answer a
narrower, combat-specific, synthetic-fixture question.

**This deserves more weight than a background note: it means `COMBAT_ARENA_*` currently proves
nothing about the real compile path, and it is a fourth instance of this arc's own week-long
theme, sitting inside the test suite itself.** `dead code` was one shape (a mechanism nothing
calls); `systems fed by nothing` was a second (a mechanism that runs and receives no input);
`mechanics whose preconditions depend on unvalidated world geometry`
(`docs/plans/world_composition_precondition_gap_finding.md`) was a third. This is a fourth,
distinct shape: **a verification mechanism whose coverage is narrower than its name implies.**
`COMBAT_ARENA_*` says "arena" — a reader reasonably assumes it exercises the real game, the way a
corpus world does. It doesn't; it exercises hand-picked component values through the same kernel
loop, with no catalog, no compiler, no content resolution in the path at all. This is the
strongest concrete justification for building this component on the real compiler rather than
extending what's there — and `quest_dense_frontier` compiling cleanly at 6 real entities is the
proof that small-and-real is achievable, not a tradeoff to negotiate away.

## 3 · Proposed shape

### 3.1 Extend the harness's execution machinery; do not replace it

Reuse `CertificationHarness.run_scenario()`'s tick loop, reproducibility check, and persistence
as-is or with minimal parameterization. The one combat-specific assumption inside it — the WIPE
stop condition (`alive_factions = {e.identity.faction for e in ... if e.combat.alive}`, using the
legacy enum) — should become opt-in per scenario category, not a hardcoded universal stop
condition; a knowledge-acquisition or cooperation scenario has no "wipe" concept at all.

### 3.2 Scenario construction goes through the real compile path

Replace `V2EntityBuilder`-only construction with `WorldCompiler.compile()` against small,
purpose-authored world specs — the same mechanism every corpus world already uses
(`WorldRepository.load_world_with_context` → `WorldCompiler.compile`), just sized down to exactly
what one mechanic needs. This is achievable without sacrificing "small": the existing corpus
already proves a real, compiled, catalog-driven world can be tiny (`quest_dense_frontier`: 6
entities; `crowded_frontier`: 38 entities across 4 regions) while still exercising real content
resolution, real faction semantics, real spatial placement — the actual system, not a stand-in for
it. New, minimal, dedicated world-module content would be authored per mechanic family (see §4),
composed the same way `data/worlds/*/world.yaml` composes existing modules. **Implementation
finding, resolving what was an open question here**: the real `resolve` step
(`python3 -m src.worldbuilding.cli resolve <world_id>`, the only supported way to produce the
`resolved/` assets `WorldRepository.load_world_with_context` requires) hardcodes its repository
root to `data/worlds` (`src/worldbuilding/cli.py`) — a separate `data/mechanic_scenarios/` root,
as originally proposed here, cannot use this tooling without a code change to the CLI itself, not
just a new directory. Scenario worlds live under `data/worlds/` with an explicit
`mechanic_scenario_*` world-id prefix and an `observability_tags: ["mechanic-scenario"]` tag on
their own module(s) instead, to stay distinguishable from real SimQ corpus worlds without needing
a second, parallel repository root. Whether to later add a real root-path option to the CLI (so
the originally-proposed separation becomes possible) is a small, separate follow-up, not a
blocker — the naming/tagging convention is sufficient to keep the two families apart today.

### 3.3 A declared assertion vocabulary, layered alongside performance conformance, not replacing it

A new, small set of typed assertion objects (exact API shape is the open question flagged in §5,
not decided here) that a scenario declares up front, e.g. in spirit (not final):

```python
MechanicScenario(
    id="FACTION_SENTIMENT_HOSTILE_ESCALATION",
    mechanic="faction_sentiment",
    world_spec="data/mechanic_scenarios/faction_hostility_escalation/world.yaml",
    ticks=300,
    assertions=[
        PairwiseTensionReaches(faction_a="...", faction_b="...", state="TENSE", by_tick=300),
    ],
)
```

Each assertion object knows how to (a) evaluate itself against a `CertificationResult`'s
`final_state` (or a captured per-tick trace, for assertions that need "did this ever happen," not
just "is this true at the end"), and (b) render a specific, named failure message — so a failed
run reports **"faction_sentiment: expected pairwise_tension >= TENSE by tick 300, reached AVOIDANT
(0.12)"**, not "conformance failed" or a bare `AssertionError`. This sits next to
`ScenarioExpectations` (performance/stability), not inside it — a scenario can fail on either axis
independently, and a report should say which.

**A hard requirement, confirmed necessary by the first scenario built against this proposal, not
a nice-to-have added in hindsight: a scenario that claims to verify mechanism X must produce a
different outcome when X's own precondition is present versus absent, and the differential itself
is the assertion — not a single pass/fail against one staged condition.** The first attempt at the
combat-judgement scenario staged only one condition (a real, correctly-mismatched hostile pair)
and observed zero attacks from the weak side — which looked like a pass, but the same zero-attack
outcome would have occurred whether the posture gate was working or entirely absent, because the
scenario never staged a case where the gate's own precondition (a pending attack decision plus a
recorded, risk-rejected posture) was actually present. Rerun as two conditions on the same forced
dispatch — posture recorded and risk-rejected, versus no posture recorded at all (the real,
documented "absence is not a verdict" case, not a monkeypatch) — and the outcome differed cleanly
(0 attacks vs. a real attack proceeding), which is what actually proves the mechanism is being
exercised. A scenario that cannot show this delta has not tested the mechanism, whatever its name
claims, and must fail — not pass — exactly the failure mode named in §2 as `COMBAT_ARENA_*`'s own
problem. This is a property the component's own scenario contract should enforce structurally
(e.g. requiring at least one "mechanism absent" condition per scenario declaration), not a
discipline left to whoever writes the next scenario to remember.

### 3.4 A parallel registry, not an extension of `ScenarioRegistry`

`COMBAT_ARENA_*` scenarios are legitimately synthetic and combat/stress-focused (50v50 stress
tests have no production-like analog and shouldn't need one). A new, separate registry
(`MechanicScenarioRegistry` or similar) keeps the two families from being conflated, and keeps
`get_scenario_expectations`'s existing combat-arena-shaped logic untouched.

## 4 · The six mechanic families, and what each scenario needs to stage

Drawn directly from what this arc built and struggled to verify by hand this week — each is a
real, already-known precondition, not a guess:

1. **Knowledge** — an entity acquires a lead and acts on it. Stage: an information source with a
   real fact, an entity positioned to query it, enough ticks for the query-response-action cycle.
2. **Cooperation** — a recruitment offer is accepted and a party forms. Stage: two compatible
   entities, a real recruitment-eligible situation, enough ticks for the offer/accept cycle.
3. **Combat judgement — built, 2026-09-15, known-positive confirmed.**
   `tests/mechanic_scenarios/test_combat_judgement_withdrawal.py`, against
   `data/worlds/mechanic_scenario_combat_judgement_withdrawal/` (real, catalog-authored
   `goblin_scout` vs `orc_warchief`, a genuine `"weaker_rival_fear"`-relationship mismatch, not
   invented stats). Two differential conditions on the same forced attack dispatch: posture
   recorded and risk-rejected (`"avoid"`) → 0 real attacks; no posture recorded at all → the
   attack proceeds. Confirms the posture-veto gate
   (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`) is the sole variable
   producing the difference — legality, range, and readiness are identical in both conditions.
   Surfaced its own real finding along the way, filed separately:
   `TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH` (the risk evaluation read this
   same 3.4x mismatch as acceptable at first contact, a question distinct from the gate's own,
   already-confirmed correctness).
4. **Faction sentiment** — hostile interaction accumulates pairwise tension to `TENSE`. Stage: two
   catalog-driven, genuinely hostile factions placed adjacent (using real `faction_id`, not the
   legacy enum), enough ticks for real combat and `pairwise_tension` accrual.
5. **World evolution** — trauma accumulates, a gate opens, a boss or lair occupant spawns. Stage:
   directly answers this session's own three parked findings
   (`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`,
   `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`) — a lair region with real hostile
   presence in range; heroes composed into a real high-hazard region.
6. **Campaign** — survivors carry identity and progression across an episode boundary. Stage: a
   real campaign-episode transition with at least one surviving entity, checking identity/
   progression fields persist correctly across the boundary.

Each family gets its own small world-module composition and its own assertion set — not one
mega-scenario trying to cover all six.

## 5 · What this component verifies, and what it does not (stated here, and in its own output)

**Five rules, all load-bearing, all already-observed rather than hypothetical (items 3, 4, and 5
added 2026-09-20, `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`, per direct peer
review of the first batch to use this component against `cognition`):**

1. **A scenario proves a mechanic works under staged conditions. It says nothing about whether
   real worlds produce those conditions.** That second question stays a content/composition
   question — exactly the distinction this arc's own
   `docs/plans/world_composition_precondition_gap_finding.md` had to learn the hard way after
   treating "never fires in the corpus" and "is broken" as the same question for most of this
   week. This component and that finding document are complementary, not redundant: the finding
   document names mechanics whose real-world preconditions are never staged; this component is
   how a future investigation would find out, cheaply, whether the mechanic itself is sound
   before or instead of chasing composition.
2. **A passing scenario proves the mechanic works under the specific conditions *that scenario*
   stages, not under all conditions.** Staged conditions are chosen, and a mechanic can work
   correctly in the staging and still fail in a configuration nobody thought to stage — the
   combat-judgement scenario's own first, naive attempt is a real instance of this: it staged a
   real hostile pair but not the specific precondition (a pending attack decision, a recorded
   rejected posture) the gate itself depends on, and the result looked like a pass without
   actually exercising the mechanism at all (see §3.3's differential-assertion requirement, added
   directly because of this).
3. **A negative or calibration verdict (`contradicted`/confirms a known `orphan`) built on "zero
   calls observed" is a stated requirement, not a habit: it must be paired with a direct-call
   positive control on the same code path.** An empty result alone cannot distinguish "never
   invoked" from "invoked and legitimately produced nothing" — and every dormant-mechanism finding
   in this arc lives in exactly that gap. The pairing is what makes a zero-result mean something.
   `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`'s `perception` and
   `quest_generation_sourcing` scenarios both do this (call the real function directly, outside the
   Kernel dispatch, and confirm it still produces real output); a scenario asserting only "the
   Kernel run produced nothing" without a positive control does not meet this component's bar for
   a negative verdict.
4. **A single scenario world is not a closed universe, and a `contradicted`/`orphan` verdict must
   say which of two possible backings it rests on.** Reusing one compiled world across scenarios
   (§3.2 favors reuse over authoring new worlds where possible) means a "zero calls observed"
   result could mean either "this mechanism is genuinely dead" or "this particular world never
   produces this mechanism's precondition" — two very different findings that look identical from
   inside one scenario. A qualifying verdict needs one of:
   - **(a) a static backing**: a never-instantiated/never-called fact that holds independently of
     which world is used (e.g. `perception`'s `PerceptionUpdatePhase` has zero constructors
     anywhere in `src/`, confirmed by a full-tree grep — no world could change that), or
   - **(b) a demonstrated backing**: the scenario's own world is shown, not assumed, to produce the
     mechanism's real trigger condition (e.g. `quest_generation_sourcing`'s scenario forces a real
     region to clear `generate_from_scar()`'s own `trauma_score > 0.3` threshold and the positive
     control confirms that precondition really does produce output when the function is called
     directly).
   Without either backing, the honest verdict is weaker than `contradicted` — "not observed in
   world X" is a real result, but not proof of dormancy, and recording it as `contradicted`/`orphan`
   would manufacture exactly the confident-false-negative shape this arc has already catalogued
   once (§3.2's misattribution class). Each scenario's own registry note must say which backing
   applies.
5. **The negative arm must be evaluated-and-rejecting, not merely unevaluated — added 2026-09-20,
   `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`.** A differential whose
   claim is about *internal logic* ("does this mechanism correctly decline when its own precondition
   isn't met") needs its negative arm to prove the mechanism was *reached and declined to act* — not
   merely that nothing happened. The instance: `goal_hierarchy`'s own detour-resolution scenario
   staged its negative arm ("entity far from the target position") at `state.tick=0`, but the phase's
   real per-entity cadence (`cadence.strategic_intelligence=20` under a live `PROD_SMALL` run, not
   the `DefaultCadence(strategic_intelligence=1)` a plain read of `pipeline.py:53` implies — that
   override only fires when no cadence is supplied at all) meant the entity was never actually
   evaluated at tick 0. The negative arm "passed" — nothing changed — for a reason unrelated to the
   distance check: the mechanism was never reached, not correctly declined. Caught only because the
   *positive* arm failed first and forced a closer look; the negative arm's own false pass would
   never have surfaced on its own. **This is a harness defect, not a search defect, and more
   dangerous than the shapes §3.1 catalogues**: a vacuous negative arm makes a differential look
   rigorous precisely when it is empty, and every verdict this component emits rests on the negative
   arm meaning something. The defense is the same logic as item 3's positive-control pairing, applied
   to the other side: **prove reach, not just outcome** — instrument the mechanism's own call site (a
   counter, a direct pre-check, or equivalent) so the negative arm's report can say "reached, declined"
   rather than only "no change observed." A verdict built on an unproven negative arm should not be
   recorded as `scenario`/`observed` until this is confirmed.
   **Distinguish from item 4's static/demonstrated backing, which this does not replace**: a scenario
   whose own *claim* is reachability itself (`perception`'s "nothing ever calls this phase",
   `temporal_pressure`'s "the gate blocks this by default") is not vacuous when its negative arm shows
   zero reach — that IS the claim, proven the same way item 4 already requires (a static fact, or a
   positive control ruling out the alternative explanation). Item 5 applies specifically when the
   claim is about the mechanism's own internal decision logic, not about whether it runs at all.

This limitation statement belongs in the component's own generated report output as well as this
document, in the same spirit as the census's own unsuppressable `LIMITATION_HEADER` — not decided
here whether that's a fixed string constant or a per-scenario field, left for the implementation
pass.

## 5.1 · A second, distinct axis: the value-differential instrument (added 2026-09-21,
`TCK-20260921-MECHANISM-PROGRESSION-VALUE-DIFFERENTIAL-INSTRUMENT`)

Everything in §§2-5 is **reachability-shaped**: the two arms of a differential differ on whether a
precondition is present or absent, and the question is whether the mechanism fires at all. That
axis cannot answer a second, equally real question for stat/trait/modifier-shaped mechanisms:
`readiness_speed_scaling` and `breakthrough_bonuses` are both real, wired, reachable code — the
open question for them is not "does this run," it's "does its own input value have any purchase
on the outcome." Per-system runtime-evidence share after Program A (merged `main`, `cognition`
11/20, `combat` 4/8, `world` 3/25, `progression` 3/15, `faction`/`social`/`economy` 0 each) showed
sweeping reachability differentials into these systems hits diminishing returns for exactly this
reason — they don't fail by not running, they fail by not mattering.

**Instrument shape**: both arms run the identical real mechanism dispatch. Only the mechanism's own
input value differs between arms — the world is otherwise held fixed. The question is whether a
downstream outcome differs. This is a genuinely different comparison than §3.3's differential
assertions (present/absent), not a variant of it.

**Calibration is a harder requirement here than for reachability.** Program A's reachability axis
had a known negative available in `quest_generation_sourcing` (a real precondition provably never
met). No equivalent "value that provably doesn't matter" exists a priori for this axis, so the
instrument must supply its own calibration before any real verdict is trustworthy:
- **Positive control**: an input certain to affect the outcome (a documented, direct formula
  input) — confirms the instrument can detect a real difference.
- **Negative control**: an input that provably does NOT feed the mechanism under test — confirms
  the instrument does not report a difference whenever anything is perturbed. Without this, a
  "values matter" result is unreadable: an instrument that always reports a difference is worse
  than none, because it would mark every mechanism as mattering.

Both controls are required in the same batch as the first real mechanism, not deferred.

**Three named traps, all real and hit during real application of this instrument
(`readiness_speed_scaling`, `derived_stats`, `evolution`/`xp_leveling`,
`test_readiness_and_derived_stats_value_differential.py`,
`test_evolution_xp_reward_value_differential.py`; the third added 2026-09-21 from the `combat`
program, `test_combat_attributes_real_fight_outcome_value_differential.py`):**

1. **Determinism/seed sensitivity — the value-differential analogue of §5 item 5's cadence trap,
   and subtler.** If varying the input also perturbs RNG draw order (e.g. a different number of
   combat rounds before a kill resolves), downstream differences can appear that have nothing to
   do with the mechanism itself. Not hypothetical here: the `evolution`/`xp_leveling` mechanism's
   own input (`defender.identity.evolution_level`) is read inside a real combat-kill resolution,
   raising exactly this risk. Resolved by direct code trace **before staging anything**, not by
   assumption: `CombatResolutionSystem.calculate_damage()` (`src/engine/combat.py:31-46`) reads
   only `combat.atk`/`combat.def_stat`, no RNG call in the function; `LevelingService.
   recalculate_combat_stats()` (`src/progression/leveling.py:76-180`) reads only
   `AttributeComponent` fields, never `identity.evolution_level`; two independent in-code comments
   (`src/domains/combat_engagement/power.py:49`, `perception.py:51`) state `evolution_level` is
   "deliberately excluded, not merely unweighted" from combat-power comparisons. The varied field
   is therefore structurally inert on the fight's own resolution — confirmed by trace, then
   confirmed again empirically (all three arms of the real test resolve the kill identically). A
   pure, RNG-free mechanism (`readiness_speed_scaling`/`derived_stats`'s own
   `recalculate_combat_stats`) is immune to this trap by construction and makes the strongest
   calibration-mechanism candidate for exactly that reason.
2. **Purpose-built worlds.** The single-shared-world limitation (§3.2) binds here too: a world with
   no progression-capable entities can't show XP mattering. Building a small number of focused
   worlds is legitimate infrastructure for this program — but they must stay production-shaped, no
   forced routes, no entity configurations the real simulation would never produce. If a mechanism
   only matters in a world the game never generates, that is itself the finding, not a staging
   failure to work around. In practice, the first batch needed no new world: both mechanisms reused
   `data/worlds/mechanic_scenario_combat_judgement_withdrawal/`, already a real catalog-driven,
   combat-capable pairing.
3. **Derivation timing — a vacuous differential arriving through a third door, neither an
   unevaluated negative arm nor RNG drift.** When the varied input feeds a DERIVED value rather
   than being read directly by the mechanism under test, the derivation has to have actually run,
   relative to the observation point, or both arms measure the pre-change state and look identical
   for a reason that has nothing to do with whether the input matters. Concrete instance (`combat`
   program): `attributes.strength` does not feed `calculate_damage()` directly — it feeds
   `combat.atk` through `LevelingService.recalculate_combat_stats()`, and the real authoritative
   apply path (`apply.py`'s own `stats_dirty` block) only recalculates derived stats at the END of
   the tick that changed the underlying attribute. A same-tick "change attribute, then attack"
   design would have staged a real attribute change and a real forced attack together, watched the
   fight resolve using the OLD, not-yet-recalculated `combat.atk`, and reported "no difference" — a
   confident false negative, since the derivation simply hadn't run yet at the moment of
   observation, not because the attribute doesn't matter. This generalizes beyond combat: any
   mechanism whose input is derived rather than raw carries this hazard, and the instrument gives
   no signal when it fires — the numbers are internally consistent, just stale. **The defense**:
   before staging a differential on a derived input, establish when that derivation actually runs
   relative to where the observation happens, and stage accordingly — either genuinely separate the
   derivation tick from the observation tick, or (as done here) call the real derivation function
   directly to obtain the value a real recalculation would produce, then stage that result for the
   observation. The second option matters for a specific reason: calling the real function means
   the scenario's expected value comes from the code, not from the scenario author's own reading of
   the formula — hand-computing the expected derived value instead would make the scenario agree
   with that reading rather than with what the code actually does, silently reintroducing exactly
   the kind of unverified assumption this whole instrument exists to remove.

**Registry recording convention**: a value-differential finding is additive to an existing
`verified` note (dated, appended), never a silent overwrite of a prior reachability verdict — the
two axes answer different questions about the same mechanism and both stay recorded. `instrument`
upgrades from `code_trace` to `scenario` when a real differential lands; `verdict` and `state`
change only when the new evidence actually changes that specific claim (see
`readiness_speed_scaling`'s own registry entry: value-differential confirmed positive, corpus-
reachability verdict unchanged, because they are different claims).

Arbitration (the third failure-to-matter shape catalogued in
`TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP`) is out of scope for this axis — it
needs its own instrument.

**A "no difference" verdict requires proof the difference would have been observable within the
scenario's own window — added 2026-09-21, per peer review of batch 1 before approving further
scaling.** Batch 1's three mechanisms were all immediate and deterministic: the outcome is fully
computed in the same tick the input is staged (a formula recalculation, a single combat kill's
reward). Most of `progression` is not shaped that way — skill unlocks fire at thresholds, reward
scaling compounds over many ticks, advancement curves may only diverge after hundreds of events. On
those, a short scenario can show no observable difference while the mechanism matters enormously,
and recording that as "the value doesn't matter" would be a confident false negative of a new kind
— the value-axis analogue of §5 item 5's vacuous negative arm, arriving on a different axis (there:
prove the mechanism was reached and declined, not merely that nothing happened; here: prove the
outcome was actually computed, not merely that no difference was observed by the time the scenario
stopped watching).

**Distinguish from this axis's own negative control (defined above)**: a negative control varies an
input the mechanism provably never reads at all (e.g. `evolution_points` for the XP-reward
formula) — no horizon question applies, because there is no outcome to wait for; the formula
structurally cannot see that field regardless of how long the scenario runs. This new rule applies
to a **real, relevant** input whose effect may simply not have manifested yet within the window
staged — a fundamentally different reason for observing "no difference."

The requirement: for any mechanism whose outcome is not fully computed within the same tick/call
the input is varied, a "no difference" result must do one of:
- **(a) demonstrate the outcome is actually computed within the scenario's own window** — e.g. run
  enough ticks/events inside the scenario itself to cross the threshold, complete the compounding
  window, or otherwise reach the point where a real difference would show up if one existed, or
- **(b) state the horizon explicitly and weaken the verdict accordingly** — record it as "no
  difference observed within N ticks/events," not "the value doesn't matter," and say in the
  registry note what would need to change (a longer window, a different starting position) to
  actually test it.

Positive results need neither — a detected difference is a detected difference regardless of how
short the window was. It is specifically the null result that must earn its own label.

**The instrument's own scope boundary — added 2026-09-21, after `progression` batch 1 + waves 2-3
went 7-for-7 real mechanisms with a 100% pass rate.** A perfect pass rate on this axis is not
evidence the axis reaches everything; it is evidence of *which mechanisms were selected*, and every
one selected so far shares a shape: a documented formula (or discrete branch/threshold selection)
producing a fully-computed, same-tick outcome, with no RNG in the path. That shape is exactly what
this instrument verifies well. It is a materially narrower claim than "this system's values
matter," and reporting "N of M mechanisms in a system now carry a value-differential scenario"
without saying so reads as progress toward covering M, when the honest claim is closer to "N of the
~N mechanisms this instrument can currently address." This is the coverage-claim error (§3.3's own
selection-effect framing) recurring on the value axis instead of the reachability axis — the fix is
the same: state what was actually tested, not what the count implies.

Three mechanism shapes, by how well this instrument reaches them:
- **Reaches well: a documented formula or discrete branch selection with a same-tick, RNG-free (or
  RNG-provably-inert) outcome.** Every mechanism this program has verified so far is this shape
  (`readiness_speed_scaling`, `derived_stats`, `evolution`/`xp_leveling`, `aging_death`,
  `entity_role`, `succession`). The instrument's calibration (a positive and negative control) is
  meaningful here because the outcome is a clean function of a clean input.
- **Reaches poorly, closer to `code_trace` than a real differential: a static catalog/content
  lookup** (e.g. `class_assignment`'s `resolve_role_defaults(role_id)` — a dict lookup by key, not
  an ongoing per-tick mechanism). Varying the lookup key and observing a different record comes
  back is barely distinguishable from reading the resolver's own source; it does not exercise
  runtime behavior the way a real Kernel-tick differential does. Treat a mechanism of this shape as
  presumptively out of scope for this instrument, not as a scenario waiting to be written.
- **Cannot reach at all, without an instrument this program has not built:**
  - **Decision-scoring inputs that feed a choice among competing options** (e.g. `personality`'s
    `bravery` feeding combat-vs-flee utility scoring) — varying the input might change a *score*,
    but whether that changes the *decision* depends on what it's competing against. This is the
    arbitration shape (`TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP`'s third named
    shape), explicitly out of scope for this instrument, not merely unattempted.
  - **A compounding/accumulating rate with no real per-entity varying input** — the §5.1 horizon
    rule above was written to handle a compounding mechanism whose outcome takes many ticks to
    materialize, but it presupposes a real input worth waiting for. If a mechanism's own rate is
    flat and uniform (the same for every entity, driven only by a global cadence/profile config,
    not by anything on the entity itself), there is no entity-level value to differential-test at
    all — the horizon rule has nothing to apply to. This is a distinct finding from "not yet
    tested": it means the instrument does not apply to that mechanism as currently implemented,
    full stop, not that a longer scenario would eventually show a difference.

A close-out or status report against this instrument should state coverage as "N of the mechanisms
in scope for this instrument," name which mechanisms were excluded and why (one of the three
shapes above, or one of the program's own stated out-of-scope reasons — no real producer, flag-
gated, no instrument yet), and never present the excluded count as remaining work for this same
instrument to eventually pick up.

## 6 · Explicitly not decided here

- The exact assertion-vocabulary API (a small typed-object DSL as sketched in §3.3, vs. plain
  callables, vs. something else) — sketched for concreteness, not committed.
- Whether `data/mechanic_scenarios/` world specs are authored as fully independent tiny worlds, or
  as parameterized variants/overrides of a small shared base module — an authoring-ergonomics
  question best answered once the first 1-2 scenarios are actually built.
- Whether the WIPE-style stop condition and other combat-arena-specific harness behavior should be
  generalized into an opt-in per-scenario-category hook, or simply left unused by non-combat
  scenario categories.
- Build order across the six families — not proposed here; a natural default would be to build the
  family(ies) this arc already has the clearest staged precondition for first (world evolution,
  faction sentiment), but that is a scheduling call, not a design one.
- Whether/how this integrates into CI (on-demand only, like the census, or per-PR for the specific
  mechanic a PR touches) — not decided; likely mirrors the census's own "on-demand only" reasoning
  but should be confirmed explicitly, not assumed by inheritance.

## 7 · Related

- `src/certification/harness.py`, `src/certification/scenarios.py`, `src/certification/models.py`,
  `src/certification/conformance.py` — the infrastructure read and partially reused above.
- `docs/plans/simulation_execution_census_initiative.md` — the sibling instrument; §7's own design
  resolution is the template this document's structure follows (division of labor stated up front,
  what's reused vs. new, what's explicitly not decided).
- `docs/plans/world_composition_precondition_gap_finding.md` — the finding this component is a
  direct, general-purpose answer to (see §5's own framing of the relationship).
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`,
  `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`,
  `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` — the parked findings mechanic family 5
  and 4 (world evolution, faction sentiment) would directly test.
