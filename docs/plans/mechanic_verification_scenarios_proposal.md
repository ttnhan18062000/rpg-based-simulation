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

**Four rules, all load-bearing, all already-observed rather than hypothetical (items 3 and 4 added
2026-09-20, `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`, per direct peer
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

This limitation statement belongs in the component's own generated report output as well as this
document, in the same spirit as the census's own unsuppressable `LIMITATION_HEADER` — not decided
here whether that's a fixed string constant or a per-scenario field, left for the implementation
pass.

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
