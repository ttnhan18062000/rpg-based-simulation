---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK
phase: open
date: 2026-10-01
tags: [engine, lifecycle, combat]
---

# Test Plan — TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK (Card C1)

## What is being tested and why it asserts a defect

This is an assessment ticket. The new tests **deliberately assert the current, defective
behaviour**, following the precedent of B0's
`tests/mechanic_scenarios/test_combat_death_trace_encounterability.py`. Their purpose is to stop
the findings decaying into prose that has to be re-derived. When the routed fix lands they are
**expected to fail and must be rewritten to the fixed contract, not deleted** — that failure is
the signal the fix changed real behaviour. This is stated in the module docstring so a future
reader cannot mistake them for an endorsement of the behaviour.

## Proof Plan

- **Level:** mechanic-scenario (real `Kernel.tick_once()` over a compiled world), plus one
  corpus-level observation. Not unit-level: the defect lives in the interaction between three
  pipeline phases, so a unit test of any one phase would miss it by construction.
- **Proof kind:** differential (A/B on a single changed field) for the mechanism; existence
  observation for production reachability. Deliberately *not* a golden-value proof — the exact
  tick/entity list is seed-dependent and pinning it would make the test a determinism tripwire
  for an unrelated subsystem.
- **Oracle source:** the hazard-free control arm, which is independently asserted by B0's landed
  `test_combat_death_trace_encounterability.py::test_forced_combat_kill_produces_combat_death_reason_in_one_tick`
  (`death_reason == "COMBAT"`). The oracle is therefore an already-trusted existing assertion, not
  a value invented by this ticket. For trauma, the oracle is the control arm's own measured value,
  compared by equality rather than against a threshold.
- **Expected effect:** changing only `hazard_kind` from an endured to a non-endured kind flips the
  committed outcome from a fully recorded combat death (`death_reason='COMBAT'`, `death_tick=0`,
  `is_permadeath=True`) to no death record at all (`death_reason=None`, `death_tick=None`,
  `is_permadeath=False`) with deactivation slipping one tick. Regional trauma is unchanged between
  arms.
- **Selected commands:**
  - `python -m pytest tests/mechanic_scenarios/test_entity_death_authority_boundary.py tests/mechanic_scenarios/test_combat_death_trace_encounterability.py -v -rA` → `5 passed`
  - `python -m pytest tests/unit/progression/test_lifecycle.py tests/unit/engine/test_apply.py -q -m "not slow"` → `46 passed`
- **Falsifiability:** if the routed fix lands, the two defect-asserting tests fail. That is the
  intended signal, stated in the module docstring, and they are to be rewritten to the fixed
  contract rather than deleted.

## New module: `tests/mechanic_scenarios/test_entity_death_authority_boundary.py`

| Test | Coverage class | Asserts |
|---|---|---|
| `test_immune_hazard_kind_is_the_negative_control_and_records_a_combat_death` | normal flow / negative control | With the arena's own compiled `hazard_kind`, `orc_clan`'s declared endurance makes drain 0 and the forced kill records `death_reason='COMBAT'`, `death_tick=0`, `is_permadeath=True`. Also pins the immunity as the *reason* drain is 0 — the first version of the probe mistook that for "the defect is absent". |
| `test_hazard_drain_destroys_a_same_tick_combat_kill_record` | failure mode / regression-prone path | Changing only `hazard_kind` to a non-endured one: `hp=0` and `combat.alive=False`, but `lifecycle.active` stays `True` on the kill tick, deactivates a tick late, and `death_reason`/`death_tick`/`is_permadeath` are never recorded. Regional trauma is booked identically to the control arm. |
| `test_unrecorded_deaths_occur_in_unscripted_corpus_play` (`@pytest.mark.slow`) | edge case / production reachability | In 120 unscripted ticks of `frontier_marches`, at least one entity is committed `combat.alive=False` + `lifecycle.active=True` + `death_reason=None`, with no staging and no injection. |

### Determinism and isolation

All three fix `seed=42`, `DeterministicRNG(42)`, `PROD_SMALL`, and `flags={"no_frame_pacing": True}`,
compile the world fresh per test, and `kernel.shutdown()` in `finally`. No shared state between
tests, no wall-clock dependence, no network.

### Deliberate choices worth defending

- **The differential is single-variable.** `hazard_level` is pinned at the world's own compiled
  `1.0` in both arms so `hazard_kind` is the only field that differs. An earlier version changed
  both and was discarded as confounded.
- **The trauma assertion is an equality against the control arm, not a threshold.** The booked
  `+1.0` decays per tick (it reads `0.9995` after two ticks). A hardcoded bound would pin the
  decay rate by accident; the claim under test is "the world books this death the same either
  way", which is exactly an equality. The first version asserted `>= 1.0` on the strength of a
  `round(..., 3)` artifact in the probe and failed — the assertion was rewritten to match the
  real claim, **not loosened to go green**.
- **The corpus test asserts only non-emptiness**, not a count. The exact tick/entity list is
  seed- and tick-budget-dependent; pinning it would make the test a determinism tripwire for an
  unrelated subsystem. The counts live in `investigation.md` with their conditions.
- **`@pytest.mark.slow` on the corpus test only.** It runs a 120-tick corpus world. Note the
  blind spot this inherits — see "Known limitation" below.

### Known limitation, stated not hidden

The corpus test is `@slow`, and per `TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED`
`@slow` is excluded from the gating CI lane, so a regression in it would not be reported
automatically. It is marked `@slow` because it genuinely is; the right resolution is that
ticket's reporting-path work, not silently promoting this one test out of the marker. Recorded
here so the gap is visible rather than assumed away.

## Existing tests re-run as controls

| Module | Why |
|---|---|
| `tests/mechanic_scenarios/test_combat_death_trace_encounterability.py` | B0's module; its `test_forced_combat_kill_produces_combat_death_reason_in_one_tick` is the independent cross-check that the hazard-free kill path still records `COMBAT`. Must stay green. |
| `tests/unit/progression/test_lifecycle.py`, `tests/unit/engine/test_apply.py` | Nearest existing coverage of `resolve_lifecycle` and the `apply.py` passive branch, i.e. the two modules this ticket's findings are about. Scoped per the Testing Rule rather than running the full suite. |

## Result

`5 passed` for the new module plus B0's module. See the ticket's Test Summary for the scoped
domain runs.

## Not tested, deliberately

- **No test of the fix**, because no fix is written (ticket Out of Scope).
- **No attempt to force the combat+hazard collision in an unscripted corpus run.** It needs a
  conjunction of two independently rare events; a test that waited for it would be a slow,
  flaky lottery. The mechanism is proved by the scripted differential and the reachability
  argument is made from separately measured rates, which is the honest decomposition.
